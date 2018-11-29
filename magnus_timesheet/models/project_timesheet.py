# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

class Task(models.Model):
    _inherit = "project.task"

    @api.one
    @api.constrains('prject_id', 'standard')
    def _check_project_standard(self):
        task = self.env['project.task'].search([('project_id', '=', self.project_id.id), ('standard', '=', True)])
        if len(task) > 0 and self.standard:
            raise ValidationError(_('You can have only one task with the standard as true per project!'))

    standard = fields.Boolean(string='Standard')