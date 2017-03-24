# Tools for Amazon EC2 deployment

If you have an Amazon EC2 account, upping a whole new cluster takes only minutes. Scripts for this are put in the aws subdirectory. Configuration files in the clusters subdirectory.

## Pre requisites

1. Linux machine with ssh, awscli, git, bind-utils, and python &gt;= 2.6
2. Git keypair, you must have a key pair for accessing Ambari on git without requiring a password, with a local copy of the private key, you must know where this key is located
3. Amazon key pair, you must have a pre-existing amazon keypair with a copy of the private key locally, you must know where this key is located

## Tools

* aws/deploy\_one\_centos\_instance.py: Adds a Centos 6 instance to a pre-existing security group
* aws/up\_aws\_cluster.py: Creates and configures an entire new cluster of Centos7 machines based upon a json config file
* aws/add\_ebs\_vol\_to\_instance.py: create a new ebs volume and mount it on a pre-existing instance.

Try their own in-built help for more information on how to use these. There are also several other small management scripts in the aws subdirectory, take a look!

## JSON configuration description:

* json file contains a dictionary.
* InstanceGroups is a member of the dictionary
* Domain is an optional member of the dictionary
* InstanceGroups is a list containing simple descriptions of collections of identical machines
* Each instance group is a dictionary, containing must have:<ul>
	<li>"Name" : "the-name-to-give-to-the-instances-no-spaces-are-allowed"</li>
	<li>"Count" : A number of these instances to create, -1 implies one unique instance, 1 or higher will append -### numbers to the end of the names</li>
	<li>"InstanceType" : "amazon.instance.type"</li>
	<li>"AccessType" : "admin/node/gateway"
		<ul> <li>admin = add sshkeys for passwordless access to every other machine</li>
			<li>node = no special access rights</li>
			<li>gateway = open port 443 to ssh</li>
		</ul>
	 </li>
	<li>"ExtraDisks" : dictionary, needs care since the device name of amazon is not the same as the device name in Centos
		<ul> <li>"Mount": "where-to_mount_it"</li>
			<li>"Size" : SizeIngGB</li>
			<li>"Attach" : "aws_expected_device_name"</li>
			<li>"Fdisk" : "device_name_seen_by_fdisk"</li>
		</ul>
	 </li>
</ul>
* The Domain dictionary is simple and gives the domain specifications for the machines, for the moment only one entry is implemented<ul>
     <li>"Name" : "the domain name for these instances, e.g. kave.io"</li>
</ul>

For example see clusters/minimal.aws.json

## JSON security description:

* Json file contains a dictionary.
* json file must at least contain the SecurityGroup and AccessKeys
* AccessKeys contains a list of dictionaries, each of these lists needs:
		<ul> <li>"Name": "what's the name of this keyfile"</li>
		</ul>
* AccessKeys can also contain the KeyFile, location of where to find the private key, and the KeyName which has special meanin
* There are three notable access keys you can register here
		<ul> <li>"Name": "SSH" a key used to ssh into the machines, used by the deploy blueprints step. Can be the same key as in AWS</li>
		    <li>"Name": "AWS" the KeyName is the name of the keypair in aws with which to configure the machines, it must correspond to the private KeyFile also given</li>
		    <li>"Name": "Git" a key used to pull/push from our private git repo, used to deploy the KaveToolbox and up amazon machines. This is optional, you can skip this part and instead you will then be deploying the corresponding released version of Ambari/KaveToolbox</li>
		</ul>
* See example at deployment/clusters/example.security.json

## Using aws tools regularly?

* Once you have written your own security config file, set it as your default AWSSECCONF in your bashrc

```sh
if [ -z "$AWSSECCONF"]; then
    export AWSSECCONF="path/to/my_security_config.json"
fi
```

## Using aws tools as an AmbariKave developer?

* The new_dev_image.py script can be used to generate/save an amazon image of a single machine with the latest AmbariKAVE pre-installed and configured. This saves a lot of time during testing. It finally tells you at the end, the ami-id of the image created. Then register this ami-id in your bashrc as AMIAMBDEV

```sh
if [ -z "$AMIAMBDEV"]; then
    export AMIAMBDEV="ami-#########"
fi
```