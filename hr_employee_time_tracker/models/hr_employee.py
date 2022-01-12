# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrEmployee(models.Model):
    _name = 'hr.employee'
    _inherit = ['hr.employee', 'data.track.thread']

class EmployeeCategory(models.Model):

    _name = "hr.employee.category"
    _inherit = ['hr.employee.category', 'data.track.thread']

class HrDepartment(models.Model):

    _name = "hr.department"
    _inherit = ['hr.department', 'data.track.thread']