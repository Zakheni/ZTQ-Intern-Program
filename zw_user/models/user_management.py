from odoo import models, fields, api
from odoo.exceptions import ValidationError
import hashlib

class ResUsers(models.Model):
    _inherit = 'res.users'

    custom_role = fields.Selection([
        ('depot_admin', 'Depot Administrator'),
        ('fleet_controller', 'Fleet Controller'),
        ('finance_admin', 'Finance Administrator'),
        ('driver', 'Driver'),
        ('finance_manager', 'Finance Manager'),
        ('depot_manager', 'Depot Manager')
    ], string='Custom Role')

    def write(self, vals):
        if 'password' in vals:
            vals['password'] = hashlib.sha256(vals['password'].encode()).hexdigest()
        res = super(ResUsers, self).write(vals)
        self.env['audit.log'].create({
            'model_name': 'res.users',
            'record_id': self.id,
            'operation': 'write',
            'user_id': self.env.uid,
            'changes': str(vals)
        })
        return res

class AuditLog(models.Model):
    _name = 'audit.log'
    _description = 'Audit Log'

    model_name = fields.Char(string='Model Name')
    record_id = fields.Integer(string='Record ID')
    operation = fields.Char(string='Operation')
    user_id = fields.Many2one('res.users', string='User')
    changes = fields.Text(string='Changes')
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now)