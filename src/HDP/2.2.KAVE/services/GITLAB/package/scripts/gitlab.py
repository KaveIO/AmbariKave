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
import os
import shutil

from resource_management import *


class Gitlab(Script):
    package = 'gitlab-7.6.2_omnibus.5.3.0.ci.1-1.el6.x86_64.rpm'
    installer_cache_path = '/tmp/'

    def install(self, env):
        #TODO: instead of throwing an exception here, I should enter gitlabs into the existing postgre database
        # correctly
        if os.path.exists('/var/lib/pgsql/data/pg_hba.conf'):
            raise SystemError(
                "You appear to already have a default postgre database installed (probably you're trying to put "
                "Gitlabs on the same machine as Ambari). This type of operation is not implemented yet. If this is "
                "very annoying for you please email us.")
        import params
        import kavecommon as kc

        self.install_packages(env)
        env.set_params(params)

        kc.copyCacheOrRepo(self.package, cache_dir=self.installer_cache_path)
        Execute('rpm --replacepkgs -i %s' % self.package)
        self.configure(env)

    def start(self, env):
        self.configure(env)
        Execute('gitlab-ctl start')

    def stop(self, env):
        Execute('gitlab-ctl stop')

    def configure(self, env):
        import params

        env.set_params(params)

        File(params.gitlab_conf_file,
             content=Template("gitlab.rb.j2"),
             mode=0600
             )

        Execute('gitlab-ctl reconfigure')

    def status(self, env):
        Execute('gitlab-ctl status')


if __name__ == "__main__":
    Gitlab().execute()
