credential select --name rallycred
blueprint select --name ambari-purehdp
instancegroup configure --AZURE --instanceGroup admin --nodecount 1 --ambariServer true --templateName d2v2-azure --securityGroupName default-azure-only-ssh-and-ssl
network select --name default-azure-network
stack create --AZURE --name purehdp-shelltest --region "North Europe"
cluster create --ambariVersion "2.5.1.0" --ambariRepoBaseURL "http://public-repo-1.hortonworks.com/ambari/centos7/2.x/updates/2.5.1.0" --ambariRepoGpgKey "http://public-repo-1.hortonworks.com/ambari/centos7/2.x/updates/2.5.1.0/RPM-GPG-KEY/RPM-GPG-KEY-Jenkins" --stack "HDP" --version "2.6.1" --stackRepoId "HDP-2.6" --stackBaseURL "http://public-repo-1.hortonworks.com/HDP/centos7/2.x/updates/2.6.1.0" --utilsRepoId "HDP-UTILS-1.1.0.21" --utilsBaseURL "http://public-repo-1.hortonworks.com/HDP-UTILS-1.1.0.21/repos/centos7" --verify true
