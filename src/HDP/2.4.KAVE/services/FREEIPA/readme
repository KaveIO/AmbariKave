# The FreeIPA Service 
The FreeIPA service is the corner stone of the security in a KAVE environment. 
There are a lot of dependencies, timing and ordering constraints we've tried to 
tackle with this service. The advantage of this is that we can create a truly 
centralized single login, the drawback is that there is no flexibility in which 
authentication provider you use. 

Challenges which have been tackled in this service include: Order in which 
server and client components are installed, distribution of administrator
password for adding new machines to the cluster. 

## General Risks Involved 
We're dealing with security here so we'll try to be really clear about the 
situations we considered and how we deal with them.

    Database of ambari-server could be compromised. (Risk: low, impact: High)
    Mitigated by not storing the administrator password in the database. The 
    directory password however remains in there. The directory password is need 
    by other services to bind the logins. This user does however have less
    privileges than the administrator user. 

    Communication of configuration between ambari-server and agent could be 
    compromised. (Risk: mid, Impact: High)
    Mitigated by introducing a limited lifetime robot-admin user accounts which 
    password is distributed once and which password is destroyed after first use.

    PAM based authentication method requires user to have HBAC access on more 
    machines then strictly necessary (Risk: low, Impact: mid)
    For Twiki we rely on PAM for user authentication. This means that the users
    that can access Twiki in principle also can log in on the same machine. They 
    have a non privileged account and in principle can't do anything here. 
    However depending on the additional services installed on the same machine 
    more possible privilege escalation opportunities open.   

## Methods of integration
FreeIPA is a single solution which ties together a couple of different 
techniques. These techniques open up various ways of integration. We've tried to 
make every as uniform as possible however we have to vary every now and than. 
The methods we use are: 

    Kerberos
    LDAP 
    PAM

Kerberos integration is used for HDP security. Once enabled via ambari this 
turns it on for all Hadoop related services. 

LDAP is used for web services that can integrate well with this. There is a 
choice here to go over port 389 and 636. It is strongly recommend to use 636 
since this is encrypted where 389 is not. 

PAM is used when LDAP does not suffice for the integration. A advantage of PAM 
is that the password validation is really secure (via sssd) however a 
disadvantage is that the user need to have HBAC access to the machine.