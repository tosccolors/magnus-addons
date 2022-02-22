# -*- coding: utf-8 -*-
from odoo import api, fields, models

    

class CreditControlPolicyLevel(models.Model):
    _inherit = "credit.control.policy.level"
    
    channel = fields.Selection(selection_add=[('phone','Phone'),('debt collector', 'Debt collector')]) 
 

