{
    'name': '3CX Extension',
    'version': '1.0',
    'category': 'Custom',
    'summary': 'Extension for 3CX integration',
    'depends': ['base', 'nalios_3cx_full'],  # Ajoute 'nalios_3cx' s'il est requis
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
}
