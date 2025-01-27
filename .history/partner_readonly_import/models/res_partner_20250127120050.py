from odoo import models, fields, api

class ContactDataCorrection(models.Model):
    _inherit = 'res.partner'

    # Exemple de champ pour identifier les contacts qui doivent être corrigés
    x_correction_done = fields.Boolean(string='Correction effectuée', default=False)

    @api.model
    def correct_contact_data(self):
        """
        Cette méthode corrige les contacts où le prénom et le nom sont inversés.
        """
        contacts = self.search([('is_company', '=', False), ('correction_done', '=', False)])

        for contact in contacts:
            if contact.first_name and contact.last_name:
                # Inverser les champs prénom et nom
                contact.write({
                    'first_name': contact.last_name,
                    'last_name': contact.first_name,
                    'correction_done': True,
                })

    @api.model
    def set_contacts_read_only(self):
        """
        Cette méthode rend les contacts en lecture seule après importation ou modification.
        """
        contacts = self.search([('is_company', '=', False), ('correction_done', '=', True)])

        for contact in contacts:
            # Rendre les contacts en lecture seule en révoquant les droits d'écriture
            contact.write({
                'read_only': True
            })
