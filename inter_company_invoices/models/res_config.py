# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp.osv import orm, fields

class inter_company_rules_configuration(orm.TransientModel):

    _inherit = 'base.config.settings'

    _columns = {
        'company_id' : fields.many2one('res.company', 'Select Company',
            help='Select company to setup Inter company rules.'),
        'rule_type' : fields.selection([('invoice_and_refunds', 'Create Invoice/Refunds when encoding invoice/refunds')],
            help='Select the type to setup inter company rules in selected company.'),
    }


    def onchange_company_id(self, cr, uid, company_id, context=None):
        res = {'value': {}}
        if company_id:
            rule_type = False
            company_obj = self.pool.get('res.company')
            company = company_obj.browse(cr, uid, company_id)
            if company.auto_generate_invoices:
                res['value'] = {'rule_type': 'invoice_and_refunds'}
        return res


    def set_inter_company_configuration(self, cr, uid, company_id, context=None):
        vals = {}
        if company_id:
            icc = self.browse(cr, uid, company_id, context=None)
            company_obj = self.pool.get('res.company')
            if icc.rule_type == 'invoice_and_refunds':
                vals = {'auto_generate_invoices': True }
                company_obj.write(vals)
        return vals
