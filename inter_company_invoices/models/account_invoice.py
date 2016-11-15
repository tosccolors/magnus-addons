# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp.osv import fields, orm
from openerp import SUPERUSER_ID
from openerp.exceptions import Warning


class account_invoice(orm.Model):

    _inherit = 'account.invoice'

    _columns = {
    'auto_generated' : fields.boolean(string='Auto Generated Document'),
    'auto_invoice_id' : fields.many2one('account.invoice', string='Source Invoice', readonly=True ),
    }

    _defaults = {
        'auto_generated' : False,
    }
    def invoice_validate(self, cr, uid, ids, context=None):
        """ Validated invoice generate cross invoice base on company rules """
        for invoice in self.browse(cr, uid, ids, context=context):
            # do not consider invoices that have already been auto-generated, nor the invoices that were already validated in the past
            company_obj = self.pool.get('res.company')
            suid = SUPERUSER_ID
            auto_invoice = self.pool.get('account.invoice').search(cr, suid, [('auto_invoice_id', '=', invoice.id), ('state', '!=', 'cancel')])
            if auto_invoice:
                raise Warning("An auto-generated Intercompany invoice is already existing and not cancelled")
            company = company_obj.find_company_from_partner(cr, suid, invoice.partner_id.id,)
            if company and company.auto_generate_invoices and not invoice.auto_generated:
                intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
                if not intercompany_uid:
                    raise Warning("Provide one user for intercompany relation for %s " % company.name)
                if invoice.type == 'out_invoice':
                    self.inter_company_create_invoice(cr, intercompany_uid, company, invoice, 'in_invoice', 'purchase')
                elif invoice.type == 'in_invoice':
                    self.inter_company_create_invoice(cr, intercompany_uid, company, invoice, 'out_invoice', 'sale')
                elif invoice.type == 'out_refund':
                    self.inter_company_create_invoice(cr, intercompany_uid, company, invoice, 'in_refund', 'purchase_refund')
                elif invoice.type == 'in_refund':
                    self.inter_company_create_invoice(cr, intercompany_uid, company, invoice, 'out_refund', 'sale_refund')
        return super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)

    def inter_company_create_invoice(self, cr, uid, company, invoice, inv_type, journal_type, context=None):
        """ create an invoice for the given company : it wil copy the invoice lines in the new
            invoice. The intercompany user is the author of the new invoice.
            :param company : the company of the created invoice
            :rtype company : res.company record
            :param inv_type : the type of the invoice ('in_refund', 'out_refund', 'in_invoice', ...)
            :rtype inv_type : string
            :param journal_type : the type of the journal to register the invoice
            :rtype journal_type : string
        """
        # find user for creating the invoice from company
        partner = invoice.company_id.partner_id
        partner_id = partner.id
        company_id = company.id
        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({'force_company': company_id})
        period_obj = self.pool.get('account.period')
        period_original_date_start = invoice.period_id.date_start
        period_original_date_stop = invoice.period_id.date_stop
        period = period_obj.search(cr, uid, [('date_start', '=', period_original_date_start), ('date_stop', '=', period_original_date_stop), ('company_id', '=', company_id)], limit=1)
        invoice_line_ids = []
        result = {}
        for line in invoice.invoice_line:
            # get invoice line data from product onchange
            product_uom_id = line.product_id.uom_id and line.product_id.uom_id.id or False
            line_obj = self.pool.get('account.invoice.line')
            if line.product_id.id:
                ids = []
                line_data = line_obj.product_id_change(cr, uid, ids,
                                                product=line.product_id.id,
                                                uom_id=product_uom_id,
                                                qty=line.quantity,
                                                name=line.name,
                                                type=inv_type,
                                                partner_id=partner_id,
                                                fposition_id=partner.property_account_position.id,
                                                company_id=company_id,
                                                context=ctx)
                if inv_type in ('in_invoice','in_refund'):
                    line_data['value']['account_analytic_id'] = company.intercompany_analytic_account.id
            else:
                result['type'] = inv_type
                result['partner_id'] = partner_id
                result['company_id'] = company_id
                if inv_type in ('in_invoice','in_refund'):
                    result['account_id'] = company.intercompany_expense_account.id
                    result['account_analytic_id'] = company.intercompany_analytic_account.id
                    result['invoice_line_tax_id'] = company.intercompany_expense_tax_id.id
                else:
                    result['account_id'] = company.intercompany_income_account.id
                    result['invoice_line_tax_id'] = company.intercompany_income_tax_id.id
                line_data = {'value': result }

            # create invoice line, as the intercompany user
            inv_line_data = self.prepare_invoice_line_data(cr, uid, line_data, line)
            inv_line_id = self.pool.get('account.invoice.line').create(cr, uid, inv_line_data, context=context)
            invoice_line_ids.append(inv_line_id)
        # create invoice, as the intercompany user
        invoice_vals = self.prepare_invoice_data(cr, uid, invoice_line_ids, period, inv_type, invoice, journal_type, partner, company)

        res = super(account_invoice,self).create(cr, uid, invoice_vals, context=context)
        return res

    def prepare_invoice_data(self, cr, uid, invoice_line_ids, period, inv_type, invoice, journal_type, partner, company, context=None):
        """ Generate invoice values
            :param invoice_line_ids : the ids of the invoice lines
            :rtype invoice_line_ids : array of integer
            :param inv_type : the type of the invoice to prepare the values
            :param journal_type : type of the journal to register the invoice_line_ids
            :rtype journal_type : string
            :rtype company : res.company record
        """
        # find the correct journal
        journal = self.pool.get('account.journal').search(cr, uid, [('type', '=', journal_type), ('company_id', '=', company.id)], limit=1)
        if not journal:
            raise Warning("Please define %s journal for this company"  % journal_type)

        # find periods of supplier company
        if context is None:
            context = {}
        context['company_id'] = company.id
        ids = []
        # find account, payment term, fiscal position, bank.
        partner_data = self.onchange_partner_id(cr, uid, ids, inv_type, partner_id=partner.id, company_id=company.id)
        res = {
            'name': invoice.name,
            #TODO : not sure !!
            'origin': partner.name + (' Invoice: ') + str(invoice.number),
            'type': inv_type,
            'date_invoice': invoice.date_invoice,
            'reference': invoice.reference,
            'account_id': partner_data['value']['account_id'] or False,
            'partner_id': partner.id,
            'journal_id': journal[0],
            'invoice_line': [(6, 0, invoice_line_ids)],
            'currency_id': invoice.currency_id and invoice.currency_id.id,
            'fiscal_position': partner_data['value']['fiscal_position'] or False,
            'payment_term': partner_data['value']['payment_term'] or False,

            'company_id': company.id,
            'period_id': period[0] or False,
            'auto_generated': True,
            'auto_invoice_id': invoice.id,
        }
        if inv_type in ('in_invoice','in_refund'):
            res['supplier_invoice_number'] = invoice.number
            res['check_total'] = invoice.amount_total
        if 'partner_bank_id' in partner_data['value']:
            res['partner_bank_id'] = partner_data['value']['partner_bank_id'] or False,
        return res


    def prepare_invoice_line_data(self, cr, uid, line_data, line, context=None):
        """ Generate invoice line values
            :param line_data : dict of invoice line data
            :rtype line_data : dict
            :param line : the invoice line object
            :rtype line : account.invoice.line record
        """
        #import pdb; pdb.set_trace()
        vals = {
            'name': line.name,
            'price_unit': line.price_unit,
            'quantity': line.quantity,
            'discount': line.discount,
            'product_id': line.product_id.id or False,
            'uos_id': line.uos_id.id or False,
            'sequence': line.sequence,
        }
        if 'invoice_line_tax_id' in line_data['value']:
            vals['invoice_line_tax_id'] = (6, 0, [line_data['value']['invoice_line_tax_id']]),
        if 'account_analytic_id' in line_data['value']:
            vals['account_analytic_id'] = line_data['value']['account_analytic_id']
        if 'account_id' in line_data['value']:
            vals['account_id'] = line_data['value']['account_id']
        return vals
