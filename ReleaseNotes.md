# The ReleaseNotes file

Contains a list of the released versions with a summary of the main changes in each version.


# Beta Releases

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

