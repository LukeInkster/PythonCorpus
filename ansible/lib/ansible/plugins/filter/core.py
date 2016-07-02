# (c) 2012, Jeroen Hoekx <jeroen@hoekx.be>
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


import sys
import base64
import itertools
import json
import os.path
import ntpath
import types
import pipes
import glob
import re
import crypt
import hashlib
import string
from functools import partial
import operator as py_operator
from random import SystemRandom, shuffle
import uuid

import yaml
from jinja2.filters import environmentfilter
from distutils.version import LooseVersion, StrictVersion
from ansible.compat.six import iteritems, string_types

from ansible import errors
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.utils.hashing import md5s, checksum_s
from ansible.utils.unicode import unicode_wrap, to_unicode
from ansible.utils.vars import merge_hash
from ansible.vars.hostvars import HostVars

try:
    import passlib.hash
    HAS_PASSLIB = True
except:
    HAS_PASSLIB = False


UUID_NAMESPACE_ANSIBLE = uuid.UUID('361E6D51-FAEC-444A-9079-341386DA8E2E')

class AnsibleJSONEncoder(json.JSONEncoder):
    '''
    Simple encoder class to deal with JSON encoding of internal
    types like HostVars
    '''
    def default(self, o):
        if isinstance(o, HostVars):
            return dict(o)
        else:
            return json.JSONEncoder.default(o)

def to_yaml(a, *args, **kw):
    '''Make verbose, human readable yaml'''
    transformed = yaml.dump(a, Dumper=AnsibleDumper, allow_unicode=True, **kw)
    return to_unicode(transformed)

def to_nice_yaml(a, indent=4, *args, **kw):
    '''Make verbose, human readable yaml'''
    transformed = yaml.dump(a, Dumper=AnsibleDumper, indent=indent, allow_unicode=True, default_flow_style=False, **kw)
    return to_unicode(transformed)

def to_json(a, *args, **kw):
    ''' Convert the value to JSON '''
    return json.dumps(a, cls=AnsibleJSONEncoder, *args, **kw)

def to_nice_json(a, indent=4, *args, **kw):
    '''Make verbose, human readable JSON'''
    # python-2.6's json encoder is buggy (can't encode hostvars)
    if sys.version_info < (2, 7):
        try:
            import simplejson
        except ImportError:
            pass
        else:
            try:
                major = int(simplejson.__version__.split('.')[0])
            except:
                pass
            else:
                if major >= 2:
                    return simplejson.dumps(a, indent=indent, sort_keys=True, *args, **kw)

    try:
        return json.dumps(a, indent=indent, sort_keys=True, cls=AnsibleJSONEncoder, *args, **kw)
    except:
        # Fallback to the to_json filter
        return to_json(a, *args, **kw)

def to_bool(a):
    ''' return a bool for the arg '''
    if a is None or type(a) == bool:
        return a
    if isinstance(a, string_types):
        a = a.lower()
    if a in ['yes', 'on', '1', 'true', 1]:
        return True
    else:
        return False

def quote(a):
    ''' return its argument quoted for shell usage '''
    return pipes.quote(a)

def fileglob(pathname):
    ''' return list of matched files for glob '''
    return glob.glob(pathname)

def regex_replace(value='', pattern='', replacement='', ignorecase=False):
    ''' Perform a `re.sub` returning a string '''

    if not isinstance(value, basestring):
        value = str(value)

    if ignorecase:
        flags = re.I
    else:
        flags = 0
    _re = re.compile(pattern, flags=flags)
    return _re.sub(replacement, value)

def regex_findall(value, regex, multiline=False, ignorecase=False):
    ''' Perform re.findall and return the list of matches '''
    flags = 0
    if ignorecase:
        flags |= re.I
    if multiline:
        flags |= re.M
    return re.findall(regex, value, flags)

def regex_search(value, regex, *args, **kwargs):
    ''' Perform re.search and return the list of matches or a backref '''

    groups = list()
    for arg in args:
        if arg.startswith('\\g'):
            match = re.match(r'\\g<(\S+)>', arg).group(1)
            groups.append(match)
        elif arg.startswith('\\'):
            match = int(re.match(r'\\(\d+)', arg).group(1))
            groups.append(match)
        else:
            raise errors.AnsibleFilterError('Unknown argument')

    flags = 0
    if kwargs.get('ignorecase'):
        flags |= re.I
    if kwargs.get('multiline'):
        flags |= re.M

    match = re.search(regex, value, flags)
    if match:
        if not groups:
            return match.group()
        else:
            items = list()
            for item in groups:
                items.append(match.group(item))
            return items

