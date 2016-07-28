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
import subprocess as sub
import os


class TestKaveCommonLib(unittest.TestCase):
    script = os.path.realpath(os.path.dirname(__file__) + '/../../dev/dist_kavecommon.py')
    gooddirs = ["/X.KAVE.Y/services/TESTERA/package/scripts",
                "/X.KAVE.Y/services/TESTER/package/scripts",
                "/services/TESTER2/package/scripts"]
    fakedirs = ["/ABC/X.KAVE.Y/services/TESTER/package/scripts",
                "/X.KAVE.Y/services/TESTER2/bar/scripts",
                "/X.KAVE.Y/services/TESTER/package/foo/bar/scripts",
                "/X.KAVE.Y/services/TESTER2/bar/scripts",
                "/X.KAVE.Y/services/TESTER/package/scripts/scripts",
                "/X.KAVE.Y/services/TESTER/package/scripts/scripts",
                ]

    def mkdirs(self):
        import tempfile
        tempdir = tempfile.mkdtemp()
        for dir in self.gooddirs:
            os.system("mkdir -p " + tempdir + dir)
        for dir in self.fakedirs:
            os.system("mkdir -p " + tempdir + dir)
        return tempdir

    def findkavecommon(self, topdir):
        found = []
        for path, dirs, files in os.walk(topdir):
            found = found + [path.replace(topdir, '') for f in files if f == 'kavecommon.py']
        return found

    def runTest(self):
        """
        Tests that verify the distribution of the kavecommon library
        """
        # make some directory structure to check the distribution changing...
        import os
        tempdir = self.mkdirs()
        p = sub.Popen(['python', self.script, tempdir])
        p.communicate()
        found = self.findkavecommon(tempdir)
        if os.path.exists(tempdir):
            os.system('rm -rf tmpdir')
        extra = [s for s in found if s not in self.gooddirs]
        missing = [s for s in self.gooddirs if s not in found]
        if len(missing + extra):
            print found, extra, missing
        self.assertFalse(len(extra), 'extra')
        self.assertFalse(len(missing), '')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestKaveCommonLib())
    return suite


if __name__ == "__main__":
    base.run(suite())
