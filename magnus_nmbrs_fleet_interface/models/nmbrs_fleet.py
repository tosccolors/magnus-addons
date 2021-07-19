from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from zeep import Client, Settings
import datetime
import xml.etree.ElementTree as ET
import os


class NMBRsFleet(models.Model):
    _name = "nmbrs.fleet"
    _description = "model used to show latest changes in fleet for nmbrs"

    driver = fields.Many2one("res.partner", string="Driver")
    employee = fields.Many2one("hr.employee", string="Employee")
    vehicle = fields.Many2one("fleet.vehicle", string="Vehicle")
    license_plate = fields.Char("License Plate")
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    nmbrs_date = fields.Date("NMBRs Date")
    nmbrs_id = fields.Char("NMBRs ID")
    end_contract = fields.Boolean("Employee stops leasing?")
    fiscal_addition_nmbrs = fields.Many2one(
        "nmbrs.fleet.fiscal.addition.mapping",
        string="Fiscal Addition NMBRs",
        readonly=True
    )

class NMBRsFleetFiscalAdditionMapping(models.Model):
    _name = "nmbrs.fleet.fiscal.addition.mapping"
    _description = "model used to save fiscal addition mapping between NMBRs and Odoo"
    _rec_name = "fiscal_addition"

    fiscal_addition = fields.Char("Fiscal Addition")
    fiscal_addition_nmbrs_id = fields.Char("NMBRs ID")

class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    nmbrs_id = fields.Char("NMBRs ID")
    fiscal_addition = fields.Many2one("nmbrs.fleet.fiscal.addition.mapping", string="Fiscal Addition NMBRs")

    def get_nmbrs_vehicle_id(self):
        if self.nmbrs_id:
            raise ValidationError("Car already has a NMBRs ID")
        self.env.cr.execute('SELECT MAX(CAST(used_nmbrs_vehicle_id AS INTEGER)) FROM nmbrs_vehicle_ids')
        new_id = max(self.env.cr.fetchone()[0] + 1, 1000000)
        self.env['nmbrs.vehicle.ids'].create({'used_nmbrs_vehicle_id': (new_id)})
        self.update({'nmbrs_id': new_id})

class NMBRsVehicleIDs(models.Model):
    _name = "nmbrs.vehicle.ids"

    used_nmbrs_vehicle_id = fields.Char()
