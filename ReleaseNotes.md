# The ReleaseNotes file

Contains a list of the released versions with a summary of the main changes in each version.


# Beta Releases

# v1.3-Beta

* Bugfix release in preparation for migration to Ambari 2.X
* Over 50 independent fixes

New features in services:

* KaveToolbox:
    move to 1.3 - Beta(lots of minor improvements), e.g. the ProtectNotebooks.sh script
* KaveToolbox:
    Possibility to customize CustomInstall.py added as configuration parameter
* Hue:
    now integrated with HBAC(host - based access control) and thus also with FreeIPA
* Jenkins:
    Migration to latest stable version
* Jenkins:
    Installer and list of default plugins now cached on our repo server
* FreeIPA:
    you can now specify also a list of sudoers in the initial configuration
* FreeIPA:
    Full usernames(first and last) can now be added through the configuration
* KaveLanding:
    Links are now sorted
* KaveLanding:
    Custom links can be provided
* TWiki:
    HBAC and LDAP access supported, thus integrated with FreeIPA
* All services reviewed to ensure they can be restarted effectively without downloads after installation
* Ambari / clusterHostInfo / can be used to determine most server locations in the cluster

New features in test and deployment framework:

* restart\_all\_services.sh script:
    recovers from most aborted blueprints see the in-built help
* Add check for datetime(ntp) in deploy\_from\_blueprint.py to avoid unknown timing issues for ambari agents
* Default blueprints updated, several spurious parameters no longer need to be specified in current ambari versions
* Slight modification to host authentication in the gitwrap script used for testing
* FDisk part of mount command is now guessed per region, simplifying the test scripts
* In tests, threads now unlock if an exception is thrown
* Small bug in packaging script fixed

Bugfixes:

* TWiki:
    LocalSiteCfg was broken through misapplication of a template
* TWiki:
    different default parameters being required through webUI vs blueprints fixed with defaults
* StormSD:
    Parameters renamed so that the install also works through the web interface
* StormSD:
    Partial fix for multiply writing the same configuration files into supervisord.conf, now less common
* StormSD:
    Start / Stop / Restart methods heavily modified to spawn background processes, otherwise they hung forever
* KaveLanding:
    bootstrap / bower not actually needed in most cases
* KaveLanding:
    removal of duplicate code
* KaveLanding:
    False positive status fixed(see status methods below)
* KaveToolbox:
    --ignore - missing - groups accidentally always applied, new logic added
* KaveToolbox:
    missing git install
* FreeIPA:
    did not declare it's forwarders configuration parameter
* Gitlab:
    Unicorn port(8080) was not configurable leading to port conflicts, fixed
* SonarQube:
    Unused parameters removed
* MongoDB:
    in the case a user - specified and IP address for a mongo server, it was not actually being applied
* Start and Install methods need to both call configure in most cases so that web interface reconfiguring is possible
* Status method needs to throw an exception when service not running
* Start / Stop / Restart methods reviewed especially for backgrounded - services

# v1.2-Beta

* Bugfix release of AmbariKave with over 40 independent fixes
* Thanks to the beta testing program for providing so much feedback

New features in services:

* storm added to the path for all users when storm is installed
* StormSD various parameters such as ports, zookeeper - servers, drpc servers, now allow for comma - separated - lists
* FreeIPA service now has a parameter to set groups, users, and initial user passwords
* FreeIPA now sets default user shell(bash as default, but it is configurable)
* new MONGODB_CLIENT adds mongo libraries for gateway machines
* MONGODB_CLIENT implements mongok script for simpler connectivity(mongok - -help)
* KaveLanding, small changes in website layout and better parsing of list of services

New features in test and deployment framework:

* current branch is now the default in tests
* deploy\_from\_blueprint.py now also creates pdsh groups for simpler local cluster management
* new restart\_all\_services.sh script to recover from aborted blueprint deploys
* New more fully tested blueprints which match better the examples on the twiki
* Cleaning script now also cleans content of the ambari - agent directory

Bugfixes:

* HUE integration with beeswax / hive minor fix in port number resolution
* add\_ebs\_volume script major fixes
* FreeIPA previously made a bind user with no password
* FreeIPA and SonarQube both had missing defaults in their configuration xml
* FreeIPA throwing a certain exception caused a different exception to be raised, confusingly
* FreeIPA now can be recovered from partial failures with a re - install
* tWiki installation was failing on jinja template resolution


# v1.1-Beta

* First version of the AmbariKave installer for public beta release(open source release)
* Stack 2.2.KAVE derived from HDP 2.2

Implemented 14 new services:

* FreeIPA as user - management component
* MongoDB and StormSD as key components in the complete lambda architecture
* Gitlabs, Jenkins, Twiki, SonarQube, Archiva, for the development line
* KaveToolbox installation in one of two modes for the analytical tools
* HUE on top of HDP for simplified hive access
* Apache and JBOSS webservers
* KaveLanding, a simple website of internal links within a KAVE
* Mail, postfix and dovecot for mail servers

Integrated services together:

* Integration of HUE into HDP
* Integration of FreeIPA with Twiki, Jenkins, Gitlabs, HDP(Kerberos, LDAP, DNS and unix users)

Implemented common libraries:

* src / shared / kavecommon is automatically distributed during patching

Automated deployment and testing:

* As part of our development cycle automated deployment and testing of deployed instances is done through aws or vagrant
* We extended the python unittests package for our testing purposes
* Implemented several developer scripts to speed up the development process
* We wrapped aws cli in a python suite to simplify these tests, but that's not really needed for most purposes
* We wrapped blueprint deployment into a simple script which is quite useful for easily deploying / redeploying clusters
