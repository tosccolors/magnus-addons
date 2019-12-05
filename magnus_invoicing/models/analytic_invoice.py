# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import json

class AnalyticInvoice(models.Model):
    _name = "analytic.invoice"
    _inherits = {'account.invoice': "invoice_id"}
    _description = "Analytic Invoice"
    _order = "date_to desc"
    _rec_name = 'partner_id'


    @api.one
    @api.depends('partner_id','account_analytic_ids', 'month_id')
    def _compute_analytic_lines(self):
        if len(self.account_analytic_ids) > 0:
            account_analytic_ids = self.account_analytic_ids.ids
            if self.month_id:
                domain = self.month_id.get_domain('date')
                domain += [('account_id', 'in', account_analytic_ids)]
            else:
                domain = [('account_id', 'in', account_analytic_ids)]
            hrs = self.env.ref('product.product_uom_hour').id
            time_domain = domain + [
                ('product_uom_id', '=', hrs),
                ('state', 'in', ['invoiceable', 'invoiced']),
            ]
            self.time_line_ids = self.env['account.analytic.line'].search(time_domain).ids

            cost_domain = domain + [('product_uom_id', '!=', hrs), ('amount', '<', 0)]
            self.cost_line_ids = self.env['account.analytic.line'].search(cost_domain).ids

            revenue_domain = domain + [('product_uom_id', '!=', hrs), ('amount', '>', 0)]
            self.revenue_line_ids = self.env['account.analytic.line'].search(revenue_domain).ids
        else:
            self.time_line_ids = []
            self.cost_line_ids = []
            self.revenue_line_ids = []


    @api.one
    @api.depends('partner_id', 'month_id', 'gb_week','project_operating_unit_id', 'project_id', 'link_project')
    def _compute_objects(self):
        ctx = self.env.context.copy()
        current_ref = ctx.get('active_invoice_id', False)

        userTotObj = userInvoicedObjs = self.env['analytic.user.total']

        ana_ids = self.env['account.analytic.line']
        if current_ref:
            # get all invoiced user total objs using current reference
            userInvoicedObjs = userTotObj.search(
                [('analytic_invoice_id', '=', current_ref), ('state', 'in', ('invoice_created', 'invoiced'))])

            # don't look for analytic lines which has been already added for other analytic invoice
            tot_obj = userTotObj.search([('analytic_invoice_id', '!=', current_ref), ('state', 'not in', ('invoice_created', 'invoiced'))])
            for t in tot_obj:
                ana_ids |= t.detail_ids

        partner_id = self.partner_id or False
        if self.project_id and self.link_project:
            partner_id = self.project_id.partner_id

        if partner_id and len(self.account_analytic_ids) == 0:
            account_analytic = self.env['account.analytic.account'].search([
                ('partner_id', '=', partner_id.id)])
            if len(account_analytic) > 0:
                self.account_analytic_ids = \
                    [(6, 0, account_analytic.ids)]

        if len(self.account_analytic_ids) > 0:
            account_analytic_ids = self.account_analytic_ids.ids
            if self.month_id:
                domain = self.month_id.get_domain('date')
                domain += [('account_id', 'in', account_analytic_ids)]
            else:
                domain = [('account_id', 'in', account_analytic_ids)]

            if self.project_operating_unit_id:
                domain += [('project_operating_unit_id', '=',self.project_operating_unit_id.id)]
            if self.project_id and self.link_project:
                domain += [('project_id', '=', self.project_id.id)]
            else:
                domain +=['|',
                          ('project_id.invoice_properties.group_invoice', '=', True),
                          ('task_id.project_id.invoice_properties.group_invoice', '=', True)
                          ]
            hrs = self.env.ref('product.product_uom_hour').id
            time_domain = domain + [
                ('chargeable', '=', True),
                ('product_uom_id', '=', hrs),
                ('state', 'in', ['invoiceable', 'progress'])
                ]
            if ana_ids:
                time_domain += [('id', 'not in', ana_ids.ids)]

            fields_grouped = [
                'id',
                'user_id',
                'task_id',
                'account_id',
                'product_id',
                'month_id',
                'week_id',
                'unit_amount',
                'project_operating_unit_id'
            ]
            grouped_by = [
                'user_id',
                'task_id',
                'account_id',
                'product_id',
                'month_id',
                'project_operating_unit_id'
            ]
            if self.gb_week:
                grouped_by.append('week_id')

            result = self.env['account.analytic.line'].read_group(
                time_domain,
                fields_grouped,
                grouped_by,
                offset=0,
                limit=None,
                orderby=False,
                lazy=False
            )

            taskUserObj = self.env['task.user']
            taskUserIds, userTotData = [], []

            if len(result) > 0:
                for item in result:
                    task_id = item.get('task_id')[0] if item.get('task_id') != False else False
                    project_id = False
                    if task_id:
                        project_id = self.env['project.task'].browse(task_id).project_id.id or False
                    vals = {
                        'name': '/',
                        'user_id': item.get('user_id')[0] if item.get(
                            'user_id') != False else False,
                        'task_id': item.get('task_id')[0] if item.get('task_id') != False else False,
                        'project_id':project_id,
                        'account_id': item.get('account_id')[0] if item.get(
                            'account_id') != False else False,
                        'gb_month_id': item.get('month_id')[0] if item.get(
                            'month_id') != False else False,
                        'gb_week_id': item.get('week_id')[0] if self.gb_week and item.get('week_id') != False else False,
                        'unit_amount': item.get('unit_amount'),
                        'product_id': item.get('product_id'),
                        'operating_unit_id': item.get('operating_unit_id'),
                        'project_operating_unit_id': item.get('project_operating_unit_id'),
                    }

                    # aut_id = self.env['analytic.user.total'].create(vals)
                    aal_domain = time_domain + [
                        ('user_id', '=', vals['user_id']),
                        ('task_id', '=', vals['task_id']),
                        ('account_id', '=', vals['account_id']),
                        ('month_id', '=', vals['gb_month_id']),
                    ]
                    if vals['gb_week_id']:
                        aal_domain += [('week_id', '=', vals['gb_week_id'])]

                    childData = []
                    for aal in self.env['account.analytic.line'].search(aal_domain):
                        childData.append((4, aal.id))
                    vals['detail_ids'] = childData

                    userTotData.append((0, 0, vals))

                    taskUser = taskUserObj.search([('task_id', '=', vals['task_id']),('user_id', '=', vals['user_id'])], limit=1)
                    taskUserIds += taskUser.ids

                    if taskUserIds:
                        taskUserIds = list(set(taskUserIds))
                        self.task_user_ids = [(6, 0, taskUserIds)]
                    else:
                        self.task_user_ids = [(6, 0, [])]

            #add invoiced user total
            for usrTot in userInvoicedObjs:
                userTotData.append((4, usrTot.id))
            self.user_total_ids = userTotData

    def _sql_update(self, self_obj, status):
        if not self_obj.ids or not status:
            return True
        cond = '='
        rec = self_obj.ids[0]
        if len(self_obj) > 1:
            cond = 'IN'
            rec = tuple(self_obj.ids)
        self.env.cr.execute("""
                            UPDATE %s SET state = '%s'
                            WHERE id %s %s
                    """ % (self_obj._table, status, cond, rec))


    @api.multi
    @api.depends('invoice_id.state')
    def _compute_state(self):
        for ai in self:
            if not ai.invoice_id:
                ai.state = 'draft'
                user_tot_objs = ai.user_total_ids.filtered(lambda ut: ut.state != 'draft')
                for user_tot in user_tot_objs:
                    self._sql_update(user_tot.detail_ids, 'progress')
                    self._sql_update(user_tot, 'draft')

            elif ai.invoice_id.state == 'cancel':
                ai.state = 'draft'
                for line in ai.invoice_line_ids:
                    self._sql_update(line.user_task_total_line_id.detail_ids, 'progress')
                    self._sql_update(line.user_task_total_line_id, 'draft')

            elif ai.invoice_id.state in ('draft','proforma','proforma2'):
                if ai.state == 'invoiced':
                    ai.state = 'open'
                else:
                    ai.state = 'open'
                for line in ai.invoice_line_ids:
                    self._sql_update(line.user_task_total_line_id.detail_ids, 'invoice_created')
                    self._sql_update(line.user_task_total_line_id, 'invoice_created')

            elif ai.invoice_id.state in ('open','paid'):
                ai.state = 'invoiced'
                for line in ai.invoice_line_ids:
                    self._sql_update(line.user_task_total_line_id.detail_ids, 'invoiced')
                    self._sql_update(line.user_task_total_line_id, 'invoiced')

    @api.model
    def _get_fiscal_month_domain(self):
        # We have access to self.env in this context.
        fm = self.env.ref('account_fiscal_month.date_range_fiscal_month').id
        return [('type_id', '=', fm)]

    @api.multi
    @api.depends('user_total_ids')
    def _compute_task_user_ids_domain(self):
        for rec in self:
            rec.task_user_ids_domain = json.dumps([
                ('user_id', 'in', rec.user_total_ids.mapped('user_id').ids),
                ('task_id', 'in', rec.user_total_ids.mapped('task_id').ids)
            ])

    @api.onchange('account_analytic_ids')
    def onchange_account_analytic(self):
        res ={}
        operating_units = self.env['operating.unit']
        for aa in self.account_analytic_ids:
            operating_units |= aa.operating_unit_ids
        if operating_units:
            res['domain'] = {'project_operating_unit_id':[
                                ('id', 'in', operating_units.ids)
                                ]}
        return res

    account_analytic_ids = fields.Many2many(
        'account.analytic.account',
        compute='_compute_objects',
        string='Analytic Account',
        store=True
    )
    task_user_ids_domain = fields.Char(
        compute="_compute_task_user_ids_domain",
        readonly=True,
        store=False,
    )
    task_user_ids = fields.Many2many(
        'task.user',
        compute='_compute_objects',
        string='Task Fee Rate',
        store=True
    )
    invoice_id = fields.Many2one(
        'account.invoice',
        string='Customer Invoice',
        required=True,
        readonly=True,
        ondelete='restrict',
        index=True
    )
    time_line_ids = fields.Many2many(
        'account.analytic.line',
        compute='_compute_analytic_lines',
        string='Time Line',
    )
    cost_line_ids = fields.Many2many(
        'account.analytic.line',
        compute='_compute_analytic_lines',
        string='Cost Line',
    )
    revenue_line_ids = fields.Many2many(
        'account.analytic.line',
        compute='_compute_analytic_lines',
        string='Revenue Line',
    )
    user_total_ids = fields.One2many(
        'analytic.user.total',
        'analytic_invoice_id',
        compute='_compute_objects',
        string='User Total Line',
        store=True
    )
    month_id = fields.Many2one(
        'date.range',
        domain=_get_fiscal_month_domain
    )
    date_from = fields.Date(
        related='month_id.date_start',
        string='Date From'
    )
    date_to = fields.Date(
        related='month_id.date_end',
        string='Date To',
        store=True
    )
    gb_task =fields.Boolean(
        'Group By Task',
        default=False
    )
    gb_week = fields.Boolean(
        'Group By Week',
        default=False
    )
    gb_month = fields.Boolean(
        'Group By Month',
        default=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'In Progress'),
        ('invoiced', 'Invoiced'),
    ],  string='Status',
        compute=_compute_state,
        copy=False,
        index=True,
        store=True,
        track_visibility='onchange',
    )
    project_operating_unit_id = fields.Many2one(
        'operating.unit',
        string='Project Operating Unit',
    )
    link_project = fields.Boolean(
        "Link Project",
        help="If true then must select project of type group invoice False"
    )
    project_id = fields.Many2one(
        'project.project',
        domain=[('invoice_properties.group_invoice', '=', False)]
    )

    def unlink_rec(self):
        user_total_ids = self.env['analytic.user.total'].search(
            [('analytic_invoice_id', '=', False)])
        if user_total_ids:
            #reset analytic line state to invoiceable
            analytic_lines = user_total_ids.mapped('detail_ids')
            analytic_lines.write({'state': 'invoiceable'})
            user_total_ids.unlink()

    @api.multi
    def write(self, vals):
        res = super(AnalyticInvoice, self).write(vals)
        self.unlink_rec()
        analytic_lines = self.user_total_ids.mapped('detail_ids')
        if analytic_lines:
            analytic_lines.write({'state': 'progress'})
        return res

    @api.model
    def create(self, vals):
        res = super(AnalyticInvoice, self).create(vals)
        analytic_lines = res.user_total_ids.mapped('detail_ids')
        if analytic_lines:
            analytic_lines.write({'state': 'progress'})
        return res

    @api.multi
    def unlink(self):
        """
            reset analytic line state to invoiceable
            :return:
        """
        analytic_lines = self.env['account.analytic.line']
        for obj in self:
            analytic_lines |= obj.user_total_ids.mapped('detail_ids')
        if analytic_lines:
            analytic_lines.write({'state': 'invoiceable'})
        return super(AnalyticInvoice, self).unlink()

    @api.multi
    def get_product_wip_account(self, product, fiscal_pos=None):
        account = product.property_account_wip_id
        if not account and product:
            raise UserError(
                _('Please define WIP account for this product: "%s" (id:%d).') %
                (product.name, product.id))

        if not fiscal_pos:
            fiscal_pos = self.env['account.fiscal.position']
        return fiscal_pos.map_account(account)

    @api.model
    def _prepare_invoice_line(self, line, invoice_id):
        ctx = self.env.context.copy()
        ctx.update({
            'active_model':'analytic.invoice',
            'active_id':line.id,
        })
        invoice_line = self.env['account.invoice.line'].with_context(ctx).new({
            'invoice_id': invoice_id,
            'product_id': line.product_id.id,
            'quantity': line.unit_amount,
            'uom_id': line.product_uom_id.id,
            'user_id': line.user_id.id,
        })

        # Add analytic tags to invoice line
        invoice_line.analytic_tag_ids |= line.tag_ids

        # Get other invoice line values from product onchange
        invoice_line._onchange_product_id()
        invoice_line_vals = invoice_line._convert_to_write(invoice_line._cache)

        # if invoicing period doesn't lie in same month
        # period_date = datetime.strptime(line.analytic_invoice_id.month_id.date_start, "%Y-%m-%d").strftime('%Y-%m')
        # cur_date = datetime.now().date().strftime("%Y-%m")
        # invoice_date = line.analytic_invoice_id.invoice_id.date or line.analytic_invoice_id.invoice_id.date_invoice
        #
        # inv_date = datetime.strptime(invoice_date, "%Y-%m-%d").strftime('%Y-%m') if invoice_date else cur_date
        # if inv_date != period_date:
        #     fpos = self.invoice_id.fiscal_position_id
        #     account = self.get_product_wip_account(line.product_id, fpos)
        #     invoice_line_vals.update({
        #             'account_id':account.id
        #         })

        invoice_line_vals.update({
            'account_analytic_id': line.account_id and line.account_id.id or False,
            'price_unit': line.fee_rate,
            'analytic_invoice_id': line.analytic_invoice_id.id,
            'origin': line.task_id.project_id.po_number
                        if line.task_id and line.task_id.project_id and line.task_id.project_id.correction_charge
                        else '/',
        })

        return invoice_line_vals

    @api.one
    def generate_invoice(self):
        if self.invoice_id.state == 'cancel':
            raise UserError(_("Can't generate invoice, kindly re-set invoice to draft'"))
        invoices = {}
        user_summary_lines = self.user_total_ids.filtered(lambda x: x.state == 'draft')
        aal_from_summary = self.env['account.analytic.line']
        user_total = self.env['analytic.user.total']

        invoices['lines'] = []

        for line in user_summary_lines:
            inv_line_vals = self._prepare_invoice_line(line, self.invoice_id.id)
            inv_line_vals['user_task_total_line_id'] = line.id
            invoices['lines'].append((0, 0, inv_line_vals))
            aal_from_summary |= line.detail_ids
            user_total |= line

        if invoices['lines']:
            self.write({'invoice_line_ids': invoices['lines']})

        self.invoice_id.compute_taxes()
        if self.state == 'draft' and aal_from_summary:
            self.state = 'open'
        if aal_from_summary:
            aal_from_summary.write({'state':'invoice_created'})
        if user_total:
            user_total.write({'state':'invoice_created'})
        return True

    @api.one
    def delete_invoice(self):
        if self.state == 'invoiced':
            self.invoice_id.action_cancel()
            self.invoice_id.action_invoice_draft()
            self.invoice_line_ids.unlink()
        elif not self.invoice_id.move_name:
            self.invoice_line_ids.unlink()
        elif self.state == 'open':
            self.invoice_line_ids.unlink()

        if not self.invoice_line_ids:
            self.state = 'draft'
            for user_total in self.user_total_ids:
                self._sql_update(user_total.detail_ids, 'progress')
                self._sql_update(user_total, 'draft')


    @api.multi
    def action_view_invoices(self):
        self.ensure_one()
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        invoices = self.mapped('invoice_id')
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif invoices:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.id
        return action


    @api.multi
    def _get_user_per_month(self):
        self.ensure_one()
        res = {}

        #FIX:on invoice send by mail action, self.user_total_ids is returning as empty set
        user_total_objs = self.user_total_ids
        if not user_total_objs:
            usrTotIDS = self.read(['user_total_ids'])[0]['user_total_ids']
            user_total_objs = self.user_total_ids.browse(usrTotIDS)

        for user_tot in user_total_objs:
            if user_tot.project_id.invoice_properties.specs_invoice_report:
                if user_tot.project_id in res:
                    if user_tot.user_id in res[user_tot.project_id]:
                        res[user_tot.project_id][user_tot.user_id]['hours'] += user_tot.unit_amount
                        res[user_tot.project_id][user_tot.user_id]['fee_rate'] += user_tot.fee_rate
                        res[user_tot.project_id][user_tot.user_id]['amount'] += user_tot.amount
                    else:
                        res[user_tot.project_id][user_tot.user_id] = {'hours': user_tot.unit_amount,
                                                                      'fee_rate': user_tot.fee_rate,
                                                                      'amount': user_tot.amount}
                    res[user_tot.project_id]['hrs_tot'] += user_tot.unit_amount
                    res[user_tot.project_id]['amt_tot'] += user_tot.amount
                else:
                    res[user_tot.project_id] = {}
                    res[user_tot.project_id][user_tot.user_id] = {'hours':user_tot.unit_amount, 'fee_rate':user_tot.fee_rate, 'amount': user_tot.amount}
                    res[user_tot.project_id]['hrs_tot'] = user_tot.unit_amount
                    res[user_tot.project_id]['amt_tot'] = user_tot.amount

        return res

    @api.multi
    def _get_user_per_day(self):
        self.ensure_one()
        result = {}
        for user_tot in self.user_total_ids:
            inv_property = user_tot.project_id.invoice_properties
            if inv_property.specs_invoice_report and inv_property.specs_type != 'per_month':
                if user_tot.project_id in result:
                    result[user_tot.project_id] |= user_tot.detail_ids
                else:
                    result[user_tot.project_id] = user_tot.detail_ids
        return result

    @api.multi
    def _get_specs_on_task(self):
        self.ensure_one()
        res = {}
        # FIX:on invoice send by mail action, self.user_total_ids is returning as empty set
        user_total_objs = self.user_total_ids
        if not user_total_objs:
            usrTotIDS = self.read(['user_total_ids'])[0]['user_total_ids']
            user_total_objs = self.user_total_ids.browse(usrTotIDS)

        for user_tot in user_total_objs:
            if user_tot.project_id.invoice_properties.specs_invoice_report and user_tot.project_id.invoice_properties.specs_on_task_level:
                if user_tot.project_id in res:
                    if user_tot.task_id in res[user_tot.project_id]:
                        res[user_tot.project_id][user_tot.task_id]['unit_amount'] += user_tot.unit_amount
                    else:
                        res[user_tot.project_id][user_tot.task_id] = {'unit_amount': user_tot.unit_amount}
                else:
                    res[user_tot.project_id] = {}
                    res[user_tot.project_id][user_tot.task_id] = {'unit_amount': user_tot.unit_amount}
        return res



