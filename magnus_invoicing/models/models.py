# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

# class magnus_invoicing(models.Model):
#     _name = 'magnus_invoicing.magnus_invoicing'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'
    _order = 'date desc'

    @api.multi
    @api.depends('date','product_uom_id')
    def _compute_week_month(self):
        for line in self:
            if not line.product_uom_id == self.env.ref('product.'
                                                       'product_uom_hour'):
                continue
            if line.date:
                line.week_id = line.find_daterange_week(line.date)
                line.month_id = line.find_daterange_month(line.date)
            elif not line.child_ids == []:
                line.week_id = line.find_daterange_week(line.child_ids.date)
                line.month_id = line.find_daterange_month(line.child_ids.date)

    def find_daterange_week(self, date):
        """
        try to find a date range with type 'week'
        with @param:date contained in its date_start/date_end interval
        """
#        date_str = fields.Date.to_string(date)
        s_args = [
            ('type_name', '=', 'Week'),
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
#        date_str = fields.Date.to_string(date)
        s_args = [
            ('type_name', '=', 'Fiscal Month'),
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


    invoiced = fields.Boolean('Invoiced')
    parent_id = fields.Many2one('account.analytic.line',
                                string='Summary Reference',
                                ondelete='cascade',
                                index=True)
    child_ids = fields.One2many('account.analytic.line', 'parent_id',
                                string='Detail Time Lines',
                                readonly=True,
                                copy=False)
    week_id = fields.Many2one('date.range',
                                compute=_compute_week_month,
                                string='Week',
                                store=True, )
    month_id = fields.Many2one('date.range',
                                compute=_compute_week_month,
                                string='Month',
                                store=True, )


    @api.model
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
                    'task_id': res.task_id.id,
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
        return res



    

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
