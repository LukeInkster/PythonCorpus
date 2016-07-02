Getting Started with Azure
==========================

Ansible includes a suite of modules for interacting with Azure Resource Manager, giving you the tools to easily create
and orchestrate infrastructure on the Microsoft Azure Cloud.

Requirements
------------

Using the Azure Resource Manager modules requires having `Azure Python SDK <https://github.com/Azure/azure-sdk-for-python>`_
installed on the host running Ansible. You will need to have >= v2.0.0RC4 installed. The simplest way to install the
SDK is via pip:

.. code-block:: bash

    $ pip install "azure>=2.0.0rc4"


Authenticating with Azure
-------------------------

Using the Azure Resource Manager modules requires authenticating with the Azure API. You can choose from two authentication strategies:

* Active Directory Username/Password
* Service Principal Credentials

Follow the directions for the strategy you wish to use, then proceed to `Providing Credentials to Azure Modules`_ for
instructions on how to actually use the modules and authenticate with the Azure API.


Using Service Principal
.......................

There is now a detailed official tutorial describing `how to create a service principal <https://azure.microsoft.com/en-us/documentation/articles/resource-group-create-service-principal-portal/>`_.

After stepping through the tutorial you will have:

* Your Client ID, which is found in the “client id” box in the “Configure” page of your application in the Azure portal
* Your Secret key, generated when you created the application. You cannot show the key after creation.
  If you lost the key, you must create a new one in the “Configure” page of your application.
* And finally, a tenant ID. It’s a UUID (e.g. ABCDEFGH-1234-ABCD-1234-ABCDEFGHIJKL) pointing to the AD containing your
  application. You will find it in the URL from within the Azure portal, or in the “view endpoints” of any given URL.


Using Active Directory Username/Password
........................................

To create an Active Directory username/password:

* Connect to the Azure Classic Portal with your admin account
* Create a user in your default AAD. You must NOT activate Multi-Factor Authentication
* Go to Settings - Administrators
* Click on Add and enter the email of the new user.
* Check the checkbox of the subscription you want to test with this user.
* Login to Azure Portal with this new user to change the temporary password to a new one. You will not be able to use the
  temporary password for OAuth login.

Providing Credentials to Azure Modules
......................................

The modules offer several ways to provide your credentials. For a CI/CD tool such as Ansible Tower or Jenkins, you will
most likely want to use environment variables. For local development you may wish to store your credentials in a file
within your home directory. And of course, you can always pass credentials as parameters to a task within a playbook. The
order of precedence is parameters, then environment variables, and finally a file found in your home directory.

Using Environment Variables
```````````````````````````

To pass service principal credentials via the environment, define the following variables:

* AZURE_CLIENT_ID
* AZURE_SECRET
* AZURE_SUBSCRIPTION_ID
* AZURE_TENANT

To pass Active Directory username/password via the environment, define the following variables:

* AZURE_AD_USER
* AZURE_PASSWORD
* AZURE_SUBSCRIPTION_ID

Storing in a File
`````````````````

When working in a development environment, it may be desirable to store credentials in a file. The modules will look
for credentials in $HOME/.azure/credentials. This file is an ini style file. It will look as follows:

.. code-block:: ini

    [default]
    subscription_id=xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    client_id=xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    secret=xxxxxxxxxxxxxxxxx
    tenant=xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

It is possible to store multiple sets of credentials within the credentials file by creating multiple sections. Each
section is considered a profile. The modules look for the [default] profile automatically. Define AZURE_PROFILE in the
environment or pass a profile parameter to specify a specific profile.

