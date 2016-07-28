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


class mockD(object):
    """
    A dictionary whose get item method actually sets items also, so that there is never a keyerror on getting.
    """

    def __init__(self):
        self.adict = {}

    def __getitem__(self, key):
        try:
            return self.adict[key]
        except KeyError:
            try:
                if key in ["hostname", 'hdfs-site', 'yarn-site']:
                    return 'mock.mock.mock'
                elif key.endswith('_host'):
                    return 'mock.mock.mock'
                elif key.endswith('_hosts'):
                    return ['mock.mock.mock']
                elif 'pass' in key and not key.endswith('initial_user_passwords'):
                    return genrand()
            except AttributeError:
                pass
            self.__setitem__(key, mockD())
            return self.adict[key]

    def __setitem__(self, key, val):
        self.adict[key] = val


class Script(object):

    @staticmethod
    def get_config():
        return mockD()

    @staticmethod
    def get_tmp_dir():
        return '/tmp/nonono.mock.mock.mock'

    @staticmethod
    def get_component_from_role(a, b):
        return b

    @staticmethod
    def is_hdp_stack_greater_or_equal(scriptnum):
        return True
