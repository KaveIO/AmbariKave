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
from resource_management import *
import kavecommon as kc


config = Script.get_config()

hostname = config["hostname"]

JENKINS_HOME = kc.default("configurations/jenkins/JENKINS_HOME", "/var/lib/jenkins", kc.is_valid_directory)
JENKINS_PORT = kc.default("configurations/jenkins/JENKINS_PORT", "8080", kc.is_valid_port)
JENKINS_HTTPS_PORT = kc.default("configurations/jenkins/JENKINS_HTTPS_PORT", "8443", kc.is_valid_port)
JENKINS_USER = kc.default("configurations/jenkins/JENKINS_USER", "jenkins", kc.is_valid_username)
JENKINS_ADMIN = kc.default("configurations/jenkins/JENKINS_ADMIN", "admin", kc.is_valid_username)
JENKINS_ADMIN_EMAIL = default("configurations/jenkins/JENKINS_ADMIN_EMAIL", "default")


if JENKINS_ADMIN_EMAIL == 'default':
    JENKINS_ADMIN_EMAIL = JENKINS_ADMIN + '@' + '.'.join(hostname.split('.')[1:])
kc.is_valid_emailid(JENKINS_ADMIN_EMAIL, "jenkins/JENKINS_ADMIN_EMAIL")

JENKINS_ADMIN_PASSWORD = config['configurations']['jenkins']['JENKINS_ADMIN_PASSWORD']
Logger.sensitive_strings[JENKINS_ADMIN_PASSWORD] = "[PROTECTED]"

download_version = default("configurations/jenkins/download_version", "1.642")
plugins = default("configurations/jenkins/plugins",
                  "ghprb, git, git-client, github, github-api, gitlab-merge-request-jenkins, gitlab-hook, "
                  "gitlab-plugin, git-parameter, git-tag-message, matrix-project, "
                  "scm-api, ssh-agent, sonar, sonargraph-plugin")
