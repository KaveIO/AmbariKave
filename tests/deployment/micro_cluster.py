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
import unittest
import sys
import base


class MicroCluster(base.LDTest):

    def runTest(self):
        """
        Create a single centos instance with the up_aws_cluster script, the minimal test of this script
        """
        import os

        lD = self.preCheck()
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        blueprint_dir = os.path.realpath(os.path.dirname(__file__) + '/blueprints/')
        import kaveaws as lA
        region = lA.detectRegion()
        clusterfile = "micro.aws.json"
        if region.startswith("ap"):
            clusterfile = "microtokyo.aws.json"
        stdout = self.deploycluster(blueprint_dir + '/' + clusterfile, cname="TestDeploy")
        self.assertTrue(stdout.strip().split("\n")[-2].startswith("Complete, created:"),
                        "failed to generate cluster, \n" + stdout)
        connectcmd = ""
        for line in range(len(stdout.split('\n'))):
            if "testing-001 connect remotely with" in stdout.split("\n")[line]:
                connectcmd = stdout.split("\n")[line + 1].strip()
        adict = stdout.split("\n")[-2].replace("Complete, created:", "")
        # try interpreting as json
        import json
        adict = base.d2j(adict)
        iid, ip = adict["testing-001"]
        self.assertTrue(ip in connectcmd)
        jsondat = open(os.path.expanduser(os.environ["AWSSECCONF"]))
        import json

        acconf = json.loads(jsondat.read())
        jsondat.close()
        keyfile = acconf["AccessKeys"]["SSH"]["KeyFile"]
        self.assertTrue(keyfile in connectcmd or os.path.expanduser(keyfile) in connectcmd,
                        "wrong keyfile seen in (" + connectcmd + ")")
        ahost = lD.remoteHost("root", ip, keyfile)
        ahost.register()
        stdout = ahost.run("cat /etc/resolv.conf")
        self.assertTrue("kave.io" in stdout,
                        "Incomplete resolv.conf, did you create a new vpc with a correct DNS? (" + connectcmd + ")")
        ahost.run("yum -y install bind-utils")
        stdout = ahost.run("host ns.kave.io")
        self.assertTrue("has address" in stdout, "Lookup broken on ns.kave.io! (" + connectcmd + ")")
        stdout = ahost.run("host testing-001.kave.io")
        self.assertTrue("has address" in stdout, "Lookup broken on testing-001.kave.io! (" + connectcmd + ")")
        stdout = ahost.run("host test-001.kave.io")
        self.assertTrue("has address" in stdout, "Lookup broken on test-001.kave.io! (" + connectcmd + ")")
        import kaveaws as lA

        privip = lA.privIP(iid)
        stdout = ahost.run("host " + privip)
        self.assertTrue("domain name pointer" in stdout,
                        "Reverse lookup broken on testing-001.kave.io! (" + connectcmd + ")")


def suite(verbose=False, branch="__local__"):
    suite = unittest.TestSuite()
    test = MicroCluster()
    test.debug = verbose
    test.branch = branch
    test.branchtype = branch
    suite.addTest(test)
    return suite


if __name__ == "__main__":
    verbose = False
    if "--verbose" in sys.argv:
        verbose = True
    branch = "__local__"
    if "--branch" in sys.argv:
        branch = "__service__"
        sys.argv = [s for s in sys.argv if s != "--branch"]
    if "--this-branch" in sys.argv:
        branch = "__local__"
        sys.argv = [s for s in sys.argv if s != "--this-branch"]
    base.run(suite(verbose, branch))
