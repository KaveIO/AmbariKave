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

systemd_lcmserver_unitfile_path = "/usr/lib/systemd/system/lcm-server.service"

LCM_UI_access_scheme = default('configurations/lcm_application/LCM_UI_access_scheme', 'https')

systemd_lcmui_unitfile_path = "/usr/lib/systemd/system/lcm-ui.service"

lcm_releaseversion = default('configurations/lcm_application/lcm_releaseversion', '0.2.5-SNAPSHOT')

lcm_application_name = default('configurations/lcm_application/lcm_application_name', 'lcmapp')

lcm_service_user = default('configurations/lcm_application/lcm_service_user', 'lcm')

lcm_install_dir = default('configurations/lcm_application/lcm_install_dir', '/opt/lcm')

lcm_home_dir = lcm_install_dir + '/lcm-complete-' + lcm_releaseversion + '/'

LCM_UI_URL = kc.default('configurations/lcm_application/LCM_UI_URL', hostname, kc.is_valid_hostname)

LCM_UI_PORT = kc.default('configurations/lcm_application/LCM_UI_PORT', '8081', kc.is_valid_port)

LCM_SecureUI_Port = kc.default('configurations/lcm_application/LCM_SecureUI_Port', '4444', kc.is_valid_port)

LCM_Server_URL = kc.default('configurations/lcm_application/LCM_Server_URL', hostname, kc.is_valid_hostname)

LCM_Server_PORT = kc.default('configurations/lcm_application/LCM_Server_PORT', '8085', kc.is_valid_port)

LCM_SecureServer_Port = kc.default('configurations/lcm_application/LCM_SecureServer_Port', '4445', kc.is_valid_port)

LCM_Swagger_PORT = kc.default('configurations/lcm_application/LCM_Swagger_PORT', '8083', kc.is_valid_port)

sever_log_file_path = default('configurations/lcm_logs/sever_log_file_path', 'logs/lcm-server.log')

server_log_file_size = default('configurations/lcm_logs/server_log_file_size', '20MB')

ui_log_file_path = default('configurations/lcm_logs/ui_log_file_path', 'logs/lcm-ui.log')

ui_log_file_size = default('configurations/lcm_logs/ui_log_file_size', '20MB')

Security_truststoreType = default('configurations/lcm_security/Security.truststoreType', 'JKS')

LCM_Server_Security_Encryption_Key = default(
    'configurations/lcm_security/LCM_Server_Security_Encryption_Key', '123456789qwertyu')

LCM_Admin_Password = default('configurations/lcm_security/LCM_Admin_Password', 'admin')

lcm_mongodb_host = default('/clusterHostInfo/mongodb_master_hosts', [None])[0]

if not lcm_mongodb_host:
    raise ValueError("Could not locate MongoDB server, did you install it in the cluster?")

lcm_mongodb_port = kc.default('configurations/mongodb/tcp_port', '27017', kc.is_valid_port)

application_properties = default('configurations/lcm_application/application_properties', """
# LCM configuration file
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
# LCM Id is used in the communication between LCMs when it is public.

lcm.server.application.name={{lcm_application_name}}

lcm.server.name={{LCM_Server_URL}}
lcm.server.port={{LCM_Server_PORT}}
lcm.server.securePort={{LCM_SecureServer_Port}}

# Example mongo configuration
lcm.server.storage=mongo
lcm.server.storage.mongo.host={{lcm_mongodb_host}}
lcm.server.storage.mongo.port={{lcm_mongodb_port}}
lcm.server.storage.mongo.database=lcm
#use syntax like bellow to authenticate
#username:password@databaseName
#or leave this field blank for unauthenticated access
lcm.server.storage.mongo.credentials=

lcm.server.basic.authentication.enabled=true
lcm.server.session.authentication.enabled=true
############################# UI settings #############################

# LCM User Interface configuration properties
lcm.ui.server.name={{LCM_UI_URL}}
lcm.ui.server.port={{LCM_UI_PORT}}
lcm.ui.server.securePort={{LCM_SecureUI_Port}}

# In case swagger is enabled REST API documentation  will be available.
# Go to http://{lcm.server.name}:{lcm.server.swagger.port}/docs for example http://localhost:8082/docs
# and place in the swagger source box: http://{{LCM_Server_URL}}:{lcm.server.swagger.port}/swagger.json
lcm.server.swagger.enable=true
lcm.server.swagger.port={{LCM_Swagger_PORT}}
""")

