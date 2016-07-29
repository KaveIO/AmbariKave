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
# import mock
import random
import string
import core
from core import *
from libraries import default
from libraries import Script


def genrand():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(14))


class Excecute(object):
    pass


class Logger(object):
    sensitive_strings = {}
