# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

class ProjectInvoicingProperties(models.Model):
    _inherit = "project.invoicing.properties"

    custom_layout = fields.Boolean('Add Custom Header/Footer')
    custom_header = fields.Text('Custom Header')
    custom_footer = fields.Text('Custom Footer')
    specs_on_task_level = fields.Boolean('Specification on task level')