security_properties = default('configurations/lcm_security/security.properties', """
###########################################################################
# LCM security configuration file.
# DO NOT SHARE THIS FILE AND MAKE SURE THAT ONLY AUTHRIZED USERS CAN ACCESS IT!
#
# The LCM is splitted up in two separate executables. The server and the UI.
# These both configured with this properties file. the distinction can be easily
# made by looking at the property names.
############################# Server settings #############################
# Username and password for the default admin user. Once a actual admin user is
# created these become unused.
lcm.server.adminUser=admin
lcm.server.adminPassword={{LCM_Admin_Password}}
# Default ssl configuration location based on installation with the    setup_ssl.sh script.
# 'certificates' directory must be in the base application directory i.e. on the same
# level as bin, logs etc...
# SSL settings for the Grizzly server in the lcm-server module
lcm.server.security.keystore=certificates/lcm-keystore.jks
lcm.server.security.keystoreType=JKS
lcm.server.security.keystorePassword=storepass
lcm.server.security.keystoreAlias=cert-lcm
lcm.server.security.keystoreKeypass=keypass
lcm.server.security.debug=ssl


# SSL settings for requests made in the lcm-server module to another LCM
lcm.client.security.truststore=certificates/lcm-truststore.jks
lcm.client.security.truststorePassword=storepass
lcm.client.security.truststoreType=JKS


# Set this to true if you want to run on HTTP in case of HTTPS misconfiguration;
# when 'false' and on HTTPS a redirect HTTP -> HTTPS is setup.
# Please be aware that, as the name suggests, this introduces a safety
# concern. Be aware that if "unsafe" mode is on then, in case of SSL
# setup
# failures, HTTP is tried automatically.
# For the server, this means that if we cannot start on SSL then we
# just try to start on HTTP; and intercom will be HTTP only too.
# For the client/ui, same as the server for the webapp listener and
# backend connection too. Please also be aware that on pure HTTP no
# data is ever encrypted!
# Unsafe mode is meant for debug as well as a way to fallback on
# faulty HTTPS.
#
# Disable server module SSL
lcm.server.unsafe=false
#
#This property must be exactly 16 symbols long!
#Make sure that it is unique and do not share it with anyone!
lcm.server.security.encryption.key={{LCM_Server_Security_Encryption_Key}}
#
############################# UI settings #############################
#
# Default ssl configuration location based on installation with the
# setup_ssl.sh script.
# 'certificates' directory must be in the base application directory
# i.e. on the same level as
# bin, logs etc...
#
#Setting for Grizzly server in lcm-ui module.
lcm.ui.server.security.keystore=certificates/ui-keystore.jks
lcm.ui.server.security.keystoreType=JKS
lcm.ui.server.security.keystorePassword=storepass
lcm.ui.server.security.keystoreAlias=cert-ui
lcm.ui.server.security.keystoreKeypass=keypass
#Requests to the lcm-server module will use bellow settings
lcm.ui.client.security.truststore=certificates/ui-truststore.jks
lcm.ui.client.security.truststorePassword=storepass
lcm.ui.client.security.truststoreType=JKS
#
# Set this to true if you want to run on HTTP in case of HTTPS
# misconfiguration; when 'false' and on HTTPS a redirect HTTP -> HTTPS is setup.
# Please be aware that, as the name suggests, this introduces a safety
# concern. Be aware that if "unsafe" mode is on then, in case of SSL setup
# failures, HTTP is tried automatically.
# For the server, this means that if we cannot start on SSL then we
# just try to start on HTTP; and intercom will be HTTP only too.
# For the client/ui, same as the server for the webapp listener and
# backend connection too. Please also be aware that on pure HTTP no
# data is ever encrypted!
# Unsafe mode is meant for debug as well as a way to fallback on faulty HTTPS.
#
# Disable ui module SSL
lcm.ui.server.unsafe=false
#
#Link to the server certificate - in the UI there is download link
lcm.ui.client.security.server.certificate=certificates/lcm-certificate.cer
""")

log4j_server_properties = default('configurations/lcm_logs/log4j-server_properties', """
# Root logger option - default one
log4j.rootLogger=INFO, serverLog
# All autorization messages are logged with this logger
log4j.category.authorizationLogger=DEBUG, authorizationLog
# All authentication messages are logged with this logger
log4j.category.authenticationLogger=DEBUG, authenticationLog
# lcm-ui module logger log4j.category.sout=DEBUG, stdout
log4j.appender.serverLog=org.apache.log4j.RollingFileAppender
log4j.appender.serverLog.File={{sever_log_file_path}}
log4j.appender.serverLog.MaxFileSize={{server_log_file_size}}
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

log4j_ui_properties = default('configurations/lcm_logs/log4j-ui_properties', """
# Root logger option - default one
log4j.rootLogger=INFO, uiLog
# lcm-ui module logger
log4j.category.sout=DEBUG, stdout

log4j.appender.uiLog=org.apache.log4j.RollingFileAppender
log4j.appender.uiLog.File={{ui_log_file_path}}
log4j.appender.uiLog.MaxFileSize={{ui_log_file_size}}
log4j.appender.uiLog.MaxBackupIndex=10
log4j.appender.uiLog.layout=org.apache.log4j.PatternLayout
log4j.appender.uiLog.layout.ConversionPattern=%d{yyyy-MM-dd HH:mm:ss}%-5p %c{1}:%L - %m%n

# Direct log messages to stdout
log4j.appender.stdout=org.apache.log4j.ConsoleAppender
log4j.appender.stdout.Target=System.out
log4j.appender.stdout.layout=org.apache.log4j.PatternLayout
log4j.appender.stdout.layout.ConversionPattern=%d{yyyy-MM-dd HH:mm:ss} %-5p %c{1}:%L - %m%n
""")
