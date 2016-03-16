#!/usr/bin/env bash
#
# This file is a derivative of a file provided by the original Ambari Project.
# This file was originally created with the following licence:
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

mysqldservice=$1
mysqldbuser=$2
mysqldbpasswd=$3

# The restart (not start) is required to pick up mysql configuration changes made by sed
# during install, in case mysql is already started. The changes are required by Hive later on.
# 2.0!
if  [ -e /var/lib/ambari-agent/ambari-sudo.sh ]; then
	/var/lib/ambari-agent/ambari-sudo.sh service $mysqldservice restart
	#Is this really expected to work? it needs the sudo wrapper as in removeMysqlUser
	echo "Creating database if not already existing"
	sudo -u mysql mysql -u root -e " CREATE DATABASE IF NOT EXISTS sonar CHARACTER SET utf8 COLLATE utf8_general_ci;"

	echo "Removing users with empty name"
	sudo -u mysql mysql -u root -e "DELETE FROM mysql.user WHERE user='';"

	echo "Adding user $mysqldbuser@%"
	sudo -u mysql mysql -u root -e "CREATE USER '$mysqldbuser'@'%' IDENTIFIED BY '$mysqldbpasswd';"
	sudo -u mysql mysql -u root -e "GRANT ALL PRIVILEGES ON sonar.* TO '$mysqldbuser'@'%';"

	sudo -u mysql mysql -u root -e "flush privileges;"
else
	# 1.7!
	service $mysqldservice restart
	echo "Creating database if not already existing"
	su mysql -s /bin/bash - -c "mysql -u root -e 'CREATE DATABASE IF NOT EXISTS sonar CHARACTER SET utf8 COLLATE utf8_general_ci;'"

	echo "Removing users with empty name"
	su mysql -s /bin/bash - -c "mysql -u root -e \"DELETE FROM mysql.user WHERE user='';\""

	for ahost in '%' 'localhost'; do
		echo "Adding user $mysqldbuser@$ahost"
		su mysql -s /bin/bash - -c "mysql -u root -e \"CREATE USER '$mysqldbuser'@'$ahost' IDENTIFIED BY '$mysqldbpasswd';\""
		su mysql -s /bin/bash - -c "mysql -u root -e \"GRANT ALL PRIVILEGES ON sonar.* TO '$mysqldbuser'@'$ahost';\""
		su mysql -s /bin/bash - -c "mysql -u root -e 'flush privileges;'"
	done

fi