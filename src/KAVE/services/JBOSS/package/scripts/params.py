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

installation_dir = default('configurations/jboss/installation_dir', '/opt/jboss-as/')
#if not len(installation_dir)>3 or '/' not in installation_dir:
#    raise ValueError("You have set a directory incorrectly! " + installation_dir)
dirname = installation_dir
kc.is_valid_directory(dirname)


config_dir = default('configurations/jboss/config_dir', '/standalone/configuration/')
#if not len(config_dir)>3 or '/' not in config_dir:
#    raise ValueError("You have set a directory incorrectly! " + config_dir)
dirname = config_dir
kc.is_valid_directory(dirname)

service_user = default('configurations/jboss/service_user', 'jboss')

jboss_xmlconf_filename = default('configurations/jboss/jboss_xmlconf_filename', 'standalone.xml')
jboss_management_filename = default('configurations/jboss/jboss_management_filename', 'mgmt-users.properties')
jboss_conf_file = installation_dir + config_dir + jboss_xmlconf_filename
mgmt_users_file = installation_dir + config_dir + jboss_management_filename


JAVA_HOME = default('configurations/jboss/JAVA_HOME', "/usr/lib/jvm/java-1.7*-openjdk*/jre")

management_user = 'admin'
management_password = default('configurations/jboss/management_password', "NOTAPASSWORD")
if management_password == "NOTAPASSWORD":
    management_password = False
else:
    Logger.sensitive_strings[management_password] = "[PROTECTED]"

# ip adresses the service will be listening on
ip_address = default('configurations/jboss/ip_address', '0.0.0.0')
ip_address_management = default('configurations/jboss/ip_address_management', '127.0.0.1')

# Port configurations
http_port = default('configurations/jboss/http_port', "8080")
https_port = default('configurations/jboss/https_port', '8443')
management_native_port = default('configurations/jboss/management_native_port', '9999')
management_http_port = default('configurations/jboss/management_http_port', '9990')
management_https_port = default('configurations/jboss/management_https_port', '9443')
ajp_port = default('configurations/jboss/ajp_port', '8009')
osgi_http_port = default('configurations/jboss/osgi_http_port', '8090')
remoting_port = default('configurations/jboss/remoting_port', '4447')
txn_recovery_environment_port = default('configurations/jboss/txn_recovery_environment_port', '4712')
txn_status_manager_port = default('configurations/jboss/txn_status_manager_port', '4713')

mail_server = default('configurations/jboss/mail_server', 'localhost')
mail_port = default('configurations/jboss/mail_port', '25')
portnum = mail_port
kc.is_valid_port(portnum)

