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
"""
Common code for multiple tests and simplified wrappers for running tests

run(mods) and parallel(mods,modargs) are wrappers for running existing test modules as a suite
^ in sequence   ^in multiple subprocesses

findServices is a helper function to return a list of services present in a given stack of this checkout

LDTest is a derived test case class from unittest.TestCase, adding common methods for running tests on newly-created
aws machines
"""
import unittest
import sys
import os
import glob
import threading
import thread
import Queue
import subprocess as sub


def findServices(stack="HDP/2.2.KAVE/services"):
    """
    Nice little helper function which lists all our services.
    returns a list of [(service-name, directory)]
    """
    dir = os.path.realpath(os.path.dirname(__file__) + "/../../")
    services = glob.glob(dir + "/src/" + stack + "/*")
    return [(s.split('/')[-1], s) for s in services if os.path.isdir(s)]


def run(mods):
    """
    Wrapper for unittest running of test suite in sequence, collecting results and exiting on failure
    mods is either a single unittest.TestSuite object, or a list of python modules that each declared a suite() method

    for a wrapper which runs test in parallel instead, see the parallel method of this module
    """
    suite = None
    if type(mods) is unittest.TestSuite:
        suite = mods
    else:
        suite = unittest.TestSuite([mod.suite() for mod in mods])

    res = unittest.TextTestRunner(verbosity=2).run(suite)
    # print dir(res)
    # print res.errors, res.failures
    if len(res.errors) == 0 and len(res.failures) == 0:
        sys.exit(0)
    sys.exit(1)


#
# unittest does not come with a way to run test in parallel, so I must design that here, the parallel method is the
# equivalent of the run() method
#

class LockOnPrintThread(threading.Thread):
    """
    A threading class which locks before printing a result,
    method should be replaced with your own method returning a
    string for printing
    """

    def __init__(self, pool, lock):
        """
        pool should be a Queue.Queue object
        lock, a thread.lock object
        """
        threading.Thread.__init__(self)
        self.lock = lock
        self.pool = pool
        self.done = False

    def run(self):
        """
        The main sequence, method, lock, print, unlock
        """
        while not self.done:
            try:
                item = self.pool.get_nowait()
                if item is not None:
                    result = self.method(self, item)
                    self.lock.acquire()
                    print result.strip()
                    self.lock.release()
            except Queue.Empty:
                self.done = True

    def method(self, item):
        """
        A const method on any class variables, must return a string
        or an exception
        """
        raise ImportError("do not call the baseclass method!")


