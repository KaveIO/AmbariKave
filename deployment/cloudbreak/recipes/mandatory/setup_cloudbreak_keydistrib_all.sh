#!/bin/sh
##############################################################################
#
# Copyright 2017 KPMG Advisory N.V. (unless otherwise stated)
#
# Licensed under the Apache License, Version 2.0 (the "License");
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
##############################################################################

#This is a Cloudbreak pre-recipe for all nodes.

#Make sure you insert the desired private key below and that you replace that with a new one on every host when the deployment is finished.
USER=cloudbreak
KEYFILE=/home/$USER/.ssh/authorized_keys
cat << EOF >> $KEYFILE
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDJKDRYe54LKtlGX6i8pXoRR33n8vaCLyNxF1V7U1RTg2mv8siQT1JZkQ4rtRF+5nwGIUW8hSPFU1r3aDx6M7D5tcN9f0iWn9V6aXDEGxJHqX69yvinvAsVaCLkUFNxhTN3NxQpAxBE5vaRdQh2h+PAVT8XwXtA9OobEiPLHEgBd2UAl1YyECavZPWwRUFbCHuodlYP/9j1xcplAm60zJqSSlHDBWV3ysayulZlE16YfGkBRn16E0EdVk4oKC3L5gyz9YPdKRSyxj0ym514rVkrtvXba/7pfPM/kHTZnVo93x8P/HKvAeZ7K7ARjarAqW09aAspRHqlfm0S2qH9EjFn ksheytanov@intracol.com
EOF
chown $USER:$USER $KEYFILE
chmod 600 $KEYFILE
