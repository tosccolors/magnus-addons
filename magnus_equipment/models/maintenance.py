# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    start_date = fields.Date(string="Purchased on")
    end_date = fields.Date(string="Replaced on")
    is_being_repaired=fields.Boolean(string="The device currently is being repaired")
    imei_number=fields.Char("IMEI Number")
    owner_history=fields.One2many('equipment.user','maintenance_equipment_id',string='Owner History')

  
class MaintanceEquipmentUser(models.Model):

    _name = 'equipment.user'

    maintenance_equipment_id=fields.Many2one('maintenance.equipment',string="Equipment")
    employee_name=fields.Many2one('hr.employee',string="Employee Name")
    from_date=fields.Date(string="From Date")