class RunFileInSubProcess(LockOnPrintThread):
    """
    Class derived from lockOnPrintThread to re-implement run method. In this case the item list sent, the queue must
    be a series of commands to be run in subprocesses
    These commands are checked for status, and then locking is done before printing their stdout/err in case of failure.
    """

    def __init__(self, pool, lock, result):
        """
        pool should be a Queue.Queue object
        lock, a thread.lock object
        """
        threading.Thread.__init__(self)
        self.lock = lock
        self.islockedbyme = False
        self.pool = pool
        self.done = False
        self.result = result
        self.errors = []
        self.margs = []

    def run(self, limit=100):
        """
        The main sequence, method, lock, adjust, unlock
        """
        looping = 0
        while not self.done and looping < limit:
            looping = looping + 1
            try:
                item = self.pool.get_nowait()
                if item is not None:
                    self.lock.acquire()
                    self.islockedbyme = True
                    myname = item.replace(os.path.realpath(os.path.dirname(__file__) + "/../") + "/", "")
                    myname = myname.replace("python ", "").replace(".py", "")
                    print "started:", myname
                    sys.__stdout__.flush()
                    self.lock.release()
                    self.islockedbyme = False
                    proc = sub.Popen(item, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
                    stdout, stderr = proc.communicate()
                    status = proc.returncode
                    self.lock.acquire()
                    self.islockedbyme = True
                    self.result[item]["stdout"] = stdout
                    self.result[item]["stderr"] = stderr
                    self.result[item]["status"] = status
                    import datetime

                    if not status:
                        print myname, "... OK"
                    else:
                        print myname, "... ERROR"
                        print myname, datetime.datetime.utcnow().strftime('%a %b %d %H:%M:%S UTC %Y')
                        print myname, " details: exited with ", status
                        print stdout
                        print stderr
                    sys.__stdout__.flush()
                    self.lock.release()
                    self.islockedbyme = False
            except Queue.Empty:
                self.done = True
                if self.islockedbyme:
                    try:
                        self.lock.release()
                        self.islockedbyme = False
                    except:
                        self.islockedbyme = False
            except Exception as e:
                print "Exiting a thread due to Error: " + str(e)
                err1, err2, err3 = sys.exc_info()
                self.errors.append(str(e) + " " + str(err1) + " " + str(err2) + "\n" + str(err3))
                if self.islockedbyme:
                    try:
                        self.lock.release()
                        self.islockedbyme = False
                    except:
                        self.islockedbyme = False


def parallel(mods, modargs=[]):
    """
    Run a set of tests in parallel, rather than in sequence, then collect and print their results.
    Mods is a set of python modules, and then each of their corresponding files is run with arguments from modargs,
    assuming the files are executable with python

    mods: python modules containing tests. Each module must be runnable with python mod.__file__, which usually means
    each file
         needs a runnable __main__ which runs some tests
    modargs: set of args which can be passed to each mod
        if it is a list, each entry of the list will be iterated over with the mod (sub-lists will be hjoined with "
        ".join() )
        if it is a dictionary of mod : [list] each entry in the list will be iterated over for the corresponding mod
        (sub-lists will be joined with " ".join() )
    e.g. mods=[foo,bar,fish], modargs={'foo':["spam","eggs"], 'bar':[["spam","and","eggs"]]} will run four tests in
    parallel:
        python foo.__file__ spam
        python foo.__file__ eggs
        python bar.__file__ spam and eggs
        python fish.__file__
    """
    # loop over threads, see the class for more details
    # create list of packages as a queue
    itemPool = Queue.Queue()
    result = {}
    items = []
    if not len(modargs):
        items = ["python " + mod.__file__.replace('.pyc', ".py") for mod in mods]
    elif type(modargs) is list:
        for mod in mods:
            for arg in modargs:
                if type(arg) is list:
                    arg = " ".join(arg)
                items.append("python " + mod.__file__.replace('.pyc', ".py") + " " + arg)
    elif type(modargs) is dict:
        for mod in mods:
            if mod not in modargs:
                items.append("python " + mod.__file__.replace('.pyc', ".py"))
                continue
            args = modargs[mod]
            # just a single arguement
            if type(args) is not list:
                items.append("python " + mod.__file__.replace('.pyc', ".py") + " " + args)
                continue
            # empty list
            if not len(args):
                items.append("python " + mod.__file__.replace('.pyc', ".py"))
                continue
            for arg in args:
                if type(arg) is list:
                    arg = " ".join(arg)
                items.append("python " + mod.__file__.replace('.pyc', ".py") + " " + arg)
    else:
        raise ValueError("failed to interpret mod and modargs")
    # print items
    for item in items:
        result[item] = {}
        itemPool.put(item)
    lock = thread.allocate_lock()
    thethreads = []
    for _i in range(20):
        t = RunFileInSubProcess(itemPool, lock, result)
        thethreads.append(t)
        t.start()
    # setup a timeout to prevent really infinite loops!
    import datetime
    import time

    begin = datetime.datetime.utcnow()
    timeout = 60 * 60 * 3
    for t in thethreads:
        while not t.done:
            if (datetime.datetime.utcnow() - begin).seconds > timeout:
                break
            time.sleep(0.1)
    nd = [t for t in thethreads if not t.done]
    errs = []
    for t in thethreads:
        errs = errs + t.errors
    if len(errs):
        raise RuntimeError("Exceptions encountered while running tests as threads, as: \n" + '\n'.join(errs))
    # print result
    FAILED = len([f for f in result if result[f]["status"] != 0])
    TIMES = []
    TESTS = []
    for key, val in result.iteritems():
        timing = [l for l in val["stderr"].split("\n") if l.startswith("Ran") and " in " in l][0].strip()
        if len(timing):
            TIMES.append(float(timing.split(" ")[-1].replace("s", "")))
            TESTS.append(int(timing.split(" ")[1]))
    print "======================================================================"
    print "Ran", sum(TESTS), "tests in", sum(TIMES).__str__() + "s", "from", len(result), "module/args"
    print
    if FAILED == 0 and len(nd) == 0:
        print "OK"
        sys.exit(0)
    if FAILED:
        print "FAILED (modules=" + str(FAILED) + ")"
    if len(nd):
        print "TIMEOUT (modules=" + str(len(nd)) + ")"
    sys.exit(1)


class LDTest(unittest.TestCase):
    """
    Derived unit test class for tests we want to run on remote aws machines. This contains simple helper functions
    common to other tests
    No runTest method is defined here, that is for you to implement.
    usually:
    self.service='some-service-name'
    self.checklist=[list of websites or files to check exist after install]
    lD=self.preCheck()
    ambari,iid=self.deployDev()
    self.waitForAmbari(ambari)
    stdout=ambari.run ... some installation commands
    self.assert("PASS" in stdout)
    self.check() #verify the checklist is present
    """
    debug = False
    branch = "__local__"
    branchtype = "__local__"

    def preCheck(self):
        """
        Check that security config exists and that lD library is importable
        """
        import kavedeploy as lD
        import kaveaws as lA

        lD.debug = self.debug
        lD.strict_host_key_checking = False
        import os

        if "AWSSECCONF" not in os.environ:
            raise SystemError(
                "You need to set the environment variable AWSSECCONF to point to your security config file before "
                "running this test")
        self.assertTrue(lA.testaws(), "Local aws installation incomplete, try again")
        self.assertTrue(len(lA.detectRegion()) > 0, "Failed to detect aws region, have you run aws configure?")
        import json

        jsondat = open(os.path.expanduser(os.environ["AWSSECCONF"]))
        l = jsondat.read()
        jsondat.close()
        # print l
        security_config = json.loads(l)
        # print lD.checksecjson(security_config)
        self.assertTrue(lA.checksecjson(security_config),
                        "Security config not readable correctly or does not contain enough keys!")
        if self.branch == "__local__":
            self.branch = lD.runQuiet(
                "bash -c \"cd " + os.path.dirname(__file__) + "; git branch | sed -n '/\* /s///p'\"")
        if self.branch == "__service__":
            self.branch = self.service
        if self.branch is not None:
            stdout = lD.runQuiet("bash -c 'cd " + os.path.dirname(__file__) + "; git branch -r;'")
            self.assertTrue("origin/" + self.branch in [s.strip() for s in stdout.split() if len(s.strip())],
                            "There is no remote branch called " + self.branch + " push your branch back to the origin "
                                                                                "to run this automated test")
        return lD

    def deployDev(self, itype=None):
        """
        Up one centos machine with the scripts and return an lD.remoteHost to that machine
        itype -> None: c3.large
        """
        import kavedeploy as lD

        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        stdout = ""
        if itype is None:
            stdout = lD.runQuiet(
                deploy_dir + "/aws/deploy_one_centos_instance.py Test-" + self.service + " --ambari-dev --not-strict")
        else:
            stdout = lD.runQuiet(
                deploy_dir + "/aws/deploy_one_centos_instance.py Test-" + self.service + " " + itype + " --ambari-dev "
                                                                                                       "--not-strict")
        self.assertTrue(stdout.split("\n")[-1].startswith("OK, iid "))
        iid = stdout.split("\n")[-1].strip()[len("OK, iid "):].split(" ")[0]
        ip = stdout.split("\n")[-1].strip().split(" ")[-1]
        self.assertTrue(stdout.split("\n")[-3].startswith("connect remotely with:"))
        connectcmd = stdout.split("\n")[-2]
        self.assertTrue(ip in connectcmd, "wrong IP seen in (" + connectcmd + ")")
        jsondat = open(os.path.expanduser(os.environ["AWSSECCONF"]))
        import json

        acconf = json.loads(jsondat.read())
        jsondat.close()
        keyfile = acconf["AccessKeys"]["SSH"]["KeyFile"]
        self.assertTrue(keyfile in connectcmd or os.path.expanduser(keyfile) in connectcmd,
                        "wrong keyfile seen in (" + connectcmd + ")")
        # add 10GB as /opt by default!
        import kaveaws as lA

        region = lA.detectRegion()
        ambari = lD.remoteHost("root", ip, keyfile)
        ambari.register()
        #
        # configure keyless access to itself! Needed for blueprints, but already done now by the new_dev_image script,
        #  but the internal ip will be different here!
        # lD.addAsHost(edit_remote=ambari,add_remote=ambari,dest_internal_ip=lA.privIP(iid)) #done in the deploy
        # script...
        #
        lD.configureKeyless(ambari, ambari, dest_internal_ip=lA.privIP(iid), preservehostname=True)
        abranch = ""
        if self.branch:
            abranch = self.branch
        stdout = ambari.run("./[a,A]mbari[k,K]ave/dev/pull-update.sh " + abranch)
        import time

        time.sleep(5)
        return ambari, iid

    def deployOS(self, osval, itype=None):
        """
        Up one centos machine with the scripts and return an lD.remoteHost to that machine
        itype -> None: c3.large
        """
        import kavedeploy as lD

        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        stdout = ""
        if itype is None:
            stdout = lD.runQuiet(
                deploy_dir + "/aws/deploy_known_instance.py "
                + osval + " Test-" + osval + "-" + self.service + " --not-strict")
        else:
            stdout = lD.runQuiet(
                deploy_dir + "/aws/deploy_known_instance.py " + osval + "Test-" + osval + "-" + self.service + " "
                + itype + " --not-strict")
        self.assertTrue(stdout.split("\n")[-1].startswith("OK, iid "))
        iid = stdout.split("\n")[-1].strip()[len("OK, iid "):].split(" ")[0]
        ip = stdout.split("\n")[-1].strip().split(" ")[-1]
        self.assertTrue(stdout.split("\n")[-3].startswith("connect remotely with:"))
        connectcmd = stdout.split("\n")[-2]
        self.assertTrue(ip in connectcmd, "wrong IP seen in (" + connectcmd + ")")
        jsondat = open(os.path.expanduser(os.environ["AWSSECCONF"]))
        import json

        acconf = json.loads(jsondat.read())
        jsondat.close()
        keyfile = acconf["AccessKeys"]["SSH"]["KeyFile"]
        self.assertTrue(keyfile in connectcmd or os.path.expanduser(keyfile) in connectcmd,
                        "wrong keyfile seen in (" + connectcmd + ")")
        ambari = lD.remoteHost("root", ip, keyfile)
        ambari.register()
        import time
        time.sleep(5)
        if osval.startswith("Centos"):
            # add 10GB to /opt
            stdout = lD.runQuiet(
                deploy_dir + "/aws/add_ebsvol_to_instance.py " + iid + " --not-strict")
        return ambari, iid

    def deploycluster(self, clusterfile, cname=None):
        """
        Wrapper around up_aws_cluster.py
        """
        if cname is None:
            cname = "Test-" + self.service
        import kavedeploy as lD
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        cmd = deploy_dir + "/aws/up_aws_cluster.py " + cname + " " + clusterfile + "  --not-strict"
        if self.branchtype in ["__local__"]:
            cmd = cmd + " --this-branch"
        return lD.runQuiet(cmd)

    def resetambari(self, ambari):
        """
        Clean ambari, ready for a new install
        """
        import kavedeploy as lD
        stdout = ambari.run(
            " bash -c 'yes | ./[a,A]mbari[k,K]ave/dev/clean.sh; ./[a,A]mbari[k,K]ave/dev/install.sh ;"
            " ./[a,A]mbari[k,K]ave/dev/patch.sh; "
            "ambari-server start; '")
        if lD.debug:
            print stdout
            print ambari.run("ambari-server status")
        self.assertTrue(
            "Waiting for server start" in stdout and "Ambari Server 'start' completed successfully." in stdout,
            "Ambari server was not restarted! " + ' '.join(ambari.sshcmd()))
        import time

        time.sleep(5)
        return True

    def monitor_request(self, ambari, clustername, requestid=1, max_rounds=60):
        """
        Watch a request for failure/success
        ambari: the ambari host remote
        clustername the name of the cluster
        requestid: the request id to monitor
        rounds, how many rounds
        """
        import kavedeploy as lD
        import time
        rounds = 1
        state = "UNKNOWN"
        ip = ambari.host
        while rounds <= max_rounds:
            stdout = lD.runQuiet(
                "curl --user admin:admin http://" + ip + ":8080/api/v1/clusters/"
                + clustername + "/requests/" + str(requestid))
            if '"request_status" : "FAILED"' in stdout:
                state = "FAILED"
                break
            if '"request_status" : "ABORTED"' in stdout:
                state = "ABORTED"
                break
            if '"request_status" : "COMPLETED"' in stdout:
                state = "COMPLETED"
                break
            time.sleep(60)
            rounds = rounds + 1
        return state

    def deployBlueprint(self, ambari, blueprint, cluster):
        """
        Deploy a blueprint on this ambari node, and wait for it to be up!
        """
        cname = cluster.split('/')[-1].split('.')[0]
        import kavedeploy as lD
        ip = ambari.host
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        # wait until ambari server is up
        self.waitForAmbari(ambari)
        stdout = lD.runQuiet(
            deploy_dir + "/deploy_from_blueprint.py " + blueprint + " " + cluster + " " + ip + " $AWSSECCONF "
                                                                                               "--not-strict")
        state = self.monitor_request(ambari, cname)
        if state == "ABORTED":
            print "Trying to recover from aborted blueprint with restarts"
            stdout = ambari.run("./[a,A]mbari[k,K]ave/dev/restart_all_services.sh " + cname)
            reqid = stdout.strip().split("\n")[-1]
            state = self.monitor_request(ambari, cname, requestid=reqid)

        self.assertFalse(state == "FAILED",
                         "deploy from blueprint failed (" + ' '.join(ambari.sshcmd()) + ")")
        self.assertFalse(state == "ABORTED",
                         "deploy from blueprint aborted (" + ' '.join(ambari.sshcmd()) + ")")
        self.assertFalse(state == "UNKNOWN", self.service + " did not install from blueprint after 60 minutes ("
                         + ' '.join(ambari.sshcmd()) + ")")
        if state == "COMPLETED":
            # done!
            return True
        else:
            raise ValueError("Unknown state: " + str(state) + " (" + ' '.join(ambari.sshcmd()) + ")")
        return

    def waitForAmbari(self, ambari):
        """
        Wait until ambari server is up and running, error if it doesn't appear!
        """
        import kavedeploy as lD
        import time
        # wait until ambari server is up
        ip = ambari.host
        rounds = 1
        flag = False
        while rounds <= 20:
            try:
                stdout = ambari.run("service iptables stop")
            except RuntimeError:
                pass
            try:
                stdout = lD.runQuiet("curl --user admin:admin http://" + ip + ":8080/api/v1/clusters")
                flag = True
                break
            except RuntimeError:
                pass
            time.sleep(60)
            rounds = rounds + 1
        self.assertTrue(flag, "ambari server not contactable after 20 minutes (" + ' '.join(ambari.sshcmd()) + ")")
        return True

    def servicesh(self, ambari, call, service, host="ambari.kave.io"):
        """
        wrapper around service.sh calls
        e.g.: self.servicesh(ambari,"status",service)
        retries once after 5 seconds in case of being unable to connect
        """
        stdout = ambari.run("./[a,A]mbari[k,K]ave/bin/service.sh " + call + " " + service + " -h " + host, exit=False)
        if "couldn't connect to host" in stdout:
            import time

            time.sleep(5)
            stdout = ambari.run("./[a,A]mbari[k,K]ave/bin/service.sh " + call + " " + service + " -h " + host)
        return stdout

    def waitForService(self, ambari, service=None):
        """
        Wait until service is installed
        """
        if service is None:
            service = self.service
        import time

        rounds = 1
        flag = False
        while rounds <= 20:
            stdout = self.servicesh(ambari, "status", service)
            self.assertFalse('INSTALL_FAILED' in stdout,
                             "Installation of " + service + " failed! (" + ' '.join(ambari.sshcmd()) + ")")
            self.assertFalse('ABORTED' in stdout,
                             "Installation of " + service + " aborted! (" + ' '.join(ambari.sshcmd()) + ")")
            if '"state" : "STARTED"' in stdout or '"state" : "INSTALLED"' in stdout:
                flag = True
                break
            time.sleep(60)
            rounds = rounds + 1
        self.assertTrue(flag, self.service + " did not install after 20 minutes (" + ' '.join(ambari.sshcmd()) + ")")
        if service == "KAVETOOLBOX":
            # KAVETOOLBOX is a client and does not have a status method
            return True
        stdout = self.servicesh(ambari, "status", service)
        if '"state" : "STARTED"' in stdout:
            # all good, no need to explicitly restart the service
            return True
        stdout = self.servicesh(ambari, "stop", service)
        time.sleep(10)
        stdout = self.servicesh(ambari, "start", service)
        time.sleep(10)
        flag = False
        rounds = 1
        while rounds <= 10:
            stdout = self.servicesh(ambari, "status", service)
            self.assertFalse('INSTALL_FAILED' in stdout,
                             "Installation of " + service + " failed! (" + ' '.join(ambari.sshcmd()) + ")")
            self.assertFalse('ABORTED' in stdout,
                             "Installation of " + service + " aborted! (" + ' '.join(ambari.sshcmd()) + ")")
            if '"state" : "STARTED"' in stdout:
                flag = True
                break
            stdout = self.servicesh(ambari, "start", service)
            time.sleep(60)
            rounds = rounds + 1
        self.assertTrue(flag, service + " did not start after 10 minutes (" + ' '.join(ambari.sshcmd()) + ")")

    def check(self, ambari):
        """
         interpret directories or websites to check exist
        """
        for check in self.checklist:
            if check.startswith("/"):
                stdout = ambari.run("if [ -e " + check + " ] ; then echo pass ; else echo fail ; fi;")
                self.assertFalse("fail" in stdout,
                                 "checking existence of " + check + " failed (" + ' '.join(ambari.sshcmd()) + ")")
            elif self.service.startswith("APACHE") and check.startswith("http://"):
                stdout = ambari.run(" curl -i -X GET --keepalive-time 5 " + check, exit=False)
                self.assertTrue(
                    "If you can read this page it means that the Apache HTTP server installed at this site is working "
                    "properly." in stdout,
                    "checking existence of " + check + " failed (" + ' '.join(ambari.sshcmd()) + ") \n" + stdout)
            elif self.service.startswith("JENKINS") and check.startswith("http://"):
                flag = False
                rounds = 1
                import time

                while rounds <= 10:
                    stdout = ambari.run(" curl -i -I --keepalive-time 5 " + check, exit=False)
                    if "200 OK" in stdout:
                        flag = True
                        break
                    time.sleep(5)
                    rounds = rounds + 1
                self.assertTrue(flag, "checking existence of " + check + " failed (" + ' '.join(
                    ambari.sshcmd()) + " 'curl -i -I --keepalive-time 5 " + check + "') \n" + stdout)
            elif check.startswith("http://"):
                stdout = ambari.run(" curl -i -I --keepalive-time 5 " + check, exit=False)
                self.assertTrue("200 OK" in stdout, "checking existence of " + check + " failed (" + ' '.join(
                    ambari.sshcmd()) + " 'curl -i -I --keepalive-time 5 " + check + "') \n" + stdout)
            elif check.startswith("https://"):
                stdout = ambari.run(" curl -k -i -I --keepalive-time 5 " + check, exit=False)
                self.assertTrue("200 OK" in stdout, "checking existence of " + check + " failed (" + ' '.join(
                    ambari.sshcmd()) + " 'curl -k -i -I --keepalive-time 5 " + check + "') \n" + stdout)
            elif len(check):
                self.assertTrue(False, "don't know how to check existence of " + check)
        return

######################
# Any other helper functions?
######################


def d2j(adict):
    """Replacements to take a literal string and return a dictionary, using ajson intermediate
    """
    replaced = adict.strip().replace('{u\'', "{'").replace(' [u\'', "['").replace(
        ' (u\'', "('").replace(' u\'', " '").replace("'", '"').replace('(', "[").replace(")", "]")
    import json
    return json.loads(replaced)
