from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
import logging
from odoo.tools import sql

from odoo.tools.translate import _

_logger = logging.getLogger(__name__)



class WasteType(models.Model):
    _name = 'waste.type'
    _description = 'Waste Type'
    _rec_name = 'display_name'

    name = fields.Selection([
        ('combustible', 'Combustible'),
        ('non_combustible', 'Non-Combustible'),
        ('hazardous', 'Hazardous')
    ], required=True, default='non_combustible')

    display_name = fields.Char(string='Waste Type', compute='_compute_display_name', store=True)

    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = dict(self._fields['name'].selection).get(record.name)

    @api.ondelete(at_uninstall=True)
    def _prevent_delete_if_referenced(self):

        if not self.env.context.get('module_uninstall'):
            for waste_type in self:
                if self.env['waste.manifest'].search_count([('waste_type_id', '=', waste_type.id)]):
                    raise UserError(
                        "Cannot delete this waste type as it's referenced by manifests. "
                        "Please update all manifests first."
                    )


class Manifest(models.Model):
    _name = 'waste.manifest'
    _description = 'Waste Manifest'

    manifest_ids = fields.Char(string='Manifest ID', required=True,
                               default=lambda self: self.env['ir.sequence'].next_by_code('waste.manifest'))

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    waste_type_id = fields.Many2one(
        'waste.type',
        string='Waste Type',
        required=True,
        ondelete='restrict',
        default=lambda self: self._get_default_waste_type()
    )


    tonnage = fields.Float(string='Tonnage')
    dt_number = fields.Char(string='DT Number')
    un_sin_code = fields.Char(string='UN/SIN Code')
    status = fields.Selection([
        ('booked', 'Booked'),
        ('generated', 'Generated'),
        ('scheduled', 'Scheduled'),
        ('delivered', 'Delivered'),
        ('authorized', 'Authorized')
    ], string='Status', default='booked')
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        domain=[('vat_number', '!=', False)]
    )
    mine_id = fields.Many2one('mine.mine', string='Mine', required=False,

                              default=lambda self: self.env['mine.mine'].search([], limit=1).id)
    disposal_site_id = fields.Many2one('disposal.site', string='Disposal Site', required=False)
    driver_id = fields.Many2one('res.users', string='Driver')

    weighbridge_receipt = fields.Binary(string='Weighbridge Receipt')
    safe_disposal_certificate = fields.Binary(string='Safe Disposal Certificate')
    signature_mine = fields.Binary(string='Mine Signature')
    signature_driver = fields.Binary(string='Driver Signature')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    item_code_ids = fields.Many2many('item.code', string='Services')
    bin_size_id = fields.Many2one(
        'product.product',
        string='Bin Size',
        help="Required for rental services"
    )

    duration_unit = fields.Selection([
        ('hours', 'Hours'),
        ('days', 'Days')
    ], string="Duration Unit", default='hours')
    transport_distance = fields.Float(string="Transport Distance (km)")
    disposal_tonnage = fields.Float(string="Disposal Tonnage (tons)")
    rental_duration = fields.Float(string="Rental Duration")
    labour_hours = fields.Float(string="Labour Hours")
    has_transport_service = fields.Boolean(compute='_compute_service_types', store=False)
    has_disposal_service = fields.Boolean(compute='_compute_service_types', store=False)
    has_rental_service = fields.Boolean(compute='_compute_service_types', store=False)
    has_labour_service = fields.Boolean(compute='_compute_service_types', store=False)
    sawis_number = fields.Char(
        string='SAWIS Number',
        required=True,
        default=lambda self: self._get_default_sawis_number()
    )

    invoice_rel_ids = fields.One2many(
        'waste.manifest.invoice.rel',
        'manifest_id',
        string='Invoice Relations'
    )

    invoice_ids = fields.Many2many(
        'waste.invoice',
        string='Invoices',
        compute='_compute_invoice_ids',
        store=False,
        readonly=True,
        relation='waste_manifest_invoice_rel',
        column1='manifest_id',
        column2='invoice_id'
    )

    @api.depends('invoice_rel_ids.invoice_id')
    def _compute_invoice_ids(self):

        self.env.cr.execute("""
            SELECT manifest_id, array_agg(invoice_id) 
            FROM waste_manifest_invoice_rel
            WHERE manifest_id IN %s
            GROUP BY manifest_id
        """, [tuple(self.ids)])

        result = dict(self.env.cr.fetchall())
        for manifest in self:
            manifest.invoice_ids = result.get(manifest.id, [])

    def _repair_invoice_relations(self):

        _logger.info("Starting manifest-invoice relation repair")

        # 1. Verify table exists
        if not sql.table_exists(self.env.cr, 'waste_manifest_invoice_rel'):
            _logger.error("Relation table does not exist!")
            return False


        self.env.cr.execute("""
            DELETE FROM waste_manifest_invoice_rel
            WHERE manifest_id NOT IN (SELECT id FROM waste_manifest)
            OR invoice_id NOT IN (SELECT id FROM waste_invoice)
        """)


        try:
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS waste_manifest_invoice_rel_manifest_id_idx 
                ON waste_manifest_invoice_rel (manifest_id)
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS waste_manifest_invoice_rel_invoice_id_idx 
                ON waste_manifest_invoice_rel (invoice_id)
            """)
        except Exception as e:
            _logger.warning("Could not create indexes: %s", str(e))

        self.env.cr.execute("COMMIT")
        _logger.info("Completed relation repair")
        return True

    def _get_default_sawis_number(self):
        if self.env.context.get('default_mine_id'):
            mine = self.env['mine.mine'].browse(self.env.context['default_mine_id'])
            return mine.sawis_number
        return False

    @api.onchange('item_code_ids')
    def _onchange_item_codes(self):

        self.transport_distance = 0.0
        self.disposal_tonnage = 0.0
        self.rental_duration = 0.0
        self.labour_hours = 0.0

        if any(code.code == 'DSP-TON' for code in self.item_code_ids):
            self.waste_type_id = self._get_default_waste_type()

    @api.depends('item_code_ids')
    def _compute_service_types(self):
        for record in self:
            codes = record.item_code_ids.mapped('code')
            record.has_transport_service = any(code in ['TRN-KM', 'TRN-LOAD'] for code in codes)
            record.has_disposal_service = 'DSP-TON' in codes
            record.has_rental_service = 'RNT-BIN' in codes
            record.has_labour_service = 'LBR-HOUR' in codes

    @api.depends('invoice_rel_ids.invoice_id')
    def _compute_invoice_ids(self):

        for manifest in self:
            try:
                manifest.invoice_ids = manifest.invoice_rel_ids.mapped('invoice_id')
            except Exception as e:
                _logger.error("Error computing invoice_ids for manifest %s: %s", manifest.id, str(e))
                manifest.invoice_ids = False


    @api.constrains('dt_number', 'waste_type_id')
    def _check_hazardous_compliance(self):
        for record in self:
            if record.waste_type_id.name == 'hazardous' and not record.dt_number:
                raise ValidationError("DT Number is required for hazardous waste!")

    @api.onchange('customer_id')
    def _onchange_customer_id(self):

        if self.customer_id:
            mines = self.env['mine.mine'].search([('customer_id', '=', self.customer_id.id)])

            if not mines:
                return {
                    'warning': {
                        'title': 'No Mines Found',
                        'message': 'Selected customer has no associated mines'
                    }
                }


            mine = mines[0]
            disposal_site = mine.disposal_site_ids[0] if mine.disposal_site_ids else False

            update_vals = {
                'mine_id': mine.id,
                'sawis_number': mine.sawis_number,
                'disposal_site_id': disposal_site.id if disposal_site else False
            }

            self.update(update_vals)
            self._compute_item_codes()

            return {
                'domain': {
                    'mine_id': [('id', 'in', mines.ids)],
                    'disposal_site_id': [('id', 'in', mine.disposal_site_ids.ids)] if mine.disposal_site_ids else []
                }
            }
        else:

            self.update({
                'mine_id': False,
                'disposal_site_id': False,
                'sawis_number': False,
                'item_code_ids': [(5, 0, 0)]
            })
            return {'domain': {'mine_id': []}}

    @api.onchange('mine_id')
    def _onchange_mine_id(self):
        if self.mine_id:
            disposal_site = self.mine_id.disposal_site_ids[0] if self.mine_id.disposal_site_ids else False
            self.update({
                'sawis_number': self.mine_id.sawis_number,
                'disposal_site_id': disposal_site.id if disposal_site else False,
                'customer_id': self.mine_id.customer_id.id,
            })
            self._compute_item_codes()
            return {'domain': {'disposal_site_id': [('id', 'in', self.mine_id.disposal_site_ids.ids)]}}
        else:
            self.update({
                'sawis_number': False,
                'disposal_site_id': False,
                'item_code_ids': [(5, 0, 0)]
            })
            return {'domain': {'disposal_site_id': []}}


    def _get_default_waste_type(self):

        waste_type = self.env.ref('zw_manifest.waste_type_non_combustible', raise_if_not_found=False)
        if not waste_type:

            waste_type = self.env['waste.type'].search([], limit=1)
            if not waste_type:

                waste_type = self.env['waste.type'].create({
                    'name': 'non_combustible'
                })
        return waste_type.id

    def unlink(self):

        try:
            # Verify access rights first
            self.check_access_rights('unlink')
            self.check_access_rule('unlink')


            existing_records = self.exists()
            if not existing_records:
                return True


            try:

                self.env.cr.execute("""
                    DELETE FROM waste_manifest_invoice_rel
                    WHERE manifest_id IN %s
                """, [tuple(existing_records.ids)])


                self.env.cr.execute("""
                    DELETE FROM waste_schedule
                    WHERE manifest_id IN %s
                """, [tuple(existing_records.ids)])


                self.env.cr.commit()

            except Exception as e:
                self.env.cr.rollback()
                error_msg = f"Failed to clean up manifest relations: {str(e)}"
                _logger.error(error_msg)
                raise UserError(_(error_msg))


            return super(Manifest, self).unlink()

        except Exception as e:
            error_msg = f"Could not delete manifests: {str(e)}"
            _logger.error(error_msg)
            raise UserError(_(error_msg))

    def _get_item_code_domain(self):
        if not self.mine_id:
            return []
        pos = self.env['purchase.order'].search([
            ('mine_id', '=', self.mine_id.id),
            ('state', 'in', ['purchase', 'done'])
        ])
        return [('id', 'in', pos.mapped('item_code_ids').ids)]

    @api.depends('mine_id')
    def _compute_item_codes(self):
        for record in self:
            if record.mine_id:
                pos = self.env['purchase.order'].search([
                    ('mine_id', '=', record.mine_id.id),
                    ('state', 'in', ['purchase', 'done'])
                ])
                record.item_code_ids = pos.mapped('item_code_ids')
            else:
                record.item_code_ids = False

    def _search_invoice_ids(self, operator, value):

        if operator == 'in':
            return [('invoice_rel_ids.invoice_id', operator, value)]
        return []








    def action_advance_status(self):
        status_map = {
            'booked': 'generated',
            'generated': 'scheduled',
            'scheduled': 'delivered',
            'delivered': 'authorized'
        }
        if self.status in status_map:
            self.status = status_map[self.status]
            self.env['audit.log'].create({
                'model_name': 'waste.manifest',
                'record_id': self.id,
                'operation': 'status_change',
                'user_id': self.env.uid,
                'changes': f"Status changed to {self.status}"
            })

    def name_get(self):

        result = []
        for record in self:
            name = record.manifest_ids if record.manifest_ids else f"MF-{record.id}"
            result.append((record.id, name))
        return result



    def write(self, vals):

        try:
            if not self:
                return True


            if 'manual_override' not in self.env.context:
                protected_fields = {'mine_id', 'disposal_site_id', 'sawis_number'}
                if any(field in vals for field in protected_fields):
                    raise UserError("These fields are auto-populated and cannot be manually changed")


            if 'invoice_rel_ids' in vals:
                self.env.cache.invalidate([(self._fields['invoice_ids'], self.ids)])


            return super(Manifest, self.with_context(no_recompute_invoice_ids=True)).write(vals)
        except Exception as e:
            _logger.error("Error writing manifest %s: %s", self.ids, str(e))
            raise
    @api.model
    def create(self, vals):

        if 'customer_id' in vals and vals['customer_id']:

            temp_record = self.new(vals)
            temp_record._onchange_customer_id()


            vals.update({
                'mine_id': temp_record.mine_id.id,
                'sawis_number': temp_record.sawis_number,
                'disposal_site_id': temp_record.disposal_site_id.id,
                'item_code_ids': [(6, 0, temp_record.item_code_ids.ids)]
            })


        required_fields = {
            'mine_id': "Mine is required (automatically set from customer)",
            'sawis_number': "SAWIS Number is required (automatically set from mine)",
            'disposal_site_id': "Disposal Site is required (automatically set from mine)"
        }

        for field, message in required_fields.items():
            if not vals.get(field):
                raise UserError(message)

        return super().create(vals)
