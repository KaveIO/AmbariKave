#!/usr/bin/env python
##############################################################################
#
# Copyright 2016 KPMG Advisory N.V. (unless otherwise stated)
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

from math import ceil

nncores = None
hadoop_nodes = None

###########################
# Helper functions
###########################


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


def round_to_upper_even(num):
    if ceil(num) % 2 == 0:
        return ceil(num)
    else:
        return ceil(num) + 1


###########################
# vm class
###########################
class virtual_machine(object):
    """
    Wrapper class to help out in book-keeping
    """

    def __init__(self, vname, copies, cores, ram, jbod, os):
        self.os = int(os)
        self.jbod = float(jbod)
        self.ram = int(ram)
        self.cores = int(cores)
        self.copies = int(copies)
        self.vname = vname

    def arr(self):
        return [self.vname, self.copies, self.cores, self.ram, self.jbod, self.os]

    def innersum(self):
        arr = self.arr()
        return arr[0:1] + [self.copies] + [a * self.copies for a in arr[2:]]


class cluster(object):
    """
    Wrapper class to help out in book-keeping and pretty-printing
    """

    def __init__(self, multinode):
        self.machines = []
        self.multinode = multinode
        self.columns = ['     name', 'count', 'vcores', 'ram / GB',
                        'jbod_storage / TB', 'other_disk / GB']

    def sum(self):
        sums = [machine.innersum() for machine in self.machines]
        count = 1
        if multinode:
            count = sum([m[1] for m in sums])
        tsums = []
        for _i in range(1, len(sums[0]), 1):
            tsums.append(sum([m[_i] for m in sums]))
        asum = ['TOTAL'] + [count] + tsums[1:]
        return asum

    def to_df(self):
        import pandas
        resultdf = pandas.DataFrame(columns=self.columns)
        for machine in self.machines:
            resultdf.loc[len(resultdf)] = machine.arr()
        resultdf.loc[len(resultdf)] = self.sum()
        return resultdf

    def pretty_print(self):
        """
        Since pandas isn't always installed, I need my own pretty-print equivalent
        """
        fstring = ['{' + str(i) + ':>' + str(len(c)) + '}' for i, c in enumerate(self.columns)]
        fstring = '  '.join(fstring)
        print('{0:<2} '.format(' ') + fstring.format(*self.columns))
        for _i, machine in enumerate(self.machines):
            print('{0:<2} '.format(_i + 1) + fstring.format(*machine.arr()))
        print('{0:<2} '.format(' ') + fstring.format(*self.sum()))

###########################
# Calculators
###########################


def calc_storm_slots(rtdata):
    """
    Uses the existing realtime system we have in place to guess
    the number of storm slots required
    """
    return int(12 * rtdata / (100))


def is_hadoop_needed(data):
    """
    Will guess based upon the data size
    whether we need hadoop
    """
    if data > 0 and data < 0.3:
        print "For < 300 GB static input data, hadoop is not necessary"
        return False
    if data <= 0:
        return False
    return True


def is_multinode_needed(hadoop, storm, storm_slots=0):
    """
    If not using hadoop, and if the storm is small enough, then we
    can get away with only using a single large VM
    """
    if not hadoop and not storm and data <= 0.1:
        print "For <= 100 GB static input data, consider a single large VM"
        return False
    if data <= 0.1 and ((not storm) or storm_slots < 8):
        print "For <= 100 GB static input data, consider a single large VM"
        return False
    return True


def ambari_node(multinode, data_scientists, amb_cores=2, amb_nodes=1, amb_ram=6):
    if multinode:
        return virtual_machine('ambari', amb_nodes * multinode + 1 * (data_scientists == 0),
                               amb_cores * multinode, amb_ram * multinode, 0, 40)
    if data_scientists == 0:
        return virtual_machine('os', 1, 1, 2, 0, 20)


