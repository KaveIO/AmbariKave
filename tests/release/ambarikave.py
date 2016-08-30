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
import base
import unittest


class TestAmbariKaveRelease(base.LDTest):
    service = "AmbariKave-Release"
    version = "2.2-Beta-Pre"
    checklist = ['/var/lib/ambari-server/resources/stacks/HDP/2.4.KAVE',
                 '/var/lib/ambari-server/resources/stacks/HDP/2.4.KAVE'
                 '/services/JENKINS/package/scripts/kavecommon.py']
    ostype = "Centos6"

    def runTest(self):
        """
        Run the packaged installer on a blank Centos machine
        """
        import os

        lD = self.pre_check()
        import kaveaws as lA
        ambari, iid = self.deploy_os(self.ostype)
        if self.ostype in ["Centos6"]:
            # work around for problematic default DNS settings :S
            ambari.run("yum -y install bind-utils")
            out = ambari.run("host " + ambari.host)
            ambari.run('python rename_me.py ' + out.split()[-1].split('.')[0] + ' '
                       + '.'.join(out.split()[-1].split('.')[1:-1]))
            # now the machine will be re-renamed with the public dns
        ambari.run("yum -y install wget curl tar zip unzip gzip rsync")
        lD.disable_security(ambari)
        ambari.run("mkdir -p /etc/kave/")
        ambari.run("rm -rf inst.*")
        ambari.run("echo http://repos:kaverepos@repos.dna.kpmglab.com/ >> /etc/kave/mirror")
        lD.deploy_our_soft(ambari, self.version, repo="http://repos:kaverepos@repos.dna.kpmglab.com")
        import time
        time.sleep(10)
        self.wait_for_ambari(ambari, rounds=15, check_inst=["inst.stdout", "inst.stderr"])
        return self.check(ambari)


if __name__ == "__main__":
    import sys

    verbose = False
    if "--verbose" in sys.argv:
        verbose = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    test1 = TestAmbariKaveRelease()
    test1.debug = verbose
    if len(sys.argv) > 1:
        test1.ostype = sys.argv[1]
    suite = unittest.TestSuite()
    suite.addTest(test1)
    base.run(suite)
