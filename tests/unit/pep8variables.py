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


class TestVariables(unittest.TestCase):
    """
    Checks conformance of all variable names with pep8 standard
    variables should be using_underscores not usingCamelCase
    COMPLETELY_UPPER_IS_OK
    Except for those inherited form the underlying library, of course!
    """
    ignorefiles = ['pep8functions.py', 'params.py', 'stack_advisor.py', 'exceptions.py']
    ignorevars = ["lD", "lA", "Logger"]

    def find_definitions(self, fullpath):
        found = []
        if os.path.isfile(fullpath):
            with open(fullpath) as fp:
                multiline = False
                for i, line in enumerate(fp):
                    if not len(line):
                        continue
                    # Handle multi-line strings, don't match within multiline strings
                    if (line.count('"""') == 1 or line.count("'''") == 1) and multiline:
                        multiline = False
                        line = ''.join(line.split('"""')[-1])
                        line = ''.join(line.split("'''")[-1])
                    if multiline:
                        continue
                    if (line.count('"""') == 1 or line.count("'''") == 1) and not multiline:
                        multiline = True
                        line = ''.join(line.split('"""')[0])
                        line = ''.join(line.split("'''")[0])
                    # Finished multiline strings, now continue ...
                    if '=' not in line:
                        continue
                    # collapse quotes in line, don't match within quotes
                    # cut off at any comments
                    line = line.split('#')[0]
                    line = ''.join(line.split('"')[::2])
                    line = ''.join(line.split("'")[::2])
                    # tokenize at open brackets, ; : or ,
                    for token in re.split('[\,,;,\(,:]', line):
                        token = token.replace('==', '')
                        if '=' not in token:
                            continue
                        tokenbefore = token.split("=")[0].strip()
                        tokenbefore = tokenbefore.split(".")[0].strip()
                        tokenbefore = tokenbefore.split("[")[0].strip()
                        if tokenbefore.lower() != tokenbefore and tokenbefore.upper() != tokenbefore:
                            found.append((fullpath, i + 1, tokenbefore))
        return found

    def runTest(self):
        """
        Walk through files and check against regex
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
                if 'mock_ambari' in root:
                    continue
                found = found + self.find_definitions(os.path.join(root, f))
        found = [i for i in found if i is not None
                 and len(i)
                 and i[-1] not in self.ignorevars]
        self.assertFalse(len(set(found)), "Mixed capitalization found in " + str(len(found))
                         + " variable names \n\t"
                         + '\n\t'.join([str(i) for i in found]))

if __name__ == "__main__":
    test = TestVariables()
    suite = unittest.TestSuite()
    suite.addTest(test)
    base.run(suite)
