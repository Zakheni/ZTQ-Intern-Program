{
    'name': 'Zi-Waste Customer Management',
    'version': '1.0',
    'summary': 'Customer Management for Zi-Waste',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/customer_views.xml',
        # 'views/menus.xml',
    ],
    'installable': True,
    'application': True,
}