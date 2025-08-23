from odoo import models, fields, api
from odoo.exceptions import ValidationError

class DisposalSite(models.Model):
    _name = 'disposal.site'
    _description = 'Waste Disposal Site'

    name = fields.Char(string='Site Name', required=True)
    address = fields.Char(string='Address')
    postal_code = fields.Char(string='Postal Code')
    contact_number = fields.Char(string='Contact Number')
    fax = fields.Char(string='Fax')
    sawis_number = fields.Char(string='SAWIS Number', required=True)





    @api.constrains('sawis_number')
    def _check_unique(self):
        for record in self:
            if self.search([('sawis_number', '=', record.sawis_number), ('id', '!=', record.id)]):
                raise ValidationError("SAWIS Number must be unique!")

