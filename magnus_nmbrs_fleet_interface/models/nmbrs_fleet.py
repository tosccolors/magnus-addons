from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from zeep import Client, Settings
import datetime
import xml.etree.ElementTree as ET
import os


class NMBRsFleet(models.Model):
    """
    Model used to show the latest fleet changes
    """
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
        "fleet.fiscal.addition.mapping",
        string="Fiscal Addition NMBRs",
        readonly=True
    )

class FiscalAdditionMapping(models.Model):
    """
    Mapping table for fiscal addition mapping between NMBRs and Odoo
    """
    _inherit = "fleet.fiscal.addition.mapping"

    fiscal_addition_nmbrs_id = fields.Char("NMBRs ID")

class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    nmbrs_id = fields.Char("NMBRs ID")
