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
import unittest
import base


class TestLicense(unittest.TestCase):

    def runTest(self):
        """
        Tests that check that every file contains the apache 2.0 license
        """
        # this list is a list of things that we don't want to check
        ignore_regex = ['.*/build/.*']
        accept_regex = ['.*\.sh$', '.*\.py$']
        # check they exist at least twice in service.sh
        import os
        import sys
        import re
        dir = os.path.realpath(os.path.dirname(__file__) + "/../../")
        all_files = []
        skip = False
        for root, dirnames, filenames in os.walk(dir):
            skip = False
            for ignore_path in ignore_regex:
                if re.match(ignore_path, root):
                    skip = True
                    break
            if skip:
                continue
            for filename in filenames:
                all_files.append(os.path.join(root, filename))
        no_license = []
        ignore = []
        matches = []
        check_contains = "http://www.apache.org/licenses/LICENSE-2.0"
        for toignore in ignore_regex:
            r = re.compile(toignore)
            ignore = ignore + filter(r.match, all_files)
        for tofind in accept_regex:
            r = re.compile(tofind)
            matches = matches + filter(r.match, all_files)
        # print matches[:10], ignore[:10]
        matches = [f for f in matches if f not in ignore]
        for f in matches:
            fop = open(f)
            fos = fop.read()
            fop.close()
            if check_contains not in fos:
                no_license.append(f)
        self.assertTrue(len(no_license) == 0,
                        "Error: Found missing licenses in " + str(len(no_license)) + " files:\n\t" + '\n\t'.join(
                            no_license))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestLicense())
    return suite


if __name__ == "__main__":
    base.run(suite())
