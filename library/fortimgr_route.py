#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {
    "metadata_version": "1.0",
    "status": ["preview"],
    "supported_by": "community"
}

DOCUMENTATION = '''
---
module: fortimgr_route
version_added: "2.3"
short_description: Manages Route configurations for FortiGate devices
description:
  - Manages FortiGate route configurations using FortiManager's jsonrpc API
author: Jacob McGill (@jmcgill298)
options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    type: str
  host:
    description:
      - The FortiManager's Address.
    required: true
    type: str
  lock:
    description:
      - True locks the ADOM, makes necessary configuration updates, saves the config, and unlocks the ADOM
    required: false
    default: True
    type: bool
  password:
    description:
      - The password associated with the username account.
    required: false
    type: str
  port:
    description:
      - The TCP port used to connect to the FortiManager if other than the default used by the transport
        method(http=80, https=443).
    required: false
    type: int
  provider:
    description:
      - Dictionary which acts as a collection of arguments used to define the characteristics
        of how to connect to the device.
      - Arguments hostname, username, and password must be specified in either provider or local param.
      - Local params take precedence, e.g. hostname is preferred to provider["hostname"] when both are specified.
    required: false
    type: dict
  session_id:
    description:
      - The session_id of an established and active session
    required: false
    type: str
  state:
    description:
      - The desired state of the route.
      - absent will remove the route if it exists.
      - present will update the configuration if needed.
    required: false
    default: present
    type: str
    choices: ["present", "absent"]
  use_ssl:
    description:
      - Determines whether to use HTTPS(True) or HTTP(False).
    required: false
    default: True
    type: bool
  username:
    description:
      - The username used to authenticate with the FortiManager.
    required: false
    type: str
  validate_certs:
    description:
      - Determines whether to validate certs against a trusted certificate file (True), or accept all certs (False).
    required: false
    default: False
    type: bool
  comment:
    description:
      - A comment to add to the route.
    required: false
    type: str
  distance:
    description:
      - The distance metric to associate to the route.
    required: false
    type: int
  destination:
    description:
      - The destination subnet.
      - This supports sending a string as cidr notation or a two element list that
        would be returned from getting existing address objects.
      - Alternatively, the netmask and network params can be used.
    required: true
    type: list
  destination_netmask: 
    description:
      - The netmask to use for the destination address.
      - The network param must be used in conjuction with netmask.
      - Alternatively, the destination param can be used for cidr notation.
    required: false
    type: str
  destination_network: 
    description:
      - The network address to use destination address.
      - The netmask param must be used in conjuction with network.
      - Alternatively, the destination param can be used for cidr notation.
    required: false
    type: str
  destination_object:
    description
      - The address or address-group object to use as the destination address
    required: false
    type: str
  fortigate:
    description:
      - The fortigate to apply the route to.
    required: true
    type: str
  gateway:
    description:
      - The gateway address for which the destination can be reached.
    required: true
    type: str
  intfc:
    description:
      - The interface used to reach the route.
    required: false
    type: list
  priority:
    description:
      - The priority to assign the route.
    required: false
    type: int
  sequence_number:
    description:
      - The sequence number of the route in FortiManager
      - This is required in order to modify an existing route's interface, destination, and gateway.
    required: false
    type: str
  vdom:
    description:
      - The vdom on the fortigate to add the route to.
    default: root
    type: str
  weight:
    description:
      - The weight to assign to the route.
    required: false
    type: int
'''

EXAMPLES = '''
- name: Add Route
  fortimgr_route:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    state: "present"
    adom: "lab"
    fortigate: "lab_fg"
    vdom: "root"
    destination: "10.2.1.0/24"
    gateway: "10.1.1.1"
    intfc: "port1"
- name: Remove Route
  fortimgr_route:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    state: "absent"
    adom: "lab"
    fortigate: "lab_fg"
    vdom: "root"
    destination: "10.2.1.0/24"
    gateway: "10.1.1.1"
'''

RETURN = '''
existing:
    description: The existing configuration for the Route (uses policy_name) before the task executed.
    returned: always
    type: dict
    sample: {"changed": false, "config": {}, "existing": {
             "blackhole": 0, "comment": "", "device": ["port1"], "distance": 10, "dst": ["10.0.0.0", "255.0.0.0"],
             "dynamic-gateway": 0, "gateway": "10.1.1.1", "internet-service": 0, "priority": 0, "seq-num": 4,
             "virtual-wan-link": 0, "weight": 17}
config:
    description: The configuration that was pushed to the FortiManager.
    returned: always
    type: dict
    sample: {"method": "update", "params": [{"data": {"device": ["port2"], "dst": ["7.7.7.7", "255.255.255.255"],
             "gateway": "2.2.2.3"}, "seq-num": 15, "url": "/pm/config/device/FortiGate-VM64-KVM/vdom/root/route/static"}]}
locked:
    description: The status of the ADOM lock command
    returned: When lock set to True
    type: bool
    sample: True
saved:
    description: The status of the ADOM save command
    returned: When lock set to True
    type: bool
    sample: True
unlocked:
    description: The status of the ADOM unlock command
    returned: When lock set to True
    type: bool
    sample: True
'''

import time
import requests
from ansible.module_utils.basic import AnsibleModule, env_fallback, return_values

requests.packages.urllib3.disable_warnings()


