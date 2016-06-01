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
import kavecommon as kc

config = Script.get_config()

hostname = config["hostname"]

enable_pam_auth = default('configurations/hue/enable_pam_auth', 'True')
enable_pam_auth = kc.trueorfalse(enable_pam_auth)

# Copied from knox configuration!!
namenode_hosts = default("/clusterHostInfo/namenode_host", None)
if type(namenode_hosts) is list:
    namenode_host = namenode_hosts[0]
else:
    namenode_host = namenode_hosts

has_namenode = (namenode_host is not None)
namenode_http_port = "50070"
namenode_rpc_port = "8020"

if has_namenode:
    if 'dfs.namenode.http-address' in config['configurations']['hdfs-site']:
        namenode_http_port = get_port_from_url(config['configurations']['hdfs-site']['dfs.namenode.http-address'])
    if 'dfs.namenode.rpc-address' in config['configurations']['hdfs-site']:
        namenode_rpc_port = get_port_from_url(config['configurations']['hdfs-site']['dfs.namenode.rpc-address'])

rm_hosts = default("/clusterHostInfo/rm_host", None)
if type(rm_hosts) is list:
    rm_host = rm_hosts[0]
else:
    rm_host = rm_hosts
has_rm = (rm_host is not None)

jt_rpc_port = "8050"
rm_port = "8080"

if has_rm:
    if 'yarn.resourcemanager.address' in config['configurations']['yarn-site']:
        jt_rpc_port = get_port_from_url(config['configurations']['yarn-site']['yarn.resourcemanager.address'])

    if 'yarn.resourcemanager.webapp.address' in config['configurations']['yarn-site']:
        rm_port = get_port_from_url(config['configurations']['yarn-site']['yarn.resourcemanager.webapp.address'])

hive_http_port = default('/configurations/hive-site/hive.server2.thrift.http.port', "10001")
hive_port = default('/configurations/hive-site/hive.server2.thrift.port', "10000")
hive_http_path = default('/configurations/hive-site/hive.server2.thrift.http.path', "cliservice")
hive_server_hosts = default("/clusterHostInfo/hive_server_host", None)
if type(hive_server_hosts) is list:
    hive_server_host = hive_server_hosts[0]
else:
    hive_server_host = hive_server_hosts

templeton_port = default('/configurations/webhcat-site/templeton.port', "50111")
webhcat_server_hosts = default("/clusterHostInfo/webhcat_server_host", None)
if type(webhcat_server_hosts) is list:
    webhcat_server_host = webhcat_server_hosts[0]
else:
    webhcat_server_host = webhcat_server_hosts

hbase_master_port = default('/configurations/hbase-site/hbase.rest.port', "8080")
hbase_master_hosts = default("/clusterHostInfo/hbase_master_hosts", None)
if type(hbase_master_hosts) is list:
    hbase_master_host = hbase_master_hosts[0]
else:
    hbase_master_host = hbase_master_hosts

oozie_server_hosts = default("/clusterHostInfo/oozie_server", None)
if type(oozie_server_hosts) is list:
    oozie_server_host = oozie_server_hosts[0]
else:
    oozie_server_host = oozie_server_hosts

has_oozie = (oozie_server_host is not None)
oozie_server_port = "11000"

if has_oozie:
    if 'oozie.base.url' in config['configurations']['oozie-site']:
        oozie_server_port = get_port_from_url(config['configurations']['oozie-site']['oozie.base.url'])

history_hosts = default("/clusterHostInfo/hs_host", None)
if type(history_hosts) is list:
    history_host = history_hosts[0]
else:
    history_host = history_hosts

has_hs = (history_host is not None)

######################################################################################


namenode = namenode_host
if namenode is None or namenode == "":
    namenode = 'localhost'
    # can reconfigure later?

yarn_host = rm_host
if yarn_host is None or yarn_host == "":
    yarn_host = 'localhost'
    # can reconfigure later?

yarn_host = rm_host
if yarn_host is None or yarn_host == "":
    yarn_host = 'localhost'
    # can reconfigure later?

