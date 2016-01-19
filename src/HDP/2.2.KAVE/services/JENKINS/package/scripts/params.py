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
from resource_management import *

config = Script.get_config()

hostname = config["hostname"]

JENKINS_HOME = default("configurations/jenkins/JENKINS_HOME", "/var/lib/jenkins")
JENKINS_PORT = default("configurations/jenkins/JENKINS_PORT", "8080")
#JENKINS_USER = default("configurations/jenkins/JENKINS_USER", "jenkins")
JENKINS_ADMIN = default("configurations/jenkins/JENKINS_ADMIN", "admin")
JENKINS_USER = config['configurations']['jenkins']['JENKINS_USER']
JENKINS_USER_PASSWORD = config['configurations']['jenkins']['JENKINS_USER_PASSWORD']
download_version = default("configurations/jenkins/download_version", "1.624")
plugins = default("configurations/jenkins/plugins",
                  "ghprb, git, git-client, github, github-api, gitlab-merge-request-jenkins, gitlab-hook, "
                  "gitlab-plugin, git-parameter, git-tag-message, matrix-project, "
                  "scm-api, ssh-agent, sonar, sonargraph-plugin")
