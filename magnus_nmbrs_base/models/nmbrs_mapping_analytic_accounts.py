from odoo import api, fields, models, _
from zeep import Client, Settings
import datetime
import xml.etree.ElementTree as ET
import os


class MappingNmbrsAnalyticAccount(models.Model):
    _name = "mapping.nmbrs.analytic.account"

    analytic_account_id_nmbrs = fields.Char("NMBRs ID")
    analytic_account_code_nmbrs = fields.Char("NMBRs Code")
    analytic_account_name_nmbrs = fields.Char("Analytic Account Name Nmbrs")
    analytic_account_odoo = fields.Many2one("account.analytic.account", string="Analytic Account Odoo")
    operating_unit = fields.Many2one("operating.unit", string="Operating Unit")