#!/usr/bin/env python
"""
This file is a derivative of a file provided by the original Ambari Project.
This file was originally created with the following licence:

Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import mysql_users
from resource_management import *

from mysql_utils import mysql_configure


class Mysql(Script):
    def install(self, env):
        import params

        self.install_packages(env)
        Package('mysql-server')
        self.configure(env)

    def clean(self, env):
        import params

        env.set_params(params)
        mysql_users.mysql_deluser()

    def configure(self, env):
        import params

        env.set_params(params)
        mysql_configure()

    def start(self, env):
        import params
        self.configure(env)

        Execute('service %s start' % params.daemon_name)

    def stop(self, env):
        import params

        Execute('service %s stop' % params.daemon_name)

    def status(self, env):
        import status_params

        Execute('pgrep -l "^%s$"' % status_params.daemon_name)


if __name__ == "__main__":
    Mysql().execute()