def ternary(value, true_val, false_val):
    '''  value ? true_val : false_val '''
    if value:
        return true_val
    else:
        return false_val


def version_compare(value, version, operator='eq', strict=False):
    ''' Perform a version comparison on a value '''
    op_map = {
        '==': 'eq', '=':  'eq', 'eq': 'eq',
        '<':  'lt', 'lt': 'lt',
        '<=': 'le', 'le': 'le',
        '>':  'gt', 'gt': 'gt',
        '>=': 'ge', 'ge': 'ge',
        '!=': 'ne', '<>': 'ne', 'ne': 'ne'
    }

    if strict:
        Version = StrictVersion
    else:
        Version = LooseVersion

    if operator in op_map:
        operator = op_map[operator]
    else:
        raise errors.AnsibleFilterError('Invalid operator type')

    try:
        method = getattr(py_operator, operator)
        return method(Version(str(value)), Version(str(version)))
    except Exception as e:
        raise errors.AnsibleFilterError('Version comparison: %s' % e)

def regex_escape(string):
    '''Escape all regular expressions special characters from STRING.'''
    return re.escape(string)

@environmentfilter
def rand(environment, end, start=None, step=None):
    r = SystemRandom()
    if isinstance(end, (int, long)):
        if not start:
            start = 0
        if not step:
            step = 1
        return r.randrange(start, end, step)
    elif hasattr(end, '__iter__'):
        if start or step:
            raise errors.AnsibleFilterError('start and step can only be used with integer values')
        return r.choice(end)
    else:
        raise errors.AnsibleFilterError('random can only be used on sequences and integers')

def randomize_list(mylist):
    try:
        mylist = list(mylist)
        shuffle(mylist)
    except:
        pass
    return mylist

def get_hash(data, hashtype='sha1'):

    try: # see if hash is supported
        h = hashlib.new(hashtype)
    except:
        return None

    h.update(data)
    return h.hexdigest()

def get_encrypted_password(password, hashtype='sha512', salt=None):

    # TODO: find a way to construct dynamically from system
    cryptmethod= {
        'md5':      '1',
        'blowfish': '2a',
        'sha256':   '5',
        'sha512':   '6',
    }

    hastype = hashtype.lower()
    if hashtype in cryptmethod:
        if salt is None:
            r = SystemRandom()
            if hashtype in ['md5']:
                saltsize = 8
            else:
                saltsize = 16
            salt = ''.join([r.choice(string.ascii_letters + string.digits) for _ in range(saltsize)])

        if not HAS_PASSLIB:
            if sys.platform.startswith('darwin'):
                raise errors.AnsibleFilterError('|password_hash requires the passlib python module to generate password hashes on Mac OS X/Darwin')
            saltstring =  "$%s$%s" % (cryptmethod[hashtype],salt)
            encrypted = crypt.crypt(password, saltstring)
        else:
            cls = getattr(passlib.hash, '%s_crypt' % hashtype)
            encrypted = cls.encrypt(password, salt=salt)

        return encrypted

    return None

def to_uuid(string):
    return str(uuid.uuid5(UUID_NAMESPACE_ANSIBLE, str(string)))

def mandatory(a):
    from jinja2.runtime import Undefined

    ''' Make a variable mandatory '''
    if isinstance(a, Undefined):
        raise errors.AnsibleFilterError('Mandatory variable not defined.')
    return a

def combine(*terms, **kwargs):
    recursive = kwargs.get('recursive', False)
    if len(kwargs) > 1 or (len(kwargs) == 1 and 'recursive' not in kwargs):
        raise errors.AnsibleFilterError("'recursive' is the only valid keyword argument")

    for t in terms:
        if not isinstance(t, dict):
            raise errors.AnsibleFilterError("|combine expects dictionaries, got " + repr(t))

    if recursive:
        return reduce(merge_hash, terms)
    else:
        return dict(itertools.chain(*map(iteritems, terms)))

