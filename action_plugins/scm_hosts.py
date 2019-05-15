#!/usr/bin/env python

# (c) Copyright 2016 Cloudera, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ansible.plugins.action import ActionBase
from cm_api.api_client import ApiException
from cm_api.api_client import ApiResource

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display

    display = Display()


class ActionModule(ActionBase):
    """ Returns map of inventory hosts and their associated SCM hostIds """

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        host_ids = {}
        host_names = {}

        # Get SCM host details from inventory
        try:
            scm_host = task_vars["groups"]["scm_server"][0]
            scm_port = task_vars["hostvars"][scm_host]["scm_port"]
            scm_user = task_vars["hostvars"][scm_host]["scm_default_user"]
            scm_pass = task_vars["hostvars"][scm_host]["scm_default_pass"]
        except KeyError as e:
            result['failed'] = True
            result['msg'] = e.message
            return result

        api = self.get_api_handle(scm_host, scm_port, scm_user, scm_pass)
        scm_host_list = api.get_all_hosts()
        display.vv("Retrieved %d host(s) from SCM" % len(scm_host_list))
        for scm_host in scm_host_list:
            display.vv("Retrieved host: name='%s',id='%s'" % (scm_host.hostname, scm_host.hostId) )
            
        if len(scm_host_list) == 0:
            result['failed'] = True
            result['msg'] = "No hosts defined in SCM"
            return result

        for inv_host in task_vars["hostvars"]:
            host = str(inv_host)
            found_host = False
            for scm_host in scm_host_list:
                try:
                    if scm_host.hostname == task_vars["hostvars"][host]["inventory_hostname"]:
                        found_host = True
                    elif scm_host.ipAddress == task_vars["hostvars"][host]["inventory_hostname"]:
                        found_host = True
                    elif scm_host.hostname == task_vars["hostvars"][host]["ansible_hostname"]:
                        found_host = True      
                    elif scm_host.hostname == task_vars["hostvars"][host]["ansible_fqdn"]:
                        found_host = True                                            
                    elif "private_ip" in task_vars["hostvars"][host]:
                        if scm_host.ipAddress == task_vars["hostvars"][host]["private_ip"]:
                            found_host = True

                    if found_host:
                        host_ids[host] = scm_host.hostId
                        host_names[host] = scm_host.hostname
                        display.vv("Inventory host '%s', SCM hostId: '%s', SCM hostname: '%s'"
                                   % (host, scm_host.hostId, scm_host.hostname))
                        break
                except KeyError as e:
                    display.vv("Key '%s' not defined for inventory host '%s'" % (e.message, host))
                    continue

            if not found_host:
                display.vv("Unable to determine SCM host details for inventory host '%s'" % host)
                continue

        display.vv("host_ids: %s" % host_ids)
        display.vv("host_names: %s" % host_names)
        result['changed'] = True
        result['host_ids'] = host_ids
        result['host_names'] = host_names
        return result

    @staticmethod
    def get_api_handle(host, port='7180', user='admin', passwd='admin', tls=False):
        """
        Get a handle to the CM API client
        :param host: Hostname of the Cloudera Manager Server (CMS)
        :param port: Port of the server
        :param user: SCM username
        :param passwd: SCM password
        :param tls: Whether to use TLS
        :return: Resource object referring to the root
        """
        api = None
        try:
            api = ApiResource(host, port, user, passwd, tls)
        except ApiException:
            pass
        return api
