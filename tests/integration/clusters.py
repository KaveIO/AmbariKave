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
        # check the files can be opened, and then check that the cluster contains the machines from the aws file
        jsons = []
        for ason in [pref + ".aws.json", pref + ".blueprint.json", pref + ".cluster.json"]:
            f = open(ason)
            l = f.read()
            f.close()
            self.assertTrue(len(l) > 1, "json file " + ason + " is a fragment or corrupted")
            try:
                interp = json.loads(l)
                jsons.append(interp)
            except:
                self.assertTrue(False, "json file " + ason + " is not complete or not readable")
        # Find what is needed for the cluster
        need_hosts = []
        need_groups = []
        for hg in jsons[-1]["host_groups"]:
            need_groups.append(hg['name'])
            for host in hg['hosts']:
                need_hosts.append(host["fqdn"])
        supplies_hosts = []
        created_groups = []
        # check that the aws file creates the machines
        dn = "kave.io"
        try:
            dn = jsons[0]["Domain"]["Name"]
        except KeyError:
            pass
        for ig in jsons[0]["InstanceGroups"]:
            if ig["Count"] > 0:
                supplies_hosts = supplies_hosts + [ig["Name"] + '-00' +
                                                   str(i + 1) + '.' + dn for i in range(ig["Count"])]
            else:
                supplies_hosts.append(ig["Name"] + '.' + dn)
        missing = [f for f in need_hosts if f not in supplies_hosts]
        extra = [f for f in supplies_hosts if f not in need_hosts]
        self.assertFalse(len(missing), "Missing creation of the hosts called " + str(missing))
        self.assertFalse(len(extra), "Asked to create hosts I won't later use " + str(extra))
        # check that the blueprint file creates the hostgroups
        for ig in jsons[1]["host_groups"]:
            created_groups.append(ig["name"])
        missing = [f for f in need_groups if f not in created_groups]
        self.assertFalse(len(missing), "Missing creation of the host groups called " + str(missing))
        # check that the supplied blueprint is the one which is given in the clusterfile
        self.assertEqual(jsons[1]["Blueprints"]["blueprint_name"], jsons[-1]["blueprint"],
                         "Blueprint name is not the same in your blueprint c.f. your clusterfile")
        # Deploy the cluster
        if self.clustername == 'prod':
            self.clustername = self.service
        stdout = self.deploycluster(pref + ".aws.json", cname=self.clustername)
        connectcmd = ""
        for line in range(len(stdout.split('\n'))):
            if "ambari connect remotely with" in stdout.split("\n")[line]:
                connectcmd = stdout.split("\n")[line + 1].strip()
        adict = stdout.split("\n")[-2].replace("Complete, created:", "")
        # try interpreting as json
        adict = base.d2j(adict)
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
        self.pull(ambari)
        self.waitForAmbari(ambari)
        self.deployBlueprint(ambari, pref + ".blueprint.json", pref + ".cluster.json")
        return self.check(ambari)


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