oozie_host = oozie_server_host
if oozie_host is None or oozie_host == "":
    oozie_host = 'localhost'
    # can reconfigure later?

hcat_host = webhcat_server_host
if hcat_host is None or hcat_host == "":
    hcat_host = 'localhost'
    # can reconfigure later?

hive_host = hive_server_host
if hive_host is None or hive_host == "":
    hive_host = 'localhost'
    # can reconfigure later?

history_host = history_host
if history_host is None or history_host == "":
    history_host = 'localhost'
    # can reconfigure later?

# PORTS


web_ui_port = default('configurations/hue/web_ui_port', '8000')
web_ui_host = default('configurations/hue/web_ui_host', '0.0.0.0')
yarn_api_port = default('configurations/hue/yarn_api_port', '8088')
nodemanager_port = default('configurations/hue/nodemanager_port', '8042')
history_port = default('configurations/hue/history_port', '19888')

hdfs_port = namenode_rpc_port
webhdfs_port = namenode_http_port
yarn_rpc_port = jt_rpc_port
hive_port = hive_port
oozie_port = oozie_server_port
hcat_port = templeton_port

# OTHERS #

# new random key with each reconfigure ... I hope this is OK!
secret_key = ''.join(
    [random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(random.randint(40, 55))])

hue_ini = default('configurations/hue/hue_ini', """# Created automatically with Ambari
# All manual changes will be undone in the case of a server restart
# Edit the template through the Ambari interface instead

#####################################
# DEVELOPMENT EDITION
#####################################

# Hue configuration file
# ===================================
#
# For complete documentation about the contents of this file, run
#       $ <hue_root>/build/env/bin/hue config_help
#
# All .ini files under the current directory are treated equally.  Their
# contents are merged to form the Hue configuration, which can
# can be viewed on the Hue at
#       http://<hue_host>:<port>/dump_config


###########################################################################
# General configuration for core Desktop features (authentication, etc)
###########################################################################

[desktop]

  kredentials_dir="/tmp"

  send_dbug_messages=1

  # To show database transactions, set database_logging to 1
  database_logging=0

  # Set this to a random string, the longer the better.
  # This is used for secure hashing in the session store.
  secret_key={{secret_key}}

  # Webserver listens on this address and port
  http_host={{web_ui_host}}
  http_port={{web_ui_port}}

  # Time zone name
  time_zone=America/Los_Angeles

  # Turn off debug
  django_debug_mode=1

  # Turn off backtrace for server error
  http_500_debug_mode=1

  # Set to true to use CherryPy as the webserver, set to false
  # to use Spawning as the webserver. Defaults to Spawning if
  # key is not specified.
  use_cherrypy_server=true

  # Webserver runs as this user
  server_user=hue
  server_group=hadoop

  # If set to false, runcpserver will not actually start the web server.
  # Used if Apache is being used as a WSGI container.
  ## enable_server=yes

  # Filename of SSL Certificate
  ## ssl_certificate=

  # Filename of SSL RSA Private Key
  ## ssl_private_key=

  # Default encoding for site data
  ## default_site_encoding=utf-8

  # Options for X_FRAME_OPTIONS header. Default is SAMEORIGIN
  x_frame_options='ALLOWALL'

  [[supervisor]]
    ## celeryd=no

  # Configuration options for user authentication into the web application
  # ------------------------------------------------------------------------
  [[auth]]

    # Authentication backend. Common settings are:
    # - django.contrib.auth.backends.ModelBackend (entirely Django backend)
    # - desktop.auth.backend.AllowAllBackend (allows everyone)
    # - desktop.auth.backend.AllowFirstUserDjangoBackend
    #     (Default. Relies on Django and user manager, after the first login)
    # - desktop.auth.backend.LdapBackend
    # - desktop.auth.backend.PamBackend
    # - desktop.auth.backend.SpnegoDjangoBackend
    # - desktop.auth.backend.RemoteUserDjangoBackend
    {% if enable_pam_auth %}
    backend=desktop.auth.backend.PamBackend
    pam_service=login
    {% else %}
    backend=desktop.auth.backend.AllowFirstUserDjangoBackend
    {% endif %}


  # Configuration options for specifying the Desktop Database.  For more info,
  # see http://docs.djangoproject.com/en/1.1/ref/settings/#database-engine
  # ------------------------------------------------------------------------
  [[database]]
    engine=sqlite3
    name=/var/lib/hue/desktop.db
    # Database engine is typically one of:
    # postgresql_psycopg2, mysql, or sqlite3
    #
    # Note that for sqlite3, 'name', below is a filename;
    # for other backends, it is the database name.
    ## engine=sqlite3
    ## host=
    ## port=
    ## user=
    ## password=
    ## name=


  # Configuration options for connecting to an external SMTP server
  # ------------------------------------------------------------------------
  [[smtp]]

    # The SMTP server information for email notification delivery
    host=localhost
    port=25
    user=
    password=

    # Whether to use a TLS (secure) connection when talking to the SMTP server
    tls=no

    # Default email address to use for various automated notification from Hue
    ## default_from_email=hue@localhost


  # Configuration options for Kerberos integration for secured Hadoop clusters
  # ------------------------------------------------------------------------
  [[kerberos]]

    # Path to Hue's Kerberos keytab file
    ## hue_keytab=/etc/security/keytabs/hue.service.keytab

    # Kerberos principal name for Hue
    ## hue_principal=hue/FQDN@REALM

    # Path to kinit
    ## kinit_path=/usr/bin/kinit

    ## Frequency in seconds with which Hue will renew its keytab. Default 1h.
    ## reinit_frequency=3600

    ## Path to keep Kerberos credentials cached.
    ## ccache_path=/tmp/hue_krb5_ccache


###########################################################################
# Settings to configure your Hadoop cluster.
###########################################################################

[hadoop]

  # Configuration for HDFS NameNode
  # ------------------------------------------------------------------------
  [[hdfs_clusters]]

    [[[default]]]
      # Enter the filesystem uri
      fs_defaultfs=hdfs://{{namenode}}:{{hdfs_port}}

      # Use WebHdfs/HttpFs as the communication mechanism. To fallback to
      # using the Thrift plugin (used in Hue 1.x), this must be uncommented
      # and explicitly set to the empty value.
      webhdfs_url=http://{{namenode}}:{{webhdfs_port}}/webhdfs/v1/

      ## security_enabled=true


  [[yarn_clusters]]

    [[[default]]]
      # Whether to submit jobs to this cluster
      submit_to=true

      ## security_enabled=false

      # Resource Manager logical name (required for HA)
      ## logical_name=

      # URL of the ResourceManager webapp address (yarn.resourcemanager.webapp.address)
      resourcemanager_api_url=http://{{yarn_host}}:{{yarn_api_port}}

      # URL of Yarn RPC adress (yarn.resourcemanager.address)
      resourcemanager_rpc_url=http://{{yarn_host}}:{{yarn_rpc_port}}

      # URL of the ProxyServer API
      proxy_api_url=http://{{yarn_host}}:{{yarn_host}}

      # URL of the HistoryServer API
      history_server_api_url=http://{{history_host}}:{{history_port}}

      # URL of the NodeManager API
      node_manager_api_url=http://{{yarn_host}}:{{nodemanager_port}}

      # HA support by specifying multiple clusters
      # e.g.

      # [[[ha]]]
    # Enter the host on which you are running the failover Resource Manager
        #resourcemanager_api_url=http://failover-host:8088
        #logical_name=failover
        #submit_to=True

###########################################################################
# Settings to configure liboozie
###########################################################################

[liboozie]
  # The URL where the Oozie service runs on. This is required in order for
  # users to submit jobs.
  oozie_url=http://{{oozie_host}}:{{oozie_port}}/oozie

  ## security_enabled=true

  # Location on HDFS where the workflows/coordinator are deployed when submitted.
  ## remote_deployement_dir=/user/hue/oozie/deployments


###########################################################################
# Settings to configure the Oozie app
###########################################################################

[oozie]

###########################################################################
# Settings to configure Beeswax
###########################################################################

[beeswax]

  # Host where Hive server Thrift daemon is running.
  # If Kerberos security is enabled, use fully-qualified domain name (FQDN).
  beeswax_server_host={{hive_host}}
  hive_server_host={{hive_host}}

  # Port where HiveServer2 Thrift server runs on.
  hive_server_port={{hive_port}}

  [[ssl]]
    # SSL communication enabled for this server.
    ## enabled=false

    # Path to Certificate Authority certificates.
    ## cacerts=/etc/hue/cacerts.pem

    # Path to the private key file.
    ## key=/etc/hue/key.pem

    # Path to the public certificate file.
    ## cert=/etc/hue/cert.pem

    # Choose whether Hue should validate certificates received from the server.
    ## validate=true



[useradmin]
  # The name of the default user group that users will be a member of
  default_user_group=hadoop
  default_username=hue
  default_user_password=1111


[hcatalog]
  templeton_url=http://{{hcat_host}}:{{hcat_port}}/templeton/v1/
  security_enabled=false

[about]
  tutorials_installed=false

[pig]
  udf_path="/tmp/udfs"

""")

