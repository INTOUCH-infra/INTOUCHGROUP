import paramiko
import pandas as pd
import os
import io
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SFTPContactSync(models.Model):
    _name = 'sftp.contact.sync'
    _description = 'Synchronisation des contacts via SFTP'

    name = fields.Char(string="Nom de la configuration", required=True)
    sftp_host = fields.Char(string="Hôte SFTP", required=True)
    sftp_port = fields.Integer(string="Port", default=22)
    sftp_username = fields.Char(string="Nom d'utilisateur", required=True)
    sftp_private_key = fields.Text(string="Clé Privée", required=True)
    sftp_directory = fields.Char(string="Répertoire distant", required=True)
    last_sync = fields.Datetime(string="Dernière synchronisation")
    active = fields.Boolean(string="Actif", default=True)

    def connect_sftp(self):
        """ Établit une connexion SFTP en utilisant une clé privée """
        try:
            transport = paramiko.Transport((self.sftp_host, self.sftp_port))
            # Charger la clé privée depuis le champ (en format string)
            key_file = io.StringIO(self.sftp_private_key)
            private_key = paramiko.RSAKey.from_private_key(key_file)
            transport.connect(username=self.sftp_username, pkey=private_key)
            sftp = paramiko.SFTPClient.from_transport(transport)
            return sftp, transport
        except Exception as e:
            raise UserError(_("Erreur de connexion SFTP : %s") % str(e))

    def fetch_latest_file(self, sftp):
        """ Récupère le dernier fichier CSV/Excel du répertoire SFTP """
        try:
            files = sftp.listdir(self.sftp_directory)
            csv_files = [f for f in files if f.endswith('.csv') or f.endswith('.xlsx')]
            if not csv_files:
                raise UserError(_("Aucun fichier CSV/Excel trouvé dans le répertoire SFTP."))

            csv_files.sort(reverse=True)
            latest_file = csv_files[0]
            local_path = os.path.join('/tmp', latest_file)
            remote_path = os.path.join(self.sftp_directory, latest_file)

            sftp.get(remote_path, local_path)
            return local_path
        except Exception as e:
            raise UserError(_("Erreur lors de la récupération du fichier : %s") % str(e))

    def process_contacts(self):
        """ Lit le fichier récupéré et met à jour/crée des contacts dans Odoo """
        sftp, transport = None, None
        try:
            sftp, transport = self.connect_sftp()
            file_path = self.fetch_latest_file(sftp)

            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            for _, row in df.iterrows():
                contact = self.env['res.partner'].search([('email', '=', row.get('email'))], limit=1)
                if contact:
                    contact.write({
                        'name': row.get('name'),
                        'phone': row.get('phone'),
                        'mobile': row.get('mobile'),
                    })
                else:
                    self.env['res.partner'].create({
                        'name': row.get('name'),
                        'email': row.get('email'),
                        'phone': row.get('phone'),
                        'mobile': row.get('mobile'),
                    })

            self.last_sync = fields.Datetime.now()
        except Exception as e:
            raise UserError(_("Erreur lors du traitement des contacts : %s") % str(e))
        finally:
            if sftp:
                sftp.close()
            if transport:
                transport.close()

    def cron_sync_contacts(self):
        """ Tâche cron pour synchroniser les contacts """
        configs = self.search([('active', '=', True)])
        for config in configs:
            config.process_contacts()
