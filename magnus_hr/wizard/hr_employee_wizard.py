# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from werkzeug import url_encode

class HREmployeeWizard(models.TransientModel):
    _name= "hr.employee.wizard"
    _description = "Employee creation wizard"
    
    firstname = fields.Char("Firstname")
    lastname = fields.Char("Lastname")
    email = fields.Char("Email")
    mobile = fields.Char("Mobile")
    gender = fields.Selection([('male','Male'),('female','Female'),('other','Other')],string="Gender")
    birthday = fields.Date("Date of Birth")
    place_of_birth = fields.Char("Place of Birth")
    acc_number = fields.Char("Account number")
    bank_name_id =  fields.Many2one("res.bank","Bank")
    login = fields.Char("Login")
    ref = fields.Char("Internal Reference")
    department_id = fields.Many2one("hr.department","Department")
    default_operating_unit_id = fields.Many2one("operating.unit","Default operating unit")
    operating_unit_ids = fields.Many2many("operating.unit",string="Operating unit")
    allocated_leaves = fields.Integer("Allocated Leaves")
    product_id = fields.Many2one("product.product","Free rate product")
    #Address
    street = fields.Char("Street")
    zip = fields.Char("Zip")
    city = fields.Char("City")
    country_id = fields.Many2one("res.country","Country")
    
    account_id = fields.Many2one("account.account","Account")
    initial_employment_date = fields.Date("Initial date of employment")
    official_date_of_employment = fields.Date("Official date of employment")
    temporary_contract = fields.Date("Temporary contract")
    category_ids = fields.Many2many("hr.employee.category",string="Category")
    external = fields.Boolean("External")
    
    role_line_ids = fields.One2many("users.role.wizard","user_role_id","Roles")

    @api.multi
    def create_employee(self):
        emp_dict = {}
        user_dict = {}
        partner_dict = {}
        """ Employee and user creation data"""
        hr_employee = self.env['hr.employee']
        hr_users = self.env['res.users']
        res_partner = self.env['res.partner']
        res_partner_bank = self.env['res.partner.bank']
        account_payment_term = self.env['account.payment.term']
        account_payment_mode = self.env['account.payment.mode']
        firstname = self.firstname
        lastname = self.lastname
        email = self.email
        gender = self.gender
        mobile = self.mobile
        birthday = self.birthday
        place_of_birth = self.place_of_birth
        bank_id = self.bank_name_id and self.bank_name_id.id
        department_id = self.department_id and self.department_id.id
        allocated_leaves = self.allocated_leaves
        account_id = self.account_id and self.account_id.id
        initial_employment_date = self.initial_employment_date
        official_date_of_employment = self.official_date_of_employment
        temporary_contract = self.temporary_contract
        category_ids = self.category_ids.ids
        acc_number = self.acc_number
        external = self.external
        login = self.login
        street = self.street
        zip = self.zip
        city =  self.city
        country_id = self.country_id and self.country_id.id
        ref = self.ref
        product_id = self.product_id and self.product_id.id
        default_operating_unit_id = self.default_operating_unit_id and self.default_operating_unit_id.id
        operating_unit_ids = self.operating_unit_ids and self.operating_unit_ids.ids
        
        full_name=''
        if firstname and lastname:
            full_name = firstname +' '+ lastname
            
            
        """ partner creation"""
        account_payment_term_id = account_payment_term.search([('name','=','Immediate Payment')],limit=1)
        account_payment_mode_id = account_payment_mode.search([('name','=','SEPA Credit Transfer (Outbound)')],limit=1)
        partner_dict.update({'name':full_name,
                             'lastname':lastname,
                             'firstname':firstname,
                             'street':street,
                             'zip':zip,
                             'city':city,
                             'country_id':country_id,
                             'email':email,
                             'mobile':mobile,
                             'ref':ref,
                             'supplier':True,
                             'customer':False,
                             'notify_email':'none',
                             'property_supplier_payment_term_id': account_payment_term_id and account_payment_term_id.id ,
                             'supplier_payment_mode_id':account_payment_mode_id and account_payment_mode_id.id,
                             'lang':'nl_NL'})
        res_partner_id = res_partner.create(partner_dict)
            
        res_partner_bank_id = res_partner_bank.search([('acc_number','=',acc_number)],limit=1)
        if res_partner_bank_id:
            res_partner_bank_id = res_partner_bank_id 
        else:
            res_partner_bank_id = res_partner_bank.create({'acc_number':acc_number,
                                     'bank_id':bank_id,
                                     'partner_id':res_partner_id and res_partner_id.id
                                     })
        
        emp_dict.update({'name':full_name,
                         'firstname':firstname,
                         'lastname':lastname,
                         'work_email':email,
                         'gender':gender,
                         'mobile_phone':mobile,
                         'birthday':birthday,
                         'place_of_birth':place_of_birth,
                         'bank_account_id':res_partner_bank_id and res_partner_bank_id.id,
                         'department_id':department_id,
                         'allocated_leaves':allocated_leaves,
                         'account_id':account_id,
                         'initial_employment_date':initial_employment_date,
                         'official_date_of_employment':official_date_of_employment,
                         'temporary_contract':temporary_contract,
                         'category_ids':[(6, 0, category_ids)],
                         'external':external,
                          'product_id':product_id,
                         })
        employee_id = hr_employee.create(emp_dict)
        
        user_dict.update({'firstname':firstname,
                          'lastname':lastname,
                          'login':login,
                          'partner_id':res_partner_id and res_partner_id.id,
                          'default_operating_unit_id':default_operating_unit_id,
                          'operating_unit_ids':[(6,0,operating_unit_ids)],
                          })
        hr_user_id = hr_users.create(user_dict)
        employee_id.write({'bank_account_id':res_partner_bank_id and res_partner_bank_id.id,
                           'address_home_id':res_partner_id and res_partner_id.id,
                           'user_id':hr_user_id and hr_user_id.id})
        
        list_role = []
        for role in self.role_line_ids:
            data = {'role_id':role.id,
                              'date_from':role.from_date,
                              'date_to':role.to_date,
                              'user_id':hr_user_id and hr_user_id.id}
            list_role.append((0, 0, data))
        hr_user_id.write({'role_line_ids':list_role})
            
        return True
    
class UsersRoleWizard(models.TransientModel):
    _name= "users.role.wizard"
    _description = "Employee role"
    
    user_role_id = fields.Many2one("hr.employee.wizard","Role")
    role_id = fields.Many2one("res.users.role","Role")
    from_date = fields.Date("From")
    to_date = fields.Date("To")
    is_enable = fields.Boolean("Enabled")
    

    
    
    
    
    
    
    
    
    
    
    




    
 

    
