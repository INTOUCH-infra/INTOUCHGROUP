from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    call_log_ids = fields.One2many(
        "res.call.log", "partner_id", string="Call Logs"
    )
