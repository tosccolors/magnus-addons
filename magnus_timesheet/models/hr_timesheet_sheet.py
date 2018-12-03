# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _, SUPERUSER_ID
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from dateutil.rrule import (rrule)
from dateutil.relativedelta import relativedelta

class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet_sheet.sheet"


    @api.model
    def default_get(self, fields):
        rec = super(HrTimesheetSheet, self).default_get(fields)
        dt = datetime.now()
        emp_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        emp_id = emp_id.id if emp_id else False
        timesheets = self.env['hr_timesheet_sheet.sheet'].search([('employee_id', '=', emp_id)])
        logged_weeks = timesheets.mapped('week_id').ids if timesheets else []
        week = self.env['date.range'].search([('type_id','in',['week','Week','WEEK']), ('date_start', '=', dt-timedelta(days=dt.weekday()))], limit=1)
        if week:
            if week.id not in logged_weeks:
                rec.update({'week_id': week.id})
            else:
                upcoming_week = self.env['date.range'].search([('id', 'not in', logged_weeks), ('type_id','in',['week','Week','WEEK']), ('date_start', '>', dt-timedelta(days=dt.weekday()))], order='date_start', limit=1)
                if upcoming_week:
                    rec.update({'week_id': upcoming_week.id})
                else:
                    rec.update({'week_id': False})
        else:
            if self._uid == SUPERUSER_ID:
                raise UserError(_('Please generate Date Ranges.\n Menu: Settings > Technical > Date Ranges > Generate Date Ranges.'))
            else:
                raise UserError(_('Please contact administrator.'))

        return rec

    def _get_week_domain(self):
        emp_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        emp_id = emp_id.id if emp_id else False
        timesheets = self.env['hr_timesheet_sheet.sheet'].search([('employee_id', '=', emp_id)])
        logged_weeks = timesheets.mapped('week_id').ids if timesheets else []
        return [('type_id','in',['week','Week','WEEK']), ('active','=',True), ('id', 'not in', logged_weeks)]

    def _default_employee(self):
        emp_ids = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    def _get_employee_domain(self):
        emp_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        domain = [('id', '=', emp_id.id)] if emp_id else [('id', '=', False)]
        return domain

    week_id = fields.Many2one('date.range', domain=_get_week_domain, string="Timesheet Week", required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee, required=True, domain=_get_employee_domain)

    @api.onchange('week_id', 'date_from', 'date_to')
    def onchange_week(self):
        self.date_from = self.week_id.date_start
        self.date_to = self.week_id.date_end

    def duplicate_last_week(self):
        if self.week_id and self.employee_id:
            ds = self.week_id.date_start
            date_start = datetime.strptime(ds, "%Y-%m-%d").date() - timedelta(days=7)
            date_end = datetime.strptime(ds, "%Y-%m-%d").date() - timedelta(days=1)
            last_week = self.env['date.range'].search([('type_id','in',['week','Week','WEEK']), ('date_start', '=', date_start), ('date_end', '=', date_end)], limit=1)
            if last_week:
                last_week_timesheet = self.env['hr_timesheet_sheet.sheet'].search([('employee_id', '=', self.employee_id.id), ('week_id', '=', last_week.id)], limit=1)
                if last_week_timesheet:
                    self.timesheet_ids.unlink()
                    self.timesheet_ids = [(0, 0, {'date': datetime.strptime(l.date, "%Y-%m-%d") + timedelta(days=7),'name': '/','project_id': l.project_id.id,'task_id': l.task_id.id}) for l in last_week_timesheet.timesheet_ids]
                else:
                    raise UserError(_("You have no timesheet logged for last week. Duration: %s to %s") %(datetime.strftime(date_start, "%d-%b-%Y"), datetime.strftime(date_end, "%d-%b-%Y")))

    @api.one
    def action_timesheet_confirm(self):
        date_from = datetime.strptime(self.date_from, "%Y-%m-%d").date()
        for i in range(7):
            date = datetime.strftime(date_from + timedelta(days=i), "%Y-%m-%d")
            hour = sum(self.env['account.analytic.line'].search([('date', '=', date), ('sheet_id', '=', self.id)]).mapped('unit_amount'))
            if hour < 0 or hour > 24:
                raise UserError(_('Logged hours should be 0 to 24.'))
            if i < 5 and hour < 8:
                raise UserError(_('Each day from Monday to Friday needs to have at least 8 logged hours.'))
        return super(HrTimesheetSheet, self).action_timesheet_confirm()


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    sheet_id = fields.Many2one('hr_timesheet_sheet.sheet', compute='_compute_sheet', string='Sheet', store=True, ondelete='cascade')

    @api.onchange('project_id')
    def onchange_project_id(self):
        res = super(AccountAnalyticLine, self).onchange_project_id()
        tasks = self.env['project.task'].search([('project_id', '=', self.project_id.id)])
        if len(tasks) == 1:
            self.task_id = tasks.id
        elif len(tasks.filtered('standard')) == 1:
            self.task_id = tasks.filtered('standard').id
        else:
            self.task_id = False
        return res

class DateRangeGenerator(models.TransientModel):
    _inherit = 'date.range.generator'

    @api.multi
    def _compute_date_ranges(self):
        self.ensure_one()
        vals = rrule(freq=self.unit_of_time, interval=self.duration_count,
                     dtstart=fields.Date.from_string(self.date_start),
                     count=self.count+1)
        vals = list(vals)
        date_ranges = []
        count_digits = len(unicode(self.count))
        for idx, dt_start in enumerate(vals[:-1]):
            date_start = fields.Date.to_string(dt_start.date())
            # always remove 1 day for the date_end since range limits are
            # inclusive
            dt_end = vals[idx+1].date() - relativedelta(days=1)
            date_end = fields.Date.to_string(dt_end)
            # year and week number are updated for name according to ISO 8601 Calendar
            date_ranges.append({
                'name': '%s%d' % (
                    str(dt_start.isocalendar()[0])+" "+self.name_prefix, int(dt_start.isocalendar()[1])),
                'date_start': date_start,
                'date_end': date_end,
                'type_id': self.type_id.id,
                'company_id': self.company_id.id})
        return date_ranges