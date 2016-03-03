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
import xml
import xml.parsers.expat
import kavecommon as kc

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


def parsefile(file):
    parser = xml.parsers.expat.ParserCreate()
    parsed = None
    with open(file, "r") as f:
        parsed = parser.ParseFile(f)
    return parsed


class TestXMLCompleteness(unittest.TestCase):

    def runTest(self):
        """Test that we have only valid xml, based upon the example
        found here: http://code.activestate.com/recipes/52256-check-xml-well-formedness/"""
        import os
        import string
        failingfiles = {}
        for root, dirs, files in os.walk(os.path.realpath(__file__ + '/../../../')):
            for f in [os.path.join(root, f) for f in files if f.endswith('.xml')]:
                try:
                    parsefile(f)
                except Exception, e:
                    failingfiles[f] = e
        self.assertEqual(len(failingfiles), 0,
                         "Found " + str(len(failingfiles))
                         + " xml errors "
                         + str(failingfiles.keys())
                         + " \n" + str(failingfiles)
                         )


class TestXMLContent(unittest.TestCase):
    prop_dict_struct = {"name": [], "value": [],
                        "display-name": [], "value-attributes": ["type", "overridable"],
                        "description": [], "comment": [],
                        "property-type": [], "deleted": [],
                        "depends-on": {"property": ["type", "name"]}
                        }
    config_files = {"configuration": {"property": prop_dict_struct}}
    command_script_struct = ["script", "scriptType", "timeout"]
    components_struct = {"component": {"name": [], "displayName": [],
                                       "comment": [], "version": [],
                                       "category": [], 'cardinality': [],
                                       "commandScript": command_script_struct,
                                       "customCommands": {"customCommand": {"commandScript": command_script_struct,
                                                                            "name": []
                                                                            }
                                                          },
                                       "auto-deploy": ["enabled", "co-locate"],
                                       "dependencies": {"dependency": {"name": [], "scope": [],
                                                                       "auto-deploy": ["enabled", "co-locate"]
                                                                       }
                                                        },
                                       "versionAdvertised": [],
                                       "clientsToUpdateConfigs": []
                                       }
                         }
    os_struct = {"osSpecific": {"osFamily": [], "packages": {"package": ["name"]}}}
    meta_info = {"metainfo": {"versions": ["active"], "extends": [],
                              'schemaVersion': [],
                              'services': {"service": {"name": [], "displayName": [],
                                                       "comment": [], "version": [],
                                                       "components": components_struct,
                                                       "osSpecifics": os_struct,
                                                       "requiredServices": ["service"],
                                                       "configuration-dependencies": ["config-type"]
                                                       }
                                           }}}

    def velement(self, element, cdict, file=None):
        if element.tag not in cdict:
            raise NameError(file + "\n" + "element not recognized " + element.tag)
        for child in element:
            if child.tag not in cdict[element.tag]:
                raise NameError(file + "\n" + child.tag + " child not expected for element " + element.tag)
            self.velement(child, cdict[element.tag], file=file)

    def runTest(self):
        """Use ETree to walk through the config tree and check the structure"""
        import os
        import string
        failingfiles = {}
        for root, dirs, files in os.walk(os.path.realpath(__file__ + '/../../../')):

            for f in [os.path.join(root, f) for f in files if f.endswith('.xml')]:
                try:
                    tree = ET.ElementTree(file=f)
                    if "configuration" in root:
                        self.velement(tree.getroot(), self.config_files, f)
                    elif "metainfo.xml" in f:
                        self.velement(tree.getroot(), self.meta_info, f)
                except ET.ParseError:
                    continue
                except NameError, e:
                    failingfiles[f] = e

        self.assertEqual(len(failingfiles), 0,
                         "Found " + str(len(failingfiles))
                         + " xml errors "
                         + str(failingfiles.keys())
                         + " \n" + str(failingfiles)
                         )


class TestMatchRequiredOrDefault(unittest.TestCase):
    skip = ['hive-site.xml', 'hdfs-site.xml', '_kave_hive-site.xml', 'oozie-site.xml']
    skip_prop = ['kavetoolbox/custom_install_template', 'twiki/ldap_bind_password',
                 'mail/hostname', 'mail/domain']

    def rm_unchecked_chars(self, astr):
        return ("".join(astr.replace("'", "").replace('+', '').replace('"', '').replace('\\', '').split()))

    def runTest(self):
        """Check that properties are either forced to be entered or have a default set,
        in case a default is set, check the same default exists in the params file"""
        import os
        import string
        failingxmlfiles = {}
        failingpyfiles = {}
        defaults = {}
        # First, part 1: check that all params are either required or have a default
        # Also fill defaults with the list of defaults to check against the params file
        for root, dirs, files in os.walk(os.path.realpath(__file__ + '/../../../')):
            for f in [os.path.join(root, f) for f in files if f.endswith('.xml') and f not in self.skip]:
                if "configuration" not in root:
                    continue
                tree = ET.ElementTree(file=f)
                for property in tree.getroot():
                    if property.tag != 'property':
                        continue
                    name = property.find('name').text
                    isRequired = (
                        'require-input' in property.attrib and
                        kc.trueorfalse(property.attrib['require-input'])
                    )
                    hasDefault = False
                    for child in property:
                        if child.tag != 'value':
                            continue
                        if child.text is not None and len(child.text.strip()):
                            hasDefault = True
                            if not isRequired:
                                try:
                                    defaults[f][name] = child.text.strip()
                                except KeyError:
                                    defaults[f] = {name: child.text.strip()}
                            break
                    if not hasDefault and not isRequired:
                        failingxmlfiles[f] = name

        self.assertEqual(len(failingxmlfiles), 0,
                         "Found " + str(len(failingxmlfiles))
                         + " xml file missing defaults/required "
                         + str(failingxmlfiles.keys())
                         + " \n" + str(failingxmlfiles)
                         )

        # Part 2: now check in the params file to see that the same default is set there
        for root, dirs, files in os.walk(os.path.realpath(__file__ + '/../../../')):
            for f in [os.path.join(root, f) for f in files if f == 'params.py' and f not in self.skip]:
                existingdefaults = None
                for existingdefaults in defaults:
                    if f.startswith(existingdefaults[:existingdefaults.find('configuration')]):
                        break
                if not existingdefaults:
                    continue
                servicename = existingdefaults.split('/')[-1].lower().split('.')[0]
                all_params = ""
                with open(f) as fp:
                    all_params = fp.read()
                all_params = self.rm_unchecked_chars(all_params)
                for defaultp, defaultv in defaults[existingdefaults].iteritems():
                    if servicename + '/' + defaultp in self.skip_prop:
                        continue
                    defaultvs = self.rm_unchecked_chars(defaultv)
                    search_string = 'default(configurations/' + servicename + '/' + defaultp + ',' + defaultvs + ')'
                    if search_string not in all_params:
                        failingpyfiles[f + '/' + servicename + '/' + defaultp] = search_string

        self.assertEqual(len(failingpyfiles), 0,
                         "Found " + str(len(failingpyfiles))
                         + " python params file missing defaults {file/service/property: missing_str_approx }"
                         + " \n" + str(failingpyfiles).replace("',", "',\n")
                         )


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestXMLCompleteness())
    suite.addTest(TestXMLContent())
    suite.addTest(TestMatchRequiredOrDefault())
    return suite


if __name__ == "__main__":
    base.run(suite())
