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

    @api.depends('date',
                 'user_id',
                 'project_id',
                 'sheet_id_computed.date_to',
                 'sheet_id_computed.date_from',
                 'sheet_id_computed.employee_id')
    def _compute_sheet(self):
        """Links the timesheet line to the corresponding sheet
        """
        for ts_line in self.filtered('project_id'):
            if not ts_line.ts_line :
                continue
            sheets = self.env['hr_timesheet_sheet.sheet'].search(
                [('date_to', '>=', ts_line.date),
                 ('date_from', '<=', ts_line.date),
                 ('employee_id.user_id.id', '=', ts_line.user_id.id),
                 ('state', 'in', ['draft', 'new'])])
            if sheets:
                # [0] because only one sheet possible for an employee between
                # 2 dates
                ts_line.sheet_id_computed = sheets[0]
                ts_line.sheet_id = sheets[0]

    @api.depends('project_id.chargeable',
                 'project_id.correction_charge',
                 'project_id.user_id',
                 'project_id.invoice_properties.expenses',
                 'sheet_id',
                 'account_id',
                 'unit_amount',
                 'task_id',
                 'product_uom_id',
                 'planned')
    def _compute_analytic_line(self):
        """Calculates a number of fields
        """
        UomHrs = self.env.ref("product.product_uom_hour").id
        for line in self:
            line.project_operating_unit_id = \
                line.account_id.operating_unit_ids \
                and line.account_id.operating_unit_ids[0] or False
            if line.project_id:
                line.chargeable = line.project_id.chargeable
                line.correction_charge = line.project_id.correction_charge
                line.project_mgr = line.project_id.user_id or False
                if line.project_id.invoice_properties:
                    line.expenses = line.project_id.invoice_properties.expenses
            elif line.account_id:
                line.project_mgr = line.account_id.project_ids.user_id or False
            if line.task_id and line.user_id:
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
                    if line.product_uom_id.id == UomHrs:
                        line.ts_line = True
                task = line.task_id
                user = line.user_id
                line.product_id = self.get_task_user_product(task.id, user.id) or False
                if not line.product_id:
                    raise ValidationError(_(
                        'Please fill in Fee Rate Product in employee %s.\n '
                    ) % line.user_id.name)
                # taskuser = self.env['task.user'].search(
                #     [('task_id', '=', task.id), ('user_id', '=', user.id)], limit=1)
                # if taskuser and taskuser.fee_rate or taskuser.product_id:
                #     fee_rate = taskuser.fee_rate or taskuser.product_id.lst_price or 0.0
                # else:
                #     employee = user._get_related_employees()
                #     fee_rate = employee.fee_rate or employee.product_id.lst_price or 0.0
                # if line.product_uom_id and line.product_uom_id.id == \
                #         self.env.ref('product.product_uom_hour').id:
                #     line.amount = line.unit_amount * - fee_rate

            if line.planned:
                if line.select_week_id:
                    line.week_id = line.select_week_id.id


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
    
    @api.model
    def default_get(self, fields):
        import pdb;
        # pdb.set_trace();
        context = self._context
        res = super(AccountAnalyticLine, self).default_get(fields)

        if 'planning_lines' in context:
            project = self.env['project.project']
            project_id = context.get('default_project_id', project)
            task_id = context.get('default_task_id', False)
            project = project.browse(project_id)
            account_id = project.analytic_account_id
            operating_unit_id = account_id.operating_unit_ids and account_id.operating_unit_ids[0] or False
            res.update({'operating_unit_id':operating_unit_id, 'name':'/', 'task_id':task_id})
        # print '.......context...default_get........\n\n',context
        # print '.......res...default_get........\n\n', res
        return res


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
    week_id = fields.Many2one(
        'date.range',
        compute=_compute_analytic_line,
        string='Week',
        store=True,
    )
    month_id = fields.Many2one(
        'date.range',
        compute=_compute_analytic_line,
        string='Month',
        store=True,
    )
    operating_unit_id = fields.Many2one(
        'operating.unit',
        compute=_compute_analytic_line,
        string='Operating Unit',
        store=True
    )
    project_operating_unit_id = fields.Many2one(
        'operating.unit',
        compute=_compute_analytic_line,
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
        compute=_compute_analytic_line,
        string='Timesheet line',
        store=True,
    )
    correction_charge = fields.Boolean(
        compute=_compute_analytic_line,
        string='Correction Chargeability',
        store=True,
    )
    chargeable = fields.Boolean(
        compute=_compute_analytic_line,
        string='Chargeable',
        store=True,
    )
    expenses = fields.Boolean(
        compute=_compute_analytic_line,
        string='Expenses',
    )
    project_mgr = fields.Many2one(
        comodel_name='res.users',
        compute=_compute_analytic_line,
        store=True
    )

    ot = fields.Boolean(
        string='Overtime',
    )
    planning_id = fields.Many2one('magnus.planning', string='Planning')


    @api.model
    def get_task_user_product(self, task_id, user_id):
        taskUserObj = self.env['task.user']
        product_id = False
        if task_id and user_id:
            taskUser = taskUserObj.search([('task_id', '=', task_id), ('user_id', '=', user_id)],
                                          limit=1)
            if taskUser and taskUser.product_id:
                product_id = taskUser.product_id.id if taskUser and taskUser.product_id else False
            else:
                #check standard task for fee earners
                project_id = self.env['project.task'].browse(task_id).project_id
                standard_task = project_id.task_ids.filtered('standard')
                if standard_task:
                    taskUser = taskUserObj.search([('task_id', '=', standard_task.id), ('user_id', '=', user_id)],
                                                  limit=1)
                    product_id = taskUser.product_id.id if taskUser and taskUser.product_id else False

        if user_id and not product_id:
            user = self.env['res.users'].browse(user_id)
            employee = user._get_related_employees()
            product_id = employee.product_id and employee.product_id.id or False
        return product_id

    @api.model
    def get_fee_rate(self, task_id=None, user_id=None):
        uid = user_id or self.user_id.id or False
        tid = task_id or self.task_id.id or False
        amount, fr = 0.0, 0.0
        if uid and tid:
            task_user = self.env['task.user'].search([
                ('user_id', '=', uid),
                ('task_id', '=', tid)], limit=1)
            if task_user and task_user.fee_rate or task_user.product_id:
                fr = task_user.fee_rate or task_user.product_id.lst_price or 0.0
            # check standard task for fee earners
            if not fr:
                project_id = self.env['project.task'].browse(tid).project_id
                standard_task = project_id.task_ids.filtered('standard')
                if standard_task:
                    task_user = self.env['task.user'].search([('task_id', '=', standard_task.id), ('user_id', '=', uid)],
                                                  limit=1)
                    if task_user and task_user.fee_rate or task_user.product_id:
                        fr = task_user.fee_rate or task_user.product_id.lst_price or 0.0
        if not fr :
            employee = self.env['hr.employee'].search([('user_id', '=', uid)])
            fr = employee.fee_rate or employee.product_id and employee.product_id.lst_price
            if self.product_id and self.product_id != employee.product_id:
                fr = self.product_id.lst_price
        return fr

    @api.model
    def get_fee_rate_amount(self, task_id=None, user_id=None, unit_amount=0.0):
        fr = self.get_fee_rate(task_id=task_id, user_id=user_id)
        unit_amount = unit_amount if unit_amount else self.unit_amount
        amount = - unit_amount * fr
        return amount

    # def _fetch_emp_plan(self):
    #     emp = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
    #     return True if emp and emp.planning_week else False
    #
    # @api.onchange('user_id')
    # def _onchange_users(self):
    #     self.planned = self._fetch_emp_plan()

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
            self.date = self.select_week_id.date_start

    @api.model
    def create(self, vals):
        # print '--------create--vals----111111111--',vals
        # print '--------create----context--111111111--', self.env.context
        if self.env.context.get('default_planned', False):
            if vals.get('select_week_id', False) and not vals.get('week_id', False):
                vals['week_id'] = vals['select_week_id']
                vals['task_id'] = self.env.context.get('default_task_id', False)
            # if vals.get('project_id', False):
            #     vals['planned'] = True

        task_id = vals.get('task_id', False)
        user_id = vals.get('user_id', False)

        #some cases product id is missing
        product_id = self.get_task_user_product(task_id, user_id) or False
        if not product_id and user_id:
            user = self.env.user.browse(user_id)
            raise ValidationError(_(
                'Please fill in Fee Rate Product in employee %s.\n '
                ) % user.name)
        if product_id:
            vals['product_id'] = product_id

        if vals.get('ts_line', False):
            unit_amount = vals.get('unit_amount', False)
            vals['amount'] = self.get_fee_rate_amount(task_id, user_id, unit_amount)
        # print '--------create--------',vals
        return super(AccountAnalyticLine, self).create(vals)

    @api.multi
    def write(self, vals):
        # print '--------write--vals----111111111--', vals
        for aal in self:
            if 'select_week_id' in vals or 'planned' in vals:
                if self.env.context.get('default_planned', False):
                    if vals.get('select_week_id', False):
                        vals['week_id'] = vals['select_week_id']
                    # if aal.project_id:
                    #     vals['planned'] = True

            task_id = vals.get('task_id', aal.task_id and aal.task_id.id)
            user_id = vals.get('user_id', aal.user_id and aal.user_id.id)

            # some cases product id is missing
            if not vals.get('product_id', aal.product_id) and user_id:
                if user_id and not vals.get('product_id', aal.product_id):
                    product_id = aal.get_task_user_product(task_id, user_id) or False
                if not product_id:
                    user = self.env.user.browse(user_id)
                    raise ValidationError(_(
                        'Please fill in Fee Rate Product in employee %s.\n '
                    ) % user.name)
                vals['product_id'] = product_id

            ts_line = vals.get('ts_line', aal.ts_line)
            if ts_line:
                unit_amount = vals.get('unit_amount', aal.unit_amount)
                vals['amount'] = aal.get_fee_rate_amount(task_id, user_id, unit_amount)
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

    @api.model
    def get_week_read(self, date_start):
        return self.env['date.range'].search([('date_start', '=', date_start)]).read(['date_start','name'])
