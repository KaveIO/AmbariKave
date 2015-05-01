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


class TestCluster(base.LDTest):
    def runTest(self):
        # create remote machine
        import os
        import sys

        lD = self.preCheck()
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        pref = os.path.dirname(__file__) + "/blueprints/" + self.service
        a = os.path.exists(pref + ".aws.json")
        b = os.path.exists(pref + ".blueprint.json")
        c = os.path.exists(pref + ".cluster.json")
        if not a or not b or not c:
            raise ValueError(
                "Incomplete description for creating " + self.service + " .aws " + str(a) + " .blueprint " + str(
                    b) + " .cluster " + str(c))
        stdout = lD.runQuiet(
            deploy_dir + "/aws/up_aws_cluster.py Test-" + self.service + " " + pref + ".aws.json  --not-strict")
        self.assertTrue(stdout.strip().split("\n")[-2].startswith("Complete, created:"),
                        "failed to create cluster, \n" + stdout)
        connectcmd = ""
        for line in range(len(stdout.split('\n'))):
            if "ambari connect remotely with" in stdout.split("\n")[line]:
                connectcmd = stdout.split("\n")[line + 1].strip()
        adict = stdout.split("\n")[-2].replace("Complete, created:", "")
        exec ("adict = " + adict)
        iid, ip = adict["ambari"]
        self.assertTrue(ip in connectcmd)
        jsondat = open(os.path.expanduser(os.environ["AWSSECCONF"]))
        import json

        acconf = json.loads(jsondat.read())
        jsondat.close()
        keyfile = acconf["AccessKeys"]["SSH"]["KeyFile"]
        self.assertTrue(keyfile in connectcmd or os.path.expanduser(keyfile) in connectcmd,
                        "wrong keyfile seen in (" + connectcmd + ")")
        ambari = lD.remoteHost("root", ip, keyfile)
        ambari.register()
        self.waitForAmbari(ambari)
        if self.branch:
            ambari.run("AmbariKave/dev/pull-update.sh " + self.branch)
        self.deployBlueprint(ambari, pref + ".blueprint.json", pref + ".cluster.json")
        return self.check(ambari)


if __name__ == "__main__":
    import sys

    verbose = False
    if "--verbose" in sys.argv:
        verbose = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    branch = None
    if "--branch" in sys.argv:
        branch = "__service__"
        sys.argv = [s for s in sys.argv if s != "--branch"]
    if "--this-branch" in sys.argv:
        branch = "__local__"
        sys.argv = [s for s in sys.argv if s != "--this-branch"]
    if len(sys.argv) < 2:
        raise KeyError("You must specify which service to test")
    service = sys.argv[1]
    test = TestCluster()
    test.service = service
    test.debug = verbose
    test.branch = branch
    test.checklist = []
    if len(sys.argv) > 2:
        test.checklist = sys.argv[2:]
    suite = unittest.TestSuite()
    suite.addTest(test)
    base.run(suite)
