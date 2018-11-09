# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class Project(models.Model):
    _inherit = "project.project"

    invoice_principle = fields.Selection([
            ('ff','Fixed Fee'),
            ('tm','Time and Material'),
            ('ctm', 'Capped Time and Material')
        ],)
    invoice_schedule_ids = fields.One2many(
        'invoice.schedule.lines',
        'project_id',
        string='Invoice Schedule')
    code = fields.Char('Project Code')
    billable = fields.Boolean('Billable')
    chargeable = fields.Boolean('Chargeable')
    tag_ids = fields.Many2many('project.tags', string='Tags')
    invoice_type = fields.Many2one('project.invoicing.type','Invoicing Type')
    invoice_period = fields.Many2one('project.invoicing.period','Invoice Periodicity')
    expenses = fields.Boolean('Expenses', default=True)
    po_number = fields.Char('PO Number')
    specs_invoice_report = fields.Boolean('Add specs attachment to invoice')

    @api.multi
    def name_get(self):
        return [(value.id, "%s%s" % (value.code + '-' if value.code else '', value.name)) for value in self]

    @api.onchange('billable','chargeable')
    def onchange_billable(self):
        if self.billable and not self.chargeable:
            self.chargeable = True


class Task(models.Model):
    _inherit = "project.task"

    task_user_ids = fields.One2many(
        'task.user',
        'task_id',
        string='Can register time',
        track_visibility='always'
    )

    @api.model
    def default_get(self, fields):
        res = super(Task, self).default_get(fields)
        active_model = self.env.context.get('active_model', False)
        if active_model and active_model == 'project.project':
            active_id = self.env.context.get('active_id', False)
            if active_id:
                project = self.env['project.project'].browse(active_id)
                res['tag_ids'] = project.tag_ids.ids
        return res

    @api.onchange('project_id')
    def onchange_tags(self):
        if self.project_id and self.project_id.tag_ids:
            self.tag_ids = list(set(self.tag_ids.ids+self.project_id.tag_ids.ids))


class TaskUser(models.Model):
    _name = 'task.user'

    @api.one
    @api.depends('product_id')
    def _default_fee_rate(self):
        if self.product_id:
            self.fee_rate = self.product_id.list_price

    @api.model
    def _default_product(self):
        if self.user_id.employee_ids.product_id:
            return self.user_id.employee_ids.product_id.id

    task_id = fields.Many2one(
        'project.task',
        string='Task'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Consultants'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Fee rate Product',
        default=_default_product
    )
    fee_rate = fields.Float(
        default=_default_fee_rate,
        string='Fee Rate',
    )

class InvoiceScheduleLine(models.Model):
    _name = 'invoice.schedule.lines'

    project_id = fields.Many2one(
        'project.project',
    )


class ProjectInvoicingType(models.Model):
    _name = "project.invoicing.type"
    _description = "Project invoicing types"

    name = fields.Char('Project Invoice Type',required=True)

class ProjectInvoicingPeriod(models.Model):
    _name = "project.invoicing.period"
    _description = "Project invoicing periods"

    name = fields.Char('Project Invoice Period',required=True)

