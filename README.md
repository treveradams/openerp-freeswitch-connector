openerp-freeswitch-connector
============================

For now, you should refer to the documentation at
http://www.akretion.com/open-source-contributions/openerp-asterisk-voip-connector

This is no longer simply a fork. It has many added features over that of the
original.

Currently working:
 * Click to Dial for customers, events, employees and applicants.
 * "Open calling partner" under Sales.
 * "Open calling applicant" under Human Resources/Recruitment
 * Pop-up on incoming call, when configured. See README.md under
   patches-for-external for caveats. Also, editing may appear to work, but it
   does not!
 * Looking up Caller ID name by phone number works for Events, CRM,
   and Employees. It does NOT work for applicants. It returns the subject
   instead! (This is a bug, I hope to fix it soon.)

It also only works (or at least is only tested) with OpenERP 7.

I will be doing the following over the next short while:
* Adding my copyright
* Adding documentation and updating comments to better reflect changes and how
  to use it
* Add click to dial every other place it makes sense


Caller ID and Pop-up on Call
============================

Please, see freeswitch_click2dial/scripts/set_name_agi.py around lines 265-276
for example python code for XML-RPC to get caller ID and do pop-up
notification. Note, causing the pop-up also fetches caller ID information.

Getting geolocation data is implemented in an uncommitted script. I am not sure
about the design. 99% of the code should be usable no matter what I decide.
The question is whether my script should be a wsgi script which runs on the
FreeSWITCH server or the OpenERP server, or an event socket script that runs on
the FreeSWITCH server.
