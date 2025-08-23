from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_id = fields.Many2one('res.company', string='Company')
    vat_number = fields.Char(string='VAT Number', required=True)
    bank_name = fields.Char(string='Bank Name')
    branch_code = fields.Char(string='Branch Code')
    account_number = fields.Char(string='Account Number')
    account_type = fields.Selection([
        ('savings', 'Savings'),
        ('business', 'Business'),
        ('checking', 'Checking')
    ], string='Account Type')
    contact_person_position = fields.Char(string='Job Position')
    second_phone = fields.Char(string='Second Contact Number Number')
    fax_number = fields.Char(string='Fax Number')
    email = fields.Char(string='Email',required=True)


    @api.constrains('vat_number')
    def _check_vat_unique(self):
        for record in self:
            if record.vat_number:
                existing = self.search([('vat_number', '=', record.vat_number), ('id', '!=', record.id)])
                if existing:
                    raise ValidationError("VAT Number must be unique!")

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        self.env['audit.log'].create({
            'model_name': 'res.partner',
            'record_id': self.id,
            'operation': 'write',
            'user_id': self.env.uid,
            'changes': str(vals)
        })
        return res

