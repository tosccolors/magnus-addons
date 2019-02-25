# -*- coding: utf-8 -*-
# Copyright 2014-2018 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=method-required-super
import logging
import collections
from odoo import _, api, fields, models


class ResPartnerRelationAll(models.AbstractModel):
    """Abstract model to show each relation from two sides."""
    _inherit = 'res.partner.relation.all'

    distribution_key = fields.Float(
        string='Percentage Distribution Key'
    )


    def _get_additional_view_fields(self):
        """Add distribution_key to view fields."""
        return ','.join([
            super(ResPartnerRelationAll, self)._get_additional_view_fields(),
            " ext.distribution_key as distribution_key"])

    def _get_additional_tables(self):
        """Add res_partner_tab table to view."""
        # pylint: disable=no-member
        return ' '.join([
            super(ResPartnerRelationAll, self)._get_additional_tables(),
            "JOIN res_partner_relation_extension ext"
            " ON bas.id = ext.relation_id"])