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

#this is a post recipe!
libdir=/usr/hdp/2.6.1.0-129/hadoop
dest=/var/lib/ambari-server/resources/views/work
for view in $(ls $dest); do
    cp $libdir/hadoop-azure-datalake* $libdir/azure-data-lake-store-sdk* "$dest/$view/WEB-INF/lib/"
done

