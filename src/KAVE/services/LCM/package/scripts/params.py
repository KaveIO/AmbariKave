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
import string
import kavecommon as kc

config = Script.get_config()

hostname = config["hostname"]
Security_truststoreType = default('configurations/lcm/Security.truststoreType', 'JKS')
lcm_server_security_encryption_key = default('configurations/lcm/lcm.server.security.encryption.key', '123456789qwertyu')
security_properties = default('configurations/lcm/security.properties', """# LCM security configuration file.
# DO NOT SHARE THIS FILE AND MAKE SURE THAT ONLY AUTHRIZED USERS CAN ACCESS IT!
#
# The LCM is splitted up in two separate executables. The server and the UI.
# These both configured with this properties file. the distinction can be easily
# made by looking at the property names.

############################# Server settings #############################

# Username and password for the default admin user. Once a actual admin user is
# created these become unused.
lcm.server.adminUser=
lcm.server.adminPassword=

# Default ssl configuration location based on installation with the setup_ssl.sh script.
# 'certificates' directory must be in the base application directory i.e. on the same level as
# bin, logs etc...
# SSL settings for the Grizzly server in the lcm-server module
lcm.server.security.keystore=certificates/server.p12
lcm.server.security.keystoreType=pkcs12
lcm.server.security.keystorePassword=
lcm.server.security.keystoreAlias=cert-lcm
lcm.server.security.keystoreKeypass=
lcm.server.security.debug=ssl

# SSL settings for requests made in the lcm-server module to another LCM
lcm.client.security.truststore=certificates/lcm.keystore
lcm.client.security.truststorePassword=
lcm.client.security.truststoreType=JKS


# Set this to true if you want to run on HTTP in case of HTTPS misconfiguration; when 'false' and on HTTPS a redirect HTTP -> HTTPS is setup.
# Please be aware that, as the name suggests, this introduces a safety concern. Be aware that if "unsafe" mode is on then, in case of SSL setup
# failures, HTTP is tried automatically.
# For the server, this means that if we cannot start on SSL then we just try to start on HTTP; and intercom will be HTTP only too.
# For the client/ui, same as the server for the webapp listener and backend connection too. Please also be aware that on pure HTTP no data is ever
# encrypted!
# Unsafe mode is meant for debug as well as a way to fallback on faulty HTTPS.

# Disable server module SSL
lcm.server.unsafe=false


#This property must be exactly 16 symbols long!
#Make sure that it is unique and do not share it with anyone!
lcm.server.security.encryption.key=

############################# UI settings #############################

# Default ssl configuration location based on installation with the setup_ssl.sh script.
# 'certificates' directory must be in the base application directory i.e. on the same level as
# bin, logs etc...

#Setting for Grizzly server in lcm-ui module.
lcm.ui.server.security.keystore=certificates/client.p12
lcm.ui.server.security.keystoreType=pkcs12
lcm.ui.server.security.keystorePassword=storepass
lcm.ui.server.security.keystoreAlias=cert-ui
lcm.ui.server.security.keystoreKeypass=storepass
#Requests to the lcm-server module will use bellow settings
lcm.ui.client.security.truststore=certificates/ui.keystore
lcm.ui.client.security.truststorePassword=storepass
lcm.ui.client.security.truststoreType=JKS

# Set this to true if you want to run on HTTP in case of HTTPS misconfiguration; when 'false' and on HTTPS a redirect HTTP -> HTTPS is setup.
# Please be aware that, as the name suggests, this introduces a safety concern. Be aware that if "unsafe" mode is on then, in case of SSL setup
# failures, HTTP is tried automatically.
# For the server, this means that if we cannot start on SSL then we just try to start on HTTP; and intercom will be HTTP only too.
# For the client/ui, same as the server for the webapp listener and backend connection too. Please also be aware that on pure HTTP no data is ever
# encrypted!
# Unsafe mode is meant for debug as well as a way to fallback on faulty HTTPS.

# Disable ui module SSL
lcm.ui.server.unsafe=false

#Link to the server certificate - in the UI there is download link
lcm.ui.client.security.server.certificate=${PWD}/src/main/resources/certificates/lcm-certificate.cer
""")

