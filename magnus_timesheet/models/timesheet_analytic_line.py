# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# Copyright 2018-2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class TimesheetAnalyticLine(models.Model):
    _name = 'timesheet.analytic.line'

    
    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    name = fields.Char('Description', required=True)
    date = fields.Date('Date', required=True, index=True, default=fields.Date.context_today)
    amount = fields.Monetary('Amount', required=True, default=0.0)
    unit_amount = fields.Float('Quantity', default=0.0)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True, store=True, compute_sudo=True)
    user_id = fields.Many2one('res.users', string='User', default=_default_user)

    # planning_analytic_id = fields.Many2one(
    #     comodel_name='magnus.planning',
    #     string='Planning id',
    # )
    week_id = fields.Many2one('date.range',string="Week",compute='compute_week_id',store=True)

    @api.depends('date')
    def compute_week_id(self):
        for line in self:
            if line.date:
                week_id = self.env['date.range'].search([('date_start','=',line.date)])
                if week_id:
                    line.week_id = week_id.id

    planning_sheet_id = fields.Many2one(
        comodel_name='magnus.planning',
        string='Sheet',
    )
    # planning_sheet_state = fields.Selection(
    #     string='Sheet State',
    #     related='planning_sheet_id.state',
    # )

    employee_id = fields.Many2one('hr.employee',string="Employee")
    project_id = fields.Many2one('project.project',string="Project")
    account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    def merge_timesheets(self):
        unit_amount = sum(
            [t.unit_amount for t in self])
        amount = sum([t.amount for t in self])
        self[0].write({
            'unit_amount': unit_amount,
            'amount': amount,
        })
        self[1:].unlink()
        return self[0]

    @api.model
    def _planning_create(self, values):
        return self.with_context(planning_create=True).create(values)

    @api.constrains('company_id', 'account_id')
    def _check_company_id(self):
        for line in self:
            if line.account_id.company_id and line.company_id.id != line.account_id.company_id.id:
                raise ValidationError(_('The selected account belongs to another company that the one you\'re trying to create an analytic item for'))

