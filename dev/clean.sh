#! /bin/bash
##############################################################################
#
# Copyright 2016 KPMG N.V. (unless otherwise stated)
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
echo "This will completely destroy your local ambari installation and database."
read -p "Are you sure? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "OK, sleeping 5 secs in case you change your mind"
    sleep 5
else
	echo "Thank goodness, exiting"
	exit 0
fi

ambari-server stop
ambari-agent stop
sleep 5
yum -y erase ambari-agent ambari-server
su - postgres bash -c 'psql -c "drop database ambari"; psql -c "drop database ambarirca";'
rm -rf /var/lib/ambari-server
rm -rf /var/lib/ambari-agent
rm -rf /etc/yum.repos.d/ambari.repo

