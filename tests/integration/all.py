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
import clusters
import base
import glob
import os

mods = [clusters]


blueprints = glob.glob(os.path.dirname(__file__) + "/blueprints/*.blueprint.json")

disabled = ["everything", "bbdemo"]

blueprints = [b.split("/")[-1].split(".")[0] for b in blueprints]
blueprints = [b for b in blueprints if b not in disabled]

if __name__ == "__main__":
    base.parallel(mods, blueprints)
