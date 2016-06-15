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

kaveganglia_username = default('configurations/kaveganglia/kaveganglia_username', 'ganglia')
kaveganglia_clustername = default('configurations/kaveganglia/kaveganglia_clustername', 'KAVE')
kaveganglia_gridname = default('configurations/kaveganglia/kaveganglia_gridname', 'KAVE')
kaveganglia_port = default('configurations/kaveganglia/kaveganglia_port', '8649')
kaveganglia_xml_port = default('configurations/kaveganglia/kaveganglia_port', '8651')
kaveganglia_interactive_port = default('configurations/kaveganglia/kaveganglia_port', '8652')
kaveganglia_carbon_port = default('configurations/kaveganglia/kaveganglia_port', '2003')
kaveganglia_riemann_port = default('configurations/kaveganglia/kaveganglia_port', '5555')
kaveganglia_udp_port = default('configurations/kaveganglia/kaveganglia_port', '6343')
gangliaslave = default('/clusterHostInfo/kave_ganglia_monitor_hosts', ['unknown'])
kaveganglia_gmetad_uid = default('configurations/kaveganglia/kaveganglia_gmetad_uid', 'nobody')

www_folder = default('configurations/kaveganglia/www_folder', '/var/www/html/')
PORT = default('configurations/kaveganglia/PORT', '80')
servername = default('configurations/kaveganglia/servername', hostname)
if servername == "hostname":
    servername = hostname

template_000_default = default('configurations/kaveganglia/template_000_default', """# Created automatically with Ambari
# All manual changes will be undone in the case of a server restart
# Edit the template through the Ambari interface instead
TraceEnable Off
Listen {{PORT}}
ServerName "{{servername}}"
DocumentRoot "{{www_folder}}"
""")

kaveganglia_conf = default('configurations/kaveganglia/kaveganglia_conf', """
#
# Ganglia monitoring system php web frontend
#

Alias /ganglia /usr/share/ganglia

<Location /ganglia>
  Order deny,allow
  # Deny from all
  Allow from all
  Allow from 127.0.0.1
  Allow from ::1
  # Allow from .example.com
</Location>""")

kaveganglia_gmetad_conf = default('configurations/kaveganglia/kaveganglia_gmetad_conf', """
#!/bin/sh
#
# chkconfig: - 20 80
# description: gmetad startup script
#
GMETAD=/usr/sbin/gmetad
#GMETAD=/usr/local/ganglia-3.6.0/sbin/gmetad

. /etc/rc.d/init.d/functions

test -f /etc/sysconfig/gmetad && . /etc/sysconfig/gmetad

export RRDCACHED_ADDRESS

start() {
    [ -x $GMETAD ] || exit 5
    [ -f /etc/ganglia/gmetad.conf ] || exit 6
    echo -n "Starting GANGLIA gmetad: "
    #daemon $GMETAD
    daemon $GMETAD -c /etc/ganglia/gmetad.conf
    RETVAL=$?
    echo
    [ $RETVAL -eq 0 ] && touch /var/lock/subsys/gmetad
    return $RETVAL
}

stop() {
    echo -n "Shutting down GANGLIA gmetad: "
    killproc $GMETAD
    RETVAL=$?
    echo
    [ $RETVAL -eq 0 ] && rm -f /var/lock/subsys/gmetad
    return $RETVAL
}

restart() {
    stop
    start
}

reload() {
    restart
}

force_reload() {
    restart
}

rh_status() {
    status $GMETAD
}

rh_status_q() {
    rh_status >/dev/null 2>&1
}

usage() {
    echo "Usage: $0 {start|stop|status|restart|condrestart|try-restart|reload|force-reload}"
}

case "$1" in
    start)
    rh_status_q && exit 0
    $1
    ;;
    stop)
    rh_status_q || exit 1
    $1
    ;;
    restart)
    $1
    ;;
    reload)
    rh_status_q || exit 7
    $1
    ;;
    force-reload)
    force_reload
    ;;
    status)
    rh_status
    ;;
    condrestart|try-restart)
    rh_status_q || exit 0
    restart
    ;;
    usage)
    $1
    ;;
    *)
    usage
    exit 2
esac
exit $?""")
