#!/bin/bash
##############################################################################
#
# Copyright 2015 KPMG N.V. (unless otherwise stated)
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
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#abort at first failure
set -e
# This should be the way, but regrettably this file is broken and will mess the installation up (misses some repos)
# wget http://public-repo-1.hortonworks.com/ambari/centos6/1.x/updates/1.6.1/ambari.repo
# sudo cp ambari.repo /etc/yum.repos.d

# The above two lines are temporarily replaced by this:
cp $CURRENT_DIR/repo/ambari.repo /etc/yum.repos.d/

bash $CURRENT_DIR/install_snippet.sh
if [[ $? -ne 0 ]]; then
	echo 'error running installation snippet!'
	exit 1
fi
