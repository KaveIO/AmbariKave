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
###############################################################################
# wrapper to install epel
#

yum info epel-release 2>/dev/null | grep installed
epel_not_installed=$?
set -e
#set -o pipefail #not a good idea, causes failures even in actual successful situations

os=`uname -r`
flavor='centos'
if [[ "$os" == *"el7"* ]]; then
	os="centos7"
	if [ -e "/etc/redhat-release" ]; then
		release=`cat /etc/redhat-release`
		if [[ "$release" == *" 7."* ]]; then
			if [[ "$release" == "Red Hat"* ]]; then
				flavor="redhat"
			fi
		fi
	fi
elif [[ "$os" == *"el6"* ]]; then
	os="centos6"
else
	echo "This script is not tested/ready for this operating system"
fi

# install requests library for python
if [[ "$flavor" == "centos" ]]; then
	yum install -y epel-release
else
	if [[ $epel_not_installed -ne 0 ]]; then
		wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
		yum -y install epel-release-latest-7.noarch.rpm
	fi
fi
# necessary step to update epel and HDP cached repos
yum clean all