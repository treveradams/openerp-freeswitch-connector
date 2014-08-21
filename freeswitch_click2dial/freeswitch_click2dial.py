# -*- encoding: utf-8 -*-
##############################################################################
#
#    FreeSWITCH Click2dial module for OpenERP
#    Copyright (C) 2014 Trever L. Adams
#    Copyright (C) 2010-2013 Alexis de Lattre <alexis@via.ecp.fr>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm
from openerp.tools.translate import _
import logging
# Lib for phone number reformating -> pip install phonenumbers
import phonenumbers
# Lib py-freeswitch from http://code.google.com/p/py-freeswitch/
# We need a version which has this commit : http://code.google.com/p/py-freeswitch/source/detail?r=8d0e1c941cce727c702582f3c9fcd49beb4eeaa4
# so a version after Nov 20th, 2012
import ESL
import sys
import csv
import StringIO
import re
#import pprint
#pp = pprint.PrettyPrinter(indent=4,stream=sys.stderr)

_logger = logging.getLogger(__name__)

class freeswitch_server(orm.Model):
    '''FreeSWITCH server object, to store all the parameters of the FreeSWITCH IPBXs'''
    _name = "freeswitch.server"
    _description = "FreeSWITCH Servers"
    _columns = {
        'name': fields.char('FreeSWITCH server name', size=50, required=True, help="FreeSWITCH server name."),
        'active': fields.boolean('Active', help="The active field allows you to hide the FreeSWITCH server without deleting it."),
        'ip_address': fields.char('FreeSWITCH IP addr. or DNS', size=50, required=True, help="IP address or DNS name of the FreeSWITCH server."),
        'port': fields.integer('Port', required=True, help="TCP port on which the FreeSWITCH Manager Interface listens. Defined in /usr/local/freeswitch/conf/autoload_configs/event_socket.conf.xml on FreeSWITCH."),
        'out_prefix': fields.char('Out prefix', size=4, help="Prefix to dial to place outgoing calls. If you don't use a prefix to place outgoing calls, leave empty."),
        'national_prefix': fields.char('National prefix', size=4, help="Prefix for national phone calls (don't include the 'out prefix'). For e.g., in France, the phone numbers look like '01 41 98 12 42' : the National prefix is '0'."),
        'international_prefix': fields.char('International prefix', required=True, size=4, help="Prefix to add to make international phone calls (don't include the 'out prefix'). For e.g., in France, the International prefix is '00'."),
        'country_prefix': fields.char('My country prefix', required=True, size=4, help="Phone prefix of the country where the FreeSWITCH server is located. For e.g. the phone prefix for France is '33'. If the phone number to dial starts with the 'My country prefix', OpenERP will remove the country prefix from the phone number and add the 'out prefix' followed by the 'national prefix'. If the phone number to dial doesn't start with the 'My country prefix', OpenERP will add the 'out prefix' followed by the 'international prefix'."),
        'password': fields.char('Event Socket password', size=30, required=True, help="Password that OpenERP will use to communicate with the FreeSWITCH Manager Interface. Refer to /usr/local/freeswitch/conf/autoload_configs/event_socket.conf.xml on your FreeSWITCH server."),
        'context': fields.char('Dialplan context', size=50, required=True, help="FreeSWITCH dialplan context from which the calls will be made; e.g. 'XML default'. Refer to /usr/local/freeswitch/conf/dialplan/* on your FreeSWITCH server."),
        'wait_time': fields.integer('Wait time (sec)', required=True, help="Amount of time (in seconds) FreeSWITCH will try to reach the user's phone before hanging up."),
        'alert_info': fields.char('Alert-Info SIP header', size=255, help="Set Alert-Info header in SIP request to user's IP Phone for the click2dial feature. If empty, the Alert-Info header will not be added. You can use it to have a special ring tone for click2dial (a silent one !) or to activate auto-answer for example."),
        'company_id': fields.many2one('res.company', 'Company', help="Company who uses the FreeSWITCH server."),
    }

    def _get_prefix_from_country(self, cr, uid, context=None):
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        country_code = user.company_id and user.company_id.partner_id and user.company_id.partner_id.country_id and user.company_id.partner_id.country_id.code or False
        default_country_prefix = False
        if country_code:
            default_country_prefix = phonenumbers.country_code_for_region(country_code)
        return default_country_prefix

    _defaults = {
        'active': True,
        'port': 8021,  # Default Event Socket port
        'national_prefix': '1',
        'international_prefix': '011',
        'country_prefix': _get_prefix_from_country,
        'context': 'XML default',
        'wait_time': 60,
        'company_id': lambda self, cr, uid, context: self.pool.get('res.company')._company_default_get(cr, uid, 'freeswitch.server', context=context),
    }

    def _check_validity(self, cr, uid, ids):
        for server in self.browse(cr, uid, ids):
            country_prefix = ('Country prefix', server.country_prefix)
            international_prefix = ('International prefix', server.international_prefix)
            out_prefix = ('Out prefix', server.out_prefix)
            national_prefix = ('National prefix', server.national_prefix)
            dialplan_context = ('Dialplan context', server.context)
            alert_info = ('Alert-Info SIP header', server.alert_info)
            password = ('Event Socket password', server.password)

            for digit_prefix in [country_prefix, international_prefix, out_prefix, national_prefix]:
                if digit_prefix[1] and not digit_prefix[1].isdigit():
                    raise orm.except_orm(_('Error :'), _("Only use digits for the '%s' on the FreeSWITCH server '%s'" % (digit_prefix[0], server.name)))
            if server.wait_time < 1 or server.wait_time > 120:
                raise orm.except_orm(_('Error :'), _("You should set a 'Wait time' value between 1 and 120 seconds for the FreeSWITCH server '%s'" % server.name))
            if server.port > 65535 or server.port < 1:
                raise orm.except_orm(_('Error :'), _("You should set a TCP port between 1 and 65535 for the FreeSWITCH server '%s'" % server.name))
            for check_string in [dialplan_context, alert_info, password]:
                if check_string[1]:
                    try:
                        string = check_string[1].encode('ascii')
                    except UnicodeEncodeError:
                        raise orm.except_orm(_('Error :'), _("The '%s' should only have ASCII caracters for the FreeSWITCH server '%s'" % (check_string[0], server.name)))
        return True


    _constraints = [
        (_check_validity, "Error message in raise", ['out_prefix', 'country_prefix', 'national_prefix', 'international_prefix', 'wait_time', 'port', 'context', 'alert_info', 'password']),
    ]


    def _reformat_number(self, cr, uid, erp_number, fs_server, context=None):
        '''
        This function is dedicated to the transformation of the number
        available in OpenERP to the number that FreeSWITCH should dial.
        You may have to inherit this function in another module specific
        for your company if you are not happy with the way I reformat
        the OpenERP numbers.
        '''

        error_title_msg = _("Invalid phone number")
        invalid_international_format_msg = _("The phone number is not written in valid international format. Example of valid international format : +33 1 41 98 12 42")
        invalid_national_format_msg = _("The phone number is not written in valid national format.")
        invalid_format_msg = _("The phone number is not written in valid format.")

        # Let's call the variable tmp_number now
        tmp_number = erp_number
        _logger.debug('Number before reformat = %s' % tmp_number)

        # Check if empty
        if not tmp_number:
            raise orm.except_orm(error_title_msg, invalid_format_msg)

        # Before starting to use prefix, we convert empty prefix whose value
        # is False to an empty string
        country_prefix = fs_server.country_prefix or ''
        national_prefix = fs_server.national_prefix or ''
        international_prefix = fs_server.international_prefix or ''
        out_prefix = fs_server.out_prefix or ''

        # Maybe one day we will use
        # phonenumbers.format_out_of_country_calling_number(phonenumbers.parse('<phone_number_e164', None), 'FR')
        # The country code seems to be OK with the ones of OpenERP
        # But it returns sometimes numbers with '-'... we have to investigate this first
        # International format
        if tmp_number[0] != '+':
            raise # This should never happen
        # Remove the starting '+' of the number
        tmp_number = tmp_number.replace('+','')
        _logger.debug('Number after removal of special char = %s' % tmp_number)

        # At this stage, 'tmp_number' should only contain digits
        if not tmp_number.isdigit():
            raise orm.except_orm(error_title_msg, invalid_format_msg)

        _logger.debug('Country prefix = %s' % country_prefix)
        if country_prefix == tmp_number[0:len(country_prefix)]:
            # If the number is a national number,
            # remove 'my country prefix' and add 'national prefix'
            tmp_number = (national_prefix) + tmp_number[len(country_prefix):len(tmp_number)]
            _logger.debug('National prefix = %s - Number with national prefix = %s' % (national_prefix, tmp_number))

        else:
            # If the number is an international number,
            # add 'international prefix'
            tmp_number = international_prefix + tmp_number
            _logger.debug('International prefix = %s - Number with international prefix = %s' % (international_prefix, tmp_number))

        # Add 'out prefix' to all numbers
        tmp_number = out_prefix + tmp_number
        _logger.debug('Out prefix = %s - Number to be sent to FreeSWITCH = %s' % (out_prefix, tmp_number))
        return tmp_number


    # TODO : one day, we will use phonenumbers.format_out_of_country_calling_number() ?
    # if yes, then we can trash the fields international_prefix, national_prefix
    # country_prefix and this kind of code
    def _convert_number_to_international_format(self, cr, uid, number, fs_server, context=None):
        '''Convert the number presented by the phone network to a number
        in international format e.g. +33141981242'''
        if number and number.isdigit() and len(number) > 5:
            if fs_server.international_prefix and number[0:len(fs_server.international_prefix)] == fs_server.international_prefix:
                number = number[len(fs_server.international_prefix):]
                number = '+' + number
            elif fs_server.national_prefix and number[0:len(fs_server.national_prefix)] == fs_server.national_prefix:
                number = number[len(fs_server.national_prefix):]
                number = '+' + fs_server.country_prefix + number
        return number


    def _get_freeswitch_server_from_user(self, cr, uid, context=None):
        '''Returns an freeswitch.server browse object'''
        # We check if the user has an FreeSWITCH server configured
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        if user.freeswitch_server_id.id:
            fs_server = user.freeswitch_server_id
        else:
            freeswitch_server_ids = self.search(cr, uid, [('company_id', '=', user.company_id.id)], context=context)
        # If no freeswitch server is configured on the user, we take the first one
            if not freeswitch_server_ids:
                raise orm.except_orm(_('Error :'), _("No FreeSWITCH server configured for the company '%s'.") % user.company_id.name)
            else:
                fs_server = self.browse(cr, uid, freeswitch_server_ids[0], context=context)
        servers = self.pool.get('freeswitch.server')
        server_ids = servers.search(cr, uid, [('id', '=', fs_server.id)], context=context)
        fake_fs_server = servers.browse(cr, uid, server_ids, context=context)
        for rec in fake_fs_server:
             fs_server = rec
             break
        return fs_server


    def _connect_to_freeswitch(self, cr, uid, context=None):
        '''
        Open the connection to the FreeSWITCH Manager
        Returns an instance of the FreeSWITCH Manager

        '''
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)

        # Note : if I write 'Error' without ' :', it won't get translated...
        # I don't understand why !

        fs_server = self._get_freeswitch_server_from_user(cr, uid, context=context)
        # We check if the current user has a chan type
        if not user.freeswitch_chan_type:
            raise orm.except_orm(_('Error :'), _('No channel type configured for the current user.'))

        # We check if the current user has an internal number
        if not user.resource:
            raise orm.except_orm(_('Error :'), _('No resource name configured for the current user'))


        _logger.debug("User's phone : %s/%s" % (user.freeswitch_chan_type, user.resource))
        _logger.debug("FreeSWITCH server = %s:%d" % (fs_server.ip_address, fs_server.port))

        # Connect to the FreeSWITCH Manager Interface
        try:
            fs_manager = ESL.ESLconnection(str(fs_server.ip_address), str(fs_server.port), str(fs_server.password))
        except Exception, e:
            _logger.error("Error in the Originate request to FreeSWITCH server %s" % fs_server.ip_address)
