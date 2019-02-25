# -*- coding: utf-8 -*-
# Copyright 2014-2018 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=method-required-super
import logging
import collections
from odoo import _, api, fields, models

# Register relations
RELATIONS_SQL_M = """\
SELECT
    (rel.id * %%(padding)s) + %(key_offset)s AS id,
    'res.partner.relation' AS res_model,
    rel.id AS res_id,
    rel.left_partner_id AS this_partner_id,
    rel.right_partner_id AS other_partner_id,
    rel.type_id,
    rel.date_start,
    rel.date_end,
    rel.distribution_key,
    %(is_inverse)s as is_inverse
FROM res_partner_relation rel"""

# Register inverse relations
RELATIONS_SQL_INVERSE_M = """\
SELECT
    (rel.id * %%(padding)s) + %(key_offset)s AS id,
    'res.partner.relation',
    rel.id,
    rel.right_partner_id,
    rel.left_partner_id,
    rel.type_id,
    rel.date_start,
    rel.date_end,
    rel.distribution_key,
    %(is_inverse)s as is_inverse
FROM res_partner_relation rel"""


class ResPartnerRelationAll(models.AbstractModel):
    """Abstract model to show each relation from two sides."""
    _inherit = 'res.partner.relation.all'

    distribution_key = fields.Float(
        string='Percentage Distribution Key'
    )

    def get_register(self):
        register = collections.OrderedDict()
        register['_lastkey'] = -1
        self.register_specification(
            register, 'relation', False, RELATIONS_SQL_M)
        self.register_specification(
            register, 'relation', True, RELATIONS_SQL_INVERSE_M)
        return register
