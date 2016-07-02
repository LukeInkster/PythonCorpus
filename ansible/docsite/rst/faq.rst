Frequently Asked Questions
==========================

Here are some commonly-asked questions and their answers.


.. _set_environment:

How can I set the PATH or any other environment variable for a task or entire playbook?
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Setting environment variables can be done with the `environment` keyword. It can be used at task or play level::

    environment:
      PATH: "{{ ansible_env.PATH }}:/thingy/bin"
      SOME: value

.. note:: starting in 2.0.1 the setup task from gather_facts also inherits the environment directive from the play, you might need to use the `|default` filter to avoid errors if setting this at play level.


How do I handle different machines needing different user accounts or ports to log in with?
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Setting inventory variables in the inventory file is the easiest way.

.. include:: ../rst_common/ansible_ssh_changes_note.rst

For instance, suppose these hosts have different usernames and ports::

    [webservers]
    asdf.example.com  ansible_port=5000   ansible_user=alice
    jkl.example.com   ansible_port=5001   ansible_user=bob

You can also dictate the connection type to be used, if you want::

    [testcluster]
    localhost           ansible_connection=local
    /path/to/chroot1    ansible_connection=chroot
    foo.example.com
    bar.example.com 

You may also wish to keep these in group variables instead, or file them in a group_vars/<groupname> file.
See the rest of the documentation for more information about how to organize variables.

.. _use_ssh:

How do I get ansible to reuse connections, enable Kerberized SSH, or have Ansible pay attention to my local SSH config file?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Switch your default connection type in the configuration file to 'ssh', or use '-c ssh' to use
Native OpenSSH for connections instead of the python paramiko library.  In Ansible 1.2.1 and later, 'ssh' will be used
by default if OpenSSH is new enough to support ControlPersist as an option.

Paramiko is great for starting out, but the OpenSSH type offers many advanced options.  You will want to run Ansible
from a machine new enough to support ControlPersist, if you are using this connection type.  You can still manage
older clients.  If you are using RHEL 6, CentOS 6, SLES 10 or SLES 11 the version of OpenSSH is still a bit old, so 
consider managing from a Fedora or openSUSE client even though you are managing older nodes, or just use paramiko.

We keep paramiko as the default as if you are first installing Ansible on an EL box, it offers a better experience
for new users.

.. _use_ssh_jump_hosts:

How do I configure a jump host to access servers that I have no direct access to?
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

With Ansible 2, you can set a `ProxyCommand` in the
`ansible_ssh_common_args` inventory variable. Any arguments specified in
this variable are added to the sftp/scp/ssh command line when connecting
to the relevant host(s). Consider the following inventory group::

    [gatewayed]
    foo ansible_host=192.0.2.1
    bar ansible_host=192.0.2.2

You can create `group_vars/gatewayed.yml` with the following contents::

    ansible_ssh_common_args: '-o ProxyCommand="ssh -W %h:%p -q user@gateway.example.com"'

Ansible will append these arguments to the command line when trying to
connect to any hosts in the group `gatewayed`. (These arguments are used
in addition to any `ssh_args` from `ansible.cfg`, so you do not need to
repeat global `ControlPersist` settings in `ansible_ssh_common_args`.)

Note that `ssh -W` is available only with OpenSSH 5.4 or later. With
older versions, it's necessary to execute `nc %h:%p` or some equivalent
command on the bastion host.

With earlier versions of Ansible, it was necessary to configure a
suitable `ProxyCommand` for one or more hosts in `~/.ssh/config`,
or globally by setting `ssh_args` in `ansible.cfg`.

.. _ec2_cloud_performance:

How do I speed up management inside EC2?
++++++++++++++++++++++++++++++++++++++++

Don't try to manage a fleet of EC2 machines from your laptop.  Connect to a management node inside EC2 first
and run Ansible from there.

.. _python_interpreters:

How do I handle python pathing not having a Python 2.X in /usr/bin/python on a remote machine?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

While you can write ansible modules in any language, most ansible modules are written in Python, and some of these
are important core ones.

By default Ansible assumes it can find a /usr/bin/python on your remote system that is a 2.X version of Python, specifically
2.4 or higher.

Setting of an inventory variable 'ansible_python_interpreter' on any host will allow Ansible to auto-replace the interpreter
used when executing python modules.   Thus, you can point to any python you want on the system if /usr/bin/python on your
system does not point to a Python 2.X interpreter.  

