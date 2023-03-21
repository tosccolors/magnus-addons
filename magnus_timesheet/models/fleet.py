# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    _sql_constraints = [('driver_uniq', 'unique (driver_id)', "The driver already owns a vehicle.")]

    def _set_odometer(self):
        for record in self:
            if record.odometer:
                date = fields.Date.context_today(record)
                data = {'value_update': record.odometer, 'date': date, 'vehicle_id': record.id}
                self.env['fleet.vehicle.odometer'].create(data)

class FleetVehicleOdometer(models.Model):
    _inherit = 'fleet.vehicle.odometer'

    _sql_constraints = [('date_uniq', 'unique (date, vehicle_id)', 'Odometer records have to have '
                                        'a unique date.')]

    @api.depends('value_period_update', 'value_update')
    def _compute_odometer_value(self):
        for odom in self:
            if odom.value_period_update > 0.0 and odom.value_update > 0.0:
                raise UserError(_("You cannot enter both period value and "
                                  "ultimo value for %s!") % (odom.date))
            older = self.sudo().search([
                ('vehicle_id', '=', odom.vehicle_id.id),
                ('date', '<', odom.date)
            ], limit=1, order='date desc')
            if older:
                if odom.value_period_update == 0.0:
                    odom.value_period = odom.value_update - older.value
                    odom.value = odom.value_update
                if odom.value_update == 0.0:
                    odom.value = older.value + odom.value_period_update
                    odom.value_period = odom.value_period_update
            else:
                if odom.value_period_update == 0.0:
                    odom.value_period = odom.value_update
                    odom.value = odom.value_update
                if odom.value_update == 0.0:
                    odom.value = odom.value_period_update
                    odom.value_period = odom.value_period_update


    value_period = fields.Float(
        compute=_compute_odometer_value,
        string='Odometer Period Value',
        group_operator="sum",
        store = True
    )
    value = fields.Float(
        compute=_compute_odometer_value,
        string='Odometer Value',
        group_operator="max",
        store=True
    )
    value_update = fields.Float(
        string='Odometer Value',
        group_operator="max",
        store=True
    )
    value_period_update = fields.Float(
        string='Odometer Period Value',
        group_operator="sum",
        store=True
    )
#    timestamp = fields.Datetime(
#    )

    @api.model
    def odo_newer(self):
        self.ensure_one()
        newer = self.sudo().search([
            ('vehicle_id', '=', self.vehicle_id.id),
            ('date','>', self.date)
            ], order='date asc')
        former_value = self.value
        for one in newer:
            period = one.value_period
            vals = {
                'value_period_update' : 0,
                'value_update': period + former_value
            }
            one.write(vals)
            former_value = period + former_value



    @api.model
    def create(self, data):
        res = super(FleetVehicleOdometer, self).create(data)
        if res.date < self.sudo().search([('vehicle_id', '=', res.vehicle_id.id)], limit=1, order='date desc').date:
            res.with_context(odo_newer=True).odo_newer()
        return res

    def write(self, data):
        res = super(FleetVehicleOdometer, self).write(data)
        for record in self.filtered(lambda s: not s.env.context.get('odo_newer')):
            if record.date < self.sudo().search([('vehicle_id', '=', record.vehicle_id.id)], limit=1, order='date desc').date:
                record.with_context(odo_newer=True).odo_newer()
        return res

    def unlink(self):
        res = {}
        for odom in self:
            vals = {
                'gone_date': odom.date,
                'gone_vehicle': odom.vehicle_id.id
            }
            res[odom.id] = vals
        super(FleetVehicleOdometer, self).unlink()
        for key, value in res.items():
            if value['gone_date'] < self.sudo().search([
                ('vehicle_id', '=', value['gone_vehicle'])
                ], limit=1, order='date desc').date:
                older = self.sudo().search([
                    ('vehicle_id', '=', value['gone_vehicle']),
                    ('date', '<', value['gone_date'])
                ], limit=1, order='date desc')
                if len(older) == 1:
                    older.with_context(odo_newer=True).odo_newer()
