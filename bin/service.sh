#!/bin/bash
##############################################################################
#
# Copyright 2016 KPMG Advisory N.V. (unless otherwise stated)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
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
function runHelp {
  echo "KAVE service install and management tool"
  echo "Usage: service.sh {install|reinstall|start|stop|list|configure|help|status} [SERVICE]"
  echo "	A local \$HOME/.netrc file must exist with the ambari credentials"
  echo "        [-a|--ambari AMBARI]		default: localhost"
  echo "        [-c|--cluster CLUSTER]		default: request from ambari"
  echo "        [-h|--host HOST]"
  echo ""
  echo "This is the main KAVE service managment tool. Idealy all the contained functionality should"
  echo "be a part of the graphical installer, since this is not up for it this tool fills in the "
  echo "gaps through some rest calls to the ambari server. The following functions are included:"
  echo "	install"
  echo " 	installs a service on the cluster."
  echo "	REQUIRES SERVICE, HOST"
  echo ""
  echo "	reinstall"
  echo "        reinstalls a services, only makes sense in a development environment."
  echo "        REQUIRES SERVICE, HOST"
  echo ""
  echo "	start"
  echo "        starts a service on the cluster. Installing or reinstalling does NOT trigger a start."
  echo "        REQUIRES SERVICE"
  echo ""
  echo "	stop"
  echo "        stops a service on the cluster. In Ambari stopping and installing a service is"
  echo "	indistinguishable so there could be some unexpected behaviour in this call."
  echo "        REQUIRES SERVICE"
  echo ""
  echo "	list"
  echo "	Lists the available services to install."
  echo ""
  echo "	configure"
  echo "	Creates and applies an new configuration for a service. Does NOT trigger a restart."
  echo "        REQUIRES SERVICE"
  echo ""
  echo "	help"
  echo "        displays this message."
  echo ""
  echo "	status"
  echo "        lists the status of this service on this machine."
  echo ""
}

function runAddService {
  echo "Adding a service"
  if [ "`curl --retry 5 -s -i --netrc http://$ambari:8080/api/v1/clusters/$cluster/services/$service -H "X-Requested-By:ambari" -w "%{http_code}" -o /dev/null`" = "404" ]; then
    echo "Adding the service to the cluster"
    curl --retry 5  -i -X POST --netrc -d '{"ServiceInfo":{"service_name":"'$service'"}}' http://$ambari:8080/api/v1/clusters/$cluster/services  -H "X-Requested-By:ambari"
    curl --retry 5  -i -X POST --netrc http://$ambari:8080/api/v1/clusters/$cluster/services/$service/components/$component  -H "X-Requested-By:ambari"
    echo
    echo "Sleeping for a bit..."
    sleep 5s
  fi
}

function runInstallService {
  echo "Installing the service"
  curl --retry 5  -i -X PUT --netrc -d '{"RequestInfo":{"context":"Install '$service'"},"Body":{"HostRoles":{"state":"INSTALLED"}}}' http://$ambari:8080/api/v1/clusters/$cluster/hosts/$host/host_components/$component -H "X-Requested-By:ambari"
  echo
  echo "Sleeping for a bit..."
  sleep 5s
}

function runInstallComponent {
  echo "Installing a component"
  curl --retry 5  -i -X POST --netrc http://$ambari:8080/api/v1/clusters/$cluster/hosts/$host/host_components/$component -H "X-Requested-By:ambari"
  echo
  echo "Sleeping for a bit..."
  sleep 5s
}

function runUninstallComponent {
  echo "Uninstalling a component"
  curl --retry 5  -i -X DELETE --netrc http://$ambari:8080/api/v1/clusters/$cluster/hosts/$host/host_components/$component -H "X-Requested-By:ambari"
  echo
  echo "Sleeping for a bit..."
  sleep 5s
}

function runStart {
  echo "Starting a service"
  curl --retry 5  -i -X PUT -d '{"RequestInfo":{"context":"Starting '$service'"},"Body":{"ServiceInfo":{"state":"STARTED"}}}' --netrc http://$ambari:8080/api/v1/clusters/$cluster/services/$service -H "X-Requested-By:ambari"
  echo
  echo "Sleeping for a bit..."
  sleep 5s
}

