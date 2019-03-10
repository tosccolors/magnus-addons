# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'
    _order = 'date desc'

    @api.depends('date', 'user_id', 'project_id', 'account_id','sheet_id_computed.date_to',
                 'sheet_id_computed.date_from',
                 'sheet_id_computed.employee_id', 'task_id', 'product_uom_id', 'planned')
    def _compute_sheet(self):
        """Links the timesheet line to the corresponding sheet
        """
        UomHrs = self.env.ref("product.product_uom_hour").id
        for line in self:
            line.project_operating_unit_id = \
                line.account_id.operating_unit_ids \
                and line.account_id.operating_unit_ids[0] or False
            if line.project_id:
                if line.task_id and line.user_id and not line.move_id:
                    uou = line.user_id._get_operating_unit_id()
                    if uou:
                        line.operating_unit_id = uou
                    if not line.planned:
                        if line.sheet_id.week_id and line.date:
                            line.week_id = line.sheet_id.week_id
                            line.month_id = line.find_daterange_month(line.date)
                        elif line.date:
                            line.week_id = line.find_daterange_week(line.date)
                            line.month_id = line.find_daterange_month(line.date)
                        elif not line.child_ids == []:
                            line.week_id = line.find_daterange_week(line.child_ids.date)
                            line.month_id = line.find_daterange_month(line.child_ids.date)
                        if line.product_uom_id.id == UomHrs:
                            line.ts_line = True
                    if not line.ts_line or line.planned:
                        continue
            else:
                continue
            sheets = self.env['hr_timesheet_sheet.sheet'].search(
                [('week_id', '=', line.week_id.id),
                 ('employee_id.user_id.id', '=', line.user_id.id),
                 ('state', 'in', ['draft', 'new'])])
            if sheets:
                # [0] because only one sheet possible for an employee between 2 dates
                line.sheet_id_computed = sheets[0]
                line.sheet_id = sheets[0]


    def find_daterange_week(self, date):
        """
        try to find a date range with type 'week'
        with @param:date contained in its date_start/date_end interval
        """
        date_range_type_cw_id = self.env.ref(
            'magnus_date_range_week.date_range_calender_week').id
        s_args = [
            ('type_id', '=', date_range_type_cw_id),
            ('date_start', '<=', date),
            ('date_end', '>=', date),
            '|',
            ('company_id', '=', self.company_id.id),
            ('company_id', '=', False),
        ]
        date_range = self.env['date.range'].search(s_args,
                                                   limit=1,
                                                   order='company_id asc')
        return date_range

    def find_daterange_month(self, date):
        """
        try to find a date range with type 'month'
        with @param:date contained in its date_start/date_end interval
        """
        date_range_type_fm_id = self.env.ref(
            'account_fiscal_month.date_range_fiscal_month').id

        s_args = [
            ('type_id', '=', date_range_type_fm_id),
            ('date_start', '<=', date),
            ('date_end', '>=', date),
            '|',
            ('company_id', '=', self.company_id.id),
            ('company_id', '=', False),
        ]
        date_range = self.env['date.range'].search(
            s_args,
            limit=1,
            order='company_id asc'
        )
        return date_range


    sheet_id = fields.Many2one(
        ondelete='cascade'
    )
    kilometers = fields.Integer(
        'Kilometers'
    )
    non_invoiceable_mileage = fields.Boolean(
        string='Invoice Mileage',
        store=True
    )
    ref_id = fields.Many2one(
        'account.analytic.line',
        string='Reference'
    )
    user_total_id = fields.Many2one(
        comodel_name='analytic.user.total',
        string='Summary Reference',
        index=True
    )
    week_id = fields.Many2one(
        'date.range',
        compute=_compute_sheet,
        string='Week',
        store=True,
    )
    month_id = fields.Many2one(
        'date.range',
        compute=_compute_sheet,
        string='Month',
        store=True,
    )
    correction_charge = fields.Boolean(
        related='project_id.correction_charge',
        string='Correction Chargeability',
        store=True,
    )
    chargeable = fields.Boolean(
        related='project_id.chargeable',
        string='Chargeable',
        store=True,
    )
    expenses = fields.Boolean(
        related='project_id.invoice_properties.expenses',
        string='Expenses',
    )
    operating_unit_id = fields.Many2one(
        'operating.unit',
        compute=_compute_sheet,
        string='Operating Unit',
        store=True
    )
    project_operating_unit_id = fields.Many2one(
        'operating.unit',
        compute=_compute_sheet,
        string='Project Operating Unit',
        store=True
    )
    task_id = fields.Many2one(
        'project.task', 'Task',
        ondelete='restrict'
    )
    select_week_id = fields.Many2one(
        'date.range',
        string='Week'
    )
    planned = fields.Boolean(
        string='Planned'
    )
    actual_qty = fields.Float(
        string='Actual Qty',
        compute='_get_qty',
        store=True
    )
    planned_qty = fields.Float(
        string='Planned Qty',
        compute='_get_qty',
        store=True
    )
    day_name = fields.Char(
        string="Day",
        compute='_get_day'
    )
    ts_line = fields.Boolean(
        compute=_compute_sheet,
        string='Timesheet line',
        store=True,
    )
    project_mgr = fields.Many2one(
        comodel_name='res.users',
        related='account_id.project_ids.user_id',
        store=True
    )


    @api.model
    def get_task_user_product(self, task_id, user_id):
        taskUserObj = self.env['task.user']
        product_id = False
        if task_id and user_id:
            taskUser = taskUserObj.search([('task_id', '=', task_id), ('user_id', '=', user_id)],
                                          limit=1)
            product_id = taskUser.product_id.id if taskUser and taskUser.product_id else False
        if not product_id:
            employee = self.env['hr.employee'].search([('user_id', '=', user_id)])
            product_id = employee.product_id and employee.product_id.id or False
        return product_id

    @api.model
    def get_fee_rate(self):
        uid = self.user_id.id or False
        tid = self.task_id.id or False
        amount, fr = 0.0, 0.0
        if uid and tid:
            task_user = self.env['task.user'].search([
                ('user_id', '=', uid),
                ('task_id', '=', tid)], limit=1)
            fr = task_user.fee_rate
        if not fr :
            employee = self.env['hr.employee'].search([('user_id', '=', uid)])
            fr = employee.fee_rate or employee.product_id and employee.product_id.lst_price
            if self.product_id and self.product_id != employee.product_id:
                fr = self.product_id.lst_price
        amount = - self.unit_amount * fr
        return amount


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
            date = self.find_daterange_week(self.date)
            self.week_id = date.id
            self.select_week_id = date.id

    @api.onchange('select_week_id')
    def _onchange_select_week(self):
        if self.select_week_id and self.select_week_id != self.week_id:
            self.week_id = self.select_week_id.id

    @api.model
    def create(self, vals):
