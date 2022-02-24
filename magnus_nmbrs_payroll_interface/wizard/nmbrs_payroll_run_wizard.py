from odoo import api, fields, models, _
from zeep import Client


class NMBRsPayrollRunWizard(models.TransientModel):
    """
    This is transient model to facilitate the payroll run wizard. Note: this model is about the runs, not the journal
    entries of the runs.
    """
    _name = "nmbrs.payroll.runs.wizard"
    _description = "Wizard to fetch payroll runs from nmbrs"

    operating_unit = fields.Many2one("operating.unit", string="Operating Unit")
    year = fields.Char(string="Year")

    @api.multi
    def fetch_payroll_runs_nmbrs(self):
        """
        This method is used to retrieve the payroll run info from numbers. Note: the payroll entry is loaded elsewhere.
        """
        config = self.env['nmbrs.interface.config'].search([])[0]
        user = config.api_user
        token = config.api_key
        authentication_v3 = {'Username': user, 'Token': token, 'Domain': 'magnus'}
        client = Client(config.endpoint_company_service)
        nmbrs_pay_roll_runs = client.service.Run_GetList(
            _soapheaders={'AuthHeaderWithDomain': authentication_v3},
            CompanyId=self.operating_unit.nmbrs_id,
            Year=self.year
        )
        nr_runs = len(nmbrs_pay_roll_runs)
        current_runs = self.env['payroll.runs.nmbrs']
        if nr_runs > 0:
            for run in nmbrs_pay_roll_runs:
                run_dict = {
                    'run_id_nmbrs': run['ID'],
                    'period': run['Description'],
                    'operating_unit': self.operating_unit.id,
                    'imported': False
                }
                if not current_runs.search([('run_id_nmbrs', '=', run['ID'])]):
                    self.env['payroll.runs.nmbrs'].create(run_dict)
