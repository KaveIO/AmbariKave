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


class TestKaveCommonLib(unittest.TestCase):
    def runTest(self):
        import kavecommon as kc

        sources = []
        for mirror in kc.mirrors():
            sources.append(kc.repoURL("", repo=mirror))
        sources.append(kc.repoURL(""))
        kc.failoverSource(sources)
        self.assertRaises(IOError, kc.failoverSource, ["non-existing-file-88989381923813.file"])  #,"bug ABK-112"
        #make some directory structure to check the permissions changing...
        import tempfile, os

        tempdir = tempfile.mkdtemp()
        os.system("mkdir -p " + tempdir + "/this/is/a/test1")
        os.system("mkdir -p " + tempdir + "/this/is/a/test2")
        os.system("mkdir -p " + tempdir + "/this/is/a/test3")
        os.system("chmod -R 555 " + tempdir + "/this ")
        kc.chmodUp(tempdir + "/this/is/a/test1", "511", seen=[tempdir, tempdir + "/this"])
        self.assertFalse(os.access(tempdir + "/this/is/a", os.W_OK), tempdir + " permissions settings failed")
        kc.chmodUp(tempdir + "/this/is/a/test1", "744", seen=[tempdir])
        self.assertTrue(os.access(tempdir + "/this/is/a", os.W_OK), tempdir + " permissions settings failed")
        self.assertFalse(os.access(tempdir + "/this/is/a/test2", os.W_OK), tempdir + " permissions settings failed")
        #create a file in this directory to test the copy/caching, at least for things without wget
        os.system("touch " + tempdir + "/this/is/test.test")
        topd = os.path.realpath(os.curdir)
        os.chdir(tempdir)
        kc.copyOrCache(sources=[tempdir + "/this/is/test.test"], filename="test.test", cache_dir=tempdir + "/this/")
        os.chdir(topd)
        self.assertTrue(os.path.exists(tempdir + "/test.test") and os.path.exists(
            tempdir + "/this/is/test.test") and os.path.exists(tempdir + "/this/test.test"),
                        tempdir + " copy/caching failed")
        #Test the trueorfalse method
        cnv={'true':True,'y':True,'ye':True,'yes':True,
             'false':False,'n':False,'no':False,'none':False,
             ' false':False,'y ':True}
        for k,v in cnv.iteritems():
            self.assertTrue(kc.trueorfalse(k)==v)
            self.assertTrue(kc.trueorfalse(k.upper())==v)
        self.assertRaises(TypeError,kc.trueorfalse,{})
        self.assertRaises(TypeError,kc.trueorfalse,'GAAAH')

        #remove this temporary file when done
        if os.path.exists(tempdir) and len(tempdir)>4:
            os.system("rm -rf " + tempdir)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestKaveCommonLib())
    return suite


if __name__ == "__main__":
    base.run(suite())
