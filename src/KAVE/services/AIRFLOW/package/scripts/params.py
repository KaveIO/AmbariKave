##############################################################################
#
# Copyright 2016 KPMG Advisory N.V. (unless otherwise stated)
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
from resource_management import *
from resource_management.core.system import System
import os
import string
import kavecommon as kc

config = Script.get_config()

hostname = config["hostname"]

airflow_home = kc.default('configurations/airflow/airflow_home', '/root/airflow', kc.is_valid_directory)

airflow_dags_folder = default('configurations/airflow/airflow_dags_folder', '/root/airflow')

airflow_base_log_folder = default('configurations/airflow/airflow_base_log_folder', '/root/airflow/logs')

airflow_executor = default('configurations/airflow/airflow_executor', 'SequentialExecutor')

airflow_sql_alchemy_conn = default('configurations/airflow/airflow_sql_alchemy_conn',
                                   'sqlite:////root/airflow/airflow.db')

airflow_sql_alchemy_pool_size = default('configurations/airflow/airflow_sql_alchemy_pool_size', '5')

sql_alchemy_pool_recycle = default('configurations/airflow/sql_alchemy_pool_recycle', '3600')

airflow_parallelism = default('configurations/airflow/airflow_parallelism', '32')

airflow_dag_concurrency = default('configurations/airflow/airflow_dag_concurrency', '16')

airflow_dags_are_paused_at_creation = default('configurations/airflow/airflow_dags_are_paused_at_creation', 'True')

airflow_non_pooled_task_slot_count = default('configurations/airflow/airflow_non_pooled_task_slot_count', '128')

airflow_max_active_runs_per_dag = default('configurations/airflow/airflow_max_active_runs_per_dag', '16')

airflow_load_examples = default('configurations/airflow/airflow_load_examples', 'True')

airflow_plugins_folder = default('configurations/airflow/airflow_plugins_folder', '/root/airflow/plugins')

airflow_fernet_key = default('configurations/airflow/airflow_fernet_key',
                             '2IT-D1Z4DV7P_uirajSKwixBUepSYB8mwZycWQDeMdI=')

airflow_donot_pickle = default('configurations/airflow/airflow_donot_pickle', 'False')

airflow_dagbag_import_timeout = default('configurations/airflow/airflow_dagbag_import_timeout', '30')

airflow_default_owner = default('configurations/airflow/airflow_default_owner', 'Airflow')

airflow_base_url = default('configurations/airflow/airflow_base_url', 'http://localhost:8082')

airflow_web_server_port = default('configurations/airflow/airflow_web_server_port', '8082')

airflow_web_server_worker_timeout = default('configurations/airflow/airflow_web_server_worker_timeout', '120')

airflow_secret_key = default('configurations/airflow/airflow_secret_key', 'temporary_key')

airflow_workers = default('configurations/airflow/airflow_workers', '4')

airflow_worker_class = default('configurations/airflow/airflow_worker_class', 'sync')

airflow_authenticate = default('configurations/airflow/airflow_authenticate', 'False')

airflow_expose_config = default('configurations/airflow/airflow_expose_config', 'True')

airflow_filter_by_owner = default('configurations/airflow/airflow_filter_by_owner', 'False')

airflow_job_heartbeat_sec = default('configurations/airflow/airflow_job_heartbeat_sec', '5')

airflow_scheduler_heartbeat_sec = default('configurations/airflow/airflow_scheduler_heartbeat_sec', '5')

airflow_max_threads = default('configurations/airflow/airflow_max_threads', '2')

AMBARI_ADMIN = config['configurations']['airflow']['admin']
AMBARI_ADMIN_PASS = config['configurations']['airflow']['admin']
www_folder = kc.default('configurations/airflow/www_folder', '/var/www/html/', kc.is_valid_directory)
AMBARI_SERVER = default("/clusterHostInfo/ambari_server_host", ['ambari'])[0]
# default('configurations/kavelanding/AMBARI_SERVER','ambari')

PORT = kc.default('configurations/airflow/PORT', '82', kc.is_valid_port)

template_000_default = default('configurations/apache/template_000_default', """# Created automatically with Ambari
# All manual changes will be undone in the case of a server restart
# Edit the template through the Ambari interface instead
TraceEnable Off
RequestHeader unset Proxy early
ServerSignature Off
ServerTokens Prod
Options -Multiviews
Listen {{PORT}}
ServerName "{{servername}}"
DocumentRoot "{{www_folder}}"
""")

