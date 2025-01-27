{
    'name': 'Contact Data Correction',
    'version': '1.0',
    'category': 'Custom',
    'author': 'Intouch',
    'website': 'https://www.intouchgroup.net',
    'summary': 'Module pour corriger les données de contacts et les rendre en lecture seule.',
    'depends': ['base', 'contacts'],
    'data': [
        'views/contact_data_correction_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
