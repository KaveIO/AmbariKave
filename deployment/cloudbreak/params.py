kave_version="33-beta"
cb_http_url="http://40.83.253.211"
cb_https_url="https://40.83.253.211"
uaa_port=8089
cb_username="admin@example.com"
cb_password="KavePassword01"
ssl_verify=False
recipes = {
  "patchambari":
    {
      "recipeType": "PRE",
      "description": "Add the KAVE Stack to ambari",
      "templatePath" : "recipes/setup_cloudbreak_kavepatch_ambari.sh"
    },
  "fix-hosts-file": 
    {
      "recipeType": "PRE",
      "description": "Fix hosts file on all nodes",
      "templatePath" : "recipes/setup_cloudbreak_fixhostsfile_all.sh"
    },
  "distibute-private-key":
    {
      "recipeType": "PRE",
      "description": "Distribute private key on all nodes",
      "templatePath" : "recipes/setup_cloudbreak_keydistrib_all.sh"
    },
  "limit-ssh-attempts":
    {
      "recipeType": "PRE",
      "description": "Limit unsuccessful ssh attempts rate",
      "templatePath" : "recipes/limit-ssh-attempts.sh"
    }}
