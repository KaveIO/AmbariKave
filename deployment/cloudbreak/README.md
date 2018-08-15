# How to deploy KAVE automatically on Azure via Cloudbreak.

## Accessing cloudbreak UI
Cloudbreak portal can be opened at ```http://<cloudbreak machine public IP>``` and use the credentials specified when deploying the machine.
If it is down or non-responsive restart it:
```bash
ssh cloudbreak@<cloudbreak machine public IP> 
cd /var/lib/cloudbreak-deployment/  # All cbd commands must be issued from this location!
sudo cbd restart
```
## Authentication
The first time you try to deploy a cluster, using the script, you will be prompted to enter your Cloudbreak login credentials (Cloudbreak username and password).
After successfully obtaining Cloudbreak access token, login credentials will be stored in the hidden file .cbcredstore, located in the user's home directory.
Note: In case of storing incorrect credentials, delete ~/.cbcredstore file.

## Configuring target cloudbreak instance details

The file __```/deployment/cloudbreak/config/cbparams.py```__ holds the necessary configuration, related to the Cloudbreak deployment:

#### Cloudbreak details
* cb_url = "https://<cloudbreak dns name>" - URL for access to Cloudbreak

#### Deployment specific configurations
* credential_name = "<cloudbreak credential name>" - Name of Cloudbreak credential which will be used for cluster deployment
* ssh_private_key = "" - Absolute path to the private SSH key that corresponds to the public key below. This parameter is necessary for clusters with FreeIPA. If no path is specified, ```~/.ssh/id_rsa``` will be used by default.
* ssh_public_key = "" - Absolute path to a public SSH key that will be distributed to the cluster nodes during cluster deployment. The matching private key will be used to access cluster nodes via SSH. If no path is specified, ```~/.ssh/id_rsa.pub``` will be used by default.
* ssl_verify = False - Parameter which control SSL certificate verification behavior. Possible values are:
  * False (Default) - no certificate verification performed. We will just trust whatever is presented by Cloudbreak. This was made the default option as by default Cloudbreak uses very primitive ssl self signed cert.
  * True - should be set when real certificate is used, or one which trust is established by other means (OS level, corp CA etc.)
  * /\<path\>/\<to\>/\<trusted public key\> - A path containing trusted certs or CA bundles can be set. In this case only the certs in this path will be trusted and no others - even if they are real ones.

* image_catalog = "<cloudbreak image catalog name>" - regostered Cloudbreak image catalog name
* image_id = "<cloudbreak image uuid>" - virtual machine image id from image catalog; machines of the cluster will be started from this image

#### Cloud provider specific cofigurations
* cloud_platform - indicates which cloud provider will be used for cluster deployment. Currently, only "AZURE" is supported.

##### Azure
* region - name of the cloud provider region in which the infrastructure will be created.
* adls_enabled = False - Parameter which indicates whether Azure Data Lake Store should be used for file system. Default is False. If set to True, a valid value for adls_name should be set as well
* adls_name = "<Azure Data Lake Store name>" - Name of existing preconfigured Azure Data Lake Store.