def ipa_node(multinode, ipa_cores=1, ipa_nodes=1, ipa_ram=3.5):
    if multinode:
        return virtual_machine('ipa', ipa_nodes, ipa_cores, ipa_ram, 0, 20)
    return None


def hadoop_nodes(data, multinode):
    global nncores
    global hadoop_nodes
    """
    Calculate sizes of the hadoop nodes
    """
    if data > 0.1 and data < 0.3:
        return [virtual_machine('datastore', 1 * multinode, 1 * multinode, 0, 0, data * 2000)]
    print "Recommended total hadoop storage is 3*(input data)*replication ~ 9*input size"
    tdisk = data * 9
    hadoop_nodes, cores_per_node, ram_per_node, disk_per_node = (0, 0, 0, 0)
    nncores, nnram_per_core, nnfac = (0, 4, 2)
    if data > 5:
        # in this case, use the recommended spec from ambari and scale the number of nodes
        disk_per_node = 16
        cores_per_node = 64
        ram_per_node = round_to_upper_even(cores_per_node * 4)
        hadoop_nodes = max(int(float(tdisk / 16)), 3)
        # then use smaller namenodes unless there is a very large cluster
        nnfac = 2 - int(hadoop_nodes >= 12)
        nncores = cores_per_node / nnfac
    elif data > 1.4:
        # in this case, use a small three-node setup and scale the disc and cores
        hadoop_nodes = 3
        disk_per_node = ceil(max(float(tdisk) / hadoop_nodes, 0.5) * 2) / 2
        # 32, 48, 64 cores for dnodes
        cores_per_node = 64
        if disk_per_node <= 8:
            cores_per_node = 32
        elif disk_per_node <= 12:
            cores_per_node = 48
        ram_per_node = round_to_upper_even(cores_per_node * 4)
        # 16, 24, 32 cores for nn
        nncores = cores_per_node / nnfac
    else:
        # tuned specifications based upon experience with
        # very small clusters
        # @ 0.3 TB -> 8 cores, 36 GB
        # @ 1 TB -> 16 cores, 72 GB
        # @ 1.2 TB, 24 cores, 112 GB
        hadoop_nodes = 3
        disk_per_node = ceil(max(float(data * 9) / hadoop_nodes, 0.5) * 2) / 2
        cores_per_node = min(max(round_to_upper_even(disk_per_node * disk_per_node * 1.9
                                                     - disk_per_node * 2.8 + 7), 2), 32)
        # Choose closest actual number of usable cores
        cores_per_node = min([8, 12, 16, 24, 32], key=lambda x: abs(x - cores_per_node))
        ram_per_node = min(round_to_upper_even(cores_per_node * 4.5), 128)
        # namenodes an be twice as small, but must at least meet a minimum spec for the overhead
        nncores = max(cores_per_node / nnfac, min(cores_per_node, 8))

    return [virtual_machine('datanodes', hadoop_nodes, cores_per_node, ram_per_node, disk_per_node, 30),
            virtual_machine('namenodes', 2, nncores, nnram_per_core * nncores, 0, 70)]


def gateway_nodes(data_scientists, multinode, nncores=None):
    """
    From the number of scientists, try to get the size of the gateway needed
    """
    if ds == 0:
        return []

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
    return virtual_machine('gateways', gateways, gw_cores, gw_ram, other_space, min(home_space + os_space, 500))


def mongo_node(data, multinode):
    # MongoDB
    mongo_data = float(data) / 10
    mongo_nodes = ceil(mongo_data)
    mongo_cores = round_to_upper_even(4 * mongo_data / mongo_nodes)
    mongo_ram = 2 * mongo_cores
    return virtual_machine('mongo', mongo_nodes * multinode,
                           mongo_cores, mongo_ram, 0, 1000 * mongo_data + 30 * multinode)


