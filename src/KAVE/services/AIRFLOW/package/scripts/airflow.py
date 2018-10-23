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
import kavecommon as kc
from kavecommon import ApacheScript
from resource_management.core.exceptions import ComponentIsNotRunning


class Airflow(kc.ApacheScript):
    airflow_config_path = "/usr/opt/local/airflow/airflow.cfg"
    airflow_webserver_pidfile_path = "/run/airflow/webserver.pid"
    systemd_env_init_path = "/etc/sysconfig/airflow"
    systemd_schd_unitfile_path = "/usr/lib/systemd/system/airflow-scheduler.service"
    systemd_ws_unitfile_path = "/usr/lib/systemd/system/airflow-webserver.service"
    # This is a hack to overcome a certain restriction in airflow which requires
    # the argument to be quoted

    quote_fix = ('sed -i \'/MARKER_EXPR = originalTextFor(MARKER_EXPR())("marker")/c'
                 '\MARKER_EXPR = originalTextFor(MARKER_EXPR(""))("marker")\''
                 ' `find /usr/lib/python* -name requirements.py`'
                 )

    def install(self, env):
        print "Installing Airflow"
        import params
        import os
        super(Airflow, self).install(env)
        kc.install_epel()

        Execute('curl --tlsv1.2 "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"')
        Execute('python get-pip.py')
        Execute('pip install -U pip setuptools')
        # Create airflow config/home dir and set permissions
        Execute('id -u airflow &>/dev/null || useradd -r -s /sbin/nologin airflow')
        Execute('mkdir -p /usr/opt/local/airflow')
        Execute('chown airflow:root /usr/opt/local/airflow')
        # Create directory to store the pid file and set permissions:
        Execute('mkdir -p /run/airflow')
        Execute('chown airflow:root /run/airflow')
        # Set the AIRFLOW_HOME environment variable. Echoing it at the end of /etc/environment
        # is just one of the possible approaches.
        Execute('echo "AIRFLOW_HOME=/usr/opt/local/airflow" >> /etc/environment')
        Execute('yum remove python2-psutil -y')
        # Install base airflow
        Execute('pip install airflow==1.7')
        # Add Airflow Hive operatiors. We should consider installing "airflow[all]"
        # for getting all possible features
        Execute('pip install airflow[hive]==1.7')

        self.configure(env)

    def configure(self, env):
        import params
        import os
        env.set_params(params)
        File(self.airflow_config_path,
             content=InlineTemplate(params.airflow_conf),
             mode=0755
             )
        File(self.systemd_env_init_path,
             content=Template("airflow"),
             mode=0755
             )
        File(self.systemd_schd_unitfile_path,
             content=Template("airflow-scheduler.service"),
             mode=0755
             )
        File(self.systemd_ws_unitfile_path,
             content=Template("airflow-webserver.service"),
             mode=0755
             )

        super(Airflow, self).configure(env)
        Execute("sed -i -e '/Defaults    requiretty/{ s/.*/# Defaults    requiretty/ }' /etc/sudoers")
        Execute(self.quote_fix)
        Execute("sudo -u airflow airflow initdb")

    def start(self, env):
        import params
        import os

        self.configure(env)
        Execute('systemctl start airflow-webserver')
        Execute('systemctl start airflow-scheduler')

    def stop(self, env):
        import params
        import os

        Execute('systemctl stop airflow-webserver')
        Execute('systemctl stop airflow-scheduler')

    def restart(self, env):

        self.configure(env)
        Execute('systemctl restart airflow-webserver')
        Execute('systemctl restart airflow-scheduler')

    def status(self, env):
        import params
        import os
        import subprocess

        check = subprocess.Popen('systemctl status airflow-webserver', shell=True)
        check.wait()
        if int(check.returncode) != 0:
            raise ComponentIsNotRunning()
        return True


if __name__ == "__main__":
    Airflow().execute()
