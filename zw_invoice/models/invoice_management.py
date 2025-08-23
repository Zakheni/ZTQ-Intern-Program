# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class WasteInvoice(models.Model):
    _name = 'waste.invoice'
    _description = 'Waste Management Invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'invoice_date desc, id desc'


    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)


    name = fields.Char(string='Invoice Number', readonly=True, copy=False, default=lambda self: _('New'))
    invoice_date = fields.Date(string='Invoice Date', required=True, default=fields.Date.context_today)
    invoice_date_due = fields.Date(string='Due Date', required=True)
    payment_reference = fields.Char(string='Payment Reference', compute='_compute_payment_reference', store=True)


    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        domain="[('vat_number', '!=', False)]",
        required=True,
        tracking=True
    )

    mine_ids = fields.Many2many(
        'mine.mine',
        string='Mines',
        required=True,
        tracking=True
    )

    manifest_rel_ids = fields.One2many(
        'waste.manifest.invoice.rel',
        'invoice_id',
        string='Manifest Relations'
    )

    manifest_ids = fields.Many2many(
        'waste.manifest',
        string='Manifests',
        compute='_compute_manifest_ids',
        inverse='_inverse_manifest_ids',
        store=False,
        readonly=False,
        relation='waste_manifest_invoice_rel',
        column1='invoice_id',
        column2='manifest_id',
        domain="""[
            ('status', '=', 'authorized'),
            ('customer_id', '=', customer_id),
            ('mine_id', 'in', mine_ids.ids),
            ('id', 'not in', used_manifest_ids),
            ('invoice_rel_ids', '=', False)
        ]""",
        help="Select manifests that haven't been invoiced yet"
    )
    used_manifest_ids = fields.Many2many(
        'waste.manifest',
        compute='_compute_used_manifest_ids',
        store=False
    )

    item_code_ids = fields.Many2many(
        'item.code',
        string='Services',
        compute='_compute_item_codes_from_manifests',
        store=True,
        readonly=False
    )

    waste_type_id = fields.Many2one(
        'waste.type',
        string='Waste Type',
        compute='_compute_waste_type_from_manifest',
        store=True,
        readonly=False,
        domain="[('id', 'in', available_waste_type_ids)]"
    )

    available_waste_type_ids = fields.Many2many(
        'waste.type',
        compute='_compute_available_waste_types',
        store=False
    )

    bin_size_id = fields.Many2one(
        'product.product',
        string='Bin Size',
        compute='_compute_bin_size',
        store=True,
        readonly=False,
        domain=lambda self: self._get_bin_size_domain()
    )

    available_bin_size_ids = fields.Many2many(
        'product.product',
        compute='_compute_available_bin_sizes',
        store=False
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )



    mine_name = fields.Char(
        string='Mine Name',
        compute='_compute_mine_name',
        store=True
    )

    total_amount_excl_tax = fields.Float(
        string='Total Excl. Tax',
        compute='_compute_totals',
        store=True,
        readonly=True,
        digits=(64, 2)
    )

    total_amount_incl_tax = fields.Float(
        string='Total Incl. Tax',
        compute='_compute_totals',
        store=True,
        readonly=True,
        digits=(64, 2)
    )


    has_transport_service = fields.Boolean(
        compute='_compute_service_flags',
        string='Has Transport Service',
        store=True
    )
    has_disposal_service = fields.Boolean(
        compute='_compute_service_flags',
        string='Has Disposal Service',
        store=True
    )
    has_rental_service = fields.Boolean(
        compute='_compute_service_flags',
        string='Has Rental Service',
        store=True
    )
    has_labour_service = fields.Boolean(
        compute='_compute_service_flags',
        string='Has Labour Service',
        store=True
    )

    # Line items
    invoice_line_ids = fields.One2many(
        'waste.invoice.line',
        'invoice_id',
        string='Invoice Lines'
    )

    # Accounting fields
    move_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True,
        copy=False
    )
    move_type = fields.Selection(
        selection=[('out_invoice', 'Customer Invoice')],
        string='Type',
        default='out_invoice',
        readonly=True
    )


    @api.depends('manifest_ids')
    def _compute_available_waste_types(self):
        for invoice in self:
            invoice.available_waste_type_ids = invoice.manifest_ids.mapped(
                'waste_type_id') if invoice.manifest_ids else False


    @api.depends('mine_ids')
    def _compute_mine_name(self):
        for invoice in self:
            invoice.mine_name = ', '.join(invoice.mine_ids.mapped('name')) if invoice.mine_ids else ''

    @api.depends('manifest_rel_ids.manifest_id')
    def _compute_manifest_ids(self):
        for invoice in self:
            try:
                if invoice.exists():
                    invoice.manifest_ids = invoice.manifest_rel_ids.mapped('manifest_id').exists()
                else:
                    invoice.manifest_ids = False
            except Exception as e:
                _logger.error("Error computing manifest_ids for invoice %s: %s", invoice.id, str(e))
                invoice.manifest_ids = False

    def _inverse_manifest_ids(self):
        for invoice in self:
            if not invoice.exists():
                continue

            try:
                current_manifests = self.env['waste.manifest'].browse(
                    invoice.manifest_rel_ids.mapped('manifest_id.id')
                )


                desired_manifests = self.env['waste.manifest'].browse(
                    invoice.manifest_ids.ids
                )


                to_add = desired_manifests - current_manifests
                to_remove = current_manifests - desired_manifests


                if to_remove:
                    invoice.manifest_rel_ids.filtered(
                        lambda r: r.manifest_id in to_remove
                    ).unlink()


                if to_add:
                    rel_vals = [{
                        'manifest_id': manifest.id,
                        'invoice_id': invoice.id
                    } for manifest in to_add if manifest.exists()]

                    if rel_vals:
                        self.env['waste.manifest.invoice.rel'].create(rel_vals)

            except Exception as e:
                _logger.error("Error in _inverse_manifest_ids for invoice %s: %s", invoice.id, str(e))
                continue

    @api.depends()
    def _compute_used_manifest_ids(self):
        for invoice in self:
            invoice.used_manifest_ids = self.env['waste.manifest.invoice.rel'].search([
                ('invoice_id', '!=', invoice.id or False)
            ]).mapped('manifest_id')

    @api.depends('name', 'invoice_date')
    def _compute_payment_reference(self):
        for invoice in self:
            if invoice.name and invoice.invoice_date:
                invoice.payment_reference = f"INV-{invoice.invoice_date.strftime('%Y%m%d')}-{invoice.name.split('/')[-1]}"
            else:
                invoice.payment_reference = False

    @api.depends('manifest_ids.item_code_ids')
    def _compute_item_codes_from_manifests(self):
        for invoice in self:
            invoice.item_code_ids = invoice.manifest_ids.mapped('item_code_ids') if invoice.manifest_ids else [
                (5, 0, 0)]

    @api.depends('manifest_ids', 'item_code_ids')
    def _compute_waste_type_from_manifest(self):
        for invoice in self:
            if invoice.manifest_ids and any(code.code == 'DSP-TON' for code in invoice.item_code_ids):
                invoice.waste_type_id = invoice.manifest_ids[0].waste_type_id
            else:
                invoice.waste_type_id = False

    @api.depends('manifest_ids', 'item_code_ids')
    def _compute_bin_size(self):
        for invoice in self:
            if invoice.manifest_ids and any(code.code == 'RNT-BIN' for code in invoice.item_code_ids):
                invoice.bin_size_id = invoice.manifest_ids[0].bin_size_id
            else:
                invoice.bin_size_id = False

    @api.depends('manifest_ids', 'item_code_ids')
    def _compute_available_bin_sizes(self):
        for invoice in self:
            if invoice.manifest_ids and any(code.code == 'RNT-BIN' for code in invoice.item_code_ids):
                invoice.available_bin_size_ids = invoice.manifest_ids.mapped('bin_size_id')
            else:
                invoice.available_bin_size_ids = [(5, 0, 0)]

    def _get_bin_size_domain(self):
        return [('id', 'in', self.available_bin_size_ids.ids)] if self.available_bin_size_ids else []

    @api.depends('item_code_ids')
    def _compute_service_flags(self):
        for invoice in self:
            codes = invoice.item_code_ids.mapped('code')
            invoice.has_transport_service = any(code in ['TRN-KM', 'TRN-LOAD'] for code in codes)
            invoice.has_disposal_service = 'DSP-TON' in codes
            invoice.has_rental_service = 'RNT-BIN' in codes
            invoice.has_labour_service = 'LBR-HOUR' in codes

    @api.depends('invoice_line_ids', 'item_code_ids', 'manifest_ids')
    def _compute_totals(self):
        for invoice in self:
            if invoice.invoice_line_ids:

                subtotal = sum(line.price_subtotal for line in invoice.invoice_line_ids)
                tax_amount = sum(line.price_tax for line in invoice.invoice_line_ids)
                invoice.total_amount_excl_tax = subtotal
                invoice.total_amount_incl_tax = subtotal + tax_amount
            elif invoice.item_code_ids and invoice.manifest_ids:

                transport_distance = sum(invoice.manifest_ids.mapped('transport_distance'))
                disposal_tonnage = sum(invoice.manifest_ids.mapped('disposal_tonnage'))
                rental_duration = sum(invoice.manifest_ids.mapped('rental_duration'))
                labour_hours = sum(invoice.manifest_ids.mapped('labour_hours'))

                subtotal = 0.0
                for code in invoice.item_code_ids.filtered(lambda c: c):
                    rate = code.base_rate
                    if code.code == 'TRN-KM':
                        rate *= transport_distance
                    elif code.code == 'DSP-TON':
                        rate *= disposal_tonnage
                    elif code.code == 'RNT-BIN':
                        rate *= rental_duration
                    elif code.code == 'LBR-HOUR':
                        rate *= labour_hours

                    if code.discount:
                        rate *= (1 - code.discount / 100)

                    subtotal += rate


                vat_tax = self.env['account.tax'].search([
                    ('amount', '=', 15.0),
                    ('type_tax_use', '=', 'sale'),
                    ('amount_type', '=', 'percent')
                ], limit=1)

                vat_amount = subtotal * (vat_tax.amount / 100) if vat_tax else 0.0
                invoice.total_amount_excl_tax = subtotal
                invoice.total_amount_incl_tax = subtotal + vat_amount
            else:
                invoice.total_amount_excl_tax = 0.0
                invoice.total_amount_incl_tax = 0.0

    @api.onchange('mine_ids')
    def _onchange_mine_ids(self):
        if self.mine_ids and self.customer_id:
            used_manifests = self.env['waste.manifest.invoice.rel'].search([
                ('invoice_id', '!=', self.id or False)
            ]).mapped('manifest_id.id')

            return {
                'domain': {
                    'manifest_ids': [
                        ('status', '=', 'authorized'),
                        ('mine_id', 'in', self.mine_ids.ids),
                        ('customer_id', '=', self.customer_id.id),
                        ('id', 'not in', used_manifests),
                        ('invoice_rel_ids', '=', False)
                    ]
                }
            }
        else:
            self.manifest_ids = [(5, 0, 0)]

    @api.onchange('manifest_ids')
    def _onchange_manifest_ids(self):
        try:
            self._compute_item_codes_from_manifests()
            self._compute_waste_type_from_manifest()
            self._compute_bin_size()
            self._compute_available_bin_sizes()
            self._compute_service_flags()
            self._generate_invoice_lines()


        except Exception as e:
            _logger.error("Error in _onchange_manifest_ids: %s", str(e))
            return {
                'warning': {
                    'title': _('Error'),
                    'message': _('An error occurred while processing manifests.')
                }
            }

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id:
            self.mine_ids = self.env['mine.mine'].search([('customer_id', '=', self.customer_id.id)])
            self._onchange_mine_ids()
        else:
            self.mine_ids = [(5, 0, 0)]
            self.manifest_ids = [(5, 0, 0)]

    @api.onchange('item_code_ids')
    def _onchange_item_code_ids(self):
        self._compute_service_flags()
        self._compute_waste_type_from_manifest()
        self._compute_bin_size()
        self._generate_invoice_lines()

    @api.onchange('invoice_date')
    def _onchange_invoice_date(self):
        if self.invoice_date:
            self.invoice_date_due = self.invoice_date + relativedelta(days=30)



    @api.constrains('manifest_ids')
    def _check_manifest(self):
        for invoice in self:
            if not invoice.manifest_ids:
                raise ValidationError(_("At least one manifest must be selected!"))


            for manifest in invoice.manifest_ids:
                if not manifest.exists():
                    raise ValidationError(_("One or more manifests no longer exist!"))
                if manifest.status != 'authorized':
                    raise ValidationError(_("All manifests must be authorized!"))


            for manifest in invoice.manifest_ids:
                if not manifest.exists():
                    continue


                other_invoices = self.env['waste.invoice'].browse(
                    [inv.id for inv in manifest.invoice_ids if inv._name == 'waste.invoice']
                )

                if other_invoices - invoice:
                    raise ValidationError(_(
                        "Manifest %s is already invoiced in %s" %
                        (manifest.manifest_ids, other_invoices.mapped('name'))
                    ))



    def _generate_invoice_lines(self):

        self.ensure_one()
        self.invoice_line_ids = [(5, 0, 0)]

        if not self.item_code_ids or not self.manifest_ids:
            return


        vat_tax = self.env['account.tax'].search([
            ('amount', '=', 15.0),
            ('type_tax_use', '=', 'sale'),
            ('amount_type', '=', 'percent')
        ], limit=1)


        transport_distance = sum(self.manifest_ids.mapped('transport_distance'))
        disposal_tonnage = sum(self.manifest_ids.mapped('disposal_tonnage'))
        rental_duration = sum(self.manifest_ids.mapped('rental_duration'))
        labour_hours = sum(self.manifest_ids.mapped('labour_hours'))

        lines = []
        for code in self.item_code_ids.filtered(lambda c: c):
            price_unit = code.base_rate


            if code.code == 'TRN-KM':
                price_unit *= transport_distance
            elif code.code == 'DSP-TON':
                price_unit *= disposal_tonnage
            elif code.code == 'RNT-BIN':
                price_unit *= rental_duration
            elif code.code == 'LBR-HOUR':
                price_unit *= labour_hours


            if code.discount:
                price_unit *= (1 - code.discount / 100)


            tax_ids = [(6, 0, [vat_tax.id])] if code.vat else []


            if not code.product_id:
                raise UserError(_("Product is not set for item code %s") % code.name)

            lines.append((0, 0, {
                'product_id': code.product_id.id,
                'name': code.name,
                'quantity': 1,
                'price_unit': price_unit,
                'tax_ids': tax_ids,
                'item_code_id': code.id,
            }))

        self.invoice_line_ids = lines

    def _prepare_account_move_vals(self):

        self.ensure_one()
        return {
            'move_type': 'out_invoice',
            'partner_id': self.customer_id.id,
            'invoice_date': self.invoice_date,
            'invoice_date_due': self.invoice_date_due,
            'currency_id': self.currency_id.id,
            'invoice_origin': self.name,
            'invoice_payment_ref': self.payment_reference,
            'company_id': self.company_id.id,
            'ref': f"Waste Invoice: {self.name}",
            'invoice_line_ids': [],
            'zw_invoice_id': self.id,
        }

    def _search_manifest_ids(self, operator, value):

        if operator == 'in':
            return [('manifest_rel_ids.manifest_id', operator, value)]
        return []


    def action_post(self):

        for invoice in self:
            if invoice.state != 'draft':
                raise UserError(_("Only draft invoices can be posted."))
            if not invoice.invoice_line_ids:
                raise UserError(_("Please generate invoice lines before posting."))
            if not invoice.manifest_ids:
                raise UserError(_("Cannot post invoice without linked manifests!"))


            move = self.env['account.move'].create(invoice._prepare_account_move_vals())


            for line in invoice.invoice_line_ids:
                self.env['account.move.line'].create(line._prepare_account_move_line_vals(move))


            move.action_post()


            invoice.write({
                'state': 'posted',
                'move_id': move.id,
                'manifest_rel_ids': [(1, rel.id, {'locked': True}) for rel in invoice.manifest_rel_ids]
            })
        return True

    def action_cancel(self):

        for invoice in self:
            if invoice.move_id:
                invoice.move_id.button_cancel()
            invoice.write({'state': 'cancelled'})
        return True

    def action_draft(self):

        self.write({'state': 'draft'})
        return True

    def action_view_account_move(self):

        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entry',
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'view_mode': 'form',
            'context': {'create': False},
        }

    @api.model
    def create(self, vals):

        if vals.get('name', _('New')) == _('New'):
            seq = self.env['ir.sequence'].search([('code', '=', 'waste.invoice')], limit=1)
            if not seq:
                raise UserError(_("Please create a sequence with code 'waste.invoice'"))
            vals['name'] = seq.next_by_id() or _('New')


        manifest_ids = vals.pop('manifest_ids', False)
        invoice = super().create(vals)

        if manifest_ids:
            invoice.write({'manifest_ids': manifest_ids})

        return invoice
    def write(self, vals):

        try:
            if 'manifest_rel_ids' in vals:
                if hasattr(self, '_fields') and 'manifest_ids' in self._fields:
                    self.env.cache.invalidate([(self._fields['manifest_ids'], self.ids)])
            return super().write(vals)
        except Exception as e:
            _logger.error("Error writing invoice %s: %s", self.ids, str(e))
            raise