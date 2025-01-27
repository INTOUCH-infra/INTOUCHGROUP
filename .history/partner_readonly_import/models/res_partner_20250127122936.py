from odoo import models, fields, api

class ContactDataCorrection(models.Model):
    _inherit = 'res.partner'

    x_correction_done = fields.Boolean(string='Correction effectuée', default=False)

    @api.model
    def correct_contact_data(self):
        contacts = self.search([('is_company', '=', False), ('x_correction_done', '=', False)])
        for contact in contacts:
            if contact.first_name and contact.last_name:
                contact.write({
                    'first_name': contact.last_name,
                    'last_name': contact.first_name,
                    'x_correction_done': True,
                })

    @api.model
    def set_contacts_read_only(self):
        contacts = self.search([('is_company', '=', False), ('x_correction_done', '=', True)])
        for contact in contacts:
            contact.write({'read_only': True})
