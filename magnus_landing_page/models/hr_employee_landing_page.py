# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date


class hr_employee_landing_page(models.TransientModel):
    _name = 'hr.employee.landing_page'
    _description = 'Employee landing page'
    _rec_name = 'employee_id'

    @api.depends('employee_id')
    def _compute_all(self):

        #current week
        self.env.cr.execute("""SELECT * FROM date_range 
                                WHERE date_start <= NOW()::date 
                                AND date_end >=NOW()::date
                                AND type_id = (SELECT id FROM date_range_type WHERE calender_week = true)
                                LIMIT 1
                            """)
        current_week_id = self.env.cr.fetchone()[0]

        next_week_id = self.get_upcoming_week()
        if current_week_id == next_week_id.id or current_week_id < next_week_id.id:
            self.current_week = True
        else:
            self.current_week = False

        if next_week_id:
            self.next_week_id = next_week_id.name
            self.next_week_id1 = next_week_id.name

        #compute vaction balance
        self.env.cr.execute("""
                SELECT allocated_leaves-leaves_taken FROM
                    (SELECT 
                        SUM(number_of_hours_temp) as allocated_leaves, employee_id
                        FROM hr_holidays                               
                        WHERE employee_id = %s
                          AND type = %s
                          AND state = %s
                        GROUP BY employee_id) hr1
                    JOIN (SELECT 
                        SUM(number_of_hours_temp) as leaves_taken, employee_id
                        FROM hr_holidays                               
                        WHERE employee_id = %s
                          AND type = %s
                          AND state = %s
                        GROUP BY employee_id ) hr2
                    on hr1.employee_id = hr2.employee_id
        """, (self.employee_id.id, 'add', 'validate', self.employee_id.id, 'remove', 'written'))
        vacation_balance = 0
        for x in self.env.cr.fetchall():
            vacation_balance += x[0]

        self.vacation_balance = vacation_balance

        user_id = self.env.user.id
        # compute overtime balance
        self.env.cr.execute("""
                SELECT overtime_hrs-overtime_taken FROM
                    (SELECT 
                        SUM(unit_amount) as overtime_hrs, user_id
                        FROM account_analytic_line                               
                        WHERE user_id = %s
                          AND ot = true
                          AND product_uom_id = 5
                        GROUP BY user_id) aa1
                    JOIN (SELECT 
                        SUM(unit_amount) as overtime_taken, user_id
                        FROM account_analytic_line                               
                        WHERE user_id = %s
                          AND state != %s
                          AND project_id IN (SELECT id FROM project_project WHERE overtime = true)
                          AND product_uom_id = 5
                        GROUP BY user_id ) aa2
                    on aa1.user_id = aa2.user_id
                """, (user_id, user_id, 'draft'))
        overtime_balance = 0
        for x in self.env.cr.fetchall():
            overtime_balance += x[0]
        self.overtime_balance = overtime_balance

        current_year = datetime.now()
        first_date = str(current_year.year) + '-1-1'
        last_date = str(current_year.year) + '-12-31'
        hr_timesheet = self.env['hr_timesheet.sheet']

        # compute private milage, Note: private_mileage is an computed field can't be calulated through SQl
        self.private_km_balance = sum(hr_timesheet.search([('employee_id', '=', self.employee_id.id),'&',('week_id.date_start','>=',first_date),('week_id.date_end','<=',last_date)]).mapped('private_mileage'))

        #my timesheet status
        self.env.cr.execute("""SELECT 
                                    id
                                    FROM hr_timesheet_sheet_sheet                               
                                    WHERE employee_id = %s
                                    AND state IN %s
                                    ORDER BY id DESC
                                    LIMIT 10                                  
                                        """, (self.employee_id.id, ('draft', 'new', 'confirm'),))
        timesheet_ids = [x[0] for x in self.env.cr.fetchall()]
        self.emp_timesheet_status_ids = [(6, 0, timesheet_ids)]

        #to be approved timesheet
        self.env.cr.execute("""SELECT 
                                id
                                FROM hr_timesheet_sheet_sheet                               
                                WHERE
                                state != 'done' AND
                                 id IN 
                                    (SELECT hr_timesheet_sheet_sheet_id 
                                    FROM hr_timesheet_sheet_sheet_res_users_rel 
                                    WHERE res_users_id = %s)
                                 ORDER BY id DESC
                                  LIMIT 10 
                                """, (user_id,))
        to_be_approved_sheets = [x[0] for x in self.env.cr.fetchall()]
        self.emp_timesheet_to_be_approved_ids = [(6, 0, to_be_approved_sheets)]

        # my expense status
        self.env.cr.execute("""SELECT 
                    id
                    FROM hr_expense_sheet                               
                    WHERE employee_id = %s
                    AND state NOT IN %s
                    ORDER BY id DESC
                    LIMIT 10 
                    """, (self.employee_id.id, ('post', 'done', 'cancel'),))
        expense_ids = [x[0] for x in self.env.cr.fetchall()]
        self.emp_expense_status_ids = [(6, 0, expense_ids)]

        # expense to be approved
        # self.env.cr.execute("""SELECT
        #                     id
        #                     FROM hr_expense_sheet
        #                     WHERE state = 'submit'
        #                     ORDER BY id
        #                     LIMIT 10
        #                     """)
        # to_be_approved_expense_ids = [x[0] for x in self.env.cr.fetchall()]

        to_be_approved_expense_ids = self.env['hr.expense.sheet'].search([('employee_id', '!=', self.employee_id.id),('state', '=', 'submit')], order='id Desc', limit=10)
        self.emp_expense_to_be_approved_ids = [(6, 0, to_be_approved_expense_ids.ids)]


    def _default_employee(self):
        emp_ids = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee, required=True)
    next_week_id = fields.Char(string="Week To Submit")
    next_week_id1 = fields.Char(string="Week To Submit")
    vacation_balance = fields.Integer(compute='_compute_all', string="Vacation Balance")
    overtime_balance = fields.Integer(compute='_compute_all', string="Overtime Balance")
    private_km_balance = fields.Integer(compute='_compute_all', string="Private Mileage Balance")
    emp_timesheet_status_ids = fields.Many2many('hr_timesheet_sheet.sheet', compute='_compute_all', string="My Timesheet Status")
    emp_timesheet_to_be_approved_ids = fields.Many2many('hr_timesheet_sheet.sheet', compute='_compute_all', string="Timesheet To Be Approved")
    emp_expense_status_ids = fields.Many2many('hr.expense.sheet', compute='_compute_all', string="My Expense Status")
    emp_expense_to_be_approved_ids = fields.Many2many('hr.expense.sheet', compute='_compute_all', string="Expense To Be Approved")
    current_week = fields.Boolean(compute='_compute_all')


    def get_upcoming_week(self):
        result = self.env['hr.timesheet.current.open'].open_timesheet()
        hr_timesheet = self.env['hr_timesheet_sheet.sheet']
        if 'res_id' in result:
            return hr_timesheet.browse(result['res_id']).week_id
        return hr_timesheet.get_week_to_submit()

    @api.multi
    def action_view_timesheet(self):
        self.ensure_one()
        return self.env['hr.timesheet.current.open'].open_timesheet()

    @api.multi
    def action_view_leaves_dashboard(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        tree_res = ir_model_data.get_object_reference('magnus_landing_page', 'view_holiday_landing_apge')
        tree_id = tree_res and tree_res[1] or False
        self.env.cr.execute("""SELECT 
                                    id
                                    FROM hr_holidays                               
                                    WHERE employee_id = %s
                                    AND ((type = 'add'
                                    AND state = 'validate' ) OR 
                                    (type = 'remove'
                            AND state = 'written'))                  
                                    """, (self.employee_id.id,))

        holidays = [x[0] for x in self.env.cr.fetchall()]
        return {
            'name': _('Leaves'),
            'view_type': 'from',
            'view_mode': 'tree',
            'res_model': 'hr.holidays',
            'view_id': False,
            'views': [(tree_id, 'tree')],
            'domain': [('id', 'in', holidays)],
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
    def action_view_analytic_tree(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        tree_res = ir_model_data.get_object_reference('magnus_landing_page', 'view_account_analytic_line_landing_page_tree')
        tree_id = tree_res and tree_res[1] or False

        user_id = self.env.user.id
        self.env.cr.execute("""
                    SELECT aa1.id, aa2.id FROM
                        (SELECT 
                            id, user_id
                            FROM account_analytic_line                               
                            WHERE user_id = %s
                              AND ot = true
                            ) aa1
                        JOIN (SELECT id, user_id
                            FROM account_analytic_line                               
                            WHERE user_id = %s
                              AND state != %s
                              AND project_id IN (SELECT id FROM project_project WHERE overtime = true)
                             ) aa2
                        on aa1.user_id = aa2.user_id
                    """, (user_id, user_id, 'draft'))

        entries = [t for item in self.env.cr.fetchall() for t in item]
        entries = list(set(entries))


        return {
            'name': _('Analytic Entries'),
            'view_type': 'from',
            'view_mode': 'tree',
            'res_model': 'account.analytic.line',
            'view_id': False,
            'views': [(tree_id, 'tree')],
            'domain': [('id', 'in', entries)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }



    @api.multi
    def no_popup_window(self):
        return {'type': 'ir.actions.act_window_close'}