odoo.define('magnus_fleet.KanbanView', function (require) {
"use strict";

    var KanbanView = require('web_kanban.KanbanView');
    // web_kanban.KanbanView
    var Model = require('web.Model');

    var KanbanView = KanbanView.include({
        render_buttons: function($node) {

            // GET BUTTON REFERENCE
            this._super($node);
            if (this.$buttons) {
                var add_driver_btn = this.$buttons.find('.add_driver');
                var remove_driver_btn = this.$buttons.find('.remove_driver');
                 // PERFORM THE ACTION
                add_driver_btn.on('click', this.proxy('do_add_driver_button'));
                remove_driver_btn.on('click', this.proxy('do_remove_driver_button'));
            }
        },
        do_add_driver_button: function() {
            return this.do_action({
                type: 'ir.actions.act_window',
                name: 'Add Driver',
                res_model: 'fleet.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                target: 'new',
                views: [[false, 'form']],
                context: {'default_add': true},
            });
            // return new Model('fleet.vehicle').call('add_driver', [[]])
            //     .done(function(result) {
            //
            //         console.log(result);
            //         location.reload(true);
            //     });
        },
        do_remove_driver_button: function() {
            return this.do_action({
                type: 'ir.actions.act_window',
                name: 'Remove Driver',
                res_model: 'fleet.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                target: 'new',
                views: [[false, 'form']],
                context: {'default_add': false},
            });
            // new Model('fleet.vehicle').call('remove_driver', [[]])
            //     .done(function(result) {
            //         console.log(result);
            //         location.reload(true);
            //     });
        }

    });
});