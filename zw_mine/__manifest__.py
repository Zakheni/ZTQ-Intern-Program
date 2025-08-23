{
    'name': 'Waste Mine Management',
    'version': '1.0',
    'summary': 'Mine Management for Zi-Waste',
    'author':'Victor',
    'depends': ['base', 'zw_item_codes','zw_disposal_site'],
    'data': [
        'security/ir.model.access.csv',
        'views/mine_views.xml',
        'views/sequence.xml',
    ],
    'post_init_hook': 'create_missing_locations',
    'installable': True,
    'application': True,
}
