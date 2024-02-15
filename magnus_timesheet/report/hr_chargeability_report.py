# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class HrChargeabilityReport(models.Model):
    _name = 'hr.chargeability.report'
    _auto = False
    _description = 'Hr Chargeability Report'

    date = fields.Date(
        'Date',
        readonly=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        readonly=True
    )
    captured_hours = fields.Float(
        string="Captured Hrs",
        readonly=True
    )
    chargeable_hours = fields.Float(
        string="Chargeable Hrs",
        readonly=True
    )
    norm_hours = fields.Float(
        string="Norm Hrs",
        readonly=True
    )
    chargeability = fields.Float(
        string="Chargeability",
        readonly=True
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        readonly=True
    )
    operating_unit_id = fields.Many2one(
        'operating.unit',
        string='Department Operating Unit',
        readonly=True
    )
    external = fields.Boolean(
        string='External',
        readonly=True
    )
    ts_optional = fields.Boolean(
        string='Timesheet Optional',
        readonly=True
    )
    ts_no_8_hours_day = fields.Boolean(
        string='No 8 Hours Per Day',
        readonly=True
    )


    @api.model_cr
    def init(self):
        """ """
        uom = self.env.ref('product.product_uom_hour').id
        tools.drop_view_if_exists(self.env.cr, 'hr_chargeability_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW hr_chargeability_report AS (
                SELECT
                    min(aa.id) as id,
                    aa.date as date,
                    aa.user_id as user_id,
                    aa.operating_unit_id as operating_unit_id,
                    aa.department_id as department_id,
                    emp.external as external,
                    emp.timesheet_optional as ts_optional,
                    emp.timesheet_no_8_hours_day as ts_no_8_hours_day,
                    SUM(unit_amount) as captured_hours,
                    SUM(CASE 
                             WHEN aa.chargeable = 'true' 
                             THEN unit_amount 
                             ELSE 0 
                        END) as chargeable_hours,
                    (COUNT (DISTINCT aa.date) * (
							 CASE 
                             WHEN dr.date_end - aa.date > 1
                             THEN 8 
                             ELSE 0 
							 END
							 )
                    - SUM(
                        CASE 
                            WHEN aa.correction_charge = 'true' 
                            THEN unit_amount 
                            ELSE 0 
                        END)) as norm_hours,
                    0.0  as chargeability
                FROM account_analytic_line aa
                JOIN resource_resource resource 
                ON (resource.user_id = aa.user_id)
                JOIN hr_employee emp 
                ON (emp.resource_id = resource.id)
                JOIN date_range dr 
                ON (dr.id = aa.week_id)
                WHERE aa.product_uom_id = %s 
                    AND aa.planned = FALSE
                    AND (aa.ot = FALSE or aa.ot is null)
                    AND aa.project_id IS NOT NULL 
                    AND resource.active = TRUE
                    AND aa.state != 'change-chargecode'
                GROUP BY 
                    aa.operating_unit_id, 
                    aa.user_id, 
                    dr.date_end, 
                    aa.date, 
                    aa.department_id, 
                    emp.external, 
                    emp.timesheet_optional, 
                    emp.timesheet_no_8_hours_day
				ORDER BY aa.date
            )""" % (uom))


    @api.model
    def read_group(
            self,
            domain,
            fields,
            groupby,
            offset=0,
            limit=None,
            orderby=False,
            lazy=True
        ):
        res = super(HrChargeabilityReport, self).read_group(
            domain,
            fields,
            groupby,
            offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy
        )
        for index, val in enumerate(res):
            # if res[index].get('norm_hours', False) and res[index].get(
            #         'chargeable_hours', False):
            res[index]['chargeability'] = \
                (res[index]['chargeable_hours'] /
                res[index]['norm_hours']) * 100 \
                    if res[index]['norm_hours'] > 0 else 0.0
            # else:
            #     raise UserError(
            #         _('You have to select Chargeable Hours and Norm Hours as '
            #           'measure for this report'))
        return res
