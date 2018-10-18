# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class AnalyticInvoice(models.Model):
    _name = "analytic.invoice"
    _description = "Analytic Invoice"
    _order = "date_to desc"

    @api.one
    @api.depends('partner_id', 'account_analytic_ids', 'month_id', 'gb_task',
                 'gb_week', 'gb_month')
    def _compute_objects(self):
        partner_id = self.partner_id or False
        if partner_id and len(self.account_analytic_ids) == 0:
            account_analytic = self.env['account.analytic.account'].search([
                ('partner_id','=', self.partner_id.id)])
            if len(account_analytic) > 0:
                self.account_analytic_ids = \
                    [(6,0,account_analytic.ids)]
        if len(self.account_analytic_ids) > 0:
            account_analytic_ids = self.account_analytic_ids.ids
            if self.month_id:
                domain = self.month_id.get_domain('date')
                domain += [('account_id', 'in', account_analytic_ids)]
            else:
                domain = [('account_id', 'in', account_analytic_ids)]
            hrs = self.env.ref('product.product_uom_hour').id
            time_domain = domain + [('product_uom_id','=', hrs)]
            self.time_line_ids = self.env['account.analytic.line'].search(
                time_domain).ids
            cost_domain = domain + [('product_uom_id', '!=', hrs),
                                        ('amount','<', 0)]
            self.cost_line_ids = self.env['account.analytic.line'].search(
                cost_domain).ids
            revenue_domain = domain + [('product_uom_id', '!=', hrs),
                                        ('amount', '>', 0)]
            self.revenue_line_ids = self.env['account.analytic.line'].search(
                revenue_domain).ids
#            import pdb;
#            pdb.set_trace()
            fields_grouped = [
                'id',
                'user_id',
                'task_id',
                'account_id',
                'month_id',
                'week_id',
                'unit_amount'
            ]
            grouped_by = [
                'user_id',
                'task_id',
                'account_id',
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
            if len(result) > 0:
                if self.user_total_ids:
                    self.env['analytic.user.total'].search(
                        [('id','in', self.user_total_ids.ids)]).unlink()
#                ids = self.user_total_ids.ids
#                result_data = []
#                for id in ids:
#                    result_data.append((2,id))
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
                        'month_id': item.get('month_id')[0] if item.get(
                            'month_id') != False else False,
                        'week_id': item.get('week_id')[0] if self.gb_week
                            and item.get('week_id') != False else False,
                        'unit_amount': item.get('unit_amount'),
                    }
#                    result_data.append((0,0,vals))
#                    self.user_total_ids = [(0,0,vals)]
                    aut_id = self.env['analytic.user.total'].create(vals)
                    aal_domain = time_domain + [
                        ('user_id','=',vals['user_id']),
                        ('task_id','=',vals['task_id']),
                        ('account_id','=',vals['account_id']),
                        ('month_id','=',vals['month_id']),
                    ]
                    if vals['week_id']:
                        aal_domain += [('week_id','=', vals['week_id'])]

                    aal = self.env['account.analytic.line'].search(aal_domain)
                    aal.write({'user_total_id': aut_id.id})
#                self.user_total_ids = result_data



    @api.model
    def _get_fiscal_month_domain(self):
        # We have access to self.env in this context.
        fm = self.env.ref('account_fiscal_month.date_range_fiscal_month').id
        return [('type_id', '=', fm)]

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
        compute='_compute_objects',
        string='Time Line',
    )
    cost_line_ids = fields.Many2many(
        'account.analytic.line',
        compute='_compute_objects',
        string='Cost Line',
    )
    revenue_line_ids = fields.Many2many(
        'account.analytic.line',
        compute='_compute_objects',
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

    def create(self, vals):
        res = super(AnalyticInvoice, self).create(vals)


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
    children_ids = fields.One2many(
        'account.analytic.line',
        'user_total_id',
        string='Detail Time Lines',
        readonly=True,
        copy=False
    )
    week_id = fields.Many2one(
        'date.range',
        string='Week',
    )
    month_id = fields.Many2one(
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
