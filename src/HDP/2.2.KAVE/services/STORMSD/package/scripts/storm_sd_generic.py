##############################################################################
#
# Copyright 2015 KPMG N.V. (unless otherwise stated)
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
import kavecommon as kc
import os
import subprocess
from resource_management import *


class StormGeneric(Script):

    def install(self,env):
        self.install_packages(env)
        self.installStorm(env)
        self.configure(env)

    def installStorm(self, env):
        #install ZeroMQ which is prerequisite for storm
        user_exist = os.system('grep storm /etc/passwd > /dev/null')
        if user_exist != 0:
            kc.copyCacheOrRepo('zeromq-2.1.7-1.el6.x86_64.rpm')
            Execute('yum install -y zeromq-2.1.7-1.el6.x86_64.rpm')
            Execute('groupadd -g 53001 storm')
            Execute('mkdir -p /app/home')
            Execute('useradd -u 53001 -g 53001 -d /app/home/storm -s /bin/bash storm -c "Storm service account"')
            Execute('chmod 700 /app/home/storm')

        storm_dir_present = os.path.isdir('/usr/local/storm')
        if not storm_dir_present:
            #download storm
            kc.copyCacheOrRepo('storm-9.3.zip')
            Execute('unzip -o -q storm-9.3.zip -d /usr/local')
            Execute('mv /usr/local/apache-storm-0.9.3* /usr/local/storm-0.9.3')
            Execute('chown -R storm:storm /usr/local/storm-0.9.3')
            Execute('ln -s /usr/local/storm-0.9.3 /usr/local/storm')

        storm_home_dir = os.path.isdir('/app/storm')
        if not storm_home_dir:
            #Creating local directory for storm
            Execute('mkdir -p /app/storm')
            Execute('chown -R storm:storm /app/storm')
            Execute('chmod 750 /app/storm')
        storm_log_dir = os.path.isdir('/var/log/storm')
        if not storm_home_dir:
            #Creating local directory for storm
            Execute('mkdir -p /var/log/storm')
            Execute('chown -R storm:storm /var/log/storm')
            Execute('chmod 750 /var/log/storm')

    def configure(self,env):
        return configureStorm(self,env)

    def configureStorm(self,env):
        import params
        env.set_params(params)
        File(params.storm_conf_file,
             content=Template("storm.yaml"),
             mode=0644
             )


class StormGenericSD(StormGeneric):
    PROG = None

    def ctlcmd(self, cmd, bg=False):
        stat, stdout, stderr = (0, "", "")
        if not bg:
            stat, stdout, stderr = kc.mycmd('supervisorctl ' + cmd + ' storm-' + self.PROG)
            if stat or "error" in stdout.lower() or "error" in stderr.lower() or "failed" in stdout.lower() or \
                            "failed" in stderr.lower() or 'refused' in stdout or 'refused' in stderr:
                self.fail_with_error(cmd + ' ' + self.PROG + ' Failed!' + stdout + stderr)
        else:
            stat, stdout, stderr = kc.mycmd('supervisorctl ' + cmd + ' storm-' + self.PROG + ' &')
        return stdout

    def install(self,env):
        self.install_packages(env)
        self.installStorm(env)
        self.installSupervisor(env)
        self.configure(env)

    def installSupervisor(self, env):
        import params

        params.PROG = self.PROG
        env.set_params(params)
        if not os.path.exists('/etc/supervisord.conf'):
            File('/etc/supervisord.conf',
                 content=Template("supervisord.conf.j2"),
                 mode=0755
                 )
        Package('epel-release')
        Package('supervisor')
        Execute('chkconfig supervisord on')

    def start(self, env):
        stat, stdout, stderr = kc.mycmd("service supervisord status")
        if "running" not in stdout:
            Execute('service supervisord start')
        self.ctlcmd('start', bg=True)
        import time

        time.sleep(5)
        stdout = self.ctlcmd('status')
        if "START" not in stdout and "RUNNING" not in stdout:
            self.fail_with_error('Start Failed!' + stdout + stderr)
        return True

    def stop(self, env):
        self.ctlcmd('stop', bg=True)

    def restart(self, env):
        self.ctlcmd('restart', bg=True)

    def status(self, env):
        Execute('service supervisord status')
        self.ctlcmd('status')

    def configure(self,env):
        self.configureStorm(env)
        return self.configureSD(env)

    def configureSD(self, env):
        import params
        params.PROG = self.PROG
        env.set_params(params)
        if not os.path.exists('/etc/supervisord.conf'):
            File('/etc/supervisord.conf',
                 content=Template("supervisord.conf.j2"),
                 mode=0755
                 )
        Execute('mkdir -p /etc/supervisord.d/')
        File("/etc/supervisord.d/" + self.PROG + ".conf",
             content=Template("prog.conf"),
             mode=0644
             )
        Execute("cat /etc/supervisord.d/*.conf >> /etc/supervisord.conf")
        kc.chownR('/etc/supervisord.d/', 'storm')
