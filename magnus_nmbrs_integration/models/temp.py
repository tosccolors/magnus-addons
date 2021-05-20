from zeep import Client, Settings
from odoo import api, fields, models, _
import xml.etree.ElementTree as ET
import os
import datetime

first_name = fields.Char("First name")
last_name = fields.Char("Last name")
start_date = fields.Date("Start date")
company_id = fields.Char("Company ID")
unprotected_mode = fields.Boolean("Unprotected Mode")
user = os.environ['nmbrs_user']
token = os.environ['nmbrs_token']
Authentication_v3 = {'Username': user, 'Token': token, 'Domain': 'magnus'}
Authentication_v2 = {'Username': user, 'Token': token}
wsdl_sandbox_v3 = 'https://api-sandbox.nmbrs.nl/soap/v3/DebtorService.asmx?WSDL'
wsdl_sandbox_v2 = 'https://api-sandbox.nmbrs.nl/soap/v2.1/EmployeeService.asmx?WSDL'
client = Client(wsdl_sandbox_v3)

# x = client.service.PersonalInfo_Update(
#     _soapheaders={'AuthHeaderWithDomain': Authentication_v3},
#     EmployeeId='1005125',
#     PersonalInfo={
#         'Id': '1005125',
#         'EmployeeNumber': '81135',
#         'BSN': '123456789',
#         'Number': '81135',
#         'FirstName': 'Donald',
#         'LastName': 'Duck',
#         'Nickname': 'Donald',
#         'Gender': 'male',
#         'NationalityCode': '1',
#         'IdentificationType': '0',
#         'BurgerlijkeStaat': 'Ongehuwd',
#         'Naamstelling': None,
#         'TelephoneWork': '06-31155435',
#         'Birthday': datetime.datetime(1996, 11, 3, 0, 0)
#     },
#     Period=5,
#     Year=2021
#     )
# x = client.service.BankAccount_Insert(
#     _soapheaders={'AuthHeaderWithDomain': Authentication_v3},
#     EmployeeId='1057235',
#     period=5,
#     year=2021,
#     UnprotectedMode=True,
#     BankAccount={
#         'Id': '1057235',
#         'Number': '81135',
#         'IBAN': 'NL75RABO0309320453',
#         'BIC': 'RABONL2U',
#         'Name': 'RABOBANK',
#         'Type': 'Bankrekening1'
#         }
#     )

# x = client.service.Journals_GetByRunCostCenter(
#     _soapheaders={'AuthHeaderWithDomain': Authentication_v3},
#     CompanyId=52171,
#     RunId=109319L
# )
# import xml.etree.ElementTree as ET
# root = ET.fromstring(x)
# lines = {}
# for i in range(len(root[0][1])):
#     line = root[0][1][i]
#     line_info = {
#         'id': line.attrib['id'],
#         'account': line[0].text,
#         'analytic_account': line[1].text,
#         'credit': line[2].text if line[3].text == 'credit'else 0,
#         'debit': line[2].text if line[3].text == 'debit'else 0,
#         'desccription': line[4].text
#     }
#     lines[i+1] = line_info

# x=client.service.Environment_Get(
#     _soapheaders={'AuthHeader': Authentication_v2}
# )

import os

api_key_nmbrs = os.environ['nmbrs_token']
a = 5
# print(x)