# Cloudera Playbook 

An Ansible Playbook that installs the Cloudera stack on RHEL/CentOS

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
host1.example.com        license_file=/path/to/cloudera_license.txt

[db_server]
host2.example.com

[krb5_server]
host3.example.com        default_realm=<REALM>

[utility_servers:children]
scm_server
db_server
krb5_server

[gateway_servers]
host4.example.com        host_template=HostTemplate-Gateway role_ref_names=HDFS-HTTPFS-1

[master_servers]
host5.example.com        host_template=HostTemplate-Master1
host6.example.com        host_template=HostTemplate-Master2
host7.example.com        host_template=HostTemplate-Master3

[worker_servers]
host8.example.com
host9.example.com
host10.example.com

[worker_servers:vars]
host_template=HostTemplate-Workers

[cdh_servers:children]
utility_servers
gateway_servers
master_servers
worker_servers
```

**Important**: fully qualified domain name (FQDN) is mandatory in the ansible_hosts file
   
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

# Enabling Kerberos

The playbook can install a local MIT KDC and configure Hadoop Security. To enable Hadoop Security:

* Specify the '[krb5_server]' host in the inventory (see above)
* Set 'krb5_kdc_type' to 'mit' in ``group_vars/krb5_server.yml``

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

# Dynamic inventory script for Cloudera Manager

Cloudera Manager specific dynamic inventory script has been created for easy integration. These are the main advantages:

* Cache management for better performance
* HTTP cookie handling
* Multi Cloudera Manager support
* SSL friendly because you can disable or enable the root CA check

**Configuration**

```
export CM_URL=https://cm_host_fqdn1:7183,https://cm_host_fqdn2:7183
export CM_USERNAME=username
```

**Install sssd**
```
yum install ansible -y
```

**Set up default ansible inventory**
```
sudo mkdir /etc/ansible
cd /etc/ansible
sudo ln -s /path/to/dynamic_inventory_cm hosts
```

**Set up SSH public key authentication for remote host(s)**

If you do not have ~/.ssh/id_rsa.pub and ~/.ssh/id_rsa files then you need to generate them with the ssh-keygen command before this:
```
ANSIBLE_HOST_KEY_CHECKING=False ansible all -m authorized_key -a key="{{ lookup('file', '~/.ssh/id_rsa.pub') }} user=$USER" -k
```

If only the root user exists then please use this instead:
```
ANSIBLE_HOST_KEY_CHECKING=False ansible all -m authorized_key -a key="{{ lookup('file', '~/.ssh/id_rsa.pub') }} user=root" -k -u root
```

Test remote host connectivity(optional)
```
ansible all -m ping
```

If only the root user exists then please use this instead:
```
ansible all -m ping -u root
```

**Other optional configuration parameters**

```
export CM_CACHE_TIME_SEC=3600
export CM_DISABLE_CA_CHECK=True
export CM_TIMEOUT_SEC=60
export CM_DEBUG=False
```

You can list the available Cloudera Manager clusters (Ansible groups) with this command:

```
dynamic_inventory_cm --list
```

**Example Ansible Ad-Hoc commands**

With the ad-hoc command feature you can run the same Linux command on all hosts. For example if you debug an issue, this can help. Example Ansible Ad-Hoc commands:

```
ansible Balaton -m command -o -a "id -Gn yarn"
ansible all -m command -o -a "date"
```

Documentation of Ansible Ad-Hoc commands:

http://docs.ansible.com/ansible/latest/intro_adhoc.html

# SSSD setup with Ansible (works on RHEL7/CentOS7 only)

**Edit default variables in ./group_vars/all** 

```
vim ./group_vars/all (this is an example configuration)
```

```
krb5_realm: AD.SEC.CLOUDERA.COM
ad_domain: "{{ krb5_realm.lower() }}"
computer_ou: ou=Hosts,ou=morhidi,ou=HadoopClusters,ou=morhidi,dc=ad,dc=sec,dc=cloudera,dc=com
domain: vpc.cloudera.com
kdc: w2k8-1.ad.sec.cloudera.com
```
**Enable kerberos on the hosts**
```
ansible-playbook -u root enable_kerberos.yaml
```
**Join the host(s) to realm**
```
ansible-playbook -u root realm_join.yaml
bind user: administrator
bind password:
```

**Remove the host(s) from realm**
```
ansible-playbook -u root realm_leave.yaml
```

# How do I contribute code?
You need to first sign and return an
[ICLA](https://github.com/cloudera/cloudera-playbook/blob/master/icla/Cloudera_ICLA_25APR2018.pdf)
and
[CCLA](https://github.com/cloudera/cloudera-playbook/blob/master/icla/Cloudera_CCLA_25APR2018.pdf)
before we can accept and redistribute your contribution. Once these are submitted you are
free to start contributing to cloudera-playbook. Submit these to CLA@cloudera.com.

# Main steps
* Fork the repo and create a topic branch
* Push commits to your repo
* Create a pull request!

## Find
We use Github issues to track bugs for this project. Find an issue that you would like to
work on (or file one if you have discovered a new issue!). If no-one is working on it,
assign it to yourself only if you intend to work on it shortly.

## Fix

Please write a good, clear commit message, with a short, descriptive title and
a message that is exactly long enough to explain what the problem was, and how it was
fixed.

License
-----------
[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)
