##############################################################################
#
# Copyright 2016 KPMG Advisory N.V. (unless otherwise stated)
#
# Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
##############################################################################
from resource_management import *
from resource_management.core.system import System
import os
import random
import string
import socket
import kavecommon as kc

config = Script.get_config()

hostname = config["hostname"]
nagios_admin_password = default('configurations/nagios/nagios_admin_password', 'nagiosadmin')
nagios_admin_email = default('configurations/nagios/nagios_admin_email', 'dna@kpmglab.com')
nagios_conf_file = default('configurations/nagios/nagios_conf_file', """ SAMPLE CONFIG SNIPPETS FOR APACHE WEB SERVER
#
# This file contains examples of entries that need
# to be incorporated into your Apache web server
# configuration file.  Customize the paths, etc. as
# needed to fit your system.

ScriptAlias /nagios/cgi-bin/ "/usr/lib64/nagios/cgi-bin/"

<Directory "/usr/lib64/nagios/cgi-bin/">
#  SSLRequireSSL
   Options ExecCGI
   AllowOverride None

   AuthName "Nagios Access"
   AuthType Basic
   AuthUserFile /etc/nagios/passwd

   <IfModule mod_authz_core.c>
      # Apache 2.4
      <RequireAll>
         Require all granted
         # Require local
         Require valid-user
      </RequireAll>
   </IfModule>
   <IfModule !mod_authz_core.c>
      # Apache 2.2
      Order allow,deny
      Allow from all
      #  Order deny,allow
      #  Deny from all
      #  Allow from 127.0.0.1
      Require valid-user
   </IfModule>
</Directory>

Alias /nagios "/usr/share/nagios/html"

<Directory "/usr/share/nagios/html">
#  SSLRequireSSL
   Options None
   AllowOverride None

   AuthName "Nagios Access"
   AuthType Basic
   AuthUserFile /etc/nagios/passwd

   <IfModule mod_authz_core.c>
      # Apache 2.4
      <RequireAll>
         Require all granted
         # Require local
         Require valid-user
      </RequireAll>
   </IfModule>
   <IfModule !mod_authz_core.c>
      # Apache 2.2
      Order allow,deny
      Allow from all
      #  Order deny,allow
      #  Deny from all
      #  Allow from 127.0.0.1
      Require valid-user
   </IfModule>
</Directory>""")
nagios_contacts_file = default('configurations/nagios/nagios_contacts_file', """##############################################################################
# CONTACTS.CFG - SAMPLE CONTACT/CONTACTGROUP DEFINITIONS
#
#
# NOTES: This config file provides you with some example contact and contact
#        group definitions that you can reference in host and service
#        definitions.
#
#        You don't need to keep these definitions in a separate file from your
#        other object definitions.  This has been done just to make things
#        easier to understand.
#
###############################################################################



###############################################################################
###############################################################################
#
# CONTACTS
#
###############################################################################
###############################################################################

# Just one contact defined by default - the Nagios admin (that's you)
# This contact definition inherits a lot of default values from the 'generic-contact'
# template which is defined elsewhere.

define contact{
        contact_name                    nagiosadmin             ; Short name of user
        use                             generic-contact         ; Inherit
        default values from generic-contact template (defined above)
        alias                           Nagios Admin            ; Full name of user

        email                           {{nagios_admin_email}}        ; Email Address
        }



###############################################################################
###############################################################################
#
# CONTACT GROUPS
#
###############################################################################
###############################################################################

# We only have one contact in this simple configuration file, so there is
# no need to create more than one contact group.

define contactgroup{
        contactgroup_name       admins
        alias                   Nagios Administrators
        members                 nagiosadmin
        }""")
