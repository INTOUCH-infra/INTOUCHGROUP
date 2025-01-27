from odoo import models, fields, api

class ContactDataCorrection(models.Model):
    _inherit = 'res.partner'

    x_correction_done = fields.Boolean(string='Correction effectuée', default=False)

    @api.multi
    def correct_contact_data(self):
        """
        Cette méthode corrige les contacts où le prénom et le nom sont inversés.
        """
        contacts = self.search([('is_company', '=', False), ('x_correction_done', '=', False)])

        for contact in contacts:
            if contact.first_name and contact.last_name:
                # Inverser les champs prénom et nom
                contact.write({
                    'first_name': contact.last_name,
                    'last_name': contact.first_name,
                    'x_correction_done': True,
                })

    @api.multi
    def set_contacts_read_only(self):
        """
        Cette méthode rend les contacts en lecture seule.
        """
        for contact in self:
            contact.write({'x_correction_done': True})