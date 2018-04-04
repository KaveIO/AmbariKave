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
import unittest
import base


class TestScan(unittest.TestCase):
    resolves_to_html = """<h3><font size=5px>'MOCK' cluster</font></h3>
<b>Servers</b><p><ul>
  <li>Ambari <a href='http://test1/'><a href='http://nowhere:8080'>admin</a> </li>
  <li>Stormsd log <a href='http://nimbus:8008'>log</a> <a href='http://node:8008'>log</a>
       <a href='http://here:8008'>log</a> <a href='http://there:8008'>log</a> </li>
</ul><p><b>Clients</b><p><ul>
  <li>elsewhere.com []</li>
  <li>here.com ['kavetoolbox']</li>
  <li>nimbus.com []</li>
  <li>node.com []</li>
  <li>nowhere.none []</li>
  <li>there.com ['kavetoolbox']</li>
</ul>"""
    resolves_to_plain = """==================
* 'MOCK' cluster
|--* Servers
|  |--* Ambari <a href='http://test1/'><a href='http://nowhere:8080'>admin</a>
|  |--* Stormsd log <a href='http://nimbus:8008'>log</a>
                <a href='http://node:8008'>log</a>
                <a href='http://here:8008'>log</a> <a href='http://there:8008'>log</a>
|
|--* Clients
|  |--* elsewhere.com []
|  |--* here.com ['kavetoolbox']
|  |--* nimbus.com []
|  |--* node.com []
|  |--* nowhere.none []
|  |--* there.com ['kavetoolbox']"""

    def runTest(self):
        """
        Test kavescan, the library which polls our ambari installer.
        Kavescan reads information from ambari as a blueprint and configuration
        and then it formats the result.

        In this unit test we can only check the parsing and formatting.
        """
        import os
        import sys

        dir = os.path.realpath(os.path.dirname(__file__) + "/../../")
        sys.path.append(os.path.realpath(dir + "/src/KAVE/services/KAVELANDING/package/scripts"))
        import kavescan as ls

        mockd1 = {"gah": {"fish": "food"}, "nah": {"foo": "bar"}}
        mockd2 = {"gah": {"chips": "food", "fish": "pie"}}
        mockout = {"gah": {"chips": "food", "fish": "food"}, "nah": {"foo": "bar"}}
        ls.cloneconfdict(mockd1, mockd2)
        self.assertTrue(mockd2 == mockout, "Cloning dictionaries failed")
        mockservices = {"MOCK": {"AMBARI_SERVER": ["nowhere.none"],
                                 "KAVETOOLBOX": ["here.com", "there.com"],
                                 "STORMSD_LOG_VIEWER": ["there.com", "node.com", "nimbus.com"]}}
        mocklinks = {"MOCK": {"AMBARI_SERVER": ["<a href='http://test1/'>"]}}
        mockhosts = {"MOCK": {"nowhere.none": ["AMBARI_SERVER"], "elsewhere.com": [],
                              "here.com": ["KAVETOOLBOX", "STORMSD_LOG_VIEWER"],
                              "there.com": ["KAVETOOLBOX", "STORMSD_LOG_VIEWER"],
                              "node.com": ["STORMSD_LOG_VIEWER"],
                              "nimbus.com": ["STORMSD_LOG_VIEWER"]}}
        mockblueprint = {}
        mockblueprint["host_groups"] = [{"name": "silly2",
                                         "components": [{"name": "KAVETOOLBOX"},
                                                        {"name": "STORMSD_LOG_VIEWER"}]},
                                        {"name": "silly3", "components": [
                                            {"name": "NOTHING"}, {"name": "STORMSD_LOG_VIEWER"}]},
                                        {"name": "silly4", "components": [{"name": "STORMSD_LOG_VIEWER"}]}
                                        ]

        self.assertTrue(ls.host_to_hostgroup(["KAVETOOLBOX", "STORMSD_LOG_VIEWER"],
                                             mockblueprint) == "silly2",
                        "incorrect hostgroup")
        # check that pickprop works
        aconfig = {"apache": {"APACHE_PORT": 9999, "DUMMY": 77}}
        noconfig = {}
        self.assertTrue(ls.pickprop(noconfig, [80]) == 80, "didn't pick correct config")
        self.assertTrue(ls.pickprop(noconfig, [80, "apache/APACHE_PORT"]) == 80, "didn't pick correct config")
        self.assertTrue(ls.pickprop(aconfig, [80, "apache/APACHE_PORT"]) == 9999, "didn't pick correct config")
        # for service in
        # mocklinks[cluster][component].append(
        #                    "<a href='http://" + host.split('.')[0] + ":" + str(
        #                        pickprop(myconfigs, port)) + "'>" + linkname + "</a> ")
        # Basic test of service_portproperty_dict and pickprop
        for host in mockhosts["MOCK"]:
            # print components
            for component in mockhosts["MOCK"][host]:
                if component in ls.service_portproperty_dict:
                    if component not in mocklinks["MOCK"]:
                        mocklinks["MOCK"][component] = []
                    for linkname, port in ls.service_portproperty_dict[component].iteritems():
                        mocklinks["MOCK"][component].append(
                            "<a href='http://" + host.split('.')[0] + ":"
                            + str(ls.pickprop({'stormsd': {'stormsd.logviewer.port': 8008}}, port))
                            + "'>" + linkname + "</a> ")
        self.assertTrue("MOCK" in mocklinks and "STORMSD_LOG_VIEWER" in mocklinks["MOCK"]
                        and "<a href='http://nimbus:8008'>log</a> " in mocklinks["MOCK"]["STORMSD_LOG_VIEWER"],
                        "resolution of links has stopped working")
        ppp = ls.pretty_print(mockservices, mockhosts, mocklinks, "plain")
        pph = ls.pretty_print(mockservices, mockhosts, mocklinks, "html")
        # ignore whitespace in this test!
        self.assertTrue(''.join(self.resolves_to_html.split()) in ''.join(pph.split()),
                        "resolution of the pretty print is messed up, \n" + pph + "should be more like\n" +
                        self.resolves_to_html)
        self.assertTrue(''.join(self.resolves_to_plain.split()) in ''.join(ppp.split()),
                        "resolution of the pretty print is messed up, \n" + ppp
                        + "should be more like\n" + self.resolves_to_plain)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestScan())
    return suite


if __name__ == "__main__":
    base.run(suite())
