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
import base


class TestScan(unittest.TestCase):
    resolves_to_html = """<h3><font size=5px>'MOCK' cluster</font></h3>
<b>Servers</b><p><ul>
  <li>Ambari <a href='http://test1/'></li>
  <li>Ganglia (['elsewhere.com'])</li>
</ul><p><b>Clients</b><p><ul>
  <li>elsewhere.com []</li>
  <li>here.com ['kavetoolbox', 'ganglia_monitor']</li>
  <li>nowhere.none []</li>
  <li>there.com ['kavetoolbox', 'ganglia_monitor']</li>
</ul>"""
    resolves_to_plain = """==================
* 'MOCK' cluster
|--* Servers
|  |--* Ambari <a href='http://test1/'>
|  |--* Ganglia (['elsewhere.com'])
|
|--* Clients
|  |--* elsewhere.com []
|  |--* here.com ['kavetoolbox', 'ganglia_monitor']
|  |--* nowhere.none []
|  |--* there.com ['kavetoolbox', 'ganglia_monitor']"""

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
        sys.path.append(os.path.realpath(dir + "/src/HDP/2.2.KAVE/services/KAVELANDING/package/scripts"))
        import kavescan as ls

        mockd1 = {"gah": {"fish": "food"}, "nah": {"foo": "bar"}}
        mockd2 = {"gah": {"chips": "food", "fish": "pie"}}
        mockout = {"gah": {"chips": "food", "fish": "food"}, "nah": {"foo": "bar"}}
        ls.cloneconfdict(mockd1, mockd2)
        self.assertTrue(mockd2 == mockout, "Cloning dictionaries failed")
        mockservices = {"MOCK": {"AMBARI_SERVER": ["nowhere.none"], "GANGLIA_SERVER": ["elsewhere.com"],
                                 "KAVETOOLBOX": ["here.com", "there.com"],
                                 "GANGLIA_MONITOR": ["here.com", "there.com"]}}
        mocklinks = {"MOCK": {"AMBARI_SERVER": ["<a href='http://test1/'>"]}}
        mockhosts = {"MOCK": {"nowhere.none": ["AMBARI_SERVER"], "elsewhere.com": ["GANGLIA_SERVER"],
                              "here.com": ["KAVETOOLBOX", "GANGLIA_MONITOR"],
                              "there.com": ["KAVETOOLBOX", "GANGLIA_MONITOR"]}}
        mockblueprint = {}
        mockblueprint["host_groups"] = [{"name": "silly1", "components": [{"name": "GANGLIA_SERVER"}]},
                                        {"name": "silly2",
                                         "components": [{"name": "KAVETOOLBOX"}, {"name": "GANGLIA_MONITOR"}]},
                                        {"name": "silly3", "components": [{"name": "NOTHING"}]}]

        self.assertTrue(ls.host_to_hostgroup(["GANGLIA_SERVER", "AMBARI_SERVER"], mockblueprint) == "silly1",
                        "failed to get correct hostgroup")
        self.assertTrue(ls.host_to_hostgroup(["KAVETOOLBOX", "GANGLIA_MONITOR"], mockblueprint) == "silly2",
                        "incorrect hostgroup")
        aconfig = {"apache": {"APACHE_PORT": 9999, "DUMMY": 77}}
        noconfig = {}
        self.assertTrue(ls.pickprop(noconfig, [80]) == 80, "didn't pick correct config")
        self.assertTrue(ls.pickprop(noconfig, [80, "apache/APACHE_PORT"]) == 80, "didn't pick correct config")
        self.assertTrue(ls.pickprop(aconfig, [80, "apache/APACHE_PORT"]) == 9999, "didn't pick correct config")
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
