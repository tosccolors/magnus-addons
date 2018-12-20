# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime, timedelta

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _fetch_emp_plan(self):
        emp = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        return True if emp and emp.planning_week else False

    @api.onchange('user_id')
    def _onchange_users(self):
        self.planned = self._fetch_emp_plan()

    @api.onchange('date')
    def _onchange_dates(self):
        if self.planned or self.env.context.get('default_planned',False) :
            dt = datetime.strptime(self.date, "%Y-%m-%d") if self.date else datetime.now().date()
            self.date = dt-timedelta(days=dt.weekday())
            self.company_id = self.env.user.company_id
            self.week_id = self.find_daterange_week(self.date)

    def _get_qty(self):
        for line in self:
            if line.planned:
                line.planned_qty = line.unit_amount
                line.actual_qty = 0.0
            else:
                line.actual_qty = line.unit_amount
                line.planned_qty = 0.0

    def _get_day(self):
        for line in self:
            self.day_name = str(datetime.strptime(line.date, '%Y-%m-%d').strftime("%m/%d/%Y"))+' ('+datetime.strptime(line.date, '%Y-%m-%d').strftime('%a')+')'



    planned = fields.Boolean(string='Planned')
    actual_qty = fields.Float(string='Actual Qty', compute='_get_qty', store=True)
    planned_qty = fields.Float(string='Planned Qty', compute='_get_qty', store=True)
    day_name = fields.Char(string="Day", compute='_get_day')