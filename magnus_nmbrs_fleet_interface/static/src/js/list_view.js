odoo.define('magnus_nmbrs_fleet_interface.ListView', function (require) {
"use strict";


    var ListView = require('web.ListView');
    var Model = require('web.Model');


    var ListView = ListView.include({
        render_buttons: function($node) {

            // GET BUTTON REFERENCE
            this._super($node);
            if (this.$buttons) {
                var fetch_nmbrs_fleet_btn = this.$buttons.find('.add_fetch_nmbrs_fleet_btn');
                 // PERFORM THE ACTION
                fetch_nmbrs_fleet_btn.on('click', this.proxy('do_add_fetch_nmbrs_fleet_btn'));
            }
        },
        do_add_fetch_nmbrs_fleet_btn: function() {
            return this.do_action({
                type: 'ir.actions.act_window',
                name: 'Fetch Fleet Changes for NMBRs',
                res_model: 'nmbrs.fleet.get.changes.wizard',
                view_type: 'form',
                view_mode: 'form',
                target: 'new',
                views: [[false, 'form']],
                context: {'default_add': true},
            });
        },
    });
});

