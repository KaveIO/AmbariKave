#!/bin/sh
##############################################################################
#
# Copyright 2017 KPMG Advisory N.V. (unless otherwise stated)
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
#This is a Cloudbreak pre-recipe for every host.

#Replace to avoid some weird behavior - my >> did not get respected.
arp -a | awk '{ gsub("\\(|)","", $2); split($1, arr, "."); print $2"\t"$1" "arr[1]}' | (echo -e "`ifconfig eth0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'`\t`hostname -f` `hostname -s`" && cat) | (echo -e "::1\t\tlocalhost localhost.localdomain localhost6 localhost6.localdomain6" && cat) | (echo -e "127.0.0.1\tlocalhost localhost.localdomain localhost4 localhost4.localdomain4" && cat) > /etc/hosts
