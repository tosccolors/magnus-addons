# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2016 BAS Solutions
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    invoice_description = fields.Html('Description')

    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        return self.env['report'].get_action(self, 'magnus_account.report_invoice_magnus_account')

    @api.multi
    def group_by_analytic_acc(self, type, uom_hrs=False):
        self.ensure_one()
        result = {}
        if type == 'sale_order':
            for line in self.invoice_line_ids:
                if line.account_analytic_id in result:
                    result[line.account_analytic_id].append(line)
                else:
                    result[line.account_analytic_id] = [line]
        if type == 'project':
            UOMHrs = self.env.ref('uom.product_uom_hour').id
            if uom_hrs:
                for line in self.invoice_line_ids.filtered(lambda l: l.uom_id.id == UOMHrs):
                    quantity = line.uom_id._compute_quantity(line.quantity, line.uom_id)
                    price_subtotal = line.uom_id._compute_price(line.price_subtotal, line.uom_id)
                    if line.account_analytic_id in result:
                        result[line.account_analytic_id]['tot_hrs'] += quantity
                        result[line.account_analytic_id]['sub_total'] += price_subtotal
                    else:
                        result[line.account_analytic_id] = {'tot_hrs':quantity, 'sub_total':price_subtotal}
            else:
                for line in self.invoice_line_ids.filtered(lambda l: not l.uom_id or l.uom_id.id != UOMHrs):
                    if line.account_analytic_id in result:
                        result[line.account_analytic_id].append(line)
                    else:
                        result[line.account_analytic_id] = [line]
        return result

    @api.multi
    def parse_invoice_description(self):
        res = False
        desc = self.invoice_description
        if desc and desc != '<p><br></p>':
            res = True
        return res

    @api.multi
    def value_conversion(self, value, monetary=False, digits=2, currency_obj=False):
        lang_objs = self.env['res.lang'].search([('code', '=', self.partner_id.lang)])
        if not lang_objs:
            lang_objs = self.env['res.lang'].search([], limit=1)
        lang_obj = lang_objs[0]

        res = lang_obj.format('%.' + str(digits) + 'f', value, grouping=True, monetary=monetary)
        if currency_obj and currency_obj.symbol:
            if currency_obj.position == 'after':
                res = u'%s\N{NO-BREAK SPACE}%s' % (res, currency_obj.symbol)
            elif currency_obj and currency_obj.position == 'before':
                res = u'%s\N{NO-BREAK SPACE}%s' % (currency_obj.symbol, res)
        return res

    @api.multi
    def get_invoice_project(self):
        project = self.env['project.project']
        analytic_invoice_id = self.invoice_line_ids.mapped('analytic_invoice_id')

        if analytic_invoice_id:
            project = analytic_invoice_id.project_id
        else:
            account_analytic_id = self.invoice_line_ids.mapped('account_analytic_id')
            if len(account_analytic_id) == 1 and len(account_analytic_id.project_ids) == 1:
                project = account_analytic_id.project_ids
        return project

    @api.multi
    def get_bank_details(self):
        self.ensure_one()
        bank_ids = self.operating_unit_id.partner_id.bank_ids.mapped('bank_id')
        bank_accs = self.env['account.journal'].search([('operating_unit_id', '=', self.operating_unit_id.id),('company_id', '=', self.company_id.id), ('bank_id', 'in', bank_ids.ids), ('type', '=', 'bank')])
        return bank_accs

class ResCompany(models.Model):
    _inherit = 'res.company'

    report_background_image = fields.Binary(
            'Background Image for Report',
            help='Set Background Image for Report')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
