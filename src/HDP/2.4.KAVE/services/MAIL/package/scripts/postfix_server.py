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


class PostfixSrv(Script):

    def install(self, env):
        import params

        self.install_packages(env)
        env.set_params(params)
        self.configure(env)
        self.start(env)

    def configure(self, env):
        import params

        env.set_params(params)
        Execute('chkconfig postfix on')
        File('/etc/postfix/main.cf',
             content=Template("main.cf.j2"),
             mode=0644
             )
        if not os.path.isfile('/etc/postfix/main.cf'):
            raise RuntimeError("Service not installed correctly")

    def start(self, env):
        self.configure(env)
        # TODO: Ambari 2.0 method should be replacing the below call
        # since Ambari 1.7.3 execute method never returns the control to script
        # So, we use nohup to detacht he start process, and we also need to redirect all the input and output
        Execute('nohup service postfix start 2> /dev/null > /dev/null < /dev/null &')

    def restart(self, env):
        """In cases where we run the starting and stopping in the background,
        a specific restart method is needed to ensure we wait between the two calls
        3s was seen to be enough in tests
        """
        self.stop(env)
        import time
        time.sleep(3)
        self.start(env)

    def stop(self, env):
        # TODO: Ambari 2.0 method should be replacing the below call
        # since Ambari 1.7.3 execute method never returns the control to script
        # So, we use nohup to detacht he start process, and we also need to redirect all the input and output
        Execute('nohup service postfix stop 2> /dev/null > /dev/null < /dev/null &')

    def status(self, env):
        # print "checking status..."
        Execute('service postfix status')


if __name__ == "__main__":
    PostfixSrv().execute()
