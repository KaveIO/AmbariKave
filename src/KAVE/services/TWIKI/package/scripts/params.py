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
import kavecommon as kc

config = Script.get_config()

hostname = config["hostname"]

www_folder = default('configurations/twiki/www_folder', '/var/www/html/')
install_dir = www_folder + "twiki/"
PORT = default('configurations/twiki/PORT', '80')
servername = default('configurations/twiki/servername', hostname)
if servername == "hostname":
    servername = hostname
admin_user = default('configurations/twiki/admin_user', 'twiki-admin')

ldap_group = default('configurations/twiki/ldap_group', 'twiki')

known_authentication_methods = ['HBAC', 'LDAP', 'NONE']
authentication_method = default('configurations/twiki/authentication_method', 'HBAC')
authentication_method = authentication_method.upper()
if authentication_method not in known_authentication_methods:
    raise ValueError("Authentication method not recognised, I only know "
                     + str(known_authentication_methods)
                     + " but you asked for " + authentication_method)
# enable_pam_auth configuration
enable_pam_auth = (authentication_method == "HBAC")
ldap_enabled = (authentication_method == "LDAP")

freeipa_host = default('/clusterHostInfo/freeipa_server_hosts', [False])[0]
if freeipa_host and ldap_enabled:
    freeipa_host_components = freeipa_host.lower().split('.')
    if len(freeipa_host_components) >= 3:
        ldap_host = freeipa_host
        ldap_port = '636'
        ldap_uid = 'uid'
        ldap_bind_user = default('configurations/twiki/ldap_bind_user', 'kave_bind_user')
        ldap_bind_password = default('configurations/twiki/ldap_bind_password', False)
        if not ldap_bind_password or len(ldap_bind_password) < 7:
            raise Exception('If you want to use ldap, you must have an ldap_bind_user with a known password')
        else:
            Logger.sensitive_strings[ldap_bind_password] = "[PROTECTED]"

        ldap_base = 'dc=' + ',dc='.join(freeipa_host_components[1:])
    else:
        raise Exception('freeipa_host was provided for twiki installation but no FQDN could be determined from this.')
elif ldap_enabled:
    raise NameError('ldap not integrated because FreeIPA is not installed in this cluster')

template_000_default = default('configurations/twiki/template_000_default', """# Created automatically with Ambari
# All manual changes will be undone in the case of a server restart
# Edit the template through the Ambari interface instead
TraceEnable Off
Listen {{PORT}}
ServerName "{{servername}}"
DocumentRoot "{{www_folder}}"
""")

authtest_httpd_conf = default('configurations/twiki/authtest_httpd_conf', """# Created automatically with Ambari
# All manual changes will be undone in the case of a server restart
# Edit the template through the Ambari interface instead

# Authorization test html
# Avoid all browser/cgi/TWiki config issues by testing the basic httpd LDAP configuration here
# If the user can access /twiki/authconf/index.html this shows the system is working

BrowserMatchNoCase ^$ blockAccess

#### Change the path to match your local installation
<Directory "{{install_dir}}authtest">
    AllowOverride None
# NOTE: For Apache 2.4 and later use "Require all granted" instead of the next two lines:
    Order Allow,Deny
    Allow from all
    Deny from env=blockAccess

        {% if ldap_enabled %}

        AuthType Basic
        AuthName "LDAP Authentication"
        AuthBasicProvider ldap
        AuthzLDAPAuthoritative on
        AuthLDAPURL ldap://{{ldap_host}}:{{ldap_port}}/cn=users,cn=accounts,{{ldap_base}}?{{ldap_uid}} NONE
        AuthLDAPBindDN {{ldap_uid}}={{ldap_bind_user}},cn=sysaccounts,cn=etc,{{ldap_base}}
        AuthLDAPBindPassword {{ldap_bind_password}}
        AuthLDAPGroupAttributeIsDN on
        Require ldap-group cn={{ldap_group}},cn=groups,cn=accounts,{{ldap_base}}

        {% elif enable_pam_auth %}
        AllowOverride None
        AuthName "KAVE Login"
        AuthType Basic
        AuthBasicAuthoritative on
        AuthBasicProvider external
        AuthExternal pwauth
        require valid-user
        {% endif %}

    # File to return on access control error (e.g. wrong password)
    # ErrorDocument 401 /twiki/bin/view/TWiki/TWikiRegistration
    # Alternatively if your users are all known to be registered you may want
    # to redirect them to the Reset_password page.
    # ErrorDocument 401 /twiki/bin/view/TWiki/Reset_password


</Directory>
""")

