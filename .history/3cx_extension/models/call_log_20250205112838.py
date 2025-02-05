import json
from odoo import http
from odoo.http import request

class CallLogController(http.Controller):
    @http.route('/3cx/logs', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_logs(self, **post):
        data = json.loads(request.httprequest.data)

        # Vérifier si le contact existe déjà
        partner = request.env['res.partner'].sudo().search([('phone', '=', data.get('phone'))], limit=1)

        if not partner:
            partner = request.env['res.partner'].sudo().create({
                'name': data.get('contact_name', 'Unknown'),
                'phone': data.get('phone'),
            })

        # Créer le log d'appel
        request.env['call.log'].sudo().create({
            'partner_id': partner.id,
            'date': data.get('date'),
            'call_type': data.get('call_type'),
            'agent_name': data.get('agent_name'),
            'agent_phone': data.get('agent_phone'),
            'call_details': data.get('details'),
        })

        return {"status": "success", "message": "Log saved successfully"}
