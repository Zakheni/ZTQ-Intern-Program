from odoo import models, fields, api
from odoo.exceptions import ValidationError

class WasteSchedule(models.Model):
    _name = 'waste.schedule'
    _description = 'Waste Collection/Disposal Schedule'

    name = fields.Char(string='Schedule ID', default=lambda self: self.env['ir.sequence'].next_by_code('waste.schedule'))
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    mine_id = fields.Many2one('mine.mine', string='Mine')
    waste_type_id = fields.Many2one('waste.type', string='Waste Type', required=True)
    scheduled_date = fields.Date(string='Scheduled Date', required=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='pending')
    manifest_id = fields.Many2one('waste.manifest', string='Manifest')
    notes = fields.Text(string='Notes')

    @api.constrains('scheduled_date')
    def _check_date(self):
        for record in self:
            if record.scheduled_date < fields.Date.today():
                raise ValidationError("Scheduled date cannot be in the past!")

    def action_confirm(self):
        self.status = 'confirmed'
        self.env['audit.log'].create({
            'model_name': 'waste.schedule',
            'record_id': self.id,
            'operation': 'status_change',
            'user_id': self.env.uid,
            'changes': f"Status changed to {self.status}"
        })