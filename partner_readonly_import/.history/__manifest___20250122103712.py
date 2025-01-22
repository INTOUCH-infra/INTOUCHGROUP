{
    'name': "Partner Readonly on Import",
    'version': '1.0',
    'summary': "Rendre les contacts en lecture seule après importation",
    'author': "Babacar NIANG",
    'website': "https://intouchgroup.net",
    'category': 'Contacts',
    'depends': ['base'],
    'data': [
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
