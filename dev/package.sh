#!/bin/bash
##############################################################################
#
# Copyright 2016 KPMG Advisory N.V. (unless otherwise stated)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
###############################################################################
# This is the release package builder. It will create things in the build directory for you.
# If you are not a dev, then just don't do this! Once it's done, making a release means
#     1. Test this tarball/installer
#     2. Tag the git repo at the right commit
#     3. Checkout the tag and rebuild within that tag
#     4. Upload the tarball to the correct noarch repos directory
#     5. Upload the install script to the correct centos (architecture specific directory)
#


#abort at first failure
set -e
#set -o pipefail #not a good idea, causes failures even in actual successful situations

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../" && pwd )"
BUILD_DIR=$PROJECT_DIR/build
DEV_DIR=$PROJECT_DIR/dev
TEST_DIR=$PROJECT_DIR/tests
SRC_DIR=$PROJECT_DIR/src
DPM_DIR=$PROJECT_DIR/deployment

cd $PROJECT_DIR
#remove pyc files!
find . -name "*.pyc" -exec rm '{}' ';'
TAG=`git name-rev --tags --name-only $(git rev-parse HEAD)`
TAG=`echo ${TAG} | sed s'/\^0//' | sed s'/\^//'`
echo $TAG

# Make the build directory
mkdir -p $BUILD_DIR
rm -rf $BUILD_DIR/*


################################################################
# Build the package tarball
################################################################
RELEASE_PACKAGE="ambarikave-package-$TAG.tar.gz"
echo "Building $RELEASE_PACKAGE"
mkdir -p $BUILD_DIR/package/ambari-server/resources/stacks/
cp -r $SRC_DIR/HDP $BUILD_DIR/package/ambari-server/resources/stacks/
mkdir -p $BUILD_DIR/package/ambari-server/resources/stacks/HDP
cp -r $SRC_DIR/KAVE $BUILD_DIR/package/ambari-server/resources/stacks/HDP/2.4.KAVE-22
cp -r $SRC_DIR/common-services $BUILD_DIR/package/ambari-server/resources/common-services
cp $PROJECT_DIR/LICENSE $PROJECT_DIR/NOTICE $PROJECT_DIR/README.md $PROJECT_DIR/ReleaseNotes.md $BUILD_DIR/package/ambari-server/

# apply dist_kavecommon.py
python $PROJECT_DIR/dev/dist_kavecommon.py $BUILD_DIR/package/ambari-server/resources/stacks/HDP

# Tar autocollapses. If I'm not in the same path as I'm taring than my tarball
# contains the full path.
cd $BUILD_DIR/package
tar -czf ../$RELEASE_PACKAGE ambari-server
cd $PROJECT_DIR


################################################################
# Build the deployment tarball
################################################################
DEPLOYMENT_TARBALL="ambarikave-deployment-$TAG.tar.gz"
echo "Building $DEPLOYMENT_TARBALL"
cp -r $DPM_DIR $BUILD_DIR/ambarikave-deployment
cp $PROJECT_DIR/LICENSE $PROJECT_DIR/NOTICE $PROJECT_DIR/ReleaseNotes.md $BUILD_DIR/ambarikave-deployment
cp $TEST_DIR/integration/blueprints/example*.json $BUILD_DIR/ambarikave-deployment/blueprints/
cp $TEST_DIR/integration/blueprints/MONGODB*.json $BUILD_DIR/ambarikave-deployment/blueprints/
cp $TEST_DIR/integration/blueprints/STORM*.json $BUILD_DIR/ambarikave-deployment/blueprints/
#remove aws parts
rm -rf $BUILD_DIR/ambarikave-deployment/aws
rm -rf $BUILD_DIR/ambarikave-deployment/lib/kaveaws.py
rm -rf $BUILD_DIR/ambarikave-deployment/clusters
rm -rf $BUILD_DIR/ambarikave-deployment/add_toolbox.py

# Tar autocollapses. If I'm not in the same path as I'm taring than my tarball
# contains the full path.
cd $BUILD_DIR
tar -czf $DEPLOYMENT_TARBALL ambarikave-deployment
cd $PROJECT_DIR


################################################################
# Write the actual installation script to the file
################################################################
RELEASE_INSTALLER="ambarikave-installer-$TAG.sh"
echo "Writing the installer: $RELEASE_INSTALLER"

echo '#!/bin/bash' > $BUILD_DIR/$RELEASE_INSTALLER
cat $PROJECT_DIR/LICENSE >> $BUILD_DIR/$RELEASE_INSTALLER
echo '' >> $BUILD_DIR/$RELEASE_INSTALLER
#echo 'set -o pipefail' >> $BUILD_DIR/$RELEASE_INSTALLER #not a good idea, causes failures even in actual successful situations
echo 'CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"' >> $BUILD_DIR/$RELEASE_INSTALLER

#Jump into cat until eof in order to write arbitrary things into the installer script
#First of all, find the name of the actual KAVE repo and copy method to use
cat << EOF >> $BUILD_DIR/$RELEASE_INSTALLER

#
# NB: the repository server uses a semi-private password only as a means of avoiding robots and reducing DOS attacks
#  this password is intended to be widely known and is used here as an extension of the URL
#
checkout="wget"
repos_server="http://repos:kaverepos@repos.kave.io/"
if [ -f /etc/kave/mirror ]; then
	while read line
	do
		#echo \$line
		if [ -z "\$line" ]; then
			continue
		fi
		#always add a trailing /
		if [ "\${line: -1}" != '/' ]; then
			line=\${line}/
		fi
		if [[ ! "\$line" =~ "http" ]]; then
			if [ -d "\$line" ]; then
				checkout="cp"
				repos_server=\${line}
				break
			fi
			continue
		fi
		res=\`curl --retry 5 -i -X HEAD "\$line" 2>&1\`
		#echo \$res
		if [[ "\$res" =~ "200 OK" ]]; then
			repos_server=\${line}
			break
		elif  [[ "\$res" =~ "302 Found" ]]; then
			repos_server=\${line}
			break
		fi
	done < /etc/kave/mirror
fi

EOF

cat $DEV_DIR/install_snippet.sh >> $BUILD_DIR/$RELEASE_INSTALLER

#Jump into cat until eof in order to write arbitrary things into the installer script
cat << EOF >> $BUILD_DIR/$RELEASE_INSTALLER

if [ ! -f $RELEASE_PACKAGE ]; then
	#echo \${checkout} \${repos_server}
	if [ \${checkout} == "cp" ]; then
		\${checkout} \${repos_server}noarch/AmbariKave/$TAG/$RELEASE_PACKAGE $RELEASE_PACKAGE
	else
		\${checkout} \${repos_server}noarch/AmbariKave/$TAG/$RELEASE_PACKAGE -O $RELEASE_PACKAGE
	fi
fi
tar -xzf $RELEASE_PACKAGE -C /var/lib/

ambari-server restart
EOF