twiki_httpd_conf = default('configurations/twiki/twiki_httpd_conf', """# Created automatically with Ambari
# All manual changes will be undone in the case of a server restart
# Edit the template through the Ambari interface instead
# Example twiki.conf file to configure Apache for TWiki.
#
# You can base your Apache configuration for TWiki on this example
# file, but you are invited to use the Apache config generator at
# http://twiki.org/cgi-bin/view/TWiki/ApacheConfigGenerator
# to easily create an Apache conf file specific to your needs.

# NOTE: If you use Apache 2.4 or later make sure to enable CGI
# in the primary apache configuration file (mod_cgi or mod_cgid).

ScriptAlias /twiki/bin "{{install_dir}}bin"

Alias /twiki/pub "{{install_dir}}pub"

# Block access to typical spam related attachments (.htm and .html files)
# Except the TWiki directory which is read only and does have attached html files.
# You should uncomment the two lines below if the TWiki is on the public Internet
#SetEnvIf Request_URI "twiki/pub/.*\.[hH][tT][mM]?$" blockAccess
#SetEnvIf Request_URI "twiki/pub/TWiki/.*\.[hH][tT][mM]?$" !blockAccess

# We set an environment variable called blockAccess.
#
# Setting a BrowserMatchNoCase to ^$ is important. It prevents TWiki from
# including its own topics as URLs and also prevents other TWikis from
# doing the same. This is important to prevent the most obvious
# Denial of Service attacks.
#
# You can expand this by adding more BrowserMatchNoCase statements to
# block evil browser agents trying the impossible task of mirroring a TWiki.
# http://twiki.org/cgi-bin/view/TWiki.ApacheConfigGenerator has a good list
# of bad spiders to block.
#
# Example:
# BrowserMatchNoCase ^SiteSucker blockAccess
BrowserMatchNoCase ^$ blockAccess


<Directory "{{install_dir}}bin">
    AllowOverride None
# NOTE: For Apache 2.4 and later use "Require all granted" instead of the next two lines:
    Order Allow,Deny
    Allow from all
    Deny from env=blockAccess

    Options ExecCGI FollowSymLinks
    SetHandler cgi-script

        {% if ldap_enabled %}

        AuthType Basic
        AuthName "LDAP Authentication"
        AuthBasicProvider ldap
        AuthzLDAPAuthoritative on
        AuthLDAPURL ldap://{{ldap_host}}:{{ldap_port}}/cn=users,cn=accounts,{{ldap_base}}?{{ldap_uid}} NONE
        AuthLDAPBindDN {{ldap_uid}}={{ldap_bind_user}},cn=sysaccounts,cn=etc,{{ldap_base}}
        AuthLDAPBindPassword {{ldap_bind_password}}
        AuthLDAPGroupAttributeIsDN on
        Require ldap-group cn={{ldap_group}},cn=groups,cn=accounts,{{ldap_base}}

        {% elif enable_pam_auth %}
        AllowOverride None
        AuthName "KAVE Login"
        AuthType Basic
        AuthBasicAuthoritative on
        AuthBasicProvider external
        AuthExternal pwauth
        require valid-user
        {% else %}

        # Password file for TWiki users
        AuthUserFile /home/httpd/twiki/data/.htpasswd
        AuthName 'Enter your WikiName: (First name and last name, no space, no dots, capitalized, e.g. JohnSmith)'
        AuthType Basic
        <FilesMatch "(attach|edit|manage|rename|save|upload|mail|logon|rest|.*auth).*">
            require valid-user
        </FilesMatch>
        {% endif %}

    # File to return on access control error (e.g. wrong password)
    # By convention this is the TWikiRegistration page, that allows users
    # to register with the TWiki. Apache requires this to be a *local* path.
    # Comment this out if you setup TWiki to completely deny access to TWikiGuest
    # in all webs or change the path to a static html page.
    ErrorDocument 401 /twiki/bin/view/TWiki/TWikiRegistration
    # Alternatively if your users are all known to be registered you may want
    # to redirect them to the Reset_password page.
    # ErrorDocument 401 /twiki/bin/view/TWiki/Reset_password

# When using Apache type login the following defines the TWiki scripts
# that makes Apache ask the browser to authenticate. It is correct that
# scripts such as view, resetpasswd & passwd are not authenticated.
# (un-comment to activate)
#<FilesMatch "(attach|edit|manage|rename|save|upload|mail|logon|rest|.*auth).*">
#    require valid-user
#</FilesMatch>

</Directory>


# This sets the options on the pub directory, which contains attachments and
# other files like CSS stylesheets and icons. AllowOverride None stops a
# user installing a .htaccess file that overrides these options.
# Finally all execution of PHP and other scripts is disabled.

# Note that files in pub are *not* protected by TWiki Access Controls,
# so if you want to control access to files attached to topics, you may
# need to add your own .htaccess files to subdirectories of pub. See the
# Apache documentation on .htaccess for more info.

#### Change the path to match your local installation
<Directory "{{install_dir}}pub">
    #if you are using an svn checkout an pseudo-install.pl, you will need to enable symlinks
    #Options FollowSymLinks
    Options None
    AllowOverride Limit
# NOTE: For Apache 2.4 and later use "Require all granted" instead of the next two lines:
    Order Allow,Deny
    Allow from all

    # If you have PHP4 or PHP5 installed as Apache module make sure the directive below is enabled
    # If you do not have PHP installed you will need to comment out the directory below
    # to avoid errors.
    # If PHP is installed as CGI this flag is not needed and will in fact make Apache fail
    php_admin_flag engine off

    # If you have PHP3 installed as Apache module make sure the directive below is enabled
    # If PHP is installed as CGI this flag is not needed and will in fact make Apache fail
    #php3_engine off

    # This line will redefine the mime type for the most common types of scripts
    AddType text/plain .shtml .php .php3 .phtml .phtm .pl .py .cgi
</Directory>
""")
