{
    'name': 'Zi-Waste Disposal Site',
    'version': '1.0',
    'summary': 'Waste Disposal Site Management for Zi-Waste',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/disposal_site_views.xml',

        'data/disposal_site_data.xml',
    ],
    'installable': True,
    'application': True,
}