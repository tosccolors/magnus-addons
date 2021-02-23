# -*- coding: utf-8 -*-
from odoo import api, fields, models

class MagnusPlanning(models.Model):
    _inherit = "magnus.planning"

    @api.one
    def _compute_emp_domain(self):
        user = self.employee_id.user_id
        self_planning = self.env.context.get('self_planning', False)
        domain = ['|','|','|',
                  ('department_id.manager_id.user_id','=',user.id),
                  ('department_id.parent_id.manager_id.user_id','=',user.id),
                  ('department_id.manager_2_ids','=',user.employee_ids.ids[0]),
                  ('parent_id.user_id','=',user.id)]
        if self_planning:
            domain = [('user_id', '=', user.id)]
        emp_list = self.env['hr.employee'].search(domain).ids
        self.emp_domain_compute = ",".join(map(str, emp_list))

    def get_employee_child_ids(self):
        child_ids = super(MagnusPlanning, self).get_employee_child_ids()
        # get co-manager departments employee list
        self.env.cr.execute("""
            WITH RECURSIVE
                subordinates AS(
                    SELECT id, parent_id FROM hr_department WHERE id IN 
                    (select hr_department_id from hr_department_hr_employee_rel where hr_employee_id = %s)
                    UNION
                    SELECT h.id, h.parent_id FROM hr_department h
                    INNER JOIN subordinates s ON s.id = h.parent_id)
                SELECT  *  FROM subordinates
            """
            % (self.employee_id.id))
        co_mgr_dept_list = [x[0] for x in self.env.cr.fetchall() if x[0]]

        op, dept_list = '=', co_mgr_dept_list[0]

        if len(co_mgr_dept_list) > 1:
            op, dept_list = 'IN', tuple(co_mgr_dept_list)

        self.env.cr.execute("""SELECT id FROM hr_employee WHERE department_id %s %s"""
            % (op, dept_list))

        co_mgr_emp_list = [x[0] for x in self.env.cr.fetchall() if x[0]]

        child_ids = list(set(co_mgr_emp_list+child_ids))
        return child_ids