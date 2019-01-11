# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _, SUPERUSER_ID

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    _sql_constraints = [('driver_uniq', 'unique (driver_id)', "The driver already owns a vehicle.")]

    def _set_odometer(self):
        for record in self:
            if record.odometer:
                date = fields.Date.context_today(record)
                data = {'value': record.odometer, 'date': date, 'vehicle_id': record.id}
                self.env['fleet.vehicle.odometer'].create(data)

class FleetVehicleOdometer(models.Model):
    _inherit = 'fleet.vehicle.odometer'

    value_period = fields.Float('Odometer Period Value', group_operator="sum")

    def odo_newer(self):
        newer = self.search([(
            'vehicle_id', '=', self.vehicle_id.id),('date','>', self.date)], limit=1, order='date asc')
        newer._compute_odometer_value()

    @api.depends('value_period', 'value')
    def _compute_odometer_value(self):
        older = self.search([(
            'vehicle_id', '=', self.vehicle_id.id),('date','<', self.date)], limit=1, order='date desc')
        if older:
            if not self.value_period:
                self.value_period = self.value - older.value
            if not self.value:
                self.value = older.value + self.value_period
        else:
            self.value = self.value_period
        if self.date < self.search([('vehicle_id', '=', self.vehicle_id.id)], limit=1, order='date desc'):
            self.odo_newer()

    '''@api.model
    def create(self, data):
        res = super(FleetVehicleOdometer, self).create(data)
        if res.date < self.search([('vehicle_id', '=', res.vehicle_id)], limit=1, order='date desc'):
            res._compute_odometer_value()'''


    @api.model
    def unlink(self):
        for odom in self:
            gone_date = odom.date
            gone_vehicle = odom.vehicle_id.id
            super(FleetVehicleOdometer, odom).unlink()
            if gone_date < odom.search([('vehicle_id', '=', gone_vehicle)], limit=1, order='date desc'):
                older = odom.search([('vehicle_id', '=', gone_vehicle), ('date', '<', gone_date)], limit=1, order='date desc')
                older.odo_newer()
