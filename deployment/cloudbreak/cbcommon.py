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
import requests
import json
import cbparams
import urlparse
import base64
from string import Template
import time


requests.packages.urllib3.disable_warnings()


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

        name = hostgroup + '-' + cbparams.kave_version
        path = '/cb/api/v1/templates/account/' + name
        url = cbparams.cb_https_url + path
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}

        response = requests.get(url, headers=headers, verify=cbparams.ssl_verify)
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

        with open('blueprints/hostgroups.azure.json') as hg_file:
            hgjson = json.load(hg_file)
        if not (hgjson and hgjson.get(hostgroup)):
            print "Description for hostgroup " + hostgroup + " is missing in blueprints/hostgroups.azure.json."
            return False

        name = hostgroup + '-' + cbparams.kave_version
        hostgroup_info = hgjson[hostgroup]
        data = {}
        data['name'] = name
        data['cloudPlatform'] = 'AZURE'
        data['parameters'] = {}
        data['parameters']['managedDisk'] = True
        data['instanceType'] = hostgroup_info['machine-type']
        data['volumeCount'] = hostgroup_info['volume-count']
        data['volumeSize'] = hostgroup_info['volume-size']
        data['volumeType'] = 'Standard_LRS'

        response = requests.post(url, data=json.dumps(
            data), headers=headers, verify=cbparams.ssl_verify)
        if response.status_code == 200:
            print str.format("Created new Cloudbreak template with name {}", name)
            return response.json()["id"]
        else:
            print str.format("Error creating Cloudbreak template with name {}", name)
            print response.text
            return False

    def check_for_blueprint(self, name):
        """
        Checks if Cloudbreak blueprint with given name exists
        """

        bp_name = name + '-' + cbparams.kave_version
        path = '/cb/api/v1/blueprints/account/' + bp_name
        url = cbparams.cb_https_url + path
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}

        response = requests.get(url, headers=headers, verify=cbparams.ssl_verify)
        if response.status_code == 200:
            return response.json()
        else:
            print str.format("Blueprint with name {} does not exist.\nBlueprint {} will be created.", bp_name, bp_name)
            return self.create_blueprint(name)

    def create_blueprint(self, name):
        """
        Creates Cloudbreak blueprint with given name
        """

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/blueprints/user'
        url = cbparams.cb_https_url + path

        try:
            with open('blueprints/' + name + '.blueprint.json') as bp_file:
                bp = json.load(bp_file)
        except (IOError, ValueError):
            print str.format("No correct blueprint .json file found for {}", name)
            return False

        data = {}
        bp_name = name + '-' + cbparams.kave_version
        data['name'] = bp_name
        data['ambariBlueprint'] = bp

        response = requests.post(url, data=json.dumps(
            data), headers=headers, verify=cbparams.ssl_verify)
        if response.status_code == 200:
            print str.format("Created new Cloudbreak blueprint with name {}", bp_name)
            return response.json()
        else:
            print str.format("Error creating Cloudbreak blueprint with name {}", bp_name)
            print response.text
            return False

    def check_for_recipe(self, name):
        """
        Checks if Cloudbreak recipe with given name exists
        """

        recipe_name = name + '-' + cbparams.kave_version
        path = '/cb/api/v1/recipes/account/' + recipe_name
        url = cbparams.cb_https_url + path
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}

        response = requests.get(url, headers=headers, verify=cbparams.ssl_verify)
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

        details = cbparams.recipes[name]
        data = {}
        data['name'] = name + '-' + cbparams.kave_version
        data['recipeType'] = details['recipeType']
        data['description'] = details['description']
        with open(details["templatePath"]) as rec_file:
            rec = rec_file.read()
        if details.get("params"):
            temp = Template(rec)
            content = content.substitute(details["params"])
            data['content'] = base64.b64encode(content)
        else:
            data['content'] = base64.b64encode(rec)

        response = requests.post(url, data=json.dumps(
            data), headers=headers, verify=cbparams.ssl_verify)
        if response.status_code == 200:
            print str.format("Created new Cloudbreak recipe with name {}-{}", name, cbparams.kave_version)
            return response.json()["id"]
        else:
            print str.format("Error creating Cloudbreak recipe with name {}-{}", name, cbparams.kave_version)
            return False

    def create_stack(self, blueprint_name, credential):
        """
        Creates Cloudbreak stack with given blueprint name
        """

        with open("stack_template.json") as stack_file:
            stack = json.load(stack_file)
        with open("blueprints/hostgroups.azure.json") as hgs_file:
            hg_info = json.load(hgs_file)
        stack["name"] = blueprint_name.lower() + str(int(time.time()))
        blueprint = self.check_for_blueprint(blueprint_name)
        if blueprint:
            hgs = [item["name"]
                   for item in blueprint["ambariBlueprint"]["host_groups"]]
        for hg in hgs:
            instance = {}
            instance["templateId"] = self.check_for_template(hg)
            instance["group"] = hg
            instance["nodeCount"] = 1
            instance["type"] = hg_info[hg]["instance-type"]
            instance["securityGroupId"] = hg_info[hg]["securityGroup"]
            stack["instanceGroups"].append(instance)

        stack["credentialId"] = credential["id"]
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/stacks/user'
        url = cbparams.cb_https_url + path
        response = requests.post(url, data=json.dumps(
            stack), headers=headers, verify=cbparams.ssl_verify)
        return (blueprint, response.json()["id"])

    def create_cluster(self, blueprint, stack_id):
        """
        Creates Cloudbreak cluster with given blueprint name and stack id
        """

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/stacks/' + str(stack_id)
        url = cbparams.cb_https_url + path
        stack = requests.get(url, headers=headers,
                             verify=cbparams.ssl_verify).json()

        with open("cluster_template.json") as cl_file:
            cluster = json.load(cl_file)
        with open("blueprints/hostgroups.azure.json") as hgs_file:
            hg_info = json.load(hgs_file)
        cluster["name"] = stack["name"]
        cluster["blueprintId"] = blueprint["id"]

        hgs = [item["name"]
               for item in blueprint["ambariBlueprint"]["host_groups"]]
        for hg in hgs:
            hostgroup = {}
            hostgroup["name"] = hg
            hostgroup["constraint"] = {}
            hostgroup["constraint"]["instanceGroupName"] = hg
            hostgroup["constraint"]["hostCount"] = 1
            hostgroup["recipeIds"] = self.get_recipe_ids(hg_info[hg]["recipes"])
            cluster["hostGroups"].append(hostgroup)

        url = url + '/cluster'
        response = requests.post(url, data=json.dumps(
            cluster), headers=headers, verify=cbparams.ssl_verify)

        return response.json()

    def get_recipe_ids(self, recipe_names):
        recipe_ids = []
        for recipe in recipe_names:
            rid = self.check_for_recipe(recipe)
            recipe_ids.append(rid)
        return recipe_ids

    def get_credential(self):
        if cbparams.credential_name:
            headers = {"Authorization": "Bearer " +
                       self.access_token, "Content-type": "application/json"}
            path = '/cb/api/v1/credentials/account/' + cbparams.credential_name
            url = cbparams.cb_https_url + path
            response = requests.get(url, headers=headers, verify = cbparams.ssl_verify)
            return response.json()
        else:
            print "Missing credential name. Please provide correct value for credential_name in cbparams.py"
            return False

    def wait_for_cluster(self, name):
        """
        Creates Cloudbreak cluster with given blueprint name and waits for it to be up
        """

        credential = self.get_credential()
        blueprint, stack_id = self.create_stack(name, credential)
        cluster = self.create_cluster(blueprint, stack_id)

        print str.format("Cluster {} requested. Waiting for Ambari...", cluster["name"])

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/stacks/' + str(stack_id) + '/cluster'
        url = cbparams.cb_https_url + path

        max_execution_time = 3600
        start = timer = int(time.time())
        timeout = start + max_execution_time
        interval = 30
        retries_count = 0
        max_retries = 10

        while timer < timeout:
            response = requests.get(
                url, headers=headers, verify=cbparams.ssl_verify)
            if response.status_code != 200:
                # ignore cluster not found response for the first 20 minutes -
                # give the cluster time to allocate resources
                if response.status_code == 404 and (timer - start < 1200):
                    time.sleep(interval)
                    timer = int(time.time())
                    continue
                if retries_count < max_retries:
                    retries_count += 1
                    time.sleep(interval)
                    timer = int(time.time())
                else:
                    print str.format("FAILURE: Unable to obtain status for cluster {}. Connection to "
                                     + "Cloudbreak might be lost or infrastructure creation might have failed.",
                                     cluster["name"])
                    return False
            else:
                if response.json() and response.json().get("status"):
                    if response.json()["status"] == "AVAILABLE":
                        print str.format("SUCCESS: Cluster {} was deployed in {} seconds.",
                                         response.json()["name"], (timer - start))
                        return True
                    if response.json()["status"].endswith("FAILED"):
                        print str.format("FAILURE: Cluster deployment {} failed: {}: {}", response.json()["name"],
                                         response.json()["status"], response.json()["statusReason"])
                        return False
                # reset retries_count after success
                if retries_count != 0:
                    retries_count = 0
                time.sleep(interval)
                timer = int(time.time())

        print str.format("FAILURE: Cluster {} failed to complete in {} seconds.",
                         cluster["name"], (max_execution_time))
        return False
