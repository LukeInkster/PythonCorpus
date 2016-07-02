# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible import constants as C
from ansible.compat.six import string_types
from ansible.errors import AnsibleParserError, AnsibleUndefinedVariable, AnsibleFileNotFound
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject, AnsibleSequence

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def load_list_of_blocks(ds, play, parent_block=None, role=None, task_include=None, use_handlers=False, variable_manager=None, loader=None):
    '''
    Given a list of mixed task/block data (parsed from YAML),
    return a list of Block() objects, where implicit blocks
    are created for each bare Task.
    '''

    # we import here to prevent a circular dependency with imports
    from ansible.playbook.block import Block

    assert isinstance(ds, (list, type(None)))

    block_list = []
    if ds:
        for block in ds:
            b = Block.load(
                block,
                play=play,
                parent_block=parent_block,
                role=role,
                task_include=task_include,
                use_handlers=use_handlers,
                variable_manager=variable_manager,
                loader=loader
            )
            # Implicit blocks are created by bare tasks listed in a play without
            # an explicit block statement. If we have two implicit blocks in a row,
            # squash them down to a single block to save processing time later.
            if b._implicit and len(block_list) > 0 and block_list[-1]._implicit:
                for t in b.block:
                    t._block = block_list[-1]
                block_list[-1].block.extend(b.block)
            else:
                block_list.append(b)

    return block_list


