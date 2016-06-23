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
import pep8

LINES_SKIP = 17

ignoreList = ["JBOSS/package/scripts/params.py", "KAVEGANGLIA/package/scripts/params.py"]


class PEP8(pep8.StyleGuide):
    """This subclass of pep8.StyleGuide will skip the first lines of each file."""

    def input_file(self, filename, lines=None, expected=None, line_offset=0):
        if lines is None:
            assert line_offset == 0
            line_offset = LINES_SKIP
            lines = pep8.readlines(filename)[LINES_SKIP:]
        return super(PEP8, self).input_file(
            filename, lines=lines, expected=expected, line_offset=line_offset)


class TestCodeFormat(unittest.TestCase):

    def runTest(self):
        """Test that we conform to PEP8."""
        import os
        import string
        pep8style = PEP8(config_file=os.path.join(os.path.dirname(__file__), 'pep8.conf'))
        allpyfiles = []
        for root, dirs, files in os.walk(os.path.realpath(__file__ + '/../../../')):
            allpyfiles = allpyfiles + [os.path.join(root, f) for f in files if f.endswith('.py')]
        allpyfiles = [a for a in allpyfiles if not max([a.endswith(b) for b in ignoreList])]
        result = pep8style.check_files(allpyfiles)
        self.assertEqual(result.total_errors, 0,
                         "Found " + str(result.total_errors)
                         + " code style errors (and warnings)."
                         + " Try running 'autopep8 --max-line-length 120 -r --in-place *'"
                         + " from the top dir \n"
                         + str(result.counters))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestCodeFormat())
    return suite


if __name__ == "__main__":
    base.run(suite())
