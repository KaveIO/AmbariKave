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
import os

from resource_management import *
<<<<<<< HEAD
import kavecommon as kc
=======
>>>>>>> 98254f88e398bba8fe9772ff25df5423508bc78c
#from kavecommon import ApacheScript
#from resource_management.core.exceptions import ComponentIsNotRunning


<<<<<<< HEAD
class Airflow(kc.ApacheScript):
=======
class Airflow():
>>>>>>> 98254f88e398bba8fe9772ff25df5423508bc78c
    # status file is needed to know if this service was started, stores the name of the index file
    #status_file = '/etc/kave/kavelanding_started'
    airflow_config_path = "/root/airflow/airflow.cfg"
    airflow_webserver_pidfile_path = "/root/airflow/airflow-webserver.pid"
<<<<<<< HEAD
    #airflow_config_path = "/etc/httpd/conf.d/ganglia.conf"
=======
    airflow_config_path = "/etc/httpd/conf.d/ganglia.conf"
>>>>>>> 98254f88e398bba8fe9772ff25df5423508bc78c


    def install(self, env):
        print "Installing Airflow"
        import params
<<<<<<< HEAD
=======
        import kavecommon as kc
>>>>>>> 98254f88e398bba8fe9772ff25df5423508bc78c
        import os
        super(Airflow, self).install(env)
        kc.install_epel()
        Execute('curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"')
        Package('python get-pip.py')
        Execute('yum -y update')
<<<<<<< HEAD
        Execute('sudo yum install -y postgresql-devel')
        Execute('yum install -y python-devel mysql-devel')
=======
        Execute('sudo yum install postgresql-devel y')
        Execute('yum install python-devel mysql-devel y')
>>>>>>> 98254f88e398bba8fe9772ff25df5423508bc78c

        #Package('python-devel')
        #Package('python-pip')

        Execute('sudo yum -y install gcc gcc-c++ libffi-devel mariadb-devel cyrus-sasl-devel')

        Execute('pip install airflow')

        self.configure(env)

    def configure(self, env):
        import params
        import os
<<<<<<< HEAD
        env.set_params(params)
        File(self.airflow_config_path,
             content=InlineTemplate(params.airflow_conf),
             mode=0755
             )
        File(self.airflow_webserver_pidfile_path,
             content=Template("airflow.j2"),
             mode=0755
             )

=======
        import kavecommon as kc
        env.set_params(params)
        #self.write_html(env)
>>>>>>> 98254f88e398bba8fe9772ff25df5423508bc78c
        super(Airflow, self).configure(env)

    def start(self, env):
        if not os.path.exists(os.path.dirname(self.status_file)):
            os.makedirs(os.path.dirname(self.status_file))
        import params
        import os
        Execute('airflow initdb')
        Execute('airflow webserver -p 8080')
        Execute('airflow scheduler')

        self.configure(env)
        super(KaveLanding, self).start(env)
        # Write the location of the index file into the status file
        if os.path.exists(params.www_folder + '/index.html'):
            with open(self.status_file, 'w') as fp:
                fp.write(params.www_folder + '/index.html')

    def stop(self, env):
        import params
        import os

        Execute('cat $AIRFLOW_HOME/airflow-webserver.pid | xargs kill -9')
<<<<<<< HEAD
        super(Airflow, self).stop(env)


    #def status(self, env):
        # Read from the status file, and check the index exists
        #if not os.path.exists(self.status_file):
            #raise ComponentIsNotRunning()
        #klfile = None
        #with open(self.status_file) as fp:
            #klfile = fp.read().split()[0].strip()
        #if len(klfile) < 5 or (not os.path.exists(klfile)):
            #raise ComponentIsNotRunning()
        #super(KaveLanding, self).status(env)


if __name__ == "__main__":
    Airflow().execute()
=======


    def status(self, env):
        # Read from the status file, and check the index exists
        if not os.path.exists(self.status_file):
            raise ComponentIsNotRunning()
        klfile = None
        with open(self.status_file) as fp:
            klfile = fp.read().split()[0].strip()
        if len(klfile) < 5 or (not os.path.exists(klfile)):
            raise ComponentIsNotRunning()
        super(KaveLanding, self).status(env)


if __name__ == "__main__":
    KaveLanding().execute()
>>>>>>> 98254f88e398bba8fe9772ff25df5423508bc78c
