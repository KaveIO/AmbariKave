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
from kavecommon import ApacheScript


class Twiki(ApacheScript):

    def install(self, env):
        import params
        import kavecommon as kc

        super(Twiki, self).install(env)
        env.set_params(params)
        kc.copyCacheOrRepo('TWiki-6.0.0.zip')
        Execute("mkdir -p " + params.install_dir)
        Execute("unzip -o -q TWiki-6.0.0.zip -d " + params.install_dir)
        Execute("mkdir -p " + params.install_dir + 'authtest')
        kc.chownR(params.install_dir, "apache")
        Execute("cp " + params.install_dir + "/bin/LocalLib.cfg.txt " + params.install_dir + "/bin/LocalLib.cfg")
        Execute("chown apache:apache " + params.install_dir + "/bin/LocalLib.cfg")
        self.configure(env)

    def configure(self, env):
        import params
        import kavecommon as kc

        env.set_params(params)
        File(params.install_dir + "bin/LocalLib.cfg",
             content=Template("LocalLib.cfg.txt"),
             mode=0644
             )
        env.set_params(params)
        File(params.install_dir + "authtest/index.html",
             content=Template("authtest.html.j2"),
             mode=0644
             )

        orignal_config = False

        if os.path.exists(params.install_dir + "lib/LocalSite.cfg"):
            with open(params.install_dir + "lib/LocalSite.cfg", 'r') as fp:
                orignal_config = fp.readlines()

        with open(params.install_dir + "lib/LocalSite.cfg", 'w') as fp:
            newstuff = Template("LocalSite.cfg.j2").get_content()
            fp.write(newstuff)
            dontclobber = [n.split('=')[0].strip() for n in newstuff.split(
                '\n') if len(n.strip()) and len(n.split('=')[0].strip())]
            if not orignal_config or not len(orignal_config):
                fp.write('\n1;\n')
            else:
                fp.write(''.join([o for o in orignal_config if o.split('=')[0].strip() not in dontclobber]))

        Execute('chmod 644 %slib/LocalSite.cfg' % params.install_dir)

        File('/etc/httpd/conf.d/twiki_httpd.conf',
             content=InlineTemplate(params.twiki_httpd_conf),
             mode=0600
             )
        Execute('chown apache:apache /etc/httpd/conf.d/twiki_httpd.conf')
        File('/etc/httpd/conf.d/authtest_httpd.conf',
             content=InlineTemplate(params.authtest_httpd_conf),
             mode=0600
             )
        Execute('chown apache:apache /etc/httpd/conf.d/authtest_httpd.conf')
        super(Twiki, self).configure(env)


# modify both the file and you are done
if __name__ == "__main__":
    Twiki().execute()