class FortiManager(object):
    """
    This is the Base Class for FortiManager modules. All methods common across several FortiManager Classes should be
    defined here and inherited by the sub-class.
    """

    def __init__(self, host, user, passw, use_ssl=True, verify=False, adom="", package="", api_endpoint="", **kwargs):
        """
        :param host: Type str.
                     The IP or resolvable hostname of the FortiManager.
        :param user: Type str.
                     The username used to authenticate with the FortiManager.
        :param passw: Type str.
                      The password associated with the user account.
        :param use_ssl: Type bool.
                        The default is True, which uses HTTPS instead of HTTP.
        :param verify: Type bool.
                       The default is False, which does not verify the certificate against the list of trusted
                       certificates.
        :param adom: Type str.
                     The FortiManager ADOM which the configuration should belong to.
        :param package: Type str.
                        The FortiManager policy package that should be used.
        :param api_endpoint: Type str.
                             The API endpoint used for a particular configuration section.
        :param kwargs: Type dict. Currently supports port.
        :param headers: Type dict.
                        The headers to include in HTTP requests.
        :param port: Type str.
                     Passing the port parameter will override the default HTTP(S) port when making requests.
        """
        self.host = host
        self.user = user
        self.passw = passw
        self.verify = verify
        self.api_endpoint = api_endpoint
        self.adom = adom
        self.package = package
        self.dvmdb_url = "/dvmdb/adom/{}/".format(self.adom)
        self.obj_url = "/pm/config/adom/{}/obj/firewall/{}".format(self.adom, self.api_endpoint)
        self.pkg_url = "/pm/config/adom/{}/pkg/{}/firewall/{}".format(self.adom, self.package, self.api_endpoint)
        self.wsp_url = "/dvmdb/adom/{}/workspace/".format(self.adom)
        self.headers = {"Content-Type": "application/json"}
        if "port" not in kwargs:
            self.port = ""
        else:
            self.port = ":{}".format(kwargs["port"])

        if use_ssl:
            self.url = "https://{fw}{port}/jsonrpc".format(fw=self.host, port=self.port)
        else:
            self.url = "http://{fw}{port}/jsonrpc".format(fw=self.host, port=self.port)

    def add_config(self, new_config):
        """
        This method is used to submit a configuration request to the FortiManager. Only the object configuration details
        need to be provided; all other parameters that make up the API request body will be handled by the method.

        :param new_config: Type list.
                           The "data" portion of the configuration to be submitted to the FortiManager.
        :return: The response from the API request to add the configuration.
        """
        body = {"method": "add", "params": [{"url": self.obj_url, "data": new_config, "session": self.session}]}
        response = self.make_request(body)

        return response

    @staticmethod
    def cidr_to_network(network):
        """
        Method is used to convert a network address in CIDR notation to a list with address and mask.
  
        :param network: Type str.
                        The network address in CIDR notation.
  
        :return: A list with address and mask in that order.
        """
        cidr_mapping = {
                "0": "0.0.0.0",
                "1": "128.0.0.0",
                "2": "192.0.0.0",
                "3": "224.0.0.0",
                "4": "240.0.0.0",
                "5": "248.0.0.0",
                "6": "252.0.0.0",
                "7": "254.0.0.0",
                "8": "255.0.0.0",
                "9": "255.128.0.0",
                "10": "255.192.0.0",
                "11": "255.224.0.0",
                "12": "255.240.0.0",
                "13": "255.248.0.0",
                "14": "255.252.0.0",
                "15": "255.254.0.0",
                "16": "255.255.0.0",
                "17": "255.255.128.0",
                "18": "255.255.192.0",
                "19": "255.255.224.0",
                "20": "255.255.240.0",
                "21": "255.255.248.0",
                "22": "255.255.252.0",
                "23": "255.255.254.0",
                "24": "255.255.255.0",
                "25": "255.255.255.128",
                "26": "255.255.255.192",
                "27": "255.255.255.224",
                "28": "255.255.255.240",
                "29": "255.255.255.248",
                "30": "255.255.255.252",
                "31": "255.255.255.254",
                "32": "255.255.255.255"
            }
  
        if "/" in network:
            network_address = network.split("/")
            mask = network_address.pop()

            if mask and int(mask) in range(0, 33):
                network_address.append(cidr_mapping[mask])
            else:
                network_address = []
        else:
            network_address = []
  
        return network_address

    @staticmethod
    def cidr_to_wildcard(wildcard):
        """
        Method is used to convert a wildcard address in CIDR notation to a list with address and mask.
  
        :param wildcard: Type str.
                        The wildcard address in CIDR notation.
  
        :return: A list with address and mask in that order.
        """
        cidr_mapping = {
            "0": "255.255.255.255",
            "1": "127.255.255.255",
            "2": "63.255.255.255",
            "3": "31.255.255.255",
            "4": "15.255.255.255",
            "5": "7.255.255.255",
            "6": "3.255.255.255",
            "7": "1.255.255.255",
            "8": "0.255.255.255",
            "9": "0.127.255.255",
            "10": "0.63.255.255",
            "11": "0.31.255.255",
            "12": "0.15.255.255",
            "13": "0.7.255.255",
            "14": "0.3.255.255",
            "15": "0.1.255.255",
            "16": "0.0.255.255",
            "17": "0.0.127.255",
            "18": "0.0.63.255",
            "19": "0.0.31.255",
            "20": "0.0.15.255",
            "21": "0.0.7.255",
            "22": "0.0.3.255",
            "23": "0.0.1.255",
            "24": "0.0.0.255",
            "25": "0.0.0.127",
            "26": "0.0.0.63",
            "27": "0.0.0.31",
            "28": "0.0.0.15",
            "29": "0.0.0.7",
            "30": "0.0.0.3",
            "31": "0.0.0.1",
            "32": "0.0.0.0"
            }
  
        if "/" in wildcard:
            wildcard_address = wildcard.split("/")
            mask = wildcard_address.pop()

            if mask and int(mask) in range(0, 33):
                wildcard_address.append(cidr_mapping[mask])
            else:
                wildcard_address = []
        else:
            wildcard_address = []
  
        return wildcard_address

    def config_absent(self, module, proposed, existing):
        """
        This function is used to determine the appropriate configuration to remove from the FortiManager when the
        "state" parameter is set to "absent" and to collect the dictionary data that will be returned by the Ansible
        Module.

        :param module: The AnsibleModule instance.
        :param proposed: The proposed config to send to the FortiManager.
        :param existing: The existing configuration for the item on the FortiManager (using the "name" key to get item).
        :return: A dictionary containing the module exit values.
        """
        changed = False
        config = {}

        if existing:
            # check if proposed is to remove a dynamic_mapping
            if "dynamic_mapping" not in proposed:
                config = self.config_delete(module, proposed["name"])
                changed = True
            else:
                diff = self.get_diff_mappings(proposed, existing)
                if diff:
                    config = self.config_update(module, diff)
                    changed = True

        return {"changed": changed, "config": config, "existing": existing}

    def config_delete(self, module, name):
        """
        This method is used to handle the logic for Ansible modules when the "state" is set to "absent" and only the
        name is provided as input into the Ansible Module. The config_lock is used to lock the configuration if the lock
        param is set to True. The config_response method is used to handle the logic from the response to delete the
        object.

        :param module: The Ansible Module instance started by the task.
        :param name: Type str.
                     The name of the object to be removed from the FortiManager.
        :return: A dictionary that corresponds to the configuration that was sent in the request body to the
                 FortiManager API. This dict will map to the "config" key returned by the Ansible Module.
        """
        # lock config if set and module not in check mode
        if module.params["lock"] and not module.check_mode:
            self.config_lock(module)

        # configure if not in check mode
        if not module.check_mode:
            response = self.delete_config(name)
            self.config_response(module, response.json(), module.params["lock"])

        return {"method": "delete", "params": [{"url": self.obj_url + "/{}".format(name)}]}

    def config_lock(self, module, msg="Unable to Lock the Configuration; Validate the ADOM is not Currently Locked."):
        """
        This method is used to handle the logic for Ansible modules for locking the ADOM when "lock" is set to True. The
        lock method is used to make the request to the FortiManager.

        :param module: The Ansible Module instance started by the task.
        :param msg: Type str.
                    A message for the module to return upon failure.
        :return: True if lock successful.
        """
        lock_status = self.lock()
        if lock_status["result"][0]["status"]["code"] != 0:
            # try to logout before failing
            self.logout()
            module.fail_json(msg=msg, locked=False, saved=False, unlocked=False)

        return True

    def config_new(self, module, new_config):
        """
        This method is used to handle the logic for Ansible modules when the "state" is set to "present" and their is
        not currently an object of the same type with the same name. The config_lock is used to lock the configuration
        if the lock param is set to True. The config_response method is used to handle the logic from the response to
        create the object.

        :param module: The Ansible Module instance started by the task.
        :param new_config: Type dict.
                           The config dictionary with the objects configuration to send to the FortiManager API. This
                           corresponds to the "data" portion of the request body.
        :return: A dictionary that corresponds to the configuration that was sent in the request body to the
                 FortiManager API. This dict will map to the "config" key returned by the Ansible Module.
        """
        # lock config if set and module not in check mode
        if module.params["lock"] and not module.check_mode:
            self.config_lock(module)

        # configure if not in check mode
        if not module.check_mode:
            response = self.add_config(new_config)
            self.config_response(module, response.json(), module.params["lock"])

        return {"method": "add", "params": [{"url": self.obj_url, "data": new_config}]}

    def config_param_absent(self, module, proposed, existing):
        """
        This function is used to determine the appropriate configuration to remove from the FortiManager when the
        "state" parameter is set to "param_absent" and to collect the dictionary data that will be returned by the
        Ansible Module.

        :param module: The AnsibleModule instance.
        :param proposed: The proposed config to send to the FortiManager.
        :param existing: The existing configuration for the item on the FortiManager (using the "name" key to get item).
        :return: A dictionary containing the module exit values.
        """
        changed = False
        config = {}

        if existing:
            # determine what diff method to call
            if "dynamic_mapping" not in proposed:
                diff = self.get_diff_remove(proposed, existing)
            else:
                diff = self.get_diff_remove_map(proposed, existing)

            if diff:
                config = self.config_update(module, diff)
                changed = True

        return {"changed": changed, "config": config, "existing": existing}

    def config_present(self, module, proposed, existing):
        """
        This function is used to determine the appropriate configuration to send to the FortiManager API when the
        "state" parameter is set to "present" and to collect the dictionary data that will be returned by the Ansible
        Module.

        :param module: The AnsibleModule instance.
        :param proposed: The proposed config to send to the FortiManager.
        :param existing: The existing configuration for the item on the FortiManager (using the "name" key to get item).
        :return: A dictionary containing the module exit values.
        """
        changed = False
        config = {}

        if not existing:
            config = self.config_new(module, proposed)
            changed = True
        else:
            # determine what diff method to call
            if "dynamic_mapping" not in proposed:
                diff = self.get_diff_add(proposed, existing)
            else:
                diff = self.get_diff_add_map(proposed, existing)

            if diff:
                config = self.config_update(module, diff)
                changed = True

        return {"changed": changed, "config": config, "existing": existing}

    def config_response(self, module, json_response, lock):
        """
        This method is to handle the logic for Ansible modules for handling the config request's response. If the lock
        parameter is set to true and the config was successful, the config_save and config_unlock methods are used to
        save the configuration and unlock the ADOM session. If the lock parameter is set to true and the config was
        unsuccessful, the config_unlock method is used to attempt to unlock the ADOM session before failing. If the lock
        parameter is set to False and the configuration is unsuccessful, the module will fail with the json response.

        :param module: The Ansible Module instance started by the task.
        :param json_response: Type dict.
                              The json response from the requests module's configuration request.
        :param lock: Type bool.
                     The setting of the configuration lock. True means locking mechanism is in place.
        :return: True if configuration was saved and the adom unlocked.
        """
        # save if config successful and session locked
        if json_response["result"][0]["status"]["code"] == 0 and lock:
            self.config_save(module)
            self.config_unlock(module)
        # attempt to unlock if config unsuccessful
        elif json_response["result"][0]["status"]["code"] != 0 and lock:
            self.config_unlock(module, msg=json_response, saved=False)
            module.fail_json(msg=json_response, locked=True, saved=False, unlocked=True)
        # fail if not using lock mode and config unsuccessful
        elif json_response["result"][0]["status"]["code"] != 0:
            module.fail_json(msg=json_response)

    def config_save(self, module, msg="Unable to Save Config, Successfully Unlocked"):
        """
        This method is used to handle the logic for Ansible modules for saving a config when "lock" is set to True. The
        save method is used to make the request to the FortiManager. If the save is unsuccessful, the module will use
        the config_unlock method to attempt to unlock before failing.

        :param module: The Ansible Module instance started by the task.
        :param msg: Type str.
                    A message for the module to return upon failure.
        :return: True if the configuration was saved successfully.
        """
        save_status = self.save()
        if save_status["result"][0]["status"]["code"] != 0:
            self.config_unlock(module, "Config Updated, but Unable to Save or Unlock", False)
            # try to logout before failing
            self.logout()
            module.fail_json(msg=msg, locked=True, saved=False, unlocked=True)

        return True

    def config_unlock(self, module, msg="Config Saved, but Unable to Unlock", saved=True):
        """
        This method is used to handle the logic for Ansible modules for locking the ADOM when "lock" is set to True. The
        config_lock is used to lock the configuration if the lock param is set to True. The unlock method is used to
        make the request to the FortiManager.

        :param module: The Ansible Module instance started by the task.
        :param msg: Type str.
                    A message for the module to return upon failure.
        :param saved: Type bool.
                      The save status of the configuration.
        :return: True if unlock successful.
        """
        unlock_status = self.unlock()
        if unlock_status["result"][0]["status"]["code"] != 0:
            # try to logout before failing
            self.logout()
            module.fail_json(msg=msg, locked=True, saved=saved, unlocked=False)

        return True

    def config_update(self, module, update_config):
        """
        This method is used to handle the logic for Ansible modules when the "state" is set to "present" and their is
        not currently an object of the same type with the same name. The config_response method is used to handle the
        logic from the response to update the object.

        :param module: The Ansible Module instance started by the task.
        :param update_config: Type dict.
                              The config dictionary with the objects configuration to send to the FortiManager API. Only
                              the keys that have updates need to be included. This corresponds to the "data" portion of
                              the request body.
        :return: A dictionary that corresponds to the configuration that was sent in the request body to the
                 FortiManager API. This dict will map to the "config" key returned by the Ansible Module.
        """
        # lock config if set and module not in check mode
        if module.params["lock"] and not module.check_mode:
            self.config_lock(module)

        # configure if not in check mode
        if not module.check_mode:
            response = self.update_config(update_config)
            self.config_response(module, response.json(), module.params["lock"])

        return {"method": "update", "params": [{"url": self.obj_url, "data": update_config}]}

    def create_revision(self, proposed):
        """
        This method is used to create an ADOM revision on the FortiManager. The make_request method is used to make the
        API request to add the revision.

        :param proposed: Type list.
                         The data portion of the API Request.
        :return: The json response data from the request to make a revision.
        """
        rev_url = "{}revision".format(self.dvmdb_url)
        body = {"method": "add", "params": [{"url": rev_url, "data": proposed}], "session": self.session}
        response = self.make_request(body).json()

        return response

    def delete_config(self, name):
        """
        This method is used to submit a configuration request to delete an object from the FortiManager.

        :param name: Type str.
                     The name of the object to be removed from the FortiManager.
        :return: The response from the API request to delete the configuration.
        """
        item_url = self.obj_url + "/{}".format(name)
        body = {"method": "delete", "params": [{"url": item_url}], "session": self.session}
        response = self.make_request(body)

        return response

    def delete_revision(self, version):
        """
        This method is used to delete an ADOM revision from the FortiManager. The make_request method is used to submit
        the request to the FortiManager.

        :param version: Type str.
                        The version number corresponding to the revision to delete.
        :return: The json response data from the request to delete the revision.
        """
        rev_url = "{}revision/{}".format(self.dvmdb_url, version)
        body = {"method": "delete", "params": [{"url": rev_url}], "session": self.session}
        response = self.make_request(body).json()

        return response

    def get_adom_fields(self, adom, fields=[]):
        """
        This method is used to get all adoms currently configured on the FortiManager. A list of fields can be passed
        in to limit the scope of what data is returned for the ADOM.

        :param adom: Type str.
                     The name of the ADOM to retrieve the configuration for.
        :param fields: Type list.
                       A list of fields to retrieve for the ADOM.
        :return: The json response from the request to retrieve the configured ADOM. An empty list is returned if the
                 request does not return any data.
        """
        body = dict(method="get", params=[dict(url="/dvmdb/adom", filter=["name", "==", adom], fields=fields)],
                    verbose=1, session=self.session)
        response = self.make_request(body)

        return response.json()["result"][0].get("data", [])

    def get_adoms_fields(self, fields=[]):
        """
        This method is used to get all adoms currently configured on the FortiManager. A list of fields can be passed
        in to limit the scope of what data is returned per ADOM.

        :param fields: Type list.
                       A list of fields to retrieve for each ADOM.
        :return: The json response from the request to retrieve the configured ADOMs. An empty list is returned if the
                 request does not return any data.
        """
        body = dict(method="get", params=[dict(url="/dvmdb/adom", fields=fields)], verbose=1, session=self.session)
        response = self.make_request(body)

        return response.json()["result"][0].get("data", [])

    def get_all(self):
        """
        This method is used to get all objects currently configured on the FortiManager for the ADOM and API Endpoint.

        :return: The list of configuration dictionaries for each object. An empty list is returned if the request does
                 not return any data.
        """
        body = {"method": "get", "params": [{"url": self.obj_url}], "verbose": 1, "session": self.session}
        response = self.make_request(body)

        return response.json()["result"][0].get("data", [])

    def get_all_fields(self, fields):
        """
        This method is used to get all objects currently configured on the FortiManager for the ADOM and API Endpoint.
        The configuration fields retrieved are limited to the list defined in the fields variable.

        :param fields: Type list.
                       The list of fields to return for each object.
        :return: The list of configuration dictionaries for each object. An empty list is returned if the request does
                 not return any data.
        """
        params = [{"url": self.obj_url, "fields": fields}]
        body = {"method": "get", "params": params, "verbose": 1, "session": self.session}
        response = self.make_request(body)

        return response.json()["result"][0].get("data", [])

    def get_device_config(self, device, vdom, config_url, fields=[]):
        """
        This method is used to retrieve the static routes configured on the managed device.

        :param device: Type str.
                       The device to retrieve the static route configuration from.
        :param vdom: Type str.
                     The vdom to retrieve the static route configuration from.
        :param config_url: Type str.
                           The url associated with the configuration section to retrieve.
        :param fields: Type list.
                       A list of fields to retrieve for the device.
        :return: The json response from the request to retrieve the static routes. An empty list is returned if the
                 request does not return any data.
        """
        config_url = "/pm/config/device/{}/vdom/{}/{}".format(device, vdom, config_url)
        body = dict(method="get", params=[dict(url=config_url, fields=fields)], verbose=1, session=self.session)
        response = self.make_request(body).json()["result"][0].get("data", [])

        if not response:
            response = []

        return response

    def get_device_fields(self, device, fields=[]):
        """
        This method is used to retrieve information about a managed device from FortiManager. A list of fields can be
        passed int o limit the scope of what data is returned for the device.

        :param device: Type str.
                       The name of the device to retrieve information for.
        :param fields: Type list.
                       A list of fields to retrieve for the device.
        :return: The json response from the request to retrieve the configured device. An empty list is returned if the
                 request does not return any data.
        """
        body = dict(method="get", params=[dict(url="/dvmdb/device", filter=["name", "==", device], fields=fields)],
                    verbose=1, session=self.session)
        response = self.make_request(body)

        return response.json()["result"][0].get("data", [])

    def get_device_ha(self, device):
        """
        This method is used to get HA information for a device managed by FortiManager.

        :param device: The device to retrieve the HA status from.
        :return: The json response from the request to retrieve the HA status. An empty list is returned if the request
                 does not return any data.
        """
        if not self.adom:
            dev_url = "/dvmdb/device/{}/ha_slave".format(self.adom, device)
        else:
            dev_url = "{}device/{}/ha_slave".format(self.dvmdb_url, device)
        body = dict(method="get", params=[dict(url=dev_url)], verbose=1, session=self.session)
        response = self.make_request(body)

        return response.json()["result"][0].get("data", [])

    def get_device_vdoms(self, device):
        """
        This method is used to retrieve the VDOMs associated with a device managed by FortiManager.

        :param device: The device to retrieve the HA status from.
        :return: The json response from the request to retrieve the HA status. An empty list is returned if the request
                 does not return any data.
        """
        if not self.adom:
            dev_url = "/dvmdb/device/{}/vdom".format(device)
        else:
            dev_url = "{}device/{}/vdom".format(self.dvmdb_url, device)
        body = dict(method="get", params=[dict(url=dev_url)], verbose=1, session=self.session)
        response = self.make_request(body)

        return response.json()["result"][0].get("data", [])

    def get_devices_fields(self, fields=[], dev_filter=[]):
        """
        This method is used to retrieve information about a managed devices from FortiManager. A list of fields can be
        passed int o limit the scope of what data is returned for each the device.

        :param fields: Type list.
                       A list of fields to retrieve for the device.
        :param dev_filter: Type list.
                       A list matching to a filter parameter for API requests [<key>, <operator>, <value>].
        :return: The json response from the request to retrieve the configured devices. An empty list is returned if the
                 request does not return any data.
        """
        if not self.adom:
            dev_url = "/dvmdb/device"
        else:
            dev_url = "{}device".format(self.dvmdb_url)

        body = dict(method="get", params=[dict(url=dev_url, fields=fields, filter=dev_filter)], verbose=1,
                    session=self.session)
        response = self.make_request(body)

        return response.json()["result"][0].get("data", [])

    @staticmethod
    def get_diff_add(proposed, existing):
        """
        This method is used to get the difference between two configurations when the "proposed" configuration is a dict
        of configuration items that should exist in the configuration for the object in the FortiManager. Either the
        get_item or get_item_fields methods should be used to obtain the "existing" variable; if either of those methods
        return an empty dict, then you should use the add_config method to add the new object.

        :param proposed: Type dict.
                         The configuration that should not exist for the object on the FortiManager.
        :param existing: Type dict.
                         The current configuration for the object that potentially needs configuration removed.
        :return: A dict corresponding to the "data" portion of an "update" request. This can be used to call the
                 update_config method.
        """
        config = {}
        for field in proposed.keys():
            if field in existing and proposed[field] != existing[field]:
                if isinstance(existing[field], list):
                    diff = list(set(proposed[field]).union(existing[field]))
                    if diff != existing[field]:
                        config[field] = diff
                elif isinstance(existing[field], dict):
                    config[field] = dict(set(proposed[field].items()).union(existing[field].items()))
                elif isinstance(existing[field], str) or isinstance(existing[field], unicode):
                    config[field] = proposed[field]
            elif field not in existing:
                config[field] = proposed[field]

        if config:
            config["name"] = proposed["name"]

        return config

    @staticmethod
    def get_diff_add_map(proposed, existing):
        """
        This method is used to get the difference between two dynamic_mapping configurations when the "proposed"
        configuration is a dict of configuration items that should exist in the configuration for the object in the
        FortiManager. Either the get_item or get_item_fields method should be used to obtain the "existing" variable; if
        either of those methods return an empty dict, then you should use the add_config method to add the new object.

        :param proposed: Type dict.
                         The configuration that should exist for the object on the FortiManager.
        :param existing: Type dict.
                         The current configuration for the object that potentially needs its configuration modified.
        :return: A dict corresponding to the "data" portion of an "update" request. This can be used to call the
                 update_config method.
        """
        name = proposed.get("name")
        proposed_map = proposed.get("dynamic_mapping")[0]
        proposed_scope = proposed_map.pop("_scope")[0]
        existing_map = existing.get("dynamic_mapping")
        config = dict(name=name, dynamic_mapping=[])
        present = False

        # check if proposed mapping already exists and make necessary updates to config
        if existing_map:
            for mapping in existing_map:
                if proposed_scope in mapping["_scope"]:
                    present = True
                    updated_map = {}
                    for field in proposed_map.keys():
                        # only consider relevant fields that have a difference
                        if field in mapping and proposed_map[field] != mapping[field]:
                            if isinstance(mapping[field], list):
                                diff = list(set(proposed_map[field]).union(mapping[field]))
                                if diff != mapping[field]:
                                    updated_map[field] = diff
                            elif isinstance(mapping[field], dict):
                                updated_map[field] = dict(set(proposed_map[field].items()).union(mapping[field].items()))
                            elif isinstance(mapping[field], str) or isinstance(mapping[field], unicode):
                                updated_map[field] = proposed_map[field]
                        elif field not in mapping:
                            updated_map[field] = proposed_map[field]
                    # config update if dynamic_mapping dict has any keys, need to append _scope key
                    if updated_map:
                        # add scope to updated_map and append the config to the list of other mappings
                        updated_map["_scope"] = mapping["_scope"]
                        config["dynamic_mapping"].append(updated_map)
                    else:
                        # set config to a null dictionary if dynamic mappings are identical and exit loop
                        config = {}
                        break
                else:
                    # keep unrelated mapping in diff so that diff can be used to update FortiManager
                    config["dynamic_mapping"].append(dict(_scope=mapping["_scope"]))

        # add mapping to config if it does not currently exist
        if not present:
            config = proposed
            config["dynamic_mapping"][0]["_scope"] = [proposed_scope]
            for mapping in existing_map:
                config["dynamic_mapping"].append(dict(_scope=mapping["_scope"]))

        return config

    @staticmethod
    def get_diff_mappings(proposed, existing):
        """
        This method is to get the diff of just the mapped Fortigate devices.
        :param proposed: Type dict.
                         The configuration that should not exist for the object on the FortiManager.
        :param existing: Type dict.
                         The current configuration for the object that potentially needs configuration removed.
        :return: A dict corresponding to the "data" portion of an "update" request. This can be used to call the
                 update_config method.
        """
        config = dict(name=proposed["name"], dynamic_mapping=[])
        existing_map = existing.get("dynamic_mapping")
        if existing_map:
            for mapping in existing_map:
                if mapping["_scope"] != proposed["dynamic_mapping"][0]["_scope"]:
                    config["dynamic_mapping"].append(dict(_scope=mapping["_scope"]))

            if len(config["dynamic_mapping"]) == len(existing_map):
                config = {}
        else:
            config = {}

        return config

    @staticmethod
    def get_diff_remove(proposed, existing):
        """
        This method is used to get the difference between two configurations when the "proposed" configuration is a dict
        of configuration items that should not exist in the configuration for the object in the FortiManager. Either the
        get_item or get_item_fields methods should be used to obtain the "existing" variable; if either of those methods
        return an empty dict, then the object does not exist and there is no configuration to remove.

        :param proposed: Type dict.
                         The configuration that should not exist for the object on the FortiManager.
        :param existing: Type dict.
                         The current configuration for the object that potentially needs configuration removed.
        :return: A dict corresponding to the "data" portion of an "update" request. This can be used to call the
                 update_config method.
        """
        config = {}
        for field in proposed.keys():
            if field in existing and isinstance(existing[field], list):
                diff = list(set(existing[field]).difference(proposed[field]))
                if diff != existing[field]:
                    config[field] = diff
            elif field in existing and isinstance(existing[field], dict):
                diff = dict(set(proposed.items()).difference(existing.items()))
                if diff != existing[field]:
                    config[field] = diff

        if config:
            config["name"] = proposed["name"]

        return config

    @staticmethod
    def get_diff_remove_map(proposed, existing):
        """
        This method is used to get the difference between two dynamic_mapping configurations when the "proposed"
        configuration is a dict of configuration items that should not exist in the configuration for the object in the
        FortiManager. Either the get_item or get_item_fields method should be used to obtain the "existing" variable; if
        either of those methods return an empty dict, then the object does not exist and there is no configuration to
        remove.

        :param proposed: Type dict.
                         The configuration that should not exist for the object on the FortiManager.
        :param existing: Type dict.
                         The current configuration for the object that potentially needs configuration removed.
        :return: A dict corresponding to the "data" portion of an "update" request. This can be used to call the
                 update_config method.
        """
        name = proposed.get("name")
        proposed_map = proposed.get("dynamic_mapping")[0]
        proposed_scope = proposed_map.pop("_scope")[0]
        existing_map = existing.get("dynamic_mapping")
        config = dict(name=name, dynamic_mapping=[])
        present = False

        # check if proposed mapping already exists and make necessary updates to config
        if existing_map:
            for mapping in existing_map:
                if proposed_scope in mapping["_scope"]:
                    present = True
                    updated_map = {}
                    for field in proposed_map.keys():
                        if field in mapping and isinstance(mapping[field], list):
                            diff = list(set(mapping[field]).difference(proposed_map[field]))
                            if diff != mapping[field]:
                                updated_map[field] = diff
                        elif field in mapping and isinstance(mapping[field], dict):
                            diff = dict(set(proposed_map.items()).difference(mapping.items()))
                            if diff != mapping[field]:
                                updated_map[field] = diff
                    # config update if dynamic_mapping dict has any keys, need to append _scope key
                    if updated_map:
                        # add scope to updated_map and append the config to the list of other mappings
                        updated_map["_scope"] = mapping["_scope"]
                        config["dynamic_mapping"].append(updated_map)
                    else:
                        # remove dynamic mapping from proposed if proposed matches existing config
                        config = {}
                        break
                else:
                    # keep unrelated mapping in diff so that diff can be used to update FortiManager
                    config["dynamic_mapping"].append(dict(_scope=mapping["_scope"]))

        # set config to dict with name only if mapping does not exist representing no change
        if not present:
            config = {}

        return config

    def get_ha(self):
        """
        This method is used to retrieve the HA status of the FortiManager.

        :return: The json response data from the request to retrieve the HA status.
        """
        body = dict(method="get", params=[dict(url="/cli/global/system/ha")], verbose=1, session=self.session)
        response = self.make_request(body).json()["result"][0].get("data", [])

        return response

    def get_install_status(self, name):
        """
        This method is used to get the config and connection status of the specified FortiGate.

        :param name: Type str.
                     The name of the FortiGate from which to retrieve the current status.
        :return: The json response data from the request to retrieve device status.
        """
        params = [{"url": "{}device".format(self.dvmdb_url), "filter": ["name", "==", name],
                   "fields": ["name", "conf_status", "conn_status"]}]
        body = {"method": "get", "params": params, "verbose": 1, "session": self.session}
        response = self.make_request(body).json()

        return response

    def get_item(self, name):
        """
        This method is used to get a specific object currently configured on the FortiManager for the ADOM and API
        Endpoint.

        :param name: Type str.
                     The name of the object to retrieve.
        :return: The configuration dictionary for the object. An empty dict is returned if the request does
                 not return any data.
        """
        item_url = self.obj_url + "/{}".format(name)
        body = {"method": "get", "params": [{"url": item_url}], "verbose": 1, "session": self.session}
        response = self.make_request(body)

        return response.json()["result"][0].get("data", {})

    def get_item_fields(self, name, fields):
        """
        This method is used to get a specific object currently configured on the FortiManager for the ADOM and API
        Endpoint. The configuration fields retrieved are limited to the list defined in the fields variable.

        :param name: Type str.
                     The name of the object to retrieve.
        :param fields: Type list.
                       The list of fields to return for each object.
        :return: The list of configuration dictionaries for each object. An empty list is returned if the request does
                 not return any data.
        """
        params = [{"url": self.obj_url, "filter": ["name", "==", name], "fields": fields}]
        body = {"method": "get", "params": params, "verbose": 1, "session": self.session}
        response = self.make_request(body)
        response_data = response.json()["result"][0].get("data", [{}])

        if response_data:
            return response_data[0]
        else:
            return {}

    def get_revision(self, name=""):
        """
        This method is used to retrieve ADOM revisions from the FortiManager. If name is not specified, all revisions
        will be returned.

        :param name: Type str.
                     The name of the revision to retrieve.
        :return: The json response data from the request to retrieve the revision.
        """
        params = [{"url": "{}revision".format(self.dvmdb_url)}]
        if name:
            # noinspection PyTypeChecker
            params[0].update({"filter": ["name", "==", name]})

        body = {"method": "get", "params": params, "verbose": 1, "session": self.session}
        response = self.make_request(body).json()

        return response

    def get_status(self):
        """
        This method is used to retrieve the status of the FortiManager.

        :return: The json response data from the request to retrieve system status.
        """
        body = dict(method="get", params=[dict(url="/sys/status")], verbose=1, session=self.session)
        response = self.make_request(body)

        return response.json()["result"][0].get("data", [])

    def get_task(self, task, wait):
        """
        This method is used to get the status of a task.

        :param task: Type str.
                     The task id to retrieve
        :param wait: Type int.
                     The number of minutes to wait before failing.
        :return: The json results from the task once completed, failed, or time ran out.
        """
        body = {"method": "get", "params": [{"url": "task/task/{}".format(task)}], "verbose": 1,
                "session": self.session}
        percent_complete = 0
        countdown = time.localtime().tm_min

        while percent_complete != 100:
            response = self.make_request(body).json()
            if response["result"][0]["status"]["code"] == 0:
                percent_complete = response["result"][0]["data"]["percent"]

            # limit execution time to specified time in minutes
            if time.localtime().tm_min - countdown > wait:
                break
            elif countdown in range((60 - wait), 61) and time.localtime().tm_min in range(wait):
                break
            else:
                time.sleep(15)

        return response

    def install_package(self, proposed):
        """
        This method is used to install a package to the end devices.

        :param proposed: Type list.
                         The data portion of the API Request.
        :return: The json result data from the task associated with request to make install the package.
        """
        body = {"method": "exec", "params": [{"url": "/securityconsole/install/package", "data": proposed, "id": 1,
                                              "session": self.session}]}

        response = self.make_request(body).json()

        # collect task id
        if response["result"][0]["status"]["code"] == 0:
            task = response["result"][0]["data"]["task"]
        else:
            return response

        # check for task completion
        task_status = self.get_task(task, 10)

        return task_status

    def lock(self):
        """
        The lock method is used to lock the ADOM to enable configurations to be sent to the FortiManager when it has
        workspace mode enabled.

        :return: The JSON response from the request to lock the session.
        """
        body = {"method": "exec", "params": [{"url": self.wsp_url + "lock"}], "session": self.session}
        response = self.make_request(body)

        return response.json()

    def login(self):
        """
        The login method is used to establish a session with the FortiManager. All necessary parameters need to be
        established at class instantiation.

        :return: The response from the login request. The instance session is also set, and defaults to None if the
        login was not successful
        """
        params = [{"url": "/sys/login/user", "data": {"user": self.user, "passwd": self.passw}}]
        body = {"method": "exec", "params": params}
        login = self.make_request(body)

        self.session = login.json().get("session")

        return login

    def logout(self):
        """
        The login method is used to establish a session with the FortiManager. All necessary parameters need to be
        established at class instantiation.

        :return: The response from the login request. The instance session is also set, and defaults to None if the
        login was not successful
        """
        body = dict(method="exec", params=[{"url": "/sys/logout"}], session=self.session)
        logout = self.make_request(body)

        return logout

    def make_request(self, body):
        """
        This method is used to make a request to the FortiManager API. All requests to FortiManager use the POST method
        to the same URL.

        :param body: Type dict.
                     The JSON body with the necessary request params.
        :return: The response from the API request.
        """
        response = requests.post(self.url, json=body, headers=self.headers, verify=self.verify)

        return response

    def preview_install(self, package, device, vdoms, lock):
        """
        This method is used to preview what changes will be pushed to the end device when the package is installed. The
        Fortimanager requires the install process be started with the preview flag in order for policy updates to be
        included in the preview request. This method will handle this process, and cancel the install task after the
        preview has been generated. This method also makes use of FortiManager's "id" field to keep track of the stages
        (install preview, generate preview, retrieve preview, cancel install) the method is currently executing, and
        returns the ID in the response. If the module returns early, then the "id" field can be used to determine where
        the failure occurred.

        :param package: Type str.
                        The name of the package in consideration for install.
        :param device: Type str.
                       The FortiNet to preview install.
        :param vdoms: Type list.
                      The list of vdoms associated with the vdom to preview install
        :param lock: Type bool
                     Determines whether the package install preview will use the auto lock field.
        :return: The json response data from the request to preview install the package.
        """
        # issue package install with preview flag to include policy in preview
        flags = ["preview"]
        if lock:
            flags.append("auto_lock_ws")

        proposed = [{"adom": self.adom, "flags": flags, "pkg": package, "scope": [device]}]
        response = self.install_package(proposed)

        if response["result"][0].get("data", {"state": "error"}).get("state") == "done":
            # generate preview request
            proposed = [{"adom": self.adom, "device": device, "vdoms": vdoms}]
            body = {"method": "exec", "params": [{"url": "/securityconsole/install/preview", "data": proposed}],
                    "id": 2, "session": self.session}
            response = self.make_request(body).json()
        else:
            response.update({"id": 1})
            return response

        # collect task id
        if response["result"][0]["status"]["code"] == 0:
            task = response["result"][0]["data"]["task"]
        else:
            return response

        task_status = self.get_task(task, 5)
        if task_status["result"][0]["data"]["percent"] == 100:
            # cancel install task
            url = "/securityconsole/package/cancel/install"
            params = [{"url": url, "data": [{"adom": self.adom, "device": device}]}]
            body = {"method": "exec", "params": params, "id": 3, "session": self.session}
            response = self.make_request(body).json()
        else:
            task_status.update({"id": 2})
            return task_status

        if response["result"][0]["status"]["code"] == 0:
            # get preview result
            params = [{"url": "/securityconsole/preview/result", "data": [{"adom": self.adom, "device": device}]}]
            body = {"method": "exec", "params": params, "id": 4,
                    "session": self.session}
            response = self.make_request(body).json()
        else:
            return response

        return response

    def restore_revision(self, version, proposed):
        """
        This method is used to restore an ADOM to a previous revision.

        :param version: Type str.
                        The version number corresponding to the revision to delete.
        :param proposed: Type list.
                         The data portion of the API request.
        :return: The json response data from the request to delete the revision.
        """
        rev_url = "{}revision/{}".format(self.dvmdb_url, version)
        body = {"method": "clone", "params": [{"url": rev_url, "data": proposed}], "session": self.session}
        response = self.make_request(body).json()

        return response

    def save(self):
        """
        The save method is used to save the ADOM configurations during a locked session.

        :return: The JSON response from the request to save the session.
        """
        body = {"method": "exec", "params": [{"url": self.wsp_url + "commit"}], "session": self.session}
        response = self.make_request(body)

        return response.json()

    def unlock(self):
        """
        The unlock method is used to lock the ADOM to enable configurations to be sent to the FortiManager when it has
        workspace mode enabled.

        :return: The JSON response from the request to unlock the session.
        """
        body = {"method": "exec", "params": [{"url": self.wsp_url + "unlock"}], "session": self.session}
        response = self.make_request(body)

        return response.json()

    def update_config(self, update_config):
        """
        This method is used to submit a configuration update request to the FortiManager. Only the object configuration
        details need to be provided; all other parameters that make up the API request body will be handled by the
        method. Only fields that need to be updated are required to be in the "update_config" variable (EX: updating
        the comment for an address group only needs the "name" and "comment" fields in the configuration dictionary).
        When including a field in the configuration update, ensure that all items are included for the desired end-state
        (EX: adding address to an address group that already has ["svr01", "svr02"] should include all three
        addresses in the "member" list, ["svr01", "svr02", "svr03"]. If you want to remove part of an item's
        configuration, this method should be used, and the item to be removed should be left off the respective list
        (EX: removing an address from an address group that has ["svr01", "svr02", "svr03"] should have a "member" list
        like ["svr01", "svr02"] with the final state of the address group containing only svr01 and svr02).

        :param update_config: Type list.
                           The "data" portion of the configuration to be submitted to the FortiManager.
        :return: The response from the API request to add the configuration.
        """
        body = {"method": "update", "params": [{"url": self.obj_url, "data": update_config, "session": self.session}]}
        response = self.make_request(body)

        return response


