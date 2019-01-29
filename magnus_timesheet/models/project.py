# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _, SUPERUSER_ID

class ProjectInvoicingProperties(models.Model):
    _inherit = "project.invoicing.properties"

    invoice_mileage = fields.Boolean('Invoice Mileage')

    @api.onchange('invoice_mileage')
    def onchange_invoice_mileage(self):
        try:
            id = self._origin.id
        except:
            id = self.id
        project = self.env['project.project'].search([('invoice_properties', '=', id)])
        if project:
            analytic_lines = self.env['account.analytic.line'].search([('project_id', 'in', project.ids), ('product_uom_id', '=', self.env.ref('product.product_uom_km').id)])
            if analytic_lines:
                non_invoiceable_mileage = False if self.invoice_mileage else True
                cond = '='
                rec = analytic_lines.ids[0]
                if len(analytic_lines) > 1:
                    cond = 'IN'
                    rec = tuple(analytic_lines.ids)
                self.env.cr.execute("""
                    UPDATE account_analytic_line SET product_uom_id = %s, non_invoiceable_mileage = %s WHERE id %s %s
                """ % (self.env.ref('product.product_uom_km').id, non_invoiceable_mileage, cond, rec))