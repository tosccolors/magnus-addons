# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID
import time
import logging

logger = logging.getLogger(__name__)

def post_init_hook(cr, pool):
    """
    This post-init-hook will update only date.range
    calender_name values in case they are not set
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    for month in env['date.range'].search([('type_id.fiscal_month', '=', True)]):
        month.calender_name = time.strftime('%B', time.strptime(month.date_start, '%Y-%m-%d'))

    for month in env['date.range'].search([('type_id.fiscal_year', '=', True)]):
        month.calender_name = time.strftime('%Y', time.strptime(month.date_start, '%Y-%m-%d'))
