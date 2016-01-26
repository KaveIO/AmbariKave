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
                    then goes on to calculate the recommended spec based upon the RET KAVE
"""

import pandas
from math import ceil

resultdf = pandas.DataFrame(columns=['name','count','vcores','ram / GB','jbod_storage / TB','other_disk / GB'])


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
mongo = yninput("Include MongoDB? ")
jboss = yninput("Include frontend server, i.e. JBOSS? ")
dev = yninput("Include development suite? ")
storm = yninput("Include Storm (i.e. realtime data)? ")
rtdata=0
if storm:
    rtdata = floatip("How much realtime data in MB per day? ")


def round_to_upper_even(num):
    if ceil(num)%2 ==0:
        return ceil(num)
    else:
        return ceil(num)+1

# See if storm fits on a single node ...
storm_slots = int(12 * rtdata / (100))

multinode=1
hadoop=True
if data == 0:
    hadoop=False
if data > 0 and data < 0.3 and ((not storm) or storm_slots < 8):
    print "For < 300 GB static input data, hadoop is not necessary"
    hadoop=False
if data <= 0.1 and ((not storm) or storm_slots < 8):
    print "For <= 100 GB static input data, consider a single large VM"
    multinode=0

# ambari:
if multinode:
    amb_cores = 2
    amb_nodes = 1
    amb_ram = 4
    resultdf.loc[len(resultdf)]=['ambari',amb_nodes*multinode+1*(ds==0),amb_cores*multinode,amb_ram*multinode,0,20]
elif ds==0:
    resultdf.loc[len(resultdf)]=['os',1,1,2,0,20]

# Gateways and home required
if ds>0:
    gateways = max(ceil(float(ds) / 8)*multinode,1)
    ds_per_gateway = ceil(float(ds)/gateways)
    gw_cores = max(round_to_upper_even(2+ds_per_gateway),8)
    gw_ram = gw_cores*4
    home_space = 100*max(ds/gateways,1)
    other_space = 100

    resultdf.loc[len(resultdf)]=['gateways',gateways,gw_cores,gw_ram,0.1,home_space+20*multinode+10]

# Hadoop space required
if data>=0.3:
    print "NB: Recommended total hadoop storage is 3*(input data)*replication ~ 9*input size"

if data>5:
    tdisk = data*9
    hadoop_nodes = max(int(float(tdisk / 16)), 3)
    disk_per_node = 16
    cores_per_node = 64
    ram_per_node = cores_per_node * 5
    nnfac = 1 + int(hadoop_nodes>=12)
    resultdf.loc[len(resultdf)]=['datanodes',hadoop_nodes,cores_per_node,ram_per_node,disk_per_node,30]
    resultdf.loc[len(resultdf)]=['namenodes',2,cores_per_node/nnfac,cores_per_node*4/nnfac,0,70]
elif data>1.2:
    tdisk = data*9
    hadoop_nodes = 3
    disk_per_node = ceil(max(float(tdisk)/hadoop_nodes,0.5)*2)/2
    # 32, 48, 64 cores for dnodes
    cores_per_node=64
    if disk_per_node <= 8:
        cores_per_node=32
    elif disk_per_node <= 12:
        cores_per_node=48
    ram_per_node = cores_per_node * 5

    resultdf.loc[len(resultdf)]=['datanodes',hadoop_nodes,cores_per_node,ram_per_node,disk_per_node,30]
    # 16, 24, 32 cores for nn
    nncores=cores_per_node/2
    nnram=nncores*4
    resultdf.loc[len(resultdf)]=['namenodes',2,nncores,nnram,0,70]
elif data>=0.3:
    hadoop_nodes = 3
    disk_per_node = ceil(max(float(data*9)/hadoop_nodes,0.5)*2)/2
    cores_per_node = min(round_to_upper_even(max(disk_per_node*6, 4)),64)
    ram_per_node = round_to_upper_even(cores_per_node * 4.6)

    resultdf.loc[len(resultdf)]=['datanodes',hadoop_nodes,cores_per_node,ram_per_node,disk_per_node,30]
    nncores=max(cores_per_node/2,min(cores_per_node,8))
    nnram=nncores*4
    resultdf.loc[len(resultdf)]=['namenodes',2,max(cores_per_node/2,min(cores_per_node,8)),max(ram_per_node/2,min(ram_per_node,32)),0,70]
elif data>0.1:
    resultdf.loc[len(resultdf)]=['datastore',1*multinode,1*multinode,0,0,data*2000]
#print resultdf

# MongoDB
mongo_data = float(data)/10
mongo_nodes = ceil(mongo_data)
mongo_cores = round_to_upper_even(4*mongo_data/mongo_nodes)
mongo_ram = 2*mongo_cores

if mongo:
    resultdf.loc[len(resultdf)]=['mongo',mongo_nodes*multinode,mongo_cores,mongo_ram,0,1000*mongo_data+30*multinode]

# Storm
storm_slots = int(12 * rtdata / (100))
storm_nodes = int(max(storm_slots/8,1))
storm_cores = round_to_upper_even(max(multinode+storm_slots/storm_nodes,4))
storm_ram=storm_cores*4

if storm:
    resultdf.loc[len(resultdf)]=['storm-workers',storm_nodes*multinode,storm_cores,storm_ram,0,30*multinode]
    resultdf.loc[len(resultdf)]=['storm-nimbus',1*multinode,2,4,0,30*multinode]

# dev
dev_cores = 2
dev_nodes = 1
dev_ram = 4
dev_disk = 100

if dev:
    resultdf.loc[len(resultdf)]=['dev',dev_nodes*multinode,dev_cores*(1+multinode)/2,dev_ram*(1+multinode)/2,0.1,dev_disk+30*multinode]

# jboss
jboss_cores = 2
jboss_nodes = 1
jboss_ram = 4

if jboss:
    resultdf.loc[len(resultdf)]=['jboss',jboss_nodes*multinode,jboss_cores*(1+multinode)/2,jboss_ram*(1+multinode)/2,0,20*multinode]

# calculate sums and append
resultdf_total=resultdf.copy()
for c in resultdf.columns:
    if c not in ["name","count"]:
        resultdf_total[c]=resultdf_total[c]*resultdf_total["count"].apply(lambda x: (multinode==0)*1+multinode*x)

sssum=resultdf_total.sum()
sssum['name']='TOTAL'

resultdf.loc[len(resultdf)] = sssum
print "---------------Recommended Specs-------------------------------------------"
print resultdf

