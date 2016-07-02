# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2013, Dylan Martin <dmartin@seattlecentral.edu>
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

from ansible.plugins.action import ActionBase
from ansible.utils.boolean import boolean
from ansible.errors import AnsibleError
from ansible.utils.unicode import to_str

class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def run(self, tmp=None, task_vars=None):
        ''' handler for unarchive operations '''
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        source  = self._task.args.get('src', None)
        dest    = self._task.args.get('dest', None)
        copy    = boolean(self._task.args.get('copy', True))
        creates = self._task.args.get('creates', None)

        if source is None or dest is None:
            result['failed'] = True
            result['msg'] = "src (or content) and dest are required"
            return result

        remote_user = task_vars.get('ansible_ssh_user') or self._play_context.remote_user
        if not tmp:
            tmp = self._make_tmp_path(remote_user)
            self._cleanup_remote_tmp = True

        if creates:
            # do not run the command if the line contains creates=filename
            # and the filename already exists. This allows idempotence
            # of command executions.
            result = self._execute_module(module_name='stat', module_args=dict(path=creates), task_vars=task_vars)
            stat = result.get('stat', None)
            if stat and stat.get('exists', False):
                result['skipped'] = True
                result['msg'] = "skipped, since %s exists" % creates
                self._remove_tmp_path(tmp)
                return result

        dest = self._remote_expand_user(dest) # CCTODO: Fix path for Windows hosts.
        source = os.path.expanduser(source)

        if copy:
            try:
                source = self._find_needle('files', source)
            except AnsibleError as e:
                result['failed'] = True
                result['msg'] = to_str(e)
                self._remove_tmp_path(tmp)
                return result

        remote_checksum = self._remote_checksum(dest, all_vars=task_vars, follow=True)
        if remote_checksum == '4':
            result['failed'] = True
            result['msg'] = "python isn't present on the system.  Unable to compute checksum"
            self._remove_tmp_path(tmp)
            return result
        elif remote_checksum != '3':
            result['failed'] = True
            result['msg'] = "dest '%s' must be an existing dir" % dest
            self._remove_tmp_path(tmp)
            return result

        if copy:
            # transfer the file to a remote tmp location
            tmp_src = self._connection._shell.join_path(tmp, 'source')
            self._transfer_file(source, tmp_src)

        # handle diff mode client side
        # handle check mode client side

        if copy:
            # fix file permissions when the copy is done as a different user
            self._fixup_perms(tmp, remote_user, recursive=True)
            # Build temporary module_args.
            new_module_args = self._task.args.copy()
            new_module_args.update(
                dict(
                    src=tmp_src,
                    original_basename=os.path.basename(source),
                ),
            )

        else:
            new_module_args = self._task.args.copy()
            new_module_args.update(
                dict(
                    original_basename=os.path.basename(source),
                ),
            )

        # execute the unarchive module now, with the updated args
        result.update(self._execute_module(module_args=new_module_args, task_vars=task_vars))
        self._remove_tmp_path(tmp)
        return result
