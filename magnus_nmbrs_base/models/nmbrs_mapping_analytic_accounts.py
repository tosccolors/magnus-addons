from odoo import api, fields, models, _


class MappingNmbrsAnalyticAccount(models.Model):
    """
    Provides a mapping table for analytic accounts between Odoo and NMBRs
    """
    _name = "mapping.nmbrs.analytic.account"

    analytic_account_id_nmbrs = fields.Char("NMBRs ID") #NMBRs Database ID
    analytic_account_code_nmbrs = fields.Char("NMBRs Code")
    analytic_account_name_nmbrs = fields.Char("Analytic Account Name Nmbrs")
    analytic_account_odoo = fields.Many2one("account.analytic.account", string="Analytic Account Odoo")
    operating_unit = fields.Many2one("operating.unit", string="Operating Unit")