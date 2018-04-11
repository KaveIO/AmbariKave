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

# ===============================================
# Cloudbreak details
# ===============================================

cb_http_url = "http://<cloudbreak pub. IP>"
cb_https_url = "https://<cloudbreak pub. IP>"
uaa_port = 8089

# ===============================================
# Deployment specific configurations
# ===============================================

credential_name = "<cloudbreak credential name>"
ssh_private_key = ""
network_name = "default-azure-network"
ssl_verify = False

# ===============================================
# Cloud provider specific configurations
# ===============================================

cloud_platform = "AZURE"

# -----------------------------------------------
# Azure
# -----------------------------------------------
region = "North Europe"
adls_enabled = False
adls_name = "<Azure Data Lake Store name>"
