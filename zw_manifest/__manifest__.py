{
    'name': 'Zi-Waste Manifest',
    'version': '1.0',
    'summary': 'Waste Manifest Management for Zi-Waste',
    'depends': ['base', 'zw_customer', 'zw_mine', 'zw_disposal_site', 'zw_user'],
    'data': [
        'security/ir.model.access.csv',
        'security/zw_manifest_security.xml',
        'views/manifest_views.xml',

        'views/schedule_views.xml',
        'data/manifest_data.xml',
        'data/schedule_data.xml',
    ],
    'installable': True,
    'application': True,
}