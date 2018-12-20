odoo.define('magnus_timesheet.sheet', function (require) {
    'use strict';

    var core = require('web.core');
    var Model = require('web.DataModel');
    var hr_timesheet_task = require('hr_timesheet_task.sheet');

    core.form_custom_registry.get('weekly_timesheet').include({
        init_add_project: function() {
            var self = this;
            this._super(parent);

            self.project_m2o.on("change:value", self.project_m2o, function() {
                self.project_m2o.trigger('changed_value');
                self.onchange_project_id();
            });

            self.$(".oe_timesheet_weekly_input").focusout(function() {
                var elms = document.getElementsByClassName('oe_timesheet_weekly_input');
                for (var i = 0; i < elms.length; i++) {
                    var hour = elms[i].value.slice(0, -3);
                    if (hour > "24" || hour < 0){
                        alert('Logged hours should be 0 to 24.');
                        elms[i].value='0';
                    }
                }
            });
        },

        onchange_project_id: function() {
            var self = this;
            var project_id = self.project_m2o.get_value();

            self.task_m2o.node.attrs.domain = [
                // show only tasks linked to the selected project
                ['project_id','=',project_id],
                // ignore tasks already in the timesheet
                ['id', 'not in', _.pluck(self.projects, 'task')],
            ];

            self.task_m2o.set_value(false);
            var Tasks = new Model('project.task');
            Tasks.query(['id']).filter([["project_id", "=", project_id], ["standard", "=", "True"]]).limit(1).all().then(function (standard_task){
                if (standard_task.length === 1) {
                    self.task_m2o.set_value(standard_task[0].id);
                }
            });
            Tasks.query(['id', 'name']).filter([["project_id", "=", project_id]]).all().then(function (task){
                if (task.length === 1) {
                    self.task_m2o.set_value(task[0].id);
                }
            });

            self.task_m2o.node.attrs.context = {'default_project_id': project_id};
            self.task_m2o.render_value();
        },

    });
});