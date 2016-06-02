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
    version = "2.1-Beta-Pre"

    def runTest(self):
        """
        Run the packaged installer on a blank Centos6 machine
        """
        import os

        lD = self.pre_check()
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        self.ostype = "Centos6"
        ambari, iid = self.deploy_os(self.ostype)
        ambari.run("yum -y install wget curl tar zip unzip gzip rsync")
        ambari.run("mkdir -p /etc/kave/")
        ambari.run("/bin/echo http://repos:kaverepos@repos.dna.kpmglab.com/ >> /etc/kave/mirror")
        ambari.run("wget http://repos:kaverepos@repos.dna.kpmglab.com/"
                   + "centos6/AmbariKave/" + self.version + "/ambarikave-installer-centos6-" + self.version + ".sh")
        ambari.run("nohup bash ambarikave-installer-centos6-" + self.version
                   + ".sh > inst.stdout 2> inst.stderr < /dev/null & ")
        self.wait_for_ambari(ambari)
        return True


if __name__ == "__main__":
    import sys

    verbose = False
    if "--verbose" in sys.argv:
        verbose = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    test1 = TestAmbariKaveRelease()
    test1.debug = verbose
    suite = unittest.TestSuite()
    suite.addTest(test1)
    base.run(suite)
