import requests
import json
import params
import urlparse
import base64
from string import Template


def get_access_token():
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
        return token
    except Exception as e:
        print "Error getting Cloudbreak access token: ", e


def check_for_template(hostgroup):
    """
    Checks if Cloudbreak template with given name exists
    """

    name = hostgroup + '-' + params.kave_version
    path = '/cb/api/v1/templates/account/' + name
    url = params.cb_https_url + path
    token = get_access_token()
    headers = {"Authorization": "Bearer " +
               token, "Content-type": "application/json"}

    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        return True
    else:
        print "Template with name " + name + " does not exist.\nTemplate " + name + " will be created."
        if create_template(hostgroup) == True:
            return True
        else:
            return False


def create_template(hostgroup):
    """
    Creates Cloudbreak template with given name
    """

    path = '/cb/api/v1/templates/user/'
    url = params.cb_https_url + path
    token = get_access_token()
    headers = {"Authorization": "Bearer " +
               token, "Content-type": "application/json"}

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
        data), headers=headers, verify=False)
    if response.status_code == 200:
        print "Created new Cloudbreak template with name " + name
        print response.text
        return True
    else:
        print "Error creating Cloudbreak template with name " + name
        print response.text
        return False


def check_for_blueprint(name):
    """
    Checks if Cloudbreak blueprint with given name exists
    """

    bp_name = name + '-' + params.kave_version
    path = '/cb/api/v1/blueprints/account/' + bp_name
    url = params.cb_https_url + path
    token = get_access_token()
    headers = {"Authorization": "Bearer " +
               token, "Content-type": "application/json"}

    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        return True
    else:
        print "Blueprint with name " + bp_name + " does not exist.\nBlueprint " + bp_name + " will be created."
        if create_blueprint(name) == True:
            return True
        else:
            return False


def create_blueprint(name):
    """
    Creates Cloudbreak blueprint with given name
    """

    token = get_access_token()
    headers = {"Authorization": "Bearer " +
               token, "Content-type": "application/json"}
    path = '/cb/api/v1/blueprints/user'
    url = params.cb_https_url + path

    try:
        with open('blueprints/' + name + '.json') as bp_file:
            bp = json.load(bp_file)
    except (IOError, ValueError):
        print "No correct blueprint .json file found for " + name
        return False

    data = {}
    bp_name = name + '-' + params.kave_version
    data['name'] = bp_name
    data['ambariBlueprint'] = bp

    response = requests.post(url, data=json.dumps(
        data), headers=headers, verify=False)
    if response.status_code == 200:
        print "Created new Cloudbreak blueprint with name " + bp_name
        return True
    else:
        print "Error creating Cloudbreak blueprint with name " + bp_name
        print response.text
        return False


def check_for_recipe(name):
    """
    Checks if Cloudbreak recipe with given name exists
    """

    recipe_name = name + '-' + params.kave_version
    path = '/cb/api/v1/recipes/account/' + recipe_name
    url = params.cb_https_url + path
    token = get_access_token()
    headers = {"Authorization": "Bearer " +
               token, "Content-type": "application/json"}

    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        return True
    else:
        print "Recipe with name " + recipe_name + " does not exist.\nRecipe " + recipe_name + " will be created."
        if create_recipe(name) == True:
            return True
        else:
            return False


def create_recipe(name):
    """
    Creates Cloudbreak recipe with given name
    """

    token = get_access_token()
    headers = {"Authorization": "Bearer " +
               token, "Content-type": "application/json"}
    path = '/cb/api/v1/recipes/user'
    url = params.cb_https_url + path

    details = params.recipes[name]
    data = {}
    data['name'] = name + '-' + params.kave_version
    data['recipeType'] = details['recipeType']
    data['description'] = details['description']
    with open(details["templatePath"]) as rec_file:
        rec = rec_file.read()
    str = Template(rec)
    content = str.substitute(details["params"])
    data['content'] = base64.b64encode(content)

    response = requests.post(url, data=json.dumps(
        data), headers=headers, verify=False)
    if response.status_code == 200:
        print "Created new Cloudbreak recipe with name " + name + '-' + params.kave_version
        return True
    else:
        print "Error creating Cloudbreak recipe with name " + name + '-' + params.kave_version
        print response.text
        return False
