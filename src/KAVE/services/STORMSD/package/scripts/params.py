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

config = Script.get_config()
storm_conf_file = "/usr/local/storm/conf/storm.yaml"
hostname = config["hostname"]

# config['configurations']['stormsd']['stormsd.zookeeper.servers'].replace(", "," ").replace(","," ").split()
storm_zookeeper_servers = default("/clusterHostInfo/zookeeper_hosts", None)
nimbus_host = default("/clusterHostInfo/nimbus_sd_master_hosts", [None])[0]
# config['configurations']['stormsd']['stormsd.drpc.servers'].replace(", "," ").replace(","," ").split()
drpc_servers = default("/clusterHostInfo/stormsd_drpc_server_hosts", False)
use_drpc = (drpc_servers is not False)
if None in [storm_zookeeper_servers]:
    raise NameError("Could not find required services of zookeeper_hostsfrom in clusterHostInfo : " +
                    str(config['clusterHostInfo']))
if None in [nimbus_host]:
    raise NameError("Could not find required services of nimbus_sd_master_hosts in clusterHostInfo: " +
                    str(config['clusterHostInfo']))

# find/replace localhost
if nimbus_host == hostname:
    nimbus_host = "localhost"
storm_zookeeper_servers = [s if s != hostname else 'localhost' for s in storm_zookeeper_servers]

if use_drpc:
    drpc_servers = [s if s != hostname else 'localhost' for s in drpc_servers]

storm_zookeeper_port = default('configurations/stormsd/stormsd.zookeeper.port', "2181")
nimbus_childopts = default('configurations/stormsd/stormsd.nimbus.childopts',
                           '-Xmx1024m')
ui_port = default('configurations/stormsd/stormsd.ui.port', "8744")
ui_childopts = default('configurations/stormsd/stormsd.ui.childopts', '-Xmx768m -Djava.net.preferIPv4Stack=true')
supervisor_slots_ports = default('configurations/stormsd/stormsd.supervisor.slots.ports',
                                 '6700, 6701').replace(", ", " ").replace(",", " ").split()
supervisor_childopts = default('configurations/stormsd/stormsd.supervisor.childopts', '-Djava.net.preferIPv4Stack=true')
worker_childopts = default('configurations/stormsd/stormsd.worker.childopts',
                           '-Xmx768m -Djava.net.preferIPv4Stack=true')
drpc_childopts = default('configurations/stormsd/stormsd.drpc.childopts', '-Xmx768m -Djava.net.preferIPv4Stack=true')
log_level = default('configurations/stormsd/stormsd.loglevel', 'WARN')
logviewer_childopts = default('configurations/stormsd/stormsd.logviewer.childopts',
                              '-Xmx128m -Djava.net.preferIPv4Stack=true')
logviewer_port = default('configurations/stormsd/stormsd.logviewer.port', '8013')
childlogdir = default('configurations/stormsd/childlogdir', '/var/log/supervisord/child')
supervisor_logfile = default('configurations/stormsd/supervisor_logfile', '/var/log/supervisord.log')
storm_yaml_config = default('configurations/stormsd/stormsd.yaml.config', """#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


########### These all have default values as shown
########### Additional configuration goes into storm.yaml

storm.local.dir: "storm-local"
storm.zookeeper.servers:
 {% for server in storm_zookeeper_servers %}
  - "{{server}}"
 {% endfor %}
storm.zookeeper.port: 2181

nimbus.host: "{{nimbus_host}}"
nimbus.childopts :"{{nimbus_childopts}}"

ui.port: {{ui_port}}
ui.childopts: "{{ui_childopts}}"

logviewer.port: {{logviewer_port}}
logviewer.childopts: "{{logviewer_childopts}}"

drpc.childopts: "{{drpc_childopts}}"

worker.childopts: "{{worker_childopts}}"

supervisor.slots.ports:
{% for port in supervisor_slots_ports %}
  - {{port}}
{% endfor %}
supervisor.childopts: "{{supervisor_childopts}}"

""")
storm_cluster_config = default('configurations/stormsd/storm_cluster_config',
                               """<?xml version="1.0" encoding="UTF-8"?>
<!--
 Licensed to the Apache Software Foundation (ASF) under one or more
 contributor license agreements.  See the NOTICE file distributed with
 this work for additional information regarding copyright ownership.
 The ASF licenses this file to You under the Apache License, Version 2.0
 (the "License"); you may not use this file except in compliance with
 the License.  You may obtain a copy of the License at
     http://www.apache.org/licenses/LICENSE-2.0
 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
-->

<configuration monitorInterval="60">
<properties>
    <property name="pattern">%d{yyyy-MM-dd HH:mm:ss.SSS} %c{1.} [%p] %msg%n</property>
</properties>
<appenders>
    <RollingFile name="A1"
                 fileName="${sys:storm.log.dir}/${sys:logfile.name}"
                 filePattern="${sys:storm.log.dir}/${sys:logfile.name}.%i">
        <PatternLayout>
            <pattern>${pattern}</pattern>
        </PatternLayout>
        <Policies>
            <SizeBasedTriggeringPolicy size="100 MB"/> <!-- Or every 100 MB -->
        </Policies>
        <DefaultRolloverStrategy max="9"/>
    </RollingFile>
    <RollingFile name="ACCESS"
                 fileName="${sys:storm.log.dir}/access.log"
                 filePattern="${sys:storm.log.dir}/access.log.%i">
        <PatternLayout>
            <pattern>${pattern}</pattern>
        </PatternLayout>
        <Policies>
            <SizeBasedTriggeringPolicy size="100 MB"/> <!-- Or every 100 MB -->
        </Policies>
        <DefaultRolloverStrategy max="9"/>
    </RollingFile>
    <Syslog name="syslog" format="RFC5424" host="localhost" port="514"
            protocol="UDP" appName="[${sys:daemon.name}]" mdcId="mdc" includeMDC="true"
            facility="LOCAL5" enterpriseNumber="18060" newLine="true" exceptionPattern="%rEx{full}"
            messageId="[${sys:user.name}:S0]" id="storm"/>
</appenders>
<loggers>
    <Logger name="backtype.storm.security.auth.authorizer" level="info">
        <AppenderRef ref="ACCESS"/>
    </Logger>
    <root level="info"> <!-- We log everything -->
        <appender-ref ref="A1"/>
        <appender-ref ref="syslog"/>
    </root>
</loggers>
</configuration>
""")