function runStop {
  echo "Stopping a service"
  curl --retry 5  -i -X PUT -d '{"RequestInfo":{"context":"Stopping '$service'"},"Body":{"ServiceInfo":{"state":"INSTALLED"}}}' --netrc http://$ambari:8080/api/v1/clusters/$cluster/services/$service -H "X-Requested-By:ambari"
  echo
  echo "Sleeping for a bit..."
  sleep 5s
}

function runStatus {
curl --retry 5  -i -X GET --netrc http://$ambari:8080/api/v1/clusters/$cluster/hosts/$host/host_components/$component -H "X-Requested-By:ambari" | grep state
}

function runConfigureService {
  result=""
  case $service in
    GITLAB)
    buildConfiguration gitlab gitlab_admin_password
      ;;
    TWIKI)
	buildConfiguration twiki ldap_bind_password
      ;;
    FREEIPA)
    buildConfiguration freeipa directory_password ldap_bind_password
      ;;
    KAVELANDING)
    buildConfiguration kavelanding AMBARI_ADMIN AMBARI_ADMIN_PASS
      ;;
    MAIL)
    buildConfiguration mail HOST_NAME HOST_DOMAIN MAIL_DIR
      ;;
    SONARQUBE)
    buildConfiguration sonar sonar_database_user_passwd
     ;;
    SONARQUBE_RUNNER)
    buildConfiguration sonar sonar_database_user_passwd
     ;;
    JENKINS)
	buildConfiguration jenkins JENKINS_ADMIN_PASSWORD
      ;;
    KAVENAGIOS)
	buildConfiguration kavenagios nagios_admin_password
      ;;

  esac
}

function buildConfiguration {
  # The first argument determines the configuration type. A bit obscure but will do for now.
  type=$1
  shift

  configuration=""
  for parameter in $@
  do
    echo "Value for $parameter?"
    read input
    if [ "$configuration" = "" ]; then
      configuration='"'$parameter'":"'$input'"'
    else
      configuration=$configuration',"'$parameter'":"'$input'"'
    fi
  done

  curl --retry 5  -i -X PUT -d '{"Clusters": {"desired_config": {"type": "'$type'", "tag": "version'`date +%Y%m%d%H%M%S`'", "properties": {'$configuration'}}}}' --netrc http://$ambari:8080/api/v1/clusters/$cluster -H "X-Requested-By:ambari"
}


function runList {
  echo "Known services:"
  echo "	GITLAB"
  echo "	KAVEGANGLIA"
  echo "	KAVENAGIOS"
  echo "	FREEIPA"
  echo "	KAVETOOLBOX"
  echo "	KAVELANDING"
  echo "	JBOSS"
  echo "	WILDFLY"
  echo "	MAIL"
  echo "	SONARQUBE"
  echo "	SONARQUBE_RUNNER"
  echo "	MONGODB"
  echo "	MONGODB_CLIENT"
  echo "	APACHE"
  echo "	ARCHIVA"
  echo "	JENKINS"
  echo "	STORMSD_DRPC_SERVER"
  echo "	STORMSD_CLIENT"
  echo "	TWIKI"
  echo "	AIRFLOW"
  echo ""
}

if [ $# -eq 0 ]; then
  runHelp
  exit
fi

# We are treating the first argument special. So we catch it and shift the rest of the arguments.
command="$1"
shift

# The second argument is special as well. This contains the service for which we will be doing something.
service="$1"
shift

args=$(getopt -l "ambari:,cluster:,host:" -o "a:c:h:" -- "$@")

eval set -- "$args"


while [ $# -ge 1 ]; do
  case "$1" in
    --)
      # No more options left.
      shift
      break
      ;;
    -a|--ambari)
      ambari="$2"
      shift
      ;;
    -c|--cluster)
      cluster="$2"
      shift
      ;;
    -h|--host)
      host="$2"
      shift
      ;;
  esac
  shift
done

if [ "$ambari" = "" ]; then
  ambari="localhost"
fi

if [ ! -f "$HOME/.netrc" ]; then
	echo "You must supply a local netrc file with the logon credentials"
	echo "File $HOME/.netrc does not exist or is unreadable"
	exit 1
fi

if [ "$cluster" = "" ]; then
  cluster="`curl --retry 5  -i -s --netrc http://$ambari:8080/api/v1/clusters | grep "cluster_name" | sed -r 's/^.*?"cluster_name" : "(.*?)".*$/\1/g'`"
