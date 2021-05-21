from odoo import api, fields, models, _
from zeep import Client, Settings
import datetime
import xml.etree.ElementTree as ET
import os

class PayrollJournalEntryNmbrsToOdoo(models.Model):
    _name = 'payroll.journal.entry.nmbrs.to.odoo'

    operating_unit_nmbrs_id = fields.Char("NMBRS ID")

    def fetch_payroll_entry(self):
        config = self.env['nmbrs.interface.config'].search([])[0]
        user = config.api_user
        token = config.api_key
        authentication_v3 = {'Username': user, 'Token': token, 'Domain': 'magnus'}
        client = Client(config.endpoint_company_service)
        api_response = client.service.Journals_GetByRunCostCenter(
            _soapheaders={'AuthHeaderWithDomain': authentication_v3},
            CompanyId=self.operating_unit_nmbrs_id,
            RunId=109319L
        )
        chart_of_accounts = self.env['account.account']
        analytic_accounts_nmbrs = self.env['mapping.nmbrs.analytic.account']
        root = ET.fromstring(api_response)
        lines = {}
        for i in range(len(root[0][1])):
            line = root[0][1][i]
            analytic_account = analytic_accounts_nmbrs.search([('analytic_account_id_nmbrs', '=', line[1].text)]).analytic_account_odoo.id
            if analytic_account:
                operating_unit = analytic_accounts_nmbrs.search([('analytic_account_id_nmbrs', '=', line[1].text)]).analytic_account_odoo.operating_unit_ids[0].id
            line_info = {
                #'id': line.attrib['id'],
                'account_id': chart_of_accounts.search([('code', '=', line[0].text), ('company_id', '=', 1)]).id,
                'analytic_account_id': analytic_account,
                'operating_unit_id': operating_unit or False,
                'credit': float(line[2].text) if line[3].text == 'credit' else 0.0,
                'debit': float(line[2].text) if line[3].text == 'debit' else 0.0,
                'name': line[4].text,
                'ref': line[4].text
            }
            lines[i + 1] = line_info
        return lines


class PayrollEntry(models.Model):
    _name = 'payroll.entry'
    name = fields.Char("Move Name")
    reference = fields.Char("Move Reference")
    create_date = fields.Date("Creation Date")
    operating_unit = fields.Many2one('operating.unit', string="Operating Unit")
    journal = fields.Many2one('account.journal', string="Journal")
    move_id = fields.Many2one(
        'account.move',
        string='Payroll Journal Entry',
        readonly=True,
        copy=False
    )

    @api.multi
    def create_move(self, lines):
        move_data = {
            'name': self.name,
            'date': datetime.datetime.today(),
            'ref': self.reference,
            'journal_id': self.journal.id,
        }
        move = self.env['account.move'].create(move_data)
        #move.post()
        for line in lines:
            vals = lines[line]
            vals['move_id'] = move.id
            self.env['account.move.line'].create(vals)
        #write_ctx = dict(self._context, allow_asset_line_update=True)
        #line.with_context(write_ctx).write({'move_id': move.id})
        #created_move_ids.append(move.id)
        # we re-evaluate the assets to determine if we can close them
        return move

    def fetch_journal_entry(self):
        data = {'operating_unit_nmbrs_id': self.operating_unit.nmbrs_id}
        api_service = self.env['payroll.journal.entry.nmbrs.to.odoo'].sudo().create(data)
        lines = api_service.fetch_payroll_entry()
        move = self.create_move(lines)
        self.move_id = move


class MappingNmbrsAnalyticAccount(models.Model):
    _name = "mapping.nmbrs.analytic.account"

    analytic_account_id_nmbrs = fields.Char("id_nmbrs")
    analytic_account_name_nmbrs = fields.Char("Analytic Account Name Nmbrs")
    analytic_account_odoo = fields.Many2one("account.analytic.account", string="Analytic Account Odoo")
    operating_unit = fields.Many2one("operating.unit", string="Operating Unit")

    def fetch_analytic_accounts_nmbrs(self):
        config = self.env['nmbrs.interface.config'].search([])[0]
        user = config.api_user
        token = config.api_key
        authentication_v3 = {'Username': user, 'Token': token, 'Domain': 'magnus'}
        client = Client(config.endpoint_company_service)
        nmbrs_analytic_accounts = client.service.CostCenter_GetList(
            _soapheaders={'AuthHeaderWithDomain': authentication_v3},
            CompanyId=self.operating_unit.nmbrs_id,
        )
        for analytic_account in nmbrs_analytic_accounts:
            nmbrs_id = analytic_account['Code']
            name = analytic_account['Description']
            vals = {'analytic_account_id_nmbrs': nmbrs_id, 'analytic_account_name_nmbrs': name}
            self.create(vals)
        return True

class PayrollRunsNmbrs(models.Model):
    _name = "payroll.runs.nmbrs"
    _description = "Helper object to load available payroll runs from NMBRs"

    run_id_nmbrs = fields.Char("Run ID NMBRs")
    period = fields.Char("Period")
    operating_unit = fields.Many2one("operating.unit", string="Operating Unit")

    def fetch_payroll_runs_nmbrs(self, operating_unit_nmbrs_id):
        config = self.env['nmbrs.interface.config'].search([])[0]
        user = config.api_user
        token = config.api_key
        authentication_v3 = {'Username': user, 'Token': token, 'Domain': 'magnus'}
        client = Client(config.endpoint_company_service)
        nmbrs_pay_roll_runs = client.service.Run_GetList(
            _soapheaders={'AuthHeaderWithDomain': authentication_v3},
            CompanyId=operating_unit_nmbrs_id,
            Year='2021'
        )
        nr_runs = len(nmbrs_pay_roll_runs)
        for i in range(nr_runs):
            self.create({
                'run_id_nmbrs': nmbrs_pay_roll_runs[i]['ID'],
                'period': nmbrs_pay_roll_runs[i]['Description'],
                'operating_unit': operating_unit_nmbrs_id
            })

