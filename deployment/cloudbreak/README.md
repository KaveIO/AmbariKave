# How to deploy KAVE automatically on Azure via Cloudbreak.

### Some notes:

Currently FreeIPA has issues installing on Cloudbreak. It has been removed from the cloudbreak blueprints until all issues are resolved.
Cloudbreak requires different blueprints, as some of the KAVE services require different settings.

### Accessing cloudbreak UI
Cloudbreak portal can be opened at ```http://<cloudbreak machine public IP>``` and use the credentials specified when deploying the machine.
If it is down or non-responsive restart it:
```bash
ssh cloudbreak@<cloudbreak machine public IP> 
cd /var/lib/cloudbreak-deployment/  # All cbd commands must be issued from this location!
sudo cbd restart
```
### Configuring target cloudbreak instance details

The file __```/deployment/cloudbreak/params.py```__ holds the necessary configuration, related to the cloud break deployment:

* kave_version = "33-beta" - This string is appended on recipe and template names so they can be differentiated. Will be generated automatically in the future.
* cb_http_url = "http://<cloudbreak public IP>"	- Cloudbreak Url for http requests
* cb_https_url = "https://<cloudbreak public IP>" - Cloudbreak Url for http**s** requests
* uaa_port = 8089  - Port on which tha UAA server is listening to on the cloudbreak instance. Default is 8089									
* cb_username = "admin@example.com"  - Username defined when cloudbreak instance was created				
* cb_password = "<password>"	- Cloudbreak user password
* ssl_verify = False - Parameter which control SSL certificate verification behavior. Possible values are:
  * False (Default) - no certificate verification performed. We will just trust whatever is presented by cloudbreak. This was made the default option as by default cloudbreak uses very primitive ssl self signed cert.
  * True - should be set when real certificate is used, or one which trust is established by other means (OS level, corp CA etc.)
  * /<path>/<to>/<trusted public key> - A path containing trusted certs or CA bundles can be set. In this case only the certs in this path will be trusted and no others - even if they are real ones.
* recipes - A json description of all the recipes which need to be available. Example value:

```json
{ "recipe-name-to-be-used":   
    {
        "recipeType": "PRE", 
        "description": "This description with show up in CLoudbreak UI",
        "templatePath": "recipes/script-to-be-executed-by-recipe.sh"
    }}
```


## What is needed to deploy a cluster:
### Blueprint(s)
Out of the box KAVE comes with a set of blueprints used for executing the integration tests and some example scenarios. They can be found in the __```/deployment/cloudbreak/blueprints/```__ folder. These are standard [ambari blueprints.](https://cwiki.apache.org/confluence/display/AMBARI/Blueprints) so new ones can be created accordingly.

### Hostgourps and machine template mapping.
Cloudbreak requires a machine template to be created and selected for each hostgoup in the selected blueprint. It uses this information to bring up the infrastructure (actual VMs) in the selected cloud provider (Azure). The file __```/deployment/cloudbreak/blueprints/hostgroups.azure.json```__ stores this information for each and every different hostgoup in all the blueprints. If a new blueprint is being created then all new/different hostgoups must be described in this file as well. Example:
```json
{
	"admin": {
		"machine-type": "Standard_D2_v2",
		"volume-size": 30,
		"instance-type": "GATEWAY",
		"securityGroup": 5,
		"recipes": [
			"patchambari",
			"fix-hosts-file",
			"distibute-private-key",
			"limit-ssh-attempts"
		]
	},
	"gateway": {
		"machine-type": "Standard_D2_v2",
		"volume-size": 150,
		"instance-type": "CORE",
		"securityGroup": 5,
		"recipes": [
			"fix-hosts-file",
			"distibute-private-key",
			"limit-ssh-attempts"
		]
	},
	"namenode-1": {
		"machine-type": "Standard_F4",
		"volume-size": 50,
		"instance-type": "CORE",
		"securityGroup": 5,
		"recipes": [
			"fix-hosts-file",
			"distibute-private-key",
			"limit-ssh-attempts"
		]
	}
}
```
Looking at the last json object:
* _namenode-1_ is the template name
*  _machine-type_ is the Azure machine template to be used
*  _volume-size_ - the amount of stogare provisioned to the node
*  _instance-type_ - "GATEWAY" for the Ambari node, "CORE" for all the rest.
*  _securityGroup_ - The ID of the security group in which nodes from the hostgroup will be created. 
   *  NOTE: To get a list of all current scurity groups, while logged in Cloudbreak UI, navigate to: ```https://<CloudbreakIP>/securitygroups/account``` Specifying security groups by name is in the roadmap.
*  _recipes_ - list of recipe names (as desctribed in params.py) to be applied to this hostgoup

### Stack
Prior to insatlling the actual HDP components and cluster a stack needs to be created. "Stack" means the **running cloud infrastructure** that is created based on the hostgroups groups and cluster details (machine templates, credential, instance-types, network, securitygroup etc.). The new cluster will use your templates and by using Azure ARM will launch the cloud stack. To configure the stack details edit the following file:
```deployment/cloudbreak/stack_template.json```  Example content:
```json
{
  "name": "",
  "credentialId": 6,
  "region": "North Europe",
  "failurePolicy": {
    "adjustmentType": "BEST_EFFORT",
    "threshold": null
  },
  "onFailureAction": "DO_NOTHING",
  "instanceGroups": [],
  "parameters": {
    "persistentStorage": "cbstore",
    "attachedStorageOption": "SINGLE"
  },
  "networkId": 4,
  "relocateDocker": true,
  "availabilityZone": null,
  "orchestrator": {
    "type": "SALT"
  },
  "tags": {
    "userDefined": {}
  },
  "platformVariant": "AZURE",
  "customImage": null,
  "flexId": null
}
```
The relevant fields are:
* **credentialId** - ID of the cloudbreak credential to be used when deploying the infrastructure.
  * NOTE: To get a list of all credentials configured in Cloudbreak, log into the UI and navigate to: ```https://<CloudbreakIP>/credentials/account``` This will return a json list of all credentials configured. A more sphisticated method on setting the credentials is planned for future releases

* **region** Name of the cloudprovider region in which the infrastructure will be created.
* **networkId** ID of the network in which the cluster will be created. 
  * NOTE: To get a list of all the networks configured in Cloudbreak, log into the UI and navigate to: ```https://<CloudbreakIP>/networks/account``` This will return a json list of all networks. A more sphisticated method on selecting the network is planned for future releases

## Running the deployment script

Presuming all is set correctly a cluster may be deployed by running the ```deployment/cloudbreak/cbdeploy.py```
It takes a blueprint/cluster name as argument. For example running:
```bash
./cbdeploy.py AIRFLOW
```
will look for the ```AIRFLOW.blueprint.json``` file inside the deployment/cloudbreak/blueprints folder. Then it would read out the host_groups defined and check their description in the ```hostgroups.azure.json``` Based on that it would create the necessary machine templates (only if they are not already present) Then create the recipes (again only if not already present) and then will create a stack and a cluster on that stack. Process can be monitored in the console or in CloudbreakUI (UI requires a refresh sometimes to acknowledge the changes).

The script can also take a list of blueprint/cluster names as parameter to deploy clusters simultaneously, or an ```"--all"``` parameter, which would deploy everything present in the blueprints folder at once.



