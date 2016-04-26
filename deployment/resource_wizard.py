#!/usr/bin/env python
##############################################################################
#
# Copyright 2015 KPMG N.V. (unless otherwise stated)
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
"""
resource_wizard.py: with very few inputs, guess the number of CPU/RAM/Disk that is required
                    for a KAVE. Uses some simple logic to decide if hadoop is needed
                    then goes on to guess a reasonable spec based upon a production KAVE
                    NB: this is a GUESS, real production clusters require fine-tuning
                    once the operational pattern of those clusters is known
"""

import pandas
from math import ceil

resultdf = pandas.DataFrame(columns=['name', 'count', 'vcores', 'ram / GB', 'jbod_storage / TB', 'other_disk / GB'])


def trueorfalse(astring):
    """
    Boolean cast from a string, understanding most ways of saying yes
    if I don't understand it, raise a TypeError
    """
    cnv = {'1': True, 'true': True, 'y': True, 'ye': True, 'yes': True, 'positive': True, 'affirmative': True,
           '0': False, 'false': False, 'n': False, 'no': False, 'none': False, 'negative': False}
    ts = type(astring)
    if ts is bool:
        return astring
    elif ts is str or ts is unicode:
        astring = astring.lower().strip()
        try:
            return cnv[astring]
        except KeyError:
            pass
        if not len(astring):
            return False
    elif astring is None:
        return False
    elif ts is int:
        return bool(astring)
    raise TypeError("Cannot guess boolean value equivalent for " + str(astring))


def floatip(message):
    for _ in range(10):
        try:
            v = raw_input(message)
            return float(v)
        except ValueError:
            continue
    raise ValueError("You must enter a number")


def yninput(message):
    for _ in range(10):
        try:
            v = raw_input(message)
            return trueorfalse(v)
        except ValueError:
            continue
    raise ValueError("You must enter something which is a synonym with true or false")

data = floatip("How much INPUT static data in TB? ")
ds = floatip("How many data scientists? ")
dev = yninput("Include development suite? ")
storm = yninput("Include Storm (i.e. realtime data)? ")
rtdata = 0
if storm:
    rtdata = floatip("How much realtime data in MB per day? ")
mongo = yninput("Include MongoDB? ")
jboss = yninput("Include frontend server, i.e. JBOSS? ")


def round_to_upper_even(num):
    if ceil(num) % 2 == 0:
        return ceil(num)
    else:
        return ceil(num) + 1

# See if storm fits on a single node ...
storm_slots = int(12 * rtdata / (100))

multinode = 1
hadoop = True
if data == 0:
    hadoop = False
if data > 0 and data < 0.3 and ((not storm) or storm_slots < 8):
    print "For < 300 GB static input data, hadoop is not necessary"
    hadoop = False
if data <= 0.1 and ((not storm) or storm_slots < 8):
    print "For <= 100 GB static input data, consider a single large VM"
    multinode = 0
if data > 10:
    print "For > 10 TB testing the performance becomes very important to cluster optimization"
    multinode = 0

# ambari:
if multinode:
    amb_cores = 2
    amb_nodes = 1
    amb_ram = 4
    resultdf.loc[len(resultdf)] = ['ambari', amb_nodes * multinode + 1 *
                                   (ds == 0), amb_cores * multinode, amb_ram * multinode, 0, 30]
elif ds == 0:
    resultdf.loc[len(resultdf)] = ['os', 1, 1, 2, 0, 20]

hadoop_nodes = 0
nncores = 0
nnram = 0
# Hadoop space required
if data >= 0.3:
    print "Recommended total hadoop storage is 3*(input data)*replication ~ 9*input size"

if data > 5:
    tdisk = data * 9
    hadoop_nodes = max(int(float(tdisk / 16)), 3)
    disk_per_node = 16
    cores_per_node = 64
    ram_per_node = round_to_upper_even(cores_per_node * 4)
    nnfac = 2 - int(hadoop_nodes >= 12)
    resultdf.loc[len(resultdf)] = ['datanodes', hadoop_nodes, cores_per_node, ram_per_node, disk_per_node, 30]
    resultdf.loc[len(resultdf)] = ['namenodes', 2, cores_per_node / nnfac, cores_per_node * 4 / nnfac, 0, 70]
elif data > 1.4:
    tdisk = data * 9
    hadoop_nodes = 3
    disk_per_node = ceil(max(float(tdisk) / hadoop_nodes, 0.5) * 2) / 2
    # 32, 48, 64 cores for dnodes
    cores_per_node = 64
    if disk_per_node <= 8:
        cores_per_node = 32
    elif disk_per_node <= 12:
        cores_per_node = 48
    ram_per_node = round_to_upper_even(cores_per_node * 4)

    resultdf.loc[len(resultdf)] = ['datanodes', hadoop_nodes, cores_per_node, ram_per_node, disk_per_node, 30]
    # 16, 24, 32 cores for nn
    nncores = cores_per_node / 2
    nnram = nncores * 4
    resultdf.loc[len(resultdf)] = ['namenodes', 2, nncores, nnram, 0, 70]