Server_Name = default('configurations/lcm/ServerName', 'localhost')
PORT = default('configurations/lcm/Port', '8080')
Secure_Port = default('configurations/lcm/SecurePort', '4444')
application_properties = default('configurations/lcm/application.properties', """# LCM configuration file
#
# The LCM is splitted up in two separate executables. The server and the UI.
# These both configured with this properties file. the distinction can be easily
# made by looking at the property names.

############################# Server settings #############################

#The maximum length of the application name property is 12.
#If the application name property is longer than that only the first 12 symbols are taken.
#The LCM id consists three components:
# - application name which is defined by the user bellow;
# - unix timestamp;
# - random alphanum.
#The length of the whole LCM id must be 32.
# LCM Id is used in the communication between LCMs it is public.
lcm.server.application.name=

lcm.server.name=localhost
lcm.server.port=8081
lcm.server.securePort=4444

# Example mongo configuration
lcm.server.storage=mongo
lcm.server.storage.mongo.host=localhost
lcm.server.storage.mongo.port=27017
lcm.server.storage.mongo.database=lcm
#use syntax like bellow to authenticate
#username:password@databaseName
#or leave this field blank for unauthenticated access
lcm.server.storage.mongo.credentials=

lcm.server.basic.authentication.enabled=true
lcm.server.session.authentication.enabled=true
############################# UI settings #############################

# LCM User Interface configuration properties
lcm.ui.server.name=localhost
lcm.ui.server.port=8080
lcm.ui.server.securePort=4443

# In case swagger is enabled REST API documentation  will be available.
# Go to http://<lcm.server.name>:<lcm.server.swagger.port>/docs for example http://localhost:8082/docs
# and place in the swagger source box: http://<lcm.server.name>:<lcm.server.swagger.port>/swagger.json
lcm.server.swagger.enable=true
lcm.server.swagger.port=8082
""")
Sever_log_file_path = default('configurations/lcm/Sever_log_file_path', 'logs/lcm-server.log')
Maximum_size_for_Server_log_file = default('configurations/lcm/Maximum_size_for_Server_log_file', '20M')
Maximum_size_for_UI_log_file = default('configurations/lcm/Maximum_size_for_UI_log_file', '20M')
log4j_server_properties = default('configurations/lcm/log4j-server.properties', """# Root logger option -  default one
log4j.rootLogger=INFO, serverLog

# All autorization messages are logged with this logger
log4j.category.authorizationLogger=DEBUG, authorizationLog

# All authentication messages are logged with this logger
log4j.category.authenticationLogger=DEBUG, authenticationLog

# lcm-ui module logger
log4j.category.sout=DEBUG, stdout

log4j.appender.serverLog=org.apache.log4j.RollingFileAppender
log4j.appender.serverLog.File=logs/lcm-server.log
log4j.appender.serverLog.MaxFileSize=20MB
log4j.appender.serverLog.MaxBackupIndex=10
log4j.appender.serverLog.layout=org.apache.log4j.PatternLayout
log4j.appender.serverLog.layout.ConversionPattern=%d{yyyy-MM-dd HH:mm:ss} %-5p %c{1}:%L - %m%n

log4j.appender.authorizationLog=org.apache.log4j.RollingFileAppender
log4j.appender.authorizationLog.File=logs/authorization.log
log4j.appender.authorizationLog.MaxFileSize=20MB
log4j.appender.authorizationLog.MaxBackupIndex=10
log4j.appender.authorizationLog.layout=org.apache.log4j.PatternLayout
log4j.appender.authorizationLog.layout.ConversionPattern=%d{yyyy-MM-dd HH:mm:ss} %-5p - %m%n

log4j.appender.authenticationLog=org.apache.log4j.RollingFileAppender
log4j.appender.authenticationLog.File=logs/authentication.log
log4j.appender.authenticationLog.MaxFileSize=20MB
log4j.appender.authenticationLog.MaxBackupIndex=10
log4j.appender.authenticationLog.layout=org.apache.log4j.PatternLayout
log4j.appender.authenticationLog.layout.ConversionPattern=%d{yyyy-MM-dd HH:mm:ss} %-5p - %m%n

# Direct log messages to stdout
log4j.appender.stdout=org.apache.log4j.ConsoleAppender
log4j.appender.stdout.Target=System.out
log4j.appender.stdout.layout=org.apache.log4j.PatternLayout
log4j.appender.stdout.layout.ConversionPattern=%d{yyyy-MM-dd HH:mm:ss} %-5p %C{1}:%L - %m%n

log4j.logger.org.mongodb.driver=ERROR
""")
log4j_ui_properties = default('configurations/lcm/log4j-ui.properties',  """# Root logger option - defailt one
log4j.rootLogger=INFO, uiLog

# lcm-ui module logger
log4j.category.sout=DEBUG, stdout

log4j.appender.uiLog=org.apache.log4j.RollingFileAppender
log4j.appender.uiLog.File={{UI_log_file_path}}
log4j.appender.uiLog.MaxFileSize={{Maximum_size_for_UI_log_file}}
log4j.appender.uiLog.MaxBackupIndex=10
log4j.appender.uiLog.layout=org.apache.log4j.PatternLayout
log4j.appender.uiLog.layout.ConversionPattern=%d{yyyy-MM-dd HH:mm:ss} %-5p %c{1}:%L - %m%n

# Direct log messages to stdout
log4j.appender.stdout=org.apache.log4j.ConsoleAppender
log4j.appender.stdout.Target=System.out
log4j.appender.stdout.layout=org.apache.log4j.PatternLayout
log4j.appender.stdout.layout.ConversionPattern=%d{yyyy-MM-dd HH:mm:ss} %-5p %c{1}:%L - %m%n
""")
UI_log_file_path = default('configurations/lcm/UI_log_file_path', 'logs/lcm-ui.log')







lcm_home = kc.default('configurations/lcm/lcm_home', '/usr/opt/local/lcm', kc.is_valid_directory)

lcm_default_owner = default('configurations/lcm/lcm_default_owner', 'lcm')

lcm_base_url = default('configurations/lcm/lcm_base_url', 'http://localhost:8080')

lcm_web_server_port = default('configurations/lcm/lcm_web_server_port', '8080')

lcm_authenticate = default('configurations/lcm/lcm_authenticate', 'False')

lcm_expose_config = default('configurations/lcm/lcm_expose_config', 'True')


AMBARI_ADMIN = config['configurations']['lcm']['admin']
AMBARI_ADMIN_PASS = config['configurations']['lcm']['admin']
www_folder = kc.default('configurations/lcm/www_folder', '/var/www/html/', kc.is_valid_directory)
AMBARI_SERVER = default("/clusterHostInfo/ambari_server_host", ['ambari'])[0]

PORT = kc.default('configurations/lcm/PORT', '8080', kc.is_valid_port)

template_000_default = default('configurations/apache/template_000_default', """# Created automatically with Ambari

""")

AMBARI_SHORT_HOST = AMBARI_SERVER.split('.')[0]
servername = kc.default('configurations/lcm/servername', hostname, kc.is_valid_hostname)
if servername == "default":
    servername = hostname

lcm_conf = default('configurations/lcm/lcm_config_path', """

 """)