#            _logger.error("Here is the detail of the error : %s" % e.strerror)
#            raise orm.except_orm(_('Error :'), _("Problem in the request from OpenERP to FreeSWITCH. Here is the detail of the error: %s." % e.strerror))
            return (False, False, False)

        return (user, fs_server, fs_manager)

    def _dial_with_freeswitch(self, cr, uid, erp_number, context=None):
        #print "_dial_with_freeswitch erp_number=", erp_number
        if not erp_number:
            raise orm.except_orm(_('Error :'), "Hara kiri : you must call the function with erp_number")

        user, fs_server, fs_manager = self._connect_to_freeswitch(cr, uid, context=context)
        fs_number = self._reformat_number(cr, uid, erp_number, fs_server, context=context)

        # The user should have a CallerID
        if not user.callerid:
            raise orm.except_orm(_('Error :'), _('No callerID configured for the current user'))

        variable = ""
        if user.freeswitch_chan_type == 'SIP':
            # We can only have one alert-info header in a SIP request
            if user.alert_info:
                variable += 'alert_info=' + user.alert_info
            elif fs_server.alert_info:
                variable += 'alert_info=' + fs_server.alert_info
        if user.variable:
            for user_variable in user.variable.split('|'):
                if len(variable) and len(user_variable):
                    variable += ','
                variable += user_variable.strip()
        if user.callerid:
            caller_name = re.search(r'([^<]*).*', user.callerid).group(1).strip()
            caller_number = re.search(r'.*<(.*)>.*', user.callerid).group(1).strip()
            if caller_name:
                if len(variable):
                    variable += ','
                caller_name = caller_name.replace(",", "\,")
                variable += 'effective_caller_id_name=' + caller_name
            if caller_number:
                if len(variable):
                    variable += ','
                variable += 'effective_caller_id_number=' + caller_number
            if fs_server.wait_time != 60:
                if len(variable):
                    variable += ','
                variable += 'ignore_early_media=true' + ','
                variable += 'originate_timeout=' + str(fs_server.wait_time)

        try:
            # api originate <effective_caller_id_number=1234,originate_timeout=7,call_timeout=7>user/2005 1005 XML Internal-FXS 'Caller ID showed to OpenERP user' 90125
