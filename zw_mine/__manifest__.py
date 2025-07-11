{
    'name': 'Zi-Waste Mine Management',
    'version': '1.0',
    'summary': 'Mine Management for Zi-Waste',
    'depends': ['base', 'zw_item_codes','zw_disposal_site'],
    'data': [
        'security/ir.model.access.csv',
        'views/mine_views.xml',
        # 'views/menus.xml',
    ],
    'installable': True,
    'application': True,
}