Some Linux operating systems, such as Arch, may only have Python 3 installed by default.  This is not sufficient and you will
get syntax errors trying to run modules with Python 3.  Python 3 is essentially not the same
language as Python 2.  Ansible modules currently need to support older Pythons for users that  still have Enterprise Linux 5 deployed, so they are not yet ported to run under Python 3.0.  This is not a problem though as you can just install Python 2 also on a managed host.

Python 3.0 support will likely be addressed at a later point in time when usage becomes more mainstream.

Do not replace the shebang lines of your python modules.  Ansible will do this for you automatically at deploy time.

.. _use_roles:

What is the best way to make content reusable/redistributable?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

If you have not done so already, read all about "Roles" in the playbooks documentation.  This helps you make playbook content
self-contained, and works well with things like git submodules for sharing content with others.

If some of these plugin types look strange to you, see the API documentation for more details about ways Ansible can be extended.

.. _configuration_file:

Where does the configuration file live and what can I configure in it?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


See :doc:`intro_configuration`.

.. _who_would_ever_want_to_disable_cowsay_but_ok_here_is_how:

How do I disable cowsay?
++++++++++++++++++++++++

If cowsay is installed, Ansible takes it upon itself to make your day happier when running playbooks.  If you decide
that you would like to work in a professional cow-free environment, you can either uninstall cowsay, or set an environment variable::

    export ANSIBLE_NOCOWS=1

.. _browse_facts:

How do I see a list of all of the ansible\_ variables?
++++++++++++++++++++++++++++++++++++++++++++++++++++++

Ansible by default gathers "facts" about the machines under management, and these facts can be accessed in Playbooks and in templates. To see a list of all of the facts that are available about a machine, you can run the "setup" module as an ad-hoc action::

    ansible -m setup hostname

This will print out a dictionary of all of the facts that are available for that particular host. You might want to pipe the output to a pager.

.. _browse_inventory_vars:

How do I see all the inventory vars defined for my host?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

You can see the resulting vars you define in inventory running the following command::

    ansible -m debug -a "var=hostvars['hostname']" localhost

.. _host_loops:

How do I loop over a list of hosts in a group, inside of a template?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

A pretty common pattern is to iterate over a list of hosts inside of a host group, perhaps to populate a template configuration
file with a list of servers. To do this, you can just access the "$groups" dictionary in your template, like this:

.. code-block:: jinja

    {% for host in groups['db_servers'] %}
        {{ host }}
    {% endfor %}

If you need to access facts about these hosts, for instance, the IP address of each hostname, you need to make sure that the facts have been populated. For example, make sure you have a play that talks to db_servers::

    - hosts:  db_servers
      tasks:
        - debug: msg="doesn't matter what you do, just that they were talked to previously."

Then you can use the facts inside your template, like this::

    {% for host in groups['db_servers'] %}
       {{ hostvars[host]['ansible_eth0']['ipv4']['address'] }}
    {% endfor %}

.. _programatic_access_to_a_variable:

How do I access a variable name programmatically?
+++++++++++++++++++++++++++++++++++++++++++++++++

An example may come up where we need to get the ipv4 address of an arbitrary interface, where the interface to be used may be supplied
via a role parameter or other input.  Variable names can be built by adding strings together, like so::

    {{ hostvars[inventory_hostname]['ansible_' + which_interface]['ipv4']['address'] }}

The trick about going through hostvars is necessary because it's a dictionary of the entire namespace of variables.  'inventory_hostname'
is a magic variable that indicates the current host you are looping over in the host loop.

.. _first_host_in_a_group:

How do I access a variable of the first host in a group?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

What happens if we want the ip address of the first webserver in the webservers group?  Well, we can do that too.  Note that if we
are using dynamic inventory, which host is the 'first' may not be consistent, so you wouldn't want to do this unless your inventory
was static and predictable.  (If you are using :doc:`tower`, it will use database order, so this isn't a problem even if you are using cloud
based inventory scripts).

Anyway, here's the trick::

    {{ hostvars[groups['webservers'][0]]['ansible_eth0']['ipv4']['address'] }}

Notice how we're pulling out the hostname of the first machine of the webservers group.  If you are doing this in a template, you
could use the Jinja2 '#set' directive to simplify this, or in a playbook, you could also use set_fact::

    - set_fact: headnode={{ groups[['webservers'][0]] }}

    - debug: msg={{ hostvars[headnode].ansible_eth0.ipv4.address }}

Notice how we interchanged the bracket syntax for dots -- that can be done anywhere.

