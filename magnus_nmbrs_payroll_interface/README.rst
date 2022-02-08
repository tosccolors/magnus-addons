.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

===========================
NMBRs Payroll Interface
===========================
This module provides the payroll interface between Odoo and NMBRs. Using this interface, payroll journal entries can directly
be loaded into Odoo, without the need for Excel imports and exports.

Features
========
* A new menu under Finance called "Payroll", where payroll related functionalities can be found.
* A submenu called payroll runs, where one load the run information from NMBRs.
* A submenu called payroll journal entries where one can load the journal entries from NMBRs to Odoo.
* A mapping table in the NMBRS menu in the top ribbon, where analytic accounts from NMBRs can be mapped to analytic accounts in Odoo.

Configuration
=============
* A mapping between Odoo analytic accounts and NMBRs analytic accounts is required to load journal entries.
* Before loading a journal entry, first load payroll runs.
* Moves are created in "draft" state. It could be necessary to change the "policy for analytic accounts" to always for **posted** moves (``Finance --> Configuration --> Account Types``). This is especially the case when not all analytic accounts in NMBRs are present or map to an analytic account in Odoo.

Security
========
* Only users in authorisation group ``NMBRs Payroll Interface`` can view this modules' menus, and create and edit this module's objects.