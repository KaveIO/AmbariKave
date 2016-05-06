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
import base
import unittest


class TestCluster(base.LDTest):

    def runTest(self):
        """
        A complete integration test.
        Providing that the files X.aws.json, X.cluster.json and X.blueprint.json exist
        this test will check that the files make sense, and then create a cluster.
        After the cluster is ready, the blueprint and clusterfile will be submitted
        and the installation will be monitored to completion.

        Common problems are fixed with service restarts
        """
        # create remote machine
        import os
        import sys
        import json

        lD = self.pre_check()
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        pref = os.path.dirname(__file__) + "/blueprints/" + self.service
        self.verify_blueprint(pref + ".aws.json", pref + ".blueprint.json", pref + ".cluster.json")
        # Deploy the cluster
        if self.clustername == 'prod':
            self.clustername = self.service
        stdout = self.deploycluster(pref + ".aws.json", cname=self.clustername)
        ambari = self.remote_from_cluster_stdout(stdout)
        ambari.register()
        self.wait_for_ambari(ambari, ["inst.stdout", "inst.stderr"])
        self.pull(ambari)
        self.wait_for_ambari(ambari)
        self.deploy_blueprint(ambari, pref + ".blueprint.json", pref + ".cluster.json")
        return self.check(ambari)


class TestFreeIPACluster(TestCluster):
    """
    Add test of the createkeytabs script to the test of the FreeIPA cluster installation
    """

    def check(self, ambari):
        super(TestFreeIPACluster, self).check(ambari)
        import time
        import os
        import subprocess as sub
        if 'yes' not in ambari.run('bash -c "if [ -e createkeytabs.py ]; then echo \"yes\"; fi ;"'):
            time.sleep(60)
        import subprocess as sub
        pwd = ambari.run("cat admin-password")
        proc = sub.Popen(ambari.sshcmd() + ['kinit admin'], shell=False,
                         stdout=sub.PIPE, stderr=sub.PIPE, stdin=sub.PIPE)
        output, err = proc.communicate(input=pwd + '\n')
        self.assertFalse(proc.returncode, "Failed to kinit admin on this node "
                         + ' '.join(ambari.sshcmd())
                         + output + " " + err
                         )
        ambari.cp(os.path.dirname(__file__) + '/kerberostest.csv', 'kerberostest.csv')
        ambari.run("./createkeytabs.py ./kerberostest.csv")

if __name__ == "__main__":
    import sys

    verbose = False
    clustername = None
    if "--verbose" in sys.argv:
        verbose = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    branch = "__local__"
    if "--branch" in sys.argv:
        branch = "__service__"
        sys.argv = [s for s in sys.argv if s != "--branch"]
    if "--this-branch" in sys.argv:
        branch = "__local__"
        sys.argv = [s for s in sys.argv if s != "--this-branch"]
    if "--prod" in sys.argv:
        clustername = 'prod'
        sys.argv = [s for s in sys.argv if s != "--prod"]
    if len(sys.argv) < 2:
        raise KeyError("You must specify which blueprint/cluster to test")
    service = sys.argv[1]
    test = TestCluster()
    if service == "FREEIPA":
        test = TestFreeIPACluster()
    test.service = service
    test.debug = verbose
    test.clustername = clustername
    test.branch = branch
    test.branchtype = branch
    test.checklist = []
    if len(sys.argv) > 2:
        test.checklist = sys.argv[2:]
    suite = unittest.TestSuite()
    suite.addTest(test)
    base.run(suite)
