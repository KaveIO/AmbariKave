# Testing Framework:

Four levels of test understood

1. **UnitTests:** tests which are pure functional unit tests of the type that can be run in seconds to test basic library functionality of python methods and classes
2. **Deployment Tests:** tests which need aws connectivity to check that we are able to deploy machines in aws, verify the deployment scripts
3. **ServiceTests:** tests which are specific to one service only, creating machines on amazon
4. **Integration tests:** Tests which create more than one service and check how they work together

Common test code is found in tests/base/base.py

# WARNING: Automatic cleaning!

Given that the deploy tests complete, the test.sh script's next move is to:

1. Stop all machines on aws in this subnet, with this keypair, created more than 20 hours ago
2. Terminate all machines on aws in this subnet, with this keypair, created more than 6 days ago
3. Delete all detached EBS volumnes which used to belong to instances

** Be careful under which security\_config.json file you run the tests! **

I advise:
* Uploading a second test keypair, and using this for tests, or using the same keypair as jenkins itself uses
* renaming any unkillable machines to have the string \_dev\_ in their name-tag on aws

# Common arguements

Common arguements include --verbose, --branch and --this-branch.

* **--verbose**: print commands run by the test. In tests where --verbose is implemented, it should print additional information during the running of the test.
* **--branch**: checkout code from a branch *matching the arguement to the test* on the remote machine. In tests where --branch is implemented it should enable the switching onto a pre-defined git branch on some remote system before the test. The convention is that the tests usually take one arguement, such as "remote_blueprint.py JBOSS" adding --branch would switch this test to checking out the branch with the same name, i.e. JBOSS.
* **--this-branch**: checkout code from the same branch as you are using here on the remote machine. In tests where --this-branch is implemented it should enable the switching onto the same branch remotely as is checked-out locally.

# Prerequisites for running deployment tests

1. A complete security config json file, export

# Running tests:

* Running all the tests:
```
test.sh
```
(with no arguments)

* Running all of the tests in a group:
```
test.sh ./<group>/all.py
```

* Running one of the tests:
```
test.sh ./<group>/<testfile.py> [arguements to test file]
```

* note that the arguements are printed in the output of the tests/<group>/all.py test
* if it is a test which needs aws, you will first need to export AWSSECCONF=/path/to/your/security.config

# Local or remote tests?

* Unit tests run locally. Unit tests assume nothing about prior software installation and can use Mock features if needed.
* All other tests create new machines on aws where the installations are made and tested

# Tests for new services

**By default we test all services, automatically. If the default installation works on the same node as ambari is running, you don't need to change anything.**

We assume that simple installation with service.sh, with no parameters, using all defaults, on the node running ambari will work. These tests are already set up and configured. Adding your new service will run the tests automatically, without you needing to do anything.

If this is not expected to work, because you need to set some parameters for the install (such as passwords), or need more than one service component then:

1. Add that this service should be ignored in service/all.py
2. Add a SERVICE.blueprint.json to service/blueprints in which your new service is configured in the "admin" hostgroup


* If there is a webpage or local file whose presence verifies that your service is up and running, add it as a "check" for this service in service/all.py

* If you want to run your service test yourself try:
```
test.sh ./service/remote_service_with_servicesh.py SERVICENAME SomeWebsiteOrFileToCheck --verbose
```
* or, if you need to run with a blueprint you just added, because the default service.sh installation won't work, try:
```
test.sh ./service/remote_service_with_blueprint.py SERVICENAME SomeWebsiteOrFileToCheck --verbose
```

# Adding a completely new test:

Note that adding a new service will test it automatically, so you only need to add some test when you have some new unit test to try, or some completely different way to test a service, perhaps loading data through some interface, for example.

1. Decide: is it a unit test, service test or integration test?
2. Decide: is it to be run in parallel or sequence after another test?

* **Sequence:** add a new test into the same file as a previous test
* **Parallel: (i)** if this is a very different type of test, add a new file into the directory, and include it in the mods list of the all.py file
* **Parallel: (ii)** if this is a very similar type of test, modify an existing file to accept an argument sys.argv, and add a list of arguements to iterate over into  all.py

Don't forget to:

* use the tests/base/base.py library to store code shared between tests
* try to allow a --verbose flag,
* copy existing tests where possible, with minimal changes to ensure a convention is created/followed
* add your test into all.py for the type of test
* try to fail early if possible

# How can I tell if a test passes or fails?

* A passing test, if written correctly, will print next to no information and finalize by printing "OK" to the command line. A good test which passes will exit with zero status code.
* A failing test test, if written correctly, will print ERROR or FAILURE and print possibly a lot of information about the final steps of the test, such as tracebacks.  A bad test which passes will exit with zero status code.
* In the case that tests are run in sequence, the first failure will stop running further tests.
* In the case that tests are run in parallel within some master test, a failure will not stop other running tests, but any number of failures will provoke a failed status of the master test.

# A test failed, how can I re-run it myself?

The failed test will have some sort of name, which will tell you what file it is from and what arguements were sent to it

* Running one of the tests:
```
test.sh t./<group>/<testfile.py> [arguements to test file]
```
* if it is a test which needs aws, you will first need to export AWSSECCONF=/path/to/your/security.config

In case this is a complicated test, such as one of the integration tests, which creates many many machines on aws and then deploys certain services on those machines, it might not be a good idea to try and re-run the entire test, however, you should also be able to find the ip of the machine in question and see at what stage it failed by checking its ambari server.

You should be intelligent enough and familiar enough with the services to try and repeat the failing step on a single node of your own, or re-deploying a blueprint, or making your own cluster to re-run a similar test, and so avoid needing to wait for the whole test suite itself to re-run.

# A test failed due to some timeout or failed check, but with little other information, how can I debug on the right machine?

If the test was to install a remote machine or cluster, it will have been created with a characteristic name, with a certain security config and at a certain time. So, you should be able to find this machine using deployment/aws/connect_to.py or browsing the ec2 web interface. Either ssh into that machine with the right keys, or more likely, take a look at what failed through ambari on http://someipaddress:8080/
