##############################################################################
#
# Copyright 2016 KPMG N.V. (unless otherwise stated)
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


class Hue(Script):
    mandatory_conf_dirs = ["/etc/hue/conf.empty", "/etc/hue/conf"]
    optional_conf_dirs = ["/etc/hue/conf.d"]

    def install(self, env):
        import params

        env.set_params(params)
        self.install_packages(env)
        self.configure(env)

    def configure(self, env):
        import params
        import kavecommon as kc

        env.set_params(params)
        Execute('chkconfig --levels 235 hue on')
        edit_dirs = self.mandatory_conf_dirs
        for mdir in self.mandatory_conf_dirs:
            Execute("mkdir -p " + mdir)
        for odir in self.optional_conf_dirs:
            if os.path.exists(odir):
                edit_dirs.append(odir)
        for edir in edit_dirs:
            edir = os.path.realpath(edir)
            Execute('chmod -R 755 ' + edir)
            File(edir + '/hue.ini', content=InlineTemplate(params.hue_ini), mode=0600)
            File(edir + '/hue_httpd.conf', content=InlineTemplate(params.hue_httpd_conf), mode=0644)
            kc.chown_r(edir, 'hue')

    def start(self, env):
        self.configure(env)
        Execute("service hue start")

    def stop(self, env):
        Execute('service hue stop')

    def status(self, env):
        print Execute('service hue status')


if __name__ == "__main__":
    Hue().execute()
