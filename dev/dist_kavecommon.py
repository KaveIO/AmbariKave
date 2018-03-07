#! /usr/bin/env python
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
"""
Copy kavecommon from src/shared into each service directory
"""
import os
import glob
import sys
import shutil

destination = os.path.realpath(sys.argv[1])
if not os.path.exists(destination):
    raise IOError("Cannot distribute to somewhere that does not exist")

servicedirs = []
for i in range(4):
    servicedirs = servicedirs + glob.glob(destination + ('/*' * i) + '/package/scripts')

servicedirs = list(set([s for s in servicedirs if len(s)]))
if len(sys.argv) > 2:
    topcopy = sys.argv[2]
else:
    topcopy = os.path.dirname(__file__) + '/../src/shared/kavecommon.py'

# copy from all files to all destinations
for s in servicedirs:
    if os.path.isdir(s):
        shutil.copy(topcopy, s)
