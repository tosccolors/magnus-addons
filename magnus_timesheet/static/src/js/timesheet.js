odoo.define('magnus_timesheet.sheet', function (require) {
    'use strict';

    var core = require('web.core');
    var Model = require('web.DataModel');
    var form_common = require('web.form_common');
    var QWeb = core.qweb;
    var hr_timesheet_task = require('hr_timesheet_task.sheet');

    core.form_custom_registry.get('weekly_timesheet').include({

        init_add_project: function() {
            var self = this;
            if (self.dfm) {
                self.dfm.destroy();
            }

            self.$('.oe_timesheet_weekly_add_row').show();
            self.dfm = new form_common.DefaultFieldManager(self);
            self.dfm.extend_field_desc({
                project: {
                    relation: 'project.project',
                },
                task: {
                    relation: 'project.task',
                },
            });
            var FieldMany2One = core.form_widget_registry.get('many2one');
            self.project_m2o = new FieldMany2One(self.dfm, {
                attrs: {
                    name: 'project',
                    type: 'many2one',
                    modifiers: '{"required": true}',
                    options: '{"no_create_edit":true, "create": false, "no_quick_create": true}'
                },
            });

            self.task_m2o = new FieldMany2One(self.dfm, {
                attrs: {
                    name: 'task',
                    type: 'many2one',
                    domain: [
                        // at this moment, it is always an empty list
                        ['project_id','=',self.project_m2o.get_value()]
                    ],
                    options: '{"no_create_edit":true, "create": false, "no_quick_create": true}'
                },
            });
            self.task_m2o.prependTo(this.$('.o_add_timesheet_line > div'));

            self.project_m2o.prependTo(this.$('.o_add_timesheet_line > div')).then(function() {
                self.project_m2o.$el.addClass('oe_edit_only');
            });

            self.project_m2o.on("change:value", self.project_m2o, function() {
                self.project_m2o.trigger('changed_value');
                self.onchange_project_id();
            });

            // onfocus changes called by on project changed_value
            // self.project_m2o.$input.focusout(function(){
            //     self.onchange_project_id();
            // });

            self.$(".oe_timesheet_button_add").click(function() {
                self.onclick_add_row_button();
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

        display_data: function() {
            var self = this;
            self.$el.html(QWeb.render("hr_timesheet_sheet.WeeklyTimesheet", {widget: self}));
            _.each(self.projects, function(project) {
                _.each(_.range(project.days.length), function(day_count) {
                    if (!self.get('effective_readonly')) {
                        self.get_box(project, day_count).val(self.sum_box(project, day_count, true)).focus(function() {
                            $(this).select();
                        });
                        self.get_box(project, day_count).val(self.sum_box(project, day_count, true)).change(function() {
                            var num = $(this).val();
                            if (self.is_valid_value(num) && num !== 0) {
                                num = Number(self.parse_client(num));
                            }
                            if (isNaN(num)) {
                                $(this).val(self.sum_box(project, day_count, true));
                            } else {
                                project.days[day_count].lines[0].unit_amount += num - self.sum_box(project, day_count);
                                var product = (project.days[day_count].lines[0].product_id instanceof Array) ? project.days[day_count].lines[0].product_id[0] : project.days[day_count].lines[0].product_id;
                                var journal = (project.days[day_count].lines[0].journal_id instanceof Array) ? project.days[day_count].lines[0].journal_id[0] : project.days[day_count].lines[0].journal_id;

                                if(!isNaN($(this).val())){
                                    $(this).val(self.sum_box(project, day_count, true));
                                }

                                self.display_totals();
                                self.sync();
                            }
                        });
                    } else {
                        self.get_box(project, day_count).html(self.sum_box(project, day_count, true));
                    }
                });
            });
            self.display_totals();
            if(!this.get('effective_readonly')) {
                this.init_add_project();
            }
        },

    });
});