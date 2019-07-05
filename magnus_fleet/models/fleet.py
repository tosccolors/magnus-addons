# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

class FleetVehicleContract(models.Model):

    _inherit = 'fleet.vehicle.log.contract'

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
                            log_contract = self.env['fleet.vehicle.log.contract'].search(
                                [('vehicle_id', '=', record.id), ('state', 'in', ('open', 'toclose'))],
                                limit=1, order='expiration_date asc')
                            if log_contract:
                                # we display only the name of the oldest overdue/due soon contract
                                name = log_contract.cost_subtype_id.name

                record.contract_renewal_overdue = overdue
                record.contract_renewal_due_soon = due_soon
                record.contract_renewal_total = total - 1  # we remove 1 from the real total for display purposes
                record.contract_renewal_name = name

    def _search_contract_renewal_due_soon(self, operator, value):
        res = []
        assert operator in ('=', '!=', '<>') and value in (True, False), 'Operation not supported'
        if (operator == '=' and value is True) or (operator in ('<>', '!=') and value is False):
            search_operator = 'in'
        else:
            search_operator = 'not in'
        today = fields.Date.context_today(self)
        datetime_today = fields.Datetime.from_string(today)
        limit_date = fields.Datetime.to_string(datetime_today + relativedelta(days=+182))
        self.env.cr.execute("""SELECT cost.vehicle_id,
                        count(contract.id) AS contract_number
                        FROM fleet_vehicle_cost cost
                        LEFT JOIN fleet_vehicle_log_contract contract ON contract.cost_id = cost.id
                        WHERE contract.expiration_date IS NOT NULL
                          AND contract.expiration_date > %s
                          AND contract.expiration_date < %s
                          AND contract.state IN ('open', 'toclose')
                        GROUP BY cost.vehicle_id""", (today, limit_date))
        res_ids = [x[0] for x in self.env.cr.fetchall()]
        res.append(('id', search_operator, res_ids))
        return res

    def scheduler_manage_contract_expiration(self):
        # This method is called by a cron task
        # It manages the state of a contract, possibly by posting a message on the vehicle concerned and updating its status
        date_today = fields.Date.from_string(fields.Date.context_today(self))
        limit_date = fields.Date.to_string(date_today + relativedelta(days=+182))
        contracts = self.search([('state', '=', 'open'), ('expiration_date', '<', limit_date)])
        res = {}
        for contract in contracts:
            if contract.vehicle_id.id in res:
                res[contract.vehicle_id.id] += 1
            else:
                res[contract.vehicle_id.id] = 1

        Vehicle = self.env['fleet.vehicle']
        for vehicle, value in res.items():
            Vehicle.browse(vehicle).message_post(body=_('%s contract(s) need(s) to be renewed and/or closed!') % value)
        return contracts.write({'state': 'toclose'})