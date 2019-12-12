# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from datetime import datetime


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

class Task(models.Model):
    _inherit = "project.task"

    task_user_ids = fields.One2many(
        'task.user',
        'task_id',
        string='Can register time',
        track_visibility='always'
    )

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

    @api.model
    def _get_category_domain(self):
        return [('categ_id','=', self.env.ref(
            'magnus_timesheet.product_category_fee_rate').id)]

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
        default=_default_product,
        domain=_get_category_domain
    )
    fee_rate = fields.Float(
        default=_default_fee_rate,
        string='Fee Rate',
    )
    
    from_date = fields.Date(
        string='From Date',
        default=datetime.today()
    )

    @api.onchange('user_id')
    def onchange_user_id(self):
        self.product_id = False
        self.fee_rate = 0
        if self.user_id:
            emp = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)])
            if emp:
                product = emp.product_id
                self.product_id = product.id
                self.fee_rate = product.lst_price

    @api.multi
    def get_user_fee_rate(self, task_id, user_id, date):
        taskUserObj = self.search([('from_date', '<=', date), ('task_id', '=', task_id), ('user_id', '=', user_id)], order='from_date Desc', limit=1)
        return taskUserObj

class InvoiceScheduleLine(models.Model):
    _name = 'invoice.schedule.lines'

    project_id = fields.Many2one(
        'project.project',
    )

class ProjectInvoicingProperties(models.Model):
    _inherit = "project.invoicing.properties"

    group_invoice = fields.Boolean('Group Invoice')
