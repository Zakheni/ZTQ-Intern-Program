from odoo import models, fields, api

class ManifestInvoiceRel(models.Model):
    _name = 'waste.manifest.invoice.rel'
    _description = 'Manifest-Invoice Relationship'
    _rec_name = 'display_name'
    _auto = True

    manifest_id = fields.Many2one(
        'waste.manifest',
        string='Manifest',
        required=True,
        ondelete='cascade',
        index=True
    )
    invoice_id = fields.Many2one(
        'waste.invoice',
        string='Invoice',
        required=True,
        ondelete='cascade',
        index=True
    )
    locked = fields.Boolean(string='Locked', default=False)

    _sql_constraints = [
        ('unique_manifest_invoice', 'UNIQUE(manifest_id, invoice_id)',
         'A manifest can only be linked to an invoice once'),
    ]

    @api.depends('manifest_id', 'invoice_id')
    def _compute_display_name(self):
        for rel in self:
            manifest_name = rel.manifest_id.manifest_ids if rel.manifest_id and rel.manifest_id.manifest_ids else 'No Manifest'
            invoice_name = rel.invoice_id.name if rel.invoice_id and rel.invoice_id.name else 'No Invoice'
            rel.display_name = f"{manifest_name} ↔ {invoice_name}"

    def init(self):

        super(ManifestInvoiceRel, self).init()


        self._cr.execute("""
            CREATE INDEX IF NOT EXISTS waste_manifest_invoice_rel_manifest_id_idx 
            ON waste_manifest_invoice_rel (manifest_id)
        """)
        self._cr.execute("""
            CREATE INDEX IF NOT EXISTS waste_manifest_invoice_rel_invoice_id_idx 
            ON waste_manifest_invoice_rel (invoice_id)
        """)