#            fs_manager.Originate(
#                user.freeswitch_chan_type + '/' + user.resource + ( ('/' + user.dial_suffix) if user.dial_suffix else ''),
#                ...
#                account = user.cdraccount,
#                variable = variable)
             dial_string = (('<' + variable + '>') if variable else '') + user.freeswitch_chan_type + '/' + user.resource + ( ('/' + user.dial_suffix) if user.dial_suffix else '') + ' ' + fs_number + ' ' + fs_server.context + ' ' + fs_number + ' ' + fs_number
             fs_manager.api('originate', dial_string.encode("ascii"))
        except Exception, e:
            _logger.error("Error in the Originate request to FreeSWITCH server %s" % fs_server.ip_address)
            _logger.error("Here is the detail of the error : '%s'" % unicode(e))
            raise orm.except_orm(_('Error :'), _("Click to dial with FreeSWITCH failed.\nHere is the error: '%s'" % unicode(e)))

        finally:
            fs_manager.disconnect()

        return True

    def _get_calling_number(self, cr, uid, context=None):

        user, fs_server, fs_manager = self._connect_to_freeswitch(cr, uid, context=context)
        calling_party_number = False
        try:
            ret = fs_manager.api('show', "calls as delim | like callee_cid_num " + str(user.internal_number))
            f = StringIO.StringIO(ret.getBody())
            reader = csv.DictReader(f, delimiter='|')
            reader.next()
            for row in reader:
                if not row["uuid"] or row["uuid"] == "":
                    break
                if row["callstate"] not in ["EARLY","ACTIVE","RINGING"]:
                    continue
                if row["b_cid_num"] and row["b_cid_num"] != None:
                    calling_party_number = row["b_cid_num"]
                elif row["cid_num"] and row["cid_num"] != None:
                    calling_party_number = row["cid_num"]
        except Exception, e:
            _logger.error("Error in the Status request to FreeSWITCH server %s" % fs_server.ip_address)
            _logger.error("Here is the detail of the error : '%s'" % unicode(e))
            raise orm.except_orm(_('Error :'), _("Can't get calling number from  FreeSWITCH.\nHere is the error: '%s'" % unicode(e)))

        finally:
            fs_manager.disconnect()

        _logger.debug("The calling party number is '%s'" % calling_party_number)

        return calling_party_number



