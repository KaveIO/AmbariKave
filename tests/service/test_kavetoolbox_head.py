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
import os


class TestKaveToolbox(base.LDTest):
    service = "KaveToolbox-HEAD"
    checklist = ['/opt/KaveToolbox', '/etc/profile.d/kave.sh', '/opt/root',
                 '/opt/eclipse', '/opt/anaconda', '/opt/kettle']
    ostype = "Centos6"

    def deploy_ktb(self, ambari):
        lD = self.pre_check()
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        stdout = lD.run_quiet(
            deploy_dir + "/add_toolbox.py " + ambari.host + " $AWSSECCONF --ip --workstation --not-strict")
        self.assertTrue("installing toolbox in background process (check before bringing down the machine)" in stdout,
                        "Failed to install KaveToolbox from git, check: " + ' '.join(ambari.sshcmd()))
        return True

    def wait_for_ktb(self, ambari):
        import time
        time.sleep(15)
        rounds = 1
        flag = False
        while rounds <= 60:
            try:
                stdout = ambari.run(" tail -n 4 inst.stdout ")
                if ("Successful install" in stdout):
                    flag = True
                    break
                stdout = ambari.run(" cat inst.stderr ")
                stdout = ''.join([s if ord(s) < 128 else '#' for s in stdout])
                self.assertFalse("exception" in stdout or "error" in stdout.lower(),
                                 "Errors detected in head KaveToolbox installation \n"
                                 + stdout + "\n-----------------\n"
                                 + ' '.join(
                                     ambari.sshcmd()))
            except RuntimeError:
                pass
            rounds = rounds + 1
            time.sleep(60)
        self.assertTrue(flag, "Installation of KaveToolbox not completed after 60 minutes")
        return True

    def check(self, ambari):
        super(TestKaveToolbox, self).check(ambari)
        # check the installed directories
        stdout = ambari.run("bash -c \"source /opt/KaveToolbox/pro/scripts/KaveEnv.sh ; which python; which root;\"")
        self.assertTrue("/opt/root/pro" in stdout and "/opt/anaconda/pro/bin" in stdout,
                        "Environment sourcing fails to find installed packages")
        # check other features
        try:
            ambari.run("which vncserver")
            ambari.run("which emacs")
            ambari.run("which firefox")
        except RuntimeError:
            self.assertTrue(False, "Could not find vncserver/emacs/firefox installed as workstation components")
        env = ambari.run("cat /opt/KaveToolbox/pro/scripts/KaveEnv.sh")
        self.assertTrue("#!/bin/bash" in env,
                        "Environment file not created correctly\n" + env + "\n-----------------\n" + ' '.join(
                            ambari.sshcmd()))
        self.assertTrue("/opt/anaconda/pro" in env,
                        "Environment file not created correctly, no anaconda part\n" + env + "\n-----------------\n"
                        + ' '.join(
                            ambari.sshcmd()))
        self.assertTrue("/opt/KaveToolbox/pro" in env,
                        "Environment file not created correctly, no KaveToolbox part\n" + env +
                        "\n-----------------\n" + ' '.join(
                            ambari.sshcmd()))
        self.assertTrue("/opt/eclipse/pro" in env,
                        "Environment file not created correctly, no eclipse part\n"
                        + env + "\n-----------------\n"
                        + ' '.join(ambari.sshcmd()))
        return True

    def runTest(self):
        """
        Check that we can install the head of KaveToolbox on aws machines
        Three OSes are possible, Centos6, Centos7 and Ubuntu14
        """
        # create remote machine
        import os
        import sys

        lD = self.pre_check()
        ambari, iid = (None, None)
        if self.ostype == "Centos6":
            ambari, iid = self.deploy_dev()
        else:
            ambari, iid = self.deploy_os(self.ostype)
            if self.ostype.startswith("Ubuntu"):
                ambari.run('apt-get update')
        self.deploy_ktb(ambari)
        self.wait_for_ktb(ambari)
        return self.check(ambari)


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
