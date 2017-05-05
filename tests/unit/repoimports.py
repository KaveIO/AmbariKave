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
import kavecommon as kc


class TestRepoImports(unittest.TestCase):
    """
    Checks for lines where we try and get a file from the repository,
    and checks that those files exist, then
    """
    ignorefiles = ['repoimports.py']
    ignorepackages = []
    replaces = {"+params.releaseversion+": kc.__version__,
                "%s": "el6"}

    def find_repolocations(self, fullpath):
        found = []
        if os.path.isfile(fullpath):
            with open(fullpath) as fp:
                package = ''
                arch = 'centos6'
                for i, line in enumerate(fp):
                    line = line.split("#")[0]
                    line = ''.join(line.split())
                    if line.startswith('package='):
                        package = line.split('package=')[-1].split(';')[0].split(',')[0]
                        package = package.strip().replace("'", '').replace('"', '').replace(')', '')
                    if 'arch=' in line:
                        arch = line.split('arch=')[-1].split(';')[0].split(',')[0].strip()
                        arch = arch.replace("'", '').replace('"', '').replace(')', '')
                    if 'kc.copy_cache_or_repo("' in line or "kc.copy_cache_or_repo('" in line:
                        package = line.split(
                            '_repo(')[-1].split(';')[0].split(',')[0].strip().replace("'", '').replace('"', '')
                    if 'kc.copy_cache_or_repo(' in line and len(package):
                        for r, p in self.replaces.iteritems():
                            package = package.replace(r, p)
                        found.append((fullpath, i + 1, arch, package))
                        package = ''
                        arch = 'centos6'
                        # break

        return found

    def runTest(self):
        """
        The most basic python test possible, checks that the files we have written
        are importable in python, this is a basic sanity check
        """
        found = []
        for root, dirs, files in os.walk(os.path.dirname(__file__) + '/../../src/KAVE'):
            if '.git' in root:
                continue
            for f in files:
                if not (f.endswith('.py')):
                    continue
                if f in self.ignorefiles:
                    continue
                found = found + self.find_repolocations(os.path.join(root, f))
        found = [i for i in found if i is not None
                 and len(i)
                 and i[-1] not in self.ignorepackages]
        failed = []
        sys.stdout.flush()
        for details in found:
            fn, ln, arch, package = details
            urls = []
            for mirror in kc.mirrors():
                if 'kavetoolbox' in package:
                    urls.append(kc.repo_url(package, arch=arch, repo=mirror, dir='KaveToolbox'))
                else:
                    urls.append(kc.repo_url(package, arch=arch, repo=mirror))
                if 'eskapade' in package:
                    urls.append(kc.repo_url(package, arch=arch, repo=mirror, dir='Eskapade'))
                else:
                    urls.append(kc.repo_url(package, arch=arch, repo=mirror))
            if not len(urls):
                if 'kavetoolbox' in package:
                    urls.append(kc.repo_url(package, arch=arch, dir='KaveToolbox'))
                else:
                    urls.append(kc.repo_url(package, arch=arch))
            if 'eskapade' in package:
                urls.append(kc.repo_url(package, arch=arch, dir='Eskapade'))
            else:
                urls.append(kc.repo_url(package, arch=arch))
            try:
                sys.stdout.flush()
                kc.failover_source(urls)
            except IOError:
                failed.append(details)
            except IOError:
                failed.append(details)
        self.assertFalse(len(failed), "Some requested downloads do not exist!\n\t" +
                         '\n\t'.join([f.__str__() for f in failed]))

if __name__ == "__main__":
    test = TestRepoImports()
    suite = unittest.TestSuite()
    suite.addTest(test)
    base.run(suite)
