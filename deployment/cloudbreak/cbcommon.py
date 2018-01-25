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
import cbparams
import urlparse
import base64
from string import Template
import time
import os
from requests.exceptions import RequestException


requests.packages.urllib3.disable_warnings()

KAVE_VERSION = "34-beta"

class CBDeploy():

    access_token = ""

    def __init__(self):
        self.get_access_token()

    def get_access_token(self):
        """
        Retrieves OAuth access token for Cloudbreak REST API.
        """

        token = None
        url = (cbparams.cb_http_url + ':' + str(cbparams.uaa_port) + '/oauth/authorize?response_type=token'
               + '&client_id=cloudbreak_shell&ope.0=openid&source=login&redirect_uri=http://cloudbreak.shell')
        headers = {'Accept': 'application/x-www-form-urlencoded',
                   'Content-type': 'application/x-www-form-urlencoded'}
        data = {'credentials': '{"username": "' + cbparams.cb_username +
                '", "password": "' + cbparams.cb_password + '"}'}

        try:
            auth = requests.post(
                url, data=data, headers=headers, allow_redirects=False)
            location_header = urlparse.urlparse(auth.headers["Location"])
            parsed_params = urlparse.parse_qsl(location_header.fragment)
            for item in parsed_params:
                if item[0] == "access_token":
                    token = item[1]
            self.access_token = token
        except Exception as e:
            print "Error getting Cloudbreak access token: ", e

    def check_for_template(self, hostgroup):
        """
        Checks if Cloudbreak template with given name exists
        """

        name = hostgroup + '-' + KAVE_VERSION
        path = '/cb/api/v1/templates/account/' + name
        url = cbparams.cb_https_url + path
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}

        try:
            response = requests.get(url, headers=headers, verify=cbparams.ssl_verify)
        except RequestException as e:
            print "Unable to get Cloudbreak template"
            raise
        if response.status_code == 200:
            return response.json()["id"]
        else:
            print str.format("Template with name {} does not exist.\nTemplate {} will be created.", name, name)
            return self.create_template(hostgroup)

    def create_template(self, hostgroup):
        """
        Creates Cloudbreak template with given name
        """

        path = '/cb/api/v1/templates/user/'
        url = cbparams.cb_https_url + path
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}

        try:
            with open('blueprints/hostgroups.azure.json') as hg_file:
                hgjson = json.load(hg_file)
        except (IOError, ValueError):
            raise StandardError("Error reading blueprints/hostgrups.azure.json file")
        if not (hgjson and hgjson.get(hostgroup)):
            raise ValueError(
                str.format("Description for hostgroup {} is missing in blueprints/hostgroups.azure.json file.",
                           hostgroup))

        name = hostgroup + '-' + KAVE_VERSION
        hostgroup_info = hgjson[hostgroup]
        data = {}
        data['name'] = name
        data['cloudPlatform'] = cbparams.cloud_platform
        data['parameters'] = {}
        data['parameters']['managedDisk'] = True
        data['instanceType'] = hostgroup_info['machine-type']
        data['volumeCount'] = hostgroup_info['volume-count']
        data['volumeSize'] = hostgroup_info['volume-size']
        data['volumeType'] = 'Standard_LRS'

        try:
            response = requests.post(url, data=json.dumps(
                data), headers=headers, verify=cbparams.ssl_verify)
        except RequestException as e:
            print str.format("Error creating Cloudbreak template with name {}: {}", name, response.text)
            raise
        if response.status_code == 200:
            print str.format("Created new Cloudbreak template with name {}", name)
            return response.json()["id"]
        else:
            raise ValueError(str.format("Error creating Cloudbreak template with name {}: {}", name, response.text))

    def check_for_blueprint(self, name):
        """
        Checks if Cloudbreak blueprint with given name exists
        """

        bp_name = name + '-' + KAVE_VERSION
        path = '/cb/api/v1/blueprints/account/' + bp_name
        url = cbparams.cb_https_url + path
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}

        try:
            response = requests.get(url, headers=headers, verify=cbparams.ssl_verify)
        except RequestException:
            print str.format("Unable to get Cloudbreak blueprint with name {}: {}", name, response.text)
            raise
        if response.status_code == 200:
            return response.json()
        else:
            print str.format("Blueprint with name {} does not exist.\nBlueprint {} will be created.", bp_name, bp_name)
            return self.create_blueprint(name)

    def create_blueprint(self, name):
        """
        Creates Cloudbreak blueprint with given name
        """

        if not self.verify_blueprint(name):
            return False

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/blueprints/user'
        url = cbparams.cb_https_url + path

        try:
            with open('blueprints/' + name + '.blueprint.json') as bp_file:
                bp = json.load(bp_file)
        except (IOError, ValueError) as e:
            raise StandardError(str.format("No correct blueprint .json file found for {}: {}", name, e))

        data = {}
        bp_name = name + '-' + KAVE_VERSION
        data['name'] = bp_name
        data['ambariBlueprint'] = bp

        try:
            response = requests.post(url, data=json.dumps(
                data), headers=headers, verify=cbparams.ssl_verify)
        except RequestException:
            print str.format("Unable to create Cloudbreak blueprint with name {}: {}", name, response.text)
            raise
        if response.status_code == 200:
            print str.format("Created new Cloudbreak blueprint with name {}", bp_name)
            return response.json()
        else:
            raise StandardError("Error creating Cloudbreak blueprint with name {}: {}", bp_name, response.text)

    def verify_blueprint(self, bp_name):

        b = os.path.exists('blueprints/' + bp_name + '.blueprint.json')
        if not b:
            print str.format("No correct blueprint .json file found for {}", bp_name)
            return False

        bp = {}
        try:
            with open('blueprints/' + bp_name + '.blueprint.json') as bp_file:
                bp = json.load(bp_file)
        except (IOError, ValueError):
            print str.format("Json file {}.blueprint.json is not complete or not readable", bp_name)
            return False
        if "host_groups" not in bp:
            print str.format("Missing 'host_groups' definition in {}.blueprint.json", bp_name)
            return False
        if "Blueprints" not in bp:
            print str.format("Missing 'Blueprints' definition in {}.blueprint.json", bp_name)
            return False
        return True

    def verify_hostgroups(self, hg_names):
        """
        Check if list of hostgroups, have the corresponding definitions in hostgroups.azure.json
        """

        h = os.path.exists('blueprints/hostgroups.azure.json')
        if not h:
            print str.format("File hostgroups.azure.json not found")
            return False
        hg_defs = {}
        try:
            with open('blueprints/hostgroups.azure.json') as hgs_file:
                hg_defs = json.load(hgs_file)
        except (IOError, ValueError):
            print "Json file hostgroups.azure.json is not complete or is not readable."
            return False
        for hg in hg_names:
            if hg not in hg_defs:
                print str.format("Missing details for hostgroup '{}' in hostgroups.azure.json file.", hg)
                return False
            for prop in ["machine-type", "volume-size", "volume-count", "instance-type",
                         "security-group", "node-count", "recipes"]:
                if prop not in hg_defs[hg]:
                    print str.format("'{}' for '{}' hostgroup is not definined in hostgroups.azure.json", prop, hg)
                    return False
                if not hg_defs[hg][prop]:
                    print str.format("Invalid or missing value for '{}' property in '{}' hostgroup definition",
                                     prop, hg)
                    return False
        return True

    def check_for_recipe(self, name):
        """
        Checks if Cloudbreak recipe with given name exists
        """

        recipe_name = name + '-' + KAVE_VERSION
        path = '/cb/api/v1/recipes/account/' + recipe_name
        url = cbparams.cb_https_url + path
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}

        try:
            response = requests.get(url, headers=headers, verify=cbparams.ssl_verify)
        except RequestException:
            print str.format("Unable to get details for recipe {} from Cloudbreak: {}", recipe_name, response.text)
            raise
        if response.status_code == 200:
            return response.json()["id"]
        else:
            print str.format("Recipe with name {} does not exist.\nRecipe {} will be created.",
                             recipe_name, recipe_name)
            return self.create_recipe(name)

    def create_recipe(self, name):
        """
        Creates Cloudbreak recipe with given name
        """

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/recipes/user'
        url = cbparams.cb_https_url + path

        try:
            with open('recipes/recipe_details.json') as rd_file:
                rd = json.load(rd_file)
        except (IOError, ValueError) as e:
            raise StandardError("Json file recipe_details.json is not complete or is not readable. ")

        if (rd.get(name)):
            details = rd[name]
        else:
            raise ValueError("Missing details for recipe {} in recipe_details.json", name)

        data = {}
        data['name'] = name + '-' + KAVE_VERSION
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
            data['content'] = base64.b64encode(content)
        else:
            data['content'] = base64.b64encode(rec)

        try:
            response = requests.post(url, data=json.dumps(
                data), headers=headers, verify=cbparams.ssl_verify)
        except RequestException:
            print str.format("Unable to create Cloudbreak recipe {}-{}", name, KAVE_VERSION)
            raise
        if response.status_code == 200:
            print str.format("Created new Cloudbreak recipe {}-{}", name, KAVE_VERSION)
            return response.json()["id"]
        else:
            raise StandardError("Error creating Cloudbreak recipe {}-{}: {}",
                                name, KAVE_VERSION, response.text)

    def create_stack(self, blueprint_name, credential):
        """
        Creates Cloudbreak stack with given blueprint name
        """

        try:
            with open("stack_template.json") as stack_file:
                stack = json.load(stack_file)
        except (IOError, ValueError) as e:
            raise StandardError("Json file stack_template.json is not complete or is not readable.")
        stack["name"] = blueprint_name.lower() + str(int(time.time()))
        blueprint = self.check_for_blueprint(blueprint_name)
        if blueprint:
            hgs = [item["name"]
                   for item in blueprint["ambariBlueprint"]["host_groups"]]
        else:
            raise Exception("Terminating stack creation for blueprint " + blueprint_name)
        if not self.verify_hostgroups(hgs):
            raise Exception("Terminating stack creation for blueprint " + blueprint_name)
        try:
            with open("blueprints/hostgroups.azure.json") as hgs_file:
                hg_info = json.load(hgs_file)
        except (IOError, ValueError) as e:
            raise StandardError("Json file blueprints/hostgroups.azure.json is not complete or is not readable.")
        for hg in hgs:
            instance = {}
            instance["templateId"] = self.check_for_template(hg)
            instance["group"] = hg
            instance["nodeCount"] = hg_info[hg]["node-count"]
            instance["type"] = hg_info[hg]["instance-type"]
            instance["securityGroupId"] = self.get_security_group_id(hg_info[hg]["security-group"])
            stack["instanceGroups"].append(instance)

        stack["credentialId"] = credential["id"]
        if cbparams.region:
            stack["region"] = cbparams.region
        else:
            raise ValueError("Missing region information. Please provide correct value for region in cbparams.pys")
        stack["networkId"] = self.get_network_id()
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/stacks/user'
        url = cbparams.cb_https_url + path
        try:
            response = requests.post(url, data=json.dumps(
                stack), headers=headers, verify=cbparams.ssl_verify)
        except RequestException:
            print str.format("Unable to create stack for blueprint {}", blueprint_name)
            raise
        if response.status_code == 200:
            return (blueprint, response.json()["id"])
        else:
            raise Exception(str.format("Stack {} could not be created: {}", stack["name"], response.text))

    def create_cluster(self, blueprint, stack_id, credential):
        """
        Creates Cloudbreak cluster with given blueprint name and stack id
        """

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/stacks/' + str(stack_id)
        url = cbparams.cb_https_url + path
        try:
            stack = requests.get(url, headers=headers,
                                 verify=cbparams.ssl_verify).json()
        except RequestException:
            print str.format("Unable to get stack with id {} from Cloudbreak.", stack_id)
            raise

        try:
            with open("cluster_template.json") as cl_file:
                cluster = json.load(cl_file)
        except (IOError, ValueError):
            raise StandardError("File cluster_template.json is not complete or is not readable.")
        try:
            with open("blueprints/hostgroups.azure.json") as hgs_file:
                hg_info = json.load(hgs_file)
        except (IOError, ValueError):
            raise StandardError("File blueprints/hostgroups.azure.json is not complete or is not readable.")
        cluster["name"] = stack["name"]
        cluster["blueprintId"] = blueprint["id"]

        hgs = [item["name"]
               for item in blueprint["ambariBlueprint"]["host_groups"]]
        if not self.verify_hostgroups(hgs):
            raise Exception("Terminating stack creation for blueprint " + blueprint_name)
        for hg in hgs:
            hostgroup = {}
            hostgroup["name"] = hg
            hostgroup["constraint"] = {}
            hostgroup["constraint"]["instanceGroupName"] = hg
            hostgroup["constraint"]["hostCount"] = 1
            hostgroup["recipeIds"] = self.get_recipe_ids(hg_info[hg]["recipes"])
            cluster["hostGroups"].append(hostgroup)

        if cbparams.adls_enabled and cbparams.adls_name:
            fileSystem = {}
            fileSystem["type"] = "ADLS"
            fileSystem["defaultFs"] = False
            fileSystem["name"] = stack["name"]
            fileSystem["properties"] = {}
            fileSystem["properties"]["tenantId"] = credential["parameters"]["tenantId"]
            fileSystem["properties"]["clientId"] = credential["parameters"]["accessKey"]
            fileSystem["properties"]["accountName"] = cbparams.adls_name
            fileSystem["properties"]["secure"] = False
            cluster["fileSystem"] = fileSystem

        url = url + '/cluster'
        try:
            response = requests.post(url, data=json.dumps(
                cluster), headers=headers, verify=cbparams.ssl_verify)
        except RequestException:
            print str.format("Error creating cluster {}", stack["name"])
            raise

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(str.format("Cluster {} could not be created: {}", stack["name"], response.text))

    def get_recipe_ids(self, recipe_names):
        recipe_ids = []
        for recipe in recipe_names:
            rid = self.check_for_recipe(recipe)
            recipe_ids.append(rid)
        return recipe_ids

    def get_network_id(self):
        if cbparams.network_name:
            headers = {"Authorization": "Bearer " +
                       self.access_token, "Content-type": "application/json"}
            path = '/cb/api/v1/networks/account/' + cbparams.network_name
            url = cbparams.cb_https_url + path
            try:
                response = requests.get(url, headers=headers, verify=cbparams.ssl_verify)
            except RequestException:
                print str.format("Unable to get information about Cloudbreak network {}", cbparams.network_name)
                raise
            else:
                if response.status_code == 200:
                    return response.json()["id"]
                else:
                    raise ValueError(str.format("Unable to obtain Cloudbreak network {}: {} - {}", cbparams.network_name,
                                                response.status_code, response.text))
        else:
            raise ValueError("Missing network name. Please provide correct value for network_name in cbparams.py")

    def get_credential(self):
        if cbparams.credential_name:
            headers = {"Authorization": "Bearer " +
                       self.access_token, "Content-type": "application/json"}
            path = '/cb/api/v1/credentials/account/' + cbparams.credential_name
            url = cbparams.cb_https_url + path
            try:
                response = requests.get(url, headers=headers, verify=cbparams.ssl_verify)
            except RequestException as e:
                print "Unable to obtain Cloudbreak credential."
                raise
            else:
                if response.status_code == 200:
                    return response.json()
                else:
                    raise ValueError("Unable to obtain Cloudbreak credential.")
        else:
            raise ValueError("Missing credential name. Please provide correct value for credential_name in cbparams.py")

    def get_security_group_id(self, name):
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/securitygroups/account/' + name
        url = cbparams.cb_https_url + path
        try:
            response = requests.get(url, headers=headers, verify=cbparams.ssl_verify)
        except RequestException:
            print "Unable to get Cloudbreak security group"
            raise
        return response.json()["id"]

    def delete_stack_by_id(self, id):
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/stacks/' + str(id)
        url = cbparams.cb_https_url + path
        params = {"forced": True}
        try:
            response = requests.delete(url, headers=headers, params=json.dumps(params), verify=cbparams.ssl_verify)
        except RequestException:
            print str.format("Cluster with id {} and its infrastructure could not be deleted.", id)
            raise
        if response.status_code != 204:
            raise StandardError(str.format(
                "Cluster with id {} and its infrastructure could not be deleted: {}", id, response.text))
        else:
            print str.format("Cluster with id {} and its infrastructure were successfully deleted.", id)

    def delete_stack_by_name(self, name):
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/stacks/user/' + name
        url = cbparams.cb_https_url + path
        params = {"forced": True}
        try:
            response = requests.delete(url, headers=headers, params=json.dumps(params), verify=cbparams.ssl_verify)
        except RequestException:
            print str.format("Cluster {} and its infrastructure could not be deleted.", name)
            raise
        if response.status_code != 204:
            raise StandardError(str.format(
                "Cluster {} and its infrastructure could not be deleted: {}", name, response.text))
        else:
            print str.format("Cluster {} and its infrastructure were successfully deleted.", name)
            return True

    def wait_for_cluster(self, name, kill_passed=False, kill_failed=False, kill_all=False, verbose=False):
        """
        Creates Cloudbreak cluster with given blueprint name and waits for it to be up
        """

        try:
            credential = self.get_credential()
            blueprint, stack_id = self.create_stack(name, credential)
            cluster = self.create_cluster(blueprint, stack_id, credential)
        except Exception as e:
            print "FAILURE: ", e
            return

        print str.format("Cluster {} requested. Waiting for Ambari...", cluster["name"])

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/stacks/' + str(stack_id)
        url = cbparams.cb_https_url + path

        max_execution_time = 5400
        start = timer = int(time.time())
        timeout = start + max_execution_time
        interval = 10
        retries_count = 0
        max_retries = 5
        latest_status = ""
        latest_status_reason = ""

        while timer < timeout:
            response = requests.get(
                url, headers=headers, verify=cbparams.ssl_verify)
            if response.status_code != 200:
                if retries_count < max_retries:
                    retries_count += 1
                    time.sleep(interval)
                    timer = int(time.time())
                else:
                    print str.format(
                        "FAILURE: Unable to obtain status for cluster {}. Connection to Cloudbreak might be lost.",
                        cluster["name"])
                    if kill_failed or kill_all:
                        self.delete_stack_by_name(cluster["name"])
                    return False
            else:
                if response.json() and response.json().get("status") and response.json().get("cluster"):
                    # if change in latest stack status is observed, log message
                    if verbose and (response.json()["status"] != latest_status
                                    or response.json()["statusReason"] != latest_status_reason):
                        latest_status = response.json()["status"]
                        latest_status_reason = response.json()["statusReason"]
                        print str.format("{} -- stack status: {} - {}; cluster status: {}",
                                         cluster["name"], response.json()["status"], response.json()["statusReason"],
                                         response.json()["cluster"]["status"])
                    if response.json()["status"].startswith("DELETE"):
                        print str.format("FAILURE: Requested deletion for cluster {}. Terminating current process.",
                                         cluster["name"])
                        return False
                    if response.json()["status"] == "AVAILABLE" and response.json()["cluster"]["status"] == "AVAILABLE":
                        print str.format("SUCCESS: Cluster {} was deployed in {} seconds.",
                                         response.json()["name"], (timer - start))
                        if kill_passed or kill_all:
                            print str.format("Cluster {} and its infrastructure will be deleted.", cluster["name"])
                            self.delete_stack_by_name(cluster["name"])
                        return True
                    if response.json()["status"].endswith("FAILED") \
                            or response.json()["cluster"]["status"].endswith("FAILED"):
                        print str.format("FAILURE: Cluster deployment {} failed. Stack status - {}: {}. Cluster status- {} : {}", cluster["name"],
                                         response.json()["status"], response.json()["statusReason"])
                        if kill_failed or kill_all:
                            print str.format("Cluster {} and its infrastructure will be deleted.", cluster["name"])
                            self.delete_stack_by_name(cluster["name"])
                        return False
                # reset retries_count after success
                if retries_count != 0:
                    retries_count = 0
                time.sleep(interval)
                timer = int(time.time())

        print str.format("FAILURE: Cluster {} failed to complete in {} seconds.",
                         cluster["name"], (max_execution_time))
        if kill_failed or kill_all:
            print str.format("Cluster {} and its infrastructure will be deleted.", cluster["name"])
            self.delete_stack_by_name(cluster["name"])
        return False
