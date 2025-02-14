# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class CallLog(models.Model):
    _name = 'res.call.log'
    _description = '3CX Call Log'

    name = fields.Char('Call System')
    partner_id = fields.Many2one('res.partner', 'Contact')
    
    # Champ date avec conversion automatique en format M/D/Y HH:MM:SS
    date = fields.Datetime('Date', default=fields.Datetime.now, required=True)
    
    ttype = fields.Char('Call Type')
    entitytype = fields.Char('Entity Type')
    agentname = fields.Char('Agent')
    agent = fields.Char('Agent ext.')

    # Utilisation de fields.Datetime pour une meilleure gestion des dates
    call_start = fields.Datetime('Call Start', default=False)
    call_established = fields.Datetime('Call Established', default=False)
    call_end = fields.Datetime('Call End', default=False)

    duration = fields.Char('Duration')
    details = fields.Char('Details')

    contact_source = fields.Selection([
        ('appel_sortant', 'Appel Sortant'),
        ('appel_entrant', 'Appel Entrant'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('facebook', 'Facebook'),
        ('x', 'X'),
        ('linkedin', 'LinkedIn'),
        ('instagram', 'Instagram'),
        ('application', 'Application Mobile'),
        ('web', 'Application Web'),
        ('office', 'Office / Visite')
    ], string="Contact Source")

    contact_type = fields.Selection([
        ('reclamation', 'Réclamation'),
        ('demande_assistance', 'Demande d\'assistance'),
        ('demande_information', 'Demande d\'information'),
        ('suggestion', 'Suggestion'),
        ('plainte', 'Plainte'),
        ('survey', 'Survey'),
        ('televente', 'Télévente'),
        ('onboarding', 'Onboarding'),
        ('rappel_suivi', 'Rappel / Suivi dossier')
    ], string="Contact Type")

    contact_reason = fields.Selection([
        ('annulation', 'Demande d\'Annulation'),
        ('remboursement', 'Demande de Remboursement'),
        ('info_produit', 'Information Produit'),
        ('comment_ca_marche', 'Comment ça marche'),
        ('assistance_compte', 'Assistance connexion Compte'),
        ('reset_pin', 'Reset Pin'),
        ('deplafonnement_kyc2', 'Déplafonnement Compte KYC2'),
        ('activation_offre', 'Activation Offre'),
        ('formation', 'Formation'),
        ('fraude', 'Fraude')
    ], string="Contact Reason")

    product = fields.Selection([
        ('mytp', 'MYTP'),
        ('aio', 'AIO'),
        ('api_web', 'API Web'),
        ('credit_digital', 'Credit Digital'),
        ('bet', 'BET'),
        ('touch_point', 'Touch Point')
    ], string="Product")

    service = fields.Selection([
        ('assurance', 'Assurance'),
        ('qr', 'QR'),
        ('paiement_marchand', 'Paiement Marchand'),
        ('bulk_paiement', 'Bulk paiement'),
        ('cash_in', 'Cash In'),
        ('cash_out', 'Cash Out'),
        ('transfert', 'Transfert'),
        ('paiement_facture', 'Paiement de facture')
    ], string="Service")

    ticket_number = fields.Char(string="Ticket Number")

    @api.model
    def create(self, vals):
        """ Remplace les chaînes vides par None (NULL) avant de créer l'enregistrement. """
        for field in ['date', 'call_start', 'call_established', 'call_end']:
            if field in vals and not vals[field]:  # Si le champ est une chaîne vide ou False
                vals[field] = None
        return super(CallLog, self).create(vals)

    def write(self, vals):
        """ Remplace les chaînes vides par None (NULL) avant de mettre à jour l'enregistrement. """
        for field in ['date', 'call_start', 'call_established', 'call_end']:
            if field in vals and not vals[field]:
                vals[field] = None
        return super(CallLog, self).write(vals)