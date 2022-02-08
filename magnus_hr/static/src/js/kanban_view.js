odoo.define('magnus_hr.KanbanView', function (require) {
"use strict";

    var KanbanView = require('web_kanban.KanbanView');
    // web_kanban.KanbanView
    var Model = require('web.Model');

    var KanbanView = KanbanView.include({
        render_buttons: function($node) {

            // GET BUTTON REFERENCE
            this._super($node);
            if (this.$buttons) {
                var add_emp_btn = this.$buttons.find('.add_employee_wizard');
                 // PERFORM THE ACTION
                add_emp_btn.on('click', this.proxy('do_add_employee_wizard'));
            }
        },
        do_add_employee_wizard: function() {
            return this.do_action({
                type: 'ir.actions.act_window',
                name: 'Create Employee',
                res_model: 'hr.employee.wizard',
                view_type: 'form',
                view_mode: 'form',
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
    });
});

