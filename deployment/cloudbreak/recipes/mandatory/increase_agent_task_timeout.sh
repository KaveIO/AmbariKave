##############################################################################
#
# Copyright 2018 KPMG Advisory N.V. (unless otherwise stated)
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
sed -i -e 's/agent.task.timeout=900/agent.task.timeout=3600/g' /etc/ambari-server/conf/ambari.properties
sed -i -e 's/agent.stack.retry.tries=5/agent.stack.retry.tries=20/g' /etc/ambari-server/conf/ambari.properties

systemctl stop ambari-server
systemctl start ambari-server