def comment(text, style='plain', **kw):
    # Predefined comment types
    comment_styles = {
        'plain': {
            'decoration': '# '
        },
        'erlang': {
            'decoration': '% '
        },
        'c': {
            'decoration': '// '
        },
        'cblock': {
            'beginning': '/*',
            'decoration': ' * ',
            'end': ' */'
        },
        'xml': {
            'beginning': '<!--',
            'decoration': ' - ',
            'end': '-->'
        }
    }

    # Pointer to the right comment type
    style_params = comment_styles[style]

    if 'decoration' in kw:
        prepostfix = kw['decoration']
    else:
        prepostfix = style_params['decoration']

    # Default params
    p = {
        'newline': '\n',
        'beginning': '',
        'prefix': (prepostfix).rstrip(),
        'prefix_count': 1,
        'decoration': '',
        'postfix': (prepostfix).rstrip(),
        'postfix_count': 1,
        'end': ''
    }

    # Update default params
    p.update(style_params)
    p.update(kw)

    # Compose substrings for the final string
    str_beginning = ''
    if p['beginning']:
        str_beginning = "%s%s" % (p['beginning'], p['newline'])
    str_prefix = str(
        "%s%s" % (p['prefix'], p['newline'])) * int(p['prefix_count'])
    str_text = ("%s%s" % (
        p['decoration'],
        # Prepend each line of the text with the decorator
        text.replace(
            p['newline'], "%s%s" % (p['newline'], p['decoration'])))).replace(
                # Remove trailing spaces when only decorator is on the line
                "%s%s" % (p['decoration'], p['newline']),
                "%s%s" % (p['decoration'].rstrip(), p['newline']))
    str_postfix = p['newline'].join(
        [''] + [p['postfix'] for x in range(p['postfix_count'])])
    str_end = ''
    if p['end']:
        str_end = "%s%s" % (p['newline'], p['end'])

    # Return the final string
    return "%s%s%s%s%s" % (
        str_beginning,
        str_prefix,
        str_text,
        str_postfix,
        str_end)

def extract(item, container, morekeys=None):
    from jinja2.runtime import Undefined

    value = container[item]

    if value is not Undefined and morekeys is not None:
        if not isinstance(morekeys, list):
            morekeys = [morekeys]

        value = reduce(lambda d, k: d[k], morekeys, value)

    return value

class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            # base 64
            'b64decode': partial(unicode_wrap, base64.b64decode),
            'b64encode': partial(unicode_wrap, base64.b64encode),

            # uuid
            'to_uuid': to_uuid,

            # json
            'to_json': to_json,
            'to_nice_json': to_nice_json,
            'from_json': json.loads,

            # yaml
            'to_yaml': to_yaml,
            'to_nice_yaml': to_nice_yaml,
            'from_yaml': yaml.safe_load,

            # path
            'basename': partial(unicode_wrap, os.path.basename),
            'dirname': partial(unicode_wrap, os.path.dirname),
            'expanduser': partial(unicode_wrap, os.path.expanduser),
            'realpath': partial(unicode_wrap, os.path.realpath),
            'relpath': partial(unicode_wrap, os.path.relpath),
            'splitext': partial(unicode_wrap, os.path.splitext),
            'win_basename': partial(unicode_wrap, ntpath.basename),
            'win_dirname': partial(unicode_wrap, ntpath.dirname),
            'win_splitdrive': partial(unicode_wrap, ntpath.splitdrive),

            # value as boolean
            'bool': to_bool,

            # quote string for shell usage
            'quote': quote,

            # hash filters
            # md5 hex digest of string
            'md5': md5s,
            # sha1 hex digeset of string
            'sha1': checksum_s,
            # checksum of string as used by ansible for checksuming files
            'checksum': checksum_s,
            # generic hashing
            'password_hash': get_encrypted_password,
            'hash': get_hash,

            # file glob
            'fileglob': fileglob,

            # regex
            'regex_replace': regex_replace,
            'regex_escape': regex_escape,
            'regex_search': regex_search,
            'regex_findall': regex_findall,

            # ? : ;
            'ternary': ternary,

            # list
            # version comparison
            'version_compare': version_compare,

            # random stuff
            'random': rand,
            'shuffle': randomize_list,
            # undefined
            'mandatory': mandatory,

            # merge dicts
            'combine': combine,

            # comment-style decoration
            'comment': comment,

            # array and dict lookups
            'extract': extract,
        }
