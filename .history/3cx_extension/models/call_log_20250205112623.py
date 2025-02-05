from odoo import models, fields

class CallLog(models.Model):
    _name = "call.log"
    _description = "3CX Call Logs"

    partner_id = fields.Many2one("res.partner", string="Contact", ondelete="cascade")
    date = fields.Datetime(string="Date")
    call_type = fields.Selection([
        ("inbound", "Inbound"),
        ("outbound", "Outbound")
    ], string="Type d'Appel")
    agent_name = fields.Char(string="Nom de l'Agent")
    agent_phone = fields.Char(string="Téléphone de l'Agent")
    call_details = fields.Text(string="Détails")
