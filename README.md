openerp-freeswitch-connector
============================

While this file now documents much of this module, the documentation found at
http://www.akretion.com/open-source-contributions/openerp-asterisk-voip-connector
may continue to hold useful information.

This is no longer simply a fork. It has many added features over that of the
original.

Currently working:
 * Click to Dial for customers, events, employees and applicants. ("Dial" next
   to phone numbers.)
 * "Open Caller" (An "A" next to preferences) will open Partners, Events,
   Employees, Applicants for jobs, etc. (This works differently than before by
   opening the record directly.)
 * Pop-up on in coming call, when configured. See README.md under
   patches-for-external for caveats. Also, editing may appear to work, but it
   does not!
 * Looking up Caller ID name by phone number works for Events, CRM,
   Employees, and Applicants.

It also only works (or at least is only tested) with OpenERP 7.

I will be doing the following over the next short while:
* Adding my copyright
* Adding documentation and updating comments to better reflect changes and how
  to use it
* Add click to dial every other place it makes sense


Configuring
===========

Your account to administer the settings for this module will need access to "Technical Features". This user may also need "Portal" access so that the menu options will show up.

Next, go to Settings > Technical > Telephony > FreeSWITCH Servers. Edit or create a new entry. You will want it to be active. Next, set the IP address or fully qualified DNS name for the FreeSWITCH server. The IP address, or IP addresses that the DNS name resolve to, must be setup with FreeSWITCH as listening for event socket connections. Next, set the port. This is the port that FreeSWITCH is configured to listen on. Finally, set the password to that which FreeSWITCH is setup to use for inbound event socket connections. Dial Plan context is the context you want any call placed by OpenERP to start in. Out Prefix is any prefix needed to get an outside line, if any; e.g. many PBXes in the USA use 9 to get an outside line. Alert-Info SIP Header is the header sent to SIP phones to set a ring tone. This can be used to make the ringing made by the phone when it is called by FreeSWITCH before dialing the called person quiet or silent. Wait Time in seconds is how long the call should continue without being answered (auto terminate after this many seconds).

For caller ID name lookup and pop-up notifications, you will need to create a user, e.g. FreeSWITCH, in OpenERP. This user only needs rights to "Phone CallerID." You will need to know this user's id (number, not name) to do XML-RPC to do look up and pop-up functionality along with the user's password.

For each user you use to use this for, you will need to setup options in the Telephony tab for the user. You can choose if pop-up notifications are active and if CRM claim call functionality is enabled. Channel Type is likely FreeTDM or SIP, although it may be something else (untested by me). Resource name is the resource to go with that channel type. For example, if it is FreeTDM and the user is port 5 in span 1, then the resource is 1/5. If the user has the internal number of 2005 in the SIP directory, then the resource is likely 2005. Internal number is the number of the user when dialed from inside the PBX/SoftSWITCH. Caller ID is what should be set as the caller ID name and number when making a call with the click to dial functionality. This must be in the format of Name &lt;number&gt;; e.g. Administrator &lt;01234567&gt;.

CDR Account is not attached at the moment. User-specific Dial Suffix is attached, but does it do anything or work? User-specific Alert-Info SIP Header overrides the server setting for the ring tone. User-specific Variable is any SIP header(s) you want to add. If there are multiple variables, separate them with pipe (|).

You will need to use the Settings > Technical > Telephony > Reformat Phone Numbers wizard if you have phone numbers that are not in the appropriate international format (this will be done for you in the future if you have the right _phone modules installed). WARNING: Be aware that if you do not have the country for your company/companies set properly, this will not do what you want. You will be sorry. You have been warned!


Caller ID and Pop-up on Call
============================

Please, see freeswitch_click2dial/scripts/get_caller_name.py. The script is documented.
I do not recommend that you use the geolocation code as it will make things too slow.


Using The Features
==================

* You should install base_phone no matter what. This handles formatting.
* base_phone_popup allows you to have FreeSWITCH pop-up information about the
  caller in active OpenERP sessions.
* All modules ending in _phone do phone number formatting/validation for lookup
  and storing for the module by the same name. If you use the module in
  question, install the _phone module. The hr_recruitment_phone module also
  does some fix-ups to make sure the right fields are returned for caller ID
  lookups.
* crm_claim_phone allows the user to claim a phone call with the partner.

Any place where modules exist to do click to dial, there will appear "Dial" (possibly translated) next to the phone number, click the dial and your phone will be called (if things are configured correctly), then FreeSWITCH will call the remote party after you answer your phone.

When a call is inbound (you do not have to have answered it, only caller ID information needs to be received), then click the A ("Open Caller") next to Preferences. This will open the appropriate record. If there is no call, nothing will happen.


Dependencies
============
See README.md under patches-for-external

Also, you will need the FreeSWITCH ESL python module. You will find it under ${FREESWITCH_SRC_TOP_DIR}/libs/esl/python. Go to ${FREESWITCH_SRC_TOP_DIR}/libs/esl. Type make. Then make pymod. You will then need to install ${FREESWITCH_SRC_TOP_DIR}/libs/esl/python/ESL.py and ${FREESWITCH_SRC_TOP_DIR}/libs/esl/python/_ESL.so into the appropriate places on your OpenERP/Odoo server. (https://wiki.freeswitch.org/wiki/Event_Socket_Library#Installation for more information.) An alternative method would involve https://github.com/gurteshwar/freeswitch-esl-python.
