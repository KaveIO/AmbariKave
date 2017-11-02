import requests
import json
import params
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
        url = params.cb_http_url + ':' + \
            str(params.uaa_port) + '/oauth/authorize?response_type=token&client_id=cloudbreak_shell&ope.0=openid&source=login&redirect_uri=http://cloudbreak.shell'
        headers = {'Accept': 'application/x-www-form-urlencoded',
                   'Content-type': 'application/x-www-form-urlencoded'}
        data = {'credentials': '{"username": "' + params.cb_username +
                '", "password": "' + params.cb_password + '"}'}

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

        name = hostgroup + '-' + params.kave_version
        path = '/cb/api/v1/templates/account/' + name
        url = params.cb_https_url + path
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}

        response = requests.get(url, headers=headers, verify=params.ssl_verify)
        if response.status_code == 200:
            return response.json()["id"]
        else:
            print "Template with name " + name + " does not exist.\nTemplate " + name + " will be created."
            return self.create_template(hostgroup)

    def create_template(self, hostgroup):
        """
        Creates Cloudbreak template with given name
        """

        path = '/cb/api/v1/templates/user/'
        url = params.cb_https_url + path
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}

        with open('blueprints/hostgroups.azure.json') as hg_file:
            hgjson = json.load(hg_file)
        if not (hgjson and hgjson.get(hostgroup)):
            print "Description for hostgroup " + hostgroup + " is missing in blueprints/hostgroups.azure.json."
            return False

        name = hostgroup + '-' + params.kave_version
        hostgroup_info = hgjson[hostgroup]
        data = {}
        data['name'] = name
        data['cloudPlatform'] = 'AZURE'
        data['parameters'] = {}
        data['parameters']['managedDisk'] = True
        data['instanceType'] = hostgroup_info['machine-type']
        data['volumeCount'] = 1
        data['volumeSize'] = hostgroup_info['volume-size']
        data['volumeType'] = 'Standard_LRS'

        response = requests.post(url, data=json.dumps(
            data), headers=headers, verify=params.ssl_verify)
        if response.status_code == 200:
            print "Created new Cloudbreak template with name " + name
            print response.text
            return response.json()["id"]
        else:
            print "Error creating Cloudbreak template with name " + name
            print response.text
            return False

    def check_for_blueprint(self, name):
        """
        Checks if Cloudbreak blueprint with given name exists
        """

        bp_name = name + '-' + params.kave_version
        path = '/cb/api/v1/blueprints/account/' + bp_name
        url = params.cb_https_url + path
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}

        response = requests.get(url, headers=headers, verify=params.ssl_verify)
        if response.status_code == 200:
            return response.json()
        else:
            print "Blueprint with name " + bp_name + " does not exist.\nBlueprint " + bp_name + " will be created."
            return self.create_blueprint(name)

    def create_blueprint(self, name):
        """
        Creates Cloudbreak blueprint with given name
        """

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/blueprints/user'
        url = params.cb_https_url + path

        try:
            with open('blueprints/' + name + '.blueprint.json') as bp_file:
                bp = json.load(bp_file)
        except (IOError, ValueError):
            print "No correct blueprint .json file found for " + name
            return False

        data = {}
        bp_name = name + '-' + params.kave_version
        data['name'] = bp_name
        data['ambariBlueprint'] = bp

        response = requests.post(url, data=json.dumps(
            data), headers=headers, verify=params.ssl_verify)
        if response.status_code == 200:
            print "Created new Cloudbreak blueprint with name " + bp_name
            return response.json()
        else:
            print "Error creating Cloudbreak blueprint with name " + bp_name
            print response.text
            return False

    def check_for_recipe(self, name):
        """
        Checks if Cloudbreak recipe with given name exists
        """

        recipe_name = name + '-' + params.kave_version
        path = '/cb/api/v1/recipes/account/' + recipe_name
        url = params.cb_https_url + path
        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}

        response = requests.get(url, headers=headers, verify=params.ssl_verify)
        if response.status_code == 200:
            return response.json()["id"]
        else:
            print "Recipe with name " + recipe_name + " does not exist.\nRecipe " + recipe_name + " will be created."
            return self.create_recipe(name)

    def create_recipe(self, name):
        """
        Creates Cloudbreak recipe with given name
        """

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/recipes/user'
        url = params.cb_https_url + path

        details = params.recipes[name]
        data = {}
        data['name'] = name + '-' + params.kave_version
        data['recipeType'] = details['recipeType']
        data['description'] = details['description']
        with open(details["templatePath"]) as rec_file:
            rec = rec_file.read()
        if details.get("params") :
            temp = Template(rec)
            content = content.substitute(details["params"])
            data['content'] = base64.b64encode(content)
        else:
            data['content'] = base64.b64encode(rec)

        response = requests.post(url, data=json.dumps(
            data), headers=headers, verify=params.ssl_verify)
        if response.status_code == 200:
            print "Created new Cloudbreak recipe with name " + name + '-' + params.kave_version
            return response.json()["id"]
        else:
            print "Error creating Cloudbreak recipe with name " + name + '-' + params.kave_version
            print response.text
            return False

    def create_stack(self, blueprint_name):
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

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/stacks/user'
        url = params.cb_https_url + path
        response = requests.post(url, data=json.dumps(
            stack), headers=headers, verify=params.ssl_verify)
        print response.text
        return (blueprint, response.json()["id"])

    def create_cluster(self, blueprint, stack_id):
        """
        Creates Cloudbreak cluster with given blueprint name and stack id
        """

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/stacks/' + str(stack_id)
        url = params.cb_https_url + path
        stack = requests.get(url, headers=headers,
                             verify=params.ssl_verify).json()

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
            cluster), headers=headers, verify=params.ssl_verify)

        return response.json()

    def get_recipe_ids(self, recipe_names):
        recipe_ids = []
        for recipe in recipe_names:
            rid = self.check_for_recipe(recipe)
            recipe_ids.append(rid)
        return recipe_ids

    def wait_for_cluster(self, name):
        """
        Creates Cloudbreak cluster with given blueprint name and waits for it to be up
        """

        blueprint, stack_id = self.create_stack(name)
        cluster = self.create_cluster(blueprint, stack_id)

        headers = {"Authorization": "Bearer " +
                   self.access_token, "Content-type": "application/json"}
        path = '/cb/api/v1/stacks/' + str(stack_id) + '/cluster'
        url = params.cb_https_url + path

        timeout = int(time.time()) + 3600
        timer = int(time.time())
        interval = 30

        while timer < timeout:
            response = requests.get(
                url, headers=headers, verify=params.ssl_verify)
            if response.json() and response.json().get("status"):
                if response.json()["status"] == "AVAILABLE":
                    print "Cluster " + response.json()["name"] + " deployed successfully."
                    return True
                if response.json()["status"].endswith("FAILED"):
                    print "Deployment of cluster " + response.json()["name"] + " failed. Status: " + response.json()["status"]
                    return False
            else:
                time.sleep(interval)
                timer = int(time.time())

        print "Error creating cluster " + cluster["name"]
        return False

if __name__ == "__main__":
    import sys, glob
    from threading import Thread

    disabled = []

    cb = CBDeploy()
    if "--all" in sys.argv:
        blueprints = glob.glob("blueprints/*.blueprint.json")
        blueprints = [b.split("/")[-1].split(".")[0] for b in blueprints]
        blueprints = [b for b in blueprints if b not in disabled]
    else:
        blueprints = sys.argv[1:]

    for i in range(0, len(blueprints)):
        print "Start cluster deployment for blueprint " + blueprints[i]
        t = Thread(target=cb.wait_for_cluster, args=(blueprints[i],))
        t.start()
        time.sleep(20)
