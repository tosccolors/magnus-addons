.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

===========================
NMBRs Employee Interface
===========================
This module provides an employee interface between Odoo and NMBRs. When using this module, an option on the
employee wizard is added such that the created employee is created in NMBRs as well, preserving the employee number
on both sides. In this version, only the creation of employees is supported. Changes in employee data should still
be taken care of manually on both sides.

Features
========
* A Boolean on employee wizard that asks for insertion of the employee in NMBRs. If the user ticks the box, several fields appear needed for the employee creation in NMBRs. Note that the data sent to NMBRs consists of those fields as well as other fields of the wizard (bank account, email, ..).
* Technically, the employee will be created in Odoo first. Subsequently, the employee is created in NMBRs and then the ID that NMBRs returns is saved on the employee in Odoo as well, to provide future communications between NMBRs and Odoo.
* A mapping table to map nationalities from Odoo to NMBRs.
* **Note**: Changes made in the employee data in Odoo are not automatically syncronized with NMBRs.

Configuration
=============
* The only part of this module that requires configuration is the nationality mapping, which can be found under ``NMBRS`` in the top ribbon. The IDs for NMBRs can be found on https://support.nmbrs.nl/hc/nl/articles/204052856-Code-nationaliteiten-nationaliteitencodes.

Security
========
* The nationality mapping is only available for users in the authorisation group NMBRs employee interface
