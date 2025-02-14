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
            header = request.httprequest.headers.get('Authorization', False)
            if not header:
                return False
            header = header.replace('Basic ', '').strip()
            decoded = base64.b64decode(header).decode("utf-8").replace(':X', '')
            stored_api_token = request.env['ir.config_parameter'].sudo().get_param('3cx.api.token')
            return stored_api_token == decoded
        except Exception as e:
            _logger.error('Erreur dans _is_3cx_authenticated: %s', e)
            return False

    def _bad_request(self, message='Bad Request'):
        """Retourne une réponse HTTP 400."""
        return Response(json.dumps({'error': message}), status=400)

    def _unauthorized(self):
        """Retourne une réponse HTTP 401."""
        return Response(json.dumps({'error': 'Unauthorized'}), status=401)

    def _success_with_data(self, data={}):
        """Retourne une réponse HTTP 200 avec des données."""
        return Response(json.dumps(data), status=200)

    def _load_json_data(self):
        """Charge et retourne les données JSON de la requête HTTP."""
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
        Convertit une date du format MM/DD/YYYY HH:MM ou MM/DD/YYYY HH:MM:SS 
        au format YYYY-MM-DD HH:MM:SS. Fixe les secondes à 00 si absentes.
        """
        if not date_str:
            return None

        # Vérifier et compléter la date si elle est en format court
        if len(date_str) == 16:  # Format '02/14/2025 09:09'
            date_str += ":00"
        
        try:
            dt = datetime.strptime(date_str, "%m/%d/%Y %H:%M:%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            _logger.error("Format de date incorrect: %s", date_str)
            return None

    def _create_call_log(self, data, partner):
        """Crée un log d'appel avec les données fournies."""
        formatted_date = self._format_date(data.get('date', ''))
        formatted_start = self._format_date(data.get('callstart', ''))
        formatted_established = self._format_date(data.get('callestablished', ''))
        formatted_end = self._format_date(data.get('callend', ''))

        if not formatted_date or not formatted_start or not formatted_end:
            _logger.error("Date(s) non valides pour le log d'appel.")
            return

        try:
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
            _logger.info("Log d'appel créé pour le partenaire: %s", partner.id)
        except Exception as e:
            _logger.error("Erreur lors de la création du log d'appel: %s", e)

    @http.route('/3cx/call/log', methods=["POST"], csrf=False, type="json", auth="public")
    def _3cx_log_call(self):
        """Réception du log d'appel depuis 3CX à la fin d'un appel."""
        if not self._is_3cx_authenticated():
            return self._unauthorized()

        data = self._load_json_data()
        _logger.info("Données reçues pour le log d'appel 3CX: %s", data)
        
        if not data:
            return self._bad_request('Aucune donnée reçue.')

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
            _logger.info('Aucun partenaire trouvé pour le numéro: %s', number)
            partner = request.env['res.partner'].sudo().create({
                'name': f'Nouveau contact: {number}',
                'phone': number
            })

        for p in partner:
            p.message_post(
                body=f"Appel reçu de {number} avec les données: {data}",
                message_type='comment', 
                subtype_xmlid='mail.mt_note'
            )
            self._create_call_log(data, p)

        return self._success_with_data({'message': "Log d'appel traité avec succès."})
