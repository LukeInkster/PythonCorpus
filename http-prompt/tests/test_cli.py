import os

from click.testing import CliRunner
from mock import patch, DEFAULT

from .base import TempAppDirTestCase
from http_prompt import xdg
from http_prompt.cli import cli, execute


def run_and_exit(cli_args=None, prompt_commands=None):
    """Run http-prompt executable, execute some prompt commands, and exit."""
    if cli_args is None:
        cli_args = []

    # Make sure last command is 'exit'
    if prompt_commands is None:
        prompt_commands = ['exit']
    else:
        prompt_commands += ['exit']

    with patch.multiple('http_prompt.cli',
                        prompt=DEFAULT, execute=DEFAULT) as mocks:
        mocks['execute'].side_effect = execute

        # prompt() is mocked to return the command in 'prompt_commands' in
        # sequence, i.e., prompt() returns prompt_commands[i-1] when it is
        # called for the ith time
        mocks['prompt'].side_effect = prompt_commands

        result = CliRunner().invoke(cli, cli_args)
        context = mocks['execute'].call_args[0][1]

    return result, context


class TestCli(TempAppDirTestCase):

    def test_without_args(self):
        result, context = run_and_exit(['http://localhost'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://localhost')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {})

    def test_incomplete_url1(self):
        result, context = run_and_exit(['://example.com'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {})

    def test_incomplete_url2(self):
        result, context = run_and_exit(['//example.com'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {})

    def test_incomplete_url3(self):
        result, context = run_and_exit(['example.com'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {})

    def test_httpie_oprions(self):
        url = 'http://example.com'
        custom_args = '--auth value: name=foo'
        result, context = run_and_exit([url] + custom_args.split())
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {'--auth': 'value:'})
        self.assertEqual(context.body_params, {'name': 'foo'})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {})

    def test_persistent_context(self):
        result, context = run_and_exit(['//example.com', 'name=bob', 'id==10'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {'name': 'bob'})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {'id': '10'})

        result, context = run_and_exit(['//example.com', 'sex=M'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {'name': 'bob', 'sex': 'M'})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {'id': '10'})

    def test_config_file(self):
        # Config file is not there at the beginning
        config_path = os.path.join(xdg.get_config_dir(), 'config.py')
        self.assertFalse(os.path.exists(config_path))

        # After user runs it for the first time, a default config file should
        # be created
        result, context = run_and_exit(['//example.com'])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists(config_path))

    def test_base_url_changed(self):
        result, context = run_and_exit(['example.com', 'name=bob', 'id==10'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {'name': 'bob'})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {'id': '10'})

        # Changing hostname should trigger a context reload
        result, context = run_and_exit(['localhost'],
                                       ['cd http://example.com/api'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com/api')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {'name': 'bob'})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {'id': '10'})

    def test_cli_arguments_with_spaces(self):
        result, context = run_and_exit(['example.com', "name=John Doe",
                                        "Authorization:Bearer API KEY"])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.querystring_params, {})
        self.assertEqual(context.body_params, {'name': 'John Doe'})
        self.assertEqual(context.headers, {'Authorization': 'Bearer API KEY'})

    @patch('http_prompt.cli.prompt')
    @patch('http_prompt.cli.execute')
    def test_press_ctrl_d(self, execute_mock, prompt_mock):
        prompt_mock.side_effect = EOFError
        execute_mock.side_effect = execute
        result = CliRunner().invoke(cli, [])
        self.assertEqual(result.exit_code, 0)
