{
    'name': 'Intouch SFTP Contact Sync',
    'version': '1.0',
    'summary': 'Synchronisation automatique des contacts via SFTP',
    'description': """
        Ce module permet la synchronisation automatique des contacts d'Intouch 
        à partir d'un serveur SFTP en important un fichier CSV ou Excel.
    """,
    'author': 'Babacar NIANG',
    'website': 'https://www.intouchgroup.net',
    'category': 'Tools',
    'license': 'LGPL-3',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/sftp_contact_views.xml',
        'data/sftp_cron.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}