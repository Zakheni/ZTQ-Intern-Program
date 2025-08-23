from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools.translate import _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _description = 'Zi-Waste Purchase Order'

    po_number = fields.Char(
        string='Purchase Order Number',
        required=True,
        default=lambda self: _('New'),
        copy=False,
        readonly=True
    )
    vendor_number = fields.Char(
        string='Vendor Number',
        default=lambda self: _('New'),
        copy=False,
        readonly=True
    )
    mine_id = fields.Many2one('mine.mine', string='Mine', required=True)
    bin_total = fields.Integer(string='Number of Bins')
    bin_in_use = fields.Many2many(
        'stock.quant',
        string='Bins in Use',
        domain="[('mine_id', '=', mine_id), ('product_id.is_asset', '=', True)]"
    )
    bin_not_in_use = fields.Integer(string='Bins Not in Use', compute='_compute_bin_not_in_use')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    item_code_ids = fields.Many2many('item.code', string='Item Codes')
    disposal_site_ids = fields.Many2many('disposal.site', string='Disposal Sites')
    waste_type_ids = fields.Many2many('waste.type', string='Waste Types')
    rental_type = fields.Selection([('bin', 'Bin'), ('trailer', 'Trailer')], string='Rental Type')
    is_rental = fields.Boolean(compute='_compute_rate_type_flags')
    is_disposal = fields.Boolean(compute='_compute_rate_type_flags')
    rate_type = fields.Char(
        string='Rate Type',
        compute='_compute_rate_type',
        store=False
    )
    customer_id = fields.Many2one('res.partner', string='Customer', compute='_compute_customer_id')
    partner_id = fields.Many2one(
        'res.partner',
        string="Vendor",
        required=False,
        states={'draft': [('readonly', False)]}
    )
    color = fields.Integer(string='Color Index', default=0)

    @api.model
    def create(self, vals):

        if vals.get('po_number', _('New')) == _('New'):
            vals['po_number'] = self.env['ir.sequence'].next_by_code('purchase.order.zi') or _('New')

        if vals.get('vendor_number', _('New')) == _('New'):
            vals['vendor_number'] = self.env['ir.sequence'].next_by_code('purchase.order.vendor') or _('New')


        if 'partner_id' not in vals or not vals['partner_id']:
            default_vendor = self.env['res.partner'].search([
                ('supplier_rank', '>', 0),
                ('company_id', 'in', [False, vals.get('company_id', self.env.company.id)])
            ], limit=1)
            if default_vendor:
                vals['partner_id'] = default_vendor.id
            else:
                raise UserError("System could not find a default vendor. Please contact your administrator.")


        record = super().create(vals)


        if record.mine_id and record.bin_in_use:
            record.bin_in_use.write({'mine_id': record.mine_id.id})

        return record

    @api.ondelete(at_uninstall=False)
    def _unlink_if_not_confirmed(self):
        for line in self:
            if line.state in ['purchase', 'done']:
                raise UserError(
                    "Cannot delete a purchase order line which is in state '%s'."
                    % line.state
                )


    @api.depends('item_code_ids.rate_type')
    def _compute_rate_type_flags(self):

        for record in self:
            rate_types = record.item_code_ids.mapped('rate_type')
            record.is_rental = 'rental' in rate_types
            record.is_disposal = 'disposal' in rate_types

    @api.depends('item_code_ids.rate_type')
    def _compute_rate_type(self):

        for record in self:

            rate_types = list(set(record.item_code_ids.mapped('rate_type')))

            rate_types.sort()
            record.rate_type = ', '.join(rate_types) if rate_types else False

    @api.depends('bin_total', 'bin_in_use')
    def _compute_bin_not_in_use(self):
        for record in self:
            record.bin_not_in_use = record.bin_total - len(record.bin_in_use)

    @api.depends('mine_id')
    def _compute_customer_id(self):
        for record in self:
            record.customer_id = record.mine_id.customer_id if record.mine_id else False

    @api.constrains('po_number', 'vendor_number')
    def _check_unique(self):
        for record in self:

            if record.po_number == _('New') or record.vendor_number == _('New'):
                continue

            if self.search([('po_number', '=', record.po_number), ('id', '!=', record.id)]):
                raise ValidationError("Purchase Order Number must be unique!")
            if self.search([('vendor_number', '=', record.vendor_number), ('id', '!=', record.id)]):
                raise ValidationError("Vendor Number must be unique!")

    @api.onchange('item_code_ids')
    def _onchange_item_codes(self):
        for record in self:
            if any(code.rate_type == 'disposal' for code in record.item_code_ids):
                record.rental_type = False
            elif any(code.rate_type == 'rental' for code in record.item_code_ids):
                record.rental_type = 'bin'

    @api.constrains('item_code_ids', 'waste_type_ids', 'disposal_site_ids')
    def _check_disposal_requirements(self):
        for record in self:
            if record.is_disposal:
                if not record.waste_type_ids:
                    raise ValidationError("Waste Type must be defined for disposal services.")
                if not record.disposal_site_ids:
                    raise ValidationError("Disposal Sites must be defined for disposal services.")

    @api.constrains('item_code_ids', 'bin_total', 'bin_in_use', 'rental_type')
    def _check_rental_requirements(self):
        for record in self:
            if record.is_rental:
                if not record.bin_total:
                    raise ValidationError("Number of Bins must be specified for rental services.")
                if not record.bin_in_use:
                    raise ValidationError("Bins in Use must be assigned for rental services.")
                if not record.rental_type:
                    raise ValidationError("Rental Type must be selected for rental services.")

    def write(self, vals):
        if 'order_line' in vals:
            for order in self:
                if order.state in ['purchase', 'done']:
                    deleted_lines = [cmd[1] for cmd in vals['order_line'] if cmd[0] == 2]
                    if deleted_lines:
                        raise UserError(
                            "Cannot delete order lines when order is in state '%s'. "
                            "Please cancel the order first." % order.state
                        )
        res = super(PurchaseOrder, self).write(vals)
        if 'bin_in_use' in vals or 'mine_id' in vals:
            for record in self:
                if record.mine_id:
                    record.bin_in_use.write({'mine_id': record.mine_id.id})
        return res


