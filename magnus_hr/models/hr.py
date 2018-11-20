# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Department(models.Model):
    _inherit = "hr.department"

    operating_unit_id = fields.Many2one('operating.unit', string='Operating Unit')

class Employee(models.Model):
    _inherit = "hr.employee"

    official_date_of_employment = fields.Date('Official Date of Employment')
    temporary_contract = fields.Date('Temporary Contract')
    end_date_of_employment = fields.Date('End Date of Employment')
    lengt_of_service = fields.Char(compute='compute_lengt_of_service', string='Length of Service', store=True)
    external = fields.Boolean('External')
    supplier = fields.Char(string='Supplier')
    mentor_id = fields.Many2one('hr.employee', string='Mentor')
    parttime = fields.Integer('Parttime')
    allocated_leaves = fields.Integer('Allocated Leaves')
    emergency_contact = fields.Char('Emergency Contact')
    description = fields.Text('Description')
    pass_number_alarm = fields.Char('Pass Number Alarm')

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

    @api.one
    @api.depends('official_date_of_employment', 'end_date_of_employment')
    def compute_lengt_of_service(self):
        start_date = self.official_date_of_employment
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date_of_employment, "%Y-%m-%d") if self.end_date_of_employment else datetime.now()
            if start_date <= end_date:
                r = relativedelta(end_date, start_date)
                self.lengt_of_service = str(r.years)+" Year(s) "+str(r.months)+" Month(s)"