def load_list_of_tasks(ds, play, block=None, role=None, task_include=None, use_handlers=False, variable_manager=None, loader=None):
    '''
    Given a list of task datastructures (parsed from YAML),
    return a list of Task() or TaskInclude() objects.
    '''

    # we import here to prevent a circular dependency with imports
    from ansible.playbook.block import Block
    from ansible.playbook.handler import Handler
    from ansible.playbook.task import Task
    from ansible.playbook.task_include import TaskInclude
    from ansible.playbook.handler_task_include import HandlerTaskInclude
    from ansible.template import Templar

    assert isinstance(ds, list)

    task_list = []
    for task_ds in ds:
        assert isinstance(task_ds, dict)

        if 'block' in task_ds:
            t = Block.load(
                task_ds,
                play=play,
                parent_block=block,
                role=role,
                task_include=None,
                use_handlers=use_handlers,
                variable_manager=variable_manager,
                loader=loader,
            )
            task_list.append(t)
        else:
            if 'include' in task_ds:
                if use_handlers:
                    t = HandlerTaskInclude.load(task_ds, block=block, role=role, task_include=task_include, variable_manager=variable_manager, loader=loader)
                else:
                    t = TaskInclude.load(task_ds, block=block, role=role, task_include=task_include, variable_manager=variable_manager, loader=loader)
                all_vars = variable_manager.get_vars(loader=loader, play=play, task=t)
                templar = Templar(loader=loader, variables=all_vars)

                # check to see if this include is dynamic or static:
                # 1. the user has set the 'static' option to false or true
                # 2. one of the appropriate config options was set
                if t.static is not None:
                    is_static = t.static
                else:
                    is_static = C.DEFAULT_TASK_INCLUDES_STATIC or \
                                (use_handlers and C.DEFAULT_HANDLER_INCLUDES_STATIC) or \
                                (not templar._contains_vars(t.args['_raw_params']) and not t.loop)

                if is_static:
                    if t.loop is not None:
                        raise AnsibleParserError("You cannot use 'static' on an include with a loop", obj=task_ds)

                    # FIXME: all of this code is very similar (if not identical) to that in
                    #        plugins/strategy/__init__.py, and should be unified to avoid
                    #        patches only being applied to one or the other location
                    if task_include:
                        # handle relative includes by walking up the list of parent include
                        # tasks and checking the relative result to see if it exists
                        parent_include = task_include
                        cumulative_path = None
                        while parent_include is not None:
                            parent_include_dir = templar.template(os.path.dirname(parent_include.args.get('_raw_params')))
                            if cumulative_path is None:
                                cumulative_path = parent_include_dir
                            elif not os.path.isabs(cumulative_path):
                                cumulative_path = os.path.join(parent_include_dir, cumulative_path)
                            include_target = templar.template(t.args['_raw_params'])
                            if t._role:
                                new_basedir = os.path.join(t._role._role_path, 'tasks', cumulative_path)
                                include_file = loader.path_dwim_relative(new_basedir, 'tasks', include_target)
                            else:
                                include_file = loader.path_dwim_relative(loader.get_basedir(), cumulative_path, include_target)

                            if os.path.exists(include_file):
                                break
                            else:
                                parent_include = parent_include._task_include
                    else:
                        try:
                            include_target = templar.template(t.args['_raw_params'])
                        except AnsibleUndefinedVariable as e:
                            raise AnsibleParserError(
                                      "Error when evaluating variable in include name: %s.\n\n" \
                                      "When using static includes, ensure that any variables used in their names are defined in vars/vars_files\n" \
                                      "or extra-vars passed in from the command line. Static includes cannot use variables from inventory\n" \
                                      "sources like group or host vars." % t.args['_raw_params'],
                                      obj=task_ds,
                                      suppress_extended_error=True,
                                  )
                        if t._role:
                            if use_handlers:
                                include_file = loader.path_dwim_relative(t._role._role_path, 'handlers', include_target)
                            else:
                                include_file = loader.path_dwim_relative(t._role._role_path, 'tasks', include_target)
                        else:
                            include_file = loader.path_dwim(include_target)

                    try:
                        data = loader.load_from_file(include_file)
                        if data is None:
                            return []
                        elif not isinstance(data, list):
                            raise AnsibleError("included task files must contain a list of tasks", obj=data)
                    except AnsibleFileNotFound as e:
                        if t.static or \
                           C.DEFAULT_TASK_INCLUDES_STATIC or \
                           C.DEFAULT_HANDLER_INCLUDES_STATIC and use_handlers:
                            raise
                        display.deprecated(
                            "Included file '%s' not found, however since this include is not " \
                            "explicitly marked as 'static: yes', we will try and include it dynamically " \
                            "later. In the future, this will be an error unless 'static: no' is used " \
                            "on the include task. If you do not want missing includes to be considered " \
                            "dynamic, use 'static: yes' on the include or set the global ansible.cfg " \
                            "options to make all inclues static for tasks and/or handlers" % include_file,
                        )
                        task_list.append(t)
                        continue

                    included_blocks = load_list_of_blocks(
                        data,
                        play=play,
                        parent_block=block,
                        task_include=t,
                        role=role,
                        use_handlers=use_handlers,
                        loader=loader,
                        variable_manager=variable_manager,
                    )

                    # pop tags out of the include args, if they were specified there, and assign
                    # them to the include. If the include already had tags specified, we raise an
                    # error so that users know not to specify them both ways
                    tags = t.vars.pop('tags', [])
                    if isinstance(tags, string_types):
                        tags = tags.split(',')

                    if len(tags) > 0:
                        if len(t.tags) > 0:
                            raise AnsibleParserError(
                                "Include tasks should not specify tags in more than one way (both via args and directly on the task)." \
                                " Mixing tag specify styles is prohibited for whole import hierarchy, not only for single import statement",
                                obj=task_ds,
                                suppress_extended_error=True,
                            )
                        display.deprecated("You should not specify tags in the include parameters. All tags should be specified using the task-level option")
                    else:
                        tags = t.tags[:]

                    # now we extend the tags on each of the included blocks
                    for b in included_blocks:
                        b.tags = list(set(b.tags).union(tags))
                    # END FIXME

                    # FIXME: send callback here somehow...
                    # FIXME: handlers shouldn't need this special handling, but do
                    #        right now because they don't iterate blocks correctly
                    if use_handlers:
                        for b in included_blocks:
                            task_list.extend(b.block)
                    else:
                        task_list.extend(included_blocks)
                else:
                    task_list.append(t)
            else:
                if use_handlers:
                    t = Handler.load(task_ds, block=block, role=role, task_include=task_include, variable_manager=variable_manager, loader=loader)
                else:
                    t = Task.load(task_ds, block=block, role=role, task_include=task_include, variable_manager=variable_manager, loader=loader)
                task_list.append(t)

    return task_list


def load_list_of_roles(ds, play, current_role_path=None, variable_manager=None, loader=None):
    '''
    Loads and returns a list of RoleInclude objects from the datastructure
    list of role definitions
    '''

    # we import here to prevent a circular dependency with imports
    from ansible.playbook.role.include import RoleInclude

    assert isinstance(ds, list)

    roles = []
    for role_def in ds:
        i = RoleInclude.load(role_def, play=play, current_role_path=current_role_path, variable_manager=variable_manager, loader=loader)
        roles.append(i)

    return roles

