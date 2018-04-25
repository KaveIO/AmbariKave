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
Note: In case of storing incorrect credentails, delete ~/.cbcredstore file.

## Configuring target cloudbreak instance details

The file __```/deployment/cloudbreak/config/cbparams.py```__ holds the necessary configuration, related to the Cloudbreak deployment:

#### Cloudbreak details
* cb_http_url = "http://<cloudbreak public IP>"	- Cloudbreak Url for http requests
* cb_https_url = "https://<cloudbreak public IP>" - Cloudbreak Url for http**s** requests
* uaa_port = 8089  - Port on which tha UAA server is listening to on the Cloudbreak instance. Default is 8089

#### Deployment specific configurations
* credential_name = "<cloudbreak credential name>" - Name of Cloudbreak credential which will be used for cluster deployment
* ssh_private_key = "" - Absolute path to the private SSH key that corresponds to the public key, registered in the credential. If no path is specified, ```~/.ssh/id_rsa``` will be used by default.
* network_name = "<network resource name>" - Name of Cloudbreak network in which the cluster will be created.
* ssl_verify = False - Parameter which control SSL certificate verification behavior. Possible values are:
  * False (Default) - no certificate verification performed. We will just trust whatever is presented by Cloudbreak. This was made the default option as by default Cloudbreak uses very primitive ssl self signed cert.
  * True - should be set when real certificate is used, or one which trust is established by other means (OS level, corp CA etc.)
  * /\<path\>/\<to\>/\<trusted public key\> - A path containing trusted certs or CA bundles can be set. In this case only the certs in this path will be trusted and no others - even if they are real ones.

#### Cloud provider specific cofigurations
* cloud_platform - indicates which cloud provider will be used for cluster deployment. Currently, only "AZURE" is supported.

##### Azure
* region - name of the cloud provider region in which the infrastructure will be created.
* adls_enabled = False - Parameter which indicates whether Azure Data Lake Store should be used for file system. Default is False. If set to True, a valid value for adls_name should be set as well
* adls_name = "<Azure Data Lake Store name>" - Azure Data Lake Store name


## What is needed to deploy a cluster:
### Blueprint(s)
Out of the box KAVE comes with a set of blueprints used for executing the integration tests and some example scenarios. They can be found in the __```/deployment/cloudbreak/blueprints/```__ folder. These are standard [ambari blueprints.](https://cwiki.apache.org/confluence/display/AMBARI/Blueprints) so new ones can be created accordingly.

### Hostgourps and machine template mapping.
Cloudbreak requires a machine template to be created and selected for each hostgroup in the selected blueprint. It uses this information to bring up the infrastructure (actual VMs) in the selected cloud provider (Azure). The file __```/deployment/cloudbreak/config/hostgroups.azure.json```__ stores this information for each and every different hostgroup in all the blueprints. If a new blueprint is being created then all new/different hostgoups must be described in this file as well. Example:
```json
{
	"admin": {
		"machine-type": "Standard_D2_v2",
		"volume-size": 30,
		"volume-count": 1,
		"instance-type": "GATEWAY",
		"security-group": "default-azure-only-ssh-and-ssl",
		"node-count" : 1,
		"recipes": [
			"patchambari",
			"fix-hosts-file",
			"limit-ssh-attempts",
			"ipv6-lo-enable"
		]
	},
	"admin-freeipa": {
		"machine-type": "Standard_D2_v2",
		"volume-size": 30,
		"volume-count": 1,
		"instance-type": "GATEWAY",
		"security-group": "default-azure-only-ssh-and-ssl",
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
		"machine-type": "Standard_D2_v2",
		"volume-size": 150,
		"volume-count": 1,
		"instance-type": "CORE",
		"security-group": "default-azure-only-ssh-and-ssl",
		"node-count" : 1,
		"recipes": [
			"fix-hosts-file",
			"limit-ssh-attempts"
		]
	},
	"namenode-1": {
		"machine-type": "Standard_F4",
		"volume-size": 50,
		"volume-count": 1,
		"instance-type": "CORE",
		"security-group": "default-azure-only-ssh-and-ssl",
		"node-count" : 1,
		"recipes": [
			"fix-hosts-file",
			"limit-ssh-attempts"
		]
	}
}
```
Looking at the last json object:
*  _namenode-1_ is the template name
*  _machine-type_ is the Azure machine template to be used
*  _volume-size_ - The amount of storage (in GB), provisioned to the node
*  _volume-count_ - Attached volumes per instance. Number between 1 and 24
*  _instance-type_ - "GATEWAY" for the Ambari node, "CORE" for all the rest
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

Security groups are part of each hostgroup definition. Either existing Cloudbreak security groups or not existing but predefines ones can be used.
The script will first check if the security group exists in Cloudbreak and will use it if present. Otherwise a new one will be automatically created during the deployment process. All that is needed in the second case is a valid security group definition file. This is a JSON file, which name corresponds to the security group name, and is located in __```/deployment/cloudbreak/securitygroups/```__ folder. For reference on how a security group definition looks like, check __```security_group_templte.json```__ file in the same folder.

## Running the deployment script

Presuming all is set correctly a cluster may be deployed by running the ```deployment/cloudbreak/cbdeploy.py```
It takes a blueprint/cluster name as argument. For example running:
```bash
./cbdeploy.py AIRFLOW
```
will look for the ```AIRFLOW.blueprint.json``` file inside the deployment/cloudbreak/blueprints folder. Then it would read out the host_groups defined and check their description in the ```hostgroups.azure.json``` Based on that it would create the necessary machine templates (only if they are not already present) Then create the recipes (again only if not already present) and then will create a stack and a cluster on that stack. Process can be monitored in the console or in CloudbreakUI (UI requires a refresh sometimes to acknowledge the changes).

The script can also take a list of blueprint/cluster names as parameter to deploy clusters simultaneously, or an ```"--all"``` parameter, which would deploy all clusters described in the blueprints folder at once.

Additionally, the script accepts parameters ```"--kill-passed"``` , ```"--kill-failed"``` ,and  ```"--kill-all"``` which indicate if and which clusters should be automatically terminated after the deployment is ready:
* --kill-passed - if present, all successfully deployed clusters will be deleted
* --kill-failed - if present, all clusters which reported failure will be deleted
* --kill-all - if present, all clusters will be deleted after deployment is complete

Use ```"--verbose"``` parameter, if you want to see more information about stack and cluster status during deployment.

```"--this-branch"``` parameter is used to deploy AmbariKave cluster from the current branch of the local Git repo.

## Deleting clusters

Cloudbreak clusters can be deleted using the ```deployment/cloudbreak/kill_clusters.py```
Running the script with given cluster name, the cluster and its infrastructure get deleted. For example:
```bash
./kill_clusters.py --name examplelambda1512132645
```

## Known issues and notes:

* Currently, when deploying clusters that contain FreeIPA, sometimes FreeIPA Client fails to install on some of the nodes. This can be resolved by choosing to manually re-install clients from Ambari UI.
* Scripts have been implemented and tested with Python 2. Some problems may occur, if you try to run the scripts with Python 3.
