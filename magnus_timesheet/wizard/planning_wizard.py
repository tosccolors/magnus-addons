# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from lxml import etree


class PlanningWizard(models.TransientModel):
    _name = 'planning.wizard'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PlanningWizard, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        if view_type == 'form':
            ctx = self.env.context
            doc = etree.XML(res['arch'])
            period = doc.xpath("//field[@name='name']")[0]
            date = datetime.now().date()
            month_start_date = date.replace(day=1)
            domain = [('type_id.calender_week', '=', False), ('type_id.fiscal_year', '=', False),
                 ('type_id.fiscal_month', '=', False), ('date_start', '>=', month_start_date)]

            cur_quarter = ctx.get('active_planning_quarter', False)
            if cur_quarter:
                domain += [('id', '!=', cur_quarter)]
            period_ids = self.env['date.range'].search(domain)
            period.set('domain', "[('id', 'in', %s)]" % (period_ids.ids))
            res['arch'] = etree.tostring(doc)
        return res

    name = fields.Many2one('date.range', string='Select Quarter', required=True, index=True)


    @api.multi
    def load_period(self):
        view_type = 'form,tree'
        planning = self.env['magnus.planning'].search(
            [('user_id', '=', self._uid), ('planning_quarter', '=', self.name.id)])
        if len(planning) > 1:
            domain = "[('id', 'in', " + str(planning.ids) + "),('user_id', '=', uid)]"
        else:
            domain = "[('user_id', '=', uid)]"
        value = {
            'domain': domain,
            'name': _('Open Planning'),
            'view_type': 'form',
            'view_mode': view_type,
            'res_model': 'magnus.planning',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {'readonly_by_pass': True}
        }
        if len(planning) == 1:
            value['res_id'] = planning.ids[0]
        else:
            value['context']['default_planning_quarter']= self.name.id
        return value
