from odoo import api, fields, models
import math


class AccountAsset(models.Model):
	_inherit = 'account.asset'

	# book_value = fields.Float(compute='_compute_book_value', method=True, digits=0, string='Book Value')
	#
	# @api.depends('salvage_value', 'value_residual')
	# def _compute_book_value(self):
	#     self.book_value = self.salvage_value + self.value_residual

	equipment_ids = fields.Many2many(
		comodel_name="maintenance.equipment", string="Equipments"
	)
	equipment_count = fields.Integer(
		string="Equipment count", compute="_compute_equipment_count"
	)

	@api.depends('equipment_ids')
	def _compute_equipment_count(self):
		for asset in self:
			asset.equipment_count = len(asset.equipment_ids)


	def button_open_equipment(self):
		self.ensure_one()
		res = self.env.ref('maintenance.hr_equipment_action').read()[0]
		res['domain'] = [('asset_ids', 'in', self.ids)]
		res['context'] = {'default_asset_ids': [(6, 0, self.ids)]}
		return res

	# Hayo Bos: This function is to create equipments (equal to the qty specified in the line). The equipments are
	# automatically linked to the just created asset.
	@api.model
	def create(self, vals):
		res = super(AccountAsset, self).create(vals)
		ctx = self._context
		if "create_asset_from_move_line" in ctx and res.profile_id.has_equipments:
			for invoice_line_nr in range(len(ctx["invoice"].invoice_line_ids)):
				line = ctx["invoice"].invoice_line_ids[invoice_line_nr]
				equipment_qty = math.ceil(line.quantity)
				equipments = self.env['maintenance.equipment']
				for equipment_nr in range(int(equipment_qty)):
					equipment_data = {
						'name': "{} [{}/{}]".format(line.name, equipment_nr + 1, equipment_qty),
						'category_id': (
							line.asset_profile_id.equipment_category_id.id
						),
						'invoice_line_id': line.id,
						'cost': line.price_subtotal / line.quantity,
						'partner_id': line.invoice_id.partner_id.id,
						'owner_user_id': line.user_id.id,
						'purchase_date': line.invoice_id.date_invoice
					}
					equipments += equipments.create(equipment_data)
				res.write({'equipment_ids': [(4, x) for x in equipments.ids]})
		return res
