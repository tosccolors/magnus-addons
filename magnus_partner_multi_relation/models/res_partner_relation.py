# -*- coding: utf-8 -*-
# Copyright 2013-2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=api-one-deprecated
"""Store relations (connections) between partners."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp

class ResPartnerRelation(models.Model):
    """Model res.partner.relation is used to store relations
    between partners in the database.

    This model is actually only used to store the data. The model
    res.partner.relation.all, based on a view that contains each record
    two times, once for the normal relation, once for the inverse relation,
    will be used to maintain the data.
    """
    _inherit = 'res.partner.relation'

    distribution_key = fields.Float(
        string='Percentage Distribution Key',
        digits=dp.get_precision('Product Unit of Measure')
    )

    invoicing_property_id = fields.Many2one(
        comodel_name='project.invoicing.properties',
        string='Invoicing Property'
    )

    @api.one
    @api.constrains('distribution_key')
    def _check_distribution_key(self):
        """Check distribution_key for valid values

        :raises ValidationError: When constraint is violated
        """
        dk = self.distribution_key
        if dk > 100 or dk < 0:
            raise ValidationError(
                _('The percentage can not be greater than 100 '
                  'or smaller than 0.')
            )

    @api.multi
    def name_get(self):
        return [
            (this.id, '%s %s %s' % (
                this.left_partner_id.name,
                this.type_id.display_name,
                this.right_partner_id.name,
            )) for this in self]