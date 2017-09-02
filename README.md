# Cloudera Playbook 

An Ansible Playbook that installs the Cloudera stack on RHEL/CentOS. There are various customization options available such as below

Install Cloudera Manager with 

    Metadata Database as Postgresql,Mariadb(with or without replication)

    Create custom cloudera manager repository

    Install specific version of Java or Default Java


see the section user variables.

# Running the playbook

* Setup an [Ansible Control Machine](http://docs.ansible.com/ansible/intro_installation.html) 
* Create Ansible configuration (optional):

```ini
$ vi ~/.ansible.cfg

[defaults]
# disable key check if host is not initially in 'known_hosts'
host_key_checking = False

[ssh_connection]
# if True, make ansible use scp if the connection type is ssh (default is sftp)
scp_if_ssh = True
```

* Create [Inventory](http://docs.ansible.com/ansible/intro_inventory.html) of cluster hosts:

```ini
$ vi ~/ansible_hosts

[scm_server]
<host>        license_file=/path/to/cloudera_license.txt

[db_server]
<host>

[krb5_server]
<host>        default_realm=<REALM>

[utility_servers:children]
scm_server
db_server
krb5_server

[gateway_servers]
<host>        host_template=HostTemplate-Gateway role_ref_names=HDFS-HTTPFS-1

[master_servers]
<host>        host_template=HostTemplate-Master1
<host>        host_template=HostTemplate-Master2
<host>        host_template=HostTemplate-Master3

[worker_servers]
<host>
<host>
<host>

[worker_servers:vars]
host_template=HostTemplate-Workers

[cdh_servers:children]
utility_servers
gateway_servers
master_servers
worker_servers
```
    
* Run playbook
 
```shell
$ ansible-playbook -i ~/ansible_hosts cloudera-playbook/site.yml
    
-i INVENTORY
   inventory host path or comma separated host list (default=/etc/ansible/hosts)
```

Ansible communicates with the hosts defined in the inventory over SSH. It assumes you’re using SSH keys to authenticate so your public SSH key should exist in ``authorized_keys`` on those hosts. Your user will need sudo privileges to install the required packages.

By default Ansible will connect to the remote hosts using the current user (as SSH would). To override the remote user name you can specify the ``--user`` option in the command, or add the following variables to the inventory:

```ini
[all:vars]
ansible_user=ec2-user
```

AWS users can use Ansible’s ``--private-key`` option to authenticate using a PEM file instead of SSH keys.

# User Variables

Playbook can be customize according to user needs.

one has to change below file for Customization.

1. To Install CM & CDH with Postgresql as metadata DB.

    ```
    database_type: postgresql
    ```
2. To Enable Replication(Only for MariaDB as time of writing)

    ```
    database_type: mysql
    mysql_replication: true
    ```
3. To Install Custom Java Version (Copy Oracle JDK version link from             http://www.oracle.com/technetwork/java/javase/downloads/java-archive-javase8-2177648.html)

    ```
    external_java: true
    # Always use otn-pub link instead of otn link as otn link required login
    jdk_dwonload_link: "http://download.oracle.com/otn-pub/java/jdk/8u141-b15/336fa29ff2bb4ef291e347e091f7f4a7/jdk-8u141-linux-x64.rpm"
    ```

4. To Create Local Cloudera Manager Repository

    ```
    local_repo: true
    ```


#Running Playbook overriding variables (Examples)

```
ansible-playbook -i cm_hosts site.yml -e "{'local_repo': 'true', 'database_type': 'postgresql'}"

ansible-playbook -i cm_test_hosts site.yml -e "{'local_repo': 'false', 'database_type': 'mysql', 'mysql_replication' : 'true'}"

ansible-playbook -i cm_test_hosts site.yml -e "{'local_repo': 'false', 'database_type': 'mysql', 'mysql_replication' : 'true','krb5_kdc_type': 'none' }"

```



```
---
# ---------------------------- cm repo related variables ------------------
local_repo: false
baseurl: "http://archive.cloudera.com/cm5/redhat/{{ ansible_distribution_major_version }}/x86_64/cm/5/"
cm_dwonload_link: "https://archive.cloudera.com/cm5/redhat/7/x86_64/cm/5/RPMS/x86_64/"


# --------------------------- Metadata DB variables -----------------------
# Type of the Database postgresql,mysql (used in scm_prepare_database script and metadata_db->main.yml)
database_type: mysql
# Possible values true, false
mysql_replication: false
mysql_root_password: changeme
mysql_replication_user: repl
mysql_replication_password: changeme

# PostgreSQl related configuration Parameters
# For more info visit https://www.cloudera.com/documentation/enterprise/5-5-x/topics/cm_ig_extrnl_pstgrs.html
# For large cluster , more than 50 Nodes shared_buffers_mb: 1024MB
shared_buffers_mb: 256MB
# For large cluster , more than 50 Nodes wal_buffers_mb: 16MB
wal_buffers_mb: 8MB
# For large cluster , more than 50 Nodes checkpoint_segments: 128
checkpoint_segments: 32
checkpoint_completion_target: 0.9

# ------------------------- Java Related variables -------------------------
#Install external Java if no internet connection or you want to use custom java
external_java: true
# Always use otn-pub link instead of otn link as otn link required login
jdk_dwonload_link: "http://download.oracle.com/otn-pub/java/jdk/8u141-b15/336fa29ff2bb4ef291e347e091f7f4a7/jdk-8u141-linux-x64.rpm"


# ------------------------ scm related variables ---------------------------

scm_repositories:
  - http://archive.cloudera.com/cdh5/parcels/5.8.3/
  - https://archive.cloudera.com/cdh5/parcels/{latest_supported}/

scm_products:
  - product: CDH
    version: 5.8.3-1.cdh5.8.3.p0.2

```

# Enabling Kerberos

The playbook can install a local MIT KDC and configure Hadoop Security. To enable Hadoop Security:

* Specify the '[krb5_server]' host in the inventory (see above)
* Set 'krb5_kdc_type' to 'mit' in ``group_vars/krb5_server``

# Overriding CDH service/role configuration

The playbook uses [Cloudera Manager Templates](https://www.cloudera.com/documentation/enterprise/latest/topics/install_cluster_template.html) to provision a cluster.
As part of the template import process Cloudera Manager applies [Autoconfiguration](https://www.cloudera.com/documentation/enterprise/latest/topics/cm_mc_autoconfig.html)
rules that set properties such as memory and CPU allocations for various roles.

If the cluster has different hardware or operational requirements then you can override these properties in ``group_vars/cdh_servers``. 
For example:

```
cdh_services:
  - type: hdfs        
    datanode_java_heapsize: 10737418240
```

These properties get added as variables to the rendered template's instantiator block and can be referenced from the service configs.
For example ``roles/cdh/templates/hdfs.j2``:

```json
"roleType": "DATANODE",
"configs": [{
  "name": "datanode_java_heapsize",
  "variable": "DATANODE_JAVA_HEAPSIZE"
}
```

# How to contribute

* Fork the repo and create a topic branch
* Push commits to your repo
* Create a pull request!