# Parameters specific for each user
class res_users(orm.Model):
    _inherit = "res.users"

    _columns = {
        'internal_number': fields.char('Internal number', size=15,
            help="User's internal phone number."),
        'dial_suffix': fields.char('User-specific dial suffix', size=15,
            help="User-specific dial suffix such as aa=2wb for SCCP auto answer."),
        'callerid': fields.char('Caller ID', size=50,
            help="Caller ID used for the calls initiated by this user."),
        # You'd probably think : FreeSWITCH should reuse the callerID of sip.conf !
        # But it cannot, cf http://lists.digium.com/pipermail/freeswitch-users/2012-January/269787.html
        'cdraccount': fields.char('CDR Account', size=50,
            help="Call Detail Record (CDR) account used for billing this user."),
        'freeswitch_chan_type': fields.selection([
            ('user', 'SIP'),
            ('FreeTDM', 'FreeTDM'),
            ('Skinny', 'Skinny'),
            ('MGCP', 'MGCP'),
            ('mISDN', 'mISDN'),
            ('H323', 'H323'),
            ('SCCP', 'SCCP'),
            ('Local', 'Local'),
            ], 'FreeSWITCH channel type',
            help="FreeSWITCH channel type, as used in the FreeSWITCH dialplan. If the user has a regular IP phone, the channel type is 'SIP'."),
        'resource': fields.char('Resource name', size=64,
            help="Resource name for the channel type selected. For example, if you use 'Dial(SIP/phone1)' in your FreeSWITCH dialplan to ring the SIP phone of this user, then the resource name for this user is 'phone1'.  For a SIP phone, the phone number is often used as resource name, but not always."),
        'alert_info': fields.char('User-specific Alert-Info SIP header', size=255, help="Set a user-specific Alert-Info header in SIP request to user's IP Phone for the click2dial feature. If empty, the Alert-Info header will not be added. You can use it to have a special ring tone for click2dial (a silent one !) or to activate auto-answer for example."),
        'variable': fields.char('User-specific Variable', size=255, help="Set a user-specific 'Variable' field in the FreeSWITCH Manager Interface 'originate' request for the click2dial feature. If you want to have several variable headers, separate them with '|'."),
        'freeswitch_server_id': fields.many2one('freeswitch.server', 'FreeSWITCH server',
            help="FreeSWITCH server on which the user's phone is connected. If you leave this field empty, it will use the first FreeSWITCH server of the user's company."),
               }

    _defaults = {
        'freeswitch_chan_type': 'SIP',
    }

    def _check_validity(self, cr, uid, ids):
        for user in self.browse(cr, uid, ids):
            for check_string in [('Resource name', user.resource), ('Internal number', user.internal_number), ('Caller ID', user.callerid)]:
                if check_string[1]:
                    try:
                        plom = check_string[1].encode('ascii')
                    except UnicodeEncodeError:
                        raise orm.except_orm(_('Error :'), _("The '%s' for the user '%s' should only have ASCII caracters" % (check_string[0], user.name)))
        return True

    _constraints = [
        (_check_validity, "Error message in raise", ['resource', 'internal_number', 'callerid']),
    ]


