from odoo import api, fields, models, _
import re


class HREmployeeWizard(models.TransientModel):
    _inherit = "hr.employee.wizard"

    send_to_nmbrs = fields.Boolean(string="Create employee in Nmbrs as well")
    start_date_contract = fields.Date(string="Start date of contract")
    # operating_unit_nmbrs = fields.Many2one("operating.unit", string="Operating Unit for Nmbrs")
    # bsn = fields.Char("BSN")
    # gross_salary = fields.Float("Salary")
    # fte = fields.Char("FTE (1, 0.8 etc)")
    # pension_contrib_employee = fields.Char("Pension Contribution Employee")
    # pension_contrib_employer = fields.Char("Pension Contribution Employer")
    # health_insurance_contrib = fields.Char("Health Insurance Contribution")
    marital_status = fields.Selection([('Gehuwd', 'Married'), ('Ongehuwd', 'Unmarried')], string="Marital Status")
    #Adress for nmbrs
    street_nmbrs = fields.Char("Street Nmbrs")
    postal_code_nmbrs = fields.Char("Postal Code Nmbrs")
    city_nmbrs = fields.Char("City Nmbrs")
    housenr_nmbrs = fields.Char("House number")
    housenr_addition_nmbrs = fields.Char("")
    nationality = fields.Many2one('hr.nmbrs.nationality', string="Nationality")
    analytic_account = fields.Many2one('account.analytic.account', string="Analytic Account")

    @api.multi
    def fetch_employee_data(self):
        employee_data = {
            'first_name': self.firstname,
            'last_name': self.lastname,
            'start_date': self.start_date_contract,
            'company_id': self.default_operating_unit_id.nmbrs_id,
            'gender': self.gender_nmbrs(),
            # 'gross_salary': self.gross_salary,
            'marital_status': self.marital_status,
            'mobile': self.mobile,
            'email': self.email,
            'birthday': self.birthday,
            'place_of_birth': self.place_of_birth,
            # 'bsn': self.bsn,
            'acc_number': self.acc_number,
            'bic': self.bank_name_id.bic,
            'unprotected_mode': True,
            'street': self.street_nmbrs,
            'analytic_account': self.analytic_account.id,
            'country_code_address': self.country_id.code,
            'housenumber': self.housenr_nmbrs,
            'housenumber_addition': self.housenr_addition_nmbrs or "",
            'zip': self.postal_code_nmbrs,
            'city': self.city_nmbrs
        }
        return employee_data

    def gender_nmbrs(self):
        if self.gender == 'other':
            return 'undefined'
        else:
            return self.gender

    @api.onchange('street')
    def _on_change_street(self):
        if self.street:
            self.street_nmbrs = re.sub(r'\d+', '', self.street)
            self.housenr_nmbrs = [int(s) for s in re.findall(r'-?\d+\.?\d*', self.street)][0]

    @api.onchange('zip')
    def _on_change_zip(self):
        if self.zip:
            self.postal_code_nmbrs = self.zip

    @api.onchange('city')
    def _on_change_city(self):
        if self.city:
            self.city_nmbrs = self.city

    @api.onchange('official_date_of_employment')
    def _on_change_contract_date(self):
        if self.official_date_of_employment:
            self.start_date_contract = self.official_date_of_employment

    @api.multi
    def create_employee(self):
        if self.send_to_nmbrs:
            employee_id = super(HREmployeeWizard, self).create_employee()
            employee_data = self.fetch_employee_data()
            employee_data['employee_number'] = self.env['hr.employee'].browse(employee_id).identification_id
            api_service = self.env['create.employee.from.odoo.to.nmbrs'].sudo().create(employee_data)
            nmbrs_id = api_service.insert_employee()
            employee_data['employee_number'] = self.env['hr.employee'].browse(employee_id).write({'employee_numbersid': nmbrs_id})

    @api.multi
    @api.onchange('department_id')
    def onchange_department_id(self):
        res = {}
        res['domain'] = {'analytic_account': [('department_id.id', '=', self.department_id.id)]}
        return res