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

from clusters import TestEskapadeCluster

import os
import base
import json
import unittest


class TestEskapadeBranch(TestEskapadeCluster):
    """
    Tests Eskapade master branch.
    Downloads master branch from the Git repository and points Eskapade installation to that.
    To test other branch, change eskapade_branch field.

    Prerequisites:
        Add EskapadeOrigin=git@gitlab-nl.dna.kpmglab.com:decision-engine/eskapade.git under GIT in $AWSSECCONF file.

    Use:
        run `./test.sh integration/test_eskapade_branch.py`.
    """
    # TODO: Parse Eskapade branch from command line.
    eskapade_branch = "master"

    def _parse_git_conf(self):
        """
        Parses AWSSECCONF security conf file.
        :return: Git key location and Eskapade Git origin.
        """
        json_file = open(os.path.expanduser(os.environ["AWSSECCONF"]))
        security_config = json.loads(json_file.read())
        json_file.close()

        self.assertTrue("GIT" in security_config["AccessKeys"], "You need to specify GIT in AWSSECCONF.")
        gitenv = security_config["AccessKeys"]["GIT"]

        self.assertTrue("KeyFile" in gitenv, "You need to specify GIT KeyFile in AWSSECCONF")
        git_key_location = gitenv["KeyFile"]
        self.assertTrue("EskapadeOrigin" in gitenv, "You need to specify EskapadeOrigin in AWSSECCONF.")
        git_origin = gitenv["EskapadeOrigin"]
        return git_key_location, git_origin

    def check_eskapade(self, host, version="*"):
        git_key_location, git_origin = self._parse_git_conf()
        if not host.gitprep:
            print("Preparing Git...")
            host.prep_git(git_key_location, git_origin=git_origin)
        install_dir = "/opt/Eskapade/{}".format(self.eskapade_branch)
        host.run("rm -rf {}".format(install_dir))

        br = "-b " + self.eskapade_branch
        host.git("clone {branch} {origin} {dir}".format(branch=br, origin=git_origin, dir=install_dir))

        super(TestEskapadeBranch, self).check_eskapade(host, self.eskapade_branch)


if __name__ == "__main__":
    import sys

    verbose = False
    clustername = None
    if "--verbose" in sys.argv:
        verbose = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    branch = "__local__"
    if "--branch" in sys.argv:
        branch = "__service__"
        sys.argv = [s for s in sys.argv if s != "--branch"]
    if "--this-branch" in sys.argv:
        branch = "__local__"
        sys.argv = [s for s in sys.argv if s != "--this-branch"]
    if "--prod" in sys.argv:
        clustername = 'prod'
        sys.argv = [s for s in sys.argv if s != "--prod"]
    if len(sys.argv) < 1:
        raise KeyError("You must specify which blueprint/cluster to test")
    service = "ESKAPADE-HEAD"
    test = TestEskapadeBranch()
    test.service = service
    test.debug = verbose
    test.clustername = clustername
    test.branch = branch
    test.branchtype = branch
    test.checklist = []
    if len(sys.argv) > 1:
        test.checklist = sys.argv[1:]
    suite = unittest.TestSuite()
    suite.addTest(test)
    base.run(suite)