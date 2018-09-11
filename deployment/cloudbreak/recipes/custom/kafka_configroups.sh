#!/bin/bash

#This is to have each broker to listen on its own public IP address. It is a POST to be added to each worker / Kafka node. Fetch its public IP, then ask for a custom config group where the property is overriden.
	
ambari_user="admin"
ambari_password="admin"
ambari_port=8080
ambari_host=$(grep hostname= /etc/ambari-agent/conf/ambari-agent.ini | cut -f 2 -d =)

n=`hostname -s`
num=${n: -1}

host_name=`hostname -f`

broker_ip=$(curl -s checkip.dyndns.org | sed -e 's/.*Current IP Address: //' -e 's/<.*$//')


#These are used elsewhere in the recipes but those must be self-contained, reasonably.
cluster_name () {
    echo "$(curl -u ${ambari_user}:${ambari_password} -i \
      -H 'X-Requested-By: ambari'  http://$ambari_host:$ambari_port/api/v1/clusters \
      2>/dev/null | sed -n 's/.*"cluster_name" : "\([^\"]*\)".*/\1/p')"
}

ambari_api_url () { 
	echo http://$ambari_host:$ambari_port/api/v1/clusters/$(cluster_name) 
}

post_data () {
	echo $(cat $1 | sed -e s"^%CLUSTER_NAME^$(cluster_name)^" -e s"^%NUM^$num^" -e s"^%HOST_NAME^$host_name^" -e s"^%IP^$broker_ip^")
}

make_request () {
	curl -i -H "X-Requested-By: ambari" -u ${ambari_user}:${ambari_password} -X POST -d "$(post_data $1)" "$(ambari_api_url)/$2"
}

kafka_configroup_json_template=$(cat <<EOF
[
   {
      "ConfigGroup": {
         "cluster_name": "%CLUSTER_NAME",
         "group_name": "broker_%NUM",
         "tag": "KAFKA_BROKER",
         "description": "KAFKA_BROKER configs for public listener",
         "hosts": [
            {
               "host_name": "%HOST_NAME"
            }
          ],
         "desired_configs": [
            {
               "type": "kafka-broker",
               "tag": "kafkalistenerconf_%NUM",
               "properties": { 
                   "advertised.listeners": "SSL://%IP:6668"
               }
            }                
        ]
     }
  }
]
EOF
)

kafka_broker_restart_json_template=$(cat <<EOF
{
    "RequestInfo": {
        "command": "RESTART",
        "context": "Restart Kafka Broker",
        "operation_level": {
            "level": "HOST_COMPONENT",
            "cluster_name": "%CLUSTER_NAME",
            "service_name": "KAFKA",
            "hostcomponent_name": "KAFKA_BROKER"
        }
    },
    "Requests/resource_filters": [{
        "service_name": "KAFKA",
        "component_name": "KAFKA_BROKER",
        "hosts": "%HOST_NAME"
    }]
}
EOF
)

echo "${kafka_configroup_json_template}" > kafka_configroup_json.template
make_request kafka_configroup_json.template config_groups

echo "${kafka_broker_restart_json_template}" > kafka_broker_restart_json.template
make_request kafka_broker_restart_json.template requests
