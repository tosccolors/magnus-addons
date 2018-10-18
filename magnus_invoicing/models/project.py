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
