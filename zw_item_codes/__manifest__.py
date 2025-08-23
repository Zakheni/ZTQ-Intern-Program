{
    'name': 'Waste Item Codes',
    'version': '16.0.1.0.1',
    'summary': 'Item Codes for Zi-Waste Rate Management',
    'author':'Victor',
    'depends': ['base','account'],
    'data': [
        'security/ir.model.access.csv',
        'views/item_code_views.xml',
        'data/item_code_data.xml',

    ],
    'installable': True,
    'application': True,
    'pre_init_hook': 'pre_init_hook',
}
