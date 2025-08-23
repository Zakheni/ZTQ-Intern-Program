{
    'name': 'Waste Asset Management',
    'version': '1.0',
    'summary': 'Asset Management for Zi-Waste',
    'depends': ['base', 'stock', 'fleet', 'maintenance', 'zw_mine','product','zw_user'],
    'author':'Victor',
    'data': [
        'security/ir.model.access.csv',
        'views/asset_views.xml',
        'views/sequence.xml',

        'data/product_data.xml',

    ],
    'installable': True,
    'application': True,
}