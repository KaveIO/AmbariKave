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

import random
import string

def genrand():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(14))

def default(a, b):
    if a in ["hostname", 'hdfs-site', 'yarn-site']:
        return 'mock.mock.mock'
    elif a.endswith('_host'):
        return 'mock.mock.mock'
    elif a.endswith('_hosts'):
        return ['mock.mock.mock']
    elif 'pass' in a and not a.endswith('initial_user_passwords'):
        return genrand()
    return b
