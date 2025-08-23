from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ItemCode(models.Model):
    _name = 'item.code'
    _description = 'Item Code'
    _rec_name = 'display_name'
    _order = 'code'

    STANDARD_CODES = [
        ('TRN-KM', 'Transport - Per Kilometer (TRN-KM)'),
        ('TRN-LOAD', 'Transport - Per Load (TRN-LOAD)'),
        ('DSP-TON', 'Disposal - Per Ton (DSP-TON)'),
        ('RNT-BIN', 'Rental - Per Bin (RNT-BIN)'),
        ('LBR-HOUR', 'Labour - Per Hour (LBR-HOUR)'),
        ('MGT-FEE', 'Management - Fixed Fee (MGT-FEE)'),
        ('other', 'Other (Custom Code)')
    ]

    # Basic Information
    code = fields.Selection(
        selection=STANDARD_CODES,
        string='Item Code',
        required=True,
        default='other'
    )
    custom_code = fields.Char(string='Custom Code', compute='_compute_custom_code', store=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

    # Rate Information
    rate_type = fields.Selection([
        ('transport', 'Transport'),
        ('disposal', 'Disposal'),
        ('rental', 'Rental'),
        ('labour', 'Labour'),
        ('management', 'Management')
    ], string='Rate Type', required=True)

    unit = fields.Char(string='Unit', required=True)
    base_rate = fields.Float(string='Base Rate', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=False
    )


    escalation_rate = fields.Float(string='Escalation Rate (%)', default=0.0)
    discount = fields.Float(string='Discount (%)', default=0.0)
    vat = fields.Float(string='VAT (%)', default=15.0)


    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved')
    ], string='Status', default='draft', readonly=True)
    color = fields.Integer(string='Color Index', default=0)


    bin_rate = fields.Float(string='Bin Rate')
    km_rate = fields.Float(string='Kilometre Rate')
    load_rate = fields.Float(string='Load Rate')
    fixed_rate = fields.Float(string='Fixed Rate')


    tonnage = fields.Float(string='Tonnage')
    waste_type = fields.Char(string='Waste Type')
    waste_details = fields.Text(string='Waste Details')
    disposal_site_id = fields.Many2one('disposal.site', string='Disposal Site')


    rental_rate = fields.Float(string='Rental Rate')
    bin_volume_type = fields.Char(string='Bin Volume Type')


    labour_cost = fields.Float(string='Labour Cost')
    quantity = fields.Float(string='Quantity')


    management_fee = fields.Float(string='Management Fee')


    @api.depends('code')
    def _compute_custom_code(self):
        for record in self:
            if record.code == 'other':
                record.custom_code = False
            else:
                record.custom_code = record.code

    @api.depends('code', 'description')
    def _compute_display_name(self):
        for record in self:
            name_parts = [record.code if record.code != 'other' else "Custom"]
            if record.description:
                name_parts.append(record.description[:30] + (record.description[30:] and '...'))
            record.display_name = ' - '.join(name_parts)


    @api.constrains('code', 'rate_type')
    def _check_rate_uniqueness(self):
        for record in self:
            if self.search_count([
                ('code', '=', record.code),
                ('rate_type', '=', record.rate_type),
                ('id', '!=', record.id)
            ]) > 0:
                raise ValidationError(
                    "A rate with this code and type already exists. "
                    "Please use a different code or rate type."
                )


    @api.onchange('code')
    def _onchange_code(self):
        if self.code:
            code_map = {
                'TRN-KM': {'rate_type': 'transport', 'unit': 'km'},
                'TRN-LOAD': {'rate_type': 'transport', 'unit': 'load'},
                'DSP-TON': {'rate_type': 'disposal', 'unit': 'ton'},
                'RNT-BIN': {'rate_type': 'rental', 'unit': 'bin'},
                'LBR-HOUR': {'rate_type': 'labour', 'unit': 'hour'},
                'MGT-FEE': {'rate_type': 'management', 'unit': 'fee'}
            }

            if self.code in code_map:
                mapping = code_map[self.code]
                self.rate_type = mapping['rate_type']
                self.unit = mapping['unit']

                desc_map = {
                    'TRN-KM': 'Transport per kilometer',
                    'TRN-LOAD': 'Transport per load',
                    'DSP-TON': 'Disposal per ton',
                    'RNT-BIN': 'Rental per bin',
                    'LBR-HOUR': 'Labour per hour',
                    'MGT-FEE': 'Management fee'
                }
                self.description = desc_map.get(self.code, '')


    def action_approve(self):
        for record in self:
            if record.state != 'approved':
                record.state = 'approved'
                record.color = 10  # Green
                self.env['audit.log'].create({
                    'model_name': 'item.code',
                    'record_id': record.id,
                    'operation': 'approve',
                    'user_id': self.env.uid,
                    'changes': f"Item code approved - {record.display_name}"
                })


    def get_rate(self, code, rate_type):

        return self.search([
            ('code', '=', code),
            ('rate_type', '=', rate_type),
            ('state', '=', 'approved')
        ], limit=1)