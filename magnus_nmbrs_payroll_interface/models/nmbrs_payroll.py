from odoo import api, fields, models, _
from zeep import Client, Settings
import datetime
import xml.etree.ElementTree as ET
from odoo.exceptions import UserError, ValidationError
import os


# class PayrollJournalEntryNmbrsToOdoo(models.Model):
#     """
#     This model is an intermediary model used to retrieve the data from NMBRs using the API
#     """
#     _name = 'payroll.journal.entry.nmbrs.to.odoo'
#
#     operating_unit = fields.Many2one("operating.unit")
#     payroll_run = fields.Many2one("payroll.runs.nmbrs")
class PayrollEntry(models.Model):
    """
    This class is used to retrieve the payroll entry data from nmbrs, and translate it to a journal entry in Odoo. In
    the object's form, the user enters all details (operating, payroll run, reference etc.) for the journal entry that
    is to be retrieved from NMBRs.
    """
    _name = 'payroll.entry'
    name = fields.Char("Move Name")
    reference = fields.Char("Move Reference")
    create_date = fields.Date("Creation Date")
    operating_unit = fields.Many2one('operating.unit', string="Operating Unit")
    journal = fields.Many2one('account.journal', string="Journal")
    created_move = fields.Many2one("account.move", "Created Move", readonly="True")
    payroll_run = fields.Many2one("payroll.runs.nmbrs", "Run")
    move_id = fields.Many2one(
        'account.move',
        string='Payroll Journal Entry',
        readonly=True,
        copy=False
    )

    @api.multi
    @api.onchange('operating_unit')
    def onchange_operating_unit(self):
        """
        This method defines a domain for the payroll run field. One should only be able to select payroll runs that
        are not already imported, and which belong to the selected operating unit.
        """
        res = {}
        res['domain'] = {'payroll_run': ['&',
                                         ('operating_unit.id', '=', self.operating_unit.id),
                                         ('imported', '=', False)
                                         ]
                         }
        return res

    @api.multi
    def fetch_journal_entry(self):
        """
        This method creates the move using the method fetch_payroll_entry (the move lines) and create_move using the
        retrieved lines.
        """
        lines = self.fetch_payroll_entry()
        move = self.create_move(lines)
        self.created_move = move
        self.move_id = move

    @api.multi
    def create_move(self, lines):
        move_data = {
            'name': self.name,
            'date': datetime.datetime.today(),
            'ref': self.reference,
            'journal_id': self.journal.id,
            'line_ids': lines
        }
        ctx = dict(self._context, check_move_validity=False)
        move = self.env['account.move'].with_context(ctx).create(move_data)
        self.env['payroll.runs.nmbrs'].browse(self.payroll_run.id).update({'imported': True})
        return move

    @api.multi
    def fetch_payroll_entry(self):
        """
        This method uses the NMBRs API to fetch the payroll entry lines.
        """
        config = self.env['nmbrs.interface.config'].search([])[0]
        if not config.operating_unit.nmbrs_id:
            raise Warning(_("You need to set the Nmbrs ID for the operating unit in Odoo"))
        user = config.api_user
        token = config.api_key
        authentication_v3 = {'Username': user, 'Token': token, 'Domain': 'magnus'}
        client = Client(config.endpoint_company_service)
        api_response = client.service.Journals_GetByRunCostCenter(
            _soapheaders={'AuthHeaderWithDomain': authentication_v3},
            CompanyId=self.operating_unit.nmbrs_id,
            RunId=self.payroll_run.run_id_nmbrs
        )
        chart_of_accounts = self.env['account.account']
        analytic_accounts_nmbrs = self.env['mapping.nmbrs.analytic.account']
        root = ET.fromstring(api_response)
        lines = []
        for i in range(len(root[0][1])):
            line = root[0][1][i]
            analytic_account = analytic_accounts_nmbrs.search(
                [
                    ('operating_unit.id', '=', self.operating_unit.id),
                    ('analytic_account_code_nmbrs', '=', line[1].text)
                ]
            ).analytic_account_odoo
            if analytic_account:
                if not analytic_account.operating_unit_ids:
                    raise UserError(_('Analytic account %s has no operating unit!') % analytic_account.name)
                else:
                    line_operating_unit = analytic_account.operating_unit_ids[0].id
            line_info = {
                'account_id': chart_of_accounts.search([('code', '=', line[0].text), ('company_id', '=', 1)]).id,
                'analytic_account_id': analytic_account.id,
                'operating_unit_id': line_operating_unit or False,
                'credit': float(line[2].text) if line[3].text == 'credit' else 0.0,
                'debit': float(line[2].text) if line[3].text == 'debit' else 0.0,
                'name': line[4].text if line[4] else '/',
                # 'ref': line[4].text
            }
            lines.append([0, 0, line_info])
        return lines


class PayrollRunsNmbrs(models.Model):
    """
    This object contains the specific payroll run info. The boolean "imported" is there to prevent double imports of the
    same run. Note: if a payroll run should be imported again, the box imported should be unticked manually in the UI in
    the listview (or using an import, or directly in the DB).
    """
    _name = "payroll.runs.nmbrs"
    _description = "Helper object to load available payroll runs from NMBRs"
    _rec_name = "period"

    run_id_nmbrs = fields.Char("Run ID NMBRs")
    period = fields.Char("Period")
    operating_unit = fields.Many2one("operating.unit", string="Operating Unit")
    imported = fields.Boolean("Imported", default=False)
