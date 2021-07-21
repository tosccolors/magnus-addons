from odoo import api, fields, models, _
from odoo.exceptions import Warning
import requests, json

class VehicleFromRDW(models.Model):
    """
    This object is an intermediate object, to retrieve data from using the RDW Open Data API.
    """
    _name = "vehicle.from.rdw"

    license_plate = fields.Char()

    def fetch_rdw_data(self):
        rdw_data = requests.get('https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken=' + self.license_plate)
        rdw_data_brandstof = requests.get('https://opendata.rdw.nl/resource/8ys7-d773.json?Kenteken=' + self.license_plate)
        if rdw_data.text[1:-2] == u'':
            raise Warning(
                _('Car is not present in RDW Open Data database, please fill details manually.'))
        rdw_data_dict = json.loads(rdw_data.text[1:-2])
        rdw_data_brandstof_dict = json.loads(rdw_data_brandstof.text[1:-2])
        data = {
            'fiscal_value': rdw_data_dict.get('catalogusprijs'),
            'brand': rdw_data_dict.get('merk'),
            'type': rdw_data_dict.get('handelsbenaming'),
            'color': rdw_data_dict.get('eerste_kleur'),
            'end_date_apk': rdw_data_dict.get('vervaldatum_apk'),
            'doors': rdw_data_dict.get('aantal_deuren'),
            'seats': rdw_data_dict.get('aantal_zitplaatsen'),
            'fuel_type': rdw_data_brandstof_dict.get('brandstof_omschrijving'),
            'co2': rdw_data_brandstof_dict.get('co2_uitstoot_gecombineerd')
        }
        return data

