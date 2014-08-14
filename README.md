openerp-freeswitch-connector
============================

Currently this is simply a fork of http://www.akretion.com/open-source-contributions/openerp-asterisk-voip-connector

Currently working:
 * Click to Dial for customers, events, employees and applicants.
 * Open calling partner under Sales.

It also only works (or at least is only tested) with OpenERP 7.

I will be doing the following over the next short while:
* Adding my copyright
* Adding documentation and updating comments to better reflect changes and how to use it
* Add click to dial every other place it makes sense
* Work on fetching the names for caller_id (this is about 90% done but not completed as I haven't decided on the right way to go about this)
* Use web_action_request and web_notification modules to open the right pages automatically. This should be mostly working, but I can't get web_action_notify to work at all.
