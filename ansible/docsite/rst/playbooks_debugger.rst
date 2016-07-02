Playbook Debugger
=================

.. contents:: Topics

In 2.1 we added a ``debug`` strategy. This strategy enables you to invoke a debugger when a task is
failed, and check several info, such as the value of a variable. Also, it is possible to update module
arguments in the debugger, and run the failed task again with new arguments to consider how you
can fix an issue.

To use ``debug`` strategy, change ``strategy`` attribute like this::

    - hosts: test
      strategy: debug
      tasks:
      ...

For example, run the playbook below::

    - hosts: test
      strategy: debug
      gather_facts: no
      vars:
        var1: value1
      tasks:
        - name: wrong variable
          ping: data={{ wrong_var }}

The debugger is invoked since *wrong_var* variable is undefined. Let's change the module's args,
and run the task again::

    PLAY ***************************************************************************

    TASK [wrong variable] **********************************************************
    fatal: [192.168.1.1]: FAILED! => {"failed": true, "msg": "ERROR! 'wrong_var' is undefined"}
    Debugger invoked
    (debug) p result
    {'msg': u"ERROR! 'wrong_var' is undefined", 'failed': True}
    (debug) p task.args
    {u'data': u'{{ wrong_var }}'}
    (debug) task.args['data'] = '{{ var1 }}'
    (debug) p task.args
    {u'data': '{{ var1 }}'}
    (debug) redo
    ok: [192.168.1.1]

    PLAY RECAP *********************************************************************
    192.168.1.1               : ok=1    changed=0    unreachable=0    failed=0

This time, the task runs successfully!

.. _available_commands:

Available Commands
++++++++++++++++++

.. _p_command:

p *task/vars/host/result*
`````````````````````````

Print values used to execute a module::

    (debug) p task
    TASK: install package
    (debug) p task.args
    {u'name': u'{{ pkg_name }}'}
    (debug) p vars
    {u'ansible_all_ipv4_addresses': [u'192.168.1.1'],
     u'ansible_architecture': u'x86_64',
     ...
    }
    (debug) p vars['pkg_name']
    u'bash'
    (debug) p host
    192.168.1.1
    (debug) p result
    {'_ansible_no_log': False,
     'changed': False,
     u'failed': True,
     ...
     u'msg': u"No package matching 'not_exist' is available"}

.. _update_args_command:

task.args[*key*] = *value*
``````````````````````````

Update module's argument.

If you run a playbook like this::

    - hosts: test
      strategy: debug
      gather_facts: yes
      vars:
        pkg_name: not_exist
      tasks:
        - name: install package
          apt: name={{ pkg_name }}

Debugger is invoked due to wrong package name, so let's fix the module's args::

    (debug) p task.args
    {u'name': u'{{ pkg_name }}'}
    (debug) task.args['name'] = 'bash'
    (debug) p task.args
    {u'name': 'bash'}
    (debug) redo

Then the task runs again with new args.

.. _update_vars_command:

vars[*key*] = *value*
`````````````````````

Update vars.

Let's use the same playbook above, but fix vars instead of args::

    (debug) p vars['pkg_name']
    u'not_exist'
    (debug) vars['pkg_name'] = 'bash'
    (debug) p vars['pkg_name']
    'bash'
    (debug) redo

Then the task runs again with new vars.

.. _redo_command:

r(edo)
``````

Run the task again.

.. _continue_command:

c(ontinue)
``````````

Just continue.

.. _quit_command:

q(uit)
``````

Quit from the debugger. The playbook execution is aborted.

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
