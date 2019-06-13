# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class Task(models.Model):
    _inherit = "project.task"

    @api.one
    @api.constrains('project_id', 'standard')
    def _check_project_standard(self):
        task = self.env['project.task'].search([('project_id', '=', self.project_id.id), ('standard', '=', True)])
        if len(task) > 1 and self.standard:
            raise ValidationError(_('You can have only one task with the standard as true per project!'))

    standard = fields.Boolean(string='Standard')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('name', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search(['!',('name', operator, name), ('jira_compound_key', operator, name)] + args, limit=limit)
        return recs.name_get()


class Project(models.Model):
    _inherit = "project.project"

    overtime = fields.Boolean(string='Overtime Taken')
    overtime_hrs = fields.Boolean(string='Overtime Hours')

    @api.one
    @api.constrains('overtime', 'overtime_hrs')
    def _check_project_overtime(self):
        company_id = self.company_id.id if self.company_id else False

        overtime_taken_project = self.search([('company_id', '=', company_id), ('overtime', '=', True)])
        if len(overtime_taken_project) > 1:
            raise ValidationError(_("You can have only one project with 'Overtime Taken' per company!"))

        overtime_project = self.search([('company_id', '=', company_id), ('overtime_hrs', '=', True)])
        if len(overtime_project) > 1:
            raise ValidationError(_("You can have only one project with 'Overtime Hours' per company!"))


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