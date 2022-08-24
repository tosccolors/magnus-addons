# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class MaintenanceEquipment(models.Model):
    _name = 'maintenance.equipment'
    _inherit = ['maintenance.equipment','data.track.thread']

    # start_date = fields.Date(string="Purchased on")
    # end_date = fields.Date(string="Replaced on")
    # is_being_repaired=fields.Boolean(string="The device currently is being repaired")
    # imei_number=fields.Char("IMEI Number")

    # General fields
    purchase_date = fields.Date(string="Date of acquisition", default=datetime.today())
    maintenance_status = fields.Many2one(
        'maintenance.equipment.maintenance.status',
        string="Equipment Status"
    )
    brand = fields.Char(string="Brand")
    model = fields.Char(string="Model")
    warranty_category = fields.Many2one(
        'maintenance.equipment.warranty.category',
        string="Warranty Category",
        track_visibility='onchange',
    )
    warranty_date = fields.Date(string='Warranty until', compute='_compute_warranty_date')
    department = fields.Many2one('hr.department', string="Department")

    # Phone specific fields
    phone_number = fields.Char(string="Phone Number", size=10)
    sim_number = fields.Char(string="SIM number")
    puk_code = fields.Char(string="PUK Code")
    imei_number = fields.Char(string="IMEI Number")
    remarks = fields.Text(string="Remarks")

    # Laptop specific fields
    cpu = fields.Char(string="CPU")
    memory = fields.Char(string="Memory")
    hard_disk = fields.Char(string="Hard Disk")
    accessories = fields.Text(string="Accessories")
    iso_security_check = fields.Date(string="ISO/Security Check")

    @api.depends('purchase_date', 'warranty_category.warranty_duration')
    def _compute_warranty_date(self):
        purchase_date = datetime.strptime(self.purchase_date, "%Y-%m-%d")
        month = purchase_date.month - 1 + self.warranty_category.warranty_duration
        year = purchase_date.year + month // 12
        month = month % 12 + 1
        day = min(purchase_date.day, calendar.monthrange(year, month)[1])
        self.warranty_date = date(year, month, day)


class MaintenanceWarrantyCategory(models.Model):
    _name = 'maintenance.equipment.warranty.category'
    _description = 'Warranty Category of asset'
    _rec_name = 'warranty_category_name'

    warranty_category_name = fields.Char(string="Warranty Category Name")
    warranty_duration = fields.Integer(string="Warranty  (months)")


class MaintenanceStatus(models.Model):
    _name = 'maintenance.equipment.maintenance.status'
    _description = "Class to account for various maintenance status, needed for date time tracking functionality"
    _rec_name = "maintenance_status_name"
    _inherit = 'data.track.thread'

    maintenance_status_name = fields.Char(string="Maintenance Status", default="status_in_use")