#        fee_rate = 0
        if 'task_id' in vals and 'user_id' in vals:
            vals['product_id'] = self.get_task_user_product(vals['task_id'], vals['user_id']) or False
            if not vals['product_id']:
                raise UserError(_(
                    'Please fill in Fee Rate Product in employee %s.\n '
                    ) % vals['user_id'])
            taskuser = self.env['task.user'].search([('user_id','=', vals['user_id'])])
            if taskuser and taskuser.fee_rate or taskuser.product_id:
                fee_rate = taskuser.fee_rate or taskuser.product_id.lst_price or 0.0
            else:
                user = self.env['res.users'].browse(vals['user_id'])
                fee_rate = user._get_related_employees().fee_rate or user._get_related_employees().product_id.lst_price or 0.0
            if vals.get('product_uom_id', False) and vals['product_uom_id'] == self.env.ref('product.product_uom_hour').id:
                vals['amount'] = vals['unit_amount'] * - fee_rate
        if self.env.context.get('default_planned', False):
            if vals.get['select_week_id', False] and vals['week_id'] != vals['select_week_id']:
                vals['week_id'] = vals['select_week_id']
            if vals.get['project_id', False]:
                vals['planned'] = True
        return super(AccountAnalyticLine, self).create(vals)

    @api.multi
    def write(self, vals):
        for aal in self:
            task_id = vals['task_id'] if 'task_id' in vals else aal.task_id.id
            user_id = vals['user_id'] if 'user_id' in vals else aal.user_id.id
            unit_amount = vals['unit_amount'] if 'unit_amount' in vals else aal.unit_amount
            if task_id and user_id:
                vals['product_id'] = product_id = aal.get_task_user_product(task_id, user_id) or False
                if not product_id:
                    raise UserError(_(
                        'Please fill in Fee Rate Product in Employee %s.\n '
                    ) % vals['user_id'])
#                fr = 0
                taskuser = self.env['task.user'].search([('user_id', '=', user_id)])
                if taskuser and taskuser.fee_rate or taskuser.product_id:
                    fr = taskuser.fee_rate or taskuser.product_id.lst_price or 0.0
                else:
                    fr = user_id._get_related_employees().fee_rate \
                               or user_id._get_related_employees().product_id.lst_price or 0.0
                if (vals.get('product_uom_id', False)
                    and vals['product_uom_id'] == self.env.ref('product.product_uom_hour').id) \
                    or (aal.product_uom_id
                    and aal.product_uom_id == self.env.ref('product.product_uom_hour')):
                    vals['amount'] = - unit_amount * fr
            if self.env.context.get('default_planned', False) or aal.default_planned:
                if vals.get('select_week_id', False):
                    vals['week_id'] = vals('select_week_id')
                if aal.project_id:
                    vals['planned'] = True
        return super(AccountAnalyticLine, self).write(vals)



    @api.depends('unit_amount')
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
            line.day_name = str(datetime.strptime(line.date, '%Y-%m-%d').strftime("%m/%d/%Y"))+' ('+datetime.strptime(line.date, '%Y-%m-%d').strftime('%a')+')'

