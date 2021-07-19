# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import Warning
import re
class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    model_id = fields.Many2one('fleet.vehicle.model', 'Model',required=False, help='Model of the vehicle')
    rdw_brand = fields.Char("RDW Merk")
    rdw_handelsnaam = fields.Char("RDW Handelsnaam")

    def fetch_data_from_rdw(self):
        rdw_data = self.env['vehicle.from.rdw'].create({'license_plate': re.sub('-', '',self.license_plate)})
        rdw_data_dict = rdw_data.fetch_rdw_data()
        self.update({
            'color': rdw_data_dict['color'],
            'seats': rdw_data_dict['seats'],
            'doors': rdw_data_dict['doors'],
            'rdw_brand': rdw_data_dict['brand'].capitalize(),
            'rdw_handelsnaam': rdw_data_dict['type'].capitalize(),
            'co2': rdw_data_dict['co2'],
            'car_value': rdw_data_dict['fiscal_value'],
            'fuel_type': self.fetch_fuel_type(rdw_data_dict['fuel_type']),
            'model_id': self.fetch_model_id(rdw_data_dict['brand'], rdw_data_dict['type'])
        })

    def fetch_fuel_type(self, rdw_fuel_type):
        if rdw_fuel_type == "Benzine":
            return "gasoline"
        elif rdw_fuel_type =="Diesel":
            return "diesel"
        elif rdw_fuel_type == "Elektriciteit":
            return "electric"
        else:
            return None

    # def fetch_transmission_type(self, rdw_transmission_type):

    def fetch_model_id(self, rdw_brand_name, rdw_model):
        #fetch brand
        brand_id = self.env["fleet.vehicle.model.brand"].search([("name", "ilike", rdw_brand_name)]).id
        if brand_id:
            model_id = self.env["fleet.vehicle.model"].search(['&', ("brand_id", "=", brand_id), ("name", 'ilike', rdw_model)]).id
            return model_id
        return None

    @api.depends('model_id', 'license_plate')
    def _compute_vehicle_name(self):
        for record in self:
            if record.model_id.brand_id.name and record.model_id.name:
                record.name = record.model_id.brand_id.name + '/' + record.model_id.name + '/' + record.license_plate
            elif record.license_plate:
                record.name = record.license_plate
            else:
                raise Warning(
                    _('Please enter a license plate'))


