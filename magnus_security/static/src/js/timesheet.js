odoo.define('magnus_security.sheet', function (require) {
    'use strict';

    var core = require('web.core');
    var session = require('web.session');
    var magnus_timesheet = require('magnus_timesheet.sheet');

    core.form_custom_registry.get('weekly_timesheet').include({

        go_to_task: function(event) {
            var hasAccess = this.check_user_groups();
            if (hasAccess) {
                var id = JSON.parse($(event.target).data('id'));
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: 'project.task',
                    res_id: id,
                    views: [[false, 'form']],
                    target: 'current',
                });
            }
        },

        go_to: function(event) {
            var hasAccess = this.check_user_groups();
            if (hasAccess) {
                var id = JSON.parse($(event.target).data('id'));
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: 'project.project',
                    res_id: id,
                    views: [[false, 'form']],
                });
            }
        },

        check_user_groups: function () {
            var hr_manager = false;
            var hr_officer = false;
            session.user_has_group('hr.group_hr_manager').then(function(has_group) {
                if(has_group) {
                    hr_manager = true;
                } else {
                    hr_manager = false;
                }
            });

            session.user_has_group('hr.group_hr_user').then(function(has_group) {
                if(has_group) {
                    hr_officer = true;
                } else {
                    hr_officer = false;
                }
            });
            if (hr_manager || hr_officer) {
                return true;
            }
            else {
                return false;
            }
            return false;
        },

    });
});