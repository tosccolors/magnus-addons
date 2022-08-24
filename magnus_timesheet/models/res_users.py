# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class ResUsers(models.Model):
	_inherit = "res.users"

	@api.multi
	def _get_related_employees(self):
		self.ensure_one()
		ctx = dict(self.env.context)
		if 'thread_model' in ctx:
			ctx['thread_model'] = 'hr.employee'
		return self.env['hr.employee'].with_context(ctx).search([('user_id', '=', self.id)])


	@api.multi
	def _get_operating_unit_id(self):
		""" Compute Operating Unit of Employee based on the OU in the
		top Department."""
		employee_id = self._get_related_employees()
		assert not employee_id or len(employee_id) == 1, 'Only one employee can have this user_id'
		if employee_id.department_id:
			if employee_id.department_id.parent_id.id == False:
				dep = employee_id.department_id
			elif employee_id.department_id.parent_id.parent_id.id == False:
				dep = employee_id.department_id.parent_id
			else:
				dep = employee_id.department_id.parent_id.parent_id
		else:
			raise ValidationError(_('The Employee in the Analytic line has '
									'no department defined. Please complete'))
		return dep.operating_unit_id
