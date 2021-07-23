.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

===========================
Fleet RDW Add on
===========================
This module provides a simple RDW add on for the fleet module. Using the license plate, the relevant information is fetched from the Open Data RDW Database.

Features
========
* A button ``Fetch RDW Data`` on a vehicle. When the license plate is entered, one can click the button to fetch all relevant data from the RDW Open Data Database.

Configuration
=============
* This module does not require any configuration.

Security
========
* The authorisation group RDW API Rights is added, providing rights to click the ``Fetch data from rdw`` button, and to create the necessary ``vehicle.from.rdw`` model
