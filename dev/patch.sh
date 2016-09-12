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
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TARGET_DIR="/var/lib/ambari-server/resources/stacks/"
TARGET_DIR_COMMON="/var/lib/ambari-server/resources/common-services/"

rsync -razl "$CURRENT_DIR/../src/HDP/" $TARGET_DIR"/HDP"
rsync -razl "$CURRENT_DIR/../src/KAVE/" $TARGET_DIR"/HDP/2.4.KAVE22"
rsync -razl "$CURRENT_DIR/../src/common-services/" $TARGET_DIR_COMMON
python $CURRENT_DIR/dist_kavecommon.py $TARGET_DIR"/HDP"

# Patch Ambari Version Finding
pline="input = re.sub(r'\\.KAVE\\..*$', '', input)"
pline2="input = re.sub(r\'\\\\.KAVE\\\\..*\$\', \'\', input)"

#for versionpath in `find / -path '/*/resource_management/*/version.py' | cut -d" " -f 1`; do
#	grep -F "$pline" $versionpath || sed -i "48i\ \ \ \ $pline2" $versionpath
#done