from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Mine(models.Model):
    _name = 'mine.mine'
    _description = 'Mine Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Mine Name', required=True, tracking=True)
    mine_id = fields.Char(string='Mine Id', required=True,
                          default=lambda self: self.env['ir.sequence'].next_by_code('mine.mine'))
    mine_code = fields.Char(string='Mine Code', required=True,
                            default=lambda self: self.env['ir.sequence'].next_by_code('mine.mine'))


    location_id = fields.Many2one(
        'stock.location',
        string='Mine Location',
        required=True,
        domain=[('usage', '=', 'internal')],
        tracking=True,
        help="Primary location for this mine where bins will be stored"
    )

    sawis_number = fields.Char(string='SAWIS Number', required=True)
    physical_address = fields.Char(string='Physical Address')
    postal_address = fields.Char(string='Postal Address')
    longitude = fields.Float(string='Longitude')
    latitude = fields.Float(string='Latitude')

    waste_collection_area_ids = fields.One2many(
        'waste.collection.area',
        'mine_id',
        string='Waste Collection Areas'
    )
    rate_ids = fields.One2many('mine.rate', 'mine_id', string='Rates')

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        domain="[('vat_number', '!=', False)]",
        help="The customer associated with this mine"
    )

    contact_name = fields.Char(string='Contact Person', related='customer_id.name', readonly=False, store=True)
    contact_number = fields.Char(string='Contact Number', related='customer_id.phone', readonly=False, store=True)
    contact_email = fields.Char(string='Contact Email', related='customer_id.email', readonly=False, store=True)
    vat_number = fields.Char(string='VAT Number', related='customer_id.vat_number', readonly=False, store=True)
    disposal_site_ids = fields.Many2many('disposal.site', string='Disposal Sites')

    @api.model
    def create(self, vals):

        if 'name' in vals and 'location_id' not in vals:
            location = self.env['stock.location'].create({
                'name': vals['name'],
                'usage': 'internal',
                'location_id': self.env.ref('stock.stock_location_locations').id
            })
            vals['location_id'] = location.id
        return super().create(vals)

    def write(self, vals):

        if 'name' in vals:
            for mine in self:
                mine.location_id.write({'name': vals['name']})
        return super().write(vals)

    @api.onchange('name')
    def _onchange_name(self):

        if self.name and not self.location_id:
            self.location_id = self.env['stock.location'].search([
                ('name', '=', self.name),
                ('usage', '=', 'internal')
            ], limit=1)

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id:
            self.update({
                'contact_name': self.customer_id.name,
                'contact_number': self.customer_id.phone,
                'contact_email': self.customer_id.email,
                'vat_number': self.customer_id.vat,
            })

    @api.constrains('mine_code', 'sawis_number')
    def _check_unique(self):
        for record in self:
            if self.search([('mine_code', '=', record.mine_code), ('id', '!=', record.id)]):
                raise ValidationError("Mine Code must be unique!")
            if self.search([('sawis_number', '=', record.sawis_number), ('id', '!=', record.id)]):
                raise ValidationError("SAWIS Number must be unique!")




class WasteCollectionArea(models.Model):
    _name = 'waste.collection.area'
    _description = 'Waste Collection Area'

    name = fields.Char(string='Area Name', required=True)
    mine_id = fields.Many2one('mine.mine', string='Mine', required=True)
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        required=True,
        domain="[('usage', '=', 'internal'), ('id', 'child_of', parent.location_id)]",
        help="Specific location for this collection area within the mine"
    )

    @api.onchange('mine_id')
    def _onchange_mine_id(self):

        if self.mine_id and self.mine_id.location_id:
            self.location_id = self.mine_id.location_id


class MineRate(models.Model):
    _name = 'mine.rate'
    _description = 'Mine Rate'

    mine_id = fields.Many2one('mine.mine', string='Mine', required=True)
    item_code_id = fields.Many2one('item.code', string='Item Code', required=True, domain="[('state', '=', 'approved')]")

    bin_rate = fields.Float(string='Bin Rate')
    km_rate = fields.Float(string='Kilometre Rate')
    load_rate = fields.Float(string='Load Rate')
    fixed_rate = fields.Float(string='Fixed Rate')
    tonnage = fields.Float(string='Tonnage')
    rental_rate = fields.Float(string='Rental Rate')
    labour_cost = fields.Float(string='Labour Cost')
    management_fee = fields.Float(string='Management Fee')
    escalation_rate = fields.Float(string='Escalation Rate (%)')
    discount = fields.Float(string='Discount (%)')
    vat = fields.Float(string='VAT (%)', default=15.0)
    waste_type = fields.Char(string='Waste Type')
    waste_details = fields.Text(string='Waste Details')
    disposal_site_id = fields.Many2one('disposal.site', string='Disposal Site')
    bin_volume_type = fields.Char(string='Bin Volume Type')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')



