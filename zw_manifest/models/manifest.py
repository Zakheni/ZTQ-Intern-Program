from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Manifest(models.Model):
    _name = 'waste.manifest'
    _description = 'Waste Manifest'

    manifest_id = fields.Char(string='Manifest ID', required=True, default=lambda self: self.env['ir.sequence'].next_by_code('waste.manifest'))
    waste_type_id = fields.Many2one('waste.type', string='Waste Type')
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
    customer_id = fields.Many2one('res.partner', string='Customer')
    mine_id = fields.Many2one('mine.mine', string='Mine')
    disposal_site_id = fields.Many2one('disposal.site', string='Disposal Site')
    driver_id = fields.Many2one('res.users', string='Driver')
    weighbridge_receipt = fields.Binary(string='Weighbridge Receipt')
    safe_disposal_certificate = fields.Binary(string='Safe Disposal Certificate')
    signature_mine = fields.Binary(string='Mine Signature')
    signature_driver = fields.Binary(string='Driver Signature')

    @api.constrains('dt_number', 'waste_type_id')
    def _check_hazardous_compliance(self):
        for record in self:
            if record.waste_type_id.name == 'Hazardous Waste' and not record.dt_number:
                raise ValidationError("DT Number is required for hazardous waste!")

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
