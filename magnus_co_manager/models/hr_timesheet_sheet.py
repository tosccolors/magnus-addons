
from odoo import api, fields, models, _


class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet.sheet"

    
    def _get_validator_user_ids(self):
        users = super(HrTimesheetSheet, self)._get_validator_user_ids()
        for timesheet in self:
            managers_to_add = []
            comanagers_ids_dept = [manager.user_id.id for manager in timesheet.department_id.manager_2_ids]
            comanagers_ids_parent_dept = [manager.user_id.id for manager in timesheet.department_id.parent_id.manager_2_ids]
            if comanagers_ids_dept and self.env.uid not in comanagers_ids_dept:
                managers_to_add = managers_to_add + comanagers_ids_dept
            elif comanagers_ids_parent_dept and self.env.uid not in comanagers_ids_parent_dept:
                managers_to_add = managers_to_add + comanagers_ids_parent_dept

            managers_to_add = list(set(managers_to_add))
            for manager in managers_to_add:
                if bool(manager): users.append(manager)
        return users
