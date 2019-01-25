# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime, timedelta

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'
    _order = 'date desc'

    # Todo: combine AccountAnalyticLine overrides of create() and write() from magnus_invoicing and magnus_timesheet
    #  and change dependency such, that magnus_timesheet is dependency of invoicing.

    @api.depends('date', 'user_id', 'project_id', 'sheet_id_computed.date_to', 'sheet_id_computed.date_from',
                 'sheet_id_computed.employee_id', 'task_id', 'product_uom_id', 'planned')
    def _compute_sheet(self):
        """Links the timesheet line to the corresponding sheet
        """
        UomHrs = self.env.ref("product.product_uom_hour").id
        for line in self:
            # if not line.project_id:
            #     super(AccountAnalyticLine, line)._compute_sheet()
            if line.project_id and line.task_id and line.user_id and not line.planned and line.product_uom_id.id == UomHrs:
                line.ts_line = True
            if not line.ts_line or line.planned:
                continue
            if line.sheet_id.week_id and line.date:
                line.week_id = line.sheet_id.week_id
                line.month_id = line.find_daterange_month(line.date)
            elif line.date:
                line.week_id = line.find_daterange_week(line.date)
                line.month_id = line.find_daterange_month(line.date)
            elif not line.child_ids == []:
                line.week_id = line.find_daterange_week(line.child_ids.date)
                line.month_id = line.find_daterange_month(line.child_ids.date)

            project = line.project_id
            line.correction_charge = project.correction_charge
            line.chargeable = project.chargeable
            line.expenses = project.invoice_properties.expenses if project.invoice_properties else False

            sheets = self.env['hr_timesheet_sheet.sheet'].search(
                [('week_id', '=', line.week_id.id),
                 ('employee_id.user_id.id', '=', line.user_id.id),
                 ('state', 'in', ['draft', 'new'])])
            if sheets:
                # [0] because only one sheet possible for an employee between 2 dates
                line.sheet_id_computed = sheets[0]
                line.sheet_id = sheets[0]

    def _search_sheet(self, operator, value):
        assert operator == 'in'
        ids = []
        for ts in self.env['hr_timesheet_sheet.sheet'].browse(value):
            self._cr.execute("""
                        SELECT l.id
                            FROM account_analytic_line l
                        WHERE %(date_to)s >= l.date
                            AND %(date_from)s <= l.date
                            AND %(user_id)s = l.user_id
                        GROUP BY l.id""", {'date_from': ts.date_from,
                                           'date_to': ts.date_to,
                                           'user_id': ts.employee_id.user_id.id, })
            ids.extend([row[0] for row in self._cr.fetchall()])
        return [('id', 'in', ids)]

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


    # invoiced = fields.Boolean(
    #     'Invoiced'
    # )
    # invoiceable = fields.Boolean(
    #     'Invoiceable'
    # )
    user_total_id = fields.Many2one(
        'analytic.user.total',
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
    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('open', 'Confirmed'),
    #     ('delayed', 'Delayed'),
    #     ('invoiceable', 'To be Invoiced'),
    #     ('progress', 'In Progress'),
    #     ('invoiced', 'Invoiced'),
    #     ('write-off', 'Write-Off'),
    #     ('change-chargecode', 'Change-Chargecode'),
    # ],
    #     string='Status',
    #     readonly=True,
    #     copy=False,
    #     index=True,
    #     track_visibility='onchange',
    #     default='draft'
    # )

    correction_charge = fields.Boolean(
        compute=_compute_sheet,
        string='Correction Chargeability',
        store=True,
    )
    chargeable = fields.Boolean(
        compute=_compute_sheet,
        string='Chargeable',
        store=True,
    )
    expenses = fields.Boolean(
        compute=_compute_sheet,
        string='Expenses',
        store=True,
    )
    write_off_move = fields.Many2one(
        'account.move',
        string='Write-off Move',
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

    # def _check_state(self):
    #     """
    #     to check if any lines computes method calls allow to modify
    #     :return: True or super
    #     """
    #     context = self.env.context.copy()
    #     if not 'active_model' in context:
    #         return True
    #     return super(AccountAnalyticLine, self)._check_state()

    def get_task_user_product(self, task_id, user_id):
        taskUserObj = self.env['task.user']
        product_id = False
        if task_id and user_id:
            taskUser = taskUserObj.search([('task_id', '=', task_id), ('user_id', '=', user_id)],
                                          limit=1)
            product_id = taskUser.product_id.id if taskUser and taskUser.product_id else False
        return product_id



    @api.model
    def get_fee_rate(self):
        uid = self.user_id.id or False
        tid = self.task_id.id or False
        amount = 0.0
        if uid and tid:
            task_user = self.env['task.user'].search([
                ('user_id', '=', uid),
                ('task_id', '=', tid)])
            fr = task_user.fee_rate
            amount = self.unit_amount * fr
        return amount

    '''@api.model
    def create(self, vals):
#        import pdb; pdb.set_trace()
        res = super(AccountAnalyticLine, self).create(vals)
        if self._context.get('aal_loop', False):
            return res
        if res.product_uom_id == self.env.ref('product.product_uom_hour'):
            s_args1 = [
                ('week_id', '=', res.week_id.id),
                ('product_id', '=', res.product_id.id),
                ('user_id', '=', res.user_id.id),
                ('company_id', '=', res.company_id.id),
                ('task_id', '=', res.task_id.id),
                ('account_id', '=', res.account_id.id),
                ('partner_id', '=', res.partner_id.id),
                ('product_uom_id', '=', res.product_uom_id.id),
                ('child_ids', '!=', False),
            ]
            second1= self.search(s_args1)
            if len(second1) == 1:
                res.parent_id = second1.id
                second1.unit_amount += res.unit_amount
                second1.amount += res.amount
            s_args2 = [
                ('week_id', '=', res.week_id.id),
                ('product_id', '=', res.product_id.id),
                ('user_id', '=', res.user_id.id),
                ('company_id', '=', res.company_id.id),
                ('task_id', '=', res.task_id.id),
                ('account_id', '=', res.account_id.id),
                ('partner_id', '=', res.partner_id.id),
                ('product_uom_id', '=', res.product_uom_id.id),
                ('child_ids', '=', False),
            ]
            second2 = self.search(s_args2)
            if len(second2) > 1:
                values = {
                    'name': '/',
                    'week_id': res.week_id.id,
                    'product_id': res.product_id.id,
                    'user_id': res.user_id.id,
                    'company_id': res.company_id.id,
                    'task_id': res.task_id.id,_compute_sheet
                    'account_id': res.account_id.id,
                    'partner_id': res.partner_id.id,
                    'product_uom_id': res.product_uom_id.id,
                }
                res2 = self.with_context(aal_loop=True).create(values)
                ua = 0
                a = 0
                for line in second2:
                    ua += line.unit_amount
                    a += line.amount
                    line.parent_id = res2.id
                res2.unit_amount = ua
                res2.amount = a
        return res'''




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
        res = super(AccountAnalyticLine, self).create(vals)
        fee_rate = 0
        UpdateCols = []
        if 'task_id' in vals and 'user_id' in vals:
            vals['product_id'] = self.get_task_user_product(vals['task_id'], vals['user_id'])
            task = self.env['project.task'].browse(vals['task_id'])
            if task.task_user_ids:
                for user in task.task_user_ids:
                    if user.user_id.id == vals['user_id']:
                        fee_rate = user.fee_rate or user.product_id.lst_price

            if vals.get('product_uom_id', False) and vals['product_uom_id'] == self.env.ref('product.product_uom_hour').id:
                amount = vals['unit_amount'] * fee_rate
                UpdateCols.append("amount = %s"%amount)
                # self.env.cr.execute(
                #     """UPDATE account_analytic_line SET amount = %s
                #     WHERE id = %s""",
                #     (amount, res.id),
                # )
        if self.env.context.get('default_planned', False):
            if res.week_id != res.select_week_id:
                UpdateCols.append("week_id = %s" % res.select_week_id.id)
                # self.env.cr.execute(
                #     """UPDATE account_analytic_line SET week_id = %s
                #     WHERE id = %s""",
                #     (res.select_week_id.id, res.id),
                # )

            if res.project_id != False:
                UpdateCols.append("planned = True")
                # self.env.cr.execute(
                #     """UPDATE account_analytic_line SET planned = TRUE WHERE id = %s""" %(res.id)
                # )
        if UpdateCols:
            col_up = ', '.join(UpdateCols)
            self.env.cr.execute(
                """UPDATE account_analytic_line SET %s WHERE id = %s""" % (col_up, res.id)
            )
        return res


    # @api.model
    # def create(self, vals):
    #     res = super(AccountAnalyticLine, self).create(vals)
    #     if self.env.context.get('default_planned', False) and res.week_id != res.select_week_id:
    #         self.env.cr.execute(
    #             """UPDATE account_analytic_line SET week_id = %s
    #             WHERE id = %s""",
    #             (res.select_week_id.id, res.id),
    #         )
    #
    #     if self.env.context.get('default_planned', True) and res.project_id != False:
    #         self.env.cr.execute(
    #             """UPDATE account_analytic_line SET planned = TRUE WHERE id = %s""" %(res.id)
    #         )
    #     return res

    @api.multi
    def write(self, vals):
        res = super(AccountAnalyticLine, self).write(vals)
        for aal in self:
            task_id = vals['task_id'] if 'task_id' in vals else aal.task_id.id
            user_id = vals['user_id'] if 'user_id' in vals else aal.user_id.id
            unit_amount = vals['unit_amount'] if 'unit_amount' in vals else aal.unit_amount
            UpdateCols = []
            if task_id and user_id:
                product_id = self.get_task_user_product(task_id, user_id)
                if product_id:
                    fee_rate = 0
                    task = self.env['project.task'].browse(task_id)
                    if task.task_user_ids:
                        for user in task.task_user_ids:
                            if user.user_id.id == user_id:
                                fee_rate = user.fee_rate or user.product_id.lst_price

                        if vals.get('product_uom_id', False) and vals['product_uom_id'] == self.env.ref('product.product_uom_hour').id:
                            amount = unit_amount * fee_rate
                            UpdateCols.append("amount = %s, product_id = %s" % (amount, product_id))
                            # self.env.cr.execute(
                            #     """UPDATE account_analytic_line SET amount = %s , product_id = %s
                            #     WHERE id = %s""",
                            #     (amount, product_id, aal.id),
                            # )

            if vals.get('select_week_id', False) and aal.week_id != aal.select_week_id:
                UpdateCols.append("week_id = %s"%aal.select_week_id.id)
                # self.env.cr.execute(
                #     """UPDATE account_analytic_line SET week_id = %s
                #     WHERE id = %s""",
                #     (aal.select_week_id.id, aal.id),
                # )

            if self.env.context.get('default_planned', False) and aal.project_id != False:
                UpdateCols.append("planned = True")
                # self.env.cr.execute(
                #     """UPDATE account_analytic_line SET planned = TRUE WHERE id = %s""" %(aal.id)
                # )
            if UpdateCols:
                col_up = ', '.join(UpdateCols)
                self.env.cr.execute(
                    """UPDATE account_analytic_line SET %s WHERE id = %s""" % (col_up, aal.id)
                )
            return res
        return res


    # @api.multi
    # def write(self, vals):
    #     res = super(AccountAnalyticLine, self).write(vals)
    #     for obj in self:
    #         if vals.get('select_week_id', False) and obj.week_id != obj.select_week_id:
    #             self.env.cr.execute(
    #                 """UPDATE account_analytic_line SET week_id = %s
    #                 WHERE id = %s""",
    #                 (obj.select_week_id.id, obj.id),
    #             )
    #
    #         if self.env.context.get('default_planned', True) and obj.project_id != False:
    #             self.env.cr.execute(
    #                 """UPDATE account_analytic_line SET planned = TRUE WHERE id = %s""" %(obj.id)
    #             )
    #     return res

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

