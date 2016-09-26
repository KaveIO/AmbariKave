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
                           '-Xmx1024m -Djava.net.preferIPv4Stack=true')
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
# storm.log4j2.conf.dir: "log4j2"
storm.zookeeper.servers:
{% for server in storm_zookeeper_servers %}
  - "{{server}}"
{% endfor %}
storm.zookeeper.port: 2181
storm.zookeeper.root: "/storm"
storm.zookeeper.session.timeout: 20000
storm.zookeeper.connection.timeout: 15000
storm.zookeeper.retry.times: 5
storm.zookeeper.retry.interval: 1000
storm.zookeeper.retry.intervalceiling.millis: 30000
storm.zookeeper.auth.user: null
storm.zookeeper.auth.password: null
storm.exhibitor.port: 8080
storm.exhibitor.poll.uripath: "/exhibitor/v1/cluster/list"
storm.cluster.mode: "distributed" # can be distributed or local
storm.local.mode.zmq: false
storm.thrift.transport: "org.apache.storm.security.auth.SimpleTransportPlugin"
storm.principal.tolocal: "org.apache.storm.security.auth.DefaultPrincipalToLocal"
storm.group.mapping.service: "org.apache.storm.security.auth.ShellBasedGroupsMapping"
storm.group.mapping.service.params: null
storm.messaging.transport: "org.apache.storm.messaging.netty.Context"
storm.nimbus.retry.times: 5
storm.nimbus.retry.interval.millis: 2000
storm.nimbus.retry.intervalceiling.millis: 60000
storm.auth.simple-white-list.users: []
storm.auth.simple-acl.users: []
storm.auth.simple-acl.users.commands: []
storm.auth.simple-acl.admins: []
storm.cluster.state.store: "org.apache.storm.cluster_state.zookeeper_state_factory"
storm.meta.serialization.delegate: "org.apache.storm.serialization.GzipThriftSerializationDelegate"
storm.codedistributor.class: "org.apache.storm.codedistributor.LocalFileSystemCodeDistributor"
storm.workers.artifacts.dir: "workers-artifacts"
storm.health.check.dir: "healthchecks"
storm.health.check.timeout.ms: 5000

### nimbus.* configs are for the master
nimbus.host: "{{nimbus_host}}"

# nimbus.seeds : ["localhost"]
nimbus.thrift.port: 6627
nimbus.thrift.threads: 64
nimbus.thrift.max_buffer_size: 1048576
nimbus.childopts: "{{nimbus_childopts}}"
nimbus.task.timeout.secs: 30
nimbus.supervisor.timeout.secs: 60
nimbus.monitor.freq.secs: 10
nimbus.cleanup.inbox.freq.secs: 600
nimbus.inbox.jar.expiration.secs: 3600
nimbus.code.sync.freq.secs: 120
nimbus.task.launch.secs: 120
nimbus.file.copy.expiration.secs: 600
nimbus.topology.validator: "org.apache.storm.nimbus.DefaultTopologyValidator"
topology.min.replication.count: 1
topology.max.replication.wait.time.sec: 60
nimbus.credential.renewers.freq.secs: 600
nimbus.queue.size: 100000
scheduler.display.resource: false

### ui.* configs are for the master

ui.host: 0.0.0.0
ui.port: {{ui_port}}
ui.childopts: "{{ui_childopts}}"
ui.actions.enabled: true
ui.filter: null
ui.filter.params: null
ui.users: null
ui.header.buffer.bytes: 4096
ui.http.creds.plugin: org.apache.storm.security.auth.DefaultHttpCredentialsPlugin
ui.http.x-frame-options: DENY


logviewer.port: {{logviewer_port}}
logviewer.childopts: "{{logviewer_childopts}}"
logviewer.cleanup.age.mins: 10080
logviewer.appender.name: "A1"
logviewer.max.sum.worker.logs.size.mb: 4096
logviewer.max.per.worker.logs.size.mb: 2048

logs.users: null

