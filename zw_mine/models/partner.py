from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    mine_ids = fields.One2many(
        comodel_name='mine.mine',
        inverse_name='customer_id',
        string='Mines',
        compute='_compute_mine_ids',
        store=False
    )

    def _compute_mine_ids(self):
        for partner in self:
            partner.mine_ids = self.env['mine.mine'].search([('customer_id', '=', partner.id)])