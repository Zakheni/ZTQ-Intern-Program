{
    'name': 'Zi-Waste Asset Management',
    'version': '1.0',
    'summary': 'Asset Management for Zi-Waste',
    'depends': ['base', 'stock', 'fleet', 'maintenance', 'zw_mine','product'],
    'data': [
        'security/ir.model.access.csv',
        'views/asset_views.xml',
        # 'views/menus.xml',
    ],
    'installable': True,
    'application': True,
}