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
import sys

host = sys.argv[1]
afile = '/etc/ambari-agent/conf/ambari-agent.ini'
f = open(afile)
ls = f.readlines()
f.close()
newls = []
for line in ls:
    if line.startswith("hostname="):
        newls.append("hostname=" + host)
        continue
    newls.append(line.strip())
f = open(afile, 'w')
f.write('\n'.join(newls))
f.close()
