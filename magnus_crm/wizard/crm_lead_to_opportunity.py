# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    @api.model
    def default_get(self, fields):
        result = super(Lead2OpportunityPartner, self).default_get(fields)
        result['action'] = 'nothing'
        return result