elif data >= 0.3:
    # @ 0.3 TB -> 8 cores, 36 GB
    # @ 1 TB -> 16 cores, 72 GB
    # @ 1.2 TB, 24 cores, 112 GB
    hadoop_nodes = 3
    disk_per_node = ceil(max(float(data * 9) / hadoop_nodes, 0.5) * 2) / 2
    cores_per_node = min(max(round_to_upper_even(disk_per_node * disk_per_node * 1.9 - disk_per_node * 2.8 + 7), 2), 32)
    cores_per_node = min([8, 12, 16, 24, 32], key=lambda x: abs(x - cores_per_node))
    ram_per_node = min(round_to_upper_even(cores_per_node * 4.5), 128)

    resultdf.loc[len(resultdf)] = ['datanodes', hadoop_nodes, cores_per_node, ram_per_node, disk_per_node, 30]
    nncores = max(cores_per_node / 2, min(cores_per_node, 8))
    nnram = nncores * 4
    resultdf.loc[len(resultdf)] = ['namenodes', 2, nncores,
                                   nnram, 0, 70]
elif data > 0.1:
    resultdf.loc[len(resultdf)] = ['datastore', 1 * multinode, 1 * multinode, 0, 0, data * 2000]
# print resultdf


# Gateways and home required
if ds > 0:
    gateways = max(ceil(float(ds) / 8) * multinode, 1)
    ds_per_gateway = ceil(float(ds) / gateways)
    gw_cores = round_to_upper_even(2 + ds_per_gateway)
    gw_cores = min([8, 12, 16, 24, 32, 48, 64], key=lambda x: abs(x - gw_cores - 1.5))
    # if more than namenode, round down
    if nncores:
        gw_cores = min(nncores, gw_cores)
    # if < 8, round up ...
    gw_cores = max(gw_cores, 8)
    gw_ram = gw_cores * 4
    # 1 user 100 GB
    # 2 users 200 GB
    # 5 users 350 GB
    # 8 users 500 GB
    home_space = max(
        min(ceil(1.5 * ds_per_gateway - 0.05 * ds_per_gateway * ds_per_gateway + 0.5) * 50, 500), 100)
    os_space = 20 * multinode + 10
    other_space = 0.1

    resultdf.loc[len(resultdf)] = ['gateways', gateways, gw_cores, gw_ram, other_space, min(home_space + os_space, 500)]


# MongoDB
mongo_data = float(data) / 10
mongo_nodes = ceil(mongo_data)
mongo_cores = round_to_upper_even(4 * mongo_data / mongo_nodes)
mongo_ram = 2 * mongo_cores

if mongo:
    resultdf.loc[len(resultdf)] = ['mongo', mongo_nodes * multinode, mongo_cores,
                                   mongo_ram, 0, 1000 * mongo_data + 30 * multinode]

# Storm
storm_slots = int(12 * rtdata / (100))
storm_nodes = int(max(storm_slots / 8, 1))
storm_cores = round_to_upper_even(max(multinode + storm_slots / storm_nodes, 4))
storm_ram = storm_cores * 4

if storm:
    resultdf.loc[len(resultdf)] = ['storm-workers', storm_nodes * multinode, storm_cores, storm_ram, 0, 30 * multinode]
    resultdf.loc[len(resultdf)] = ['storm-nimbus', 1 * multinode, 2, 4, 0, 30 * multinode]

# dev
dev_cores = 2
dev_nodes = 1
dev_ram = 4
dev_disk = 100

if dev:
    resultdf.loc[len(resultdf)] = ['dev', dev_nodes * multinode, dev_cores * (1 + multinode) /
                                   2, dev_ram * (1 + multinode) / 2, 0.1, dev_disk + 30 * multinode]

# jboss
jboss_cores = 2
jboss_nodes = 1
jboss_ram = 4

if jboss:
    resultdf.loc[len(resultdf)] = ['jboss', jboss_nodes * multinode, jboss_cores *
                                   (1 + multinode) / 2, jboss_ram * (1 + multinode) / 2, 0, 20 * multinode]

# calculate sums and append
resultdf_total = resultdf.copy()
for c in resultdf.columns:
    if c not in ["name", "count"]:
        resultdf_total[c] = resultdf_total[c] * \
            resultdf_total["count"].apply(lambda x: (multinode == 0) * 1 + multinode * x)

sssum = resultdf_total.sum()
sssum['name'] = 'TOTAL'

resultdf.loc[len(resultdf)] = sssum
print "------------------- Guess Reasonable Specs --------------------------------"
print resultdf
if multinode:
    print "-----------------  Most relevant example blueprints  ----------------------"
    print "---- (don't forget to modify and test, especially modifying passwords) ----"
    if storm and hadoop_nodes > 0:
        print "- test/integration/blueprint/examplelambda.*.json"
    elif hadoop_nodes > 0:
        print "- test/integration/blueprint/examplehadoop.*.json"
    else:
        if storm:
            print "- test/integration/blueprint/STORM.*.json"
        if dev:
            print "- test/integration/blueprint/exampledev.*.json"
        if mongo:
            print "- test/service/blueprint/mongodb.*.json"
        if not (storm or dev or mongo):
            print "- test/integration/blueprint/KAVELANDING.*.json"
