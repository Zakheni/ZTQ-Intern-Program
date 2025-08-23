{
    'name': 'Waste Manifest',

    'summary': 'Waste Manifest Management for Zi-Waste',
    'author':'Victor',
    'depends': ['base', 'zw_customer', 'zw_mine', 'zw_disposal_site', 'zw_user','zw_item_codes'],
    'data': [
        'security/ir.model.access.csv',
        'security/zw_manifest_security.xml',
        'views/manifest_views.xml',

        'views/schedule_views.xml',
        'data/manifest_data.xml',
        'data/schedule_data.xml',
        'data/waste_types_data.xml',


    ],
    'version': '16.0.1.0',


    'installable': True,
    'application': True,
}