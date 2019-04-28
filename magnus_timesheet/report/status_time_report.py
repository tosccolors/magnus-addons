# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools

class StatusTimeReport(models.Model):
    _name = 'status.time.report'
    _auto = False
    _description = 'Status Time Report'

#    date = fields.Date('Date', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    week_id = fields.Many2one('date.range', string='Week', readonly=True)
    sheet_id = fields.Many2one('hr_timesheet_sheet.sheet', string='Employee', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
#    operating_unit_id = fields.Many2one('operating.unit', string='Department Operating Unit', readonly=True)
    state = fields.Char('State', readonly=True)
    validators = fields.Char(
        string='Validators'
    )
    ts_optional = fields.Boolean(
        'Time Sheet Optional',
        readonly=True
    )
    external = fields.Boolean(string='External', readonly=True)


    @api.model_cr
    def init(self):
        """ """
        drcw = self.env.ref('magnus_date_range_week.date_range_calender_week').id
        tools.drop_view_if_exists(self.env.cr, 'status_time_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW status_time_report AS (
            SELECT 
            hrc.id * 100 + dr.id as id,
            dr.id as week_id, 
            hrc.id as employee_id, 
            hrc.department_id as dep_id, 
            hrc.name_related as name, 
            hrc.external as external,
            hrc.timesheet_optional as ts_optional,
            string_agg(rp.name,',') as validators,
            htsss.state as state,
            dr.name as week
            FROM date_range dr
            CROSS JOIN  hr_employee hrc
            LEFT JOIN hr_timesheet_sheet_sheet htsss ON (dr.id = htsss.week_id and hrc.id = htsss.employee_id)
            LEFT JOIN hr_department hd ON (hd.id = hrc.department_id)
            LEFT JOIN hr_timesheet_sheet_sheet_res_users_rel validators ON (htsss.id = validators.hr_timesheet_sheet_sheet_id)
            LEFT JOIN res_users ru ON (validators.res_users_id = ru.id)
            LEFT JOIN res_partner rp ON (rp.id = ru.partner_id)
            WHERE dr.type_id = %s 
            AND hrc.official_date_of_employment < dr.date_start
            AND (
            hrc.end_date_of_employment > dr.date_end 
            OR hrc.end_date_of_employment is NULL
            )
            GROUP BY hrc.id, dr.id, hrc.department_id, hrc.name_related, htsss.state
            ORDER BY name, week
            )""" % (drcw))


