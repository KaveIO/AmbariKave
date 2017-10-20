import requests
import json
import params
import urlparse


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
