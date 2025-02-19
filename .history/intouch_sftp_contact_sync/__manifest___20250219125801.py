{
    'name': 'SFTP Contact Sync',
    'version': '1.0',
    'summary': 'Synchronisation des contacts via SFTP',
    'description': 'Ce module permet de synchroniser les contacts depuis un serveur SFTP distant.',
    'author': 'Intouch group',
    'website': 'https://www.intouchgroup.net',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/sftp_contact_sync_views.xml',
    ],
    'installable': True,
    'application': True,
    'external_dependencies': {
        'python': ['paramiko', 'pandas'],
    },
}