from odoo import api, fields, models, _
from zeep import Client


class NMBRsAnalyticAccountWizard(models.TransientModel):
    """
    This is a transient model, used to show a form to fetch the analytic accounts from NMBRs.
    """
    _name= "nmbrs.analytic.account.wizard"
    _description = "Wizard to fetch analytic accounts from nmbrs"

    operating_unit = fields.Many2one("operating.unit", string="Operating Unit")

    # @api.multi
    def fetch_analytic_accounts_nmbrs(self):
        """
        This function loads the analytic accounts from NMBRs for the selected Operating unit. There is a check
        to prevent double loading. The user can subsequently create the mapping in the UI using the list view.
        """
        config = self.env['nmbrs.interface.config'].search([])[0]
        user = config.api_user
        token = config.api_key
        authentication_v3 = {'Username': user, 'Token': token, 'Domain': 'magnus'}
        client = Client(config.endpoint_company_service)
        if not self.operating_unit.nmbrs_id:
            raise Warning(_("You need to set the Nmbrs ID for the operating unit in Odoo"))
        nmbrs_analytic_accounts = client.service.CostCenter_GetList(
            _soapheaders={'AuthHeaderWithDomain': authentication_v3},
            CompanyId=self.operating_unit.nmbrs_id,
        )
        if len(nmbrs_analytic_accounts) > 0:
            vals = []
            current_analytic_accounts = self.env['mapping.nmbrs.analytic.account']
            for analytic_account in nmbrs_analytic_accounts:
                nmbrs_id = analytic_account['Id']
                name = analytic_account['Description']
                nmbrs_code = analytic_account['Code']
                vals = {
                    'analytic_account_id_nmbrs': nmbrs_id,
                    'analytic_account_code_nmbrs': nmbrs_code,
                    'analytic_account_name_nmbrs': name,
                    'operating_unit': self.operating_unit.id,
                    'nmbrs_code': nmbrs_code
                }
                if not current_analytic_accounts.search([('analytic_account_id_nmbrs', '=', nmbrs_id)]):
                    self.env['mapping.nmbrs.analytic.account'].create(vals)
