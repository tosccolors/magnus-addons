.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

===========================
NMBRs Fleet Interface
===========================
This module provides an interface between NMBRs and Odoo for fleet related changes. This can be useful when employees are
given leasecars, which also have implications for the employees' payslips. Using this interface, fleet changes made in Odoo
can easily be send to NMBRs as well.

Features
========
* A new menu under ``Finance --> Payroll`` where, using a query, a user can retrieve all recent fleet changes.
* In the aforementioned menu, the user can easily select which changes should be send to NMBRs and do so using the new menu action
* If the leasecar is created in Odoo, but is not yet present in NMBRs, then when fleet changes with this car are being sent to NMBRs, the car is automatically created in NMBRs
* Using a mapping table, one can map fiscal addition (bijtelling) from Odoo to NMBRs, from the ``NMBRS`` menu. All information can be found on: https://support.nmbrs.com/hc/en-us/articles/360015523160-Nmbrs-API-enumerations-
* **Note** the RDW API is required for this module

Configuration
=============
* The fiscal addition mapping can be configured under the ``NMBRS`` menu item in the top ribbon. Then go to ``Mapping Fiscal Addition``.
* The NMBRs database ID of the vehicle is stored in Odoo as well, in the field ``nmbrs_id`` on the ``fleet_vehicle`` object.
* **Note** an initial initialization where IDs are loaded from NMBRs to Odoo might be required.

Security
========
* Only users in the authorisation group ``NMBRs Fleet Interface`` can view the recent fleet changes, and send them to NMBRs.