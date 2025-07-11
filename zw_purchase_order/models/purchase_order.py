from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _name = 'zi.purchase.order'
    _description = 'Zi-Waste Purchase Order'

    po_number = fields.Char(string='Purchase Order Number', required=True)
    vendor_number = fields.Char(string='Vendor Number')
    mine_id = fields.Many2one('mine.mine', string='Mine', required=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    bin_total = fields.Integer(string='Number of Bins')
    bin_in_use = fields.Integer(string='Bins in Use')
    bin_not_in_use = fields.Integer(string='Bins Not in Use', compute='_compute_bin_not_in_use')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    @api.depends('bin_total', 'bin_in_use')
    def _compute_bin_not_in_use(self):
        for record in self:
            record.bin_not_in_use = record.bin_total - record.bin_in_use

    @api.constrains('po_number')
    def _check_unique(self):
        for record in self:
            if self.search([('po_number', '=', record.po_number), ('id', '!=', record.id)]):
                raise ValidationError("Purchase Order Number must be unique!")
