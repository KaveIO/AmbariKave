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


class jsonbpchecks(base.LDTest):

    def runTest(self):
        """
        Tests which read all blueprints/aws/clusterfiles and verify consistency
        """
        import kavedeploy as lD
        import os

        deploydir = os.path.dirname(lD.__file__)
        testdir = os.path.dirname(__file__)
        import glob
        # find all json files
        jsons = glob.glob(deploydir + "/*/*.json") + glob.glob(testdir + "/../*/*.json") + glob.glob(
            testdir + "/../*/*/*.json")
        # check json completeness
        interpreted = {}
        for ason in jsons:
            interpreted[ason] = self.check_json(ason)
        # verify .aws files
        for ason in jsons:
            if ason.endswith('.aws.json'):
                self.verify_awsjson(interpreted[ason], ason)
        # verify blueprint files
        for ason in jsons:
            if ason.endswith('.blueprint.json'):
                self.verify_bpjson(interpreted[ason], ason)
        # do grouped consistency tests
        groups = {}
        for ason in jsons:
            cat = '.'.join(ason.split('.')[:-2])
            self.service = ason.split('/')[-1].split('.')[1]
            try:
                groups[cat].append(ason)
            except KeyError:
                groups[cat] = [ason]
        for k, group in groups.iteritems():
            if len(set(group)) == 3:
                self.verify_blueprint(k + '.aws.json', k + '.blueprint.json', k + '.cluster.json')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(jsonbpchecks())
    return suite


if __name__ == "__main__":
    base.run(suite())
