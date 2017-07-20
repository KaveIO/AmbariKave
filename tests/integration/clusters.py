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
from sys import stdout


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
        self.stdout = self.deploycluster(pref + ".aws.json", cname=self.clustername)
        ambari, _ = self.remote_from_cluster_stdout(self.stdout, 'ambari')
        ambari.register()
        self.wait_for_ambari(ambari, check_inst=["inst.stdout", "inst.stderr"])
        self.pull(ambari)
        self.wait_for_ambari(ambari)
        self.deploy_blueprint(ambari, pref + ".blueprint.json", pref + ".cluster.json")
        return self.check(ambari)


class TestFreeIPACluster(TestCluster):
    """
    Add test of the createkeytabs script to the test of the FreeIPA cluster installation
    """

    def checkipaserver(self, ipaserver):
        import time
        import os
        import subprocess as sub

        # Check kerberos
        if 'yes' in ipaserver.run('bash -c "if [ -e createkeytabs.py ]; then echo \"yes\"; fi ;"'):
            time.sleep(60)
        pwd = ipaserver.run("cat admin-password")
        proc = sub.Popen(ipaserver.sshcmd() + ['kinit admin'], shell=False,
                         stdout=sub.PIPE, stderr=sub.PIPE, stdin=sub.PIPE)
        output, err = proc.communicate(input=pwd + '\n')
        self.assertFalse(proc.returncode, "Failed to kinit admin on this node "
                         + ' '.join(ipaserver.sshcmd())
                         + output + " " + err
                         )
        ipaserver.cp(os.path.dirname(__file__) + '/kerberostest.csv', 'kerberostest.csv')
        ipaserver.run("./createkeytabs.py ./kerberostest.csv")

    def check(self, ambari):
        super(TestCluster, self).check(ambari)
        ipaserver, _ = self.remote_from_cluster_stdout(self.stdout, 'freeipa')
        self.checkipaserver(ipaserver)


class TestEskapadeCluster(TestCluster):
    def check_eskapade(self, host):
        """
        Run Eskapade integration tests.
        :param host: Eskapade host
        """
        import subprocess as sub
        test_type = "integration"
        proc = sub.Popen(host.sshcmd() + ["run_tests.py", test_type],
                         shell=False, stdout=sub.PIPE, stderr=sub.PIPE, universal_newlines=True)
        try:
            output, err = proc.communicate(timeout=600)
        except sub.TimeoutExpired as exc:
            self.assertTrue(False,
                            "Eskapade {} tests failed with timeout exception. Msg: {}.".format(test_type, exc.args))
            return
        self.assertTrue("FAILED" not in err, "Eskapade {} tests failed.".format(test_type))
        self.assertEqual(''.join(err.split())[-2:], "OK",
                         "Eskapade {} tests supposedly failed, did not get OK response.".format(test_type))

    def check(self, ambari):
        super(TestCluster, self).check(ambari)
        eskapade, _ = self.remote_from_cluster_stdout(self.stdout, 'eskapade')
        self.check_eskapade(eskapade)


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
    if service.startswith("FREEIPA"):
        test = TestFreeIPACluster()
    if service.startswith("ESKAPADE"):
        test = TestEskapadeCluster()
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