drpc.port: 3772
drpc.worker.threads: 64
drpc.max_buffer_size: 1048576
drpc.queue.size: 128
drpc.invocations.port: 3773
drpc.invocations.threads: 64
drpc.request.timeout.secs: 600
drpc.childopts: "-Xmx768m"
drpc.http.port: 3774
drpc.https.port: -1
drpc.https.keystore.password: ""
drpc.https.keystore.type: "JKS"
drpc.http.creds.plugin: org.apache.storm.security.auth.DefaultHttpCredentialsPlugin
drpc.authorizer.acl.filename: "drpc-auth-acl.yaml"
drpc.authorizer.acl.strict: false

transactional.zookeeper.root: "/transactional"
transactional.zookeeper.servers: null
transactional.zookeeper.port: null

## blobstore configs
supervisor.blobstore.class: "org.apache.storm.blobstore.NimbusBlobStore"
supervisor.blobstore.download.thread.count: 5
supervisor.blobstore.download.max_retries: 3
supervisor.localizer.cache.target.size.mb: 10240
supervisor.localizer.cleanup.interval.ms: 600000

nimbus.blobstore.class: "org.apache.storm.blobstore.LocalFsBlobStore"
nimbus.blobstore.expiration.secs: 600

storm.blobstore.inputstream.buffer.size.bytes: 65536
client.blobstore.class: "org.apache.storm.blobstore.NimbusBlobStore"
storm.blobstore.replication.factor: 3
# For secure mode we would want to change this config to true
storm.blobstore.acl.validation.enabled: false

### supervisor.* configs are for node supervisors
# Define the amount of workers that can be run on this machine. Each worker is assigned a port to use for communication
supervisor.slots.ports:
{% for port in supervisor_slots_ports %}
  - {{port}}
{% endfor %}
supervisor.childopts: "{{supervisor_childopts}}"
supervisor.run.worker.as.user: false
#how long supervisor will wait to ensure that a worker process is started
supervisor.worker.start.timeout.secs: 120
#how long between heartbeats until supervisor considers that worker dead and tries to restart it
supervisor.worker.timeout.secs: 30
#how many seconds to sleep for before shutting down threads on worker
supervisor.worker.shutdown.sleep.secs: 1
#how frequently the supervisor checks on the status of the processes it's monitoring and restarts if necessary
supervisor.monitor.frequency.secs: 3
#how frequently the supervisor heartbeats to the cluster state (for nimbus)
supervisor.heartbeat.frequency.secs: 5
supervisor.enable: true
supervisor.supervisors: []
supervisor.supervisors.commands: []
supervisor.memory.capacity.mb: 3072.0
#By convention 1 cpu core should be about 100, but this can be adjusted if needed
# using 100 makes it simple to set the desired value to the capacity measurement
# for single threaded bolts
supervisor.cpu.capacity: 400.0

### worker.* configs are for task workers
worker.heap.memory.mb: 768
worker.childopts: "{{worker_childopts}}"
worker.gc.childopts: ""

# Unlocking commercial features requires a special license from Oracle.
# See http://www.oracle.com/technetwork/java/javase/terms/products/index.html
# For this reason, profiler features are disabled by default.
worker.profiler.enabled: false
worker.profiler.childopts: "-XX:+UnlockCommercialFeatures -XX:+FlightRecorder"
worker.profiler.command: "flight.bash"
worker.heartbeat.frequency.secs: 1

# check whether dynamic log levels can be reset from DEBUG to INFO in workers
worker.log.level.reset.poll.secs: 30

# control how many worker receiver threads we need per worker
topology.worker.receiver.thread.count: 1

task.heartbeat.frequency.secs: 3
task.refresh.poll.secs: 10
task.credentials.poll.secs: 30

# now should be null by default
topology.backpressure.enable: false
backpressure.disruptor.high.watermark: 0.9
backpressure.disruptor.low.watermark: 0.4

zmq.threads: 1
zmq.linger.millis: 5000
zmq.hwm: 0

storm.messaging.netty.server_worker_threads: 1
storm.messaging.netty.client_worker_threads: 1
storm.messaging.netty.buffer_size: 5242880 #5MB buffer

