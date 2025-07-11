from odoo import models, fields,api
from odoo.exceptions import ValidationError

class ItemCode(models.Model):
    _name = 'item.code'
    _description = 'Item Code'

    code = fields.Char(string='Item Code', required=True)
    description = fields.Text(string='Description')
    unit = fields.Char(string='Unit', required=True)
    rate_type = fields.Selection([
        ('transport', 'Transport'),
        ('disposal', 'Disposal'),
        ('rental', 'Rental'),
        ('labour', 'Labour'),
        ('management', 'Management')
    ], string='Rate Type', required=True)
    end_date = fields.Date(string='End Date')

    @api.constrains('code')
    def _check_unique(self):
        for record in self:
            if self.search([('code', '=', record.code), ('id', '!=', record.id)]):
                raise ValidationError("Item Code must be unique!")