Passing as Parameters
`````````````````````

If you wish to pass credentials as parameters to a task, use the following parameters for service principal:

* client_id
* secret
* subscription_id
* tenant

Or, pass the following parameters for Active Directory username/password:

* ad_user
* password
* subscription_id


Creating Virtual Machines
-------------------------

There are two ways to create a virtual machine, both involving the azure_rm_virtualmachine module. We can either create
a storage account, network interface, security group and public IP address and pass the names of these objects to the
module as parameters, or we can let the module do the work for us and accept the defaults it chooses.

Creating Individual Components
..............................

An Azure module is available to help you create a storage account, virtual network, subnet, network interface,
security group and public IP. Here is a full example of creating each of these and passing the names to the
azure_rm_virtualmachine module at the end:

.. code-block:: yaml

    - name: Create storage account
      azure_rm_storageaccount:
        resource_group: Testing
        name: testaccount001
        account_type: Standard_LRS

    - name: Create virtual network
      azure_rm_virtualnetwork:
        resource_group: Testing
        name: testvn001
        address_prefixes: "10.10.0.0/16"

    - name: Add subnet
      azure_rm_subnet:
        resource_group: Testing
        name: subnet001
        address_prefix: "10.10.0.0/24"
        virtual_network: testvn001

    - name: Create public ip
      azure_rm_publicipaddress:
        resource_group: Testing
        allocation_method: Static
        name: publicip001

    - name: Create security group that allows SSH
        azure_rm_securitygroup:
        resource_group: Testing
        name: secgroup001
        rules:
          - name: SSH
            protocol: Tcp
            destination_port_range: 22
            access: Allow
            priority: 101
            direction: Inbound

    - name: Create NIC
      azure_rm_networkinterface:
        resource_group: Testing
        name: testnic001
        virtual_network: testvn001
        subnet: subnet001
        public_ip_name: publicip001
        security_group: secgroup001

    - name: Create virtual machine
      azure_rm_virtualmachine:
        resource_group: Testing
        name: testvm001
        vm_size: Standard_D1
        storage_account: testaccount001
        storage_container: testvm001
        storage_blob: testvm001.vhd
        admin_username: admin
        admin_password: Password!
        network_interfaces: testnic001
        image:
          offer: CentOS
          publisher: OpenLogic
          sku: '7.1'
          version: latest

Each of the Azure modules offers a variety of parameter options. Not all options are demonstrated in the above example.
See each individual module for further details and examples.


Creating a Virtual Machine with Default Options
...............................................

If you simply want to create a virtual machine without specifying all the details, you can do that as well. The only
caveat is that you will need a virtual network with one subnet already in your resource group. Assuming you have a
virtual network already with an existing subnet, you can run the following to create a VM:

.. code-block:: yaml

    azure_rm_virtualmachine:
      resource_group: Testing
      name: testvm10
      vm_size: Standard_D1
      admin_username: chouseknecht
      ssh_password: false
      ssh_public_keys: "{{ ssh_keys }}"
      image:
        offer: CentOS
        publisher: OpenLogic
        sku: '7.1'
        version: latest


Dynamic Inventory Script
------------------------

If you are not familiar with Ansible's dynamic inventory scripts, check out `Intro to Dynamic Inventory <http://docs.ansible.com/ansible/intro_dynamic_inventory.html>`_.

The Azure Resource Manager inventory script is called azure_rm.py. It authenticates with the Azure API exactly the same as the
Azure modules, which means you will either define the same environment variables described above in `Using Environment Variables`_,
create a $HOME/.azure/credentials file (also described above in `Storing in a File`_), or pass command line parameters. To see available command
line options execute the following:

.. code-block:: bash

    $ ./ansible/contrib/inventory/azure_rm.py --help

As with all dynamic inventory scripts, the script can be executed directly, passed as a parameter to the ansible command,
or passed directly to ansible-playbook using the -i option. No matter how it is executed the script produces JSON representing
all of the hosts found in your Azure subscription. You can narrow this down to just hosts found in a specific set of
Azure resource groups, or even down to a specific host.

For a given host, the inventory script provides the following host variables:

