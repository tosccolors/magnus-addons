# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _, SUPERUSER_ID

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    _sql_constraints = [('driver_uniq', 'unique (driver_id)', "The driver already owns a vehicle.")]