# -*- encoding: utf-8 -*-
##############################################################################
#
#    FreeSWITCH click2dial HR Recruitment module for OpenERP
#    Copyright (C) 2014 Trever L. Adams
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

{
    "name": "FreeSWITCH Click2dial HR Recruitment",
    "version": "0.1",
    "author": "Trever L. Adams",
    "website": "",
    "license": "AGPL-3",
    "category": "Phone",
    "description": """
    This module adds a button "Dial" button on the Recruitment Application Form

    A detailed documentation for the OpenERP-FreeSWITCH connector is available on the site : http://github.com/treveradams/openerp-freeswitch-connector
    """,
    "depends": [
        'freeswitch_click2dial',
        'hr_recruitment_phone',
    ],
    "demo": [],
    "data": [
        'wizard/open_calling_partner_view.xml',
        'hr_recruitment_view.xml',
    ],
    "installable": True,
    "application": True,
}
