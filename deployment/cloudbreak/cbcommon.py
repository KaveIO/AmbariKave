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
"""
A Python module, containing functions for interaction with Cloudbreak.
"""

import requests
import json
from config import cbparams
import sys
if sys.version_info[0] > 2:
    import urllib.parse as urlparse
else:
    import urlparse
import base64
from string import Template
import time
import os
from socket import gethostbyname
from requests.exceptions import RequestException


requests.packages.urllib3.disable_warnings()

KAVE_VERSION = "34-beta"


class CBDeploy:

    access_token = ""

    def __init__(self):
        self.get_access_token()

    def get_access_token(self):
        """
        Retrieves OAuth access token for Cloudbreak REST API.
        """

        import getpass

        token = None
        stored_credentials = os.path.isfile(os.path.expanduser('~/.cbcredstore'))

        if stored_credentials:
            try:
                with open(os.path.expanduser('~/.cbcredstore')) as cred_file:
                    content = cred_file.readline().strip().split(',')
                    user = content[0]
                    passwd = base64.b64decode(content[1]).decode()
            except (IOError, ValueError):
                print ("Error reading Cloudbreak login credentials.")
                raise
        else:
            if sys.version_info[0] > 2:
                user = input("Please enter Cloudbreak username: ")
            else:
                user = raw_input("Please enter Cloudbreak username: ")
            passwd = getpass.getpass()

        url = (cbparams.cb_url + '/identity/oauth/authorize?response_type=token'
               + '&client_id=cloudbreak_shell&ope.0=openid&source=login&redirect_uri=http://cloudbreak.shell')
        headers = {'Accept': 'application/x-www-form-urlencoded',
                   'Content-type': 'application/x-www-form-urlencoded'}
        data = {'credentials': '{"username": "' + user +
                '", "password": "' + passwd + '"}'}

        try:
            auth = requests.post(
                url, data=data, headers=headers, allow_redirects=False, verify=cbparams.ssl_verify)
            location_header = urlparse.urlparse(auth.headers["Location"])
            parsed_params = urlparse.parse_qsl(location_header.fragment)
            for item in parsed_params:
                if item[0] == "access_token":
                    token = item[1]
            self.access_token = token
        except Exception as e:
            print ("Error getting Cloudbreak access token: ", e)
        if (not stored_credentials) and self.access_token:
            # if getting token passed successfully, store the login credentials
            self.store_cloudbreak_user_credentials(user, base64.b64encode(passwd.encode()).decode())

    def store_cloudbreak_user_credentials(self, username, password):
        """
        Store Cloudbreak username and password in the user home to be used for further authentication
        :param username: Cloudbreak username
        :param password: Cloudbreak password
        """
        try:
            content = username + ',' + password
            file = open(os.path.expanduser('~/.cbcredstore'), "w")
            file.writelines(content)
            file.close()
            os.chmod(os.path.expanduser('~/.cbcredstore'), 0o600)
        except:
            print ("Cloudbreak credentials were not successfully stored.")

    def check_for_blueprint(self, name):
        """
        Checks if Cloudbreak blueprint with given name exists
        """

        bp_name = name + '-' + KAVE_VERSION
        path = '/cb/api/v1/blueprints/account/' + bp_name
        url = cbparams.cb_url + path
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}

        try:
            response = requests.get(url, headers=headers, verify=cbparams.ssl_verify)
        except RequestException:
            print (str.format("Unable to get Cloudbreak blueprint with name {}: {}", name, response.text))
            raise
        if response.status_code == 200:
            if self.compare_blueprints(response.json(), name):
                # local and Cloudbreak versions are the same; use this resource
                return response.json()
            else:
                # try to delete the resource from Cloudbreak and create a new one
                print (str.format("Trying to delete existing {} blueprint...", name))
                if self.delete_blueprint(name):
                    # resource was deleted successfully; create a new one with the same name
                    return self.create_blueprint(name)
                else:
                    # resource was not deleted; create a new one with a different name
                    import random
                    import string
                    print (str.format("Creating new {} blueprint... ", name))
                    rnd_str = ''.join([random.choice(string.ascii_lowercase) for n in range(5)])
                    return self.create_blueprint(name, rnd_str)
        else:
            print (str.format("Blueprint with name {} does not exist.\nBlueprint {} will be created.",
                              bp_name, bp_name))
            return self.create_blueprint(name)

    def create_blueprint(self, name, random=False):
        """
        Creates Cloudbreak blueprint with given name
        """

        if not self.verify_blueprint(name):
            return False

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/blueprints/user'
        url = cbparams.cb_url + path

        try:
            with open('blueprints/' + name + '.blueprint.json') as bp_file:
                bp = json.load(bp_file)
        except (IOError, ValueError) as e:
            raise StandardError(str.format("No correct blueprint .json file found for {}: {}", name, e))

        data = {}
        if (random):
            bp_name = name + '-' + random + '-' + KAVE_VERSION
        else:
            bp_name = name + '-' + KAVE_VERSION
        data['name'] = bp_name
        data['ambariBlueprint'] = base64.b64encode(json.dumps(bp).encode()).decode()

        try:
            response = requests.post(url, data=json.dumps(
                data), headers=headers, verify=cbparams.ssl_verify)
        except RequestException:
            print (str.format("Unable to create Cloudbreak blueprint with name {}: {}", name, response.text))
            raise
        if response.status_code == 200:
            print (str.format("Created new Cloudbreak blueprint with name {}", bp_name))
            return response.json()
        else:
            raise StandardError("Error creating Cloudbreak blueprint with name {}: {}", bp_name, response.text)

    def delete_blueprint(self, name):
        """
        Delete blueprint from Cloudbreak server
        :param name: blueprint name
        """
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/blueprints/user/' + name + '-' + KAVE_VERSION
        url = cbparams.cb_url + path

        try:
            response = requests.delete(url, headers=headers, verify=cbparams.ssl_verify)
        except RequestException:
            print (str.format("Unable to delete Cloudbreak blueprint with name {}: {}",
                              name + '-' + KAVE_VERSION, response.text))
            raise
        if response.status_code == 204:
            print (str.format("Blueprint {} successfully deleted.", name + '-' + KAVE_VERSION))
            return True
        else:
            print (str.format("Error deleting Cloudbreak blueprint with name {}: {}",
                              name + '-' + KAVE_VERSION, response.text))
            return False

    def compare_blueprints(self, res, name):
        """
        Compare if the local blueprint is the same as this returned from Cloudbreak server
        :param res: data returned from CB server API
        :param name: name of the local blueprint to compare
        """

        local_resource_name = 'blueprints/' + name + '.blueprint.json'
        res = json.loads(base64.b64decode(res['ambariBlueprint']))
        try:
            with open(local_resource_name) as lr_file:
                loc_res = json.load(lr_file)
        except (IOError, ValueError) as e:
            raise StandardError(
                str.format(
                    "File blueprints/{}.blueprint.json is not complete or is not readable.",
                    name))
        if res == loc_res:
            return True
        else:
            print (str.format("Local and remote versions of blueprint {} don't match!", name))
            return False

    def compare_recipes(self, res, name):
        """
        Compare if the local recipe is the same as this returned from Cloudbreak server
        :param res: data returned from CB server API
        :param name: name of the local recipe to compare
        """

        res = base64.b64decode(res['content'])
        try:
            with open('recipes/recipe_details.json') as rd_file:
                rd = json.load(rd_file)
        except (IOError, ValueError) as e:
            raise StandardError("Json file recipe_details.json is not complete or is not readable. ")
        with open(rd[name]['templatePath']) as rf:
            loc_rec = rf.read()
        if res == loc_rec:
            return True
        else:
            print (str.format("Local and remote versions of recipe {} don't match!", name))
            return False

    def verify_blueprint(self, bp_name):
        """
        Verifies if a blueprint with [bp_name].blueprint.json exists in blueprints directory.
        Verifies that the JSON contains definitions about host_groups and Blueprints
        Verifies that AMBARI_SERVER and FREEIPA_SERVER components are not installed on the same host
        :param bp_name: blueprint name
        """

        b = os.path.exists('blueprints/' + bp_name + '.blueprint.json')
        if not b:
            print (str.format("No correct blueprint .json file found for {}", bp_name))
            return False

        bp = {}
        try:
            with open('blueprints/' + bp_name + '.blueprint.json') as bp_file:
                bp = json.load(bp_file)
        except (IOError, ValueError):
            print (str.format("Json file {}.blueprint.json is not complete or not readable", bp_name))
            return False
        if "host_groups" not in bp:
            print (str.format("Missing 'host_groups' definition in {}.blueprint.json", bp_name))
            return False
        if "Blueprints" not in bp:
            print (str.format("Missing 'Blueprints' definition in {}.blueprint.json", bp_name))
            return False
        # Verify that AMBARI_SREVER and FREEIPA_SREVER components won't be installed on the same host
        for hg in bp["host_groups"]:
            comps = [cn["name"] for cn in hg["components"]]
            if "AMBARI_SERVER" in comps and "FREEIPA_SERVER" in comps:
                print ("Both AMBARI_SERVER and FREEIPA_SERVER components detected in hostgroup " +
                       hg["name"] + ". Make sure these components don't reside in the same hostgroup.")
                return False
        return True

    def verify_hostgroups(self, hg_names):
        """
        Check if list of hostgroups, have the corresponding definitions in hostgroups.azure.json
        """

        h = os.path.exists('config/hostgroups.azure.json')
        if not h:
            print (str.format("File hostgroups.azure.json not found"))
            return False
        hg_defs = {}
        try:
            with open('config/hostgroups.azure.json') as hgs_file:
                hg_defs = json.load(hgs_file)
        except (IOError, ValueError):
            print ("Json file hostgroups.azure.json is not complete or is not readable.")
            return False
        hostgroups = {}
        for hg in hg_names:
            if hg not in hg_defs:
                print (str.format("Missing details for hostgroup '{}' in hostgroups.azure.json file.", hg))
                return False
            for prop in ["instance-type", "volume-size", "volume-count", "type",
                         "security-group", "node-count", "recipes"]:
                if prop not in hg_defs[hg]:
                    print (str.format("'{}' for '{}' hostgroup is not definined in hostgroups.azure.json", prop, hg))
                    return False
                if not hg_defs[hg][prop]:
                    print (str.format("Invalid or missing value for '{}' property in '{}' hostgroup definition",
                                      prop, hg))
                    return False
                # Verify that "patchambari" recipe is executed only on Ambari nodes
                if "patchambari" in hg_defs[hg]["recipes"] and hg_defs[hg]["type"] != "GATEWAY":
                    print (str.format('Wrong hostgroup definition for {}. "patchamabri" recipe can be only executed '
                                      'on Ambari Server nodes.', hg))
                    return False
                hostgroups[hg] = hg_defs[hg]
        return hostgroups

    def check_for_recipe(self, name):
        """
        Checks if Cloudbreak recipe with given name exists
        :param name: name of the recipe
        """

        recipe_name = name + '-' + KAVE_VERSION
        path = '/cb/api/v1/recipes/account/' + recipe_name
        url = cbparams.cb_url + path
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}

        try:
            response = requests.get(url, headers=headers, verify=cbparams.ssl_verify)
        except RequestException:
            print (str.format("Unable to get details for recipe {} from Cloudbreak: {}", recipe_name, response.text))
            raise
        if response.status_code == 200:
            if self.compare_recipes(response.json(), name):
                # local and Cloudbreak versions are the same; use this resource
                return response.json()['name']
            else:
                # delete recipe from Cloudbreak and create a new one
                print (str.format("Trying to delete existing recipe {} ...", name))
                if self.delete_recipe(name):
                    return self.create_recipe(name)
                else:
                    # recipe was not deleted; create a new one with a different name
                    import random
                    import string
                    print (str.format("Creating new {} recipe... ", name))
                    rnd_str = ''.join([random.choice(string.ascii_lowercase) for n in range(5)])
                    return self.create_recipe(name, rnd_str)
        else:
            print (str.format("Recipe with name {} does not exist.\nRecipe {} will be created.",
                              recipe_name, recipe_name))
            return self.create_recipe(name)

    def create_recipe(self, name, random=False):
        """
        Creates Cloudbreak recipe with given name
        If random parameter is passed the name of the recipe is build with this parameter in it to avoid
        overwriting of existing recipe
        :param name: recipe name
        :param random: random string to append to recipe name
        """

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/recipes/user'
        url = cbparams.cb_url + path

        try:
            with open('recipes/recipe_details.json') as rd_file:
                rd = json.load(rd_file)
        except (IOError, ValueError) as e:
            raise StandardError("Json file recipe_details.json is not complete or is not readable. ")

        if rd.get(name):
            details = rd[name]
        else:
            raise ValueError("Missing details for recipe {} in recipe_details.json", name)

        data = {}
        if random:
            rec_name = name + '-' + random + '-' + KAVE_VERSION
        else:
            rec_name = name + '-' + KAVE_VERSION
        data['name'] = rec_name
        data['recipeType'] = details['recipeType']
        data['description'] = details['description']
        try:
            with open(details["templatePath"]) as rec_file:
                rec = rec_file.read()
        except (IOError, ValueError):
            raise StandardError(str.format("File {} is missing or is not readable. ", details["templatePath"]))
        if details.get("params"):
            temp = Template(rec)
            content = content.substitute(details["params"])
            data['content'] = base64.encode(content.encode()).decode()
        else:
            data['content'] = base64.b64encode(rec.encode()).decode()

        try:
            response = requests.post(url, data=json.dumps(
                data), headers=headers, verify=cbparams.ssl_verify)
        except RequestException:
            print (str.format("Unable to create Cloudbreak recipe {}", rec_name))
            raise
        if response.status_code == 200:
            print (str.format("Created new Cloudbreak recipe {}", rec_name))
            return response.json()["name"]
        else:
            raise StandardError("Error creating Cloudbreak recipe {}: {}", rec_name, response.text)

    def delete_recipe(self, name):
        """
        Delete recipe from Cloudbreak server
        :param name: recipe name
        """
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/recipes/user/' + name + '-' + KAVE_VERSION
        url = cbparams.cb_url + path

        try:
            response = requests.delete(url, headers=headers, verify=cbparams.ssl_verify)
        except RequestException:
            print (str.format("Unable to delete Cloudbreak recipe {}-{}", name, KAVE_VERSION))
            raise
        if response.status_code == 204:
            print (str.format("Successfully deleted Cloudbreak recipe {}-{}", name, KAVE_VERSION))
            return True
        else:
            print (str.format("Error deleting Cloudbreak recipe {}-{}: {}", name, KAVE_VERSION, response.text))
            return False

    def create_instancegroup(self, instancegroup, recipes):
        """
        Return instance configuration based on hostgroups.azure.json
        :param instancegroup: name of the instance group
        :param recipes: recipes to be applied for this instance
        """

        try:
            with open('config/hostgroups.azure.json') as hg_file:
                hgjson = json.load(hg_file)
        except (IOError, ValueError):
            raise StandardError("Error reading blueprints/hostgrups.azure.json file")
        if not (hgjson and hgjson.get(instancegroup)):
            raise ValueError(
                str.format("Description for hostgroup {} is missing in config/hostgroups.azure.json file.",
                           instancegroup))

        hostgroup_info = hgjson[instancegroup]
        instance = {}
        try:
            with open('instancegroup_template.json') as ig_file:
                instance = json.load(ig_file)
        except (IOError, ValueError):
            raise StandardError("Error reading blueprints/hostgrups.azure.json file")
        instance['group'] = instancegroup
        instance['type'] = hostgroup_info['type']

        instance['template']['instanceType'] = hostgroup_info['instance-type']
        instance['template']['volumeCount'] = hostgroup_info['volume-count']
        instance['template']['volumeSize'] = hostgroup_info['volume-size']
        instance['template']['volumeType'] = hostgroup_info['volume-type']
        instance["securityGroup"] = self.create_security_group(hostgroup_info['security-group'])
        instance["recipeNames"] = []
        for recipe in hostgroup_info["recipes"]:
            instance["recipeNames"].append(recipes[recipe])
        return instance

    def get_my_public_ip(self):
        """
        Try to determine the public IP by
        parsing output from https://jsonip.com
        """
        try:
            response = requests.get('https://jsonip.com')
        except RequestException as e:
            print ("Unable to get public IP address")
            raise
        else:
            if response.status_code == 200:
                return str(response.json()['ip'])

    def create_security_group(self, name):
        """
        Read local security groups config file
        :param name: name of the config file
        """
        cbhost = urlparse.urlparse(cbparams.cb_url)
        cb_ip = gethostbyname(cbhost.hostname)
        try:
            filtered_data = ''
            with open('securitygroups/' + name + '.json') as sg_file:
                raw_data = sg_file.read()
                filtered_data = raw_data.replace('<only-me>', self.get_my_public_ip() +
                                                 "/32").replace('<cloudbreak-ip>', cb_ip + "/32")
            sg = json.loads(filtered_data)
        except (IOError, ValueError) as e:
            raise StandardError("Error processing " + name + ".json")
        return sg

    def delete_stack_by_id(self, id):
        """
        Try to delete cluster by its Cloudbreak ID
        :param id: cluster ID
        """

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/stacks/' + str(id)
        url = cbparams.cb_url + path
        params = {"forced": True}
        try:
            response = requests.delete(url, headers=headers, params=json.dumps(params), verify=cbparams.ssl_verify)
        except RequestException:
            print (str.format("Cluster with id {} and its infrastructure could not be deleted.", id))
            raise
        if response.status_code != 204:
            raise StandardError(str.format(
                "Cluster with id {} and its infrastructure could not be deleted: {}", id, response.text))
        else:
            print (str.format("Cluster with id {} and its infrastructure were successfully deleted.", id))

    def delete_stack_by_name(self, name):
        """
        Try to delete cluster by cluster name
        :param name: cluster name
        """

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/stacks/user/' + name
        url = cbparams.cb_url + path
        params = {"forced": True}
        try:
            response = requests.delete(url, headers=headers, params=json.dumps(params), verify=cbparams.ssl_verify)
        except RequestException:
            print (str.format("Cluster {} and its infrastructure could not be deleted.", name))
            raise
        if response.status_code != 204:
            raise StandardError(str.format(
                "Cluster {} and its infrastructure could not be deleted: {}", name, response.text))
        else:
            print (str.format("Cluster {} and its infrastructure were successfully deleted.", name))
            return True

    def get_ssh_public_key(self, path):
        """
        Get the public ssh key from path. If param not set defaults to ~/.ssh/id_rsa.pub
        :param path: path to the public key - default ~/.ssh/id_rsa.pub
        """
        if not path:
            path = os.path.expanduser('~') + "/.ssh/id_rsa.pub"
        try:
            with open(path) as key_file:
                pkey_content = key_file.read()
            return pkey_content.rstrip('\r\n')
        except (IOError, ValueError):
            raise

    def get_public_ips(self, instances):
        """
        Collect public IPs of all the hosts in the cluster
        :param instances: deployed instances data returned by Amabri server API
        """

        ips = {}
        for ig in instances:
            if ig["metadata"] and ig["metadata"][0] and ig["metadata"][0]["publicIp"]:
                ips[ig["group"]] = ig["metadata"][0]["publicIp"]
            else:
                return False
        return ips


    def distribute_package(self, remoteip):
        """
        Create tarball with Kave patch and copy to remoteip
        :param remoteip: the IP address of the remote machine
        """

        import subprocess

        # if no SSH private key location is set, use the default ~/.ssh/id_rsa
        if not cbparams.ssh_private_key:
            cbparams.ssh_private_key = os.path.expanduser('~') + "/.ssh/id_rsa"
        subprocess.call(["tar", "czf", "kave-patch.tar.gz", "-C", "../../src", "KAVE", "shared"])
        print ("Copying KAVE archive to a remote machine...")
        subprocess.call(["scp", "-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no",
                         "-i", cbparams.ssh_private_key, "kave-patch.tar.gz", "../../dev/dist_kavecommon.py",
                         "cloudbreak@" + remoteip + ":~"])
        subprocess.call(["rm", "-rf", "kave-patch.tar.gz"])

    def distribute_keys(self, remoteip, ipa_server_node=False):
        """
        Create /root/.ssh folder in the remoteip host, than copy the authorized_keys file from cloudbreak user to
        root user. If the remote host has FreeIPA component (ipa_server_node parameter),
        copy local public key to remote root user folder
        :param remoteip: the IP address of the remote machine
        :param ipa_server_node: does the remote machine contains FreeIPA server component
        """

        import subprocess

        # if no SSH private key location is set, use the default ~/.ssh/id_rsa
        if not cbparams.ssh_private_key:
            cbparams.ssh_private_key = os.path.expanduser('~') + "/.ssh/id_rsa"
        subprocess.call(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
                         "-i", cbparams.ssh_private_key, "cloudbreak@" + remoteip,
                         "sudo", "mkdir", "-p", "/root/.ssh"])
        subprocess.call(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
                         "-i", cbparams.ssh_private_key, "cloudbreak@" + remoteip,
                         "sudo", "cp", "/home/cloudbreak/.ssh/authorized_keys", "/root/.ssh/authorized_keys"])

        if ipa_server_node:
            subprocess.call(["scp", "-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no",
                             "-i", cbparams.ssh_private_key, cbparams.ssh_private_key,
                             "cloudbreak@" + remoteip + ":~/id_rsa"])
            subprocess.call(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
                             "-i", cbparams.ssh_private_key, "cloudbreak@" + remoteip,
                             "sudo", "mv", "/home/cloudbreak/id_rsa", "/root/.ssh/id_rsa"])
            subprocess.call(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
                             "-i", cbparams.ssh_private_key, "cloudbreak@" + remoteip,
                             "sudo", "chmod", "600", "/root/.ssh/id_rsa"])
            subprocess.call(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
                             "-i", cbparams.ssh_private_key, "cloudbreak@" + remoteip,
                             "sudo", "chown", "root:root", "/root/.ssh/id_rsa"])

    def find_nodes_with_component(self, cluster, component):
        """
        Find all nodes in the cluster that contains give component
        :param cluster: cluster data
        :param component: name of the component to search
        """

        nodes = []
        bp = json.loads(base64.b64decode(cluster['cluster']['blueprint']['ambariBlueprint']))
        for hg in bp['host_groups']:
            for comp in hg["components"]:
                if comp["name"] == component:
                    nodes.append(hg["name"])
        return nodes

    def get_credential(self):
        """
        Try to obtain account details from Cloudbreak account
        """

        if cbparams.credential_name:
            headers = {"Authorization": "Bearer " +
                       self.access_token, "Content-type": "application/json"}
            path = '/cb/api/v1/credentials/account/' + cbparams.credential_name
            url = cbparams.cb_url + path
            try:
                response = requests.get(url, headers=headers, verify=cbparams.ssl_verify)
            except RequestException as e:
                print ("Unable to obtain Cloudbreak credential.")
                raise
            else:
                if response.status_code == 200:
                    return response.json()
                else:
                    raise ValueError("Unable to obtain Cloudbreak credential.")
        else:
            raise ValueError("Missing credential name. Please provide correct value for credential_name in cbparams.py")

    def create_cluster(self, name, local_repo):
        """
        Try to collect and send all the information for cluster creation to Cloudbreak server
        :param name: blueprint name that will be submitted
        :param local_repo: should we use local repository or we will checkout from git
        """

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v2/stacks/user'
        url = cbparams.cb_url + path
        try:
            with open("cluster_template.json") as cl_file:
                cluster = json.load(cl_file)
        except (IOError, ValueError):
            raise StandardError("File cluster_template.json is not complete or is not readable.")

        blueprint = self.check_for_blueprint(name)
        cluster["general"]["name"] = name.lower() + str(int(time.time()))
        cluster["general"]["credentialName"] = cbparams.credential_name

        cluster["placement"]["region"] = cbparams.region
        cluster["cluster"]["ambari"]["blueprintName"] = blueprint["name"]

        cluster["stackAuthentication"]["publicKey"] = self.get_ssh_public_key(cbparams.ssh_public_key)

        cluster["imageSettings"]["imageCatalog"] = cbparams.image_catalog
        cluster["imageSettings"]["imageId"] = cbparams.image_id

        if blueprint:
            ambp = json.loads(base64.b64decode(blueprint["ambariBlueprint"]))
            hgs = [item["name"] for item in ambp["host_groups"]]

        hg_defs = self.verify_hostgroups(hgs)
        if not hg_defs:
            raise Exception("Terminating stack creation for blueprint ", name)
        recipes = set()
        recipes_mapping = {}
        for hg in hgs:
            recipes = recipes.union(hg_defs[hg]["recipes"])
        for recipe in recipes:
            if local_repo and recipe == "patchambari":
                recipes_mapping[recipe] = self.check_for_recipe(recipe + "-git")
            else:
                recipes_mapping[recipe] = self.check_for_recipe(recipe)
        for hg in hgs:
            instance = self.create_instancegroup(hg, recipes_mapping)
            cluster["instanceGroups"].append(instance)

        if cbparams.adls_enabled and cbparams.adls_name:
            credential = self.get_credential()
            fileSystem = {}
            fileSystem["type"] = "ADLS"
            fileSystem["defaultFs"] = False
            fileSystem["name"] = cluster["general"]["name"]
            fileSystem["properties"] = {}
            fileSystem["properties"]["tenantId"] = credential["parameters"]["tenantId"]
            fileSystem["properties"]["clientId"] = credential["parameters"]["accessKey"]
            fileSystem["properties"]["accountName"] = cbparams.adls_name
            fileSystem["properties"]["secure"] = False
            cluster["fileSystem"] = fileSystem

        try:
            response = requests.post(url, data=json.dumps(
                cluster), headers=headers, verify=cbparams.ssl_verify)
        except RequestException:
            print (str.format("Error creating cluster {}", cluster["general"]["name"]))
            raise
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(str.format("Cluster {} could not be created: {}", cluster["general"]["name"],
                                       response.text))

    def wait_for_cluster(self, name, local_repo=False, kill_passed=False, kill_failed=False, kill_all=False,
                         verbose=False):
        """
        Wait for cluster until it is ready. Check for cluster status and report errors is any
        :param name: blueprint name
        :param local_repo: use local repository for Kave patch or checkout it from git
        :param kill_passed: terminate all clusters that are successfully built - for testing purposes
        :param kill_failed: terminate all clusters that failed to built - for testing purposes
        :param kill_all: terminate all clusters at the end - for testing purposes
        :param verbose: be more verbose
        """
        freeipa_included = False
        freeipa_server_list = []
        try:
            cluster = self.create_cluster(name, local_repo)
            freeipa_server_list = self.find_nodes_with_component(cluster, "FREEIPA_SERVER")
            if freeipa_server_list:
                freeipa_included = True
        except Exception as e:
            print ("FAILURE: ", e)
            return

        print (str.format("Cluster {} requested. Waiting for Ambari...", cluster["name"]))

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v2/stacks/' + str(cluster["id"]) + '/status'
        url = cbparams.cb_url + path

        # How much time to wait for the cluster to become ready
        max_execution_time = 7200
        start = timer = int(time.time())
        timeout = start + max_execution_time
        # How much seconds to sleep between the server checks
        interval = 10
        retries_count = 0
        # How many times to try to obtain HTTP status 200 from the cluster
        max_retries = 5
        latest_status = ""
        latest_status_reason = ""
        package_distributed = False
        keys_distributed = False

        while timer < timeout:
            response = requests.get(
                url, headers=headers, verify=cbparams.ssl_verify)
            if response.status_code != 200:
                if retries_count < max_retries:
                    retries_count += 1
                    time.sleep(interval)
                    timer = int(time.time())
                else:
                    print (str.format(
                        "FAILURE: Unable to obtain status for cluster {}. Connection to Cloudbreak might be lost.",
                        cluster['name']))
                    if kill_failed or kill_all:
                        self.delete_stack_by_name(cluster['name'])
                    return False
            else:
                if response.json() and response.json().get("status") and response.json().get("clusterStatus"):
                    # if change in latest stack status is observed, log message
                    if verbose and (response.json()["status"] != latest_status
                                    or response.json()["statusReason"] != latest_status_reason):
                        latest_status = response.json()["status"]
                        latest_status_reason = response.json()["statusReason"]
                        print (str.format("{} -- stack status: {} - {}; cluster status: {} - {}",
                                          cluster['name'], response.json()["status"], response.json()["statusReason"],
                                          response.json()["clusterStatus"], response.json()["clusterStatusReason"]))
                    if response.json()["status"].startswith("DELETE"):
                        print (str.format("FAILURE: Requested deletion for cluster {}. Terminating current process.",
                                          cluster['name']))
                        return False
                    if response.json()["status"] == "AVAILABLE" and response.json()["clusterStatus"] == "AVAILABLE":
                        print (str.format("SUCCESS: Cluster {} was deployed in {} seconds.",
                                          cluster["name"], (timer - start)))
                        if kill_passed or kill_all:
                            print (str.format("Cluster {} and its infrastructure will be deleted.", cluster['name']))
                            self.delete_stack_by_name(cluster['name'])
                        return True
                    if response.json()["status"].endswith("FAILED") \
                            or (response.json()["clusterStatus"].endswith("FAILED")):
                        msg = str.format("FAILURE: Cluster deployment {} failed. Stack status - {}: {}.",
                                         cluster['name'], response.json()["status"], response.json()["statusReason"])
                        if response.json()["clusterStatus"] and response.json()["clusterStatusReason"]:
                            msg += str.format(" Cluster status: {} - {}", response.json()["clusterStatus"],
                                              response.json()["clusterStatusReason"])
                        print (msg)
                        if kill_failed or kill_all:
                            print (str.format("Cluster {} and its infrastructure will be deleted.", cluster["name"]))
                            self.delete_stack_by_name(cluster['name'])
                        return False

                    if (local_repo and not package_distributed) or (freeipa_included and not keys_distributed):
                        cluster_info = requests.get(url[0:url.rfind('/')],
                                                    headers=headers, verify=cbparams.ssl_verify)
                        if local_repo and not package_distributed:
                            ambarinode = [node for node in cluster_info.json()['instanceGroups']
                                          if node["type"] == 'GATEWAY'][0]
                            if ambarinode['metadata'] and ambarinode['metadata'][0]\
                                    and ambarinode['metadata'][0]['publicIp']:
                                ambari_ip = ambarinode['metadata'][0]['publicIp']
                                if ambari_ip:
                                    self.distribute_package(ambari_ip)
                                    package_distributed = True
                        if freeipa_included and not keys_distributed:
                            instancegroups = cluster_info.json()['instanceGroups']
                            igs = self.get_public_ips(instancegroups)
                            if igs:
                                for ig in igs:
                                    if ig in freeipa_server_list:
                                        self.distribute_keys(igs[ig], True)
                                    else:
                                        self.distribute_keys(igs[ig])
                                keys_distributed = True
                # reset retries_count after success
                if retries_count != 0:
                    retries_count = 0
                time.sleep(interval)
                timer = int(time.time())

        print (str.format("FAILURE: Cluster {} failed to complete in {} seconds.",
                          cluster['name'], (max_execution_time)))
        if kill_failed or kill_all:
            print (str.format("Cluster {} and its infrastructure will be deleted.", cluster['name']))
            self.delete_stack_by_name(cluster['name'])
        return False
