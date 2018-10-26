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

    def _current_week(self):
        dt = datetime.now()
        week = self.env['date.range'].search([('type_id','=','week'), ('date_start', '=', dt-timedelta(days=dt.weekday()))], limit=1)
        if not week:
            if self._uid == SUPERUSER_ID:
                raise UserError(_('Please generate Date Ranges.\n Menu: Settings > Technical > Date Ranges > Generate Date Ranges.'))
            else:
                raise UserError(_('Please contact administrator.'))
        return week.id

    def _get_domain(self):
        last_month = datetime.strftime(datetime.now().date() - relativedelta(months=1), "%Y-%m-%d")
        next_month = datetime.strftime(datetime.now().date() + relativedelta(months=1), "%Y-%m-%d")
        return [('type_id','=','week'), ('active','=',True), ('date_end', '>=', last_month), ('date_start', '<=', next_month)]

    week_id = fields.Many2one('date.range', domain=_get_domain, string="Timesheet Week", default=_current_week, required=True)

    @api.onchange('week_id', 'date_from', 'date_to')
    def onchange_week(self):
        self.date_from = self.week_id.date_start
        self.date_to = self.week_id.date_end

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