.. code-block:: JSON

    {
      "ansible_host": "XXX.XXX.XXX.XXX",
      "computer_name": "computer_name2",
      "fqdn": null,
      "id": "/subscriptions/subscription-id/resourceGroups/galaxy-production/providers/Microsoft.Compute/virtualMachines/object-name",
      "image": {
        "offer": "CentOS",
        "publisher": "OpenLogic",
        "sku": "7.1",
        "version": "latest"
      },
      "location": "westus",
      "mac_address": "00-0D-3A-31-2C-EC",
      "name": "object-name",
      "network_interface": "interface-name",
      "network_interface_id": "/subscriptions/subscription-id/resourceGroups/galaxy-production/providers/Microsoft.Network/networkInterfaces/object-name1",
      "network_security_group": null,
      "network_security_group_id": null,
      "os_disk": {
        "name": "object-name",
        "operating_system_type": "Linux"
      },
      "plan": null,
      "powerstate": "running",
      "private_ip": "172.26.3.6",
      "private_ip_alloc_method": "Static",
      "provisioning_state": "Succeeded",
      "public_ip": "XXX.XXX.XXX.XXX",
      "public_ip_alloc_method": "Static",
      "public_ip_id": "/subscriptions/subscription-id/resourceGroups/galaxy-production/providers/Microsoft.Network/publicIPAddresses/object-name",
      "public_ip_name": "object-name",
      "resource_group": "galaxy-production",
      "security_group": "object-name",
      "security_group_id": "/subscriptions/subscription-id/resourceGroups/galaxy-production/providers/Microsoft.Network/networkSecurityGroups/object-name",
      "tags": {
        "db": "mysql"
      },
      "type": "Microsoft.Compute/virtualMachines",
      "virtual_machine_size": "Standard_DS4"
    }

Host Groups
...........

By default hosts are grouped by:

* azure (all hosts)
* location name
* resource group name
* security group name
* tag key
* tag key_value

You can control host groupings and host selection by either defining environment variables or creating an
azure_rm.ini file in your current working directory.

NOTE: An .ini file will take precedence over environment variables.

NOTE: The name of the .ini file is the basename of the inventory script (i.e. 'azure_rm') with a '.ini'
extension. This allows you to copy, rename and customize the inventory script and have matching .ini files all in
the same directory.

Control grouping using the following variables defined in the environment:

* AZURE_GROUP_BY_RESOURCE_GROUP=yes
* AZURE_GROUP_BY_LOCATION=yes
* AZURE_GROUP_BY_SECURITY_GROUP=yes
* AZURE_GROUP_BY_TAG=yes

Select hosts within specific resource groups by assigning a comma separated list to:

* AZURE_RESOURCE_GROUPS=resource_group_a,resource_group_b

Select hosts for specific tag key by assigning a comma separated list of tag keys to:

* AZURE_TAGS=key1,key2,key3

Or, select hosts for specific tag key:value pairs by assigning a comma separated list key:value pairs to:

* AZURE_TAGS=key1:value1,key2:value2

If you don't need the powerstate, you can improve performance by turning off powerstate fetching:

* AZURE_INCLUDE_POWERSTATE=no

A sample azure_rm.ini file is included along with the inventory script in contrib/inventory. An .ini
file will contain the following:

.. code-block:: ini

    [azure]
    # Control which resource groups are included. By default all resources groups are included.
    # Set resource_groups to a comma separated list of resource groups names.
    #resource_groups=

    # Control which tags are included. Set tags to a comma separated list of keys or key:value pairs
    #tags=

    # Include powerstate. If you don't need powerstate information, turning it off improves runtime performance.
    # Valid values: yes, no, true, false, True, False, 0, 1.
    include_powerstate=yes

    # Control grouping with the following boolean flags. Valid values: yes, no, true, false, True, False, 0, 1.
    group_by_resource_group=yes
    group_by_location=yes
    group_by_security_group=yes
    group_by_tag=yes


Examples
........

Here are some examples using the inventory script:

.. code-block:: bash

    # Execute /bin/uname on all instances in the Testing resource group
    $ ansible -i azure_rm.py Testing -m shell -a "/bin/uname -a"

    # Use the inventory script to print instance specific information
    $ ./ansible/contrib/inventory/azure_rm.py --host my_instance_host_name --resource-groups=Testing --pretty

    # Use the inventory script with ansible-playbook
    $ ansible-playbook -i ./ansible/contrib/inventory/azure_rm.py test_playbook.yml

Here is a simple playbook to exercise the Azure inventory script:

.. code-block:: yaml

    - name: Test the inventory script
      hosts: azure
      connection: local
      gather_facts: no
      tasks:
        - debug: msg="{{ inventory_hostname }} has powerstate {{ powerstate }}"

You can execute the playbook with something like:

.. code-block:: bash

    $ ansible-playbook -i ./ansible/contrib/inventory/azure_rm.py test_azure_inventory.yml
