from odoo import api, fields, models, _
import re


class HREmployeeWizard(models.TransientModel):
    """Some additions to the preexisting employee wizard (magnus-addons) to facilitate inserting the employee in NMBRs"""
    _inherit = "hr.employee.wizard"

    send_to_nmbrs = fields.Boolean(string="Create employee in Nmbrs as well")
    start_date_contract = fields.Date(string="Start date of contract")
    marital_status = fields.Selection([('Gehuwd', 'Married'), ('Ongehuwd', 'Unmarried')], string="Marital Status")
    street_nmbrs = fields.Char("Street Nmbrs")
    postal_code_nmbrs = fields.Char("Postal Code Nmbrs")
    city_nmbrs = fields.Char("City Nmbrs")
    housenr_nmbrs = fields.Char("House number")
    housenr_addition_nmbrs = fields.Char("")
    nationality = fields.Many2one('hr.nmbrs.nationality', string="Nationality")
    analytic_account = fields.Many2one('account.analytic.account', string="Analytic Account")

    @api.multi
    def fetch_employee_data(self):
        """Collects the relevant data and returns a dict"""
        employee_data = {
            'first_name': self.firstname,
            'last_name': self.lastname,
            'start_date': self.start_date_contract,
            'company_id': self.default_operating_unit_id.nmbrs_id,
            'gender': self.gender_nmbrs(),
            'marital_status': self.marital_status,
            'mobile': self.mobile,
            'email': self.email,
            'birthday': self.birthday,
            'place_of_birth': self.place_of_birth,
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
        """A small conversion function between 'other' in Odoo and 'undefined' in NMBRs"""
        if self.gender == 'other':
            return 'undefined'
        else:
            return self.gender

    @api.onchange('street')
    def _on_change_street(self):
        """Converses the address info to a number proof format"""
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
        """If the box "send to NMBRs" is ticked, then call create a create.employee.from.odoo.to.nmbrs record, and
        use functions from this object to insert the employee in nmbrs"""
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
        """Function that sets a domain on the selectable analytic accounts based on the selected department"""
        res = {}
        res['domain'] = {'analytic_account': [('department_id.id', '=', self.department_id.id)]}
        return res
