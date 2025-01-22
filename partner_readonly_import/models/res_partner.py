from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_is_imported = fields.Boolean(string="Imported", default=False)
