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


class TestPyFilenames(unittest.TestCase):

    def runTest(self):
        """
        TCheck that there are no upper-case letters or dashes in python filenames
        """
        import os
        import string
        for root, dirs, files in os.walk(os.path.realpath(__file__ + '/../../../')):
            upperfiles = [os.path.join(root, f) for f in files if f.lower() != f and f.endswith('.py')]
            self.assertTrue(len(upperfiles) == 0, "Python files with upper-case letters detected" + str(upperfiles))
            dashfiles = [os.path.join(root, f) for f in files if '-' in f and f.endswith('.py')]
            self.assertTrue(len(dashfiles) == 0, "Python files with dashes detected" + str(dashfiles))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestPyFilenames())
    return suite


if __name__ == "__main__":
    base.run(suite())
