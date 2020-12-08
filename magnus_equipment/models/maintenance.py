# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class MaintenanceEquipment(models.Model):
    _name = 'maintenance.equipment'
    _inherit = ['maintenance.equipment','data.track.thread']

    start_date = fields.Date(string="Assigned on")
    end_date = fields.Date(string="Replaced on")
    is_being_repaired = fields.Boolean(string="The device currently is being repaired")
    imei_number = fields.Char("IMEI Number")
    puk_code = fields.Char("PUK Code")


