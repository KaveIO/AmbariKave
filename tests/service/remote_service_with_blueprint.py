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


class TestServiceBlueprint(base.LDTest):

    def runTest(self):
        """
        The remote_blueprint test ups a dev machine and submits a blueprint to it.
        It monitors the status of the service specified with service.sh
        This can only work if the service to be monitored shares the same name as the blueprint
        """
        # create remote machine
        import os
        import sys
        import json

        lD = self.pre_check()
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        bp = os.path.dirname(__file__) + "/blueprints/" + self.service + ".blueprint.json"
        cf = os.path.dirname(__file__) + "/blueprints/default.cluster.json"
        af = os.path.dirname(__file__) + "/blueprints/default.aws.json"
        if not os.path.exists(bp):
            raise ValueError("No blueprint with which to install " + self.service)
        self.verify_blueprint(af, bp, cf)
        if self.service not in [s for s, d in base.find_services()]:
            raise ValueError(
                "This test can only work for blueprints where the name of the blueprint matches a known service. Else "
                "try remote_blueprint.py")
        ambari, iid = self.deploy_dev()
        # clean the existing blueprint ready for re-install
        self.pull(ambari)
        self.resetambari(ambari)
        self.deploy_blueprint(ambari, bp, cf)
        # wait for the install and then check if the directories etc. are there
        self.wait_for_service(ambari)
        self.check(ambari)


#####
# If you need to update this, go to the machine where this test fialed, and run ./AmbariKave/dev/scan.sh
#####
__kavelanding_plain__ = """Welcome to your KAVE
==================
* 'default' cluster
|--* Servers
|  |--* Ambari <a href='http://ambari:8080'>admin</a>
|  |--* Jenkins <a href='http://ambari:8888'>jenkins</a>
|  |--* Metrics (['ambari.kave.io'])
|  |--* Zookeeper (['ambari.kave.io'])
|
|--* Clients
|  |--* ambari.kave.io ['kavelanding', 'metrics_monitor', 'zookeeper_client']"""


#####
# If you need to update this, go to the machine where this test failed, and run ./AmbariKave/dev/scan.sh html
#####
__kavelanding_html__ = """<h3><font size=5px>'default' cluster</font></h3>
<b>Servers</b><p><ul>
  <li>Ambari <a href='http://ambari:8080'>admin</a></li>
  <li>Jenkins <a href='http://ambari:8888'>jenkins</a></li>
  <li>Metrics (['ambari.kave.io'])</li>
  <li>Zookeeper (['ambari.kave.io'])</li>
</ul><p><b>Clients</b><p><ul>
  <li>ambari.kave.io ['kavelanding', 'metrics_monitor', 'zookeeper_client']</li>
</ul>"""


def nowhite(astring):
    """
    return a string with no whitespace
    """
    return ''.join(astring.split())


class TestServiceKaveLanding(TestServiceBlueprint):

    def check(self, ambari):
        super(TestServiceKaveLanding, self).check(ambari)
        ppp = ambari.run("./[a,A]mbari[k,K]ave/dev/scan.sh")
        pph = ambari.run("./[a,A]mbari[k,K]ave/dev/scan.sh localhost html")
        self.assertTrue(nowhite(__kavelanding_plain__) == nowhite(ppp),
                        "Incorrect response from KaveLanding, scan.sh \n" + __kavelanding_plain__ +
                        "\n-----------\nnot equal to\n-------\n" + ppp)
        self.assertTrue(nowhite(__kavelanding_html__) in nowhite(pph),
                        "Incorrect response from KaveLanding, scan.sh" + __kavelanding_html__ + "\n-----------\nnot "
                                                                                                "equal to\n-------\n"
                        + pph)
        pph2 = ambari.run("curl --retry 5  -X GET http://localhost/", exit=False)
        self.assertTrue(nowhite(__kavelanding_html__) in nowhite(pph2), "KaveLanding page is incomplete")


class TestServiceFreeIPA(TestServiceBlueprint):

    def check(self, ambari):
        super(TestServiceFreeIPA, self).check(ambari)
        # Check kerberos
        import subprocess as sub
        import os
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


class TestServiceEskapade(TestServiceBlueprint):
    def check(self, ambari):
        super(TestServiceEskapade, self).check(ambari)

        import subprocess as sub

        test_type = "unit"
        ambari.run(" source /opt/KaveToolbox/pro/scripts/KaveEnv.sh;"
                   " cd /opt/Eskapade/*/tests; eskapade_trial")
        """
        TODO: Change the code above to the one below once run_tests.py returns error exit code if the tests fail.
        ambari.run("source /opt/KaveToolbox/pro/scripts/KaveEnv.sh;"
                   " source /opt/Eskapade/*/setup.sh;"
                   " run_tests.py {}".foramt(test_type))
        """


if __name__ == "__main__":
    import sys

    verbose = False
    branch = "__local__"
    if "--verbose" in sys.argv:
        verbose = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    if "--branch" in sys.argv:
        branch = "__service__"
        sys.argv = [s for s in sys.argv if s != "--branch"]
    if "--this-branch" in sys.argv:
        branch = "__local__"
        sys.argv = [s for s in sys.argv if s != "--this-branch"]
    if len(sys.argv) < 2:
        raise KeyError("You must specify which service to test")
    service = sys.argv[1]
    test = TestServiceBlueprint()
    if service == "KAVELANDING":
        test = TestServiceKaveLanding()
    if service == "ESKAPADE":
        test = TestServiceEskapade()
    test.service = service
    test.debug = verbose
    test.branch = branch
    test.checklist = []
    if len(sys.argv) > 2:
        test.checklist = sys.argv[2:]
    suite = unittest.TestSuite()
    suite.addTest(test)
    base.run(suite)
