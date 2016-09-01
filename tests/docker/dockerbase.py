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
"""
Shared functions for working with docker containers in subprocesses
"""
import subprocess
import sys
import os


class DockerRun(object):
    """
    Enter is docker run, creates a bash-liek subprocess which is killed on exit
    """

    def __init__(self, image, options=[],
                 stdout=None, stderr=None,
                 stdin=subprocess.PIPE):
        self.image = image
        self.options = options
        self.process = None
        self.stdout = stdout
        self.stdin = stdin
        self.stderr = stderr

    def __enter__(self):
        self.process = subprocess.Popen(["docker", "run"] + self.options
                                        + ["-i", self.image, "/bin/bash"],
                                        stdin=self.stdin,
                                        stdout=self.stdout,
                                        stderr=self.stderr)
        return self

    def run(self, cmd, logfile=None):
        if logfile is not None:
            cmd = cmd + ' | tee -a ' + logfile
        self.process.stdin.write(cmd + '\n')
        self.process.stdin.flush()

    def finalcommand(self, cmd):
        _stdout, _stderr = self.process.communicate(cmd + '\n')
        return self.process.returncode, _stdout, _stderr

    def __exit__(self, *args, **kwargs):
        print args, kwargs
        if self.process is None:
            return
        else:
            try:
                self.process.communicate('exit\n')
            except:
                pass
            try:
                self.process.kill()
            except OSError:
                pass

        return self


class DockerRunInit(object):
    """
    Docker is started with an init command, then an exec is connected to it
    """

    def __init__(self, image, options=[],
                 stdout=None, stderr=None,
                 stdin=subprocess.PIPE):
        self.image = image
        self.options = options
        self.process = None
        self.stdout = stdout
        self.stdin = stdin
        self.stderr = stderr

    def __enter__(self):
        self.iprocess = subprocess.Popen(["docker", "run"] + self.options
                                         + ["-v", "/sys/fs/cgroup:/sys/fs/cgroup:ro"]
                                         + ["--privileged", "-e", "container=docker"]
                                         + ["-i", self.image, "/usr/sbin/init"],
                                         stdout=subprocess.PIPE)
        containers = subprocess.Popen(["docker", "ps"], stdout=subprocess.PIPE)
        containers = containers.communicate()[0].split('\n')
        container = [c.split()[0] for c in containers if self.image in c]
        self.process = subprocess.Popen(["docker", "exec"]
                                        + ["-i", container, "/bin/bash"],
                                        stdin=self.stdin,
                                        stdout=self.stdout,
                                        stderr=self.stderr)
        return self

    def run(self, cmd, logfile=None):
        if logfile is not None:
            cmd = cmd + ' | tee -a ' + logfile
        self.process.stdin.write(cmd + '\n')
        self.process.stdin.flush()

    def finalcommand(self, cmd):
        _stdout, _stderr = self.process.communicate(cmd + '\n')
        return self.process.returncode, _stdout, _stderr

    def __exit__(self, *args, **kwargs):
        print args, kwargs
        if self.process is None:
            return
        else:
            try:
                self.process.communicate('exit\n')
            except:
                pass
            try:
                self.process.kill()
                self.process.ikill()
            except OSError:
                pass

        return self
