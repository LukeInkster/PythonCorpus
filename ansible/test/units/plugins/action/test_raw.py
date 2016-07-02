# (c) 2016, Saran Ahluwalia <ahlusar.ahluwalia@gmail.com>
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


from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock, Mock
from ansible.plugins.action.raw import ActionModule
from ansible.playbook.task import Task

class TestCopyResultExclude(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # The current behavior of the raw aciton in regards to executable is currently in question; 
    # the test_raw_executable_is_not_empty_string verifies the current behavior (whether it is desireed or not. 
    # Please refer to the following for context:
    # Issue: https://github.com/ansible/ansible/issues/16054
    # PR: https://github.com/ansible/ansible/pull/16085


    def test_raw_executable_is_not_empty_string(self):

        play_context = Mock()
        task = MagicMock(Task)
        task.async = MagicMock()
        connection = Mock()

        task.args = {'_raw_params': 'Args1'}
        play_context.check_mode = False

        self.mock_am = ActionModule(task, connection, play_context, loader=None, templar=None, shared_loader_obj=None)
        self.mock_am._low_level_execute_command = Mock(return_value = {})
        self.mock_am.display = Mock()

        self.mock_am.run()
        self.mock_am._low_level_execute_command.assert_called_with('Args1', executable=False)

    def test_raw_check_mode_is_True(self):

        play_context = Mock()
        task = MagicMock(Task)
        task.async = MagicMock()
        connection = Mock()

        task.args = {'_raw_params': 'Args1'}
        play_context.check_mode = True

        self.mock_am = ActionModule(task, connection, play_context, loader=None, templar=None, shared_loader_obj=None)
        self.mock_am._low_level_execute_command = Mock(return_value = {})
        self.mock_am.display = Mock()

        skipped_result = self.mock_am.run()

        self.assertEqual(skipped_result.get('skipped'), True)

    def test_raw_test_environment_is_None(self):

        play_context = Mock()
        task = MagicMock(Task)
        task.async = MagicMock()
        connection = Mock()

        task.args = {'_raw_params': 'Args1'}
        task.environment = None
        play_context.check_mode = False

        self.mock_am = ActionModule(task, connection, play_context, loader=None, templar=None, shared_loader_obj=None)
        self.mock_am._low_level_execute_command = Mock(return_value = {})
        self.mock_am.display = Mock()

        self.assertEqual(task.environment, None)

    def test_raw_task_vars_is_not_None(self):

        play_context = Mock()
        task = MagicMock(Task)
        task.async = MagicMock()
        connection = Mock()

        task.args = {'_raw_params': 'Args1'}
        task.environment = None
        play_context.check_mode = False

        self.mock_am = ActionModule(task, connection, play_context, loader=None, templar=None, shared_loader_obj=None)
        self.mock_am._low_level_execute_command = Mock(return_value = {})
        self.mock_am.display = Mock()

        self.mock_am.run(task_vars={'a': 'b'})
        self.assertEqual(task.environment, None)


