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
import os
import imp
import sys
import re

class TestFunctions(unittest.TestCase):
    """
    Checks conformance of all function names with pep8 standard
    Functions should be using_underscores not usingCapitalization
    Except for the function runTest inherited form the underlying library, of course!
    """
    re = re.compile("\s*def *[a-z,_,0-9]*([A-Z])[a-z,A-Z,_,0-9]*\(")
    ignorefiles = ['pep8functions.py','stack_advisor.py']
    ignorefunctions = ["def runTest"]

    def find_definitions(self, fullpath):
        found = []
        if os.path.isfile(fullpath):
            with open(fullpath) as fp:
                for i, line in enumerate(fp):
                    for match in re.finditer(self.re, line):
                        found.append((fullpath, i + 1, line.strip().split('(')[0].replace('  ',' ')))
        return found

    def runTest(self):
        """
        The most basic python test possible, checks that the files we have written
        are importable in python, this is a basic sanity check
        """
        found = []
        for root, dirs, files in os.walk(os.path.realpath(__file__ + '/../../../')):
            if '.git' in root:
                continue
            for f in files:
                if not (f.endswith('.py')):
                    continue
                if f in self.ignorefiles:
                    continue
                found = found + self.find_definitions(os.path.join(root, f))
        found = [i for i in found if i is not None
                 and len(i)
                 and i[-1] not in self.ignorefunctions]
        self.assertFalse(len(set(found)), "Mixed capitalization found in " + str(len(found))
                         + " function names \n\t"
                         + '\n\t'.join([str(i) for i in found]))

if __name__ == "__main__":
    test = TestFunctions()
    suite = unittest.TestSuite()
    suite.addTest(test)
    base.run(suite)