.. _file_recursion:

How do I copy files recursively onto a target host?
+++++++++++++++++++++++++++++++++++++++++++++++++++

The "copy" module has a recursive parameter, though if you want to do something more efficient for a large number of files, take a look at the "synchronize" module instead, which wraps rsync.  See the module index for info on both of these modules.

.. _shell_env:

How do I access shell environment variables?
++++++++++++++++++++++++++++++++++++++++++++

If you just need to access existing variables, use the 'env' lookup plugin.  For example, to access the value of the HOME
environment variable on management machine::

   ---
   # ...
     vars:
        local_home: "{{ lookup('env','HOME') }}"

If you need to set environment variables, see the Advanced Playbooks section about environments.

Ansible 1.4 will also make remote environment variables available via facts in the 'ansible_env' variable::

   {{ ansible_env.SOME_VARIABLE }}

.. _user_passwords:

How do I generate crypted passwords for the user module?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The mkpasswd utility that is available on most Linux systems is a great option::

    mkpasswd --method=SHA-512

If this utility is not installed on your system (e.g. you are using OS X) then you can still easily
generate these passwords using Python. First, ensure that the `Passlib <https://code.google.com/p/passlib/>`_
password hashing library is installed.

    pip install passlib

Once the library is ready, SHA512 password values can then be generated as follows::

    python -c "from passlib.hash import sha512_crypt; import getpass; print sha512_crypt.encrypt(getpass.getpass())"

.. _commercial_support:

Can I get training on Ansible or find commercial support?
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Yes!  See our `services page <http://www.ansible.com/services>`_ for information on our services and training offerings. Support is also included with :doc:`tower`. Email `info@ansible.com <mailto:info@ansible.com>`_ for further details.

We also offer free web-based training classes on a regular basis. See our `webinar page <http://www.ansible.com/webinars-training>`_ for more info on upcoming webinars.

.. _web_interface:

Is there a web interface / REST API / etc?
++++++++++++++++++++++++++++++++++++++++++

Yes!  Ansible, Inc makes a great product that makes Ansible even more powerful
and easy to use. See :doc:`tower`.

.. _docs_contributions:

How do I submit a change to the documentation?
++++++++++++++++++++++++++++++++++++++++++++++

Great question!  Documentation for Ansible is kept in the main project git repository, and complete instructions for contributing can be found in the docs README `viewable on GitHub <https://github.com/ansible/ansible/blob/devel/docsite/README.md>`_.  Thanks!

.. _keep_secret_data:

How do I keep secret data in my playbook?
+++++++++++++++++++++++++++++++++++++++++

If you would like to keep secret data in your Ansible content and still share it publicly or keep things in source control, see :doc:`playbooks_vault`.

In Ansible 1.8 and later, if you have a task that you don't want to show the results or command given to it when using -v (verbose) mode, the following task or playbook attribute can be useful::

    - name: secret task
      shell: /usr/bin/do_something --value={{ secret_value }}
      no_log: True

This can be used to keep verbose output but hide sensitive information from others who would otherwise like to be able to see the output.

The no_log attribute can also apply to an entire play::

    - hosts: all
      no_log: True

Though this will make the play somewhat difficult to debug.  It's recommended that this
be applied to single tasks only, once a playbook is completed.


.. _when_to_use_brackets:
.. _dynamic_variables:
.. _interpolate_variables:

When should I use {{ }}? Also, how to interpolate variables or dynamic variable names
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

A steadfast rule is 'always use {{ }} except when `when:`'.
Conditionals are always run through Jinja2 as to resolve the expression,
so `when:`, `failed_when:` and `changed_when:` are always templated and you should avoid adding `{{}}`.

In most other cases you should always use the brackets, even if previouslly you could use variables without specifying (like `with_` clauses),
as this made it hard to distinguish between an undefined variable and a string.

Another rule is 'moustaches don't stack'. We often see this::

     {{ somevar_{{other_var}} }}

The above DOES NOT WORK, if you need to use a dynamic variable use the hostvars or vars dictionary as appropriate::

    {{ hostvars[inventory_hostname]['somevar_' + other_var] }}


.. _i_dont_see_my_question:

I don't see my question here
++++++++++++++++++++++++++++

Please see the section below for a link to IRC and the Google Group, where you can ask your question there.

.. seealso::

   :doc:`index`
       The documentation index
   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_best_practices`
       Best practices advice
   `User Mailing List <http://groups.google.com/group/ansible-project>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel



