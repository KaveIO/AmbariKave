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


def gethostbyname(astr):
    return '0.0.0.0'


def error():
    raise NameError()


def timeout():
    raise SysError()


_GLOBAL_DEFAULT_TIMEOUT = 10
IPPROTO_TCP = ""
TCP_NODELAY = 1
has_ipv6 = True
