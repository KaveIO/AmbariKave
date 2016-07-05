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
This wonderful script is going to help me create and test 100 different regular expressions
Usage:
    --apply json_filename
    --create json_filename
    --test json_filename
    --restore

--apply, perform all SED as given in this json file, makes a .rebak copy of each file
--create, create a new json file with a new list of regex
--test, check that a given json file contains the correct seds
        for this machine and that the result of applying these seds worked
--restore, find all .rebak files, and overwrite any recent changes with these
--debug, print out some extra status information and commands

"""
import re
import os
import glob
import subprocess

# ###############################################################################
# Global steering parameters
# These parameters are only required in the creation and testing of a json file
# they are not used during the application of the sed
#

debug = False
# Which file names to completely ignore on finding the regex
ignore_files = ['cacerts', 'jisfreq.py', 'euctwfreq.py',
                'big5freq.py', 'cacert.pem', 'unistring.py']
# Which file directories to completely ignore on finding the regex
ignore_dirs = ['/etc/pki/pki-tomcat/ca/archives']
# Which file extentions to completely ignore on finding the regex
skip_endings = ['so', 'pyc', 'pem', 'cert', 'bin', 'exe', 'sh', 'pyo', 'bak', 'bkp', 'ipabkp', 'rebak']
# Which lines to completely ignore on finding the regex
ignore_matches = ["#ServerName www.example.com:8443"]
# Which file extentions to completely ignore on finding the regex
comment_in_manually = ["#CONNECTOR_PORT", "# pki_https_port", "# pki_http_port", "#CONNECTOR_PORT"]

ignore_file_matches = {}

start_insecure = '8080'
start_secure = '8443'
pki_insecure_port = '8081'
pki_secure_port = '8444'

sed_searches = {start_insecure: '[0-9][0-9][0-9][0-9]',
                start_secure: '[0-9][0-9][0-9][0-9]'}
sed_escapes = '\\/().*[]|+'
sed_replaces = {start_insecure: '{{pki_insecure_port}}', start_secure: '{{pki_secure_port}}'}
non_dynamic_replaces = {'{{pki_insecure_port}}': pki_insecure_port, '{{pki_secure_port}}': pki_secure_port}

dir_search = ["/etc/sysconfig", "/etc/tomcat", "/etc/pki",  # "/etc/httpd", #HTTPD should __not__ be modified!
              "/etc/pki-tomcat", "/usr/lib/python*/site-packages/ipa*", "/usr/lib/python*/site-packages/pki*"]

# ###############################################################################
# Functional definitions


def find_all_matches(search):
    """
    Iterate through a search path, find all strings matching start_insecure or start_secure
    return the files/line-numbers/line-content so long as they dont'appear in
    the ignore_files or ignore_matches
    """
    found = []
    for adir in search:
        for sdir in glob.glob(adir):
            if debug:
                print 'searching', sdir
            if not os.path.exists(sdir):
                continue
            if sdir in ignore_dirs:
                continue
            for root, dirs, files in os.walk(sdir):
                if root in ignore_dirs:
                    continue
                for afile in files:
                    if afile in ignore_files:
                        # print "ignoring", afile
                        continue
                    if '.' in afile and afile.split('.')[-1] in skip_endings:
                        continue
                    if not os.path.isfile(root + '/' + afile):
                        # print "nofile", afile
                        continue
                    if not os.access(root + '/' + afile, os.R_OK):
                        # print "unreadable", afile
                        continue
                    try:
                        # print "trying", afile
                        with open(root + '/' + afile) as fp:
                            for i, line in enumerate(fp):
                                line = line.replace('\n', '')
                                if start_insecure in line or start_secure in line:
                                    if line in ignore_matches:
                                        continue
                                    if afile in ignore_file_matches and line in ignore_file_matches[afile]:
                                        continue
                                    found.append((root + '/' + afile, i + 1, line))
                    except IOError, UnicodeDecodeError:
                        continue
            if debug and len(found):
                print 'so far I have found', len(found)
    return found


def commentstrip(line):
    '''
    Some comments in files I need to manually comment in myself
    This small function is reused several times
    '''
    if line.strip().startswith('#'):
        for fc in comment_in_manually:
            if line.strip().startswith(fc):
                line = line.replace("# ", "").replace("#", "")
    return line


def sed_from_matches(matches):
    """
    Take a list of strings, and return a list of strings with all the sed replaces
    """
    ret = []
    for line in matches:
        iret = line + ''
        for sesc in sed_escapes:
            # print 'replacing ', sesc
            iret = iret.replace(sesc, '\\' + sesc)
            # print iret
        search = iret + ''
        for searchk, searchv in sed_searches.iteritems():
            search = search.replace(searchk, searchv)
        search = search.replace("\n", "")
        addl = (len(search.lstrip()) != len(search))
        addr = (len(search.rstrip()) != len(search))
        search = '\s*'.join(search.split())
        if addl:
            search = '\s*' + search
        if addr:
            search = search + '\s*'
        replace = iret + ''
        for replacek, replacev in sed_replaces.iteritems():
            replace = replace.replace(replacek, replacev)
        replace = replace.replace("\n", "")
        replace = commentstrip(replace)
        ret.append((search, replace))
        # duplicate to also allow changes after the comment is replaced
        searchc = commentstrip(search)
        if searchc != search:
            ret.append((searchc, replace))
    return ret


def create_match_dictionary(saveas=None):
    """
    Combines all above functions, reads the local filesystem for matches,
    then returns a a complex dictionary
    filename: [(line_number, original, search, replace, expected)]
    """
    c7_dict = {}
    if debug:
        print 'generate dictionary'
    i = 0
    for filename, linenum, line in find_all_matches(dir_search):
        i = i + 1
        search, replace = sed_from_matches([line])[0]
        expected = line.replace(start_secure, pki_secure_port)
        expected = expected.replace(start_insecure, pki_insecure_port)
        expected = commentstrip(expected)
        try:
            c7_dict[filename].append((linenum, line, search, replace, expected))
        except KeyError:
            c7_dict[filename] = [(linenum, line, search, replace, expected)]
    if saveas is not None:
        import json
        with open(saveas, 'w') as fp:
            json.dump(c7_dict, fp)
        if debug:
            print 'wrote', saveas
    if debug:
        print 'found/created', i, 'seds from', len(c7_dict), 'files'
    return c7_dict


def apply_regex_from_json(regexdict):
    """
    When supplied with a dictionary, will sed every file for the regex list provided
    filename: [(line_number, original, search, replace, expected)]
    runs:
    sed -i 's/search/replace/' filename
    """
    if debug:
        print "modifying", len(regexdict), 'files'
    for afile, lines in regexdict.iteritems():
        if debug:
            print len(lines), "lines in", afile
        for linenum, original, search, replace, expected in lines:
            if not os.path.exists(afile + '.rebak'):
                process = subprocess.Popen(['cp', '-f', afile, afile + '.rebak'])
            # run the replaces in case this is not done dynamically by ambari
            for r, v in non_dynamic_replaces.iteritems():
                replace = replace.replace(r, v)
            command = ['sed', '-i', '-r', 's/^' + search + '/' + replace + '/', afile]
            if debug:
                print command
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = process.communicate()
            if debug:
                print output


def check_original_from_json(regexdict):
    """
    When supplied with a dictionary will check that the original os-installed files provided
     do have the lines written in the right places
    filename: [(line_number, original, search, replace, expected)]
    """
    for afile, lines in regexdict.iteritems():
        if os.path.exists(afile + '.rebak'):
            afile = afile + '.rebak'
        orig_lines = []
        if not os.path.exists(afile):
            raise NameError('The file I should be editing/checking does not exist! ' + afile)
        with open(afile) as fp:
            orig_lines = fp.readlines()
        for linenum, original, search, replace, expected in lines:
            if debug:
                print 'checking',  afile, linenum, original
            if len(orig_lines) < linenum:
                raise ValueError("File not long enough! " + afile + " linenum " + str(linenum))
            if orig_lines[int(linenum) - 1].replace('\n', '') != original:
                if original.startswith("#"):
                    # ignore commented-out lines, not important
                    continue
                # Don't worry about manually commented-in lines
                flag = False
                for comment_removal in comment_in_manually:
                    if original.startswith(commentstrip(comment_removal)):
                        flag = True
                if not flag:
                    raise ValueError("Expected line to replace not found! "
                                     + afile + " linenum " + str(linenum)
                                     + " " + original)

def check_sed_directly(regexdict):
    """
    When supplied with a dictionary will check that the original os-installed files provided
     do have the lines written in the right places
    filename: [(line_number, original, search, replace, expected)]
    """
    for afile, lines in regexdict.iteritems():
        for linenum, original, search, replace, expected in lines:
            # run the replaces in case this is not done dynamically by ambari
            for r, v in non_dynamic_replaces.iteritems():
                replace = replace.replace(r, v)
            if debug:
                print 'checking',  original, search, replace, expected

        command = ['sed', '-r', 's/^' + search + '/' + replace + '/']
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = process.communicate(input = original+'\n')
        if output[0].replace('\n','') != expected:
            print 'checking',  original, search, replace, expected
            print 'failed, resulted in ', output
            raise ValueError("This regular expression does not work " + search)


def check_changed_from_json(regexdict):
    """
    When supplied with a dictionary will check that the overwritten sed-ed files
     do have the expected lines written in the right places
    filename: [(line_number, original, search, replace, expected)]
    """
    for afile, lines in regexdict.iteritems():
        changed_lines = []
        with open(afile) as fp:
            changed_lines = fp.readlines()
        for linenum, original, search, replace, expected in lines:
            if debug:
                print 'checking',  afile, linenum, expected
            if len(changed_lines) < linenum:
                raise ValueError("File not long enough! " + afile + " linenum " + str(linenum))
            if changed_lines[int(linenum) - 1].replace('\n', '') != expected:
                raise ValueError("Expected line not replaced! "
                                 + afile + " linenum " + str(linenum)
                                 + " " + expected)


def check_for_line_changes(check_this_default_dict, against_this_dynamic_dict):
    """
    Check if additional regexs need to be added to the json file
    Provided with two dictionaries will compare what should have been there
    raises a Value Error if anything is missing.
    """
    if debug:
        print 'checking for new/changed regex'
    missing_files = [f for f in check_this_default_dict if f not in against_this_dynamic_dict]
    new_files = [f for f in against_this_dynamic_dict if f not in check_this_default_dict]
    missing_lines = [[f] + list(v) for f, v in check_this_default_dict.iteritems()
                     if f in against_this_dynamic_dict and v[0] not in
                     [v[0] for k, v in against_this_dynamic_dict[f].iteritems()]]
    new_lines = [[f] + list(v) for f, v in against_this_dynamic_dict.iteritems()
                 if f in check_this_default_dict and v[0] not in
                 [v[0] for k, v in check_this_default_dict[f].iteritems()]]

    if len(missing_files + new_files + missing_lines + new_lines):
        print "Missing files: ", missing_files
        print "Missing lines: ", missing_lines
        print "New files: ", new_files
        print "New lines: ", new_lines
        raise ValueError("New regexs need to be added to this json file")

def restore_from_backup(search):
    """
    Same search, but now find/restore any rebak files encountered
    """
    for adir in search:
        for sdir in glob.glob(adir):
            if debug:
                print 'searching', sdir
            if not os.path.exists(sdir):
                continue
            if sdir in ignore_dirs:
                continue
            for root, dirs, files in os.walk(sdir):
                if root in ignore_dirs:
                    continue
                for afile in files:
                    if afile.endswith('.rebak'):
                        if debug:
                            print 'restoring', afile
                        process = subprocess.Popen(['mv', root + '/' + afile, root + '/' + afile[:-len('.rebak')]]
                                                   , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        output = process.communicate()
                        if debug:
                            print output

# ###############################################################################
# Main program

if __name__ == "__main__":
    import sys
    if '--help' in sys.argv:
        print __doc__
        sys.exit(0)
    if '--debug' in sys.argv:
        global debug
        debug = True
        sys.argv = [s for s in sys.argv if s!='--debug']
    if len(sys.argv) < 3 and '--restore' not in sys.argv:
        print __doc__
        raise AttributeError("Please supply a mode and filename")
    if len(sys.argv) < 2:
        print __doc__
        raise AttributeError("Please supply a mode")
    if sys.argv[1] not in ['--apply', '--create', '--test', '--restore']:
        print __doc__
        raise AttributeError("Please supply a valid mode")
    mode = sys.argv[1]
    filename = sys.argv[-1]
    if mode == '--create':
        create_match_dictionary(filename)
    elif mode == '--restore':
        restore_from_backup(dir_search)
    else:
        if not os.path.exists(filename):
            print __doc__
            raise IOError('the file you supply must exist!')
        loaded = {}
        import json
        with open(filename) as fp:
            loaded = json.load(fp)
        if not len(loaded):
            print __doc__
            raise IOError('Unable to interpret json file, file empty or corrupt')
        if mode == '--apply':
            apply_regex_from_json(loaded)
        else:
            check_sed_directly(loaded)
            check_original_from_json(loaded)
            check_changed_from_json(loaded)
            dynamic = create_match_dictionary()
            check_for_line_changes(loaded, dynamic)
