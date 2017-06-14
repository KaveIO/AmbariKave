How to deploy KAVE automatically on Cloudbreak.

This was tested with the FreeIPA cluster attached, but scripts have been slightly refactored afterwards - please test them singly before starting a new deployment.

Open the Cloudbreak portal at http://40.83.253.211 (admin@example.com/Ka...01); if it is down or non-responsive restart it:
-ssh cloudbreak@40.83.253.211 (cloudbreak/Ka...01)
-cd /var/lib/cloudbreak-deployment/
-sudo cbd restart

The scope of the story is to migrate every blueprint we defined (example, integration tests etc). Porting a single blueprint on Cloudbreak means:
-create a blueprint
-create the associated template - the cluster VMs (optional); you can go with the default minviable Azure size, or create custom ones with the sizes we already use (see the aws.json file)
-create the three recipes (una tantum): these are just shell scripts, there is one for the Ambari node only to install the KAVE and other two to be added for all nodes
-start the deployment
-make sure that the deployment finishes
-make sure that all Ambari services are green, i.e. no errors in the installation tasks

Should there be any issues, they must be fixed and the whole installation needs to be retried; in parallel a branch containing the fixes must be created.

It is important to repeat that a successful porting is an all-green, no installation hiccups deployment.
