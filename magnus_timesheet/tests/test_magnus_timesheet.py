from time import strftime
from dateutil.rrule import WEEKLY
from odoo.tests.common import TransactionCase


class TestMagnusTimesheet(TransactionCase):
    def setUp(self):
        super(TestMagnusTimesheet, self).setUp()
        self.user = self.env.ref('base.user_demo')
        self.user_employee = self.user.employee_ids
        self.user_employee.official_date_of_employment = strftime('%Y-01-06')
        # create weeks for current year
        self.env['date.range.generator'].create({
            'type_id': self.env.ref(
                'magnus_date_range_week.date_range_calender_week'
            ).id,
            'unit_of_time': WEEKLY,
            'name_prefix': 'week-',
            'date_start': strftime('%Y-01-01'),
            'count': 52,
            'duration_count': 1,
        }).action_apply()
        # create vehicle for demo user
        self.vehicle = self.env['fleet.vehicle']
        self.env['data.time.tracker'].create({
            'model': 'fleet.vehicle',
            'relation_model': 'res.partner',
            'relation_ref': self.user.partner_id.id,
            'date_from': strftime('%Y-01-01'),
            'date_to': strftime('%Y-12-31'),
        })
        # TODO: create more users/other records used below

    def test_timesheet_create(self):
        """ Test functions called during create of one timesheet """
        sheet = self.env['hr_timesheet_sheet.sheet'].sudo(
            self.user
        ).create({})
        self.assertTrue(sheet.week_id, 'There should be a week set')
        self.assertEqual(
            sheet.employee_id, self.user.employee_ids,
            'Timesheet should autoselect the user\'s employee',
        )
        # TODO: test more computed fields/defaults

    def test_full_flow(self):
        """ Test the full flow of a sheet from begin to end """
        pass

    def test_actions(self):
        """ Test actions to be run on timesheets """

    # TODO: client side tests
    # TODO: server side form tests
    # (both are horrible to use in v10)
