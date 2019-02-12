# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools

class HrChargeabilityReport(models.Model):
    _name = 'hr.chargeability.report'
    _auto = False
    _description = 'Hr Chargeability Report'

    date = fields.Date('Date', readonly=True)
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    chargeable_hours = fields.Float(string="Charegeable Hrs", readonly=True)
    norm_hours = fields.Float(string="Norm Hrs", readonly=True)
    chargeability = fields.Float(string="Chargeability", readonly=True)

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
                        SUM(CASE WHEN aa.chargeable = 'true' THEN unit_amount ELSE 0 END) as chargeable_hours,
                        ((COUNT(project_id)*8) - SUM(CASE WHEN aa.correction_charge = 'true' THEN unit_amount ELSE 0 END)) as norm_hours,
                        ((SUM(CASE WHEN aa.chargeable = 'true' THEN unit_amount ELSE 0 END))/
                         (CASE WHEN
                            ((COUNT(project_id)*8) - SUM(CASE WHEN aa.correction_charge = 'true' THEN unit_amount ELSE 0 END)) = 0  
                            THEN 1
                            ELSE ((COUNT(project_id)*8) - SUM(CASE WHEN aa.correction_charge = 'true' THEN unit_amount ELSE 0 END)) END
                         ))*100 as chargeability
                    FROM
                        account_analytic_line as aa 
                    WHERE aa.product_uom_id = %s AND aa.project_id IS NOT NULL 
                    AND (aa.correction_charge = true OR aa.chargeable = true)

                    GROUP BY aa.user_id, aa.date
                )""" % (uom))

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(HrChargeabilityReport, self).read_group(domain, fields, groupby, offset, limit=limit, orderby=orderby, lazy=lazy)
        for index, val in enumerate(res):
            domain = val.get('__domain', False)

            if domain:
                where_query = self._where_calc(domain)
                from_clause, where_clause, where_clause_params = where_query.get_sql()

                list_query = ("""
                        SELECT
                            chargeable_hours, norm_hours
                          FROM
                            {0}
                          WHERE {1}
                     """.format(
                    from_clause,
                    where_clause
                ))

                self.env.cr.execute(list_query, where_clause_params)
            else:
                list_query = ("""
                        SELECT
                            chargeable_hours, norm_hours
                          FROM
                            hr_chargeability_report
                     """
                )
                self.env.cr.execute(list_query)
            result = self._cr.fetchall()
            chargeable_hours, norm_hours = 0, 0
            for r in result:
                chargeable_hours += r[0]
                norm_hours += r[1]
            if chargeable_hours or norm_hours:
                norm_hours = norm_hours if norm_hours else chargeable_hours #if norm_hrs zero chargeability would be 100%
                res[index]['chargeability'] = (chargeable_hours / norm_hours) * 100

        return res
