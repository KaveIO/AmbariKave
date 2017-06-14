Azure account support: Bart van der Kolk
Azure test user: kave-test@kpmgnl.onmicrosoft.com/Ka..01
Azure Resource Group: KoA_Cloudbreak - DO NOT DELETE!

Deploy Cloudbreak on Azure, https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fsequenceiq%2Fazure-cbd-quickstart%2F1.6.3%2Fazuredeploy.json

Install the Azure CLI:
-yum check-update ; yum install -y gcc libffi-devel python-devel openssl-devel
-curl -L https://aka.ms/InstallAzureCli | bash

Check that the deployment is ok:
-ssh cloudbreak@40.83.253.211 (pass Ka...01)
-sudo su
-cd /var/lib/cloudbreak-deployment; ANY cbd COMMAND MUST BE RUN FROM HERE !
-grep "export PUBLIC_IP=" Profile ---> export PUBLIC_IP=40.83.253.211
-cbd doctor
-cbd logs cloudbreak | grep "Started CloudbreakApplication in" ---> Application - [owner:spring] [type:springLog] [id:] [name:] Started CloudbreakApplic...

new command:
az login
az account set -s "b2c7cebc-..." #choose the right subscription!
az ad sp create-for-rbac --name cloudbreak-app-an --password Kav..01 --role Owner

old command:
cbd azure configure-arm --app_name koacbd --app_password Ka...01 --subscription_id a31a9a22-ae1c-4dea-8086-... --username kave-test@kpmgnl.onmicrosoft.com --password Ka...01

new output:
{
  "appId": "23d8acb2-29b6-44fe-bf46-38f774248063",
  "displayName": "cloudbreak-app-an",
  "name": "http://cloudbreak-app-an",
  "password": "KavePassword01",
  "tenant": "d8e9043f-c360-49f3-bfcf-0d12d1ba54a9"
}

old output:
Subscription ID: a31a9a22-ae1c-4dea-8086-...
App ID: d26ad9c1-255c-42d7-9fe2-51ab5efdd40d
Password: Ka...01
App Owner Tenant ID: d8e9043f-c360-49f3-bfcf-0d12d1ba54a9
This is what you fill in to create a CBD credential.

generate a new ssh key: ssh-keygen -t rsa -b 4096 -C "kave@kpmg.com"

login into https://40.83.253.211/sl/

To get a shell on one of the microservice dockers, $docker exec -i -t cbreak_sultans_1 /bin/bash

Because of https://github.com/sequenceiq/cloudbreak/issues/1492 you will not be able to register. Just use the credentials shown in the Profile file.

Modify the default credentials for example, have a look here https://github.com/sequenceiq/cloudbreak-deployer/issues/35. So basically add the default user and pass to the profile then give:
cbd kill
cbd delete
cbd generate
cbd start

Now you can create setups & clusters!

You may use the KAVE blueprint collection directly without any modification but:
-the stack property is ignored, actually Cloudbreak only works with regular HDP-X.Y stacks
-for the point above, we need to patch KAVE beforehand, see the recipe script
-in future releases of KAVE and Cloudbreak, make the right stack version is picked
So the strategy is to silently patch the regular 2.5 stack with the KAVE services.

The automated cluster provisioning on the FreeIPA blueprint goes through, but a few services fail, ipa too of course. Next step: test every blueprint and close in on possible issues. Notice: Cloudbreak can take care of the kerberization of the cluster, so perhaps we can drop FreeIPA once and for good, so it might be ok to test the blueprints removing the FreeIPA service.

Once the cluster is deployed, you will be able to login with something like:
ssh -i id_rsa_kave -L 8080:akz-a0:8080 cloudbreak@52.178.46.15

Now that is the private key we used to bootstrap, and we put it in clear text in the recipe, which is a bad thing. To be safe, add some machinery to replace this:
-create a new id_dsa key (we call it dsa just temporarily not to get locked out)
-copy it to every node: pdcp -w node1,...,noden ~/.ssh/id_dsa ~/.ssh
-create a new authorized_keys: cat ~/.ssh/id_dsa > ~/.ssh/authorized_keys
-set the right permissions to this file: rw cloudbreak only
-copy it to every node: pdcp ...
-overwrite the old private key: pdsh ... mv ~/.ssh/id_dsa ~/.ssh/id_rsa

If you want to connect passless with the cloudbreak user also remotely, copy this id_rsa locally too.