def storm_cluster(storm_slots, multinode):
    storm_nodes = int(max(storm_slots / 8, 1))
    storm_cores = round_to_upper_even(max(multinode + storm_slots / storm_nodes, 4))
    storm_ram = storm_cores * 4
    return [virtual_machine('storm-wrk', storm_nodes * multinode, storm_cores, storm_ram, 0, 30 * multinode),
            virtual_machine('nimbus', 1 * multinode, 2, 4, 0, 30 * multinode)]


def dev_node(multinode):
    dev_cores = 2
    dev_nodes = 1
    dev_ram = 8
    dev_disk = 100
    return virtual_machine('dev', dev_nodes * multinode, dev_cores * (1 + multinode) / 2,
                           dev_ram * (1 + multinode) / 2, 0.1, dev_disk + 30 * multinode)


def jboss_node(multinode):
    # jboss
    jboss_cores = 2
    jboss_nodes = 1
    jboss_ram = 4
    return virtual_machine('jboss', jboss_nodes * multinode, jboss_cores * (1 + multinode) / 2,
                           jboss_ram * (1 + multinode) / 2, 0, 20 * multinode)


def total(rdf):
    # calculate sum of input dataframe
    resultdf_total = resultdf.copy()
    for c in resultdf.columns:
        if c not in ["name", "count"]:
            resultdf_total[c] = resultdf_total[c] * \
                resultdf_total["count"].apply(lambda x: (multinode == 0) * 1 + multinode * x)

    sssum = resultdf_total.sum()
    sssum['name'] = 'TOTAL'
    return sssum


def relevent_blueprints(storm, hadoop, dev, mongo):
    ret = []
    if storm and hadoop > 0:
        ret.append("test/integration/blueprint/examplelambda.*.json")
    elif hadoop > 0:
        ret.append("test/integration/blueprint/examplehadoop.*.json")
    else:
        if storm:
            ret.append("test/integration/blueprint/STORM.*.json")
        if dev:
            ret.append("test/integration/blueprint/exampledev.*.json")
        if mongo:
            ret.append("test/service/blueprint/mongodb.*.json")
        if not (storm or dev or mongo):
            ret.append("test/integration/blueprint/KAVELANDING.*.json")
    return ret

############################
# Main
############################

if __name__ == '__main__':
    data = floatip("How much INPUT static data in TB? ")
    ds = floatip("How many data scientists? ")
    dev = yninput("Include development suite? ")
    storm = yninput("Include Storm (i.e. realtime data)? ")
    rtdata = 0
    if storm:
        rtdata = floatip("How much realtime data in MB per day? ")
    mongo = yninput("Include MongoDB? ")
    jboss = yninput("Include frontend server, i.e. JBOSS? ")

    # See if storm fits on a single node ...
    storm_slots = calc_storm_slots(rtdata)
    hadoop = is_hadoop_needed(data)
    multinode = is_multinode_needed(hadoop, storm, storm_slots=0)
    result_cluster = cluster(multinode)

    # ambari:
    if multinode or ds == 0:
        result_cluster.machines.append(ambari_node(multinode, ds))

    # ambari:
    if multinode:
        result_cluster.machines.append(ipa_node(multinode))

    if hadoop or data > 0.1:
        for line in hadoop_nodes(data, multinode):
            result_cluster.machines.append(line)

    if ds > 0:
        result_cluster.machines.append(gateway_nodes(ds, multinode, nncores))

    if mongo:
        result_cluster.machines.append(mongo_node(data, multinode))

    if storm:
        for line in storm_cluster(storm_slots, multinode):
            result_cluster.machines.append(line)

    if dev:
        result_cluster.machines.append(dev_node(multinode))

    if jboss:
        result_cluster.machines.append(jboss_node(multinode))

    print "------------------- Guess Reasonable Specs --------------------------------"
    result_cluster.pretty_print()
    # print resultdf
    if multinode:
        print "-----------------  Most relevant example blueprints  ----------------------"
        print "---- (don't forget to modify and test, especially modifying passwords) ----"
        for bp in relevent_blueprints(storm, hadoop, dev, mongo):
            print " -", bp
