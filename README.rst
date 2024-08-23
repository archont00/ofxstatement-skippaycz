This is a parser for CSV credit card transaction history exported from Skip Pay s.r.o. (Czech Republic)
from the web app (Purchases: filter the transactions as needed and export as CSV).

The expected field separator is semicolumn (";") and character encoding UTF-8.

It is a plugin for `ofxstatement`_.

.. _ofxstatement: https://github.com/kedder/ofxstatement

Usage
=====
::

  $ ofxstatement convert -t skippaycz:CC MP_mesicni_platby_22082024.csv MP_mesicni_platby_22082024.ofx

Configuration
=============
::

  $ ofxstatement edit-config

and set e.g. the following:
::

  [skippaycz:CC]
  plugin = skippaycz
  currency = CZK
  account = Skip Pay CC
  account_type = CREDITLINE

Issues
======

Feel free to create GitHub pull request for any updates or corrections.
