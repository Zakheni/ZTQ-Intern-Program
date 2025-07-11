{
    'name': 'Zi-Waste Item Codes',
    'version': '1.0',
    'summary': 'Item Codes for Zi-Waste Rate Management',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/item_code_views.xml',
        # 'views/menus.xml',
        'data/item_code_data.xml',

    ],
    'installable': True,
    'application': True,
}