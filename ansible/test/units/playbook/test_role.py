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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.playbook.block import Block
from ansible.playbook.role import Role
from ansible.playbook.role.include import RoleInclude
from ansible.playbook.task import Task

from units.mock.loader import DictDataLoader
from units.mock.path import mock_unfrackpath_noop

class TestRole(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_with_tasks(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo_tasks/tasks/main.yml": """
            - shell: echo 'hello world'
            """,
        })

        mock_play = MagicMock()
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load('foo_tasks', play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        self.assertEqual(str(r), 'foo_tasks')
        self.assertEqual(len(r._task_blocks), 1)
        assert isinstance(r._task_blocks[0], Block)

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_with_handlers(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo_handlers/handlers/main.yml": """
            - name: test handler
              shell: echo 'hello world'
            """,
        })

        mock_play = MagicMock()
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load('foo_handlers', play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        self.assertEqual(len(r._handler_blocks), 1)
        assert isinstance(r._handler_blocks[0], Block)

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_with_vars(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo_vars/defaults/main.yml": """
            foo: bar
            """,
            "/etc/ansible/roles/foo_vars/vars/main.yml": """
            foo: bam
            """,
        })

        mock_play = MagicMock()
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load('foo_vars', play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        self.assertEqual(r._default_vars, dict(foo='bar'))
        self.assertEqual(r._role_vars, dict(foo='bam'))

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_with_metadata(self):

        fake_loader = DictDataLoader({
            '/etc/ansible/roles/foo_metadata/meta/main.yml': """
                allow_duplicates: true
                dependencies:
                  - bar_metadata
                galaxy_info:
                  a: 1
                  b: 2
                  c: 3
            """,
            '/etc/ansible/roles/bar_metadata/meta/main.yml': """
                dependencies:
                  - baz_metadata
            """,
            '/etc/ansible/roles/baz_metadata/meta/main.yml': """
                dependencies:
                  - bam_metadata
            """,
            '/etc/ansible/roles/bam_metadata/meta/main.yml': """
                dependencies: []
            """,
            '/etc/ansible/roles/bad1_metadata/meta/main.yml': """
                1
            """,
            '/etc/ansible/roles/bad2_metadata/meta/main.yml': """
                foo: bar
            """,
            '/etc/ansible/roles/recursive1_metadata/meta/main.yml': """
                dependencies: ['recursive2_metadata']
            """,
            '/etc/ansible/roles/recursive2_metadata/meta/main.yml': """
                dependencies: ['recursive1_metadata']
            """,
        })

        mock_play = MagicMock()
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load('foo_metadata', play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        role_deps = r.get_direct_dependencies()

        self.assertEqual(len(role_deps), 1)
        self.assertEqual(type(role_deps[0]), Role)
        self.assertEqual(len(role_deps[0].get_parents()), 1)
        self.assertEqual(role_deps[0].get_parents()[0], r)
        self.assertEqual(r._metadata.allow_duplicates, True)
        self.assertEqual(r._metadata.galaxy_info, dict(a=1, b=2, c=3))

        all_deps = r.get_all_dependencies()
        self.assertEqual(len(all_deps), 3)
        self.assertEqual(all_deps[0].get_name(), 'bam_metadata')
        self.assertEqual(all_deps[1].get_name(), 'baz_metadata')
        self.assertEqual(all_deps[2].get_name(), 'bar_metadata')

        i = RoleInclude.load('bad1_metadata', play=mock_play, loader=fake_loader)
        self.assertRaises(AnsibleParserError, Role.load, i, play=mock_play)

        i = RoleInclude.load('bad2_metadata', play=mock_play, loader=fake_loader)
        self.assertRaises(AnsibleParserError, Role.load, i, play=mock_play)

        i = RoleInclude.load('recursive1_metadata', play=mock_play, loader=fake_loader)
        self.assertRaises(AnsibleError, Role.load, i, play=mock_play)

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_complex(self):

        # FIXME: add tests for the more complex uses of
        #        params and tags/when statements

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo_complex/tasks/main.yml": """
            - shell: echo 'hello world'
            """,
        })

        mock_play = MagicMock()
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load(dict(role='foo_complex'), play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        self.assertEqual(r.get_name(), "foo_complex")

