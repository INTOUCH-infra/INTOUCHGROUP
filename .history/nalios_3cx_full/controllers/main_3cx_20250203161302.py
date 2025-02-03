# -*- coding: utf-8 -*- 

import base64
import json
import logging
import phonenumbers
from datetime import datetime
from markupsafe import Markup

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

class Main3CX(http.Controller):

    def _is_3cx_authenticated(self):
        """Vérifie l'en-tête Authorization pour le token 3CX."""
        try:
            header = request.httprequest.headers.get('Authorization', False)
            if not header:
                return False
            header = header.replace('Basic ', '').strip()
            decoded = base64.b64decode(header).decode("utf-8").replace(':X', '')
            stored_api_token = request.env['ir.config_parameter'].sudo().get_param('3cx.api.token')
            return stored_api_token == decoded
        except Exception as e:
            _logger.error('Erreur lors de la récupération de l\'en-tête Authorization: %s', e)
            return False

    def _bad_request(self):
        _logger.info('Requête incorrecte !')
        return Response(json.dumps({'error': 'Bad Request'}), status=400)

    def _unauthorized(self):
        _logger.info('Requête non autorisée !')
        return Response(json.dumps({'error': 'Unauthorized'}), status=401)

    def _success_with_data(self, data={}):
        return Response(json.dumps(data), status=200)

    def _load_json_data(self):
        return json.loads(request.httprequest.data)

    def _sanitize_number(self, number):
        """
        Normalise et formate le numéro de téléphone.
        """
        if not number:
            return ""
        try:
            if number.startswith("00"):
                number = "+" + number[2:]
            parsed_number = phonenumbers.parse(number, None)
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            return number.lstrip("0")

    def _parse_date(self, date_string):
        """Parse et convertit la chaîne de date en objet datetime."""
        _logger.info(f"Essai de parsing de la date: {date_string}")
        date_formats = ["%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S"]
        for fmt in date_formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        _logger.info(f"Format de date invalide pour {date_string}")
        return None

    def _partner_data_json(self, partner):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url').rstrip('/')
        return {
            'id': partner.id,
            'name': partner.name,
            'company': partner.parent_id and partner.parent_id.name or 'N/A',
            'email': partner.email,
            'phone': partner.phone,
            'phone_1': partner.phone_1,
            'mobile': partner.mobile,
            'mobile_1': partner.mobile_1,
            'show_url': base_url + '/web?#view_type=form&id=%s&model=res.partner' % (partner.id,)
        }

    def _get_livechat_data(self, data):
        msg = "Sujet: %s<br/>" % data.get('subject', '')
        msg += "Date: %s<br/>" % data.get('date', '')
        msg += "Durée: %s<br/>" % data.get('duration', '')
        msg += "Nom de l'agent: %s<br/>" % data.get('agentname', '')
        msg += "Téléphone de l'agent: %s<br/>" % data.get('agent', '')        
        msg += "Messages: <br/>%s" % data.get('messages', '').replace('\n', '<br/>')
        return Markup(msg)

    def _get_message_data(self, data):
        msg = "Sujet: %s<br/>" % data.get('subject', '')
        msg += "Date: %s<br/>" % data.get('date')
        msg += "Type d'appel: %s<br/>" % data.get('type', '')
        msg += "Entité: %s<br/>" % data.get('entitytype', '')
        msg += "Nom de l'agent: %s<br/>" % data.get('agentname', '')
        msg += "Téléphone de l'agent: %s<br/>" % data.get('agent', '')
        msg += "Détails: %s" % data.get(data.get('type', 'no').lower(), '')
        return Markup(msg)

    @http.route('/3cx/search/email/<string:email>', methods=["GET"], csrf=False, type="http", auth="public")
    def search_3cx_email(self, email):
        """Recherche un partenaire Odoo avec l'email donné."""
        if not self._is_3cx_authenticated():
            return self._unauthorized()
        _logger.info('Recherche Email 3CX avec l\'email %s' % email)
        if not email:
            return self._bad_request()
        partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
        if not partner:
            partner = request.env['res.partner'].sudo().create({
                'name': 'Nouvel email: ' + email,
                'email': email,
            })
        return self._success_with_data(self._partner_data_json(partner))

    @http.route('/3cx/search/number/<string:number>/<string:ttype>', methods=["GET"], csrf=False, type="http", auth="public")
    def search_3cx_number(self, number, ttype):
        """Recherche un partenaire Odoo avec le numéro donné."""
        if not self._is_3cx_authenticated():
            return self._unauthorized()
        if not number:
            return self._bad_request()
        sanitized_number = self._sanitize_number(number)
        _logger.info('Numéro normalisé: %s' % sanitized_number)
        partner = request.env['res.partner'].sudo().search([ 
            '|', '|', '|', 
            ('mobile_format', 'ilike', str(sanitized_number)),
            ('mobile_1_format', 'ilike', str(sanitized_number)),
            ('phone_format', 'ilike', str(sanitized_number)),
            ('phone_1_format', 'ilike', str(sanitized_number))
        ], limit=1)
        if not partner:
            partner = request.env['res.partner'].sudo().create({
                'name': 'Nouveau contact à partir du numéro: ' + sanitized_number,
                'phone': sanitized_number
            })
        return self._success_with_data(self._partner_data_json(partner))

    @http.route('/3cx/call/log', methods=["POST"], csrf=False, type="json", auth="public")
    def _3cx_log_call(self):
        """Log d'appel reçu de 3CX après qu'un appel est terminé."""
        if not self._is_3cx_authenticated():
            return self._unauthorized()
        data = self._load_json_data()
        _logger.info('Log d\'appel 3CX reçu avec les données: %s' % data)
        if not data:
            return self._bad_request()
        number = data.get('phone', False)
        if not number:
            return self._bad_request()
        sanitized_number = self._sanitize_number(number)
        partner = request.env['res.partner'].sudo().search([
            '|', '|', '|', 
            ('mobile_format', 'ilike', str(sanitized_number)),
            ('mobile_1_format', 'ilike', str(sanitized_number)),
            ('phone_format', 'ilike', str(sanitized_number)),
            ('phone_1_format', 'ilike', str(sanitized_number))
        ], limit=1)
        if not partner:
            _logger.info('Aucun partenaire trouvé pour le numéro %s' % sanitized_number)
            partner = request.env['res.partner'].sudo().create({
                'name': 'Nouveau contact à partir du numéro: ' + sanitized_number,
                'phone': sanitized_number
            })
        for p in partner:
            p.message_post(body=self._get_message_data(data), message_type='comment', subtype_xmlid='mail.mt_note')
            self._create_call_log(data, p)
        return self._success_with_data()

    def _create_call_log(self, data, partner):
        date_string = data.get('date', '')
        if not date_string:
            _logger.warning("La date est manquante dans les données de l'appel.")
        parsed_date = self._parse_date(date_string)
        if parsed_date is None:
            _logger.warning(f"Erreur lors du parsing de la date: {date_string}. Utilisation de la date actuelle.")
            parsed_date = datetime.now()  # Utilisation de la date actuelle si la conversion échoue
        request.env['res.call.log'].sudo().create({
            'name': data.get('subject', ''),
            'date': parsed_date,  # Assurez-vous que la date est bien au format datetime
            'ttype': data.get('type', ''),
            'entitytype': data.get('entitytype', ''),
            'agentname': data.get('agentname', ''),
            'agent': data.get('agent', ''),
            'call_start': data.get('callstart', ''),
            'call_established': data.get('callestablished', ''),
            'call_end': data.get('callend', ''),
            'partner_id': partner.id,
            'duration': data.get('duration', ''),
            'details': data.get(data.get('type', 'no').lower(), '')
        })

    @http.route('/3cx/chat/create', methods=["POST"], csrf=False, type="json", auth="public")
    def _3cx_create_chat(self):
        """Création de chat reçue de 3CX lorsqu'un chat est marqué comme 'Traité'."""
        if not self._is_3cx_authenticated():
            return self._unauthorized()
        data = self._load_json_data()
        _logger.info('Données de chat 3CX : %s' % data)
        if not data:
            return self._bad_request()
        return self._success_with_data(self._get_livechat_data(data))
