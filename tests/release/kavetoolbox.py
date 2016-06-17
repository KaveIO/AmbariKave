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
import kavecommon as kc
import sys
import os

sys.path.append(os.path.dirname(__file__) + '/../service')
import test_kavetoolbox_head


class TestKaveToolboxRelease(test_kavetoolbox_head.TestKaveToolbox):
    """
    Simple test class to check if the released version of KTB installer works.
    Derived class from the existing service test, thereby saving a looot of code
    duplication in this test.
    Centos6/7 and Ubuntu can all be tested.
    """
    service = "KaveToolbox-Release"
    version = "2.1-Beta"

    def deploy_ktb(self, ambari):
        if self.ostype.lower().startswith("centos"):
            ambari.run("yum -y install wget curl tar zip unzip gzip rsync")
        else:
            ambari.run("apt-get install -y wget curl tar zip unzip gzip rsync")
        ambari.run("wget http://repos:kaverepos@repos.dna.kpmglab.com/"
                   + "noarch/KaveToolbox/" + self.version + "/kavetoolbox-installer-" + self.version + ".sh")
        ambari.run("rm -rf inst.* ")
        ambari.run("nohup bash kavetoolbox-installer-" + self.version
                   + ".sh --workstation --quiet > inst.stdout 2> inst.stderr < /dev/null & ")
        return True


if __name__ == "__main__":
    import sys

    verbose = False
    if "--verbose" in sys.argv:
        verbose = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    test1 = TestKaveToolboxRelease()
    test1.debug = verbose
    if len(sys.argv) > 1:
        test1.ostype = sys.argv[1]
    suite = unittest.TestSuite()
    suite.addTest(test1)
    base.run(suite)
