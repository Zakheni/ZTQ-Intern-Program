{
    'name': 'Zi-Purchase Order Management',
    'version': '1.0',
    'summary': 'Purchase Order Management for Zi-Waste',
    'depends': ['base', 'zw_item_codes'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
        # 'views/menus.xml',
    ],
    'installable': True,
    'application': True,
}