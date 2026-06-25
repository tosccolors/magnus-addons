# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Magnus customization for timesheet",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Magnus customization for timesheet",
    "author": "The Open Source Company",
    "website": "http://www.tosc.nl",
    "category": "module_category_specific_industry_applications",
    "depends": [
        "ps_timesheet_invoicing",
        "ps_timesheet_lunch",
    ],
    "installable": True,
    "data": [
        "views/hr_timesheet_sheet.xml",
        "views/ps_time_line.xml",
    ],
}
