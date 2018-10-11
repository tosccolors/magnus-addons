# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class AnalyticInvoice(models.Model):
    _name = "analytic.invoice"
    _description = "Analytic Invoice"
    _order = "date_to desc"

    @api.one
    @api.depends('partner_id', 'account_analytic_ids', 'month_id')
    def _compute_objects(self):
        partner_id = self.partner_id or False
        account_analytic_ids = self.account_analytic_ids or False
        if partner_id and not account_analytic_ids:
            account_analytic = self.env['account.analytic.account'].search([
                ('partner_id','=', self.partner_id.id)])
            self.account_analytic_ids = account_analytic_ids = \
                account_analytic.ids
        if not account_analytic_ids == []:
            domain = self.month_id._get_domain
            domain.append(('account_id', 'in', [account_analytic_ids]))
            self.analytic_line_ids = self.env['account.analytic.lines'].search(
                domain).ids

#        ('project_id.allow_timesheets', '=', True)

    @api.model
    def _get_fiscal_month_domain(self):
        # We have access to self.env in this context.
        fm = self.env.ref('account_fiscal_month.date_range_fiscal_month').id
        return [('type_id', '=', fm)]

    account_analytic_ids = fields.Many2many(
        'account.analytic.account',
        compute='_compute_objects',
        string='Analytic Account',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        domain=[('is_company','=', True)],
    )
    invoice_ids = fields.Many2many(
        'account.invoice',
        string='Customer Invoices',
        ondelete='cascade',
        index=True
    )
    invoice_line_ids = fields.One2many(
        'account.invoice.line',
        'analytic_invoice_id',
        string='New Invoice Lines',
        ondelete='cascade',
        index=True
    )
    analytic_line_ids = fields.Many2many(
        'account.analytic.line',
        compute='_compute_objects',
        string='Analytic Line',
    )
    month_id = fields.Many2one(
        'date.range',
        domain=_get_fiscal_month_domain
    )
    date_from = fields.Date(
        related=month_id.date_start,
        string='Date From'
    )
    date_to = fields.Date(
        related=month_id.date_end,
        string='Date To',
        store=True
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