AMBARI_SHORT_HOST = AMBARI_SERVER.split('.')[0]
servername = kc.default('configurations/airflow/servername', hostname, kc.is_valid_hostname)
if servername == "default":
    servername = hostname

airflow_conf = default('configurations/airflow/airflow_config_path', """
[core]
# The home folder for airflow, default is ~/airflow
# default: /root/airflow
airflow_home = {{airflow_home}}

# The folder where your airflow pipelines live, most likely a
# subfolder in a code repository
# default: /root/airflow/dags
dags_folder = {{airflow_dags_folder}}

# The folder where airflow should store its log files. This location
# default: /root/airflow/logs
base_log_folder = {{airflow_base_log_folder}}

# Airflow can store logs remotely in AWS S3 or Google Cloud Storage. Users
# must supply a remote location URL (starting with either 's3://...' or
# 'gs://...') and an Airflow connection id that provides access to the storage
# location.
remote_base_log_folder =
remote_log_conn_id =
# Use server-side encryption for logs stored in S3
encrypt_s3_logs = False
# deprecated option for remote log storage, use remote_base_log_folder instead!
# s3_log_folder =

# The executor class that airflow should use. Choices include
# SequentialExecutor, LocalExecutor, CeleryExecutor
# default: SequentialExecutor
executor = {{airflow_executor}}


# The SqlAlchemy connection string to the metadata database.
# SqlAlchemy supports many different database engine, more information
# their website
# default: sqlite:////root/airflow/airflow.db
sql_alchemy_conn = {{airflow_sql_alchemy_conn}}

# The SqlAlchemy pool size is the maximum number of database connections
# in the pool.
# default: 5
sql_alchemy_pool_size = {{airflow_sql_alchemy_pool_size}}

# The SqlAlchemy pool recycle is the number of seconds a connection
# can be idle in the pool before it is invalidated. This config does
# not apply to sqlite.
# default: 3600
sql_alchemy_pool_recycle = {{airflow_sql_alchemy_pool_recycle}}

# The amount of parallelism as a setting to the executor. This defines
# the max number of task instances that should run simultaneously
# on this airflow installation
# default: 32
parallelism = {{airflow_parallelism}}

# The number of task instances allowed to run concurrently by the scheduler
# default: 16
dag_concurrency = {{airflow_dag_concurrency}}

# Are DAGs paused by default at creation
# default: True
dags_are_paused_at_creation = {{airflow_dags_are_paused_at_creation}}

# When not using pools, tasks are run in the "default pool",
# whose size is guided by this config element
# default: 128
non_pooled_task_slot_count = {{airflow_non_pooled_task_slot_count}}

# The maximum number of active DAG runs per DAG
# default: 16
max_active_runs_per_dag = {{airflow_max_active_runs_per_dag}}

# Whether to load the examples that ship with Airflow. It's good to
# get started, but you probably want to set this to False in a production
# environment
# default: True
load_examples = {{airflow_load_examples}}

# Where your Airflow plugins are stored
# default: /root/airflow/plugins
plugins_folder = {{airflow_plugins_folder}}

# Secret key to save connection passwords in the db
# default: 2IT-D1Z4DV7P_uirajSKwixBUepSYB8mwZycWQDeMdI=
fernet_key = {{airflow_fernet_key}}

# Whether to disable pickling dags
# default: False
donot_pickle = {{airflow_donot_pickle}}

# How long before timing out a python file import while filling the DagBag
# default: 30
dagbag_import_timeout = {{airflow_dagbag_import_timeout}}


[operators]
# The default owner assigned to each new operator, unless
# provided explicitly or passed via `default_args`
# default: Airflow
default_owner = {{airflow_default_owner}}


[webserver]
# The base url of your website as airflow cannot guess what domain or
# cname you are using. This is used in automated emails that
# airflow sends to point links to the right web server
# default: http://localhost:8080
base_url = {{airflow_base_url}}

# The ip specified when starting the web server
# default:
web_server_host = 0.0.0.0

# The port on which to run the web server
# default: 8080
web_server_port = {{airflow_web_server_port}}

# The time the gunicorn webserver waits before timing out on a worker
# default: 120
web_server_worker_timeout = {{airflow_web_server_worker_timeout}}

# Secret key used to run your flask app
# default: temporary_key
secret_key = {{airflow_secret_key}}

# Number of workers to run the Gunicorn web server
# default: 4
workers = {{airflow_workers}}

# The worker class gunicorn should use. Choices include
# sync (default), eventlet, gevent
# default: sync
worker_class = {{airflow_worker_class}}

# Expose the configuration file in the web server
# default: true
expose_config = {{airflow_expose_config}}

# Set to true to turn on authentication:
# http://pythonhosted.org/airflow/installation.html#web-authentication
# default: False
authenticate = {{airflow_authenticate}}

# Filter the list of dags by owner name (requires authentication to be enabled)
# default: False
filter_by_owner = {{airflow_filter_by_owner}}

[email]
email_backend = airflow.utils.email.send_email_smtp

[smtp]
# If you want airflow to send emails on retries, failure, and you want to use
# the airflow.utils.email.send_email_smtp function, you have to configure an smtp
# server here
smtp_host = localhost
smtp_starttls = True
smtp_ssl = False
smtp_user = airflow
smtp_port = 25
smtp_password = airflow
smtp_mail_from = airflow@airflow.com

[celery]
# This section only applies if you are using the CeleryExecutor in
# [core] section above

# The app name that will be used by celery
celery_app_name = airflow.executors.celery_executor

# The concurrency that will be used when starting workers with the
# "airflow worker" command. This defines the number of task instances that
# a worker will take, so size up your workers based on the resources on
# your worker box and the nature of your tasks
celeryd_concurrency = 16

# When you start an airflow worker, airflow starts a tiny web server
# subprocess to serve the workers local log files to the airflow main
# web server, who then builds pages and sends them to users. This defines
# the port on which the logs are served. It needs to be unused, and open
# visible from the main web server to connect into the workers.
worker_log_server_port = 8793

# The Celery broker URL. Celery supports RabbitMQ, Redis and experimentally
# a sqlalchemy database. Refer to the Celery documentation for more
# information.
broker_url = sqla+mysql://airflow:airflow@localhost:3306/airflow

# Another key Celery setting
celery_result_backend = db+mysql://airflow:airflow@localhost:3306/airflow

# Celery Flower is a sweet UI for Celery. Airflow has a shortcut to start
# it `airflow flower`. This defines the port that Celery Flower runs on
flower_port = 5555

# Default queue that tasks get assigned to and that worker listen on.
default_queue = default

[scheduler]
# Task instances listen for external kill signal (when you clear tasks
# from the CLI or the UI), this defines the frequency at which they should
# listen (in seconds).
# default: 5
job_heartbeat_sec = {{airflow_job_heartbeat_sec}}

# The scheduler constantly tries to trigger new tasks (look at the
# scheduler section in the docs for more information). This defines
# how often the scheduler should run (in seconds).
# default: 5
scheduler_heartbeat_sec = {{airflow_scheduler_heartbeat_sec}}

# Statsd (https://github.com/etsy/statsd) integration settings
# statsd_on =  False
# statsd_host =  localhost
# statsd_port =  8125
# statsd_prefix = airflow

# The scheduler can run multiple threads in parallel to schedule dags.
# This defines how many threads will run. However airflow will never
# use more threads than the amount of cpu cores available.
# default: 2
max_threads = {{airflow_max_threads}}

[mesos]
# Mesos master address which MesosExecutor will connect to.
master = localhost:5050

# The framework name which Airflow scheduler will register itself as on mesos
framework_name = Airflow

# Number of cpu cores required for running one task instance using
# 'airflow run <dag_id> <task_id> <execution_date> --local -p <pickle_id>'
# command on a mesos slave
task_cpu = 1

# Memory in MB required for running one task instance using
# 'airflow run <dag_id> <task_id> <execution_date> --local -p <pickle_id>'
# command on a mesos slave
task_memory = 256

# Enable framework checkpointing for mesos
# See http://mesos.apache.org/documentation/latest/slave-recovery/
checkpoint = False

# Failover timeout in milliseconds.
# When checkpointing is enabled and this option is set, Mesos waits
# until the configured timeout for
# the MesosExecutor framework to re-register after a failover. Mesos
# shuts down running tasks if the
# MesosExecutor framework fails to re-register within this timeframe.
# failover_timeout = 604800

# Enable framework authentication for mesos
# See http://mesos.apache.org/documentation/latest/configuration/
authenticate = False

# Mesos credentials, if authentication is enabled
# default_principal = admin
# default_secret = admin
 """)
