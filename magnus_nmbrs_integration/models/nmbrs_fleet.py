from odoo import api, fields, models, _
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
    nmbrs_id = fields.Char("NMBRs ID")
    fiscal_addition_nmbrs = fields.Many2one("nmbrs.fleet.fiscal.addition.mapping", string="Fiscal Addition NMBRs")

class NMBRsFleetFiscalAdditionMapping(models.Model):
    _name = "nmbrs.fleet.fiscal.addition.mapping"
    _description = "model used to save fiscal addition mapping between NMBRs and Odoo"
    _rec_name = "fiscal_addition"

    fiscal_addition = fields.Float("Fiscal Addition")
    fiscal_addition_nmbrs_id = fields.Char("NMBRs ID")

class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    nmbrs_id = fields.Char("NMBRs ID")