class FMRoute(FortiManager):
    """
    This is the class used for interacting with FortiGate devices and VDOMs.

    :param fortigate: Type str.
                      The particular fortigate to interact with.
    :param vdom: Type str.
                 The particular vdom on the fortigate to interact with.
    """

    def __init__(self, host, user, passw, fortigate, vdom, use_ssl=True, verify=False, adom="", package="",
                 api_endpoint="", **kwargs):
        super(FMRoute, self).__init__(host, user, passw, use_ssl, verify, adom, package, api_endpoint, **kwargs)

        self.fortigate = fortigate
        self.vdom = vdom
        self.dev_url = "/pm/config/device/{}/vdom/{}".format(self.fortigate, self.vdom)
        self.obj_url = "{}/router/static".format(self.dev_url)

    def config_absent(self, module, proposed, existing):
        """
        This function is used to determine the appropriate configuration to remove from the FortiManager when the
        "state" parameter is set to "absent" and to collect the dictionary data that will be returned by the Ansible
        Module.

        :param module: The AnsibleModule instance.
        :param proposed: The proposed config to send to the FortiManager.
        :param existing: The existing configuration for the item on the FortiManager (using the "name" key to get item).
        :return: A dictionary containing the module exit values.
        """
        changed = False
        config = {}

        # proposed length of 1 is just the sequence number of the route
        if existing:
            config = self.config_delete(module, existing["seq-num"])
            changed = True
        else:
            existing = {}

        return {"changed": changed, "config": config, "existing": existing}

    def config_new(self, module, new_config):
        """
        This method is used to handle the logic for Ansible modules when the "state" is set to "present" and their is
        not currently an object of the same type with the same name. The config_lock is used to lock the configuration
        if the lock param is set to True. The config_response method is used to handle the logic from the response to
        create the object.

        :param module: The Ansible Module instance started by the task.
        :param new_config: Type dict.
                           The config dictionary with the objects configuration to send to the FortiManager API. This
                           corresponds to the "data" portion of the request body.
        :return: A dictionary that corresponds to the configuration that was sent in the request body to the
                 FortiManager API. This dict will map to the "config" key returned by the Ansible Module.
        """
        # lock config if set and module not in check mode
        if module.params["lock"] and not module.check_mode:
            self.config_lock(module)

        # configure if not in check mode
        if not module.check_mode:
            response = self.add_config(new_config)
            self.config_response(module, response.json(), module.params["lock"])
            sequence_number = response.json().get("result", [{}])[0].get("data", {}).get("seq-num", "None")
            new_config.update({"seq-num": sequence_number})

        return {"method": "add", "params": [{"url": self.obj_url, "data": new_config}]}

    def config_present(self, module, proposed, existing):
        """
        This function is used to determine the appropriate configuration to send to the FortiManager API when the
        "state" parameter is set to "present" and to collect the dictionary data that will be returned by the Ansible
        Module.

        :param module: The AnsibleModule instance.
        :param proposed: The proposed config to send to the FortiManager.
        :param existing: The existing configuration for the item on the FortiManager (using the "name" key to get item).
        :return: A dictionary containing the module exit values.
        """
        changed = False
        config = {}

        if not existing:
            config = self.config_new(module, proposed)
            changed = True
        else:
            diff = self.get_diff_add(proposed, existing)
            if diff and module.params["sequence_number"]:
                config = self.config_update(module, diff)
                changed = True
            elif diff and "device" in diff:
                module.fail_json(msg="This module does not support creating a route matching an existing destination"
                                     " prefix that points to a different interface. Modifying an existing route's"
                                     " interface can be done using the sequence_number parameter", existing=existing)
            elif diff and "gateway" in diff:
                diff.pop("seq-num")
                config = self.config_new(module, proposed)
                changed = True
            elif diff:
                config = self.config_update(module, diff)
                changed = True

        return {"changed": changed, "config": config, "existing": existing}

    @staticmethod
    def get_diff_add(proposed, existing):
        """
        This method is used to get the difference between two configurations when the "proposed" configuration is a dict
        of configuration items that should exist in the configuration for the object in the FortiManager. Either the
        get_item or get_item_fields methods should be used to obtain the "existing" variable; if either of those methods
        return an empty dict, then you should use the add_config method to add the new object.

        :param proposed: Type dict.
                         The configuration that should not exist for the object on the FortiManager.
        :param existing: Type dict.
                         The current configuration for the object that potentially needs configuration removed.
        :return: A dict corresponding to the "data" portion of an "update" request. This can be used to call the
                 update_config method.
        """
        config = {}
        replace = ["device"]
        for field in proposed.keys():
            if field in existing and proposed[field] != existing[field]:
                if field in replace:
                    # replace the entries that are lists with fixed length of one
                    config[field] = proposed[field]
                elif isinstance(existing[field], list):
                    diff = list(set(proposed[field]).union(existing[field]))
                    if diff != existing[field]:
                        config[field] = diff
                elif isinstance(existing[field], dict):
                    config[field] = dict(set(proposed[field].items()).union(existing[field].items()))
                elif isinstance(existing[field], str) or isinstance(existing[field], int) or isinstance(existing[field], unicode):
                    config[field] = proposed[field]
            elif field not in existing:
                config[field] = proposed[field]

        if config:
            config["seq-num"] = existing["seq-num"]

        return config

    @staticmethod
    def get_diff_remove(proposed, existing):
        """
        This method is used to get the difference between two configurations when the "proposed" configuration is a dict
        of configuration items that should not exist in the configuration for the object in the FortiManager. Either the
        get_item or get_item_fields methods should be used to obtain the "existing" variable; if either of those methods
        return an empty dict, then the object does not exist and there is no configuration to remove.

        :param proposed: Type dict.
                         The configuration that should not exist for the object on the FortiManager.
        :param existing: Type dict.
                         The current configuration for the object that potentially needs configuration removed.
        :return: A dict corresponding to the "data" portion of an "update" request. This can be used to call the
                 update_config method.
        """
        config = {}
        ignore = ["device", "dst", "dstaddr"]
        for field in proposed.keys():
            # ignore lists that can only have a length of one
            if field in ignore:
                pass
            elif field in existing and isinstance(existing[field], list):
                diff = list(set(existing[field]).difference(proposed[field]))
                if diff != existing[field]:
                    config[field] = diff
            elif field in existing and isinstance(existing[field], dict):
                diff = dict(set(proposed.items()).difference(existing.items()))
                if diff != existing[field]:
                    config[field] = diff

        if config:
            config["seq-num"] = existing["seq-num"]

        return config

    def get_item(self, sequence_number):
        """
        This method is used to get a specific static route currently configured on the FortiGate and VDOM specified in
        the class instance. The destination and gateway are used to distinguish the route.

        :param sequence_number: Type: str.
                                The sequence number in FortiManager of an existing route.
        :return: The configuration for the object as a dictionary. An empty dict is returned if the request does not
                 return any data.
        """
        route_url = "{}/{}".format(self.obj_url, sequence_number)
        body = dict(method="get", params=[dict(url=route_url)], session=self.session)
        response = self.make_request(body).json()["result"][0].get("data", {})

        if not response:
            response = {}

        return response

    def get_item_destination(self, destination, gateway):
        """
        This method is used to get a specific static route currently configured on the FortiGate and VDOM specified in
        the class instance. The destination and gateway are used to distinguish the route.

        :param destination: Type: list,str.
                            The destination address to look up. Specifying the address should be a list in the format
                            of [destination, mask]. Using an address or address group object should be a string.
        :param gateway: Type str.
                        The gateway address used to reach the destination.
        :return: The configuration for the objects as a list with a dictionary. A list with an empty dict is returned if
                 the request does not return any data.
        """
        if isinstance(destination, list):
            dst = ["dst", "==", destination]
        else:
            dst = ["dstaddr", "==", destination]

        dst_filter = [dst, "&&", ["gateway", "==", gateway]]
        body = dict(method="get", params=[dict(url=self.obj_url, filter=dst_filter)], session=self.session)
        response = self.make_request(body).json()["result"][0].get("data", [{}])

        if not response:
            response = [{}]

        return response

    def get_item_fields(self, destination, gateway, fields):
        """
        This method is used to get a specific object currently configured on the FortiManager for the ADOM and API
        Endpoint. The configuration fields retrieved are limited to the list defined in the fields variable.

        :param destination: Type: list,str.
                            The destination address to look up. Specifying the address should be a list in the format
                            of [destination, mask]. Using an address or address group object should be a string.
        :param fields: Type list.
                       The list of fields to return for each object.
        :param gateway: Type str.
                        The gateway address used to reach the destination.
        :return: The list of configuration dictionaries for each object. An empty list is returned if the request does
                 not return any data.
        """
        if isinstance(destination, list):
            dst = ["dst", "==", destination]
        else:
            dst = ["dstaddr", "==", destination]

        dst_filter = [dst, "&&", ["gateway", "==", gateway]]
        params = [dict(url=self.obj_url, filter=dst_filter, fields=fields)]
        body = dict(method="get", params=params, verbose=1, session=self.session)
        response = self.make_request(body)
        response_data = response.json()["result"][0].get("data", [{}])

        if not response:
            response = [{}]

        return response


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str"),
        host=dict(required=False, type="str"),
        lock=dict(default=True, type="bool"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        port=dict(required=False, type="int"),
        provider=dict(required=False, type="dict"),
        session_id=dict(required=False, type="str"),
        state=dict(choices=["absent", "present"], default="present", type="str"),
        use_ssl=dict(default=True, type="bool"),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"])),
        validate_certs=dict(default=False, type="bool"),
        comment=dict(required=False, type="str"),
        distance=dict(required=False, type="int"),
        destination=dict(required=False, type="list"),
        destination_object=dict(required=False, type="str"),
        destination_netmask=dict(required=False, type="str"),
        destination_network=dict(required=False, type="str"),
        fortigate=dict(required=False, type="str"),
        gateway=dict(required=False, type="str"),
        intfc=dict(required=False, type="list"),
        priority=dict(required=False, type="int"),
        sequence_number=dict(required=False, type="str"),
        vdom=dict(default="root", type="str"),
        weight=dict(required=False, type="int")
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True,
                           required_together=[["destination_network", "destination_netmask"]],
                           mutually_exclusive=[["destination", "destination_network"]])
    provider = module.params["provider"] or {}

    # prevent secret params in provider from logging
    no_log = ["password"]
    for param in no_log:
        if provider.get(param):
            module.no_log_values.update(return_values(provider[param]))

    # allow local params to override provider
    for param, pvalue in provider.items():
        if module.params.get(param) is None:
            module.params[param] = pvalue

    adom = module.params["adom"]
    host = module.params["host"]
    password = module.params["password"]
    port = module.params["port"]
    session_id = module.params["session_id"]
    state = module.params["state"]
    use_ssl = module.params["use_ssl"]
    username = module.params["username"]
    validate_certs = module.params["validate_certs"]
    fortigate = module.params["fortigate"]
    vdom = module.params["vdom"]
    seq_num = module.params["sequence_number"]
    dst = module.params["destination"]
    if dst and len(dst) == 1 and "/" in dst[0]:
        dst = FortiManager.cidr_to_network(dst[0])
    elif dst and len(dst) == 1:
        dst = [str(dst[0]), "255.255.255.255"]
    elif module.params["destination_network"] and module.params["destination_netmask"]:
        dst = [module.params["destination_network"], module.params["destination_netmask"]]

    args = {
        "comment": module.params["comment"],
        "device": module.params["intfc"],
        "distance": module.params["distance"],
        "dst": dst,
        "dstaddr": module.params["destination_object"],
        "gateway": module.params["gateway"],
        "priority": module.params["priority"],
        "seq-num": seq_num,
        "weight": module.params["weight"]
    }

    argument_check = dict(host=host, fortigate=fortigate)
    for key, val in argument_check.items():
        if not val:
            module.fail_json(msg="{} is required".format(key))

    if args.get("dst") and args.get("dstaddr"):
        module.fail_json(msg="Destination Addresses cannnot be both Network Addresses and Address Objects")

    if not seq_num:
        if not args.get("gateway"):
            module.fail_json(msg="The gateway parameter is required when not specifying the sequence number"
                                 " of an existing route.")
        elif not args.get("dst") and not args.get("dstaddr"):
            module.fail_json(msg="Either the destination or destination_object parameter is required when"
                                 " not specifying the sequence number of an existing route.")

    # "if isinstance(v, bool) or v" should be used if a bool variable is added to args
    proposed = dict((k, v) for k, v in args.items() if v)

    kwargs = dict()
    if port:
        kwargs["port"] = port

    # validate successful login or use established session id
    session = FMRoute(host, username, password, fortigate, vdom, use_ssl, validate_certs, adom, **kwargs)
    if not session_id:
        session_login = session.login()
        if not session_login.json()["result"][0]["status"]["code"] == 0:
            module.fail_json(msg="Unable to login")
    else:
        session.session = session_id

    # get existing configuration from fortimanager and make necessary changes
    if seq_num:
        existing = session.get_item(seq_num)
    else:
        destination = proposed.get("dst")
        if not destination:
            destination = proposed.get("dstaddr")
        existing = session.get_item_destination(destination, proposed["gateway"])[0]

    if state == "present":
        results = session.config_present(module, proposed, existing)
    else:
        results = session.config_absent(module, proposed, existing)

    # if module has made it this far and lock set, then all related return values are true
    if module.params["lock"] and results["changed"]:
        locked = dict(locked=True, saved=True, unlocked=True)
        results.update(locked)

    # logout, build in check for future logging capabilities
    if not session_id:
        session_logout = session.logout()
        # if not session_logout.json()["result"][0]["status"]["code"] == 0:
        #     results["msg"] = "Completed tasks, but unable to logout of FortiManager"
        #     module.fail_json(**results)

    return module.exit_json(**results)


if __name__ == "__main__":
    main()
