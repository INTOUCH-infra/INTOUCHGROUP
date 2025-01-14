# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models

class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    partner_id = fields.Many2one(
        'res.partner', string='Partner', readonly=False)
    type = fields.Selection([('manually', 'Manually'), ('link', 'Send Through Email')],
                            string='Answer Type', default='manually', required=True, readonly=True)

    def survey_user_input(self):
        return {
            'name': 'Survey User_input',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'survey.user_input',
            'view_id': self.env.ref('survey.survey_user_input_view_form').id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
        }

    def survey_resume_answer(self):
        return {
            'type': 'ir.actions.act_url',
            'name': "Resume Survey",
            'target': 'self',
            'url': '/survey/%s/%s' % (self.survey_id.access_token, self.access_token)
        }

    def survey_view_answers(self):
        """ Open the website page with the survey form """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': "View Answers",
            'target': 'self',
            'url': '/survey/print/%s?answer_token=%s' % (self.survey_id.access_token, self.access_token)
        }
