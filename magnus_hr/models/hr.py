# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class Employee(models.Model):
    _inherit = "hr.employee"

    official_date_of_employment = fields.Date('Official Date of Employment')
    temporary_contract = fields.Date('Temporary Contract')
    end_date_of_employment = fields.Date('End Date of Employment')
    external = fields.Boolean('External')
    supplier_id = fields.Many2one('res.partner', domain=[('supplier', '=', True), ('company_type', '=', 'company')], string='Supplier')
    mentor_id = fields.Many2one('hr.employee', string='Mentor')
    parttime = fields.Integer('Parttime')
    allocated_leaves = fields.Integer('Allocated Leaves')
    emergency_contact = fields.Char('Emergency Contact')
    description = fields.Text('Description')
    pass_number_alarm = fields.Char('Pass Number Alarm')
    slamid = fields.Char('Slam ID')
    personnel_number = fields.Char('Personnel Number')
    employee_numbersid = fields.Char('Employee NMBRs ID')
    date_last_promotion = fields.Date('Date of last Promotion')
    klippa_user = fields.Boolean(
        string="Employee uses Klippa"
    )
    has_private_car = fields.Boolean(string="Employee has a private car")
    leave_hours = fields.Float(string="Leave Hours")

    def validate_dates(self):
        start_date = self.official_date_of_employment
        end_date = self.end_date_of_employment
        if start_date and end_date and start_date > end_date:
            raise ValidationError(_('End Date of Employment cannot be set before Official Date of Employment.'))

    @api.onchange('official_date_of_employment', 'end_date_of_employment')
    def onchange_dates(self):
        self.validate_dates()

    @api.one
    @api.constrains('official_date_of_employment', 'end_date_of_employment')
    def _check_closing_date(self):
        self.validate_dates()

    @api.depends('contract_ids', 'initial_employment_date', 'end_date_of_employment')
    def _compute_months_service(self):
        date_now = fields.Date.today()
        Contract = self.env['hr.contract'].sudo()
        for employee in self:
            nb_month = 0
            if employee.end_date_of_employment:
                date_now = employee.end_date_of_employment

            if employee.initial_employment_date:
                first_contract = employee._first_contract()
                if first_contract:
                    to_dt = fields.Date.from_string(first_contract.date_start)
                else:
                    to_dt = fields.Date.from_string(date_now)

                from_dt = fields.Date.from_string(
                    employee.initial_employment_date)

                nb_month += relativedelta(to_dt, from_dt).years * 12 + \
                    relativedelta(to_dt, from_dt).months + \
                    self.check_next_days(to_dt, from_dt)

            contracts = Contract.search([('employee_id', '=', employee.id)],
                                        order='date_start asc')
            for contract in contracts:
                from_dt = fields.Date.from_string(contract.date_start)
                if contract.date_end and contract.date_end < date_now:
                    to_dt = fields.Date.from_string(contract.date_end)
                else:
                    to_dt = fields.Date.from_string(date_now)
                nb_month += relativedelta(to_dt, from_dt).years * 12 + \
                    relativedelta(to_dt, from_dt).months + \
                    self.check_next_days(to_dt, from_dt)

            employee.length_of_service = nb_month