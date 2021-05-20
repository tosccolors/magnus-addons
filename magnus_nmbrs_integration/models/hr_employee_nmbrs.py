from odoo import api, fields, models, _
# import odoo.addons.decimal_precision as dp
# from odoo.exceptions import UserError
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client, Settings
import os
from zeep.transports import Transport
# from zeep.plugins import HistoryPlugin
# from odoo.addons.queue_job.job import job, related_action
# from odoo.addons.queue_job.exception import FailedJobError
# from unidecode import unidecode
import datetime
# from suds.plugin import MessagePlugin
# from lxml import etree
# from dicttoxml import dicttoxml

class HrEmployeeFromOdooToNmbrs(models.Model):
    _name = 'create.employee.from.odoo.to.nmbrs'

    first_name = fields.Char("First name")
    last_name = fields.Char("Last name")
    start_date = fields.Date("Start date")
    company_id = fields.Char("Company ID")
    gender = fields.Char("Gender")
    email = fields.Char("email")
    bsn = fields.Char("BSN")
    mobile = fields.Char("Mobile")
    birthday = fields.Date("Birthday")
    place_of_birth = fields.Char("Place of birth")
    code_country_of_birth = fields.Char("Country Code of Birth Country")
    nationality = fields.Char("Nationality")
    bic = fields.Char("BIC")
    acc_number = fields.Char("Bank account number")
    marital_status = fields.Char("Marital Status")
    street = fields.Char("Street")
    housenumber = fields.Char("Housenumber")
    housenumber_addition = fields.Char("Housenumber Addition")
    zip = fields.Char("ZIP")
    city = fields.Char("City")
    country_code_address = fields.Char("Country Code of Address")
    gross_salary = fields.Char("Gross Salary")
    fte = fields.Char("FTE (1, 0.8 etc)")
    pension_contrib_employee = fields.Char("Pension Contribution Employee")
    pension_contrib_employer = fields.Char("Pension Contribution Employer")
    health_insurance_contrib = fields.Char("Health Insurance Contribution")
    unprotected_mode = fields.Boolean("Unprotected Mode")

    def insert_employee(self):
        config = self.env['nmbrs.interface.config'].search([])[0]
        user = config.api_user
        token = config.api_key
        authentication_v3 = {'Username': user, 'Token': token, 'Domain': 'magnus'}
        client = Client(config.endpoint_employee_service)
        nmbrs_id = client.service.Employee_Insert(
            _soapheaders={'AuthHeaderWithDomain': authentication_v3},
            StartDate=self.start_date,
            FirstName=self.first_name,
            LastName=self.last_name,
            CompanyId=self.company_id,
            UnprotectedMode=self.unprotected_mode
        )
        nmbrs_data = client.service.PersonalInfo_GetCurrent(
            _soapheaders={'AuthHeaderWithDomain': self.authentication_v3},
            EmployeeId=nmbrs_id,
        )
        nmbrs_nr = nmbrs_data['EmployeeNumber']

        client.service.PersonalInfo_UpdateCurrent(
            _soapheaders={'AuthHeaderWithDomain': self.authentication_v3},
            EmployeeId=nmbrs_id,
            PersonalInfo={
                'Id': nmbrs_id,
                'EmployeeNumber': nmbrs_nr,
                'BSN': self.bsn,
                'Number': nmbrs_nr,
                'FirstName': self.first_name,
                'LastName': self.last_name,
                'Nickname': self.first_name,
                'EmailWork': self.email,
                'Gender': self.gender,
                'NationalityCode': '1', # To Do: mapping
                'IdentificationType': '0', #To Do: mapping
                'BurgerlijkeStaat': self.marital_status,
                'Naamstelling': None,
                'TelephoneWork': self.mobile,
                'Birthday': self.birthday
            }
        )

        client.service.BankAccount_InsertCurrent(
        _soapheaders={'AuthHeaderWithDomain': self.authentication_v3},
        EmployeeId=nmbrs_id,
        #UnprotectedMode=True,
        BankAccount={
            'Id': nmbrs_id,
            'Number': nmbrs_nr,
            'IBAN': self.acc_number,
            'BIC': self.bic,
            #'Name': 'RABOBANK',
            'Type': 'Bankrekening1'
            }
        )

        client.service.Address_InsertCurrent(
            _soapheaders={'AuthHeaderWithDomain': self.authentication_v3},
            EmployeeId=nmbrs_id,
            Address={
                'Id': nmbrs_id,
                'Default': True,
                'Street': self.street,
                'PostalCode': self.zip,
                'HouseNumber': self.housenumber,
                'HouseNumberAddition': self.housenumber_addition,
                'City': self.city,
                'CountryISOCode': self.country_code_address,
                'Type': 'HomeAddress',
                }
            )
        return nmbrs_id


class NmbrsNationality(models.Model):
    _name = "hr.nmbrs.nationality"
    _rec_name = "nationality"

    nationality = fields.Char("Country")
    country_code_nmbrs = fields.Char("Country Code Nmbrs")
