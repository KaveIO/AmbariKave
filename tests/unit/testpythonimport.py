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
import os
import imp
import sys


class TestPyImport(unittest.TestCase):
    skip = ["stack_advisor.py"]
    first = ["storm_sd_generic.py", "mongo_base.py", "mysql_users.py", "mysql_utils.py"]

    def tryimporting(self, fullpath):
        fname = os.path.basename(fullpath)
        path = os.path.realpath(os.path.dirname(fullpath))
        mname = fname.split('.')[0]
        if os.path.isfile(fullpath):
            try:
                imp.load_source(mname, fullpath)
            except ImportError:
                sys.path.append(os.path.dirname(fullpath))
                imp.load_source(mname, fullpath)
        else:
            sys.path.append(path)
            found = imp.find_module(mname)
            imp.load_module(mname, found[0], found[1], found[2])
            

    def runTest(self):
        """
        TCheck that there are no upper-case letters or dashes in python filenames
        """
        self.tryimporting(os.path.dirname(__file__) + '/mock/resource_management')
        self.tryimporting(os.path.dirname(__file__) + '/mock/socket.py')
        import resource_management
        import socket
        pfiles = []
        for root, dirs, files in os.walk(os.path.realpath(__file__ + '/../../../src')):
            pfiles = pfiles + [os.path.join(root, f) for f in files if f.endswith('.py') and f not in self.skip]
        print len(pfiles)
        for f in self.first:
            fname = [fi for fi in pfiles if fi.endswith(f)][0]
            self.tryimporting(fname)
        for f in [f for f in pfiles if os.path.basename(f) not in self.first]:
            self.tryimporting(f)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestPyImport())
    return suite


if __name__ == "__main__":
    base.run(suite())
