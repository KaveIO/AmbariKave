Tests which are specific to one service only

- remote\_service\_with\_servicesh.py will attempt to create a service with default parameters through the service.sh script
- remote\_service\_with\_blueprint.py will attempt to create a service with a blueprint, if the blueprint SERVICE.blueprint.sh lives in the blueprints subdirectory
- test\_kavetoolbox\_head.py ups a machine and installs the head/master of KaveToolbox to it.

e.g.:

```
bin/test.sh tests/service/remote_service_with_servicesh.py SERVICENAME SomeWebsiteOrFileToCheck --verbose
bin/test.sh tests/service/remote_service_with_blueprint.py SERVICENAME SomeWebsiteOrFileToCheck --verbose
bin/test.sh tests/service/test_kavetoolbox_head.py --verbose
```

--verbose and --branch and --this-branch are implemented in this test suite.