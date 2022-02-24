odoo.define('magnus_nmbrs_base.ListView', function (require) {
"use strict";


    var ListView = require('web.ListView');
    var Model = require('web.Model');


    var ListView = ListView.include({
        render_buttons: function($node) {

            // GET BUTTON REFERENCE
            this._super($node);
            if (this.$buttons) {
                var fetch_nmbrs_analytic_accounts_btn = this.$buttons.find('.add_fetch_nmbrs_analytic_accounts');
                 // PERFORM THE ACTION
                fetch_nmbrs_analytic_accounts_btn.on('click', this.proxy('do_add_fetch_nmbrs_analytic_accounts'));
            }
        },
        do_add_fetch_nmbrs_analytic_accounts: function() {
            return this.do_action({
                type: 'ir.actions.act_window',
                name: 'Fetch Analytic Accounts NMBRs',
                res_model: 'nmbrs.analytic.account.wizard',
                view_type: 'form',
                view_mode: 'form',
                target: 'new',
                views: [[false, 'form']],
                context: {'default_add': true},
            });
        },
    });
});