class AnalyticUserTotal(models.Model):
    _name = "analytic.user.total"
    _inherit = 'account.analytic.line'
    _description = "Analytic User Total"

    @api.one
    @api.depends('unit_amount', 'user_id', 'task_id','analytic_invoice_id.task_user_ids')
    def _compute_fee_rate(self):
        """
            First, look get fee rate from task_user_ids from analytic invoice.
            Else, get fee rate from method get_fee_rate()
        :return:
        """
        task_user = self.analytic_invoice_id.task_user_ids.filtered(
            lambda line: line.user_id == self.user_id
                    and line.task_id == self.task_id
        )
        if task_user:
            self.fee_rate = fr = task_user[0].fee_rate
            self.amount = - self.unit_amount * fr
        else:
            self.fee_rate = fr = self.get_fee_rate(False, False)
            self.amount = - self.unit_amount * fr


    @api.one
    def _compute_analytic_line(self):
        for aut in self:
            aut.count_analytic_line = str(len(aut.detail_ids)) + ' (records)'

    analytic_invoice_id = fields.Many2one(
        'analytic.invoice'
    )
    fee_rate = fields.Float(
        compute=_compute_fee_rate,
        string='Fee Rate'
    )
    amount = fields.Float(
        compute=_compute_fee_rate,
        string='Amount'
    )
    detail_ids = fields.One2many(
        'account.analytic.line',
        'user_total_id',
        string='Detail Time Lines',
        readonly=True,
        copy=False
    )
    count_analytic_line = fields.Char(
        compute=_compute_analytic_line,
        string='Detail Time Lines'
    )
    gb_week_id = fields.Many2one(
        'date.range',
        string='Week',
    )
    gb_month_id = fields.Many2one(
        'date.range',
        string='Month',
    )
