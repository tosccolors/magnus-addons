.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

===========================
NMBRs Interface Base Module
===========================

This module provides the base module for the interfaces between Odoo and NMBRs. All NMBRs interfaces depend on
module, as it provides the underlying, shared functionalities for the separate interfaces. This module itself is not an
interface.

Features
========
* A configuration view ``top ribbon --> NMBRS``, where an authorised user can provide her / his username and API token
* A mapping table to map analytic accounts between NMBRs and Odoo
* Addition of an ID field on the operating unit object

Configuration
=============
* To configure the API credentials, go to ``NMBRS`` in the top ribbon. The API token should be copied from NMBRs,  see https://support.nmbrs.nl/hc/nl/articles/115003926251-Nmbrs-koppelen-via-een-API-token.
* The API user should have sufficient rights in NMBRs, which can be configured using a user template, see https://support.nmbrs.nl/hc/nl/articles/115005903907-API-User-Template.
* NMBRs has a special "sandbox" environment, which is a copy from the production database. This copy is refreshed every 24 hours. To use the sandbox, the endpoint should be api-sandbox.nmbrs.nl instead of api.nmbrs.nl. By default, the sandbox endpoints are configured.
* Technical API documentation can be found here: https://api.nmbrs.nl/soap/v3/.

Security
========
* The configuration menu is only available for users in the authorisation group NMBRs Interface Configuration
