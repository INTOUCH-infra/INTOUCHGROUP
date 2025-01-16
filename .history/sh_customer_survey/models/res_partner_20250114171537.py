# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models, _
from odoo.exceptions import UserError
import werkzeug

class Partner(models.Model):
    _inherit = "res.partner"

    survey_id = fields.Many2one('survey.survey', string='Survey Form')
    survey_user_input_ids = fields.Many2many(
        "survey.user_input", string="Survey User Input Ids", readonly=True, compute='_compute_get_survey_user_input_ids')
    survey_token = fields.Char("survey_token")

    def _compute_get_survey_user_input_ids(self):
        for rec in self:
            rec.survey_user_input_ids = []
            survey_user_input_details = self.env['survey.user_input'].sudo().search(
                [('partner_id', '=', rec.id)], order="id desc")
            if survey_user_input_details:
                rec.survey_user_input_ids = survey_user_input_details.ids

    #Test Survey
    def action_view_survey(self, answer=None):
        if not self.survey_id:
            raise UserError(_("Please Select Survey Form."))

        self.ensure_one()
        url = '%s?%s' % (self.survey_id.get_start_url(), werkzeug.urls.url_encode({'answer_token': answer and answer.access_token or None}))
        url += 'partner_id='+str(self.id)
        return {
            'type': 'ir.actions.act_url',
            'name': "Start Survey",
            'target': 'self',
            'url': url,
        }


    def action_view_print_survey(self):
        if not self.survey_id:
            raise UserError(_("Please Select Survey Form."))
        return {
            'type': 'ir.actions.act_url',
            'name': "Print Survey",
            'target': 'self',
            'url':  self.survey_id.with_context(relative_url=True).print_url
        }

    #Share and invite by email Survey
    def action_view_send_survey(self):
        if not self.survey_id:
            raise UserError(_("Please Select Survey Form."))

        if (not self.survey_id.page_ids and self.survey_id.questions_layout == 'page_per_section') or not self.survey_id.question_ids:
            raise UserError(
                _('You cannot send an invitation for a survey that has no questions.'))

        template = self.env.ref(
            'survey.mail_template_user_input_invite', raise_if_not_found=False)

        local_context = dict(
            self.env.context,
            default_survey_id=self.survey_id.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            notif_layout='mail.mail_notification_light',
            default_survey_start_url=self.survey_id.with_context(
                relative_url=True).public_url + "?partner_id="+str(self.id),
            default_partner_ids=[(6, 0, [self.id])]
        )
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'survey.invite',
            'target': 'new',
            'context': local_context,
        }

    #View Result Survey
    def action_view_result_survey(self):
        if not self.survey_id:
            raise UserError(_("Please Select Survey Form."))
        return {
            'type': 'ir.actions.act_url',
            'name': "Results of the Survey",
            'target': 'self',
            'url': self.survey_id.with_context(relative_url=True).result_url
        }
