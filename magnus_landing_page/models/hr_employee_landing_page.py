# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class hr_employee_landing_page(models.TransientModel):
    _name = 'hr.employee.landing_page'
    _description = 'Employee landing page'
    _rec_name = 'employee_id'

    @api.depends('employee_id')
    def _compute_all(self):

        # compute timesheet week
        next_week_id = self.get_upcoming_week()
        if next_week_id:
            self.next_week_id = next_week_id.name

        #compute vaction balance
        hr_holidays = self.env['hr.holidays']
        emp_holidays = hr_holidays.search([('employee_id', '=', self.employee_id.id)])
        allocated_leaves = sum(emp_holidays.filtered(lambda eh: eh.type == 'add').mapped('number_of_hours_temp'))
        applied_leaves = sum(emp_holidays.filtered(lambda eh: eh.type == 'remove').mapped('number_of_hours_temp'))
        self.vacation_balance = allocated_leaves - applied_leaves

        # compute overtime balance
        analytic_line = self.env['account.analytic.line']

        overtime_hrs = sum(analytic_line.search([('ot', '=', True)]).mapped('unit_amount'))#overtime hrs entries isn't updated by any action
        overtime_taken = sum(analytic_line.search([('project_id.overtime', '=', True), ('state', '!=', 'draft')]).mapped('unit_amount'))
        self.overtime_balance = overtime_hrs - overtime_taken

        hr_timesheet = self.env['hr_timesheet_sheet.sheet']

        # compute private milage
        self.private_km_balance = sum(hr_timesheet.search([('employee_id', '=', self.employee_id.id)]).mapped('private_mileage'))

        #my timesheet status
        timesheet_ids = hr_timesheet.search([('employee_id', '=', self.employee_id.id), ('state', 'in', ('draft', 'new', 'confirm'))])
        self.emp_timesheet_status_ids = [(6, 0, timesheet_ids.ids)]

        #my to be approved timesheet
        to_be_approved_sheets = hr_timesheet.search([('state', '!=', 'done'), ('validator_user_ids', '=', self.env.uid)])
        self.emp_timesheet_to_be_approved_ids = [(6, 0, to_be_approved_sheets.ids)]

        hr_expense_sheet = self.env['hr.expense.sheet']

        # my expense status
        expense_ids = hr_expense_sheet.search([('employee_id', '=', self.employee_id.id)])
        self.emp_expense_status_ids = [(6, 0, expense_ids.ids)]

        # expense to be approved
        to_be_approved_expense_ids = hr_expense_sheet.search([('state', '=', 'submit')])
        self.emp_expense_to_be_approved_ids = [(6, 0, to_be_approved_expense_ids.ids)]


    def _default_employee(self):
        emp_ids = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee, required=True)
    next_week_id = fields.Char(string="Week To Submit")
    vacation_balance = fields.Integer(compute='_compute_all', string="Vacation Balance")
    overtime_balance = fields.Integer(compute='_compute_all', string="Overtime Balance")
    private_km_balance = fields.Integer(compute='_compute_all', string="Private Mileage Balance")
    emp_timesheet_status_ids = fields.Many2many('hr_timesheet_sheet.sheet', compute='_compute_all', string="My Timesheet Status")
    emp_timesheet_to_be_approved_ids = fields.Many2many('hr_timesheet_sheet.sheet', compute='_compute_all', string="Timesheet To Be Approved")
    emp_expense_status_ids = fields.Many2many('hr.expense.sheet', compute='_compute_all', string="My Expense Status")
    emp_expense_to_be_approved_ids = fields.Many2many('hr.expense.sheet', compute='_compute_all', string="Expense To Be Approved")


    def get_upcoming_week(self):
        date_range = self.env['date.range']
        upcoming_week = date_range
        dt = datetime.now()

        emp_id = self.employee_id.id

        timesheets = self.env['hr_timesheet_sheet.sheet'].search([('employee_id', '=', emp_id)])
        logged_weeks = timesheets.mapped('week_id').ids if timesheets else []

        date_range_type_cw_id = self.env.ref(
            'magnus_date_range_week.date_range_calender_week').id
        employement_date = self.employee_id.official_date_of_employment
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
        week = date_range.search([('type_id', '=', date_range_type_cw_id), ('date_start', '=', dt - timedelta(days=dt.weekday()))],limit=1)
        if week or past_weeks:
            if past_weeks and past_weeks.id not in logged_weeks:
                upcoming_week = past_weeks
            elif week and week.id not in logged_weeks:
                upcoming_week = week
            else:
                next_week = date_range.search([
                    ('id', 'not in', logged_weeks),
                    ('type_id', '=', date_range_type_cw_id),
                    ('date_start', '>', dt - timedelta(days=dt.weekday()))
                ], order='date_start', limit=1)
                if next_week:
                    upcoming_week = next_week

        return upcoming_week

    @api.multi
    def action_view_timesheet(self):
        self.ensure_one()
        return self.env['hr.timesheet.current.open'].open_timesheet()

    @api.multi
    def action_view_leaves_dashboard(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        tree_res = ir_model_data.get_object_reference('hr_holidays', 'view_holiday_simple')
        tree_id = tree_res and tree_res[1] or False
        return {
            'name': _('Leaves'),
            'view_type': 'from',
            'view_mode': 'tree',
            'res_model': 'hr.holidays',
            'view_id': False,
            'views': [(tree_id, 'tree')],
            'domain': [('employee_id', '=', self.employee_id.id), ('holiday_type','=','employee'), ('type', '=', 'remove'), ('state', '!=', 'refuse')],
            'context': {'search_default_year': 1, 'search_default_group_employee': 1},
            'target':'current',
            'type': 'ir.actions.act_window',
        }


    @api.multi
    def action_view_timesheet_tree(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        tree_res = ir_model_data.get_object_reference('hr_timesheet_sheet', 'hr_timesheet_sheet_tree_simplified')
        tree_id = tree_res and tree_res[1] or False
        return {
            'name': _('Timesheet'),
            'view_type': 'from',
            'view_mode': 'tree',
            'res_model': 'hr_timesheet_sheet.sheet',
            'view_id': False,
            'views': [(tree_id, 'tree')],
            'domain': [('employee_id.user_id', '=', self.env.uid)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def no_popup_window(self):
        return {'type': 'ir.actions.act_window_close'}