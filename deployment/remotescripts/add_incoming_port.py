##############################################################################
#
# Copyright 2016 KPMG Advisory N.V. (unless otherwise stated)
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

port = sys.argv[1]
afile = '/etc/sysconfig/iptables'
f = open(afile)
l = f.read()
f.close()
l = l.replace('-A INPUT', '-A INPUT -m state --state NEW -m tcp -p tcp --dport ' + str(port) + ' -j ACCEPT\n-A INPUT')
f = open(afile, 'w')
f.write(l)
f.close()
