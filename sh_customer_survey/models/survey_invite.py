# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models, api
import werkzeug

class SurveyInvite(models.TransientModel):
    _inherit = 'survey.invite'

    survey_start_url = fields.Char('Survey URL', compute='_compute_survey_start_url')

    @api.depends('survey_id.access_token')
    def _compute_survey_start_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for invite in self:
            if self.env.context.get('default_survey_start_url'):
                invite.survey_start_url = self.env.context.get('default_survey_start_url')
            else:
                invite.survey_start_url = werkzeug.urls.url_join(base_url, invite.survey_id.get_start_url()) if invite.survey_id else False
