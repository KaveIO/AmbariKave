#!/bin/sh

#This is a Cloudbreak pre-recipe for the Ambari node.
#Log at /var/log/recipes/pre-kaveprepatch.log

#At every release, please update these variables.
KAVE_VERSION=3.3
HDP_STACK=2.6
KAVE_STACK=$HDP_STACK.$KAVE_VERSION.KAVE
DEFAULT_STACK_ADVISOR=HDP26StackAdvisor
PARENT_STACK_ADVISOR=HDP25StackAdvisor
KAVE_STACK_ADVISOR=HDP2633KAVEStackAdvisor

yum -y install wget curl tar zip unzip gzip python
wget http://repos:kaverepos@repos.kave.io/noarch/AmbariKave/$KAVE_VERSION-Beta/ambarikave-package-$KAVE_VERSION-Beta.tar.gz
tar -xzf ambarikave-package-$KAVE_VERSION-Beta.tar.gz -C /var/lib \
--transform "s/$KAVE_STACK/$HDP_STACK/" \
--exclude ambari-server/resources/stacks/HDP/$KAVE_STACK/metainfo.xml \
--exclude ambari-server/resources/stacks/HDP/$KAVE_STACK/services/stack_advisor.py
--exclude repoinfo.xml
systemctl stop ambari-server
systemctl start ambari-server