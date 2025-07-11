from email.policy import default

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    manifest_id = fields.Many2one('waste.manifest', string='Manifest')
    mine_id = fields.Many2one('mine.mine', string='Mine')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        required=True,
        default='draft',
        ondelete={'draft': 'set default', 'posted': 'cascade', 'cancel': 'cascade'},
    )

    @api.model
    def create_from_manifest(self, manifest):
        if manifest.status != 'authorized':
            raise ValidationError("Manifest must be authorized to generate invoice!")
        invoice = self.create({
            'move_type': 'out_invoice',
            'partner_id': manifest.customer_id.id,
            'manifest_id': manifest.id,
            'mine_id': manifest.mine_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': f"Waste Disposal - {manifest.waste_type_id.name}",
                'quantity': manifest.tonnage,
                'price_unit': self._get_rate(manifest),
                'tax_ids': [(6, 0, [self.env['account.tax'].search([('amount', '=', 15)], limit=1).id])]
            })],
            'state': 'pro_forma'
        })
        self.env['audit.log'].create({
            'model_name': 'account.move',
            'record_id': invoice.id,
            'operation': 'create',
            'user_id': self.env.uid,
            'changes': f"Invoice created for manifest {manifest.manifest_id}"
        })
        return invoice

    def _get_rate(self, manifest):
        rate = self.env['mine.rate'].search([
            ('mine_id', '=', manifest.mine_id.id),
            ('waste_type', '=', manifest.waste_type_id.name),
            ('rate_type', '=', 'disposal')
        ], limit=1)
        return rate.fixed_rate or 100.0  # Placeholder rate

    def action_authorize(self):
        self.state = 'posted'
        self.env['audit.log'].create({
            'model_name': 'account.move',
            'record_id': self.id,
            'operation': 'authorize',
            'user_id': self.env.uid,
            'changes': "Invoice authorized"
        })

    def action_reject(self):
        self.state = 'rejected'
        self.env['audit.log'].create({
            'model_name': 'account.move',
            'record_id': self.id,
            'operation': 'reject',
            'user_id': self.env.uid,
            'changes': "Invoice rejected"
        })

    def action_fix(self):
        self.state = 'pro_forma'
        self.env['audit.log'].create({
            'model_name': 'account.move',
            'record_id': self.id,
            'operation': 'fix',
            'user_id': self.env.uid,
            'changes': "Invoice fixed"
        })
