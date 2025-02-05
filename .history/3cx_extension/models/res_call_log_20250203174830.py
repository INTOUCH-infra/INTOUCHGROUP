from odoo import models, fields

class ResCallLog(models.Model):
    _inherit = 'res.call.log'

    def _create_call_log(self, data, partner):
        date_string = data.get('date', '')
        parsed_date = self._parse_date(date_string) if date_string else fields.Datetime.now()

        log_entry = self.sudo().create({
            'name': data.get('subject', ''),
            'date': parsed_date,
            'ttype': data.get('type', ''),
            'entitytype': data.get('entitytype', ''),
            'agentname': data.get('agentname', ''),
            'agent': data.get('agent', ''),
            'call_start': data.get('callstart', ''),
            'call_established': data.get('callestablished', ''),
            'call_end': data.get('callend', ''),
            'duration': data.get('duration', ''),
            'details': data.get(data.get('type', 'no').lower(), ''),
            'partner_id': partner.id,
        })
        return log_entry
