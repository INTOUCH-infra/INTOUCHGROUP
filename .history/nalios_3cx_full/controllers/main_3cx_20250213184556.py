from datetime import datetime

class Main3CX(http.Controller):
    def _is_3cx_authenticated(self):
        """Checking Authorization header for 3CX Token."""
        try:
            header = request.httprequest.headers.get('Authorization', False)
            if not header:
                return False
            header = header.replace('Basic ', '').strip()
            decoded = base64.b64decode(header)
            decoded = decoded.decode("utf-8").replace(':X', '')
            stored_api_token = request.env['ir.config_parameter'].sudo().get_param('3cx.api.token')
            if stored_api_token != decoded:
                return False
            return True
        except Exception as e:
            _logger.info('Could not get Basic Authorization header. View error below for more information :')
            _logger.info(e)
            return False

    def _bad_request(self):
        _logger.info('Bad request!')
        return Response(json.dumps({'error': 'Bad Request'}), status=400)

    def _unauthorized(self):
        _logger.info('Unauthorized request!')
        return Response(json.dumps({'error': 'Unauthorized'}), status=401)

    def _success_with_data(self, data={}):
        return Response(json.dumps(data), status=200)

    def _load_json_data(self):
        return json.loads(request.httprequest.data)

    def _sanitize_number(self, number):
        """Sanitize phone numbers to ensure a consistent format."""
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
            'company': partner.parent_id and partner.parent_id.name or 'N/A',
            'email': partner.email,
            'phone': partner.phone,
            'phone_1': partner.phone_1,
            'mobile': partner.mobile,
            'mobile_1': partner.mobile_1,
            'show_url': base_url + '/web?#view_type=form&id=%s&model=res.partner' % (partner.id,)
        }

    def _validate_and_format_date(self, date_str):
        """Validate and format date strings to ensure they follow a consistent format."""
        if not date_str:
            return ""
        try:
            # Try to parse the date using a known format
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            # Convert it to ISO 8601 format (if needed)
            return parsed_date.isoformat()
        except ValueError:
            _logger.error(f"Invalid date format: {date_str}. Expected format: YYYY-MM-DD HH:MM:SS")
            return ""

    def _get_livechat_data(self, data):
        msg = "Subject: %s<br/>" % data.get('subject', '')
        msg += "Date: %s<br/>" % self._validate_and_format_date(data.get('date', ''))
        msg += "Duration: %s<br/>" % data.get('duration', '')
        msg += "Agent Name: %s<br/>" % data.get('agentname', '')
        msg += "Agent Phone: %s<br/>" % data.get('agent', '')        
        msg += "Messages: <br/>%s" % data.get('messages', '').replace('\n', '<br/>')
        return Markup(msg)

    def _get_message_data(self, data):
        msg = "Subject: %s<br/>" % data.get('subject', '')
        msg += "Date: %s<br/>" % self._validate_and_format_date(data.get('date', ''))
        msg += "Call Type: %s<br/>" % data.get('type', '')
        msg += "Entity: %s<br/>" % data.get('entitytype', '')
        msg += "Agent Name: %s<br/>" % data.get('agentname', '')
        msg += "Agent Phone: %s<br/>" % data.get('agent', '')
        msg += "Details: %s" % data.get(data.get('type', 'no').lower(), '')
        return Markup(msg)

    @http.route('/3cx/call/log', methods=["POST"], csrf=False, type="json", auth="public")
    def _3cx_log_call(self):
        """Call log received from 3CX when call is finished."""
        if not self._is_3cx_authenticated():
            return self._unauthorized()
        data = self._load_json_data()
        _logger.info('3CX Call Log called with data %s' % data)
        if not data:
            return self._bad_request()
        number = data.get('phone', False)
        if not number:
            return self._bad_request()
        number = self._sanitize_number(number)
        if not (partner := request.env['res.partner'].sudo().search(['|', '|', '|', ('mobile_format', 'ilike', str(number)), ('mobile_1_format', 'ilike', str(number)), ('phone_format', 'ilike', str(number)), ('phone_1_format', 'ilike', str(number))], limit=1)):
            _logger.info('No partner found for number %s' % number)
            partner = request.env['res.partner'].sudo().create({
                'name': 'New contact from number : ' + number,
                'phone': number
            })
        for p in partner:
            p.message_post(body=self._get_message_data(data), message_type='comment', subtype_xmlid='mail.mt_note')
            self._create_call_log(data, p)
        return self._success_with_data()

    def _create_call_log(self, data, partner):
        request.env['res.call.log'].sudo().create({
            'name': data.get('subject', ''),
            'date': self._validate_and_format_date(data.get('date', '')),
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
        """Chat log received from 3CX when a Chat is ticked as 'Dealt With'"""
        if not self._is_3cx_authenticated():
            return self._unauthorized()
        data = self._load_json_data()
        _logger.info('3CX Chat Create called with data %s' % data)
        if not data:
            return self._bad_request()
        email = data.get('email', False)
        if not email:
            return self._bad_request()
        if not (partner := request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)):
            partner = request.env['res.partner'].sudo().create({
                'name': data.get('name', 'New from Livechat Email : %s' % email),
                'email': email,
                'mobile': data.get('number', ''),
            })
        livechat_body = self._get_livechat_data(data)
        for p in partner:
            p.message_post(body=livechat_body, message_type='comment', subtype_xmlid='mail.mt_note')
        return self._success_with_data()
