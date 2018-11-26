# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from lxml import etree


class AnalyticInvoice(models.Model):
    _name = "analytic.invoice"
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
            time_domain = domain + [('product_uom_id', '=', hrs), ('state', 'in', ['invoiceable', 'invoiced']),
                                    '|',('invoiceable', '=', True),('invoiced', '=', True)]

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
    @api.depends('partner_id', 'account_analytic_ids', 'month_id', 'gb_week')
    def _compute_objects(self):
        partner_id = self.partner_id or False
        if partner_id and len(self.account_analytic_ids) == 0:
            account_analytic = self.env['account.analytic.account'].search([
                ('partner_id', '=', self.partner_id.id)])
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

            hrs = self.env.ref('product.product_uom_hour').id
            time_domain = domain + [('product_uom_id', '=', hrs), ('state', 'in', ['invoiceable', 'invoiced']),
                                    '|',('invoiceable', '=', True),('invoiced', '=', True)]

            fields_grouped = [
                'id',
                'user_id',
                'task_id',
                'account_id',
                'product_id',
                'month_id',
                'week_id',
                'unit_amount'
            ]
            grouped_by = [
                'user_id',
                'task_id',
                'account_id',
                'product_id',
                'month_id',
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
            taskUserIds = []

            if len(result) > 0:               
                userTotData = []
                for item in result:
                    vals = {
                        'analytic_invoice_id': self.id,
                        'name': '/',
                        'user_id': item.get('user_id')[0] if item.get(
                            'user_id') != False else False,
                        'task_id': item.get('task_id')[0] if item.get(
                            'task_id') != False else False,
                        'account_id': item.get('account_id')[0] if item.get(
                            'account_id') != False else False,
                        'gb_month_id': item.get('month_id')[0] if item.get(
                            'month_id') != False else False,
                        'gb_week_id': item.get('week_id')[0] if self.gb_week and item.get('week_id') != False else False,
                        'unit_amount': item.get('unit_amount'),
                        'product_id': item.get('product_id'),
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
                    vals['children_ids'] = childData

                    userTotData.append((0, 0, vals))

                    taskUser = taskUserObj.search([('task_id', '=', vals['task_id']),('user_id', '=', vals['user_id'])])
                    taskUserIds += taskUser.ids
                self.user_total_ids = userTotData

                if taskUserIds:
                    taskUserIds = list(set(taskUserIds))
                    self.task_user_ids = [(6, 0, taskUserIds)]
                else:
                    self.task_user_ids = [(6, 0, [])]

    @api.model
    def _get_fiscal_month_domain(self):
        # We have access to self.env in this context.
        fm = self.env.ref('account_fiscal_month.date_range_fiscal_month').id
        return [('type_id', '=', fm)]

    def _compute_invoice_count(self):
        for line in self:
            line.invoice_count = len(line.invoice_ids.ids)

    @api.multi
    def action_done(self):
        self.state = 'invoiced'

    name = fields.Char

    account_analytic_ids = fields.Many2many(
        'account.analytic.account',
        compute='_compute_objects',
        string='Analytic Account',
        store=True
    )
    task_user_ids = fields.Many2many(
        'task.user',
        compute='_compute_objects',
        string='User Role',
        store=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        domain=[('is_company','=', True)],
    )
    invoice_ids = fields.Many2many(
        'account.invoice',
        string='Customer Invoices',
        ondelete='restrict',
        index=True
    )
    invoice_line_ids = fields.One2many(
        'account.invoice.line',
        'analytic_invoice_id',
        string='New Invoice Lines',
        ondelete='cascade',
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
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    invoice_count = fields.Integer('Invoices', compute='_compute_invoice_count')

    def unlink_rec(self):
        user_total_ids = self.env['analytic.user.total'].search(
            [('analytic_invoice_id', '=', False)])
        if user_total_ids:
            cond = '='
            rec = user_total_ids.ids[0]
            if len(user_total_ids) > 1:
                cond = 'IN'
                rec = tuple(user_total_ids.ids)
            self.env.cr.execute("""
                                DELETE FROM  analytic_user_total WHERE id %s %s
                        """ % (cond, rec))


    @api.multi
    def write(self, vals):
        res = super(AnalyticInvoice, self).write(vals)
        self.unlink_rec()
        return res

    @api.model
    def _prepare_invoice(self, lines):
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))
        vals = {
            # 'date_invoice': invoice_date,
            # 'date': posting_date or False,
            'type': 'out_invoice',
            'account_id': self.partner_id.property_account_receivable_id.id,
            'partner_id': self.partner_id.id,
            'invoice_line_ids': lines['lines'],
            # 'comment': lines['name'],
            'payment_term_id': self.partner_id.property_payment_term_id.id or False,
            'journal_id': journal_id,
            'fiscal_position_id': self.partner_id.property_account_position_id.id or False,
            'user_id': self.env.user.id,
            'company_id': self.env.user.company_id.id,
            # 'operating_unit_id': operating_unit.id,
            # 'payment_mode_id': payment_mode.id or False,
            # 'partner_bank_id': payment_mode.fixed_journal_id.bank_account_id.id
            # if payment_mode.bank_account_link == 'fixed'
            # else partner.bank_ids and partner.bank_ids[0].id or False,
        }
        return vals


    @api.multi
    def _prepare_invoice_line(self, line):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param line: sales order line to invoice
        """
        line.ensure_one()
        account = line.product_id.property_account_income_id or line.product_id.categ_id.property_account_income_categ_id
        if not account and line.product_id:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (line.product_id.name, line.product_id.id, line.product_id.categ_id.name))

        fpos = self.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        # project = False
        # if line.project_id:
        #     project = line.project_id
        # elif line.task_id:
        #     project = line.task_id.project_id

        res = {
            'name': line.product_id.name or '/',
            # 'sequence': line.sequence,
            'origin': line.task_id.project_id.po_number if line.task_id and line.task_id.project_id and line.task_id.correction_charge else '/',
            'account_id': account.id,
            'price_unit': line.fee_rate,
            'quantity': line.unit_amount,
            # 'discount': line.discount,
            'uom_id': line.product_uom_id.id,
            'product_id': line.product_id and line.product_id.id or False,
            # 'layout_category_id': line.layout_category_id and line.layout_category_id.id or False,
            # 'invoice_line_tax_ids': [(6, 0, line.tax_id.ids or [])],
            'account_analytic_id': line.account_id and line.account_id.id or False,
            'analytic_tag_ids': [(6, 0, line.tag_ids.ids or [])],
            'analytic_invoice_id':line.analytic_invoice_id.id,
            # 'project_id': project.id if project else False
        }
        return res

    @api.one
    def generate_invoice(self):
        invoices = {}
        invoices['lines'] = []
        user_summary_lines = self.user_total_ids.filtered(lambda x: x.invoiced == False)
        for line in user_summary_lines:
            inv_line_vals = self._prepare_invoice_line(line)
            invoices['lines'].append((0, 0, inv_line_vals))
        if invoices['lines']:
            if self.invoice_ids:
                invoice = self.env['account.invoice'].browse(self.invoice_ids.ids[0])
                invoice.write({'lines':invoices['lines']})
            else:
                vals = self._prepare_invoice(invoices)
                invoice = self.env['account.invoice'].create(vals)
                invoice.compute_taxes()
                self.invoice_ids = [(4, invoice.id)]
        for line in user_summary_lines:
            # line.children_ids.with_context({'UpdateState':True}).write({'invoiced':True,'state':'invoiced'})
            # line.with_context({'UpdateState':True}).write({'invoiced':True,'state':'invoiced'})
            cond = '='
            rec = line.children_ids.ids[0]
            if len(line.children_ids) > 1:
                cond = 'IN'
                rec = tuple(line.children_ids.ids)
            self.env.cr.execute("""
                        UPDATE account_analytic_line SET state = 'invoiced', invoiced = true WHERE id %s %s
                """ % (cond, rec))
            self.env.cr.execute("""
                        UPDATE analytic_user_total SET state = 'invoiced', invoiced = true WHERE id = %s
                """ % (line.id))
        if self.state == 'draft':
            self.state = 'open'
        return True


    @api.multi
    def action_view_invoices(self):
        self.ensure_one()
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        invoices = self.mapped('invoice_ids')
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif invoices:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.id
        return action


class AnalyticUserTotal(models.Model):
    _name = "analytic.user.total"
    _inherit = 'account.analytic.line'
    _description = "Analytic User Total"

    @api.one
    @api.depends('unit_amount', 'user_id', 'task_id')
    def _compute_fee_rate(self):
        uid = self.user_id.id or False
        tid = self.task_id.id or False
        if uid and tid:
            task_user = self.env['task.user'].search([
                ('user_id','=', uid),
                ('task_id','=', tid)])
            self.fee_rate = fr = task_user.fee_rate
            self.amount = self.unit_amount * fr

    @api.one
    def _compute_analytic_line(self):
        for aut in self:
            aut.count_analytic_line = str(len(aut.children_ids)) + ' (records)'

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
    # children_ids = fields.One2many(
    #     'account.analytic.line',
    #     'user_total_id',
    #     string='Detail Time Lines',
    #     readonly=True,
    #     copy=False
    # )
    children_ids = fields.Many2many(
        'account.analytic.line',
        'analytic_invoice_account_line_rel'
        'user_total_id',
        'analytic_account_id',
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




    '''
    uom_id = fields.Many2one('product.uom', string='Unit of Measure',
                             ondelete='set null', index=True, oldname='uos_id')
    product_id = fields.Many2one('product.product', string='Product',
                                 ondelete='restrict', index=True)
    account_id = fields.Many2one('account.account', string='Account',
                                 required=True,
                                 domain=[('deprecated', '=', False)],
                                 default=_default_account,
                                 help="The income or expense account related to the selected product.")
    price_unit = fields.Float(string='Unit Price', required=True,
                              digits=dp.get_precision('Product Price'))
    price_subtotal = fields.Monetary(string='Amount',
                                     store=True, readonly=True,
                                     compute='_compute_price')
    price_subtotal_signed = fields.Monetary(string='Amount Signed',
                                            currency_field='company_currency_id',
                                            store=True, readonly=True,
                                            compute='_compute_price',
                                            help="Total amount in the currency of the company, negative for credit notes.")
    quantity = fields.Float(string='Quantity',
                            digits=dp.get_precision('Product Unit of Measure'),
                            required=True, default=1)
    discount = fields.Float(string='Discount (%)',
                            digits=dp.get_precision('Discount'),
                            default=0.0)

    analytic_tag_ids = fields.Many2many('account.analytic.tag',
                                        string='Analytic Tags')
    company_id = fields.Many2one('res.company', string='Company',
                                 related='invoice_id.company_id', store=True,
                                 readonly=True, related_sudo=False)

    currency_id = fields.Many2one('res.currency',
                                  related='invoice_id.currency_id', store=True,
                                  related_sudo=False)
    company_currency_id = fields.Many2one('res.currency',
                                          related='invoice_id.company_currency_id',
                                          readonly=True,
                                          related_sudo=False)'''



'''class InterInvoiceLine(models.Model):
    _name = 'inter.invoice.line'
    _description = 'Inter Invoice Line'

    name = fields.Text(string='Description', required=True)
    origin = fields.Char(string='Source Document',
                         help="Reference of the document that produced this invoice.")
    sequence = fields.Integer(default=10,
                              help="Gives the sequence of this line when displaying the invoice.")
    invoice_id = fields.Many2one('account.invoice', string='Invoice Reference',
                                 ondelete='cascade', index=True)
    uom_id = fields.Many2one('product.uom', string='Unit of Measure',
                             ondelete='set null', index=True, oldname='uos_id')
    product_id = fields.Many2one('product.product', string='Product',
                                 ondelete='restrict', index=True)
    account_id = fields.Many2one('account.account', string='Account',
                                 required=True, domain=[('deprecated', '=', False)],
                                 default=_default_account,
                                 help="The income or expense account related to the selected product.")
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    price_subtotal = fields.Monetary(string='Amount',
                                     store=True, readonly=True, compute='_compute_price')
    price_subtotal_signed = fields.Monetary(string='Amount Signed', currency_field='company_currency_id',
                                            store=True, readonly=True, compute='_compute_price',
                                            help="Total amount in the currency of the company, negative for credit notes.")
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'),
                            required=True, default=1)
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'),
                            default=0.0)
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    company_id = fields.Many2one('res.company', string='Company',
                                 related='invoice_id.company_id', store=True, readonly=True, related_sudo=False)
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 related='invoice_id.partner_id', store=True, readonly=True, related_sudo=False)
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id', store=True, related_sudo=False)
    company_currency_id = fields.Many2one('res.currency', related='invoice_id.company_currency_id', readonly=True,
                                          related_sudo=False)'''
