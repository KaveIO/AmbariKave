##############################################################################
#
# Copyright 2015 KPMG N.V. (unless otherwise stated)
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
import remote_service_with_servicesh
import remote_service_with_blueprint
import remote_blueprint
import test_kavetoolbox_head
import base
import glob
import os

mods = [test_kavetoolbox_head, remote_service_with_servicesh, remote_service_with_blueprint]

# Ignore services which do not have a working default configuration, or have default ports which conflict with 8080
ignoreServices = ["GITLAB", "TWIKI", "FREEIPA", "JENKINS",
                  "JBOSS", "KAVELANDING", "HUE", "STORMSD", "SONARQUBE", "MAIL"]

services = [s for s, ds in base.findServices() if s not in ignoreServices]

checks = {"APACHE": ["http://localhost/"],
          "KAVETOOLBOX": ["/opt/KaveToolbox", '/etc/profile.d/kave.sh'],
          "KAVELANDING": ["http://localhost/"],
          "JENKINS": ["http://localhost:8888/login"],
          "JBOSS": ["http://localhost:8888/"],
          "TWIKI": ["http://localhost/twiki/"],
          "FREEIPA": ["https://ambari.kave.io/ipa/ui/"],
          "STORM": ["http://localhost:8744/"],
          "MONGODB": ["/var/lib/mongo"],
          "SONARQUBE": ["http://localhost:5051/"],
          "GITLAB": ["http://localhost:7777/"]
          }

# service.sh will do all services apart from the ignored services
serviceargs = []
for service in services:
    if service in checks:
        serviceargs.append([service] + checks[service])
    else:
        serviceargs.append(service)

# blueprints will just do all the defined blueprints


blueprints = glob.glob(os.path.dirname(__file__) + "/blueprints/*.blueprint.json")

blueprints = [b.split("/")[-1].split(".")[0] for b in blueprints]

all_services = [s for s, ds in base.findServices()]

blueprint_services = [b for b in blueprints if b in all_services]

blueprint_serviceargs = []
for service in blueprint_services:
    if service in checks:
        blueprint_serviceargs.append([service] + checks[service])
    else:
        blueprint_serviceargs.append(service)

blueprint_not_services = [b for b in blueprints if b not in blueprint_services]

blueprint_not_serviceargs = []
for service in blueprint_not_services:
    if service in checks:
        blueprint_not_serviceargs.append([service] + checks[service])
    else:
        blueprint_not_serviceargs.append(service)

modargs = {test_kavetoolbox_head: ['Centos6', 'Centos7', 'Ubuntu14'],
           remote_service_with_servicesh: serviceargs,
           remote_service_with_blueprint: blueprint_serviceargs,
           remote_blueprint: blueprint_not_serviceargs
           }

if __name__ == "__main__":
    base.parallel(mods, modargs)
