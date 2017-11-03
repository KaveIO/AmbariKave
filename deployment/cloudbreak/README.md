# How to deploy KAVE automatically on Azure via Cloudbreak.

## Some notes:

Currently FreeIPA has issues installing on Cloudbreak. It has been removed from the cloudbreak blueprints until all issues are resolved.
Cloudbreak requires different blueprints, as some of the KAVE services require different settings.

## Accessing cloudbreak UI
Cloudbreak portal can be opened at ```http://<cloudbreak machine public IP>``` and use the credentials specified when deploying the machine.
If it is down or non-responsive restart it:
```bash
ssh cloudbreak@<cloudbreak machine public IP> 
cd /var/lib/cloudbreak-deployment/  # All cbd commands must be issued from this location!
sudo cbd restart
```

## Configuring Cloudbreak related settings

The file \deployment\cloudbreak\params.py holds the necessary configuration related to the cloud break deployment:

Parameter Name - Example Value - Description

+--------+--------+--------+
| asdsdf | asdsdf | asdasf |
+--------+--------+--------+
| 1      | 2      | 3      |
+--------+--------+--------+
| 432    | 5c     | dfv    |
+--------+--------+--------+
| v      | bgbf   | dfgd   |
+--------+--------+--------+


kave_version* = "33-beta"\
cb_http_url = "http://<cloudbreak public IP>"\
cb_https_url = "https://13.64.195.21"\
uaa_port = 8089\
cb_username = "admin@example.com"\
cb_password = "KavePassword01"\
ssl_verify = False




The scope of the story is to migrate every blueprint we defined (example, integration tests etc). Porting a single blueprint on Cloudbreak means:
-create a blueprint
-create the associated template - the cluster VMs (optional); you can go with the default minviable Azure size, or create custom ones with the sizes we already use (see the aws.json file)
-create the three recipes (una tantum): these are just shell scripts, there is one for the Ambari node only to install the KAVE and other two to be added for all nodes
-start the deployment
-make sure that the deployment finishes
-make sure that all Ambari services are green, i.e. no errors in the installation tasks

Should there be any issues, they must be fixed and the whole installation needs to be retried; in parallel a branch containing the fixes must be created.

It is important to repeat that a successful porting is an all-green, no installation hiccups deployment.
