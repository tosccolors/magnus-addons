# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime
class FleetVehicleContract(models.Model):

    _inherit = 'fleet.vehicle.log.contract'

    km_range_contract = fields.Integer("Kilometer Range Contract")
    price_more_km = fields.Float("Price more km")
    price_less_km = fields.Float("Price less km")
    lease_period = fields.Integer("Lease Period")
    
    @api.model
    def create(self,vals):
        if vals.get('start_date') and (vals.get('lease_period') > 0):
            start_date = datetime.strptime(vals.get('start_date'), '%Y-%m-%d')
            end_date = start_date + relativedelta(months=vals.get('lease_period'))
            vals.update({'expiration_date':end_date})
        return super(FleetVehicleContract,self).create(vals)
    
    @api.multi
    def write(self,vals):
        if vals.get('lease_period') > 0:
            start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
            end_date = start_date + relativedelta(months=vals.get('lease_period'))
            vals.update({'expiration_date':end_date})
        return super(FleetVehicleContract,self).write(vals)
        
    @api.onchange('lease_period')
    @api.depends('lease_period')
    def _lease_priod_on_change(self):
        if self.lease_period > 0:
            if self.start_date:
                start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
                end_date = start_date + relativedelta(months=self.lease_period)
                self.expiration_date = end_date
    
    @api.onchange('sum_cost')
    @api.depends('sum_cost')
    def _amount_on_change(self):
        self.amount = self.sum_cost
    
class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    
    fiscal_addition = fields.Float("Fiscal Addition")
    hoem_work_distance = fields.Integer("Home/Work Distance")
    location = fields.Integer("Personal Contribution")


    @api.depends('log_contracts')
    def _compute_contract_reminder(self):
        for record in self:
            overdue = False
            due_soon = False
            total = 0
            name = ''
            for element in record.log_contracts:
                if element.state in ('open', 'toclose') and element.expiration_date:
                    current_date_str = fields.Date.context_today(record)
                    due_time_str = element.expiration_date
                    current_date = fields.Date.from_string(current_date_str)
                    due_time = fields.Date.from_string(due_time_str)
                    diff_time = (due_time - current_date).days
                    if diff_time < 0:
                        overdue = True
                        total += 1
                    if diff_time < 182 and diff_time >= 0:
                            due_soon = True
                            total += 1
                    if overdue or due_soon:
                        log_contract = self.env['fleet.vehicle.log.contract'].search([('vehicle_id', '=', record.id), ('state', 'in', ('open', 'toclose'))],
                            limit=1, order='expiration_date asc')
                        if log_contract:
                            #we display only the name of the oldest overdue/due soon contract
                            name = log_contract.cost_subtype_id.name

            record.contract_renewal_overdue = overdue
            record.contract_renewal_due_soon = due_soon
            record.contract_renewal_total = total - 1  # we remove 1 from the real total for display purposes
            record.contract_renewal_name = name