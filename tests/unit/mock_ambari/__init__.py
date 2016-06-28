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
"""Simple mock for tests where we use src packages.
"""
import mock


class Excecute(object):
    pass


class mockD(dict):
    """
    A dictionary whose get item method actually sets items also, so that there is never a keyerror on getting.
    """

    def __getitem__(self, key):
        try:
            return super(self, dict).__getitem__[key]
        except KeyError:
            if key in ["hostname"]:
                return 'mock'
            elif key.endswith('_host'):
                return 'mock'
            elif key.endswith('_hosts'):
                return ['mock']
            self.__setitem__(key, mockD())
            return super(self, dict).__getitem__[key]


class Script(object):

    def get_config(self):
        return mockD()


def default(a, b):
    return b
