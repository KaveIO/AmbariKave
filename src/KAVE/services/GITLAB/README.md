GitLab  
======

Postgres setting
----------------

By default GitLab uses its own embedded Postgres database. Optionally it can be
used with an existing (external) Postgres server. 
There are some parameters during the installation for the external database settings.


| Parameter             | Description                           |Values                  | Required    | Default             |
|:----------------------|:-------------------------------------:|------------------------|------------:|---------------------|
|use_external_postgres  | Use external database or embedded one | Boolean (true/false)   | Yes         | false               |
|postgres_database_host | External database host                | Hostname or IP address | Conditional | 127.0.0.1           |
|postgres_database_port | External database port                | DB listening port (int)| Conditional | 5432                |
|postgres_database_name | External database name                | Database name          | Conditional | gitlabhq_production |
|postgres_database_user | External database user                | Database user          | Conditional | gitlab              |

* The installation process will try to create and initialize new database and new user for GitLab so it is impossible 
to use an existing one.
 
* The password used for the external database is the same as the administrator password set for GitLab.

* They are different types of authentication available for Postgres server and a changes may be necessary in GitLab
configuration file which is exposed through the Ambari UI.
