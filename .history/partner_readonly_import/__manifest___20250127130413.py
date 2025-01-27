{
    'name': 'Partner Read-Only Import',
    'version': '1.0',
    'summary': 'Module pour corriger et rendre les contacts en lecture seule',
    'description': 'Ce module ajoute une fonctionnalité pour corriger les contacts et les rendre en lecture seule.',
    'author': 'Intouch group',
    'website': 'http://www.intouchgroup.net',
    'category': 'Contacts',
    'depends': ['base'],
    'data': [
        'views/contact_data_correction_view.xml',
        'models/contact_data_correction.py',
    ],
}