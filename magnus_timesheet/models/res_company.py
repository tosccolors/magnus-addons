# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Company(models.Model):
    _inherit = 'res.company'

    wip_journal_id = fields.Many2one('account.journal', 'WIP Journal', domain=[('type','=','wip')])

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
