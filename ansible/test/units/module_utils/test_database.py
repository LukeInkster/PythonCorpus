import collections
import mock
import os
import re

from nose.tools import eq_
try:
    from nose.tools import assert_raises_regexp
except ImportError:
    # Python < 2.7
    def assert_raises_regexp(expected, regexp, callable, *a, **kw):
        try:
            callable(*a, **kw)
        except expected as e:
            if isinstance(regexp, basestring):
                regexp = re.compile(regexp)
            if not regexp.search(str(e)):
                raise Exception('"%s" does not match "%s"' %
                                (regexp.pattern, str(e)))
        else:
            if hasattr(expected,'__name__'): excName = expected.__name__
            else: excName = str(expected)
            raise AssertionError("%s not raised" % excName)

from ansible.module_utils.database import (
    pg_quote_identifier,
    SQLParseError,
)


# Note: Using nose's generator test cases here so we can't inherit from
# unittest.TestCase
class TestQuotePgIdentifier(object):

    # These are all valid strings
    # The results are based on interpreting the identifier as a table name
    valid = {
        # User quoted
        '"public.table"': '"public.table"',
        '"public"."table"': '"public"."table"',
        '"schema test"."table test"': '"schema test"."table test"',

        # We quote part
        'public.table': '"public"."table"',
        '"public".table': '"public"."table"',
        'public."table"': '"public"."table"',
        'schema test.table test': '"schema test"."table test"',
        '"schema test".table test': '"schema test"."table test"',
        'schema test."table test"': '"schema test"."table test"',

        # Embedded double quotes
        'table "test"': '"table ""test"""',
        'public."table ""test"""': '"public"."table ""test"""',
        'public.table "test"': '"public"."table ""test"""',
        'schema "test".table': '"schema ""test"""."table"',
        '"schema ""test""".table': '"schema ""test"""."table"',
        '"""wat"""."""test"""': '"""wat"""."""test"""',
        # Sigh, handle these as well:
        '"no end quote': '"""no end quote"',
        'schema."table': '"schema"."""table"',
        '"schema.table': '"""schema"."table"',
        'schema."table.something': '"schema"."""table"."something"',

        # Embedded dots
        '"schema.test"."table.test"': '"schema.test"."table.test"',
        '"schema.".table': '"schema."."table"',
        '"schema."."table"': '"schema."."table"',
        'schema.".table"': '"schema".".table"',
        '"schema".".table"': '"schema".".table"',
        '"schema.".".table"': '"schema.".".table"',
        # These are valid but maybe not what the user intended
        '."table"': '".""table"""',
        'table.': '"table."',
    }

    invalid = {
        ('test.too.many.dots', 'table'): 'PostgreSQL does not support table with more than 3 dots',
        ('"test.too".many.dots', 'database'): 'PostgreSQL does not support database with more than 1 dots',
        ('test.too."many.dots"', 'database'): 'PostgreSQL does not support database with more than 1 dots',
        ('"test"."too"."many"."dots"', 'database'): "PostgreSQL does not support database with more than 1 dots",
        ('"test"."too"."many"."dots"', 'schema'): "PostgreSQL does not support schema with more than 2 dots",
        ('"test"."too"."many"."dots"', 'table'): "PostgreSQL does not support table with more than 3 dots",
        ('"test"."too"."many"."dots"."for"."column"', 'column'): "PostgreSQL does not support column with more than 4 dots",
        ('"table "invalid" double quote"', 'table'): 'User escaped identifiers must escape extra quotes',
        ('"schema "invalid"""."table "invalid"', 'table'): 'User escaped identifiers must escape extra quotes',
        ('"schema."table"','table'): 'User escaped identifiers must escape extra quotes',
        ('"schema".', 'table'): 'Identifier name unspecified or unquoted trailing dot',
    }

    def check_valid_quotes(self, identifier, quoted_identifier):
        eq_(pg_quote_identifier(identifier, 'table'), quoted_identifier)

    def test_valid_quotes(self):
        for identifier in self.valid:
            yield self.check_valid_quotes, identifier, self.valid[identifier]

    def check_invalid_quotes(self, identifier, id_type, msg):
        assert_raises_regexp(SQLParseError, msg, pg_quote_identifier, *(identifier, id_type))

    def test_invalid_quotes(self):
        for test in self.invalid:
            yield self.check_invalid_quotes, test[0], test[1], self.invalid[test]

    def test_how_many_dots(self):
        eq_(pg_quote_identifier('role', 'role'), '"role"')
        assert_raises_regexp(SQLParseError, "PostgreSQL does not support role with more than 1 dots", pg_quote_identifier, *('role.more', 'role'))

        eq_(pg_quote_identifier('db', 'database'), '"db"')
        assert_raises_regexp(SQLParseError, "PostgreSQL does not support database with more than 1 dots", pg_quote_identifier, *('db.more', 'database'))

        eq_(pg_quote_identifier('db.schema', 'schema'), '"db"."schema"')
        assert_raises_regexp(SQLParseError, "PostgreSQL does not support schema with more than 2 dots", pg_quote_identifier, *('db.schema.more', 'schema'))

        eq_(pg_quote_identifier('db.schema.table', 'table'), '"db"."schema"."table"')
        assert_raises_regexp(SQLParseError, "PostgreSQL does not support table with more than 3 dots", pg_quote_identifier, *('db.schema.table.more', 'table'))

        eq_(pg_quote_identifier('db.schema.table.column', 'column'), '"db"."schema"."table"."column"')
        assert_raises_regexp(SQLParseError, "PostgreSQL does not support column with more than 4 dots", pg_quote_identifier, *('db.schema.table.column.more', 'column'))
