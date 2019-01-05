# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _, SUPERUSER_ID
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.rrule import (rrule)
from dateutil.relativedelta import relativedelta

class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet_sheet.sheet"
    _order = "week_id desc"

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

    @api.onchange('week_id')
    def onchange_week_id(self):
        return {'domain':{'week_id':self._get_week_domain()}}

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

    def _get_vehicle(self):
        vehicle = False
        if self.employee_id:
            user = self.employee_id.user_id if self.employee_id.user_id else False
            if user:
                vehicle = self.env['fleet.vehicle'].search([('driver_id', '=', user.partner_id.id)], limit=1)
        return vehicle

    def _get_latest_odometer(self):
        latest_odometer = self.starting_mileage_editable
        vehicle = self._get_vehicle()
        if vehicle:
            latest_odometer = self.env['fleet.vehicle.odometer'].search([('vehicle_id', '=', vehicle.id)], order='date desc', limit=1).value
        if vehicle and self.week_id:
            latest_odometer = self.env['fleet.vehicle.odometer'].search([('vehicle_id', '=', vehicle.id), ('date', '<', self.week_id.date_start)], order='date desc', limit=1).value
        return latest_odometer

    @api.one
    @api.depends('employee_id','week_id')
    def _get_starting_mileage(self):
        self.starting_mileage = self._get_latest_odometer()

    @api.one
    @api.depends('timesheet_ids.kilometers')
    def _get_business_mileage(self):
        self.business_mileage = sum(self.timesheet_ids.mapped('kilometers')) if self.timesheet_ids else 0

    @api.one
    @api.depends('end_mileage','business_mileage','starting_mileage')
    def _get_private_mileage(self):
        self.private_mileage = self.end_mileage - self.business_mileage - self.starting_mileage

    @api.one
    @api.depends('employee_id','week_id')
    def _compute_vehicle(self):
        self.vehicle = True if self._get_vehicle() else False

    @api.one
    @api.depends('timesheet_ids')
    def _get_overtime_hours(self):
        if self.week_id and self.employee_id:
            date_from = datetime.strptime(self.week_id.date_start, "%Y-%m-%d").date()
            overtime_hours = 0
            for i in range(7):
                date = datetime.strftime(date_from + timedelta(days=i), "%Y-%m-%d")
                hours = sum(self.env['account.analytic.line'].search([('date', '=', date), ('sheet_id', '=', self.id)]).mapped('unit_amount'))
                if i < 5 and hours > 8:
                    overtime_hours += hours - 8
                elif i > 4 and hours > 0:
                    overtime_hours += hours
            overtime_taken = sum(self.env['account.analytic.line'].search([('sheet_id', '=', self.id), ('sheet_id.employee_id', '=', self.employee_id.id), ('project_id.overtime', '=', True)]).mapped('unit_amount'))
            self.overtime_hours = overtime_hours - overtime_taken

    week_id = fields.Many2one('date.range', domain=_get_week_domain, string="Timesheet Week", required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee, required=True, domain=_get_employee_domain)
    starting_mileage = fields.Integer(compute='_get_starting_mileage', string='Starting Mileage', store=True)
    starting_mileage_editable = fields.Integer(string='Starting Mileage')
    vehicle = fields.Boolean(compute='_compute_vehicle', string='Vehicle', store=True)
    business_mileage = fields.Integer(compute='_get_business_mileage', string='Business Mileage', store=True)
    private_mileage = fields.Integer(compute='_get_private_mileage', string='Private Mileage', store=True)
    end_mileage = fields.Integer('End Mileage')
    overtime_hours = fields.Integer(compute="_get_overtime_hours", string='Overtime Hours', store=True)
    odo_log_id = fields.Many2one('fleet.vehicle.odometer',  string="Odo Log ID")

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
                current_week_lines = [(0, 0, {'date': l.date,'name': l.name,'project_id': l.project_id.id,'task_id': l.task_id.id, 'unit_amount': l.unit_amount}) for l in self.timesheet_ids] if self.timesheet_ids else []
                if last_week_timesheet:
                    self.timesheet_ids.unlink()
                    last_week_lines = [(0, 0, {'date': datetime.strptime(l.date, "%Y-%m-%d") + timedelta(days=7),'name': '/','project_id': l.project_id.id,'task_id': l.task_id.id}) for l in last_week_timesheet.timesheet_ids]
                    self.timesheet_ids = current_week_lines + last_week_lines
                else:
                    raise UserError(_("You have no timesheet logged for last week. Duration: %s to %s") %(datetime.strftime(date_start, "%d-%b-%Y"), datetime.strftime(date_end, "%d-%b-%Y")))

    def _check_end_mileage(self):
        total = self.starting_mileage + self.business_mileage
        if self.end_mileage < total:
            raise ValidationError(_('End Mileage cannot be lower than the Starting Mileage + Business Mileage.'))

    @api.one
    def action_timesheet_confirm(self):
        self._check_end_mileage()
        vehicle = self._get_vehicle()
        if vehicle:
            self.odo_log_id = self.env['fleet.vehicle.odometer'].create({
                'value': self.end_mileage,
                'date': self.week_id.date_end or fields.Date.context_today(self),
                'vehicle_id': vehicle.id
            })
        date_from = datetime.strptime(self.date_from, "%Y-%m-%d").date()
        for i in range(7):
            date = datetime.strftime(date_from + timedelta(days=i), "%Y-%m-%d")
            hour = sum(self.env['account.analytic.line'].search([('date', '=', date), ('sheet_id', '=', self.id)]).mapped('unit_amount'))
            if hour < 0 or hour > 24:
                raise UserError(_('Logged hours should be 0 to 24.'))
            if not self.employee_id.timesheet_no_8_hours_day:
                if i < 5 and hour < 8:
                    raise UserError(_('Each day from Monday to Friday needs to have at least 8 logged hours.'))
        return super(HrTimesheetSheet, self).action_timesheet_confirm()

    @api.one
    def action_timesheet_done(self):
        res = super(HrTimesheetSheet, self).action_timesheet_done()
        for aal in self.timesheet_ids.filtered('kilometers'):
            non_invoiceable_mileage = False if aal.project_id.invoice_properties and \
                            aal.project_id.invoice_properties.invoice_mileage else True
            res = {
                'state': 'confirm',
                'unit_amount': aal.kilometers,
                'non_invoiceable_mileage': non_invoiceable_mileage,
                'product_uom_id': self.env.ref('product.product_uom_km').id
            }
            vals = aal.copy_data(default=res)[0]
            newaal = self.env['account.analytic.line'].create(vals)
            aal.ref_id = newaal.id
        return res

    @api.one
    def action_timesheet_draft(self):
        res = super(HrTimesheetSheet, self).action_timesheet_draft()
        if self.timesheet_ids and self.timesheet_ids.mapped('ref_id'):
            self.timesheet_ids.mapped('ref_id').unlink()
        if self.odo_log_id:
            self.env['fleet.vehicle.odometer'].search([('id','=', self.odo_log_id.id)]).unlink()
            self.odo_log_id = False
        return res

    @api.one
    def write(self, vals):
        result = super(HrTimesheetSheet, self).write(vals)
        lines = self.env['account.analytic.line'].search([('sheet_id', '=', self.id)]).filtered(lambda line: line.unit_amount > 24 or line.unit_amount < 0)
        for l in lines:
            l.write({'unit_amount': 0})
        return result

class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    sheet_id = fields.Many2one('hr_timesheet_sheet.sheet', compute='_compute_sheet', string='Sheet', store=True, ondelete='cascade')
    kilometers = fields.Integer('Kilometers')
    non_invoiceable_mileage = fields.Boolean(string='Invoice Mileage', store=True)
    ref_id = fields.Many2one('account.analytic.line', string='Reference')

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