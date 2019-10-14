# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.queue_job.exception import FailedJobError
import logging
_logger = logging.getLogger(__name__)

class AnalyticLineStatus(models.TransientModel):
    _name = "analytic.line.status"
    _description = "Analytic line Status"

    name = fields.Selection([
        ('invoiceable', 'To be invoiced'),
        ('delayed', 'Delayed'),
        ('write-off', 'Write-Off'),
        ('open', 'Confirmed')
    ], string='Lines to be'
    )
    wip = fields.Boolean(
        "WIP"
    )
    wip_percentage = fields.Float(
        "WIP Percentage",
        default=100,
    )
    description = fields.Char(
        "Description"
    )

    def validate_entries_month(self, analytic_ids):
        fields_grouped = [
            'id',
            'month_id',
            'company_id',
        ]
        grouped_by = [
            'month_id',
            'company_id',
        ]
        result = self.env['account.analytic.line'].read_group(
            [('id', 'in', analytic_ids)],
            fields_grouped,
            grouped_by,
            offset=0,
            limit=None,
            orderby=False,
            lazy=False
        )
        if len(result) > 1:
            raise ValidationError(
                _("Entries must belong to same month!"))
        return True

    @api.one
    def analytic_invoice_lines(self):
        context = self.env.context.copy()
        analytic_ids = context.get('active_ids',[])
        analytic_lines = self.env['account.analytic.line'].browse(analytic_ids)
        status = str(self.name)
        not_lookup_states = ['draft','progress', 'invoiced', 'delayed', 'write-off','change-chargecode']

        entries = analytic_lines.filtered(lambda a: a.state not in not_lookup_states)

        no_invoicing_property_entries = entries.filtered(lambda al: not al.project_id.invoice_properties)
        if no_invoicing_property_entries and status == 'invoiceable':
            project_names = ','.join([al.project_id.name for al in no_invoicing_property_entries])
            raise UserError(_(
                'Project(s) %s doesn\'t have invoicing properties.'
                )%project_names)

        if entries:
            cond, rec = ("IN", tuple(entries.ids)) if len(entries) > 1 else ("=", entries.id)
            self.env.cr.execute("""
                UPDATE account_analytic_line SET state = '%s' WHERE id %s %s
                """ % (status, cond, rec))
            self.env.invalidate_all()
            if status == 'delayed' and self.wip and self.wip_percentage > 0.0:
                self.validate_entries_month(analytic_ids)
                # self.with_delay(eta=datetime.now(), description="WIP Posting").prepare_account_move(analytic_ids)
                self.prepare_account_move(analytic_ids)
            if status == 'invoiceable':
                self.with_context(active_ids=entries.ids).prepare_analytic_invoice()
        return True


    def prepare_analytic_invoice(self):
        def analytic_invoice_create(result, link_project):
            for res in result:
                project_id = False
                analytic_account_ids = res[0]
                partner_id = res[1]
                partner = self.env['res.partner'].browse(partner_id)
                month_id = res[2]
                project_operating_unit_id = res[3]

                if link_project:
                    project_id = res[4]
                    partner_id = self.env['project.project'].browse(project_id).invoice_address.id

                search_domain = [
                    ('partner_id', '=', partner_id),
                    ('account_analytic_ids', 'in', analytic_account_ids),
                    ('project_operating_unit_id', '=', project_operating_unit_id),
                    ('state', 'not in', ('invoiced', 're_confirmed')),
                    ('month_id', '=', month_id)]
                if link_project:
                    search_domain += [('project_id', '=', project_id)]
                    search_domain += [('link_project', '=', True)]
                else:
                    search_domain += [('link_project', '=', False)]

                analytic_invobj = analytic_invoice.search(search_domain, limit=1)
                if analytic_invobj:
                    ctx = self.env.context.copy()
                    ctx.update({'active_invoice_id': analytic_invobj.id})
                    analytic_invobj.with_context(ctx).partner_id = partner_id
                    # analytic_invobj.with_context(ctx).month_id = month_id
                    # analytic_invobj.with_context(ctx).project_operating_unit_id = project_operating_unit_id
                else:
                    data = {
                        'partner_id': partner_id,
                        'type': 'out_invoice',
                        'account_id': partner.property_account_receivable_id.id,
                        'month_id':month_id,
                        'project_operating_unit_id':project_operating_unit_id,
                        'operating_unit_id': project_operating_unit_id,
                        'link_project': False,
                        'payment_term_id': partner.property_payment_term_id.id or False,
                        'journal_id': self.env['account.invoice'].default_get(['journal_id'])['journal_id'],
                        'fiscal_position_id': partner.property_account_position_id.id or False,
                        'user_id': self.env.user.id,
                        'company_id': self.env.user.company_id.id,
                        'date_invoice': datetime.now().date(),
                    }
                    if link_project:
                        data.update({'project_id': project_id, 'link_project': True})
                    analytic_invoice.create(data)


        context = self.env.context.copy()
        entries_ids = context.get('active_ids', [])
        if len(self.env['account.analytic.line'].browse(entries_ids).filtered(lambda a: a.state != 'invoiceable')) > 0:
            raise UserError(_('Please select only Analytic Lines with state "To Be Invoiced".'))

        analytic_invoice = self.env['analytic.invoice']
        cond, rec = ("in", tuple(entries_ids)) if len(entries_ids) > 1 else ("=", entries_ids[0])

        sep_entries = self.env['account.analytic.line'].search([
            ('id', cond, rec),
            '|',
            ('project_id.invoice_properties.group_invoice', '=', False),
            ('task_id.project_id.invoice_properties.group_invoice', '=', False)
        ])
        if sep_entries:
            rec = list(set(entries_ids)-set(sep_entries.ids))
            cond, rec = ("IN", tuple(rec)) if len(rec) > 1 else ("=", rec and rec[0] or [])
        if rec:
            self.env.cr.execute("""
                SELECT array_agg(account_id), partner_id, month_id, project_operating_unit_id
                FROM account_analytic_line
                WHERE id %s %s AND date_of_last_wip IS NULL 
                GROUP BY partner_id, month_id, project_operating_unit_id"""
                % (cond, rec))

            result = self.env.cr.fetchall()
            analytic_invoice_create(result, False)

            #reconfirmed seperate entries
            self.env.cr.execute("""
                            SELECT array_agg(account_id), partner_id, month_of_last_wip, project_operating_unit_id
                            FROM account_analytic_line
                            WHERE id %s %s AND date_of_last_wip IS NOT NULL AND month_of_last_wip IS NOT NULL 
                            GROUP BY partner_id, month_of_last_wip, project_operating_unit_id"""
                                % (cond, rec))

            reconfirm_res = self.env.cr.fetchall()
            analytic_invoice_create(reconfirm_res, False)

        if sep_entries:
            cond1, rec1 = ("IN", tuple(sep_entries.ids)) if len(sep_entries) > 1 else ("=", sep_entries.id)
            self.env.cr.execute("""
                SELECT array_agg(account_id), partner_id, month_id, project_operating_unit_id, project_id
                FROM account_analytic_line
                WHERE id %s %s AND date_of_last_wip IS NULL
                GROUP BY partner_id, month_id, project_operating_unit_id, project_id"""
                        % (cond1, rec1))

            result1 = self.env.cr.fetchall()
            analytic_invoice_create(result1, True)

            # reconfirmed grouping entries
            self.env.cr.execute("""
                            SELECT array_agg(account_id), partner_id, month_of_last_wip, project_operating_unit_id, project_id
                            FROM account_analytic_line
                            WHERE id %s %s AND date_of_last_wip IS NOT NULL AND month_of_last_wip IS NOT NULL 
                            GROUP BY partner_id, month_of_last_wip, project_operating_unit_id, project_id"""
                                % (cond1, rec1))

            reconfirm_res1 = self.env.cr.fetchall()
            analytic_invoice_create(reconfirm_res1, True)


    @api.onchange('wip_percentage')
    def onchange_wip_percentage(self):
        if self.wip and self.wip_percentage < 0:
            warning = {'title': _('Warning'),
                       'message': _('Percentage can\'t be negative!')}
            return {'warning': warning, 'value':{'wip_percentage': 0}}

    @api.model
    def _calculate_fee_rate(self, line):
        amount = line.get_fee_rate_amount(False, False)
        if self.wip and self.wip_percentage > 0:
            amount = amount - (amount * (self.wip_percentage / 100))
        return amount

    @api.model
    def _prepare_move_line(self, line):
        res = []
        if line.unit_amount == 0:
            return res

        analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.account_id.tag_ids]
        amount = abs(self._calculate_fee_rate(line))

        move_line_debit = {
            'date_maturity': line.date,
            'partner_id': line.partner_id.id,
            'name': line.name,
            'debit': amount,
            'credit': 0.0,
            ## todo also the category properties
            'account_id': line.product_id.property_account_wip_id.id,
            'currency_id': line.currency_id.id,
            'quantity': line.unit_amount,
            'product_id': line.product_id.id,
            'product_uom_id': line.product_uom_id.id,
            'analytic_account_id': line.account_id.id,
            'analytic_tag_ids': analytic_tag_ids,
            'operating_unit_id': line.operating_unit_id and line.operating_unit_id.id or False,
            'user_id': line.user_id and line.user_id.id or False
        }

        res.append(move_line_debit)

        move_line_credit = move_line_debit.copy()
        move_line_credit.update({
            'debit': 0.0,
            'credit': amount,
            ## todo also the category properties
            'account_id': line.product_id.property_account_income_id.id,
        })
        res.append(move_line_credit)
        return res

    # @job
    @api.multi
    def prepare_account_move(self, analytic_lines_ids):
        """ Creates analytics related financial move lines """

        acc_analytic_line = self.env['account.analytic.line']
        account_move = self.env['account.move']


        fields_grouped = [
            'id',
            'partner_id',
            'operating_unit_id',
            'month_id',
            'company_id',
        ]
        grouped_by = [
            'partner_id',
            'operating_unit_id',
            'month_id',
            'company_id',
        ]

        result = acc_analytic_line.read_group(
            [('id','in', analytic_lines_ids)],
            fields_grouped,
            grouped_by,
            offset=0,
            limit=None,
            orderby=False,
            lazy=False
        )
        narration = self.description if self.wip else ''
        try:
            if len(result) > 0:
                wip_journal = self.env.ref('magnus_invoicing.wip_journal')
                if not wip_journal.sequence_id:
                    raise UserError(_('Please define sequence on the type WIP journal.'))
                for item in result:
                    partner_id = item['partner_id'][0]
                    operating_unit_id = item['operating_unit_id'][0]
                    month_id = item['month_id'][0]
                    company_id = item['company_id'][0]

                    date_end = self.env['date.range'].browse(month_id).date_end

                    partner = self.env['res.partner'].browse(partner_id)
                    if not partner.property_account_receivable_id:
                        raise UserError(_('Please define receivable account for partner %s.') % (partner.name))

                    aml = []
                    analytic_line_obj = acc_analytic_line.search([('id', 'in', analytic_lines_ids),('partner_id', '=', partner_id),('operating_unit_id', '=', operating_unit_id)])
                    for aal in analytic_line_obj:
                        if not aal.product_id.property_account_wip_id:
                            raise UserError(_('Please define WIP account for product %s.') % (aal.product_id.name))
                        for ml in self._prepare_move_line(aal):
                            aml.append(ml)

                    line = [(0, 0, l) for l in aml]

                    move_vals = {
                        'type':'receivable',
                        'ref': narration,
                        'line_ids': line,
                        'journal_id': wip_journal.id,
                        'date': date_end,
                        'narration': 'WIP move',
                        'to_be_reversed': True,
                    }

                    ctx = dict(self._context, lang=partner.lang)
                    ctx['company_id'] = company_id
                    ctx_nolang = ctx.copy()
                    ctx_nolang.pop('lang', None)
                    move = account_move.with_context(ctx_nolang).create(move_vals)
                    if move:
                        move._post_validate()
                        move.post()

                    account_move |= move

                    cond = '='
                    rec = analytic_line_obj.ids[0]
                    if len(analytic_line_obj) > 1:
                        cond = 'IN'
                        rec = tuple(analytic_line_obj.ids)

                    wip_month_id = analytic_line_obj[0].find_daterange_month(datetime.now().strftime("%Y-%m-%d"))

                    line_query = ("""
                                    UPDATE
                                       account_analytic_line
                                    SET date_of_last_wip = CURRENT_DATE, month_of_last_wip = {0}
                                    WHERE id {1} {2}
                                    """.format(
                        wip_month_id.id or False, cond, rec))

                    self.env.cr.execute(line_query)

        except Exception, e:
            raise FailedJobError(
                _("The details of the error:'%s'") % (unicode(e)))

        # self.with_delay(eta=datetime.now(), description="WIP Reversal").wip_reversal(account_move)
        self.wip_reversal(account_move)

        return "WIP moves successfully created. Reversal will be processed in separate jobs.\n "

    # @job
    @api.multi
    def wip_reversal(self, moves):
        for move in moves:
            try:
                date = datetime.strptime(move.date, "%Y-%m-%d") + timedelta(days=1)
                move.create_reversals(
                    date=date, journal=move.journal_id,
                    move_prefix='WIP Reverse', line_prefix='WIP Reverse',
                    reconcile=False)
            except Exception, e:
                raise FailedJobError(
                    _("The details of the error:'%s'") % (unicode(e)))
        return "WIP Reversal moves successfully created.\n "