fi
if [ $service = "GITLAB" ]; then
  component="GITLAB_SERVER"
elif [ $service = "FREEIPA" ]; then
  component="FREEIPA_SERVER"
elif [ $service = "FREEIPA_CLIENT" ]; then
  component="FREEIPA_CLIENT"
  service="FREEIPA"
elif [ $service = "KAVETOOLBOX" ]; then
  component="KAVETOOLBOXNODE"
elif [ $service = "KAVETOOLBOXGATE" ]; then
  service="KAVETOOLBOX"
  component="KAVETOOLBOXGATE"
elif [ $service = "KAVELANDING" ]; then
  component="KAVELANDING"
elif [ $service = "MONGODB" ]; then
	component="MONGODB_MASTER"
elif [ $service = "MONGODB_CLIENT" ]; then
	service="MONGODB"
	component="MONGODB_CLIENT"
elif [ $service = "APACHE" ]; then
	component="APACHE_WEB_MASTER"
elif [ $service = "JENKINS" ]; then
	component="JENKINS_MASTER"
elif [ $service = "JBOSS" ]; then
  component="JBOSS_APP_SERVER"
elif [ $service = "WILDFLY" ]; then
  component="WILDFLY_APP_SERVER"
elif [ $service = "MAIL" ]; then
  component="POSTFIX_SERVER"
elif [ $service = "GANGLIA" ]; then
  component="GANGLIA_SERVER"
elif [ $service = "KAVEGANGLIA" ]; then
  component="KAVEGANGLIA_SERVER"
elif [ $service = "KAVEGANGLIA_MONITOR" ]; then
  component="KAVEGANGLIA_MONITOR"
  service="KAVEGANGLIA"
elif [ $service = "GANGLIA_MONITOR" ]; then
  component="GANGLIA_MONITOR"
elif [ $service = "ARCHIVA" ]; then
  component="ARCHIVA_SERVER"
elif [ $service = "SONARQUBE" ]; then
  component="SONARQUBE_SERVER"
elif [ $service = "SONARQUBE_RUNNER" ]; then
  component="SONARQUBE_RUNNER"
elif [ $service = "STORMSD_DRPC_SERVER" ]; then
  service="STORMSD"
  component="STORMSD_DRPC_SERVER"
elif [ $service = "STORMSD_CLIENT" ]; then
  service="STORMSD"
  component="STORMSD_CLIENT"
elif [ $service = "TWIKI" ]; then
  component="TWIKI_SERVER"
elif [ $service = "NAGIOS" ]; then
  component="NAGIOS_SERVER"
elif [ $service = "KAVENAGIOS" ]; then
  component="KAVENAGIOS_SERVER"
elif [ $service = "KAVENAGIOS_MONITOR" ]; then
  service="KAVENAGIOS"
  component="KAVENAGIOS_MONITOR"
elif [ $service = "AMBARI_METRICS" ]; then
  component="METRICS_COLLECTOR"
elif [ $service = "ZOOKEEPER" ]; then
  component="ZOOKEEPER_SERVER"
elif [ $service = "METRICS" ]; then
  component="METRICS_COLLECTOR"
elif [ $service = "METRICS_MONITOR" ]; then
  service="AMBARI_METRICS"
  component="METRICS_MONITOR"
elif [ $service = "AIRFLOW" ]; then
  component="AIRFLOW_SERVER"
else
  echo "ERROR: unknown service caught: $service"
  runHelp
  exit 1
fi

# Running the main command switch and calling the functions that actually do stuff.
if [ $command = "install" ]; then
  runAddService
  runInstallComponent
  runConfigureService
  runInstallService
elif [ $command = "reinstall" ]; then
  runStop
  runUninstallComponent
  runInstallComponent
  runConfigureService
  runInstallService
elif [ $command = "start" ]; then
  runStart
elif [ $command = "stop" ]; then
  runStop
elif [ $command = "list" ]; then
  runList
elif [ $command = "configure" ]; then
  runConfigureService
elif [ $command = "status" ]; then
 runStatus
elif [ $command = "help" ]; then
  runHelp
else
  echo "ERROR: unknown command caught: $command"
  runHelp
  exit 1
fi