## What is needed to deploy a cluster:
### Blueprint(s)
Out of the box KAVE comes with a set of blueprints used for executing the integration tests and some example scenarios. They can be found in the __```/deployment/cloudbreak/blueprints/```__ folder. These are standard [ambari blueprints.](https://cwiki.apache.org/confluence/display/AMBARI/Blueprints) so new ones can be created accordingly.

### Hostgourps and machine template mapping.
Cloudbreak requires a machine template to be created and selected for each hostgroup in the selected blueprint. It uses this information to bring up the infrastructure (actual VMs) in the selected cloud provider (Azure). The file __```/deployment/cloudbreak/config/hostgroups.azure.json```__ stores this information for each and every different hostgroup in all the blueprints. If a new blueprint is being created then all new/different hostgroups must be described in this file as well. Example:
```json
{
    "admin": {
        "instance-type": "Standard_D2_v2",
        "volume-size": 30,
        "volume-count": 1,
        "type" : "GATEWAY",
        "volume-type": "Standard_LRS",
        "security-group" : "default_security_group",
        "node-count" : 1,
        "recipes": [
                    "patchambari",
                    "fix-hosts-file",
                    "limit-ssh-attempts",
                    "ipv6-lo-enable"
                    ]
    },
    "admin-freeipa": {
        "instance-type": "Standard_D2_v2",
        "volume-size": 30,
        "volume-count": 1,
        "type" : "GATEWAY",
        "volume-type": "Standard_LRS",
        "security-group" : "default_security_group",
        "node-count" : 1,
        "recipes": [
                    "patchambari",
                    "fix-hosts-file",
                    "limit-ssh-attempts",
                    "ipv6-lo-enable",
                    "ipa-security-settings"
                    ]
    },
    "gateway": {
        "instance-type": "Standard_D2_v2",
        "volume-size": 150,
        "volume-count": 1,
        "type" : "CORE",
        "volume-type": "Standard_LRS",
        "security-group" : "default_security_group",
        "node-count" : 1,
        "recipes": [
                    "fix-hosts-file",
                    "limit-ssh-attempts"
                    ]
    },
    "namenode-1": {
        "instance-type": "Standard_F4",
        "volume-size": 50,
        "volume-count": 1,
        "type" : "CORE",
        "volume-type": "Standard_LRS",
        "security-group" : "default\_security\_group",
        "node-count" : 1,
        "recipes": [
                    "fix-hosts-file",
                    "limit-ssh-attempts"
                    ]
    }

}
```
Looking at the last json object:
*  _namenode-1_ is the hostgroup name
*  _instance-type_ is the Azure machine template to be used
*  _volume-size_ - The amount of storage (in GB), provisioned to the node
*  _volume-count_ - Attached volumes per instance. Number between 1 and 24
*  _type_ - "GATEWAY" for the Ambari node, "CORE" for all the rest
*  _security-group_ - Name of the security group in which nodes from the hostgroup will be created
*  _node-count_ - Number of nodes to be deployed
*  _recipes_ - List of recipe names (as described in recipe_details.py) to be applied to this hostgoup

Note: "admin-freeipa" hostgroup is used for Ambari node template in clusters with FreeIPA included. Otherwise "admin" hostgroup is used.

### Manage recipes

Cloudbreak recipe is a script extension to a cluster that runs on all nodes before or after the Ambari cluster installation.
Recipes related information is kept in __```/deployment/cloudbreak/recipes/```__ folder. The subfolders __```mandatory```__  and __```custom```__ contain the recipes definitions. __```mandatory```__  folder contains KAVE related recipes, which should not be changed or deleted and all custom recipes should be placed in __```custom```__ folder.
Each recipe should be described in  __```recipe_details.json```__ file in the following format:

```json
{ "recipe-name-to-be-used":
    {
        "recipeType": "PRE",
        "description": "This description with show up in CLoudbreak UI",
        "templatePath": "recipes/custom/script-to-be-executed-by-recipe.sh"
    }
}
```
### Manage security groups

Security groups are part of each hostgroup definition. Either existing security groups that is already available in the selected provider region or predefined set of rules can be used.
Security groups referenced in hostgroups definitions need a matching JOSN file, located in __```/deployment/cloudbreak/securitygroups/```__ folder. The content of the file depends on the type of the security group. If you prefer using an existing security group, you need to specify the corresponding security group id. Check __```existing_security_group.json```__ for reference. Otherwise, a list of security rules that relates to the security group should be defined. By default __```default_security_group```__ is used in the predefined blueprints:

```json
{
    "securityRules": [
        {
            "subnet": "0.0.0.0/0",
            "ports": "9443",
            "protocol": "tcp"
        },
        {
            "subnet": "0.0.0.0/0",
            "ports": "22",
            "protocol": "tcp"
        },
        {
            "subnet": "0.0.0.0/0",
            "protocol": "tcp",
            "ports": "443"
        }
    ]
}
```

You can create your own security group with adding or removing security rules, following the format above, where:
*  _subnet_ - definition of allowed subnet in CIDR format
*  _ports_ - comma separated list of accessible ports
*  _protocol_ - protocol of the rule


## Running the deployment script

Presuming all is set correctly a cluster may be deployed by running the ```deployment/cloudbreak/cbdeploy.py```
It takes a blueprint/cluster name as argument. For example running:
```bash
./cbdeploy.py AIRFLOW
```
will look for the ```AIRFLOW.blueprint.json``` file inside the deployment/cloudbreak/blueprints folder. Then it would read out the host_groups defined and check their description in the ```hostgroups.azure.json``` Based on that it would create the necessary blueprint (only if it is not already present). Then create the recipes (again only if not already present) and then will create a stack and a cluster on that stack. Process can be monitored in the console or in CloudbreakUI (UI requires a refresh sometimes to acknowledge the changes).

Blueprints and recipes are resources which are stored in Cloubreak and reused for subsequent deployments. When deploying a cluster the script will first check if the resource is created in Cloudbreak. If missing, it will be created using the local definition of the blueprint/recipe. If such resource is already created in Cloudbreak, it will be compared with the local version, stored on the machine and in case there are no differences, the deployment will proceed using the resource present in Cloudbreak. If any differences in the local and version from Cloudbreak are detected, then the script will try to delete the resource from Cloudbreak and recreate it. However, if any clusters are using this blueprint/recipe at this moment, deletion will not be possible. In this case a new resource will be created (with the same name and random string appended) and it will be used for the current deployment.

The script can also take a list of blueprint/cluster names as parameter to deploy clusters simultaneously, or an ```"--all"``` parameter, which would deploy all clusters described in the blueprints folder at once.

Additionally, the script accepts parameters ```"--kill-passed"``` , ```"--kill-failed"``` ,and  ```"--kill-all"``` which indicate if and which clusters should be automatically terminated after the deployment is ready:
* --kill-passed - if present, all successfully deployed clusters will be deleted
* --kill-failed - if present, all clusters which reported failure will be deleted
* --kill-all - if present, all clusters will be deleted after deployment is complete

Use ```"--verbose"``` parameter, if you want to see more information about stack and cluster status during deployment.

```"--this-branch"``` parameter is used to deploy AmbariKave cluster from the current branch of the local Git repo.

## Deleting clusters

Cloudbreak clusters can be deleted using the ```deployment/cloudbreak/kill_clusters.py``` script.
Running the script with given cluster name, the cluster and its infrastructure get deleted. For example:
```bash
./kill_clusters.py --name examplelambda1512132645
```

## Using custom images
As Cloudbreak uses its own images with which include default configuration and default tooling for provisioning you 
need to build your own image using this [tool](https://github.com/hortonworks/cloudbreak-images) provided by Hortonworks. 
 
Basically you should follow these steps when creating custom image.
1. Find and clone the correct branch. The repository contains different branches for different Cloudbreak versions. If you are using 1.16.3 or 1.16.4-rc.7 version of Cloudbreak then the related branch is rc-1.16). 
If you are using 2.0.1 version of Cloudbreak then the related image branch is rc-2.0 and so on.

2. Set environment variables. 
Example for environment variables:
    ```
    export ARM_CLIENT_ID=3234bb21-e6d0-*****-****-**********
    export ARM_CLIENT_SECRET=2c8bzH******************************
    export ARM_SUBSCRIPTION_ID=a9d4456e-349f-*****-****-**********
    export ARM_TENANT_ID=b60c9401-2154-*****-****-**********
    export ARM_GROUP_NAME=resourcegroupname
    export ARM_STORAGE_ACCOUNT=storageaccountname
    ```
3. Images for Cloudbreak are created by [Packer](https://www.packer.io/docs/). The main entry point for creating an image is the `Makefile` which provides wrapper functionality around Packer scripts. 
You can find more details about how it works in the [Packer documentation](https://www.packer.io/docs/).

    Main configuration of Packer for building the Cloudbreak images is located in the `packer.json` file. 
    
    Execute the following command: 
    
    CentOS 7: ```make build-azure-centos7``` 
    
    RHEL 6: ```make build-azure-rhel6```  
4. Prepare the custom image catalog JSON file and save it in a location accessible to the Cloudbreak VM. Example JSON [file](https://docs.hortonworks.com/HDPDocuments/Cloudbreak/Cb-doc-resources/custom-image-catalog.json).
5. Register the image in Cloudbreak using ``cb imagecatalog create`` ([documentation](https://hortonworks.github.io/cloudbreak-documentation/latest/cli-reference/index.html#imagecatalog-create))
or manually [register image in the profile](https://hortonworks.github.io/cloudbreak-documentation/latest/images/index.html#register-image-catalog-in-the-profile). 

If you want to start from your own base image, follow the instructions in [Advanced topics](https://github.com/hortonworks/cloudbreak-images/blob/master/README.dev.md) 
to modify the package.json to start from your own base image. Then use the commands above to build that image.

## Known issues and notes:

* Currently, when deploying clusters that contain FreeIPA, sometimes FreeIPA Client fails to install on some of the nodes. This can be resolved by choosing to manually re-install clients from Ambari UI.
* Clusters containing FreeIPA server may fail to deploy due to a certificates generation issue. No stable workaround found yet.
* Scripts support both Python 2 and 3 environments.