jbossxmlconfig =default('configurations/jboss/jbossxmlconfig',"""
<?xml version='1.0' encoding='UTF-8'?>
<server xmlns="urn:jboss:domain:1.2">
    <extensions>
        <extension module="org.jboss.as.clustering.infinispan"/>
        <extension module="org.jboss.as.configadmin"/>
        <extension module="org.jboss.as.connector"/>
        <extension module="org.jboss.as.deployment-scanner"/>
        <extension module="org.jboss.as.ee"/>
        <extension module="org.jboss.as.ejb3"/>
        <extension module="org.jboss.as.jaxrs"/>
        <extension module="org.jboss.as.jdr"/>
        <extension module="org.jboss.as.jmx"/>
        <extension module="org.jboss.as.jpa"/>
        <extension module="org.jboss.as.logging"/>
        <extension module="org.jboss.as.mail"/>
        <extension module="org.jboss.as.naming"/>
        <extension module="org.jboss.as.osgi"/>
        <extension module="org.jboss.as.pojo"/>
        <extension module="org.jboss.as.remoting"/>
        <extension module="org.jboss.as.sar"/>
        <extension module="org.jboss.as.security"/>
        <extension module="org.jboss.as.threads"/>
        <extension module="org.jboss.as.transactions"/>
        <extension module="org.jboss.as.web"/>
        <extension module="org.jboss.as.webservices"/>
        <extension module="org.jboss.as.weld"/>
    </extensions>
    <management>
        <security-realms>
            <security-realm name="ManagementRealm">
                <authentication>
                    <properties path="mgmt-users.properties" relative-to="jboss.server.config.dir"/>
                </authentication>
            </security-realm>
            <security-realm name="ApplicationRealm">
                <authentication>
                    <properties path="application-users.properties" relative-to="jboss.server.config.dir"/>
                </authentication>
            </security-realm>
        </security-realms>
        <management-interfaces>
            <native-interface security-realm="ManagementRealm">
                <socket-binding native="management-native"/>
            </native-interface>
            <http-interface security-realm="ManagementRealm">
                <socket-binding http="management-http"/>
            </http-interface>
        </management-interfaces>
    </management>
    <profile>
        <subsystem xmlns="urn:jboss:domain:logging:1.1">
            <console-handler name="CONSOLE">
                <level name="INFO"/>
                <formatter>
                    <pattern-formatter pattern="%d{HH:mm:ss,SSS} %-5p [%c] (%t) %s%E%n"/>
                </formatter>
            </console-handler>
            <periodic-rotating-file-handler name="FILE">
                <formatter>
                    <pattern-formatter pattern="%d{HH:mm:ss,SSS} %-5p [%c] (%t) %s%E%n"/>
                </formatter>
                <file relative-to="jboss.server.log.dir" path="server.log"/>
                <suffix value=".yyyy-MM-dd"/>
                <append value="true"/>
            </periodic-rotating-file-handler>
            <logger category="com.arjuna">
                <level name="WARN"/>
            </logger>
            <logger category="org.apache.tomcat.util.modeler">
                <level name="WARN"/>
            </logger>
            <logger category="sun.rmi">
                <level name="WARN"/>
            </logger>
            <logger category="jacorb">
                <level name="WARN"/>
            </logger>
            <logger category="jacorb.config">
                <level name="ERROR"/>
            </logger>
            <root-logger>
                <level name="INFO"/>
                <handlers>
                    <handler name="CONSOLE"/>
                    <handler name="FILE"/>
                </handlers>
            </root-logger>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:configadmin:1.0"/>
        <subsystem xmlns="urn:jboss:domain:datasources:1.0">
            <datasources>
                <datasource jndi-name="java:jboss/datasources/ExampleDS" pool-name="ExampleDS" enabled="true" use-java-context="true">
                    <connection-url>jdbc:h2:mem:test;DB_CLOSE_DELAY=-1</connection-url>
                    <driver>h2</driver>
                    <security>
                        <user-name>sa</user-name>
                        <password>sa</password>
                    </security>
                </datasource>
                <drivers>
                    <driver name="h2" module="com.h2database.h2">
                        <xa-datasource-class>org.h2.jdbcx.JdbcDataSource</xa-datasource-class>
                    </driver>
                </drivers>
            </datasources>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:deployment-scanner:1.1">
            <deployment-scanner path="deployments" relative-to="jboss.server.base.dir" scan-interval="5000"/>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:ee:1.0"/>
        <subsystem xmlns="urn:jboss:domain:ejb3:1.2">
            <session-bean>
                <stateless>
                    <bean-instance-pool-ref pool-name="slsb-strict-max-pool"/>
                </stateless>
                <stateful default-access-timeout="5000" cache-ref="simple"/>
                <singleton default-access-timeout="5000"/>
            </session-bean>
            <pools>
                <bean-instance-pools>
                    <strict-max-pool name="slsb-strict-max-pool" max-pool-size="20" instance-acquisition-timeout="5" instance-acquisition-timeout-unit="MINUTES"/>
                    <strict-max-pool name="mdb-strict-max-pool" max-pool-size="20" instance-acquisition-timeout="5" instance-acquisition-timeout-unit="MINUTES"/>
                </bean-instance-pools>
            </pools>
            <caches>
                <cache name="simple" aliases="NoPassivationCache"/>
                <cache name="passivating" passivation-store-ref="file" aliases="SimpleStatefulCache"/>
            </caches>
            <passivation-stores>
                <file-passivation-store name="file"/>
            </passivation-stores>
            <async thread-pool-name="default"/>
            <timer-service thread-pool-name="default">
                <data-store path="timer-service-data" relative-to="jboss.server.data.dir"/>
            </timer-service>
            <remote connector-ref="remoting-connector" thread-pool-name="default"/>
            <thread-pools>
                <thread-pool name="default">
                    <max-threads count="10"/>
                    <keepalive-time time="100" unit="milliseconds"/>
                </thread-pool>
            </thread-pools>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:infinispan:1.2" default-cache-container="hibernate">
            <cache-container name="hibernate" default-cache="local-query">
                <local-cache name="entity">
                    <transaction mode="NON_XA"/>
                    <eviction strategy="LRU" max-entries="10000"/>
                    <expiration max-idle="100000"/>
                </local-cache>
                <local-cache name="local-query">
                    <transaction mode="NONE"/>
                    <eviction strategy="LRU" max-entries="10000"/>
                    <expiration max-idle="100000"/>
                </local-cache>
                <local-cache name="timestamps">
                    <transaction mode="NONE"/>
                    <eviction strategy="NONE"/>
                </local-cache>
            </cache-container>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:jaxrs:1.0"/>
        <subsystem xmlns="urn:jboss:domain:jca:1.1">
            <archive-validation enabled="true" fail-on-error="true" fail-on-warn="false"/>
            <bean-validation enabled="true"/>
            <default-workmanager>
                <short-running-threads>
                    <core-threads count="50"/>
                    <queue-length count="50"/>
                    <max-threads count="50"/>
                    <keepalive-time time="10" unit="seconds"/>
                </short-running-threads>
                <long-running-threads>
                    <core-threads count="50"/>
                    <queue-length count="50"/>
                    <max-threads count="50"/>
                    <keepalive-time time="10" unit="seconds"/>
                </long-running-threads>
            </default-workmanager>
            <cached-connection-manager/>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:jdr:1.0"/>
        <subsystem xmlns="urn:jboss:domain:jmx:1.1">
            <show-model value="true"/>
            <remoting-connector/>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:jpa:1.0">
            <jpa default-datasource=""/>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:mail:1.0">
            <mail-session jndi-name="java:jboss/mail/Default">
                <smtp-server outbound-socket-binding-ref="mail-smtp"/>
            </mail-session>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:naming:1.1"/>
        <subsystem xmlns="urn:jboss:domain:osgi:1.2" activation="lazy">
            <properties>
                <!-- Specifies the beginning start level of the framework -->
                <property name="org.osgi.framework.startlevel.beginning">1</property>
            </properties>
            <capabilities>
                <!-- modules registered with the OSGi layer on startup -->
                <capability name="javax.servlet.api:v25"/>
                <capability name="javax.transaction.api"/>
                <!-- bundles started in startlevel 1 -->
                <capability name="org.apache.felix.log" startlevel="1"/>
                <capability name="org.jboss.osgi.logging" startlevel="1"/>
                <capability name="org.apache.felix.configadmin" startlevel="1"/>
                <capability name="org.jboss.as.osgi.configadmin" startlevel="1"/>
            </capabilities>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:pojo:1.0"/>
        <subsystem xmlns="urn:jboss:domain:remoting:1.1">
            <connector name="remoting-connector" socket-binding="remoting" security-realm="ApplicationRealm"/>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:resource-adapters:1.0"/>
        <subsystem xmlns="urn:jboss:domain:sar:1.0"/>
        <subsystem xmlns="urn:jboss:domain:security:1.1">
            <security-domains>
                <security-domain name="other" cache-type="default">
                    <authentication>
                        <login-module code="Remoting" flag="optional">
                            <module-option name="password-stacking" value="useFirstPass"/>
                        </login-module>
                        <login-module code="RealmUsersRoles" flag="required">
                            <module-option name="usersProperties" value="${jboss.server.config.dir}/application-users.properties"/>
                            <module-option name="rolesProperties" value="${jboss.server.config.dir}/application-roles.properties"/>
                            <module-option name="realm" value="ApplicationRealm"/>
                            <module-option name="password-stacking" value="useFirstPass"/>
                        </login-module>
                    </authentication>
                </security-domain>
                <security-domain name="jboss-web-policy" cache-type="default">
                    <authorization>
                        <policy-module code="Delegating" flag="required"/>
                    </authorization>
                </security-domain>
                <security-domain name="jboss-ejb-policy" cache-type="default">
                    <authorization>
                        <policy-module code="Delegating" flag="required"/>
                    </authorization>
                </security-domain>
            </security-domains>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:threads:1.1"/>
        <subsystem xmlns="urn:jboss:domain:transactions:1.1">
            <core-environment>
                <process-id>
                    <uuid/>
                </process-id>
            </core-environment>
            <recovery-environment socket-binding="txn-recovery-environment" status-socket-binding="txn-status-manager"/>
            <coordinator-environment default-timeout="300"/>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:web:1.1" default-virtual-server="default-host" native="false">
            <connector name="http" protocol="HTTP/1.1" scheme="http" socket-binding="http"/>
            <virtual-server name="default-host" enable-welcome-root="true">
                <alias name="localhost"/>
                <alias name="example.com"/>
            </virtual-server>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:webservices:1.1">
            <modify-wsdl-address>true</modify-wsdl-address>
            <wsdl-host>${jboss.bind.address:127.0.0.1}</wsdl-host>
            <endpoint-config name="Standard-Endpoint-Config"/>
            <endpoint-config name="Recording-Endpoint-Config">
                <pre-handler-chain name="recording-handlers" protocol-bindings="##SOAP11_HTTP ##SOAP11_HTTP_MTOM ##SOAP12_HTTP ##SOAP12_HTTP_MTOM">
                    <handler name="RecordingHandler" class="org.jboss.ws.common.invocation.RecordingServerHandler"/>
                </pre-handler-chain>
            </endpoint-config>
        </subsystem>
        <subsystem xmlns="urn:jboss:domain:weld:1.0"/>
    </profile>
    <interfaces>
        <interface name="management">
            <inet-address value="${jboss.bind.address.management:{{ip_address_management}}}"/>
        </interface>
        <interface name="public">
            <inet-address value="${jboss.bind.address:{{ip_address}}}"/>
        </interface>
        <!-- TODO - only show this if the jacorb subsystem is added  -->
        <interface name="unsecure">
            <!--
              ~  Used for IIOP sockets in the standard configuration.
              ~                  To secure JacORB you need to setup SSL
              -->
            <inet-address value="${jboss.bind.address.unsecure:127.0.0.1}"/>
        </interface>
    </interfaces>
    <socket-binding-group name="standard-sockets" default-interface="public" port-offset="${jboss.socket.binding.port-offset:0}">
        <socket-binding name="management-native" interface="management" port="${jboss.management.native.port:{{management_native_port}}}"/>
        <socket-binding name="management-http" interface="management" port="${jboss.management.http.port:{{management_http_port}}}"/>
        <socket-binding name="management-https" interface="management" port="${jboss.management.https.port:{{management_https_port}}}"/>
        <socket-binding name="ajp" port="{{ajp_port}}"/>
        <socket-binding name="http" port="{{http_port}}"/>
        <socket-binding name="https" port="{{https_port}}"/>
        <socket-binding name="osgi-http" interface="management" port="{{osgi_http_port}}"/>
        <socket-binding name="remoting" port="{{remoting_port}}"/>
        <socket-binding name="txn-recovery-environment" port="{{txn_recovery_environment_port}}"/>
        <socket-binding name="txn-status-manager" port="{{txn_status_manager_port}}"/>
        <outbound-socket-binding name="mail-smtp">
            <remote-destination host="{{mail_server}}" port="{{mail_port}}"/>
        </outbound-socket-binding>
    </socket-binding-group>
</server>
""")