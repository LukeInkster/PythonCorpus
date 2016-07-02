Introduction
============

Modules (also referred to as "task plugins" or "library plugins") are the ones that do
the actual work in ansible, they are what gets executed in each playbook task.
But you can also run a single one using the 'ansible' command.

Let's review how we execute three different modules from the command line::

    ansible webservers -m service -a "name=httpd state=started"
    ansible webservers -m ping
    ansible webservers -m command -a "/sbin/reboot -t now"

Each module supports taking arguments.  Nearly all modules take ``key=value``
arguments, space delimited.  Some modules take no arguments, and the command/shell modules simply
take the string of the command you want to run.

From playbooks, Ansible modules are executed in a very similar way::

    - name: reboot the servers
      action: command /sbin/reboot -t now

Which can be abbreviated to::

    - name: reboot the servers
      command: /sbin/reboot -t now

Another way to pass arguments to a module is using yaml syntax also called 'complex args' ::

    - name: restart webserver
      service:
        name: httpd
        state: restarted

All modules technically return JSON format data, though if you are using the command line or playbooks, you don't really need to know much about
that.  If you're writing your own module, you care, and this means you do not have to write modules in any particular language -- you get to choose.

Modules strive to be `idempotent`, meaning they will seek to avoid changes to the system unless a change needs to be made.  When using Ansible
playbooks, these modules can trigger 'change events' in the form of notifying 'handlers' to run additional tasks.

Documentation for each module can be accessed from the command line with the ansible-doc tool::

    ansible-doc yum

A list of all installed modules is also available::

    ansible-doc -l


.. seealso::

   :doc:`intro_adhoc`
       Examples of using modules in /usr/bin/ansible
   :doc:`playbooks`
       Examples of using modules with /usr/bin/ansible-playbook
   :doc:`developing_modules`
       How to write your own modules
   :doc:`developing_api`
       Examples of using modules with the Python API
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

