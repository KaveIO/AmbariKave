Tests which are specific to one service only. There are several ways we can test a service, but each of them is pretty complex. Testing a service entails having a machine where we can install the service and check it is running by checking some website or directory or logfile. So, each of these service tests has the following basic form:

a) Do some sanity checks
b) Create new machine on aws, following the user's dev image, meaning ambari is pre-installed and running
c) Install something on it with Ambari
d) Monitor the progress of that installation in some way
e) verify afterwards the content of some directory or webpage

Each service is different and often they have different requirements. Here we try to provide the minimal environment in which to run the fastest most isolated test of the service installation/running. We have created four different scripts for that. If the actual test requires more than one machine, we do not run it here, so that means we cannot test here anything which interferes with an existing abari installation on the same node.

* remote\_service\_with\_servicesh.py: will attempt to create a service with default parameters through the service.sh script. Here I use the pre-created user's dev image to start a machine quickly with a running ambari. Then I use the service.sh script to add just one service with default configuration. If a service can be installed stand-alone with no forced configuration parameters, then remote\_service\_with\_servicesh.py is the best/fastest test.
* remote\_service\_with\_blueprint.py: will attempt to create a service with a blueprint, if the blueprint SERVICE.blueprint.sh lives in the blueprints subdirectory. Here I can set non-default parameters for a service, or install some prerequisite service or service group. If a service needs passwords, or other such forced parameters, or some prerequisite other service, then a blueprint is the  best way to check it works. This test takes around five minutes longer than the service.sh test because it must clean and potentially re-install the entire ambari server in order to deploy a new blueprint. However, it then checks the status of the one service in question through service.sh, monitors only that service and so does not need the entire blueprint or other services to be working before declaring success.
* remote\_blueprint.py: will run a one-machine blueprint, if the blueprint XXXX.blueprint.sh lives in the blueprints subdirectory. This test takes the longest, it means you can monitor more than just the status of one service, but the status of an entire blueprint installation. Here we have the least requirements, so long as the blueprint is complete, this test will run it.
* test\_kavetoolbox\_head.py ups a machine and installs the head/master of KaveToolbox to it. For KaveToolbox the tests take a long time, because installation of around 3GB of software takes a long time. However we don't need to do this through ambari, we can do it with the kavetoolbox installer itself. This is the only set of checks were we run on different OS versions. KaveToolbox should work on Ubuntu, Centos6 and Centos7.

e.g.:

```
bin/test.sh tests/service/remote_service_with_servicesh.py SERVICENAME SomeWebsiteOrFileToCheck --verbose
bin/test.sh tests/service/remote_service_with_blueprint.py SERVICENAME SomeWebsiteOrFileToCheck --verbose
bin/test.sh tests/service/test_kavetoolbox_head.py --verbose
```

--verbose and --branch and --this-branch are implemented in this test suite.

The all.py test suite in this suite knows exactly what combination of services to run with each test, and will run them all in parallel, since  they run on independent aws machines. Running the entire test suite then is as fast as running the single slowest test (test\_kavetoolbox\_head or  remote\_service\_with\_blueprint.py FreeIPA)