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
        date_range_type_cw_id = self.env.ref(
            'magnus_date_range_week.date_range_calender_week').id
        past_week_domain = [('type_id', '=', date_range_type_cw_id), ('date_end', '<', dt - timedelta(days=dt.weekday()))]
        if logged_weeks:
            past_week_domain += [('id', 'not in', logged_weeks)]
        past_weeks = self.env['date.range'].search(past_week_domain, limit=1, order='date_start')
        week = self.env['date.range'].search([('type_id','=',date_range_type_cw_id), ('date_start', '=',
                                                                                      dt-timedelta(days=dt.weekday()))], limit=1)
        if week or past_weeks:
            if past_weeks.id not in logged_weeks:
                rec.update({'week_id': past_weeks.id})
            elif week.id not in logged_weeks:
                rec.update({'week_id': week.id})
            else:
                upcoming_week = self.env['date.range'].search([
                    ('id', 'not in', logged_weeks),
                    ('type_id','=',date_range_type_cw_id),
                    ('date_start', '>', dt-timedelta(days=dt.weekday()))
                ], order='date_start', limit=1)
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
        date_range_type_cw_id = self.env.ref(
            'magnus_date_range_week.date_range_calender_week').id
        return [('type_id','=', date_range_type_cw_id), ('active','=',True), ('id', 'not in', logged_weeks)]

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
            user = self.employee_id.user_id or False
            if user:
                dtt_vehicle = self.env['data.time.tracker'].search([
                    ('model','=','fleet.vehicle'),
                    ('relation_model','=','res.partner'),
                    ('relation_ref', '=', user.partner_id.id),
                    ('date_from', '<', self.date_from),
                    ('date_to', '>=', self.date_to)],limit=1)
                if dtt_vehicle:
                    vehicle = self.env['fleet.vehicle'].search([
                        ('id', '=', dtt_vehicle.model_ref)], limit=1)
                else:
                    vehicle = self.env['fleet.vehicle'].search([
                    ('driver_id', '=', user.partner_id.id)], limit=1)
        return vehicle

    def _get_latest_mileage(self):
        vehicle = self._get_vehicle()
        if vehicle and self.week_id:
            latest_mileage = self.env['fleet.vehicle.odometer'].search([('vehicle_id', '=', vehicle.id), ('date', '<', self.week_id.date_start)], order='date desc', limit=1).value
        elif vehicle:
            latest_mileage = self.env['fleet.vehicle.odometer'].search([('vehicle_id', '=', vehicle.id)], order='date desc', limit=1).value
        else:
            latest_mileage = self.starting_mileage_editable
        return latest_mileage

    @api.multi
    @api.depends('employee_id','week_id')
    def _get_starting_mileage(self):
        for sheet in self:
            sheet.vehicle = True if sheet._get_vehicle() else False
            sheet.starting_mileage = sheet._get_latest_mileage()

    @api.multi
    @api.depends('timesheet_ids.kilometers')
    def _get_business_mileage(self):
        for sheet in self:
            sheet.business_mileage = sum(sheet.timesheet_ids.mapped('kilometers')) if sheet.timesheet_ids else 0

    @api.multi
    @api.depends('end_mileage','business_mileage','starting_mileage')
    def _get_private_mileage(self):
        for sheet in self:
            m = sheet.end_mileage - sheet.business_mileage - sheet.starting_mileage
            sheet.private_mileage = m if m > 0 else 0

    @api.one
    @api.depends('timesheet_ids')
    def _get_overtime_hours(self):
        overtime_hours = 0.0
        aal = self.timesheet_ids.filtered(lambda a: not a.task_id.standby and not a.project_id.overtime)
        working_hrs = sum(aal.mapped('unit_amount'))
        if working_hrs > 40:
            overtime_hours = working_hrs - 40

        self.overtime_hours = overtime_hours


    week_id = fields.Many2one('date.range', domain=_get_week_domain, string="Timesheet Week", required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee, required=True, domain=_get_employee_domain)
    starting_mileage = fields.Integer(compute='_get_starting_mileage', string='Starting Mileage', store=False)
    starting_mileage_editable = fields.Integer(string='Starting Mileage')
    vehicle = fields.Boolean(compute='_get_starting_mileage', string='Vehicle', store=False)
    business_mileage = fields.Integer(compute='_get_business_mileage', string='Business Mileage', store=True)
    private_mileage = fields.Integer(compute='_get_private_mileage', string='Private Mileage', store=False)
    end_mileage = fields.Integer('End Mileage')
    overtime_hours = fields.Float(compute="_get_overtime_hours", string='Overtime Hours', store=True)
    odo_log_id = fields.Many2one('fleet.vehicle.odometer',  string="Odo Log ID")
    overtime_analytic_line_id = fields.Many2one('account.analytic.line', string="Overtime Entry")

    @api.onchange('week_id', 'date_from', 'date_to')
    def onchange_week(self):
        self.date_from = self.week_id.date_start
        self.date_to = self.week_id.date_end

  #  @api.onchange('starting_mileage', 'business_mileage')
  #  def onchange_private_mileage(self):
  #      if self.private_mileage == 0:
  #          self.end_mileage = self.starting_mileage + self.business_mileage


    def duplicate_last_week(self):
        if self.week_id and self.employee_id:
            ds = self.week_id.date_start
            date_start = datetime.strptime(ds, "%Y-%m-%d").date() - \
                                                        timedelta(days=7)
            date_end = datetime.strptime(ds, "%Y-%m-%d").date() - \
                                                        timedelta(days=1)
            date_range_type_cw_id = self.env.ref(
                'magnus_date_range_week.date_range_calender_week').id
            last_week = self.env['date.range'].search([
                ('type_id','=',date_range_type_cw_id),
                ('date_start', '=', date_start),
                ('date_end', '=', date_end)
            ], limit=1)
            if last_week:
                last_week_timesheet = self.env['hr_timesheet_sheet.sheet'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('week_id', '=', last_week.id)
                ], limit=1)
                current_week_lines = [(0, 0, {
                    'date': l.date,
                    'name': l.name,
                    'project_id': l.project_id.id,
                    'task_id': l.task_id.id,
                    'user_id': l.user_id.id,
                    'unit_amount': l.unit_amount
                }) for l in self.timesheet_ids] if self.timesheet_ids else []
                if last_week_timesheet:
                    self.timesheet_ids.unlink()
                    last_week_lines = [(0, 0, {
                        'date': datetime.strptime(l.date, "%Y-%m-%d") +
                                timedelta(days=7),
                        'name': '/',
                        'project_id': l.project_id.id,
                        'task_id': l.task_id.id,
                        'user_id': l.user_id.id
                    }) for l in last_week_timesheet.timesheet_ids]
                    self.timesheet_ids = current_week_lines + last_week_lines
                else:
                    raise UserError(_(
                        "You have no timesheet logged for last week. "
                        "Duration: %s to %s"
                    ) %(datetime.strftime(date_start, "%d-%b-%Y"),
                        datetime.strftime(date_end, "%d-%b-%Y")))

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
                'value_period_update': self.business_mileage + self.private_mileage,
                'date': self.week_id.date_end or fields.Date.context_today(self),
                'vehicle_id': vehicle.id
            })
        date_from = datetime.strptime(self.date_from, "%Y-%m-%d").date()
        for i in range(7):
            date = datetime.strftime(date_from + timedelta(days=i), "%Y-%m-%d")
            hour = sum(self.env['account.analytic.line'].search([('date', '=', date), ('sheet_id', '=', self.id), ('task_id.standby', '=', False)]).mapped('unit_amount'))
            if hour < 0 or hour > 24:
                raise UserError(_('Logged hours should be 0 to 24.'))
            if not self.employee_id.timesheet_no_8_hours_day:
                if i < 5 and hour < 8:
                    raise UserError(_('Each day from Monday to Friday needs to have at least 8 logged hours.'))
        return super(HrTimesheetSheet, self).action_timesheet_confirm()


    @api.one
    def create_overtime_entries(self):
        analytic_line = self.env['account.analytic.line']
        if self.overtime_hours and not self.overtime_analytic_line_id:
            company_id = self.company_id.id if self.company_id else self.employee_id.company_id.id
            overtime_project = self.env['project.project'].search([('company_id', '=', company_id), ('overtime_hrs', '=', True)])
            overtime_project_task = self.env['project.task'].search([('project_id.id','=', overtime_project), ('standard', '=', True)])
            if not overtime_project:
                raise ValidationError(_("Please define project with 'Overtime Hours'!"))

            uom = self.env.ref('product.product_uom_hour').id
            analytic_line = analytic_line.create({
                'name':'Overtime',
                'account_id':overtime_project.analytic_account_id.id,
                'project_id':overtime_project.id,
                'task_id':overtime_project_task.id,
                'date':self.date_to,
                'unit_amount':self.overtime_hours,
                'product_uom_id':uom,
                'ot':True,
                'user_id':self.user_id.id,
            })
            self.overtime_analytic_line_id = analytic_line.id
        elif self.overtime_analytic_line_id:
            if self.overtime_hours:
                self.overtime_analytic_line_id.write({'unit_amount':self.overtime_hours})
            else:
                self.overtime_analytic_line_id.unlink()
        return self.overtime_analytic_line_id


    @api.one
    def action_timesheet_done(self):
        """
        On timesheet confirmed update analytic state to confirmed
        :return: Super
        """
        res = super(HrTimesheetSheet, self).action_timesheet_done()
        self.create_overtime_entries()
        self.copy_wih_query()
        return res

    def copy_wih_query(self):
        query = """
        INSERT INTO
        account_analytic_line
        (       create_uid,
                user_id,
                account_id,
                company_id,
                write_uid,
                amount,
                unit_amount,
                date,
                create_date,
                write_date,
                partner_id,
                name,
                code,
                currency_id,
                ref,
                general_account_id,
                move_id,
                product_id,
                amount_currency,
                project_id,
                department_id,
                task_id,
                sheet_id,
                ts_line,
                so_line,
                user_total_id,
                month_id,
                week_id,
                account_department_id,               
                expenses,
                chargeable,
                operating_unit_id,
                correction_charge,
                write_off_move,
                ref_id,
                actual_qty,
                planned_qty,
                planned,
                select_week_id,
                kilometers,
                state,
                non_invoiceable_mileage,
                product_uom_id )
        SELECT  aal.create_uid as create_uid,
                aal.user_id as user_id,
                aal.account_id as account_id,
                aal.company_id as company_id,
                aal.write_uid as write_uid,
                aal.amount as amount,
                aal.kilometers as unit_amount,
                aal.date as date,
                %(create)s as create_date,
                %(create)s as write_date,
                aal.partner_id as partner_id,
                aal.name as name,
                aal.code as code,
                aal.currency_id as currency_id,
                aal.ref as ref,
                aal.general_account_id as general_account_id,
                aal.move_id as move_id,
                aal.product_id as product_id,
                aal.amount_currency as amount_currency,
                aal.project_id as project_id,
                aal.department_id as department_id,
                aal.task_id as task_id,
                NULL as sheet_id,
                NULL as ts_line,
                aal.so_line as so_line,
                aal.user_total_id as user_total_id,
                aal.month_id as month_id,
                aal.week_id as week_id,
                aal.account_department_id as account_department_id,
                aal.expenses as expenses,
                aal.chargeable as chargeable,
                aal.operating_unit_id as operating_unit_id,
                aal.correction_charge as correction_charge,
                aal.write_off_move as write_off_move,              
                aal.id as ref_id,
                aal.actual_qty as actual_qty,
                aal.planned_qty as planned_qty,
                aal.planned as planned,
                aal.select_week_id as select_week_id,
                0 as kilometers,
                CASE
                  WHEN ip.invoice_mileage IS NULL THEN true
                  ELSE ip.invoice_mileage
                END AS non_invoiceable_mileage,
                %(km)s as product_uom_id      
        FROM
         account_analytic_line aal
         LEFT JOIN project_project pp 
         ON pp.id = aal.project_id
         LEFT JOIN project_invoicing_properties ip
         ON ip.id = pp.invoice_properties
         RIGHT JOIN hr_timesheet_sheet_sheet hss
         ON hss.id = aal.sheet_id
        WHERE hss.id = %(sheet)s
        AND aal.ref_id IS NULL
        AND aal.kilometers > 0       
        ;"""
        km_id = self.env.ref('product.product_uom_km').id
        heden = str(fields.Datetime.to_string(fields.datetime.now()))
        self.env.cr.execute(query, {'create': heden,'km': km_id, 'sheet':self.id})
        self.env.invalidate_all()
        return True

    @api.one
    def action_timesheet_draft(self):
        """
        On timesheet reset draft check analytic shouldn't be in invoiced
        :return: Super
        """
        res = super(HrTimesheetSheet, self).action_timesheet_draft()
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

    @api.multi
    def action_view_overtime_entry(self):
        self.ensure_one()
        action = self.env.ref('analytic.account_analytic_line_action_entries')
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': 'form',
            'view_mode': 'form',
            'target': action.target,
            'res_id': self.overtime_analytic_line_id.id or False,
            'res_model': action.res_model,
            'domain': [('id', '=', self.overtime_analytic_line_id.id)],
        }


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