hue_httpd_conf = default('configurations/hue/hue_httpd_conf', """# Created automatically with Ambari
# All manual changes will be undone in the case of a server restart
# Edit the template through the Ambari interface instead

Listen {{web_ui_port}}

WSGIPythonHome /usr/lib/hue/build/env
WSGIPythonPath /usr/lib/hue/build/env/bin/python

<VirtualHost *:{{web_ui_port}}>
  ServerName <FQDN>

  ## WSGI settings
  WSGIDaemonProcess hue_httpd display-name=hue_httpd processes=8 threads=10 user=hue
  WSGIScriptAlias / /usr/lib/hue/desktop/core/src/desktop/wsgi.py
  <Directory /usr/lib/hue/desktop/core/src/desktop>
    Order deny,allow
    Allow from all
  </Directory>

  Alias "/static/" "/usr/lib/hue/desktop/core/static/"
  Alias "/about/static/" "/usr/lib/hue/apps/about/static/"
  Alias "/beeswax/static/" "/usr/lib/hue/apps/beeswax/static/"
  Alias "/filebrowser/static/" "/usr/lib/hue/apps/filebrowser/src/filebrowser/static/"
  Alias "/hcatalog/static/" "/usr/lib/hue/apps/hcatalog/src/hcatalog/static/"
  Alias "/help/static/" "/usr/lib/hue/apps/help/src/help/static/"
  Alias "/jobbrowser/static/" "/usr/lib/hue/apps/jobbrowser/static/"
  Alias "/jobsub/static/" "/usr/lib/hue/apps/jobsub/static/"
  Alias "/oozie/static/" "/usr/lib/hue/apps/oozie/static/"
  Alias "/pig/static/" "/usr/lib/hue/apps/pig/src/pig/static/"
  Alias "/shell/static/" "/usr/lib/hue/apps/shell/src/shell/static/"
  Alias "/useradmin/static/" "/usr/lib/hue/apps/useradmin/static/"

  <IfModule mod_expires.c>
    <FilesMatch "\.(jpg|gif|png|css|js)$">
      ExpiresActive on
      ExpiresDefault "access plus 1 day"
    </FilesMatch>
  </IfModule>

  ## SSL part
  # SSLEngine on
  # SSLOptions +StrictRequire

  # SSLProtocol -all +TLSv1 +SSLv3
  # SSLCipherSuite HIGH:MEDIUM:!aNULL:+SHA1:+MD5:+HIGH:+MEDIUM

  # SSLCertificateFile /etc/ssl/hue.crt
  # SSLCertificateKeyFile /etc/ssl/hue.key

  # SSLProxyEngine off

  ## Logging
  ErrorLog /var/log/httpd/error_hue_httpd_log
  CustomLog /var/log/httpd/access_hue_httpd_log combined
</VirtualHost>
""")