storm.messaging.netty.max_retries: 300
storm.messaging.netty.max_wait_ms: 1000
storm.messaging.netty.min_wait_ms: 100


storm.messaging.netty.transfer.batch.size: 262144
# Sets the backlog value to specify when the channel binds to a local address
storm.messaging.netty.socket.backlog: 500


storm.messaging.netty.authentication: false

# Default plugin to use for automatic network topology discovery
storm.network.topography.plugin: org.apache.storm.networktopography.DefaultRackDNSToSwitchMapping

# default number of seconds group mapping service will cache user group
storm.group.mapping.service.cache.duration.secs: 120

### topology.* configs are for specific executing storms
topology.enable.message.timeouts: true
topology.debug: false
topology.workers: 1
topology.acker.executors: null
topology.eventlogger.executors: 0
topology.tasks: null
# maximum amount of time a message has to complete before it's considered failed
topology.message.timeout.secs: 30
topology.multilang.serializer: "org.apache.storm.multilang.JsonSerializer"
topology.shellbolt.max.pending: 100
topology.skip.missing.kryo.registrations: false
topology.max.task.parallelism: null
topology.max.spout.pending: null
topology.state.synchronization.timeout.secs: 60
topology.stats.sample.rate: 0.05
topology.builtin.metrics.bucket.size.secs: 60
topology.fall.back.on.java.serialization: true
topology.worker.childopts: null
topology.worker.logwriter.childopts: "-Xmx64m"
topology.executor.receive.buffer.size: 1024 #batched
topology.executor.send.buffer.size: 1024 #individual messages
topology.transfer.buffer.size: 1024 # batched
topology.tick.tuple.freq.secs: null
topology.worker.shared.thread.pool.size: 4
topology.spout.wait.strategy: "org.apache.storm.spout.SleepSpoutWaitStrategy"
topology.sleep.spout.wait.strategy.time.ms: 1
topology.error.throttle.interval.secs: 10
topology.max.error.report.per.interval: 5
topology.kryo.factory: "org.apache.storm.serialization.DefaultKryoFactory"
topology.tuple.serializer: "org.apache.storm.serialization.types.ListDelegateSerializer"
topology.trident.batch.emit.interval.millis: 500
topology.testing.always.try.serialize: false
topology.classpath: null
topology.environment: null
topology.bolts.outgoing.overflow.buffer.enable: false
topology.disruptor.wait.timeout.millis: 1000
topology.disruptor.batch.size: 100
topology.disruptor.batch.timeout.millis: 1
topology.disable.loadaware: false
topology.state.checkpoint.interval.ms: 1000

# Configs for Resource Aware Scheduler

# Recommended range of 0-29 but no hard limit set.
topology.priority: 29
topology.component.resources.onheap.memory.mb: 128.0
topology.component.resources.offheap.memory.mb: 0.0
topology.component.cpu.pcore.percent: 10.0
topology.worker.max.heap.size.mb: 768.0
topology.scheduler.strategy: "org.apache.storm.scheduler.resource.strategies.scheduling.DefaultResourceAwareStrategy"
resource.aware.scheduler.eviction.strategy:
"org.apache.storm.scheduler.resource.strategies.eviction.DefaultEvictionStrategy"
resource.aware.scheduler.priority.strategy:
"org.apache.storm.scheduler.resource.strategies.priority.DefaultSchedulingPriorityStrategy"

dev.zookeeper.path: "/tmp/dev-storm-zookeeper"

pacemaker.host: "localhost"
pacemaker.port: 6699
pacemaker.base.threads: 10
pacemaker.max.threads: 50
pacemaker.thread.timeout: 10
pacemaker.childopts: "-Xmx1024m"
pacemaker.auth.method: "NONE"
pacemaker.kerberos.users: []

#default storm daemon metrics reporter plugins
storm.daemon.metrics.reporter.plugins:
     - "org.apache.storm.daemon.metrics.reporters.JmxPreparableReporter"


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
