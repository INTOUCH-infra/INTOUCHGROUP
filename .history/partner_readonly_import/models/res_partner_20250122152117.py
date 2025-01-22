from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    imported = fields.Boolean(string="Imported", default=False)

    @api.onchange('imported')
    def _onchange_imported(self):
        """Empêcher la modification des champs si le contact est importé."""
        if self.imported:
            for field in self._fields:
                if field not in ('id', 'imported'):
                    self._fields[field].readonly = True
