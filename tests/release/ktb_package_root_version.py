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
import base
import unittest
import kavecommon as kc
import sys
import os

sys.path.append(os.path.dirname(__file__) + '/../service')
import test_kavetoolbox_head


class PackageRootFromKTB(test_kavetoolbox_head.TestKaveToolbox):
    """
    Deploys a copy of KTB, compiling root instead of downloading it
    Then zips up the root version following the wiki instructions and
    copies the tarball back
    """
    service = "KaveToolbox-RootCompile"
    workstation = False

    def deploy_ktb(self, ambari):
        ambari.run('mkdir -p /etc/kave/')
        ambari.cp(os.path.dirname(__file__) + '/_compile_root_custom.py', '/etc/kave/CustomInstall.py')
        return super(PackageRootFromKTB, self).deploy_ktb(ambari)

    def check(self,ambari):
        super(PackageRootFromKTB, self).check(ambari)
        # Abuse the check method to package up the now working root installation
        ambari.run('mkdir -p /tmp/rootcompile')
        # dynamically find which version was installed
        _version = ambari.run('ls -d /opt/root/v*').split()[-1].split('/')[-1]
        ambari.run('cp -r /opt/root/%s /tmp/rootcompile/root' % _version)
        _os = self.osType.lower()
        if _os.startswith('ubuntu'):
            os = 'ubuntu'
        ambari.run('bash -c "cd /tmp/rootcompile; tar cvzf root_%s_%s.tar.gz root;"' % (_version, _os))
        ambari.pull('/tmp/rootcompile/root_%s_%s.tar.gz' % (_version, _os), 'root_%s_%s.tar.gz' % (_version, _os))
        self.assertTrue(os.path.exists('root_%s_%s.tar.gz' % (_version, _os)), "failed to copy tarfile")


if __name__ == "__main__":
    import sys

    verbose = False
    if "--verbose" in sys.argv:
        verbose = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    test1 = PackageRootFromKTB()
    test1.debug = verbose
    if len(sys.argv) > 1:
        test1.ostype = sys.argv[1]
    suite = unittest.TestSuite()
    suite.addTest(test1)
    base.run(suite)
