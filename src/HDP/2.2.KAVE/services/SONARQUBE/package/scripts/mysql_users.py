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

from resource_management import *

# Used to add hive access to the needed components
def mysql_adduser():
    import params

    File(params.mysql_adduser_path,
         mode=0755,
         content=StaticFile('addMysqlUser.sh')
         )
    Execute('bash -x %s %s %s %s' % (params.mysql_adduser_path, params.daemon_name,
                                     params.sonar_database_user_name, params.sonar_database_user_passwd),
            tries=3,
            try_sleep=5,
            path='/usr/sbin:/sbin:/usr/local/bin:/bin:/usr/bin'
            )


# Removes hive access from components
def mysql_deluser():
    import params

    File(params.mysql_deluser_path,
         mode=0755,
         content=StaticFile('removeMysqlUser.sh')
         )
    Execute('bash -x %s %s %s %s' % (params.mysql_removeuser_path, params.daemon_name,
                                     params.sonar_database_user_name, params.sonar_database_user_passwd),
            tries=3,
            try_sleep=5,
            path='/usr/sbin:/sbin:/usr/local/bin:/bin:/usr/bin',
            )
