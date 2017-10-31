kave_version="33-beta"
cb_http_url="http://40.83.253.211"
cb_https_url="https://40.83.253.211"
uaa_port=8089
cb_username="admin@example.com"
cb_password="KavePassword01"
ssl_verify=False
recipes = {"testrecipe": {"recipeType": "PRE",
                          "description": "test recipe from code",
                          "templatePath" : "recipes/testrecipe.sh",
                          "params" : {"text" : 'echo "hello world" > /dev/null'}},
           "testrec2": {"key1": "value1"}}
