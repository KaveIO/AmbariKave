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


class TestAService(base.LDTest):

    def runTest(self):
        """
        The remote_blueprint test ups a dev machine and installs a service simply through service.sh.
        It monitors the status of the service specified with service.sh
        This can only be applied to services which have no forced parameters, i.e. where the default
        parameters work fine and are all that is needed.
        """
        # create remote machine
        import os
        import sys

        lD = self.pre_check()
        known = [s for s, d in base.find_services()]
        self.assertTrue(self.service in known, "The service " + self.service + " is unknown, check the case")
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        ambari, iid = self.deploy_dev()
        self.pull(ambari)
        # restart ganglia and nagios
        if self.branch:
            abranch = self.service
        for restart in ["METRICS_MONITOR", "AMBARI_METRICS", "ZOOKEEPER"]:
            stdout = self.servicesh(ambari, "stop", restart)
        for restart in ["ZOOKEEPER", "AMBARI_METRICS", "METRICS_MONITOR"]:
            self.wait_for_service(ambari, restart)
        import time

        time.sleep(15)
        # install the component on top of the blueprint
        stdout = self.servicesh(ambari, "install", self.service)
        self.assertTrue("IN_PROGRESS" in stdout or "InProgress" in stdout or "status\" : \"Accepted" in stdout,
                        "Was unable to install " + self.service + " through service.sh, (" + ' '.join(
                            ambari.sshcmd()) + ")")
        self.wait_for_service(ambari)
        return self.check(ambari)


#####
# If you need to update this, go to the machine where this test fialed, and run ./AmbariKave/dev/scan.sh
#####
__kavelanding_plain__ = """Welcome to your KAVE
==================
* 'default' cluster
|--* Servers
|  |--* Ambari <a href='http://ambari:8080'>admin</a>
|  |--* Jenkins <a href='http://ambari:8888'>jenkins</a>
|  |--* Metrics <a href='http://ambari:3000'>grafana</a>
|  |--* Metrics collector (['ambari.kave.io'])
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
  <li>Metrics <a href='http://ambari:3000'>grafana</a></li>
  <li>Metrics collector (['ambari.kave.io'])</li>
  <li>Zookeeper (['ambari.kave.io'])</li>
</ul><p><b>Clients</b><p><ul>
  <li>ambari.kave.io ['kavelanding', 'metrics_monitor', 'zookeeper_client']</li>
</ul>"""


class TestServiceKaveLanding(TestAService):

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


class TestServiceFreeIPA(TestAService):

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
        # check port number patching still applies correctly
        ambari.run("python "
                   "/var/lib/ambari-server/resources/stacks/HDP/*.KAVE/services/FREEIPA/package/scripts/sed_ports.py"
                   " --test /etc/kave/portchanges_static.json --debug")
        ambari.run("python "
                   "/var/lib/ambari-server/resources/stacks/HDP/*.KAVE/services/FREEIPA/package/scripts/sed_ports.py"
                   " --test /etc/kave/portchanges_new.json --debug")


if __name__ == "__main__":
    import sys

    verbose = False
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
    if len(sys.argv) < 2:
        raise KeyError("You must specify which service to test")
    service = sys.argv[1]
    test = TestAService()
    if service == "KAVELANDING":
        test = TestServiceKaveLanding()
    if service == "FREEIPA":
        test = TestServiceFreeIPA()
    test.service = service
    test.branch = branch
    test.debug = verbose
    test.checklist = []
    if len(sys.argv) > 2:
        test.checklist = sys.argv[2:]
    suite = unittest.TestSuite()
    suite.addTest(test)
    base.run(suite)
