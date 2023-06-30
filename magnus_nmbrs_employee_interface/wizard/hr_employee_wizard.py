from odoo import api, fields, models, _
import re


class HREmployeeWizard(models.TransientModel):
    """Some additions to the preexisting employee wizard (magnus-addons) to facilitate inserting the employee in NMBRs"""
    _inherit = "hr.employee.wizard"

    def _compute_street_number(self):
        """Converses the address info to a number proof format"""
        if self.street:
            self.street_nmbrs = re.sub(r'\d+', '', self.street)
            self.housenr_nmbrs = [int(s) for s in re.findall(r'-?\d+\.?\d*', self.street)][0]

    send_to_nmbrs = fields.Boolean(string="Create employee in Nmbrs as well")
    marital_status = fields.Selection([('Gehuwd', 'Married'), ('Ongehuwd', 'Unmarried')], string="Marital Status")
    street_nmbrs = fields.Char("Street Nmbrs", compute=_compute_street_number)
    housenr_nmbrs = fields.Char("House number", compute=_compute_street_number)
    housenr_addition_nmbrs = fields.Char("")
    nationality = fields.Many2one('hr.nmbrs.nationality', string="Nationality")
    analytic_account = fields.Many2one('account.analytic.account', string="Analytic Account")

    
    def fetch_employee_data(self):
        """Collects the relevant data and returns a dict"""
        employee_data = {
            'first_name': self.firstname,
            'last_name': self.lastname,
            'start_date': self.official_date_of_employment,
            'company_id': self.default_operating_unit_id.nmbrs_id,
            'gender': 'undefined' if self.gender == 'other' else self.gender,
            'marital_status': self.marital_status,
            'mobile': self.mobile,
            'email': self.email,
            'birthday': self.birthday,
            'place_of_birth': self.place_of_birth,
            'acc_number': self.acc_number,
            'bic': self.bank_name_id.bic,
            'unprotected_mode': True,
            'street': self.street_nmbrs or False,
            'analytic_account': self.analytic_account.id,
            'country_code_address': self.country_id.code,
            'housenumber': self.housenr_nmbrs or False,
            'housenumber_addition': self.housenr_addition_nmbrs or "",
            'zip': self.zip or False,
            'city': self.city or False
        }
        return employee_data

    
    def create_all(self):
        """If the box "send to NMBRs" is ticked, then call create a create.employee.from.odoo.to.nmbrs record, and
        use functions from this object to insert the employee in nmbrs"""
        employee_id = super(HREmployeeWizard, self).create_all()
        if self.send_to_nmbrs:
            employee_data = self.fetch_employee_data()
            employee_data['employee_number'] = self.env['hr.employee'].browse(employee_id.id).identification_id
            api_service = self.env['create.employee.from.odoo.to.nmbrs'].sudo().create(employee_data)
            nmbrs_id = api_service.insert_employee()
            self.env['hr.employee'].browse(employee_id.id).write({'employee_numbersid': nmbrs_id})
        return employee_id

    
    @api.onchange('department_id')
    def onchange_department_id(self):
        """Function that sets a domain on the selectable analytic accounts based on the selected department"""
        mapped_analytic_account_ids = self.env['mapping.nmbrs.analytic.account'].search([]).mapped('analytic_account_odoo').ids
        res = {}
        res['domain'] = {'analytic_account': [('id','in',mapped_analytic_account_ids)]}
        return res
