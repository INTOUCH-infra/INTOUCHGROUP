from odoo import models, fields

class ResCallLog(models.Model):
    _name = "res.call.log"
    _description = "Call Log"

    partner_id = fields.Many2one("res.partner", string="Partner", ondelete="cascade")
    call_date = fields.Datetime(string="Call Date", default=fields.Datetime.now)
    call_duration = fields.Integer(string="Call Duration (Seconds)")
    call_notes = fields.Text(string="Notes")
