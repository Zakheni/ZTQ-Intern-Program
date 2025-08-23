{
    'name': 'Purchase Order Management',
    'version': '1.0',
    'summary': 'Purchase Order Management for Zi-Waste',
    'depends': ['base', 'zw_item_codes','zw_disposal_site','zw_asset','zw_mine'],
    'depends': ['base', 'zw_item_codes','zw_disposal_site','zw_asset','zw_mine'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
        'views/sequence.xml',
    ],
    'installable': True,
    'application': True,
}