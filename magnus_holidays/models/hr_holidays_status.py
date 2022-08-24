# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrHolidaysStatus(models.Model):
	_inherit = "hr.leave.type"

	date_end = fields.Datetime(string="Expiry Date", default='2080-12-31 00:00:00')
	is_leave_type_of_wizard = fields.Boolean(string="Is leave type of wizard")
	limit = fields.Boolean('Allow to Override Limit',
		help='If you select this check box, the system allows the employees to take more leaves '
			 'than the available ones for this type and will not take them into account for the '
			 '"Remaining Legal Leaves" defined on the employee form.')

	# @api.multi # this method is replced by (self, employee_id)
	# def get_hours(self, employee):
	# 	self.ensure_one()
	# 	result = {
	# 		'max_hours': 0,
	# 		'remaining_hours': 0,
	# 		'hours_taken': 0,
	# 		'virtual_remaining_hours': 0,
	# 	}
    #
	# 	holiday_ids = employee.holiday_ids.filtered(lambda x: ((x.state == 'validate' and x.type == 'add') or (x.state == 'written' and x.type == 'remove')) and x.holiday_status_id == self)
    #
	# 	for holiday in holiday_ids:
	# 		hours = holiday.number_of_hours_temp
	# 		if holiday.type == 'add':
	# 			result['virtual_remaining_hours'] += hours
	# 			if holiday.state == 'validate':
	# 				result['max_hours'] += hours
	# 				result['remaining_hours'] += hours
	# 		elif holiday.type == 'remove':  # number of hours is negative
	# 			result['virtual_remaining_hours'] -= hours
	# 			if holiday.state == 'written':
	# 				result['hours_taken'] += hours
	# 				result['remaining_hours'] -= hours
    #
	# 	return result

	@api.multi
	def get_days(self, employee_id):
		# need to use `dict` constructor to create a dict per id
		result = dict(
			(id, dict(max_leaves=0, leaves_taken=0, remaining_leaves=0, virtual_remaining_leaves=0)) for id in self.ids)

		requests = self.env['hr.leave'].search([
			('employee_id', '=', employee_id),
			('state', 'in', ['confirm', 'validate1', 'validate', 'written']),
			('holiday_status_id', 'in', self.ids)
		])

		allocations = self.env['hr.leave.allocation'].search([
			('employee_id', '=', employee_id),
			('state', 'in', ['confirm', 'validate1', 'validate']),
			('holiday_status_id', 'in', self.ids)
		])

		for request in requests:
			status_dict = result[request.holiday_status_id.id]
			status_dict['virtual_remaining_leaves'] -= (request.number_of_hours_display
			if request.leave_type_request_unit == 'hour'
			else request.number_of_days)
			if request.state in ('validate', 'written'):
				status_dict['leaves_taken'] += (request.number_of_hours_display
				if request.leave_type_request_unit == 'hour'
				else request.number_of_days)
				status_dict['remaining_leaves'] -= (request.number_of_hours_display
				if request.leave_type_request_unit == 'hour'
				else request.number_of_days)

		for allocation in allocations.sudo():
			status_dict = result[allocation.holiday_status_id.id]
			if allocation.state == 'validate':
				# note: add only validated allocation even for the virtual
				# count; otherwise pending then refused allocation allow
				# the employee to create more leaves than possible
				status_dict['virtual_remaining_leaves'] += (allocation.number_of_hours_display
				if allocation.type_request_unit == 'hour'
				else allocation.number_of_days)
				status_dict['max_leaves'] += (allocation.number_of_hours_display
				if allocation.type_request_unit == 'hour'
				else allocation.number_of_days)
				status_dict['remaining_leaves'] += (allocation.number_of_hours_display
				if allocation.type_request_unit == 'hour'
				else allocation.number_of_days)
		return result