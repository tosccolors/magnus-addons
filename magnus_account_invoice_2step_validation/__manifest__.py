# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013 - 2018 Magnus - Willem Hulshof - www.magnus.nl
#
#
##############################################################################

{
    'name' : 'magnus_account_invoice_2step_validation',
    'version' : '0.9',
    'category': 'accounts',
    'description': """
This module adds authorization steps in workflow in magnus supplier invoices.
=============================================================================

Enchanced to add
* Authorization
* Verification status on the Invoice

    """,
    'author'  : 'TOSC - Willem Hulshof',
    'website' : 'http://www.tosc.nl',
    'depends' : ['account_invoice_2step_validation',
    ],
    'data' : [
        "views/account_move_view.xml",
    ],
    'demo' : [],
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

