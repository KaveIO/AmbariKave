Deployment
===========

Description:
------------

Python libraries, scripts, executables and templates for automatic AmbariKave deployment.

Preamble:
---------

Ambari is based upon a service-provision model, that services can be added, started and stopped, on machines within some local cluster.

Automatic deployment has two thrusts:

1. Creating a cluster with the given prerequisites

2. Installing ambari services on a cluster based on a template

It's as easy as A, B, C!

* **A:** aquire. The step in which you gather the computer resources for your cluster and configure any internal/external firewalls. At the end of this step you will have a group of machines within which one node is designated the "admin" node and has passwordless key-based ssh into the other nodes of the cluster. For a setup with aws this is all automated, and uses the up\_aws\_cluster.py script. For aws you will need a security config file, and a cluster definition file, see below.
* **B:** blueprint. Here the list of services you want to run grouped together into host groups running the same services. Ambari manages this via blueprints, where the entire configuration of your cluster can be stored.
* **C:** cluster. Here the nodes in your cluster are assigned to the correct host groups.

## 1. (**A**) Aquire/creating a cluster

A cluster is needed with a given configuration. There are three concepts within AmbariKave:

* The Admin: Ambari is installed here, this node's root user must have key-based ssh access to all other machines in the cluster
* The Workstation: Usually an edge node, requires additional interactive toolset and configuration of access over ssh
* The Node: Runs some specific set of services defined by a configuration and controlled by the admin

In general the following steps are needed:

1. Up virtual machines within a cluster
2. Configure access/firewalls
3. Name the machines within this cluster, or collect their local ips, ensure all machines share a common set of host names
3. Designate one machine as the Admin node and share ssh keys between it and the other machines to enable secure passwordless access from the Admin node to root on the other machines

* <b>aws/up\_aws\_cluster.py:</b>
   * Completes these steps for a cluster on amazon EC2/VPC (see further below)
* <b>clusters/</b>
   * directory with example configurations


## 2. (**B** & **C**) Installing services onto anywhere within the cluster

This can be completed through the ambari web interface, using the command-line-tools/curl API, or through ambari blueprints. The quickest for a cluster of known compatible components is to use blueprints. For blueprints, the following steps are needed:

1. Design your blueprint, taking into account which services will be on which nodes
2. Design your cluster, allocating node to be within host groups
3. Deploy this blueprint to the cluster

* <b>deploy\_from\_blueprint.py:</b>
   * Completely automated blueprint deployment, one-click-installer, see below
* <b>blueprints/</b>
   * directory with example configurations

For more about blueprints see: https://cwiki.apache.org/confluence/display/AMBARI/Blueprints

## **A, B, C** revisited, how simple it is on aws:

The **A, B, C** method on amazon is super simple. You need an aws security config.json file, which points to all the keys you will use later then for each cluster you need

* **A** the something.aws.json file. Tells amazon which machines to create and what to call them. You can also use a cloudformation file here.
* **B** the something.blueprint.json file. Tells ambari what services to create and how to group them together.
* **C** the something.cluster.json file. Tells ambari which hosts go into which group, ambari will install everything on thsoe host that you asked for in the blueprint.

With these three files, and your security config you have everything you need.
* up\_aws\_cluster.py will take your security config and your something.aws.json file to create the machines
* deploy\_from\_blueprint.py will take your something.blueprint.json file and your something.cluster.json file to up all of the required services on those machines.


# Tools for generic deployment

## Pre requisites

1. Linux machine with ssh, git, and python &gt;= 2.6
2. Git keypair, you must have a key pair for accessing Ambari on git without requiring a password, with a local copy of the private key, you must know where this key is located
3. Remote host access by key pair, you must have a pre-existing keypair for accessing all remote hosts you want to configure, with a copy of the private key locally, you must know where this key is located

## Tools

* add\_toolbox.py: add the KaveToolbox to a given remote machine
* resource\_wizard.py: based upon our recent clusters make a guess on the resources required for a given cluster
* deploy\_from\_blueprint.py: deploy service groups across an entire cluster

# More on blueprints

Please see the installation wiki and the ambari blueprints pages

* https://cwiki.apache.org/confluence/display/AMBARI/Blueprints


* _A blueprint:_ Defines the services running on certain host_groups and the common configurations of all those services
* _A cluster configuration:_ allocates hosts to those host groups, and the components will then be installed on them.

Blueprints are quite complex to write yourself, but Ambari can output them from an already running/working cluster. Cluster configurations are easy to write. best to copy the examples provided in the bluprints directory.

1. Obtain /write blueprint
2. Obtain/write cluster template, make sure you overwrite any default passwords
3. Ensure ambari is installed on one cluster node, and that this cluster node has access to all other nodes without password, using sshkeys
4. You can then install the blueprints very simply, either if you're remote or on the ambari node itself.

Submitting blueprints correctly and consistently is a bit tricky, so we have the following command-line tool for that which can run remotely or on the ambari node itself.

```sh
deploy_from_blueprint.py blueprint.json cluster.json [hostname=localhost] [access_key_if_remote]
```
