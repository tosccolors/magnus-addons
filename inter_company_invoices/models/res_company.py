# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp.osv import fields, orm
from openerp import SUPERUSER_ID


class res_company(orm.Model):

    _inherit = 'res.company'

    _columns = {
        'auto_generate_invoices' : fields.boolean(string="Create Invoices/Refunds when encoding invoices/refunds made to this company",
            help="Generate Customer/Supplier Invoices (and refunds) when encoding invoices (or refunds) made to this company.\n e.g: Generate a Customer Invoice when a Supplier Invoice with this company as supplier is created."),
        'intercompany_user_id' : fields.many2one('res.users', string="Intercompany User",
            help="Responsible user for creation of documents triggered by intercompany rules."),
        'intercompany_expense_account': fields.many2one('account.account', string="Intercompany Expense Account", domain=[('type','<>','view'),('type','<>','income'), ('type', '<>', 'closed')],
            help="Default account to be used for Supplier Invoices"),
        'intercompany_income_account': fields.many2one('account.account', string="Intercompany Income Account", domain=[('type','<>','view'),('type','<>','expense'), ('type', '<>', 'closed')],
            help="Default account to be used for Customer Invoices"),
        'intercompany_analytic_account': fields.many2one('account.analytic.account', string="Intercompany Analytic Account", help="Default analytic account to be used for Supplier Invoices"),
        'intercompany_expense_tax_id': fields.many2one('account.tax', string="Intercompany Expense Tax Id", domain=[('type_tax_use','=','purchase')],
            help="Default tax code to be used for Supplier Invoices"),
        'intercompany_income_tax_id': fields.many2one('account.tax', string="Intercompany Income Tax Id", domain=[('type_tax_use','=','sale')],
            help="Default tax code to be used for Customer Invoices"),
    }
    _defaults = {
        'intercompany_user_id' : SUPERUSER_ID,
    }

    def find_company_from_partner(self, cr, uid, partner_id, context=None):
        company_id = self.search(cr, uid, [('partner_id', '=', partner_id)], limit=1)
        company = self.browse(cr, uid, company_id)
        return company and company[0] or False



