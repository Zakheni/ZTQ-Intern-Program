{
    'name': 'Waste Invoice Management',
    'version': '1.0',
    'summary': 'Invoice Management for Zi-Waste',
    'author':'Victor',
    'depends': ['base', 'account', 'zw_manifest', 'zw_mine'],
    'data': [
        'security/ir.model.access.csv',
        'views/invoice_views.xml',
        'security/security.xml',
        'data/ir_sequence_data.xml',
    ],
    'installable': True,
    'application': True,
}