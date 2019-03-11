# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet_sheet.sheet"

    def copy_wih_query(self):
        """
        Overriden: to add invoiced, invoiceable, and state for KM(s) analytic entries
        :return:
        """
        query = """
        INSERT INTO
        account_analytic_line
        (       create_uid,
                user_id,
                account_id,
                company_id,
                write_uid,
                amount,
                unit_amount,
                date,
                create_date,
                write_date,
                partner_id,
                name,
                code,
                currency_id,
                ref,
                general_account_id,
                move_id,
                product_id,
                amount_currency,
                project_id,
                department_id,
                task_id,
                sheet_id,
                so_line,
                user_total_id,
                invoiced,
                invoiceable,
                month_id,
                week_id,
                account_department_id,               
                expenses,
                chargeable,
                operating_unit_id,
                project_operating_unit_id,
                correction_charge,
                write_off_move,
                ref_id,
                actual_qty,
                planned_qty,
                planned,
                select_week_id,
                kilometers,
                state,
                non_invoiceable_mileage,
                product_uom_id )
        SELECT  aal.create_uid as create_uid,
                aal.user_id as user_id,
                aal.account_id as account_id,
                aal.company_id as company_id,
                aal.write_uid as write_uid,
                0.0 as amount,
                aal.kilometers as unit_amount,
                aal.date as date,
                %(create)s as create_date,
                %(create)s as write_date,
                aal.partner_id as partner_id,
                aal.name as name,
                aal.code as code,
                aal.currency_id as currency_id,
                aal.ref as ref,
                aal.general_account_id as general_account_id,
                aal.move_id as move_id,
                aal.product_id as product_id,
                aal.amount_currency as amount_currency,
                aal.project_id as project_id,
                aal.department_id as department_id,
                aal.task_id as task_id,
                NULL as sheet_id,
                aal.so_line as so_line,
                aal.user_total_id as user_total_id,
                aal.invoiced as invoiced,
                aal.invoiceable as invoiceable,
                aal.month_id as month_id,
                aal.week_id as week_id,
                aal.account_department_id as account_department_id,
                aal.expenses as expenses,
                aal.chargeable as chargeable,
                aal.operating_unit_id as operating_unit_id,
                aal.project_operating_unit_id as project_operating_unit_id,
                aal.correction_charge as correction_charge,
                aal.write_off_move as write_off_move,              
                aal.id as ref_id,
                aal.actual_qty as actual_qty,
                aal.planned_qty as planned_qty,
                aal.planned as planned,
                aal.select_week_id as select_week_id,
                0 as kilometers,
                'open' as state,
                CASE
                  WHEN ip.invoice_mileage IS NULL THEN true
                  ELSE ip.invoice_mileage
                END AS non_invoiceable_mileage,
                %(km)s as product_uom_id      
        FROM
         account_analytic_line aal
         LEFT JOIN project_project pp 
         ON pp.id = aal.project_id
         LEFT JOIN project_invoicing_properties ip
         ON ip.id = pp.invoice_properties
         RIGHT JOIN hr_timesheet_sheet_sheet hss
         ON hss.id = aal.sheet_id
        WHERE hss.id = %(sheet)s
        AND aal.ref_id IS NULL
        AND aal.kilometers > 0       
        ;"""
        km_id = self.env.ref('product.product_uom_km').id
        heden = str(fields.Datetime.to_string(fields.datetime.now()))
        self.env.cr.execute(query, {'create': heden,'km': km_id, 'sheet':self.id})
        self.env.invalidate_all()
        return True

    @api.one
    def action_timesheet_done(self):
        """
        On timesheet confirmed update analytic state to confirmed
        :return: Super
        """
        res = super(HrTimesheetSheet, self).action_timesheet_done()
        if self.timesheet_ids:
            cond = '='
            rec = self.timesheet_ids.ids[0]
            if len(self.timesheet_ids) > 1:
                cond = 'IN'
                rec = tuple(self.timesheet_ids.ids)
            self.env.cr.execute("""
                        UPDATE account_analytic_line SET state = 'open' WHERE id %s %s
                """ % (cond, rec))
        return res

    @api.one
    def action_timesheet_draft(self):
        """
        On timesheet reset draft check analytic shouldn't be in invoiced
        :return: Super
        """
        if self.timesheet_ids.filtered('invoiced') or any([ts.state == 'progress' for ts in self.timesheet_ids]):
            raise UserError(_('You cannot modify timesheet entries either Invoiced or belongs to Analytic Invoiced!'))
        res = super(HrTimesheetSheet, self).action_timesheet_draft()
        if self.timesheet_ids:
            cond = '='
            rec = self.timesheet_ids.ids[0]
            if len(self.timesheet_ids) > 1:
                cond = 'IN'
                rec = tuple(self.timesheet_ids.ids)
            self.env.cr.execute("""
                            UPDATE account_analytic_line SET state = 'draft', invoiceable = false WHERE id %s %s;
                            DELETE FROM account_analytic_line WHERE ref_id %s %s;
                    """ % (cond, rec, cond, rec))
            self.env.invalidate_all()
        return res