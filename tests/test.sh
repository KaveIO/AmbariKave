#! /bin/bash
##############################################################################
#
# Copyright 2015 KPMG N.V. (unless otherwise stated)
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
# Test runner script, unit tests are runnable without specific local installation
# further tests require aws availability, aws configuration, and AWSSECCONF variable defined
#

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH=$CURRENT_DIR/../deployment/lib:$CURRENT_DIR/../tests/base:$CURRENT_DIR/../src/shared:$PYTHONPATH
export BAHDIR=$CURRENT_DIR

if [ ! -z "$1" ]; then
	python $@
	exit $?
fi


########## TDD stats
echo "============================= TDD STATS =============================="
date --utc
mbc=`find ${BAHDIR}/../bin/ -type f -name '*.*' | grep -v .pyc | xargs cat | sed '/^\s*#/d;/^\s*$/d' | wc -l`
msc=`find ${BAHDIR}/../src/ -type f -name '*.*' | grep -v .pyc | xargs cat | sed '/^\s*#/d;/^\s*$/d' | wc -l`
mdc=`find ${BAHDIR}/../deployment/ -type f -name '*.*' | grep -v .pyc | xargs cat | sed '/^\s*#/d;/^\s*$/d' | wc -l`
mtc=`find ${BAHDIR}/../tests/ -type f -name '*.*' | grep -v .pyc | xargs cat | sed '/^\s*#/d;/^\s*$/d' | wc -l`
#echo $mlc $mtc
mlc=$(($mbc+$msc+$mdc))
tdd=`python -c "print float($mtc) / $mlc"`
echo "TDD Stats, Code:Test " $mlc:$mtc "ratio:" $tdd
########## Unit tests
echo "============================= UNIT TESTS ============================="
date --utc
python $CURRENT_DIR/unit/all.py
res=$?
if [[ $res -ne 0 ]] ; then
	echo "ABORT FURTHER TESTS"
	exit 1
fi

if [ -z "$AWSSECCONF" ]; then
	echo "NO AWSSECCONF VARIABLE DEFINED, NOT RUNNING AWS CHECKS"
	echo "(export AWSSECCONF='/path/to/security/config/file')"
	date --utc
	exit 1
fi

########## Deploy tests
echo "========================== DEPLOY (aws) TESTS ========================"
date --utc
python $CURRENT_DIR/deployment/all.py
res=$?
if [[ $res -ne 0 ]] ; then
	echo "ABORT FURTHER TESTS"
	date --utc
	exit 1
fi

########## Clean test machines older than one week, stop machines older than one day
echo "============================= CLEANING ==============================="
date --utc
yes | python $CURRENT_DIR/../deployment/aws/kill_or_stop_smarter.py
res=$?
if [[ $res -ne 0 ]] ; then
	echo "ABORT FURTHER TESTS"
	date --utc
	exit 1
fi

########## Service tests
echo "======================= SERVICE (aws) TESTS =========================="
date --utc
python $CURRENT_DIR/service/all.py
res=$?
if [[ $res -ne 0 ]] ; then
	echo "ABORT FURTHER TESTS"
	date --utc
	exit 1
fi

########## Kill stopped machines older than one day, kill machines younger than 6 hours with Test- in the name
echo "============================= CLEANING ==============================="
date --utc
yes | python $CURRENT_DIR/kill_recent_tests.py
res=$?
if [[ $res -ne 0 ]] ; then
	echo "ABORT FURTHER TESTS"
	date --utc
	exit 1
fi

########## Integration tests
echo "====================== INTEGRATION (aws) TESTS ======================="
date --utc
python $CURRENT_DIR/integration/all.py
res=$?
if [[ $res -ne 0 ]] ; then
	echo "INTEGRATION FAILED"
	date --utc
	exit 1
fi

######### Succeeded
date --utc
echo "OK"