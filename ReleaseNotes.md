# The ReleaseNotes file

Contains a list of the released versions with a summary of the main changes in each version.


# Beta Releases

## v1.2-Beta

* Bugfix release of AmbariKave with over 40 independent fixes
* Thanks to the beta testing program for providing so much feedback

New features in services:

* storm added to the path for all users when storm is installed
* StormSD various parameters such as ports, zookeeper-servers, drpc servers, now allow for comma-separated-lists
* FreeIPA service now has a parameter to set groups, users, and initial user passwords
* FreeIPA now sets default user shell (bash as default, but it is configurable)
* new MONGODB_CLIENT adds mongo libraries for gateway machines
* MONGODB_CLIENT implements mongok script for simpler connectivity (mongok --help)
* KaveLanding, small changes in website layout and better parsing of list of services

New features in test and deployment framework:

* current branch is now the default in tests
* deploy\_from\_blueprint.py now also creates pdsh groups for simpler local cluster management
* new restart\_all\_services.sh script to recover from aborted blueprint deploys
* New more fully tested blueprints which match better the examples on the twiki
* Cleaning script now also cleans content of the ambari-agent directory

Bugfixes:

* HUE integration with beeswax/hive minor fix in port number resolution
* add\_ebs\_volume script major fixes
* FreeIPA previously made a bind user with no password
* FreeIPA and SonarQube both had missing defaults in their configuration xml
* FreeIPA throwing a certain exception caused a different exception to be raised, confusingly
* FreeIPA now can be recovered from partial failures with a re-install
* tWiki installation was failing on jinja template resolution


## v1.1-Beta

* First version of the AmbariKave installer for public beta release (open source release)
* Stack 2.2.KAVE derived from HDP 2.2

Implemented 14 new services:

* FreeIPA as user-management component
* MongoDB and StormSD as key components in the complete lambda architecture
* Gitlabs, Jenkins, Twiki, SonarQube, Archiva, for the development line
* KaveToolbox installation in one of two modes for the analytical tools
* HUE on top of HDP for simplified hive access
* Apache and JBOSS webservers
* KaveLanding, a simple website of internal links within a KAVE
* Mail, postfix and dovecot for mail servers

Integrated services together:

* Integration of HUE into HDP
* Integration of FreeIPA with Twiki, Jenkins, Gitlabs, HDP (Kerberos, LDAP, DNS and unix users)

Implemented common libraries:

* src/shared/kavecommon is automatically distributed during patching

Automated deployment and testing:

* As part of our development cycle automated deployment and testing of deployed instances is done through aws or vagrant
* We extended the python unittests package for our testing purposes
* Implemented several developer scripts to speed up the development process
* We wrapped aws cli in a python suite to simplify these tests, but that's not really needed for most purposes
* We wrapped blueprint deployment into a simple script which is quite useful for easily deploying/redeploying clusters

