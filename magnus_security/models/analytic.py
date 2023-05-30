# -*- coding: utf-8 -*-

from odoo import models, fields, api
from lxml import etree
# from odoo.osv.orm import setup_modifiers
from odoo import SUPERUSER_ID

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        result = super(AccountAnalyticLine, self).fields_view_get(
            view_id, view_type, toolbar, submenu)
        if (self.user_has_groups("hr.group_hr_manager,hr.group_hr_user") or SUPERUSER_ID == self._uid) and view_type == 'tree':
            doc = etree.XML(result['arch'])
            pro_nodes = doc.xpath("//field[@name='project_id']")
            if pro_nodes:
                # pro_nodes[0].set('widget', 'many2one_clickable')
                # setup_modifiers(
                #     pro_nodes[0], result['fields']['project_id'])
                pro_nodes[0].attrib["widget"] = "many2one_clickable"
            tsk_nodes = doc.xpath("//field[@name='task_id']")
            if tsk_nodes:
                # tsk_nodes[0].set('widget', 'many2one_clickable')
                # setup_modifiers(
                #     tsk_nodes[0], result['fields']['task_id'])
                tsk_nodes[0].attrib["widget"] = "many2one_clickable"
            result['arch'] = etree.tostring(doc)
        return result






