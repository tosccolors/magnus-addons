# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class NmbrsInterfaceConfig(models.Model):
    _name = 'nmbrs.interface.config'
    _description = 'NMBRs interface configuration'

    api_user = fields.Char("API User", help="User login of API user in NMBRs")
    api_key = fields.Char(string='API Key', help="API key")
    endpoint_employee_service = fields.Char(strin="Endpoint Employee Service")
    endpoint_debtor_service = fields.Char(strin="Endpoint Debtory Service")
    endpoint_company_service = fields.Char(strin="Endpoint Company Service")

    # show only first record to configure, no options to create an additional one
    @api.multi
    def default_view(self):
        configurations = self.search([])
        if not configurations:
            endpoint_employee_service = 'https://api-sandbox.nmbrs.nl/soap/v3/EmployeeService.asmx?WSDL'
            endpoint_debtor_service = 'https://api-sandbox.nmbrs.nl/soap/v3/DebtorService.asmx?WSDL'
            endpoint_company_service = 'https://api-sandbox.nmbrs.nl/soap/v3/CompanyService.asmx?WSDL'
            self.write({'endpoint_employee_service': endpoint_employee_service,
                        'endpoint_debtor_service': endpoint_debtor_service,
                        'endpoint_company_service': endpoint_company_service
                        })
            configuration = self.id
            _logger.info("Pubble order interface configuration record created")
        else:
            configuration = configurations[0].id
        action = {
            "type": "ir.actions.act_window",
            "res_model": "nmbrs.interface.config",
            "view_type": "form",
            "view_mode": "form",
            "res_id": configuration,
            "target": "inline",
        }
        return action

    @api.multi
    def save_config(self):
        self.write({})
        return True