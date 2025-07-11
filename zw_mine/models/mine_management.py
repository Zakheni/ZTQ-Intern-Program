from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Mine(models.Model):
    _name = 'mine.mine'
    _description = 'Mine Management'

    name = fields.Char(string='Mine Name', required=True)
    vat_number = fields.Char(string='VAT Number')
    mine_code = fields.Char(string='Mine Code', required=True)
    sawis_number = fields.Char(string='SAWIS Number', required=True)
    physical_address = fields.Char(string='Physical Address')
    postal_address = fields.Char(string='Postal Address')
    contact_name = fields.Char(string='Contact Name')
    contact_number = fields.Char(string='Contact Number')
    contact_email = fields.Char(string='Contact Email')
    longitude = fields.Float(string='Longitude')
    latitude = fields.Float(string='Latitude')
    waste_collection_area_ids = fields.One2many('waste.collection.area', 'mine_id', string='Waste Collection Areas')
    rate_ids = fields.One2many('mine.rate', 'mine_id', string='Rates')

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

class MineRate(models.Model):
    _name = 'mine.rate'
    _description = 'Mine Rate'

    name = fields.Char(string='Mine Name', required=True)
    mine_id = fields.Many2one('mine.mine', string='Mine', required=True)
    item_code_id = fields.Many2one('item.code', string='Item Code', required=True)
    rate_type = fields.Selection(related='item_code_id.rate_type', string='Rate Type', readonly=True)
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