class phone_common(orm.AbstractModel):
    _inherit = 'phone.common'

    def action_dial(self, cr, uid, ids, context=None):
        '''Read the number to dial and call _connect_to_freeswitch the right way'''
        if context is None:
            context = {}
        if not isinstance(context.get('field2dial'), (unicode, str)):
            raise orm.except_orm(_('Error :'), "The function action_dial must be called with a 'field2dial' key in the context containing a string '<phone_field>'.")
        else:
            phone_field = context.get('field2dial')
        erp_number_read = self.read(cr, uid, ids[0], [phone_field], context=context)
        erp_number_e164 = erp_number_read[phone_field]
        # Check if the number to dial is not empty
        if not erp_number_e164:
            raise orm.except_orm(_('Error :'), _('There is no phone number !'))
        return self.pool['freeswitch.server']._dial_with_freeswitch(cr, uid, erp_number_e164, context=context)

    def _prepare_incall_pop_action(
            self, cr, uid, record_res, number, context=None):
        # Not executed because this module doesn't depend on base_phone_popup
        # TODO move to a dedicated module freeswitch_popup ?
        action = super(phone_common, self)._prepare_incall_pop_action(
            cr, uid, record_res, number, context=context)
        if not action:
            action = {
                'name': _('No Partner Found'),
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.open.calling.partner',
                'view_mode': 'form',
                'views': [[False, 'form']],  # Beurk, but needed
                'target': 'new',
                'context': {'incall_number_popup': number}
            }
        return action
