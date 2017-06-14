#!/bin/sh

#This is a Cloudbreak pre-recipe for the Ambari node.
#Log at /var/log/recipes/pre-kaveprepatch.log

#At every release, please update these variables.
KAVE_VERSION=3.1-Beta
HDP_STACK=2.5
KAVE_STACK=2.5.3.1.KAVE
DEFAULT_STACK_ADVISOR=HDP25StackAdvisor
PARENT_STACK_ADVISOR=HDP24StackAdvisor
KAVE_STACK_ADVISOR=HDP2530KAVEStackAdvisor

yum -y install wget curl tar zip unzip gzip python
wget http://repos:kaverepos@repos.kave.io/noarch/AmbariKave/$KAVE_VERSION/ambarikave-package-$KAVE_VERSION.tar.gz
tar -xzf ambarikave-package-$KAVE_VERSION.tar.gz -C /var/lib --transform "s/$KAVE_STACK/$HDP_STACK/" --exclude ambari-server/resources/stacks/HDP/$KAVE_STACK/metainfo.xml --exclude repoinfo.xml
sed -i -e "s/$DEFAULT_STACK_ADVISOR/$PARENT_STACK_ADVISOR/" -e "s/$KAVE_STACK_ADVISOR/$DEFAULT_STACK_ADVISOR/" /var/lib/ambari-server/resources/stacks/HDP/$HDP_STACK/services/stack_advisor.py
ambari-server stop
ambari-server start
