# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError

class AnalyticLineStatus(models.TransientModel):
    _name = "analytic.line.status"
    _description = "Analytic line Status"

    name = fields.Selection([
        ('invoiceable', 'To be invoiced'),
        ('delayed', 'Delayed'),
        ('write-off', 'Write-Off'),
        ('open', 'Confirmed')
    ], string='Lines to be')
    wip = fields.Boolean("WIP")
    wip_percentage = fields.Float("WIP Percentage")
    description = fields.Char("Description")

    @api.one
    def analytic_invoice_lines(self):
        context = self.env.context.copy()
        analytic_ids = context.get('active_ids',[])
        analytic_lines = self.env['account.analytic.line'].browse(analytic_ids)
        status = str(self.name)
        not_lookup_states = ['draft','progress', 'invoiced', 'delayed', 'change-chargecode']
        entries = analytic_lines.filtered(lambda a: a.invoiced != True and a.state not in not_lookup_states)
        if entries:
            cond, rec = ("IN", tuple(entries.ids)) if len(entries) > 1 else ("=", entries.id)
            invoiceable = True if status == 'invoiceable' else False
            self.env.cr.execute("""
                UPDATE account_analytic_line SET state = '%s', invoiceable = %s WHERE id %s %s
                """ % (status, invoiceable, cond, rec))
            if status == 'delayed' and self.wip_percentage > 0.0:
                self.prepare_account_move()
            if status == 'invoiceable':
                self._prepare_analytic_invoice(entries)

        return True


    def _prepare_analytic_invoice(self, entries):

        analytic_invoice = self.env['analytic.invoice']
        cond, rec = ("in", tuple(entries.ids)) if len(entries) > 1 else ("=", entries.id)

        sep_entries = self.env['account.analytic.line'].search([('id', cond, rec), '|', ('project_id.invoice_properties.group_invoice', '=', False),('task_id.project_id.invoice_properties.group_invoice', '=', False)])
        if sep_entries:
            rec = list(set(entries.ids)-set(sep_entries.ids))
            cond, rec = ("IN", tuple(rec)) if len(rec) > 1 else ("=", rec and rec[0] or [])
        if rec:
            self.env.cr.execute("""
                SELECT array_agg(account_id), partner_id, month_id, project_operating_unit_id
                FROM account_analytic_line
                WHERE id %s %s
                GROUP BY partner_id, month_id, project_operating_unit_id"""
                % (cond, rec))

            result = self.env.cr.fetchall()
            for res in result:
                analytic_account_ids = res[0]
                partner_id = res[1]
                month_id = res[2]
                project_operating_unit_id = res[3]
                search_domain = [('partner_id', '=', partner_id), ('account_analytic_ids', 'in', analytic_account_ids), ('project_operating_unit_id', '=', project_operating_unit_id), ('state', '!=', 'invoiced'), ('month_id', '=', month_id), ('link_project', '=', False)]
                analytic_invobj = analytic_invoice.search(search_domain, limit=1)
                if analytic_invobj:
                    ctx = self.env.context.copy()
                    ctx.update({'active_invoice_id': analytic_invobj.id})
                    analytic_invobj.with_context(ctx).partner_id = partner_id
                    # analytic_invobj.with_context(ctx).month_id = month_id
                    # analytic_invobj.with_context(ctx).project_operating_unit_id = project_operating_unit_id
                else:
                    analytic_invoice.create({'partner_id':partner_id, 'month_id':month_id, 'project_operating_unit_id':project_operating_unit_id})

        if sep_entries:
            cond1, rec1 = ("IN", tuple(sep_entries.ids)) if len(sep_entries) > 1 else ("=", sep_entries.id)
            self.env.cr.execute("""
                SELECT array_agg(account_id), partner_id, month_id, project_operating_unit_id, project_id
                FROM account_analytic_line
                WHERE id %s %s
                GROUP BY partner_id, month_id, project_operating_unit_id, project_id"""
                        % (cond1, rec1))

            result1 = self.env.cr.fetchall()
            for res in result1:
                analytic_account_ids = res[0]
                partner_id = res[1]
                month_id = res[2]
                project_operating_unit_id = res[3]
                project_id = res[4]

                search_domain = [('partner_id', '=', partner_id), ('account_analytic_ids', 'in', analytic_account_ids), ('project_operating_unit_id', '=', project_operating_unit_id), ('state', '!=', 'invoiced'), ('month_id', '=', month_id), ('project_id', '=', project_id), ('link_project', '=', True)]

                analytic_invobj = analytic_invoice.search(search_domain, limit=1)
                if analytic_invobj:
                    ctx = self.env.context.copy()
                    ctx.update({'active_invoice_id': analytic_invobj.id})
                    analytic_invobj.with_context(ctx).partner_id = partner_id
                    # analytic_invobj.with_context(ctx).month_id = month_id
                    # analytic_invobj.with_context(ctx).project_operating_unit_id = project_operating_unit_id
                    # analytic_invobj.with_context(ctx).project_id = project_id
                else:
                    analytic_invoice.create({'partner_id':partner_id, 'month_id':month_id, 'project_operating_unit_id':project_operating_unit_id, 'project_id':project_id, 'link_project': True})
                # analytic_invoice.create(
                #     {'partner_id': entries.partner_id, 'month_id': entries.month_id, 'project_operating_unit_id': entries.project_operating_unit_id, 'project_id':})


    @api.onchange('wip_percentage')
    def onchange_wip_percentage(self):
        if self.wip and self.wip_percentage < 0:
            warning = {'title': _('Warning'),
                       'message': _('Percentage can\'t be negative!')}
            return {'warning': warning, 'value':{'wip_percentage': 0}}

    @api.model
    def _calculate_fee_rate(self, line):
        amount = line.get_fee_rate()
        if self.wip and self.wip_percentage > 0:
            amount = amount - (amount * (self.wip_percentage / 100))
        return amount

    @api.model
    def _prepare_move_line(self, line):
        res = []
        if line.unit_amount == 0:
            return res

        analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.account_id.tag_ids]
        amount = self._calculate_fee_rate(line)

        move_line_debit = {
            'date_maturity': line.date,
            'partner_id': line.partner_id.id,
            'name': line.name,
            'debit': amount,
            'credit': 0.0,
            'account_id': line.partner_id.property_account_receivable_id.id,
            'currency_id': line.currency_id.id,
            'quantity': line.unit_amount,
            'product_id': line.product_id.id,
            'product_uom_id': line.product_uom_id.id,
            'analytic_account_id': line.account_id.id,
            'analytic_tag_ids': analytic_tag_ids,
            'operating_unit_id': line.project_operating_unit_id and line.project_operating_unit_id.id or False,
        }

        res.append(move_line_debit)

        move_line_credit = move_line_debit.copy()
        move_line_credit.update({'debit':0.0, 'credit':amount, 'account_id':line.product_id.property_account_wip_id.id,'operating_unit_id': line.operating_unit_id and line.operating_unit_id.id or False})
        res.append(move_line_credit)

        return res

    @api.multi
    def prepare_account_move(self):
        """ Creates analytics related financial move lines """

        acc_analytic_line = self.env['account.analytic.line']
        account_move = self.env['account.move']

        analytic_lines_ids = self.env.context.get('active_ids', [])

        fields_grouped = [
            'id',
            'partner_id',
            'operating_unit_id',
            'company_id',
        ]
        grouped_by = [
            'partner_id',
            'operating_unit_id',
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

        if len(result) > 0:
            wip_journal = self.env.ref('magnus_invoicing.wip_journal')
            if not wip_journal.sequence_id:
                raise UserError(_('Please define sequence on the type WIP journal.'))

            for item in result:
                partner_id = item['partner_id'][0]
                operating_unit_id = item['operating_unit_id'][0]
                company_id = item['company_id'][0]

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
                    'date': datetime.now().date(),
                    'narration': 'WIP move',
                    'to_be_reversed': True,
                }

                ctx = dict(self._context, lang=partner.lang)
                ctx['company_id'] = company_id
                ctx_nolang = ctx.copy()
                ctx_nolang.pop('lang', None)
                move_id = account_move.with_context(ctx_nolang).create(move_vals)

                cond = '='
                rec = analytic_line_obj.ids[0]
                if len(analytic_line_obj) > 1:
                    cond = 'IN'
                    rec = tuple(analytic_line_obj.ids)
                self.env.cr.execute("""
                        UPDATE account_analytic_line SET write_off_move = %s WHERE id %s %s
                """ % (move_id.id, cond, rec))

        return True
