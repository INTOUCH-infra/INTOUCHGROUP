# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models
from werkzeug import urls

class Survey(models.Model):
    _inherit = "survey.survey"

    print_url = fields.Char("Print link", compute="_compute_print_url")
    result_url = fields.Char("Results link", compute="_compute_print_url")
    public_url = fields.Char("Public link", compute="_compute_print_url")

    def _compute_print_url(self):
        """ Computes a public URL for the survey """
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        for survey in self:
            survey.print_url = urls.url_join(
                base_url, "survey/print/%s" % (survey.access_token))
            survey.result_url = urls.url_join(
                base_url, "survey/results/%s" % (survey.id))
            survey.public_url = urls.url_join(base_url,
             "survey/start/%s" % (survey.access_token))

    def _create_answer(self, user=False, partner=False, email=False, test_entry=False, check_attempts=True, **additional_vals):
        """ Main entry point to get a token back or create a new one. This method
        does check for current user access in order to explicitely validate
        security.

          :param user: target user asking for a token; it might be void or a
                       public user in which case an email is welcomed;
          :param email: email of the person asking the token is no user exists;
        """

        partner_id=''
        if partner:
            if len(partner)>1:
                for rec in partner:
                    partner_id=partner_id+str(rec.id)
                partner=self.env['res.partner'].sudo().browse(int(partner_id))

        self.check_access_rights('read')
        self.check_access_rule('read')
        user_inputs = self.env['survey.user_input']
        for survey in self:
            if partner and not user and partner.user_ids:
                user = partner.user_ids[0]

            invite_token = additional_vals.pop('invite_token', False)
            survey._check_answer_creation(user, partner, email, test_entry=test_entry, check_attempts=check_attempts, invite_token=invite_token)
            answer_vals = {
                'survey_id': survey.id,
                'test_entry': test_entry,
                'is_session_answer': survey.session_state in ['ready', 'in_progress']
            }
            if survey.session_state == 'in_progress':
                # if the session is already in progress, the answer skips the 'new' state
                answer_vals.update({
                    'state': 'in_progress',
                    'start_datetime': fields.Datetime.now(),
                })
            if partner:
                answer_vals['partner_id'] = partner.id

            elif user and not user._is_public():
                answer_vals['partner_id'] = user.partner_id.id
                answer_vals['email'] = user.email
                answer_vals['nickname'] = user.name
            else:
                answer_vals['email'] = email
                answer_vals['nickname'] = email

            if invite_token:
                answer_vals['invite_token'] = invite_token
            elif survey.is_attempts_limited and survey.access_mode != 'public':
                # attempts limited: create a new invite_token
                # exception made for 'public' access_mode since the attempts pool is global because answers are
                # created every time the user lands on '/start'
                answer_vals['invite_token'] = self.env['survey.user_input']._generate_invite_token()

            answer_vals.update(additional_vals)
            user_inputs += user_inputs.create(answer_vals)
        for question in self.mapped('question_ids').filtered(
                lambda q: q.question_type == 'char_box' and (q.save_as_email or q.save_as_nickname)):
            for user_input in user_inputs:
                if question.save_as_email and user_input.email:
                    user_input.save_lines(question, user_input.email)
                if question.save_as_nickname and user_input.nickname:
                    user_input.save_lines(question, user_input.nickname)

        return user_inputs
