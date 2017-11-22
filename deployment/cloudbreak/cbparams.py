##############################################################################
#
# Copyright 2017 KPMG Advisory N.V. (unless otherwise stated)
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
kave_version = "33-beta"
cb_http_url = "http://<cloudbreak pub. IP>"
cb_https_url = "https:///<cloudbreak pub. IP>"
uaa_port = 8089
cb_username = "admin@example.com"
cb_password = "<cloudbreak account password>"
credential_name = "<cloudbreak credential name>"
adls_enabled = False
adls_name = "<Azure Data Lake Store name>"
ssl_verify = False
recipes = {
    "patchambari":
    {
        "recipeType": "PRE",
        "description": "Add the KAVE Stack to ambari",
        "templatePath": "recipes/mandatory/setup_cloudbreak_kavepatch_ambari.sh"
    },
    "fix-hosts-file":
    {
        "recipeType": "PRE",
        "description": "Fix hosts file on all nodes",
        "templatePath": "recipes/mandatory/setup_cloudbreak_fixhostsfile_all.sh"
    },
    "distibute-private-key":
    {
        "recipeType": "PRE",
        "description": "Distribute private key on all nodes",
        "templatePath": "recipes/mandatory/setup_cloudbreak_keydistrib_all.sh"
    },
    "limit-ssh-attempts":
    {
        "recipeType": "PRE",
        "description": "Limit unsuccessful ssh attempts rate",
        "templatePath": "recipes/mandatory/limit-ssh-attempts.sh"
    }}
