from odoo import api, fields, models, _
from zeep import Client, Settings
from datetime import datetime


class HrEmployeeFromOdooToNmbrs(models.TransientModel):
    """Transient model used to insert an employee in NMBRs"""
    _name = 'create.employee.from.odoo.to.nmbrs'

    first_name = fields.Char("First name")
    employee_number = fields.Char("Nmbrs number")
    last_name = fields.Char("Last name")
    start_date = fields.Date("Start date")
    company_id = fields.Char("Company ID")
    gender = fields.Char("Gender")
    email = fields.Char("email")
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
    analytic_account = fields.Many2one('account.analytic.account', string="Analytic Account")
    unprotected_mode = fields.Boolean("Unprotected Mode")

    @api.multi
    def insert_employee(self):
        config = self.env['nmbrs.interface.config'].search([])[0]
        user = config.api_user
        token = config.api_key
        authentication_v3 = {'Username': user, 'Token': token, 'Domain': 'magnus'}
        client = Client(config.endpoint_employee_service)
        mapping_analytic_account_nmbrs_object = analytic_account_nmbrs_id = self.env['mapping.nmbrs.analytic.account'].search([('analytic_account_odoo', '=', self.analytic_account.id)])
        analytic_account_nmbrs_id = mapping_analytic_account_nmbrs_object.analytic_account_id_nmbrs
        analytic_account_nmbrs_code = mapping_analytic_account_nmbrs_object.analytic_account_code_nmbrs
        analytic_account_nmbrs_description = mapping_analytic_account_nmbrs_object.analytic_account_name_nmbrs
        #Create the emplyoee in NMBRs
        nmbrs_id = client.service.Employee_Insert(
            _soapheaders={'AuthHeaderWithDomain': authentication_v3},
            StartDate=datetime.strptime(str(self.start_date),'%Y-%m-%d'),
            FirstName=self.first_name,
            LastName=self.last_name,
            CompanyId=self.company_id,
            UnprotectedMode=self.unprotected_mode
        )
        #Update employee info
        client.service.PersonalInfo_UpdateCurrent(
            _soapheaders={'AuthHeaderWithDomain': authentication_v3},
            EmployeeId=nmbrs_id,
            PersonalInfo={
                'Id': nmbrs_id,
                'EmployeeNumber': self.employee_number,
                # 'BSN': self.bsn,
                'Number': self.employee_number,
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
                'Birthday': datetime.strptime(str(self.birthday),'%Y-%m-%d')
            }
        )
        #Update bank account
        client.service.BankAccount_InsertCurrent(
        _soapheaders={'AuthHeaderWithDomain': authentication_v3},
        EmployeeId=nmbrs_id,
        BankAccount={
            'Id': nmbrs_id,
            'Number': self.employee_number,
            'IBAN': self.acc_number,
            'BIC': self.bic,
            'Type': 'Bankrekening1'
            }
        )
        #Insert adress
        client.service.Address_InsertCurrent(
            _soapheaders={'AuthHeaderWithDomain': authentication_v3},
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
        #Update analytic account of salary costs
        client.service.CostCenter_UpdateCurrent(
            _soapheaders={'AuthHeaderWithDomain': authentication_v3},
            EmployeeId=nmbrs_id,
            CostCenters={
                'EmployeeCostCenter':
                {
                    'Id': analytic_account_nmbrs_id,
                    'CostCenter': {
                        'Code': analytic_account_nmbrs_code,
                        # 'Description': analytic_account_nmbrs_description,
                        # 'Id': None
                    },
                    'Kostensoort': None,
                    'Percentage': 100,
                    'Default': True
                }
            }
        )
        return nmbrs_id #Is catched in wizard, and saved on employee


class NmbrsNationality(models.Model):
    """Object to facilitate a mapping between the nationalities in NMBRs and Odoo"""
    _name = "hr.nmbrs.nationality"
    _rec_name = "nationality"

    nationality = fields.Char("Country")
    country_code_nmbrs = fields.Char("Country Code Nmbrs")
