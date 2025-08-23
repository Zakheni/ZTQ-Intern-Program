from odoo import models, fields, api


class WasteInvoiceLine(models.Model):
    _name = 'waste.invoice.line'
    _description = 'Waste Invoice Line'
    _order = 'invoice_id, sequence, id'

    invoice_id = fields.Many2one(
        'waste.invoice',
        string='Invoice',
        required=True,
        ondelete='cascade',
        index=True
    )
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one(
        'product.product',
        string='Product'
    )
    name = fields.Text(string='Description', required=True)
    quantity = fields.Float(
        string='Quantity',
        digits='Product Unit of Measure',
        default=1.0
    )
    price_unit = fields.Float(
        string='Unit Price',
        digits='Product Price'
    )
    price_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_amount',
        store=True
    )
    price_tax = fields.Float(
        string='Tax Amount',
        compute='_compute_amount',
        store=True
    )
    price_total = fields.Float(
        string='Total',
        compute='_compute_amount',
        store=True
    )
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes'
    )
    item_code_id = fields.Many2one(
        'item.code',
        string='Service Code'
    )

    @api.depends('quantity', 'price_unit', 'tax_ids')
    def _compute_amount(self):
        for line in self:
            taxes = line.tax_ids.compute_all(
                line.price_unit,
                line.invoice_id.currency_id,
                line.quantity,
                product=line.product_id,
                partner=line.invoice_id.customer_id
            )
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    def _prepare_account_move_line_vals(self, move):
        self.ensure_one()
        return {
            'move_id': move.id,
            'name': self.name,
            'quantity': self.quantity,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.tax_ids.ids)],
            'product_id': self.product_id.id,
            'account_id': self.product_id.property_account_income_id.id or
                          self.product_id.categ_id.property_account_income_categ_id.id
        }