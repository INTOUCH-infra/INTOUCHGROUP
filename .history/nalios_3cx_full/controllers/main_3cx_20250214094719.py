# -*- coding: utf-8 -*-

import base64
import json
import logging
import phonenumbers
from markupsafe import Markup

from odoo import http
from odoo.http import request, Response
from datetime import datetime

_logger = logging.getLogger(__name__)


class Main3CX(http.Controller):
    def _is_3cx_authenticated(self):
        """Checking Authorization header for 3CX Token."""
        try:
            header = request.httprequest.headers.get('Authorization', False)
            if not header:
                return False
            header = header.replace('Basic ', '').strip()
            decoded = base64.b64decode(header).decode("utf-8").replace(':X', '')
            stored_api_token = request.env['ir.config_parameter'].sudo().get_param('3cx.api.token')
            return stored_api_token == decoded
        except Exception as e:
            _logger.error('Error in _is_3cx_authenticated: %s', e)
            return False

    def _bad_request(self):
        return Response(json.dumps({'error': 'Bad Request'}), status=400)

    def _unauthorized(self):
        return Response(json.dumps({'error': 'Unauthorized'}), status=401)

    def _success_with_data(self, data={}):
        return Response(json.dumps(data), status=200)

    def _load_json_data(self):
        return json.loads(request.httprequest.data)

    def _sanitize_number(self, number):
        """Normalize phone numbers to a consistent format."""
        if not number:
            return ""
        try:
            if number.startswith("00"):
                number = "+" + number[2:]
            parsed_number = phonenumbers.parse(number, None)
            formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            return formatted_number
        except phonenumbers.NumberParseException:
            return number.lstrip("0")

    def _partner_data_json(self, partner):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url').rstrip('/')
        return {
            'id': partner.id,
            'name': partner.name,
            'company': partner.parent_id.name if partner.parent_id else 'N/A',
            'email': partner.email,
            'phone': partner.phone,
            'phone_1': partner.phone_1,
            'mobile': partner.mobile,
            'mobile_1': partner.mobile_1,
            'show_url': f"{base_url}/web?#view_type=form&id={partner.id}&model=res.partner"
        }

    def format_date(date_str):
    try:
        # Conversion du format reçu (%d/%m/%Y %H:%M) vers le format attendu (%Y-%m-%d %H:%M:%S)
        date_obj = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
        return date_obj.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        _logger.error(f"Erreur de format de date pour : {date_str}")
        return None  # Retourne None si le format est incorrect


    def _create_call_log(self, data, partner):
        """Create a call log entry."""
        formatted_date = self._format_date(data.get('date', ''))
        formatted_start = self._format_date(data.get('callstart', ''))
        formatted_established = self._format_date(data.get('callestablished', ''))
        formatted_end = self._format_date(data.get('callend', ''))

        request.env['res.call.log'].sudo().create({
            'name': data.get('subject', ''),
            'date': formatted_date,
            'ttype': data.get('type', ''),
            'entitytype': data.get('entitytype', ''),
            'agentname': data.get('agentname', ''),
            'agent': data.get('agent', ''),
            'call_start': formatted_start,
            'call_established': formatted_established,
            'call_end': formatted_end,
            'partner_id': partner.id,
            'duration': data.get('duration', ''),
            'details': data.get(data.get('type', 'no').lower(), '')
        })

    @http.route('/3cx/call/log', methods=["POST"], csrf=False, type="json", auth="public")
    def _3cx_log_call(self):
        """Call log received from 3CX when call is finished."""
        if not self._is_3cx_authenticated():
            return self._unauthorized()
        data = self._load_json_data()
        _logger.info('3CX Call Log called with data %s', data)
        if not data:
            return self._bad_request()
        number = self._sanitize_number(data.get('phone', ''))
        if not number:
            return self._bad_request()
        partner = request.env['res.partner'].sudo().search([
            '|', '|', '|',
            ('mobile_format', 'ilike', number),
            ('mobile_1_format', 'ilike', number),
            ('phone_format', 'ilike', number),
            ('phone_1_format', 'ilike', number)
        ], limit=1)

        if not partner:
            _logger.info('No partner found for number %s', number)
            partner = request.env['res.partner'].sudo().create({
                'name': f'New contact from number: {number}',
                'phone': number
            })

        for p in partner:
            p.message_post(body=self._get_message_data(data), message_type='comment', subtype_xmlid='mail.mt_note')
            self._create_call_log(data, p)
        return self._success_with_data()

