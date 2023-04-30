
# -*- coding: utf-8 -*-
# Copyright 2018 The Open Source Company ((www.tosc.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import calendar

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'
    _order = 'date desc'

    @api.depends(
                 'sheet_id_computed.date_to',
                 'sheet_id_computed.date_from',
                 'sheet_id_computed.employee_id',
                 )
    def _compute_sheet(self):
        """Links the timesheet line to the corresponding sheet
        overridden from method in hr_timesheet_sheet without super()
        """
        # we first get value of sheet_id in cache, because it is empty for all to be computed fields
        # because sheet_id does not get a value when sheets is empty, we need the original value.
        # we have to filter self for records existing in db
        self.filtered(lambda i: isinstance(i.id, (int, long))).read(['sheet_id'])
        uom_hrs = self.env.ref("product.product_uom_hour").id
        for ts_line in self.filtered(lambda line: line.task_id and line.product_uom_id.id == uom_hrs):
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
                        AND l.task_id is not NULL
                        AND %(uom_hrs)s = l.product_uom_id
                    GROUP BY l.id""", {'date_from': ts.date_from,
                                       'date_to': ts.date_to,
                                       'user_id': ts.employee_id.user_id.id,
                                       'uom_hrs': self.env.ref("product.product_uom_hour").id})
            ids.extend([row[0] for row in self._cr.fetchall()])
        return [('id', 'in', ids)]

    @api.depends('project_id.chargeable',
                 'project_id.correction_charge',
                 'project_id.user_id',
                 'project_id.invoice_properties.expenses',
                 'account_id',
                 'unit_amount',
                 'planned',
                 'date',
                 'task_id',
                 'user_id',
                 'task_id.task_user_ids',
                 'task_user_id.from_date',
                 'task_user_id.product_id',
                 'task_user_id.fee_rate',
                 )
    def _compute_analytic_line(self):
        self.filtered(lambda i: isinstance(i.id, (int, long))).read(['task_user_id','line_fee_rate','product_id','amount'])
        uom_hrs = self.env.ref("product.product_uom_hour").id
        for line in self.filtered(lambda line: line.task_id and line.product_uom_id.id == uom_hrs):
            # all analytic lines need a project_operating_unit_id and
            # for all analytic lines day_name, week_id and month_id are computed
            date = line.date
            line.project_operating_unit_id = \
                line.account_id.operating_unit_ids \
                and line.account_id.operating_unit_ids[0] or False
            line.day_name = str(datetime.strptime(date, '%Y-%m-%d').
                                strftime("%m/%d/%Y")) + \
                            ' (' + datetime.strptime(date, '%Y-%m-%d'). \
                                strftime('%a') + ')'
            line.week_id = line.find_daterange_week(date)
            line.month_id = var_month_id = line.find_daterange_month(date)
            # only when project_id these fields are computed
            if line.project_id:
                line.chargeable = line.project_id.chargeable
                line.correction_charge = line.project_id.correction_charge
                line.project_mgr = line.project_id.user_id or False
                if line.project_id.invoice_properties:
                    line.expenses = line.project_id.invoice_properties.expenses
            else:
                line.project_mgr = line.account_id.project_ids.user_id or False
            task = line.task_id
            user = line.user_id
            date = line.date
            # only if task_id the remaining fields are computed
            if task and user:
                uou = user._get_operating_unit_id()
                if uou:
                    line.operating_unit_id = uou
                    if line.planned:
                        line.planned_qty = line.unit_amount
                        line.actual_qty = 0.0
                    else:
                        if line.month_of_last_wip:
                            line.wip_month_id = line.month_of_last_wip
                        else:
                            line.wip_month_id = var_month_id
                        if line.product_uom_id.id == uom_hrs:
                            line.ts_line = True
                            if date and line.state in ['new',
                                                       'draft',
                                                       'open',
                                                       'delayed',
                                                       'invoiceable',
                                                       'progress',
                                                       're_confirmed',]:
                                task_user = self.env['task.user'].get_task_user_obj(task.id, user.id, date)[:1]
                                if task_user:
                                    line.task_user_id = task_user
                                #check standard task for fee earners
                                else:
                                    project_id = self.env['project.task'].browse(task.id).project_id
                                    standard_task = project_id.task_ids.filtered('standard')
                                    if len(standard_task) == 1 :
                                        line.task_user_id = self.env['task.user'].get_task_user_obj(standard_task.id, user.id, date) or False
                                line.line_fee_rate = line.get_fee_rate()[0]
                                line.amount = line.get_fee_rate_amount()
                                line.product_id = line.get_task_user_product()
                        line.actual_qty = line.unit_amount
                        line.planned_qty = 0.0


    def _inverse_product_amount(self):
        return

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
        if 'timesheet_date_from' in context:
            date = context.get('timesheet_date_from')
            res.update({'date': date})
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
    wip_month_id = fields.Many2one(
        'date.range',
        compute=_compute_analytic_line,
        store=True,
        string="Month of Analytic Line or last Wip Posting"
    )
    month_of_last_wip = fields.Many2one(
        "date.range",
        "Month Of Next Reconfirmation"
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
    task_user_id = fields.Many2one(
        'task.user',
        string='Task User Fee Rate',
        compute=_compute_analytic_line,
        store=True
    )
    planned = fields.Boolean(
        string='Planned'
    )
    actual_qty = fields.Float(
        string='Actual Qty',
        compute=_compute_analytic_line,
        store=True
    )
    planned_qty = fields.Float(
        string='Planned Qty',
        compute=_compute_analytic_line,
        store=True
    )
    day_name = fields.Char(
        string="Day",
        compute=_compute_analytic_line,
        store=True,
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
        store=True,
    )
    project_mgr = fields.Many2one(
        comodel_name='res.users',
        compute=_compute_analytic_line,
        store=True
    )
    ot = fields.Boolean(
        string='Overtime',
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee'
    )
    line_fee_rate = fields.Float(
        compute=_compute_analytic_line,
        string='Fee Rate',
        store=True,
    )
    amount = fields.Monetary(
        compute=_compute_analytic_line,
        inverse=_inverse_product_amount,
        string='Amount',
        # required=True,
        default=0.0,
        store=True
    )
    product_id = fields.Many2one(
        'product.product',
        compute=_compute_analytic_line,
        inverse=_inverse_product_amount,
        store=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Confirmed'),
        ('delayed', 'Delayed'),
        ('invoiceable', 'To be Invoiced'),
        ('progress', 'In Progress'),
        ('invoice_created', 'Invoice Created'),
        ('invoiced', 'Invoiced'),
        ('write-off', 'Write-Off'),
        ('change-chargecode', 'Change-Chargecode'),
        ('re_confirmed', 'Re-Confirmed'),
        ('invoiced-by-fixed', 'Invoiced by Fixed'),
        ('expense-invoiced', 'Expense Invoiced')
    ],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        track_visibility='onchange',
        default='draft'
    )
    user_total_id = fields.Many2one(
        'analytic.user.total',
        string='Summary Reference',
    )
    date_of_last_wip = fields.Date(
        "Date Of Last WIP"
    )
    date_of_next_reconfirmation = fields.Date(
        "Date Of Next Reconfirmation"
    )

    @api.model
    def get_task_user_product(self):
        product_id = False
        if self.task_user_id:
            product_id = self.task_user_id.product_id
        if self.user_id and not product_id:
            # user = self.env['res.users'].browse(self.user_id.id)
            employee = self.user_id._get_related_employees()

            product_id = employee.product_id or False
        return product_id

    @api.model
    def get_fee_rate(self):
        task_user = self.task_user_id
        fr = 0.0
        ic_fr = 0.0
        if task_user:
            fr = task_user.fee_rate or 0.0
            ic_fr = task_user.ic_fee_rate or 0.0
        return [fr, ic_fr]

    @api.model
    def get_fee_rate_amount(self):
        fr = self.get_fee_rate()[0]
        unit_amount = self.unit_amount
        amount = - unit_amount * fr
        return amount

    @api.onchange('date')
    def _onchange_dates(self):
        if self.planned or self.env.context.get('default_planned',False) :
            dt = datetime.strptime(self.date, "%Y-%m-%d") if self.date else datetime.now().date()
            self.date = dt-timedelta(days=dt.weekday())
            self.company_id = self.env.user.company_id
            date = self.find_daterange_week(self.date)
            self.week_id = date.id
        elif self.sheet_id and not self.sheet_id.date_from <= self.date <= self.sheet_id.date_to:
            self.date = self.sheet_id.date_from
            return {
                'warning': {'title': _('Error'), 'message': _('Please fill in date within timesheet dates.'), },
            }
        elif self.env.context.get('timesheet_date_from',False) and \
            self.env.context.get('timesheet_date_to',False) and not \
            self.env.context.get('timesheet_date_from') <= self.date <= self.env.context.get('timesheet_date_to'):
            self.date = self.env.context.get('timesheet_date_from')
            return {
                'warning': {'title': _('Error'), 'message': _('Please fill in date within timesheet dates.'), },
            }


    @api.onchange('product_id', 'product_uom_id', 'unit_amount', 'currency_id')
    def on_change_unit_amount(self):
        if self.product_uom_id == self.env.ref("product.product_uom_hour").id:
            return {}
        return super(AccountAnalyticLine, self).on_change_unit_amount()

    @api.multi
    def write(self, vals):
        uom_hour = self.env.ref("product.product_uom_hour")
        # don't call super if only state has to be updated
        if self and 'state' in vals and len(vals) == 1:
            state = vals['state']
            cond, rec = ("IN", tuple(self.ids)) if len(self) > 1 else ("=",
                                                                       self.id)
            self.env.cr.execute("""
                               UPDATE %s SET state = '%s' WHERE id %s %s
                               """ % (self._table, state, cond, rec))
            self.env.invalidate_all()
            vals.pop('state')
            return True
        ## todo
        if not (
                'unit_amount' in vals or
                'product_uom_id' in vals or
                'sheet_id' in vals or
                'date' in vals or
                'project_id' in vals or
                'task_id' in vals or
                'user_id' in vals or
                'name' in vals or
                'ref' in vals
        ) and any(this.product_uom_id == uom_hour for this in self):
            # always copy context to keep other context reference
            context = self.env.context.copy()
            context.update({'analytic_check_state': True})
            return super(AccountAnalyticLine, self.with_context(context)).write(
                vals)
        return super(AccountAnalyticLine, self).write(vals)

    def _get_timesheet_cost(self, values):
        ## turn off updating amount and account
        values = values if values is not None else {}
        if values.get('project_id') or self.project_id:
            if values.get('amount'):
                return {}
            # unit_amount = values.get('unit_amount', 0.0) or self.unit_amount
            user_id = values.get('user_id') or self.user_id.id or self._default_user()
            user = self.env['res.users'].browse([user_id])
            emp = self.env['hr.employee'].search([('user_id', '=', user_id)], limit=1)
            # cost = emp and emp.timesheet_cost or 0.0
            uom = (emp or user).company_id.project_time_mode_id
            # Nominal employee cost = 1 * company project UoM (project_time_mode_id)
            return {
                # 'amount': -unit_amount * cost,
                'product_uom_id': uom.id,
                # 'account_id': values.get('account_id') or self.account_id.id or emp.account_id.id,
            }
        return {}

    def _check_state(self):
        """
        to check if any lines computes method calls allow to modify
        :return: True or super
        """
        context = self.env.context.copy()
        if 'analytic_check_state' in context \
                or 'active_invoice_id' in context:
            return True
        return super(AccountAnalyticLine, self)._check_state()

    @api.model
    def run_reconfirmation_process(self):
        current_date = datetime.now().date()
        # pre_month_start_date = current_date.replace(day=1, month=current_date.month - 1)
        month_days = calendar.monthrange(current_date.year, current_date.month)[1]
        month_end_date = current_date.replace(day=month_days)

        domain = [('date_of_next_reconfirmation', '!=', False), ('date_of_next_reconfirmation', '<=', month_end_date),
                  ('state', '=', 'delayed')]
        query_line = self._where_calc(domain)
        self_tables, where_clause, where_clause_params = query_line.get_sql()

        list_query = ("""                    
                UPDATE {0}
                SET state = 're_confirmed', date_of_next_reconfirmation = null
                WHERE {1}                          
                     """.format(
            self_tables,
            where_clause
        ))
        self.env.cr.execute(list_query, where_clause_params)
        return True

    @api.multi
    def modified(self, fnames):
        if not self.env.context.get('_timesheet_write'):
            # disable modification triggers when writing timesheets
            return super(AccountAnalyticLine, self).modified(fnames)

    @api.multi
    def _get_sale_order_line(self, vals=None):
        if not self.env.context.get('_timesheet_write'):
            # disable linking sale order lines to analytic lines on timesheets
            return super(AccountAnalyticLine, self)._get_sale_order_line(vals=vals)
        return dict(vals or {})
