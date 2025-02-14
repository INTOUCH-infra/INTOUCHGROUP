# -*- coding: utf-8 -*-

import base64
import json
import logging
import phonenumbers
from datetime import datetime
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

class Main3CX(http.Controller):

    def _is_3cx_authenticated(self):
        """Vérifie l'authentification du token 3CX dans le header."""
        try:
            header = request.httprequest.headers.get('Authorization', '').replace('Basic ', '').strip()
            if not header:
                return False
            decoded_token = base64.b64decode(header).decode("utf-8").replace(':X', '')
            stored_api_token = request.env['ir.config_parameter'].sudo().get_param('3cx.api.token')
            return stored_api_token == decoded_token
        except Exception as e:
            _logger.error('Erreur dans _is_3cx_authenticated: %s', e)
            return False

    def _bad_request(self, message='Bad Request'):
        return Response(json.dumps({'error': message}), status=400)

    def _unauthorized(self):
        return Response(json.dumps({'error': 'Unauthorized'}), status=401)

    def _success_with_data(self, data={}):
        return Response(json.dumps(data), status=200)

    def _load_json_data(self):
        try:
            return json.loads(request.httprequest.data)
        except json.JSONDecodeError:
            _logger.error('Erreur de décodage JSON')
            return {}

    def _sanitize_number(self, number):
        """Normalise les numéros de téléphone au format E164."""
        if not number:
            return ""
        try:
            if number.startswith("00"):
                number = "+" + number[2:]
            parsed_number = phonenumbers.parse(number, None)
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            _logger.warning('Numéro de téléphone non valide: %s', number)
            return number.lstrip("0")

    def _format_date(self, date_str):
        """
        Convertit une date au format DD/MM/YYYY HH:MM[:SS] ou MM/DD/YYYY HH:MM[:SS]
        en format YYYY-MM-DD HH:MM:SS (format Odoo).
        """
        if not date_str:
            return None
        
        # Ajouter les secondes si elles ne sont pas présentes
        if len(date_str) == 16:
            date_str += ":00"
        
        # Formats de date acceptés
        formats = ["%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%m/%d/%Y %H:%M"]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d %H:%M:%S")  # Format Odoo
            except ValueError:
                continue
        
        _logger.error("Format de date incorrect: %s", date_str)
        return None

    def _create_call_log(self, data, partner):
        """Crée un log d'appel avec les données fournies."""
        date_fields = ['date', 'callstart', 'callestablished', 'callend']
        formatted_dates = {field: self._format_date(data.get(field, '')) for field in date_fields}

        for field in ['callstart', 'callestablished', 'callend']:
            if not formatted_dates[field]:
                formatted_dates[field] = formatted_dates['date']
        
        if None in formatted_dates.values():
            _logger.error("Date(s) non valides pour le log d'appel: %s", formatted_dates)
            return

        try:
            request.env['res.call.log'].sudo().create({
                'name': data.get('subject', ''),
                'date': formatted_dates['date'],
                'ttype': data.get('type', ''),
                'entitytype': data.get('entitytype', ''),
                'agentname': data.get('agentname', ''),
                'agent': data.get('agent', ''),
                'call_start': formatted_dates['callstart'],
                'call_established': formatted_dates['callestablished'],
                'call_end': formatted_dates['callend'],
                'partner_id': partner.id,
                'duration': data.get('duration', ''),
                'details': data.get(data.get('type', 'no').lower(), '')
            })
            _logger.info("Log d'appel créé pour le partenaire: %s", partner.id)
        except Exception as e:
            _logger.error("Erreur lors de la création du log d'appel: %s", e)

    @http.route('/3cx/call/log', methods=["POST"], csrf=False, type="json", auth="public")
    def _3cx_log_call(self):
        """Réception du log d'appel depuis 3CX."""
        if not self._is_3cx_authenticated():
            return self._unauthorized()

        data = self._load_json_data()
        if not data:
            return self._bad_request('Aucune donnée reçue.')
        
        _logger.info("Données reçues pour le log d'appel 3CX: %s", data)
        
        number = self._sanitize_number(data.get('phone', ''))
        if not number:
            return self._bad_request('Numéro de téléphone non fourni.')

        partner = request.env['res.partner'].sudo().search([
            '|', '|', '|',
            ('mobile_format', 'ilike', number),
            ('mobile_1_format', 'ilike', number),
            ('phone_format', 'ilike', number),
            ('phone_1_format', 'ilike', number)
        ], limit=1)

        if not partner:
            partner = request.env['res.partner'].sudo().create({
                'name': f'Nouveau contact: {number}',
                'phone': number
            })
            _logger.info("Nouveau partenaire créé pour le numéro: %s", number)
        
        partner.message_post(
            body=f"Appel reçu de {number} avec les données: {data}",
            message_type='comment', 
            subtype_xmlid='mail.mt_note'
        )
        
        self._create_call_log(data, partner)

        return self._success_with_data({'message': "Log d'appel traité avec succès."})