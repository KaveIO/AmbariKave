AmbariKave
==========

This repository has three parts:
- Additional services added as patches into the Ambari installer. This is "the payload". The src and bin subdirectories.
- Deployment tools for amazon and generic systems to automate the deployment and speed up testing. The deployment subdirectory.
- Development tools and tests for developers of this project. The dev and tests subdirectories.

We also endeavor to provide an extensive [wiki documentation](https://github.com/KaveIO/AmbariKave/wiki)

Relationship to Ambari
======================

AmbariKave extends Ambari adding some more services. It does this by adding a stack to Ambari. Ambari is nicely extensible and adding a stack does not interfere with older stacks, not can it interfere with already running services.

This means there are two general ways to install these services

* Install ambari however you wish to, and then add our patch for a new stack
* Use our wrapper around the ambari installer to install and also patch

Installation (on the 'ambari node' of your cluster, or one large machine)
=========================================================================

If you are looking for the extensive documentation, including descriptions of disk/cpu/ram requirements, please look at [the installation wiki](https://github.com/KaveIO/AmbariKave/wiki/Detailed-Guides-AmbariKave)

* Ambari is a cluster installation management system for hadoop-based clusters. It installs separate services on different machines across a cluster. AmbariKave is a small extention fo this. If what you're looking for is a common set of data science tools to install on one single machine (without a database or hdfs) consider [KaveToolbox](http://github.com/KaveIO/KaveToolbox)

* To download and install a released version of AmbariKave from the repos server: http://repos.kave.io , e.g. 2.2-Beta, with username repos and password kaverepos, including downloading and installing ambari:
```
yum -y install wget curl tar zip unzip gzip python
wget http://repos:kaverepos@repos.kave.io/noarch/AmbariKave/2.2-Beta/ambarikave-installer-2.2-Beta.sh
sudo bash ambarikave-installer-2.2-Beta.sh
```

( NB: the repository server uses a semi-private password only as a means of avoiding robots and reducing DOS attacks
  this password is intended to be widely known and is used here as an extension of the URL )

* OR to install the HEAD from git: example given with ssh copying from this github repo.
```
# If on Centos6, turn off iptables with:
sudo service iptables stop
sudo chkconfig iptables off
# If on Centos7 use:
systemctl disable firewalld
systemctl stop firewalld
#test ssh keys with
ssh -T git@github.com
#if this works,
git clone git@github.com:KaveIO/AmbariKave.git
# Once you have a local checkout, install it with:
cd AmbariKave
sudo dev/install.sh
sudo dev/patch.sh
sudo ambari-server start
```

Then to provision your cluster go to: http://YOUR_AMBARI_NODE:8080 or deploy using a blueprint, see https://cwiki.apache.org/confluence/display/AMBARI/Blueprints

Installation (patch) over existing Ambari
=========================================

* Released version of AmbariKave from the repos server: http://repos.kave.io , e.g. 2.2-Beta, with username repos and password kaverepos, over existing ambari:
```
yum -y install wget curl tar zip unzip gzip python
wget http://repos:kaverepos@repos.kave.io/noarch/AmbariKave/2.2-Beta/ambarikave-package-2.2-Beta.tar.gz
tar -xzf ambarikave-package-2.2-Beta.tar.gz -C /var/lib/
```

* OR to install the HEAD from git: example given with ssh copying from this github repo.
```
#test ssh keys with
ssh -T git@github.com
#if this works,
git clone git@github.com:KaveIO/AmbariKave.git
# Once you have a local checkout, install it with:
sudo ambari-server stop
cd AmbariKave
sudo dev/patch.sh
sudo ambari-server start
```


Update our patches
====================

If you have the head checked out from git, you can update with:

Connect to your ambari/admin node
```
sudo where/I/checked/out/ambari/dev/pull-update.sh
```
pull-update also respects git branches, as a command-line argument and is linked into the way we do automated deployment and testing

To update between released versions, simply install the new version over the old version after stopping the ambari server. Installing a new version of the stack, will not trigger an update of any running service. You would need to do this manually in the current state.
```
sudo ambari-server stop
wget http://repos:kaverepos@repos.kave.io/noarch/AmbariKave/2.2-Beta/ambarikave-installer-2.2-Beta.sh
sudo bash ambarikave-installer-2.2-Beta.sh
```

( NB: the repository server uses a semi-private password only as a means of avoiding robots and reducing DOS attacks
  this password is intended to be widely known and is used here as an extension of the URL )

Installation of a full cluster
==============================

If you are looking for the extensive documentation, including descriptions of disk/cpu/ram requirements, please look at [the installation wiki](https://github.com/KaveIO/AmbariKave/wiki/Detailed-Guides-AmbariKave)

If you have taken the released version, go to http://YOUR_AMBARI_NODE:8080 or deploy using a blueprint, see https://cwiki.apache.org/confluence/display/AMBARI/Blueprints
If you have git access, and are working from the git version, See the wiki.

We really recommend installation beginning from a blueprint, but first one must carfully design the blueprint and/or test on some other test resource. The web interface is great for single one-time custom installations, a blueprint is good for pre-tested redeployable installations.

Installation Kerberization with FreeIPA
=======================================

FreeIPA can provide all necessary keytabs for your kerberized cluster, using the kerberos.csv given by the Ambari wizard.
Be careful because you need to pause while using the wizard when given the option to download the csv, and do some things on the command line before continuing.

You can follow the tutorial here: https://youtu.be/hL1yiMlgg0E

[![Kerberizing Cluster](http://img.youtube.com/vi/hL1yiMlgg0E/0.jpg)](https://youtu.be/hL1yiMlgg0E "Kerberizing Cluster")

And/or follow these steps:

 * Installed and configure the cluster how you wish, with all services.
 * Start the wizard
 * Select the manual configuration option and say yes that you have installed all requirements.
 * Modify the realm to match your FreeIPA realm
 * Modify advanced settings only if you think it's very necessary or you know what you are doing
 * When given the option, download the csv of all keytabs, then do not continue on the wizard, don't click anything, don't stop or exit the wizard, before you've created the keytabs you need using the instructions below
 * copy this csv to the ambari node, somewhere readable by the root user
 * ssh to your ambari node
 * become the root user (sudo su)
 * kinit as a user with full administration rights (kinit admin)
 * run the /root/createkeytabs.py script over the kerberos.csv file you downloaded/copied (./createkeytabs.py ./kerberos.csv)
 * Once this script is finished, if everything worked, continue with the wizard

The createkeytabs.py script creates all necessary service and user principals, any missing local users or groups, creates temporary keytabs on the ambari node, copies them to the required places on the nodes, removes the local intermediate files, and tests that the new ketyabs work for those services.


Deployment tools
==============================

See the deployment subdirectory, or the deployment tarball kept separately

Downloading deployment tools
----------------------------

```
yum -y install wget curl tar zip unzip gzip python
wget http://repos:kaverepos@repos.kave.io/noarch/AmbariKave/2.2-Beta/ambarikave-deployment-2.2-Beta.tar.gz
tar -xzf ambarikave-deployment-2.2-Beta.tar.gz
```

Or download the head from github. See the github readme on the deployment tools, the help written for each tool, or better yet, contact us if you'd like some advice on how to use anything here. [Deployment readme](https://github.com/KaveIO/AmbariKave/tree/master/deployment)

Internet during installation, firewalls and nearside cache/mirror options
-------------------------------------------------------------------------

Ideally all of your nodes will have access to the internet during installation in order to download software.

If this is not the case, you can, possibly, implement a near-side cache/mirror of all required software. This is not very easy, but once it is done one time, you can keep it for later.
* Centos6: [Howto](https://ostechnix.wordpress.com/2013/01/05/setup-local-yum-server-in-centos-6-x-rhel-6-x-scientific-linux-6-x/)
* EPEL: [Mirror FAQ](http://www.cyberciti.biz/faq/fedora-sl-centos-redhat6-enable-epel-repo/) , [Mirroring](https://fedoraproject.org/wiki/Infrastructure/Mirroring)
* Ambari: [Local Repositories](https://ambari.apache.org/1.2.1/installing-hadoop-using-ambari/content/ambari-chap1-6.html)  [Deploying HDP behind a firewall](http://docs.hortonworks.com/HDPDocuments/HDP1/HDP-1.2.1/bk_reference/content/reference_chap4.html)

To setup a local near-side cache for the KAVE tool stack is quite easy.
First either copy the entire repository website to your own internal apache server, or copy the contents of the directories to your own shared directory visible from every node.

```
mkdir -p /my/shared/dir
cd  /my/shared/dir
wget -R http://repos.kave.io/
```

Then create a /etc/kave/mirror file on each node with the new top-level directory to try first before looking for our website:
```
echo "/my/shared/dir" >> /etc/kave/mirror
echo "http://my/local/apache/mirror" >> /etc/kave/mirror
```

So long as the directory structure of the nearside cache is identical to our website, you can drop, remove or replace, any local packages you will never install from this directory structure, and update it as our repo server updates.


Versioning System
=========================================

Read more here about kave versioning: https://github.com/KaveIO/AmbariKave/wiki/kave-versioning

## Relationship with Ambari Stacks

KAVE extends a HDP stack, adding additional services. See the versioning diagram on our wiki for details.

The HDP stack number looks like X.Y, with a major and minor version. The KAVE also has an W.Z versioning scheme, but this is not 100% coupled to the HDP stack.

## KAVE tags

A KAVE official version tag appears like:

* **Major.minor-qualifier** i.e. **2.2-Beta**

The tag is split into four parts:

* **Major**: Major versions separate backwards incompatible changes or drastic noticable changes to the user experience or interface
* **.minor**: Minor versions represent subsequent releases of bugfixes, small improvements or changes which do not affect the user experience
* **qualifier**: Some logical qualification of the tag making it easier to understand. It is our convention to always use the -Beta tag at the moment. Example qualifies may include -Test (a release for developer testing only), -Pre (prerelease of a release candidate for beta-testing).

## What consititues a major version change?

A new major version is started whenever changes of the following type are made:

* **Backwards incompatible change:** a change which completely prevents working with previous systems or installations.
* **Major version increase of Ambari:** AmbariKave relies on Ambari, and if they increase major version, then so will we
* **Serious security-related bugfix:** in the unlikely event that a major fault is discovered we will always increase the major version and inform the mailing list as to the reason for this
* **Drastic change in user experience or interface:**  in order that users are aware that their experience will drastically change we increase the major version number whenever something drastically different in the experience is changed

## KAVE stack in Ambari

We currently name our stack within ambari to reflect both the version of the HDP stack we depend on, and the installed version of the KAVE.

* X.Y.W.Z.KAVE implies HDP stack X.Y with KAVE stack W.Z . In this way we are explicit about our dependencies. E.g.: 2.4.2.2.KAVE is KAVE release 2.2 running on top of Ambari HDP stack 2.4

This is the stack name you will see in blueprints and in the ambari web interface. In older KAVE versions we used a different approach, not including the KAVE stack tag.
