# -*- coding: utf-8 -*-
from odoo import api, fields, models

CHANNEL_LIST = [("letter", "Letter"), ("email", "Email"), ("phone", "Phone"), ('debt collector', 'Debt collector')]

class CreditControlPolicyLevel(models.Model):
    _inherit = "credit.control.policy.level"
    
    channel = fields.Selection(selection=CHANNEL_LIST, required=True)
 

