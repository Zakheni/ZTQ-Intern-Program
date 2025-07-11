{
    'name': 'Zi-Waste User Management',
    'version': '1.0',
    'summary': 'User Management for Zi-Waste',
    'depends': ['base'],
    'data': [
        'security/zw_user_security.xml',
        'security/ir.model.access.csv',
        'views/user_views.xml',

    ],
    'installable': True,
    'application': True,
}