#! /usr/bin/env python
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
# Will find py files and sh files without the license and ask you if you want to add it ...

import os, sys, re

license_from = os.path.abspath(os.path.dirname(__file__) + "/../LICENSE")
#this list is a list of things that we don't want to check
ignore_regex = ['.*/build/.*']
accept_regex = ['.*\.sh$', '.*\.py$']
#check they exist at least twice in service.sh

#
# Load the license from the license file
#
licf = open(license_from)
license = licf.read()
licf.close()


#
# Find all files without a license
#

#import fnmatch
dir = os.path.realpath(os.path.dirname(__file__) + "/../")
all_files = []
skip = False
for root, dirnames, filenames in os.walk(dir):
    skip = False
    for ignore_path in ignore_regex:
        if re.match(ignore_path, root):
            skip = True
            break
    if skip:
        continue
    for filename in filenames:
        all_files.append(os.path.join(root, filename))
no_license = []
ignore = []
matches = []
check_contains = "http://www.apache.org/licenses/LICENSE-2.0"
for toignore in ignore_regex:
    r = re.compile(toignore)
    ignore = ignore + filter(r.match, all_files)
for tofind in accept_regex:
    r = re.compile(tofind)
    matches = matches + filter(r.match, all_files)
#print matches[:10], ignore[:10]
matches = [f for f in matches if f not in ignore]
for f in matches:
    fop = open(f)
    fos = fop.read()
    fop.close()
    if check_contains not in fos:
        no_license.append(f)

print "Found:", len(no_license), "files without licenses"

#
# Prompt and then add to those files ...
#

print "Going through one-by-one to add them"

yes = set(['yes', 'y', 'ye'])
failed = []

for afile in no_license:
    print "-----------------------------------------------"
    print afile, "first 10 lines:"
    fop = open(afile)
    fos = fop.readlines()
    fop.close()
    end = 10
    if len(fos) < 10:
        end = -1
    print "".join(fos[:end])
    print "-----------------------------------------------"
    yn = raw_input("Add license? [Y/n]").lower().strip()
    if yn.lower() not in yes:
        continue
    pos = 0
    if fos[0].startswith('#!'):
        pos = 1
    fop = open(afile, 'w')
    fop.write(''.join(fos[:pos]))
    fop.write(license)
    fop.write(''.join(fos[pos:]))
    fop.close()
    #double check !!
    fop = open(afile)
    fos = fop.read()
    fop.close()
    if check_contains not in fos:
        failed.append(f)
        print "Error, wasn't added correctly!"
    print "OK, done, next ..."

if len(failed):
    print "Error: failed to add to", len(failed), " files"
    sys.exit(1)
