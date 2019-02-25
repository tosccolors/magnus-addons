# -*- coding: utf-8 -*-
# Copyright 2013-2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=api-one-deprecated
"""Store relations (connections) between partners."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartnerRelationExtension(models.Model):
    """Model res.partner.relation.extension is used to extend relations
    between partners in the database.

    This model is actually only used to store the data. The model
    res.partner.relation.all, based on a view that contains each record
    two times, once for the normal relation, once for the inverse relation,
    will be used to maintain the data.
    """
    _name = 'res.partner.relation.extension'
    _inherits = {'res.partner.relation': "relation_id"}

    relation_id = fields.Many2one(
        'res.partner.relation',
        string='Partner Multi Relation',
        ondelete="cascade",
        required=True,
        auto_join=True
    )
    distribution_key = fields.Float(
        string='Percentage Distribution Key'
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