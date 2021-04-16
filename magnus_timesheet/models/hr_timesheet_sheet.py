# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _, SUPERUSER_ID
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.rrule import (rrule)
from dateutil.relativedelta import relativedelta
from openerp.tools.float_utils import float_compare
from ....addons.queue_job.job import job

class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet_sheet.sheet"
    _order = "week_id desc"

    def get_week_to_submit(self):
        dt = datetime.now()
        emp_obj = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        emp_id = emp_obj.id if emp_obj else False
        timesheets = self.env['hr_timesheet_sheet.sheet'].search([('employee_id', '=', emp_id)])
        logged_weeks = timesheets.mapped('week_id').ids if timesheets else []
        date_range = self.env['date.range']
        date_range_type_cw_id = self.env.ref(
            'magnus_date_range_week.date_range_calender_week').id
        employement_date = emp_obj.official_date_of_employment
        employement_week = date_range.search(
            [('type_id', '=', date_range_type_cw_id), ('date_start', '<=', employement_date),
             ('date_end', '>=', employement_date)])
        past_week_domain = [('type_id', '=', date_range_type_cw_id),
                            ('date_end', '<', dt - timedelta(days=dt.weekday()))]
        if employement_week:
            past_week_domain += [('date_start', '>=', employement_week.date_start)]

        if logged_weeks:
            past_week_domain += [('id', 'not in', logged_weeks)]
        past_weeks = date_range.search(past_week_domain, limit=1, order='date_start')
        week = date_range.search([('type_id', '=', date_range_type_cw_id), ('date_start', '=', dt - timedelta(days=dt.weekday()))], limit=1)

        if week or past_weeks:
            if past_weeks and past_weeks.id not in logged_weeks:
                return past_weeks
            elif week and week.id not in logged_weeks:
                return week
            else:
                upcoming_week = date_range.search([
                    ('id', 'not in', logged_weeks),
                    ('type_id','=',date_range_type_cw_id),
                    ('date_start', '>', dt-timedelta(days=dt.weekday()))
                ], order='date_start', limit=1)
                if upcoming_week:
                    return upcoming_week
                else:
                    return False
        return False

    @api.model
    def default_get(self, fields):
        rec = super(HrTimesheetSheet, self).default_get(fields)
        week = self.get_week_to_submit()
        if week:
            rec.update({'week_id': week.id})
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
                dtt_vehicle = self.env['data.time.tracker'].sudo().search([
                    ('model','=','fleet.vehicle'),
                    ('relation_model','=','res.partner'),
                    ('relation_ref', '=', user.partner_id.id),
                    ('date_from', '<', self.date_from),
                    ('date_to', '>=', self.date_to)],limit=1)
                if dtt_vehicle:
                    vehicle = self.env['fleet.vehicle'].sudo().search([
                        ('id', '=', dtt_vehicle.model_ref)], limit=1)
                else:
                    vehicle = self.env['fleet.vehicle'].sudo().search([
                    ('driver_id', '=', user.partner_id.id)], limit=1)
        return vehicle

    def _get_latest_mileage(self):
        vehicle = self._get_vehicle()
        odoo_meter_sudo = self.env['fleet.vehicle.odometer'].sudo()
        if vehicle and self.week_id:
            latest_mileage = odoo_meter_sudo.sudo().search([('vehicle_id', '=', vehicle.id), ('date', '<', self.week_id.date_start)], order='date desc', limit=1).value
        elif vehicle:
            latest_mileage = odoo_meter_sudo.sudo().search([('vehicle_id', '=', vehicle.id)], order='date desc', limit=1).value
        else:
            latest_mileage = self.sudo().starting_mileage_editable
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
            sheet.business_mileage = sum(sheet.sudo().timesheet_ids.mapped('kilometers')) if sheet.timesheet_ids else 0

    @api.multi
    @api.depends('end_mileage','business_mileage','starting_mileage')
    def _get_private_mileage(self):
        for sheet in self:
            m = sheet.end_mileage - sheet.business_mileage - sheet.starting_mileage
            sheet.private_mileage = m if m > 0 else 0

    @api.one
    @api.depends('timesheet_ids')
    def _get_overtime_hours(self):
        aal_incl_ott = self.timesheet_ids.filtered(lambda a: not a.task_id.standby)
        aal_ott = self.timesheet_ids.filtered('project_id.overtime')
        working_hrs_incl_ott = sum(aal_incl_ott.mapped('unit_amount'))
        ott = sum(aal_ott.mapped('unit_amount'))
        self.overtime_hours = working_hrs_incl_ott - 40
        self.overtime_hours_delta = working_hrs_incl_ott - ott - 40

    week_id = fields.Many2one(
        'date.range',
        domain=_get_week_domain,
        string="Timesheet Week",
        required=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        default=_default_employee,
        required=True,
        domain=_get_employee_domain
    )
    starting_mileage = fields.Integer(
        compute='_get_starting_mileage',
        string='Starting Mileage',
        store=False
    )
    starting_mileage_editable = fields.Integer(
        string='Starting Mileage'
    )
    vehicle = fields.Boolean(
        compute='_get_starting_mileage',
        string='Vehicle',
        store=False
    )
    business_mileage = fields.Integer(
        compute='_get_business_mileage',
        string='Business Mileage',
        store=True
    )
    private_mileage = fields.Integer(
        compute='_get_private_mileage',
        string='Private Mileage',
        store=True
    )
    end_mileage = fields.Integer(
        'End Mileage'
    )
    overtime_hours = fields.Float(
        compute="_get_overtime_hours",
        string='Overtime Hours',
        store=True
    )
    overtime_hours_delta = fields.Float(
        compute="_get_overtime_hours",
        string='Change in Overtime Hours',
        store=True
    )
    odo_log_id = fields.Many2one(
        'fleet.vehicle.odometer',
        string="Odo Log ID"
    )
    overtime_analytic_line_id = fields.Many2one(
        'account.analytic.line',
        string="Overtime Entry"
    )
    date_from = fields.Date(
        related='week_id.date_start',
        string='Date From',
        store=True,
    )
    date_to = fields.Date(
        related='week_id.date_end',
        string='Date To',
        store=True,
    )
    ## with override of date fields as related of week_id not necessary anymore
    # @api.onchange('week_id', 'date_from', 'date_to')
    # def onchange_week(self):
    #     self.date_from = self.week_id.date_start
    #     self.date_to = self.week_id.date_end

    #  @api.onchange('starting_mileage', 'business_mileage')
    #  def onchange_private_mileage(self):
    #      if self.private_mileage == 0:
    #          self.end_mileage = self.starting_mileage + self.business_mileage

    @api.constrains('week_id', 'employee_id')
    def _check_sheet_date(self, forced_user_id=False):
        for sheet in self:
            new_user_id = forced_user_id or sheet.user_id and sheet.user_id.id
            if new_user_id:
                self.env.cr.execute('''
                        SELECT id
                        FROM hr_timesheet_sheet_sheet
                        WHERE week_id=%s
                        AND user_id=%s''',
                        (sheet.week_id.id, new_user_id)
                )
                if self.env.cr.rowcount > 1:
                    raise ValidationError(_(
                        'You cannot have 2 timesheets with the same week_id!\nPlease use the menu \'My Current Timesheet\' to avoid this problem.'))

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        super(HrTimesheetSheet, self).onchange_employee_id()
        return {'domain': {'week_id': self._get_week_domain()}}

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
                if not last_week_timesheet:
                    raise UserError(_(
                        "You have no timesheet logged for last week. "
                        "Duration: %s to %s"
                    ) % (datetime.strftime(date_start, "%d-%b-%Y"),
                         datetime.strftime(date_end, "%d-%b-%Y")))
                ## todo What if during last week department_id and/or operating_unit_id and/or product_id has changed?
                ## todo nothing because when unit_amount is set in the timesheet, _compute_analytic_line and write() are called

                else:
                    self.copy_with_query(last_week_timesheet.id)


    def _check_end_mileage(self):
        total = self.starting_mileage + self.business_mileage
        if self.end_mileage < total:
            raise ValidationError(_('End Mileage cannot be lower than the Starting Mileage + Business Mileage.'))

    @api.one
    def action_timesheet_draft(self):
        """
        On timesheet reset draft check analytic shouldn't be in invoiced
        :return: Super
        """
        if any([ts.state == 'progress' for ts in self.timesheet_ids]):
            # if self.timesheet_ids.filtered('invoiced') or any([ts.state == 'progress' for ts in self.timesheet_ids]):
            raise UserError(_('You cannot modify timesheet entries either Invoiced or belongs to Analytic Invoiced!'))
        res = super(HrTimesheetSheet, self).action_timesheet_draft()
        if self.timesheet_ids:
            cond = '='
            rec = self.timesheet_ids.ids[0]
            if len(self.timesheet_ids) > 1:
                cond = 'IN'
                rec = tuple(self.timesheet_ids.ids)
            self.env.cr.execute("""
                                UPDATE account_analytic_line SET state = 'draft' WHERE id %s %s;
                                DELETE FROM account_analytic_line WHERE ref_id %s %s;
                        """ % (cond, rec, cond, rec))
            self.env.invalidate_all()
        if self.odo_log_id:
            self.env['fleet.vehicle.odometer'].sudo().search([('id', '=', self.odo_log_id.id)]).unlink()
            self.odo_log_id = False
        if self.overtime_analytic_line_id:
            self.overtime_analytic_line_id.unlink()
        return res



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
                if i < 5 and float_compare(hour, 8, precision_digits=3, precision_rounding=None) < 0:
                    raise UserError(_('Each day from Monday to Friday needs to have at least 8 logged hours.'))
        return super(HrTimesheetSheet, self).action_timesheet_confirm()

    @api.one
    def create_overtime_entries(self):
        analytic_line = self.env['account.analytic.line']
        if self.overtime_hours > 0 and not self.overtime_analytic_line_id:
            company_id = self.company_id.id if self.company_id else self.employee_id.company_id.id
            overtime_project = self.env['project.project'].search([('company_id', '=', company_id), ('overtime_hrs', '=', True)])
            overtime_project_task = self.env['project.task'].search([('project_id', '=', overtime_project.id), ('standard', '=', True)])
            if not overtime_project:
                raise ValidationError(_("Please define project with 'Overtime Hours'!"))

            uom = self.env.ref('product.product_uom_hour').id
            analytic_line = analytic_line.create({
                'name':'Overtime line',
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
            if self.overtime_hours > 0:
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
        if self.timesheet_ids:
            cond = '='
            rec = self.timesheet_ids.ids[0]
            if len(self.timesheet_ids) > 1:
                cond = 'IN'
                rec = tuple(self.timesheet_ids.ids)
            self.env.cr.execute("""
                                    UPDATE account_analytic_line SET state = 'open' WHERE id %s %s
                            """ % (cond, rec))
        self.create_overtime_entries()
        self.generate_km_lines()
        return res

    @job(default_channel='root.timesheet')
    def _recompute_timesheet(self, fields):
        """Recompute this sheet and its lines.
        This function is called asynchronically after create/write"""
        for this in self:
            this.modified(fields)
            if 'timesheet_ids' not in fields:
                continue
            this.mapped('timesheet_ids').modified(
                self.env['account.analytic.line']._fields.keys()
            )
        self.recompute()

    def _queue_recompute_timesheet(self, fields):
        """Queue a recomputation if appropriate"""
        if not fields or not self:
            return
        return self.with_delay(
            description=' '.join([self.employee_id.name, self.display_name, self.date_from[:4]]),
            identity_key=self._name + ',' + ','.join(map(str, self.ids)) +
            ',' + ','.join(fields)
        )._recompute_timesheet(fields)

    @api.model
    def create(self, vals):
        result = super(
            HrTimesheetSheet, self.with_context(_timesheet_write=True)
        ).create(vals)
        result._queue_recompute_timesheet(['timesheet_ids'])
        return result

    @api.one
    def write(self, vals):
        result = super(
            HrTimesheetSheet, self.with_context(_timesheet_write=True)
        ).write(vals)
        self.env['account.analytic.line'].search([
            ('sheet_id', '=', self.id),
            '|',
            ('unit_amount', '>', 24),
            ('unit_amount', '<', 0),
        ]).write({'unit_amount': 0})
        if 'timesheet_ids' in vals:
            self._queue_recompute_timesheet(['timesheet_ids'])
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

    def copy_with_query(self, last_week_timesheet_id=None):
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
                month_id,
                week_id,
                account_department_id,               
                chargeable,
                operating_unit_id,
                project_operating_unit_id,
                correction_charge,
                ref_id,
                actual_qty,
                planned_qty,
                planned,
                kilometers,
                state,
                non_invoiceable_mileage,
                product_uom_id )
        SELECT  DISTINCT ON (task_id)
                aal.create_uid as create_uid,
                aal.user_id as user_id,
                aal.account_id as account_id,
                aal.company_id as company_id,
                aal.write_uid as write_uid,
                0 as amount,
                0 as unit_amount,
                aal.date + 7 as date,
                %(create)s as create_date,
                %(create)s as write_date,
                aal.partner_id as partner_id,
                '/' as name,
                aal.code as code,
                aal.currency_id as currency_id,
                aal.ref as ref,
                aal.general_account_id as general_account_id,
                aal.move_id as move_id,
                aal.product_id as product_id,
                0 as amount_currency,
                aal.project_id as project_id,
                aal.department_id as department_id,
                aal.task_id as task_id,
                %(sheet_aal)s as sheet_id,
                aal.ts_line as ts_line,
                dr.id as month_id,
                %(week_id_aal)s as week_id,
                aal.account_department_id as account_department_id,
                aal.chargeable as chargeable,
                aal.operating_unit_id as operating_unit_id,
                aal.project_operating_unit_id as project_operating_unit_id,
                aal.correction_charge as correction_charge,
                NULL as ref_id,
                0 as actual_qty,
                0 as planned_qty,
                aal.planned as planned,
                0 as kilometers,
                'draft' as state,
                CASE
                  WHEN ip.invoice_mileage IS NULL THEN true
                  ELSE ip.invoice_mileage
                END AS non_invoiceable_mileage,
                aal.product_uom_id as product_uom_id
        FROM account_analytic_line aal
             LEFT JOIN project_project pp 
             ON pp.id = aal.project_id
             LEFT JOIN account_analytic_account aaa
             ON aaa.id = aal.account_id
             LEFT JOIN project_invoicing_properties ip
             ON ip.id = pp.invoice_properties
             RIGHT JOIN hr_timesheet_sheet_sheet hss
             ON hss.id = aal.sheet_id
             LEFT JOIN date_range dr 
             ON (dr.type_id = 2 and dr.date_start <= aal.date +7 and dr.date_end >= aal.date + 7)
             LEFT JOIN hr_employee he 
             ON (hss.employee_id = he.id)
             LEFT JOIN task_user tu 
             ON (tu.task_id = aal.task_id and tu.user_id = aal.user_id and aal.date >= tu.from_date)
        WHERE hss.id = %(sheet_select)s
             AND aal.ref_id IS NULL             
             AND aal.task_id NOT IN 
                 (
                 SELECT DISTINCT task_id
                 FROM account_analytic_line
                 WHERE sheet_id = %(sheet_aal)s
                 )
             ;"""

        self.env.cr.execute(query, {'create': str(fields.Datetime.to_string(fields.datetime.now())),
                                    'week_id_aal': self.week_id.id,
                                    'sheet_select': last_week_timesheet_id,
                                    'sheet_aal': self.id,
                                    }
                            )
        self.env.invalidate_all()
        return True

    def generate_km_lines(self):
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
                month_id,
                week_id,
                account_department_id,               
                chargeable,
                operating_unit_id,
                project_operating_unit_id,
                correction_charge,
                ref_id,
                actual_qty,
                planned_qty,
                planned,
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
                aal.month_id as month_id,
                aal.week_id as week_id,
                aal.account_department_id as account_department_id,
                aal.chargeable as chargeable,
                aal.operating_unit_id as operating_unit_id,
                aal.project_operating_unit_id as project_operating_unit_id,
                aal.correction_charge as correction_charge,
                aal.id as ref_id,
                aal.actual_qty as actual_qty,
                aal.planned_qty as planned_qty,
                aal.planned as planned,
                0 as kilometers,
                'open' as state,
                CASE
                  WHEN ip.invoice_mileage IS NULL THEN true
                  ELSE ip.invoice_mileage
                END AS non_invoiceable_mileage,
                %(uom)s as product_uom_id
        FROM account_analytic_line aal
             LEFT JOIN project_project pp 
             ON pp.id = aal.project_id
             LEFT JOIN account_analytic_account aaa
             ON aaa.id = aal.account_id
             LEFT JOIN project_invoicing_properties ip
             ON ip.id = pp.invoice_properties
             RIGHT JOIN hr_timesheet_sheet_sheet hss
             ON hss.id = aal.sheet_id
             LEFT JOIN date_range dr 
             ON (dr.type_id = 2 and dr.date_start <= aal.date +7 and dr.date_end >= aal.date + 7)
             LEFT JOIN hr_employee he 
             ON (hss.employee_id = he.id)
             LEFT JOIN task_user tu 
             ON (tu.task_id = aal.task_id and tu.user_id = aal.user_id and aal.date >= tu.from_date)
        WHERE hss.id = %(sheet_select)s
             AND aal.ref_id IS NULL             
             AND aal.kilometers > 0 ;
        """
        self.env.cr.execute(query, {'create': str(fields.Datetime.to_string(fields.datetime.now())),
                                    'week_id_aal': self.week_id.id,
                                    'uom': self.env.ref('product.product_uom_km').id,
                                    'sheet_select': self.id,
                                    }
                            )
        self.env.invalidate_all()
        return True


class DateRangeGenerator(models.TransientModel):
    _inherit = 'date.range.generator'

    @api.multi
    def _compute_date_ranges(self):
        self.ensure_one()
        vals = rrule(freq=self.unit_of_time,
                     interval=self.duration_count,
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
