from odoo import api, fields, models, _
from zeep import Client, Settings
import datetime
import re


class NMBRsFleetwizard(models.TransientModel):
    _name = "nmbrs.fleet.get.changes.wizard"
    _description = "Wizard to fetch fleet changes for nmbrs"

    from_date = fields.Date(string="Start date")
    to_date = fields.Date(string="End date")

    @api.multi
    def fetch_recently_changed_leases(self):
        line_query = ("""          DELETE FROM nmbrs_fleet;
                                   INSERT INTO nmbrs_fleet (driver, vehicle, license_plate, from_date, to_date, employee, nmbrs_id, fiscal_addition_nmbrs)
                                    SELECT 
                                           res_partner.id AS driver,
                                           fleet_vehicle.id AS vehicle,
                                           fleet_vehicle.license_plate AS license_plate,
                                           date_from AS from_date, 
                                           date_to AS to_date,
                                           hr_employee.id AS employee,
                                           hr_employee.employee_numbersid AS nmbrs_id,
                                           fama.id AS fiscal_addition
                                    FROM data_time_tracker
                                    INNER JOIN fleet_vehicle on model_ref = fleet_vehicle.id
                                    INNER JOIN res_partner on relation_ref = res_partner.id
                                    INNER JOIN res_users on res_partner.id = res_users.partner_id
                                    INNER JOIN resource_resource res_res on res_res.user_id = res_users.id
                                    INNER JOIN hr_employee on hr_employee.resource_id = res_res.id
                                    --LEFT OUTER JOIN nmbrs_fleet_fiscal_addition_mapping fama on CAST(fama.fiscal_addition AS TEXT) = CAST(fleet_vehicle.fiscal_addition AS TEXT)
                                    LEFT OUTER JOIN nmbrs_fleet_fiscal_addition_mapping fama on fama.fiscal_addition = fleet_vehicle.fiscal_addition
                                    WHERE data_time_tracker.model = 'fleet.vehicle' 
                                    AND (
                                    (date_to >= {0} AND date_to <= {1}) OR
                                    (date_from >= {0} AND date_from <= {1})
                                    ) 
                           """.format(
            "'%s'" % self.from_date,
            "'%s'" % self.to_date))
        self.env.cr.execute(line_query)


class FleetChangesFromOdooToNMBRs(models.TransientModel):
    _name = "fleet.changes.from.odoo.to.nmbrs"
    _description = "Wizard to send fleet changes from odoo to nmbrs"

    @api.multi
    def send_changes_to_nmbrs(self):
        context = dict(self._context)
        vehicle_object = self.env['fleet.vehicle']
        nmbrs_fleet_object = self.env['nmbrs.fleet']
        config = self.env['nmbrs.interface.config'].search([])[0]
        user = config.api_user
        token = config.api_key
        authentication_v3 = {'Username': user, 'Token': token, 'Domain': 'magnus'}
        client = Client(config.endpoint_employee_service)

        for change in nmbrs_fleet_object.browse(context.get('active_ids', [])):
            fiscal_value = vehicle_object.browse(change.vehicle.id).car_value
            fiscal_addition = change.fiscal_addition_nmbrs.fiscal_addition_nmbrs_id
            employee_id_nmbrs = change.nmbrs_id
            license_plate = change.license_plate
            date = change.from_date
            client.service.LeaseCar_Insert(
                _soapheaders={'AuthHeaderWithDomain': authentication_v3},
                EmployeeId=employee_id_nmbrs,
                LeaseAuto={
                    'Id': 1,
                    'LicensePlate': license_plate,
                    'CatalogValue': fiscal_value,
                    'StartDate': date,
                    'ContributionPrivatePercentage': fiscal_addition,
                    'ContractDuration': 0,
                    'LeasingPriceMonth': 0,
                    'MaxMileage': 0,
                    'PriceMoreMileage': 0,
                    'PriceLessMileage': 0,
                    'FirstResgistrationDate': datetime.datetime(1, 1, 1, 0, 0),
                    'CO2Emissions': 0,
                    'EndDate': datetime.datetime(1, 1, 1, 0, 0),
                    'ReasonNoContribution': 0,
                    'ContributionPrivateUse': 0,
                    'ContributionNotDeductible': 0
                },
                Year=int(date.strip()[:4]),
                Period=int(date.strip()[5:7])
            )

        return {'type': 'ir.actions.act_window_close'}