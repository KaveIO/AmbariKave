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
import glob
import os
import sys
import imp


class RedirectStdStreams(object):

    def __init__(self, stdout=None, stderr=None):
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush()
        self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush()
        self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr


class TestIpaPortSed(unittest.TestCase):

    def runTest(self):
        """
        Tests which cehck the function of the deployment library,
        but do not need any environment parameters or access to aws
        """
        loc = glob.glob(os.path.dirname(__file__) + '/../../src/KAVE/services/FREEIPA/package/scripts/sed_ports.py')[0]
        self.assertTrue(os.path.exists(loc), "Could not find sed_ports script")
        sed_ports = imp.load_source('sed_ports', loc)
        for cl in sed_ports.comment_in_manually:
            ll = sed_ports.commentstrip(cl)
            self.assertTrue(len(ll))
            self.assertTrue(len(ll) < len(cl))
            self.assertTrue(len(ll) + 2 >= len(cl))
            self.assertTrue(not ll.startswith('#'))
        test_seds = ['     a   ', '   \\b()+=17    ', '   http://808080808443    ']
        expect = [('\\s*a\\s*', '     a   '),
                  ('\\s*\\\\b\\(\\)\\+=17\\s*', '   \\\\b\\(\\)\\+=17    '),
                  ('\\s*http:\\/\\/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]\\s*',
                   '   http:\\/\\/{{pki_insecure_port}}{{pki_insecure_port}}{{pki_secure_port}}    ')]
        self.assertEquals(sed_ports.sed_from_matches(test_seds), expect)
        seddir = os.path.dirname(__file__) + "/sedtests"
        sed_ports.dir_search = [seddir]
        sed_ports.ignore_matches = ["ignorematch 8443"]
        sed_ports.ignore_dirs = [seddir + "/ignoredir"]
        sed_ports.ignore_files = ["ignorefile"]
        expect = [(seddir + '/subdira/subdirb/matchfile.txt', 3, 'matchline, contains 8080')]
        self.assertEquals(sed_ports.find_all_matches(sed_ports.dir_search), expect)
        expect = {seddir + '/subdira/subdirb/matchfile.txt': [(3, 'matchline, contains 8080',
                                                                  'matchline,\\s*contains\\s*[0-9][0-9][0-9][0-9]',
                                                                  'matchline, contains {{pki_insecure_port}}',
                                                                  'matchline, contains 8081')
                                                              ]
                  }
        self.assertEquals(sed_ports.create_match_dictionary(), expect)
        self.assertTrue(sed_ports.check_original_from_json(expect))
        self.assertTrue(sed_ports.check_sed_directly(expect))
        # Check the verifiers with dictionaries containing either lists or tuples
        expct2 = {seddir + '/subdira/subdirb/matchfile.txt': [[3, 'matchline, contains 8080',
                                                                  'matchline,\\s*contains\\s*[0-9][0-9][0-9][0-9]',
                                                                  'matchline, contains {{pki_insecure_port}}',
                                                                  'matchline, contains 8081']
                                                              ]
                  }
        self.assertTrue(sed_ports.check_original_from_json(expct2))
        self.assertTrue(sed_ports.check_sed_directly(expct2))
        # Check for equality where it should exist
        self.assertTrue(sed_ports.check_for_line_changes(expect, expct2))
        expct3 = {seddir + '/subdira/subdirb/matchfile.txt': [[4, 'matchline, contains 8080',
                                                                  'matchline,\\s*contains\\s*[0-9][0-9][0-9][0-9]',
                                                                  'matchline, contains {{pki_insecure_port}}',
                                                                  'matchline, contains 8081']
                                                              ],
                  'dummy': [[5, 'a', 'a', 'a', 'a']]
                  }
        self.assertTrue(sed_ports.check_for_line_changes(expct3, expct3))
        try:
            with open(os.devnull, 'w') as devnull:
                with RedirectStdStreams(stdout=devnull, stderr=devnull):
                    sed_ports.check_for_line_changes(expect, expct3)
            self.assertFalse(True, 'Required ValueError was not raised')
        except ValueError:
            pass
        # test the seds in the .json.j2 files
        templates = glob.glob(os.path.dirname(loc) + '/../templates/*.json.j2')
        for temp in templates:
            import json
            tjson = {}
            with open(temp) as tp:
                tjson = json.load(tp)
            self.assertTrue(len(tjson))
            self.assertTrue(sed_ports.check_sed_directly(tjson))
            self.assertTrue(sed_ports.check_for_line_changes(tjson, tjson))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestIpaPortSed())
    return suite


if __name__ == "__main__":
    base.run(suite())
