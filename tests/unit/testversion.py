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
import os
import imp
import sys
import re


class TestVersions(unittest.TestCase):
    """
    Checks that all the specified versions are consistent
    """
    regex = re.compile("([0-9]\.[0-9]-Beta(-Pre)?)")
    restack = re.compile("([0-9]\.[0-9]\.[0-9]\.[0-9]\.KAVE)")
    ignore = ["ReleaseNotes.md"]
    check_against = "3.0-Beta"
    check_against_stack = "2.5.3.0.KAVE"

    def findversion(self, fullpath, regex):
        found = []
        if os.path.isfile(fullpath):
            with open(fullpath) as fp:
                for i, line in enumerate(fp):
                    for match in re.finditer(regex, line):
                        found.append((fullpath, i + 1, match.groups()))
        return found

    def iterfiles(self, regex):
        found = []
        foundstack = []
        for root, dirs, files in os.walk(os.path.realpath(__file__ + '/../../../')):
            if '.git' in root:
                continue
            for f in files:
                if (f.endswith('.png') or f.endswith('.ppt') or
                        f.endswith('.pptx') or f.endswith('.css') or
                        f.endswith('.svg') or f.endswith('.jpeg') or
                        f.endswith('.jpg') or f.endswith('.bmp') or
                        f.endswith('.pdf') or f.endswith('.pyc')):
                    continue
                if f in self.ignore:
                    continue
                found = found + self.findversion(os.path.join(root, f), regex)
        found = [i for i in found if i is not None and len(i)]
        foundn = [i[-1][0] for i in found]
        return found, foundn

    def runTest(self):
        """
        The most basic python test possible, checks that the files we have written
        are importable in python, this is a basic sanity check
        """
        self.assertTrue(self.check_against[:3] == self.check_against_stack[4:7],
                        "This version does not appear in the stack name!! Modify the stack name if required.")
        for regex, version in [(self.regex, self.check_against), (self.restack, self.check_against_stack)]:
            found, foundn = self.iterfiles(regex)
            self.assertTrue(len(set(foundn)) == 1, "Mis-matching version numbers found! \n\t" +
                            '\n\t'.join([str(i) for i in found]))
            foundp = [i for i in foundn if i != version]
            self.assertFalse(len(set(foundp)), "Versions match, but are not what was expected: "
                             + self.check_against + " \n\t"
                             + '\n\t'.join([str(i) for i in found]))

if __name__ == "__main__":
    test = TestVersions()
    import sys
    if len(sys.argv) > 1:
        test.check_against = sys.argv[-1]
    suite = unittest.TestSuite()
    suite.addTest(test)
    base.run(suite)
