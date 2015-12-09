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
import base
import unittest


class TestKaveToolbox(base.LDTest):
    service = "KaveToolbox-HEAD"
    checklist = ['/opt/KaveToolbox', '/etc/profile.d/kave.sh', '/opt/root', '/opt/eclipse', '/opt/anaconda',
                 '/opt/kettle']
    ostype = "Centos6"

    def runTest(self):
        # create remote machine
        import os
        import sys

        lD = self.preCheck()
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        ambari, iid = (None, None)
        if self.ostype == "Centos6":
            ambari, iid = self.deployDev()
        else:
            ambari, iid = self.deployOS(self.ostype)
            if self.ostype.startswith("Ubuntu"):
                ambari.run('apt-get update')
        stdout = lD.runQuiet(
            deploy_dir + "/add_toolbox.py " + ambari.host + " $AWSSECCONF --ip --workstation --not-strict")
        self.assertTrue("installing toolbox in background process (check before bringing down the machine)" in stdout,
                        "Failed to install KaveToolbox from git, check: " + ' '.join(ambari.sshcmd()))
        # clean the existing blueprint ready for re-install
        import time

        time.sleep(15)
        rounds = 1
        flag = False
        while rounds <= 60:
            stdout = ambari.run(" tail -n 4 inst.stdout ")
            if ("Successful install" in stdout):
                flag = True
                break
            stdout = ambari.run(" cat inst.stderr ")
            self.assertFalse("xception" in stdout or "rror" in stdout,
                             "Errors detected in head KaveToolbox installation \n" + stdout + "\n-----------------\n"
                             + ' '.join(
                                 ambari.sshcmd()))
            rounds = rounds + 1
            time.sleep(60)
        self.assertTrue(flag, "Installation of KaveToolbox not completed after 60 minutes")
        self.check(ambari)
        # check the installed directories
        stdout = ambari.run("bash -c \"source /opt/KaveToolbox/scripts/KaveEnv.sh ; which python; which root;\"")
        self.assertTrue("/opt/root/pro" in stdout and "/opt/anaconda/bin" in stdout,
                        "Environment sourcing fails to find installed packages")
        # check other features
        try:
            ambari.run("which vncserver")
            ambari.run("which emacs")
            ambari.run("which firefox")
        except RuntimeError:
            self.assertTrue(False, "Could not find vncserver/emacs/firefox installed as workstation components")
        env = ambari.run("cat /opt/KaveToolbox/scripts/KaveEnv.sh")
        self.assertTrue("#!/bin/bash" in env,
                        "Environment file not created correctly\n" + env + "\n-----------------\n" + ' '.join(
                            ambari.sshcmd()))
        self.assertTrue("/opt/anaconda" in env,
                        "Environment file not created correctly, no anaconda part\n" + env + "\n-----------------\n"
                        + ' '.join(
                            ambari.sshcmd()))
        self.assertTrue("/opt/KaveToolbox/bin" in env,
                        "Environment file not created correctly, no KaveToolbox part\n" + env +
                        "\n-----------------\n" + ' '.join(
                            ambari.sshcmd()))
        self.assertTrue("/opt/eclipse" in env,
                        "Environment file not created correctly, no eclipse part\n"
                        + env + "\n-----------------\n"
                        + ' '.join(ambari.sshcmd()))
        return


if __name__ == "__main__":
    import sys

    verbose = False
    if "--verbose" in sys.argv:
        verbose = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    test1 = TestKaveToolbox()
    test1.debug = verbose
    if len(sys.argv) > 1:
        test1.ostype = sys.argv[1]
    suite = unittest.TestSuite()
    suite.addTest(test1)
    base.run(suite)
