Tests which create more than one service and check how they work together

clusters.py will create an entire cluster, and install from a blueprint onto that cluster presuming that the blueprints, cluster def and aws def live within the blueprints subdir

i.e. the test ./integration/clusters.py exampledev will read exampledev.aws.json to create a cluster, then deploy the blueprint exampledev.blueprint.json and exampledev.cluster.json to that cluster. It will monitor the progress and attempt to recover from known failures. The all.py suite is pretty simple in this directory, it reads the name of all the blueprints and will run one test for each in parallel.

--verbose is implemented in this test suite
--branch is implemented in this test suite
--this-branch is implemented in this test suite