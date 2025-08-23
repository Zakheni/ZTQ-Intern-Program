{
    'name': 'Waste Customer Management',
    'version': '1.0',
    'summary': 'Customer Management for Zi-Waste',
    'author':'Victor',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/customer_views.xml',

    ],
    'installable': True,
    'application': True,
}