{
    'name': 'Zi-Waste Invoice Management',
    'version': '1.0',
    'summary': 'Invoice Management for Zi-Waste',
    'depends': ['base', 'account', 'zw_manifest', 'zw_mine'],
    'data': [
        'security/ir.model.access.csv',
        'views/invoice_views.xml',
        # 'views/menus.xml',
    ],
    'installable': True,
    'application': True,
}