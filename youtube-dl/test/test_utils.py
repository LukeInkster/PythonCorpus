#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Various small unit tests
import io
import json
import xml.etree.ElementTree

from youtube_dl.utils import (
    age_restricted,
    args_to_str,
    encode_base_n,
    clean_html,
    date_from_str,
    DateRange,
    detect_exe_version,
    determine_ext,
    dict_get,
    encode_compat_str,
    encodeFilename,
    escape_rfc3986,
    escape_url,
    extract_attributes,
    ExtractorError,
    find_xpath_attr,
    fix_xml_ampersands,
    InAdvancePagedList,
    intlist_to_bytes,
    is_html,
    js_to_json,
    limit_length,
    ohdave_rsa_encrypt,
    OnDemandPagedList,
    orderedSet,
    parse_duration,
    parse_filesize,
    parse_count,
    parse_iso8601,
    read_batch_urls,
    sanitize_filename,
    sanitize_path,
    prepend_extension,
    replace_extension,
    remove_start,
    remove_end,
    remove_quotes,
    shell_quote,
    smuggle_url,
    str_to_int,
    strip_jsonp,
    timeconvert,
    unescapeHTML,
    unified_strdate,
    unified_timestamp,
    unsmuggle_url,
    uppercase_escape,
    lowercase_escape,
    url_basename,
    urlencode_postdata,
    urshift,
    update_url_query,
    version_tuple,
    xpath_with_ns,
    xpath_element,
    xpath_text,
    xpath_attr,
    render_table,
    match_str,
    parse_dfxp_time_expr,
    dfxp2srt,
    cli_option,
    cli_valueless_option,
    cli_bool_option,
)
from youtube_dl.compat import (
    compat_chr,
    compat_etree_fromstring,
    compat_urlparse,
    compat_parse_qs,
)


class TestUtil(unittest.TestCase):
    def test_timeconvert(self):
        self.assertTrue(timeconvert('') is None)
        self.assertTrue(timeconvert('bougrg') is None)

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename('abc'), 'abc')
        self.assertEqual(sanitize_filename('abc_d-e'), 'abc_d-e')

        self.assertEqual(sanitize_filename('123'), '123')

        self.assertEqual('abc_de', sanitize_filename('abc/de'))
        self.assertFalse('/' in sanitize_filename('abc/de///'))

        self.assertEqual('abc_de', sanitize_filename('abc/<>\\*|de'))
        self.assertEqual('xxx', sanitize_filename('xxx/<>\\*|'))
        self.assertEqual('yes no', sanitize_filename('yes? no'))
        self.assertEqual('this - that', sanitize_filename('this: that'))

        self.assertEqual(sanitize_filename('AT&T'), 'AT&T')
        aumlaut = 'ä'
        self.assertEqual(sanitize_filename(aumlaut), aumlaut)
        tests = '\u043a\u0438\u0440\u0438\u043b\u043b\u0438\u0446\u0430'
        self.assertEqual(sanitize_filename(tests), tests)

        self.assertEqual(
            sanitize_filename('New World record at 0:12:34'),
            'New World record at 0_12_34')

        self.assertEqual(sanitize_filename('--gasdgf'), '_-gasdgf')
        self.assertEqual(sanitize_filename('--gasdgf', is_id=True), '--gasdgf')
        self.assertEqual(sanitize_filename('.gasdgf'), 'gasdgf')
        self.assertEqual(sanitize_filename('.gasdgf', is_id=True), '.gasdgf')

        forbidden = '"\0\\/'
        for fc in forbidden:
            for fbc in forbidden:
                self.assertTrue(fbc not in sanitize_filename(fc))

    def test_sanitize_filename_restricted(self):
        self.assertEqual(sanitize_filename('abc', restricted=True), 'abc')
        self.assertEqual(sanitize_filename('abc_d-e', restricted=True), 'abc_d-e')

        self.assertEqual(sanitize_filename('123', restricted=True), '123')

        self.assertEqual('abc_de', sanitize_filename('abc/de', restricted=True))
        self.assertFalse('/' in sanitize_filename('abc/de///', restricted=True))

        self.assertEqual('abc_de', sanitize_filename('abc/<>\\*|de', restricted=True))
        self.assertEqual('xxx', sanitize_filename('xxx/<>\\*|', restricted=True))
        self.assertEqual('yes_no', sanitize_filename('yes? no', restricted=True))
        self.assertEqual('this_-_that', sanitize_filename('this: that', restricted=True))

        tests = 'aäb\u4e2d\u56fd\u7684c'
        self.assertEqual(sanitize_filename(tests, restricted=True), 'aab_c')
        self.assertTrue(sanitize_filename('\xf6', restricted=True) != '')  # No empty filename

        forbidden = '"\0\\/&!: \'\t\n()[]{}$;`^,#'
        for fc in forbidden:
            for fbc in forbidden:
                self.assertTrue(fbc not in sanitize_filename(fc, restricted=True))

        # Handle a common case more neatly
        self.assertEqual(sanitize_filename('\u5927\u58f0\u5e26 - Song', restricted=True), 'Song')
        self.assertEqual(sanitize_filename('\u603b\u7edf: Speech', restricted=True), 'Speech')
        # .. but make sure the file name is never empty
        self.assertTrue(sanitize_filename('-', restricted=True) != '')
        self.assertTrue(sanitize_filename(':', restricted=True) != '')

        self.assertEqual(sanitize_filename(
            'ÂÃÄÀÁÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖŐØŒÙÚÛÜŰÝÞßàáâãäåæçèéêëìíîïðñòóôõöőøœùúûüűýþÿ', restricted=True),
            'AAAAAAAECEEEEIIIIDNOOOOOOOOEUUUUUYPssaaaaaaaeceeeeiiiionooooooooeuuuuuypy')

    def test_sanitize_ids(self):
        self.assertEqual(sanitize_filename('_n_cd26wFpw', is_id=True), '_n_cd26wFpw')
        self.assertEqual(sanitize_filename('_BD_eEpuzXw', is_id=True), '_BD_eEpuzXw')
        self.assertEqual(sanitize_filename('N0Y__7-UOdI', is_id=True), 'N0Y__7-UOdI')

    def test_sanitize_path(self):
        if sys.platform != 'win32':
            return

        self.assertEqual(sanitize_path('abc'), 'abc')
        self.assertEqual(sanitize_path('abc/def'), 'abc\\def')
        self.assertEqual(sanitize_path('abc\\def'), 'abc\\def')
        self.assertEqual(sanitize_path('abc|def'), 'abc#def')
        self.assertEqual(sanitize_path('<>:"|?*'), '#######')
        self.assertEqual(sanitize_path('C:/abc/def'), 'C:\\abc\\def')
        self.assertEqual(sanitize_path('C?:/abc/def'), 'C##\\abc\\def')

        self.assertEqual(sanitize_path('\\\\?\\UNC\\ComputerName\\abc'), '\\\\?\\UNC\\ComputerName\\abc')
        self.assertEqual(sanitize_path('\\\\?\\UNC/ComputerName/abc'), '\\\\?\\UNC\\ComputerName\\abc')

        self.assertEqual(sanitize_path('\\\\?\\C:\\abc'), '\\\\?\\C:\\abc')
        self.assertEqual(sanitize_path('\\\\?\\C:/abc'), '\\\\?\\C:\\abc')
        self.assertEqual(sanitize_path('\\\\?\\C:\\ab?c\\de:f'), '\\\\?\\C:\\ab#c\\de#f')
        self.assertEqual(sanitize_path('\\\\?\\C:\\abc'), '\\\\?\\C:\\abc')

        self.assertEqual(
            sanitize_path('youtube/%(uploader)s/%(autonumber)s-%(title)s-%(upload_date)s.%(ext)s'),
            'youtube\\%(uploader)s\\%(autonumber)s-%(title)s-%(upload_date)s.%(ext)s')

        self.assertEqual(
            sanitize_path('youtube/TheWreckingYard ./00001-Not bad, Especially for Free! (1987 Yamaha 700)-20141116.mp4.part'),
            'youtube\\TheWreckingYard #\\00001-Not bad, Especially for Free! (1987 Yamaha 700)-20141116.mp4.part')
        self.assertEqual(sanitize_path('abc/def...'), 'abc\\def..#')
        self.assertEqual(sanitize_path('abc.../def'), 'abc..#\\def')
        self.assertEqual(sanitize_path('abc.../def...'), 'abc..#\\def..#')

        self.assertEqual(sanitize_path('../abc'), '..\\abc')
        self.assertEqual(sanitize_path('../../abc'), '..\\..\\abc')
        self.assertEqual(sanitize_path('./abc'), 'abc')
        self.assertEqual(sanitize_path('./../abc'), '..\\abc')

    def test_prepend_extension(self):
        self.assertEqual(prepend_extension('abc.ext', 'temp'), 'abc.temp.ext')
        self.assertEqual(prepend_extension('abc.ext', 'temp', 'ext'), 'abc.temp.ext')
        self.assertEqual(prepend_extension('abc.unexpected_ext', 'temp', 'ext'), 'abc.unexpected_ext.temp')
        self.assertEqual(prepend_extension('abc', 'temp'), 'abc.temp')
        self.assertEqual(prepend_extension('.abc', 'temp'), '.abc.temp')
        self.assertEqual(prepend_extension('.abc.ext', 'temp'), '.abc.temp.ext')

    def test_replace_extension(self):
        self.assertEqual(replace_extension('abc.ext', 'temp'), 'abc.temp')
        self.assertEqual(replace_extension('abc.ext', 'temp', 'ext'), 'abc.temp')
        self.assertEqual(replace_extension('abc.unexpected_ext', 'temp', 'ext'), 'abc.unexpected_ext.temp')
        self.assertEqual(replace_extension('abc', 'temp'), 'abc.temp')
        self.assertEqual(replace_extension('.abc', 'temp'), '.abc.temp')
        self.assertEqual(replace_extension('.abc.ext', 'temp'), '.abc.temp')

    def test_remove_start(self):
        self.assertEqual(remove_start(None, 'A - '), None)
        self.assertEqual(remove_start('A - B', 'A - '), 'B')
        self.assertEqual(remove_start('B - A', 'A - '), 'B - A')

    def test_remove_end(self):
        self.assertEqual(remove_end(None, ' - B'), None)
        self.assertEqual(remove_end('A - B', ' - B'), 'A')
        self.assertEqual(remove_end('B - A', ' - B'), 'B - A')

    def test_remove_quotes(self):
        self.assertEqual(remove_quotes(None), None)
        self.assertEqual(remove_quotes('"'), '"')
        self.assertEqual(remove_quotes("'"), "'")
        self.assertEqual(remove_quotes(';'), ';')
        self.assertEqual(remove_quotes('";'), '";')
        self.assertEqual(remove_quotes('""'), '')
        self.assertEqual(remove_quotes('";"'), ';')

    def test_ordered_set(self):
        self.assertEqual(orderedSet([1, 1, 2, 3, 4, 4, 5, 6, 7, 3, 5]), [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(orderedSet([]), [])
        self.assertEqual(orderedSet([1]), [1])
        # keep the list ordered
        self.assertEqual(orderedSet([135, 1, 1, 1]), [135, 1])

    def test_unescape_html(self):
        self.assertEqual(unescapeHTML('%20;'), '%20;')
        self.assertEqual(unescapeHTML('&#x2F;'), '/')
        self.assertEqual(unescapeHTML('&#47;'), '/')
        self.assertEqual(unescapeHTML('&eacute;'), 'é')
        self.assertEqual(unescapeHTML('&#2013266066;'), '&#2013266066;')
        # HTML5 entities
        self.assertEqual(unescapeHTML('&period;&apos;'), '.\'')

    def test_date_from_str(self):
        self.assertEqual(date_from_str('yesterday'), date_from_str('now-1day'))
        self.assertEqual(date_from_str('now+7day'), date_from_str('now+1week'))
        self.assertEqual(date_from_str('now+14day'), date_from_str('now+2week'))
        self.assertEqual(date_from_str('now+365day'), date_from_str('now+1year'))
        self.assertEqual(date_from_str('now+30day'), date_from_str('now+1month'))

    def test_daterange(self):
        _20century = DateRange("19000101", "20000101")
        self.assertFalse("17890714" in _20century)
        _ac = DateRange("00010101")
        self.assertTrue("19690721" in _ac)
        _firstmilenium = DateRange(end="10000101")
        self.assertTrue("07110427" in _firstmilenium)

    def test_unified_dates(self):
        self.assertEqual(unified_strdate('December 21, 2010'), '20101221')
        self.assertEqual(unified_strdate('8/7/2009'), '20090708')
        self.assertEqual(unified_strdate('Dec 14, 2012'), '20121214')
        self.assertEqual(unified_strdate('2012/10/11 01:56:38 +0000'), '20121011')
        self.assertEqual(unified_strdate('1968 12 10'), '19681210')
        self.assertEqual(unified_strdate('1968-12-10'), '19681210')
        self.assertEqual(unified_strdate('28/01/2014 21:00:00 +0100'), '20140128')
        self.assertEqual(
            unified_strdate('11/26/2014 11:30:00 AM PST', day_first=False),
            '20141126')
        self.assertEqual(
            unified_strdate('2/2/2015 6:47:40 PM', day_first=False),
            '20150202')
        self.assertEqual(unified_strdate('Feb 14th 2016 5:45PM'), '20160214')
        self.assertEqual(unified_strdate('25-09-2014'), '20140925')
        self.assertEqual(unified_strdate('27.02.2016 17:30'), '20160227')
        self.assertEqual(unified_strdate('UNKNOWN DATE FORMAT'), None)

    def test_unified_timestamps(self):
        self.assertEqual(unified_timestamp('December 21, 2010'), 1292889600)
        self.assertEqual(unified_timestamp('8/7/2009'), 1247011200)
        self.assertEqual(unified_timestamp('Dec 14, 2012'), 1355443200)
        self.assertEqual(unified_timestamp('2012/10/11 01:56:38 +0000'), 1349920598)
        self.assertEqual(unified_timestamp('1968 12 10'), -33436800)
        self.assertEqual(unified_timestamp('1968-12-10'), -33436800)
        self.assertEqual(unified_timestamp('28/01/2014 21:00:00 +0100'), 1390939200)
        self.assertEqual(
            unified_timestamp('11/26/2014 11:30:00 AM PST', day_first=False),
            1417001400)
        self.assertEqual(
            unified_timestamp('2/2/2015 6:47:40 PM', day_first=False),
            1422902860)
        self.assertEqual(unified_timestamp('Feb 14th 2016 5:45PM'), 1455471900)
        self.assertEqual(unified_timestamp('25-09-2014'), 1411603200)
        self.assertEqual(unified_timestamp('27.02.2016 17:30'), 1456594200)
        self.assertEqual(unified_timestamp('UNKNOWN DATE FORMAT'), None)

    def test_determine_ext(self):
        self.assertEqual(determine_ext('http://example.com/foo/bar.mp4/?download'), 'mp4')
        self.assertEqual(determine_ext('http://example.com/foo/bar/?download', None), None)
        self.assertEqual(determine_ext('http://example.com/foo/bar.nonext/?download', None), None)
        self.assertEqual(determine_ext('http://example.com/foo/bar/mp4?download', None), None)
        self.assertEqual(determine_ext('http://example.com/foo/bar.m3u8//?download'), 'm3u8')

    def test_find_xpath_attr(self):
        testxml = '''<root>
            <node/>
            <node x="a"/>
            <node x="a" y="c" />
            <node x="b" y="d" />
            <node x="" />
        </root>'''
        doc = compat_etree_fromstring(testxml)

        self.assertEqual(find_xpath_attr(doc, './/fourohfour', 'n'), None)
        self.assertEqual(find_xpath_attr(doc, './/fourohfour', 'n', 'v'), None)
        self.assertEqual(find_xpath_attr(doc, './/node', 'n'), None)
        self.assertEqual(find_xpath_attr(doc, './/node', 'n', 'v'), None)
        self.assertEqual(find_xpath_attr(doc, './/node', 'x'), doc[1])
        self.assertEqual(find_xpath_attr(doc, './/node', 'x', 'a'), doc[1])
        self.assertEqual(find_xpath_attr(doc, './/node', 'x', 'b'), doc[3])
        self.assertEqual(find_xpath_attr(doc, './/node', 'y'), doc[2])
        self.assertEqual(find_xpath_attr(doc, './/node', 'y', 'c'), doc[2])
        self.assertEqual(find_xpath_attr(doc, './/node', 'y', 'd'), doc[3])
        self.assertEqual(find_xpath_attr(doc, './/node', 'x', ''), doc[4])

    def test_xpath_with_ns(self):
        testxml = '''<root xmlns:media="http://example.com/">
            <media:song>
                <media:author>The Author</media:author>
                <url>http://server.com/download.mp3</url>
            </media:song>
        </root>'''
        doc = compat_etree_fromstring(testxml)
        find = lambda p: doc.find(xpath_with_ns(p, {'media': 'http://example.com/'}))
        self.assertTrue(find('media:song') is not None)
        self.assertEqual(find('media:song/media:author').text, 'The Author')
        self.assertEqual(find('media:song/url').text, 'http://server.com/download.mp3')

    def test_xpath_element(self):
        doc = xml.etree.ElementTree.Element('root')
        div = xml.etree.ElementTree.SubElement(doc, 'div')
        p = xml.etree.ElementTree.SubElement(div, 'p')
        p.text = 'Foo'
        self.assertEqual(xpath_element(doc, 'div/p'), p)
        self.assertEqual(xpath_element(doc, ['div/p']), p)
        self.assertEqual(xpath_element(doc, ['div/bar', 'div/p']), p)
        self.assertEqual(xpath_element(doc, 'div/bar', default='default'), 'default')
        self.assertEqual(xpath_element(doc, ['div/bar'], default='default'), 'default')
        self.assertTrue(xpath_element(doc, 'div/bar') is None)
        self.assertTrue(xpath_element(doc, ['div/bar']) is None)
        self.assertTrue(xpath_element(doc, ['div/bar'], 'div/baz') is None)
        self.assertRaises(ExtractorError, xpath_element, doc, 'div/bar', fatal=True)
        self.assertRaises(ExtractorError, xpath_element, doc, ['div/bar'], fatal=True)
        self.assertRaises(ExtractorError, xpath_element, doc, ['div/bar', 'div/baz'], fatal=True)

    def test_xpath_text(self):
        testxml = '''<root>
            <div>
                <p>Foo</p>
            </div>
        </root>'''
        doc = compat_etree_fromstring(testxml)
        self.assertEqual(xpath_text(doc, 'div/p'), 'Foo')
        self.assertEqual(xpath_text(doc, 'div/bar', default='default'), 'default')
        self.assertTrue(xpath_text(doc, 'div/bar') is None)
        self.assertRaises(ExtractorError, xpath_text, doc, 'div/bar', fatal=True)

    def test_xpath_attr(self):
        testxml = '''<root>
            <div>
                <p x="a">Foo</p>
            </div>
        </root>'''
        doc = compat_etree_fromstring(testxml)
        self.assertEqual(xpath_attr(doc, 'div/p', 'x'), 'a')
        self.assertEqual(xpath_attr(doc, 'div/bar', 'x'), None)
        self.assertEqual(xpath_attr(doc, 'div/p', 'y'), None)
        self.assertEqual(xpath_attr(doc, 'div/bar', 'x', default='default'), 'default')
        self.assertEqual(xpath_attr(doc, 'div/p', 'y', default='default'), 'default')
        self.assertRaises(ExtractorError, xpath_attr, doc, 'div/bar', 'x', fatal=True)
        self.assertRaises(ExtractorError, xpath_attr, doc, 'div/p', 'y', fatal=True)

    def test_smuggle_url(self):
        data = {"ö": "ö", "abc": [3]}
        url = 'https://foo.bar/baz?x=y#a'
        smug_url = smuggle_url(url, data)
        unsmug_url, unsmug_data = unsmuggle_url(smug_url)
        self.assertEqual(url, unsmug_url)
        self.assertEqual(data, unsmug_data)

        res_url, res_data = unsmuggle_url(url)
        self.assertEqual(res_url, url)
        self.assertEqual(res_data, None)

    def test_shell_quote(self):
        args = ['ffmpeg', '-i', encodeFilename('ñ€ß\'.mp4')]
        self.assertEqual(shell_quote(args), """ffmpeg -i 'ñ€ß'"'"'.mp4'""")

    def test_str_to_int(self):
        self.assertEqual(str_to_int('123,456'), 123456)
        self.assertEqual(str_to_int('123.456'), 123456)

    def test_url_basename(self):
        self.assertEqual(url_basename('http://foo.de/'), '')
        self.assertEqual(url_basename('http://foo.de/bar/baz'), 'baz')
        self.assertEqual(url_basename('http://foo.de/bar/baz?x=y'), 'baz')
        self.assertEqual(url_basename('http://foo.de/bar/baz#x=y'), 'baz')
        self.assertEqual(url_basename('http://foo.de/bar/baz/'), 'baz')
        self.assertEqual(
            url_basename('http://media.w3.org/2010/05/sintel/trailer.mp4'),
            'trailer.mp4')

    def test_parse_duration(self):
        self.assertEqual(parse_duration(None), None)
        self.assertEqual(parse_duration(False), None)
        self.assertEqual(parse_duration('invalid'), None)
        self.assertEqual(parse_duration('1'), 1)
        self.assertEqual(parse_duration('1337:12'), 80232)
        self.assertEqual(parse_duration('9:12:43'), 33163)
        self.assertEqual(parse_duration('12:00'), 720)
        self.assertEqual(parse_duration('00:01:01'), 61)
        self.assertEqual(parse_duration('x:y'), None)
        self.assertEqual(parse_duration('3h11m53s'), 11513)
        self.assertEqual(parse_duration('3h 11m 53s'), 11513)
        self.assertEqual(parse_duration('3 hours 11 minutes 53 seconds'), 11513)
        self.assertEqual(parse_duration('3 hours 11 mins 53 secs'), 11513)
        self.assertEqual(parse_duration('62m45s'), 3765)
        self.assertEqual(parse_duration('6m59s'), 419)
        self.assertEqual(parse_duration('49s'), 49)
        self.assertEqual(parse_duration('0h0m0s'), 0)
        self.assertEqual(parse_duration('0m0s'), 0)
        self.assertEqual(parse_duration('0s'), 0)
        self.assertEqual(parse_duration('01:02:03.05'), 3723.05)
        self.assertEqual(parse_duration('T30M38S'), 1838)
        self.assertEqual(parse_duration('5 s'), 5)
        self.assertEqual(parse_duration('3 min'), 180)
        self.assertEqual(parse_duration('2.5 hours'), 9000)
        self.assertEqual(parse_duration('02:03:04'), 7384)
        self.assertEqual(parse_duration('01:02:03:04'), 93784)
        self.assertEqual(parse_duration('1 hour 3 minutes'), 3780)
        self.assertEqual(parse_duration('87 Min.'), 5220)
        self.assertEqual(parse_duration('PT1H0.040S'), 3600.04)

    def test_fix_xml_ampersands(self):
        self.assertEqual(
            fix_xml_ampersands('"&x=y&z=a'), '"&amp;x=y&amp;z=a')
        self.assertEqual(
            fix_xml_ampersands('"&amp;x=y&wrong;&z=a'),
            '"&amp;x=y&amp;wrong;&amp;z=a')
        self.assertEqual(
            fix_xml_ampersands('&amp;&apos;&gt;&lt;&quot;'),
            '&amp;&apos;&gt;&lt;&quot;')
        self.assertEqual(
            fix_xml_ampersands('&#1234;&#x1abC;'), '&#1234;&#x1abC;')
        self.assertEqual(fix_xml_ampersands('&#&#'), '&amp;#&amp;#')

    def test_paged_list(self):
        def testPL(size, pagesize, sliceargs, expected):
            def get_page(pagenum):
                firstid = pagenum * pagesize
                upto = min(size, pagenum * pagesize + pagesize)
                for i in range(firstid, upto):
                    yield i

            pl = OnDemandPagedList(get_page, pagesize)
            got = pl.getslice(*sliceargs)
            self.assertEqual(got, expected)

            iapl = InAdvancePagedList(get_page, size // pagesize + 1, pagesize)
            got = iapl.getslice(*sliceargs)
            self.assertEqual(got, expected)

        testPL(5, 2, (), [0, 1, 2, 3, 4])
        testPL(5, 2, (1,), [1, 2, 3, 4])
        testPL(5, 2, (2,), [2, 3, 4])
        testPL(5, 2, (4,), [4])
        testPL(5, 2, (0, 3), [0, 1, 2])
        testPL(5, 2, (1, 4), [1, 2, 3])
        testPL(5, 2, (2, 99), [2, 3, 4])
        testPL(5, 2, (20, 99), [])

    def test_read_batch_urls(self):
        f = io.StringIO('''\xef\xbb\xbf foo
            bar\r
            baz
            # More after this line\r
            ; or after this
            bam''')
        self.assertEqual(read_batch_urls(f), ['foo', 'bar', 'baz', 'bam'])

    def test_urlencode_postdata(self):
        data = urlencode_postdata({'username': 'foo@bar.com', 'password': '1234'})
        self.assertTrue(isinstance(data, bytes))

    def test_update_url_query(self):
        def query_dict(url):
            return compat_parse_qs(compat_urlparse.urlparse(url).query)
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'quality': ['HD'], 'format': ['mp4']})),
            query_dict('http://example.com/path?quality=HD&format=mp4'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'system': ['LINUX', 'WINDOWS']})),
            query_dict('http://example.com/path?system=LINUX&system=WINDOWS'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'fields': 'id,formats,subtitles'})),
            query_dict('http://example.com/path?fields=id,formats,subtitles'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'fields': ('id,formats,subtitles', 'thumbnails')})),
            query_dict('http://example.com/path?fields=id,formats,subtitles&fields=thumbnails'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path?manifest=f4m', {'manifest': []})),
            query_dict('http://example.com/path'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path?system=LINUX&system=WINDOWS', {'system': 'LINUX'})),
            query_dict('http://example.com/path?system=LINUX'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'fields': b'id,formats,subtitles'})),
            query_dict('http://example.com/path?fields=id,formats,subtitles'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'width': 1080, 'height': 720})),
            query_dict('http://example.com/path?width=1080&height=720'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'bitrate': 5020.43})),
            query_dict('http://example.com/path?bitrate=5020.43'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'test': '第二行тест'})),
            query_dict('http://example.com/path?test=%E7%AC%AC%E4%BA%8C%E8%A1%8C%D1%82%D0%B5%D1%81%D1%82'))

    def test_dict_get(self):
        FALSE_VALUES = {
            'none': None,
            'false': False,
            'zero': 0,
            'empty_string': '',
            'empty_list': [],
        }
        d = FALSE_VALUES.copy()
        d['a'] = 42
        self.assertEqual(dict_get(d, 'a'), 42)
        self.assertEqual(dict_get(d, 'b'), None)
        self.assertEqual(dict_get(d, 'b', 42), 42)
        self.assertEqual(dict_get(d, ('a', )), 42)
        self.assertEqual(dict_get(d, ('b', 'a', )), 42)
        self.assertEqual(dict_get(d, ('b', 'c', 'a', 'd', )), 42)
        self.assertEqual(dict_get(d, ('b', 'c', )), None)
        self.assertEqual(dict_get(d, ('b', 'c', ), 42), 42)
        for key, false_value in FALSE_VALUES.items():
            self.assertEqual(dict_get(d, ('b', 'c', key, )), None)
            self.assertEqual(dict_get(d, ('b', 'c', key, ), skip_false_values=False), false_value)

    def test_encode_compat_str(self):
        self.assertEqual(encode_compat_str(b'\xd1\x82\xd0\xb5\xd1\x81\xd1\x82', 'utf-8'), 'тест')
        self.assertEqual(encode_compat_str('тест', 'utf-8'), 'тест')

    def test_parse_iso8601(self):
        self.assertEqual(parse_iso8601('2014-03-23T23:04:26+0100'), 1395612266)
        self.assertEqual(parse_iso8601('2014-03-23T22:04:26+0000'), 1395612266)
        self.assertEqual(parse_iso8601('2014-03-23T22:04:26Z'), 1395612266)
        self.assertEqual(parse_iso8601('2014-03-23T22:04:26.1234Z'), 1395612266)
        self.assertEqual(parse_iso8601('2015-09-29T08:27:31.727'), 1443515251)
        self.assertEqual(parse_iso8601('2015-09-29T08-27-31.727'), None)

    def test_strip_jsonp(self):
        stripped = strip_jsonp('cb ([ {"id":"532cb",\n\n\n"x":\n3}\n]\n);')
        d = json.loads(stripped)
        self.assertEqual(d, [{"id": "532cb", "x": 3}])

        stripped = strip_jsonp('parseMetadata({"STATUS":"OK"})\n\n\n//epc')
        d = json.loads(stripped)
        self.assertEqual(d, {'STATUS': 'OK'})

        stripped = strip_jsonp('ps.embedHandler({"status": "success"});')
        d = json.loads(stripped)
        self.assertEqual(d, {'status': 'success'})

    def test_uppercase_escape(self):
        self.assertEqual(uppercase_escape('aä'), 'aä')
        self.assertEqual(uppercase_escape('\\U0001d550'), '𝕐')

    def test_lowercase_escape(self):
        self.assertEqual(lowercase_escape('aä'), 'aä')
        self.assertEqual(lowercase_escape('\\u0026'), '&')

    def test_limit_length(self):
        self.assertEqual(limit_length(None, 12), None)
        self.assertEqual(limit_length('foo', 12), 'foo')
        self.assertTrue(
            limit_length('foo bar baz asd', 12).startswith('foo bar'))
        self.assertTrue('...' in limit_length('foo bar baz asd', 12))

    def test_escape_rfc3986(self):
        reserved = "!*'();:@&=+$,/?#[]"
        unreserved = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~'
        self.assertEqual(escape_rfc3986(reserved), reserved)
        self.assertEqual(escape_rfc3986(unreserved), unreserved)
        self.assertEqual(escape_rfc3986('тест'), '%D1%82%D0%B5%D1%81%D1%82')
        self.assertEqual(escape_rfc3986('%D1%82%D0%B5%D1%81%D1%82'), '%D1%82%D0%B5%D1%81%D1%82')
        self.assertEqual(escape_rfc3986('foo bar'), 'foo%20bar')
        self.assertEqual(escape_rfc3986('foo%20bar'), 'foo%20bar')

    def test_escape_url(self):
        self.assertEqual(
            escape_url('http://wowza.imust.org/srv/vod/telemb/new/UPLOAD/UPLOAD/20224_IncendieHavré_FD.mp4'),
            'http://wowza.imust.org/srv/vod/telemb/new/UPLOAD/UPLOAD/20224_IncendieHavre%CC%81_FD.mp4'
        )
        self.assertEqual(
            escape_url('http://www.ardmediathek.de/tv/Sturm-der-Liebe/Folge-2036-Zu-Mann-und-Frau-erklärt/Das-Erste/Video?documentId=22673108&bcastId=5290'),
            'http://www.ardmediathek.de/tv/Sturm-der-Liebe/Folge-2036-Zu-Mann-und-Frau-erkl%C3%A4rt/Das-Erste/Video?documentId=22673108&bcastId=5290'
        )
        self.assertEqual(
            escape_url('http://тест.рф/фрагмент'),
            'http://xn--e1aybc.xn--p1ai/%D1%84%D1%80%D0%B0%D0%B3%D0%BC%D0%B5%D0%BD%D1%82'
        )
        self.assertEqual(
            escape_url('http://тест.рф/абв?абв=абв#абв'),
            'http://xn--e1aybc.xn--p1ai/%D0%B0%D0%B1%D0%B2?%D0%B0%D0%B1%D0%B2=%D0%B0%D0%B1%D0%B2#%D0%B0%D0%B1%D0%B2'
        )
        self.assertEqual(escape_url('http://vimeo.com/56015672#at=0'), 'http://vimeo.com/56015672#at=0')

    def test_js_to_json_realworld(self):
        inp = '''{
            'clip':{'provider':'pseudo'}
        }'''
        self.assertEqual(js_to_json(inp), '''{
            "clip":{"provider":"pseudo"}
        }''')
        json.loads(js_to_json(inp))

        inp = '''{
            'playlist':[{'controls':{'all':null}}]
        }'''
        self.assertEqual(js_to_json(inp), '''{
            "playlist":[{"controls":{"all":null}}]
        }''')

        inp = '''"The CW\\'s \\'Crazy Ex-Girlfriend\\'"'''
        self.assertEqual(js_to_json(inp), '''"The CW's 'Crazy Ex-Girlfriend'"''')

        inp = '"SAND Number: SAND 2013-7800P\\nPresenter: Tom Russo\\nHabanero Software Training - Xyce Software\\nXyce, Sandia\\u0027s"'
        json_code = js_to_json(inp)
        self.assertEqual(json.loads(json_code), json.loads(inp))

        inp = '''{
            0:{src:'skipped', type: 'application/dash+xml'},
            1:{src:'skipped', type: 'application/vnd.apple.mpegURL'},
        }'''
        self.assertEqual(js_to_json(inp), '''{
            "0":{"src":"skipped", "type": "application/dash+xml"},
            "1":{"src":"skipped", "type": "application/vnd.apple.mpegURL"}
        }''')

        inp = '''{"foo":101}'''
        self.assertEqual(js_to_json(inp), '''{"foo":101}''')

    def test_js_to_json_edgecases(self):
        on = js_to_json("{abc_def:'1\\'\\\\2\\\\\\'3\"4'}")
        self.assertEqual(json.loads(on), {"abc_def": "1'\\2\\'3\"4"})

        on = js_to_json('{"abc": true}')
        self.assertEqual(json.loads(on), {'abc': True})

        # Ignore JavaScript code as well
        on = js_to_json('''{
            "x": 1,
            y: "a",
            z: some.code
        }''')
        d = json.loads(on)
        self.assertEqual(d['x'], 1)
        self.assertEqual(d['y'], 'a')

        on = js_to_json('["abc", "def",]')
        self.assertEqual(json.loads(on), ['abc', 'def'])

        on = js_to_json('{"abc": "def",}')
        self.assertEqual(json.loads(on), {'abc': 'def'})

        on = js_to_json('{ 0: /* " \n */ ",]" , }')
        self.assertEqual(json.loads(on), {'0': ',]'})

        on = js_to_json(r'["<p>x<\/p>"]')
        self.assertEqual(json.loads(on), ['<p>x</p>'])

        on = js_to_json(r'["\xaa"]')
        self.assertEqual(json.loads(on), ['\u00aa'])

        on = js_to_json("['a\\\nb']")
        self.assertEqual(json.loads(on), ['ab'])

        on = js_to_json('{0xff:0xff}')
        self.assertEqual(json.loads(on), {'255': 255})

        on = js_to_json('{077:077}')
        self.assertEqual(json.loads(on), {'63': 63})

        on = js_to_json('{42:42}')
        self.assertEqual(json.loads(on), {'42': 42})

    def test_extract_attributes(self):
        self.assertEqual(extract_attributes('<e x="y">'), {'x': 'y'})
        self.assertEqual(extract_attributes("<e x='y'>"), {'x': 'y'})
        self.assertEqual(extract_attributes('<e x=y>'), {'x': 'y'})
        self.assertEqual(extract_attributes('<e x="a \'b\' c">'), {'x': "a 'b' c"})
        self.assertEqual(extract_attributes('<e x=\'a "b" c\'>'), {'x': 'a "b" c'})
        self.assertEqual(extract_attributes('<e x="&#121;">'), {'x': 'y'})
        self.assertEqual(extract_attributes('<e x="&#x79;">'), {'x': 'y'})
        self.assertEqual(extract_attributes('<e x="&amp;">'), {'x': '&'})  # XML
        self.assertEqual(extract_attributes('<e x="&quot;">'), {'x': '"'})
        self.assertEqual(extract_attributes('<e x="&pound;">'), {'x': '£'})  # HTML 3.2
        self.assertEqual(extract_attributes('<e x="&lambda;">'), {'x': 'λ'})  # HTML 4.0
        self.assertEqual(extract_attributes('<e x="&foo">'), {'x': '&foo'})
        self.assertEqual(extract_attributes('<e x="\'">'), {'x': "'"})
        self.assertEqual(extract_attributes('<e x=\'"\'>'), {'x': '"'})
        self.assertEqual(extract_attributes('<e x >'), {'x': None})
        self.assertEqual(extract_attributes('<e x=y a>'), {'x': 'y', 'a': None})
        self.assertEqual(extract_attributes('<e x= y>'), {'x': 'y'})
        self.assertEqual(extract_attributes('<e x=1 y=2 x=3>'), {'y': '2', 'x': '3'})
        self.assertEqual(extract_attributes('<e \nx=\ny\n>'), {'x': 'y'})
        self.assertEqual(extract_attributes('<e \nx=\n"y"\n>'), {'x': 'y'})
        self.assertEqual(extract_attributes("<e \nx=\n'y'\n>"), {'x': 'y'})
        self.assertEqual(extract_attributes('<e \nx="\ny\n">'), {'x': '\ny\n'})
        self.assertEqual(extract_attributes('<e CAPS=x>'), {'caps': 'x'})  # Names lowercased
        self.assertEqual(extract_attributes('<e x=1 X=2>'), {'x': '2'})
        self.assertEqual(extract_attributes('<e X=1 x=2>'), {'x': '2'})
        self.assertEqual(extract_attributes('<e _:funny-name1=1>'), {'_:funny-name1': '1'})
        self.assertEqual(extract_attributes('<e x="Fáilte 世界 \U0001f600">'), {'x': 'Fáilte 世界 \U0001f600'})
        self.assertEqual(extract_attributes('<e x="décompose&#769;">'), {'x': 'décompose\u0301'})
        # "Narrow" Python builds don't support unicode code points outside BMP.
        try:
            compat_chr(0x10000)
            supports_outside_bmp = True
        except ValueError:
            supports_outside_bmp = False
        if supports_outside_bmp:
            self.assertEqual(extract_attributes('<e x="Smile &#128512;!">'), {'x': 'Smile \U0001f600!'})

    def test_clean_html(self):
        self.assertEqual(clean_html('a:\nb'), 'a: b')
        self.assertEqual(clean_html('a:\n   "b"'), 'a:    "b"')

    def test_intlist_to_bytes(self):
        self.assertEqual(
            intlist_to_bytes([0, 1, 127, 128, 255]),
            b'\x00\x01\x7f\x80\xff')

    def test_args_to_str(self):
        self.assertEqual(
            args_to_str(['foo', 'ba/r', '-baz', '2 be', '']),
            'foo ba/r -baz \'2 be\' \'\''
        )

    def test_parse_filesize(self):
        self.assertEqual(parse_filesize(None), None)
        self.assertEqual(parse_filesize(''), None)
        self.assertEqual(parse_filesize('91 B'), 91)
        self.assertEqual(parse_filesize('foobar'), None)
        self.assertEqual(parse_filesize('2 MiB'), 2097152)
        self.assertEqual(parse_filesize('5 GB'), 5000000000)
        self.assertEqual(parse_filesize('1.2Tb'), 1200000000000)
        self.assertEqual(parse_filesize('1,24 KB'), 1240)

    def test_parse_count(self):
        self.assertEqual(parse_count(None), None)
        self.assertEqual(parse_count(''), None)
        self.assertEqual(parse_count('0'), 0)
        self.assertEqual(parse_count('1000'), 1000)
        self.assertEqual(parse_count('1.000'), 1000)
        self.assertEqual(parse_count('1.1k'), 1100)
        self.assertEqual(parse_count('1.1kk'), 1100000)
        self.assertEqual(parse_count('1.1kk '), 1100000)
        self.assertEqual(parse_count('1.1kk views'), 1100000)

    def test_version_tuple(self):
        self.assertEqual(version_tuple('1'), (1,))
        self.assertEqual(version_tuple('10.23.344'), (10, 23, 344))
        self.assertEqual(version_tuple('10.1-6'), (10, 1, 6))  # avconv style

    def test_detect_exe_version(self):
        self.assertEqual(detect_exe_version('''ffmpeg version 1.2.1
built on May 27 2013 08:37:26 with gcc 4.7 (Debian 4.7.3-4)
configuration: --prefix=/usr --extra-'''), '1.2.1')
        self.assertEqual(detect_exe_version('''ffmpeg version N-63176-g1fb4685
built on May 15 2014 22:09:06 with gcc 4.8.2 (GCC)'''), 'N-63176-g1fb4685')
        self.assertEqual(detect_exe_version('''X server found. dri2 connection failed!
Trying to open render node...
Success at /dev/dri/renderD128.
ffmpeg version 2.4.4 Copyright (c) 2000-2014 the FFmpeg ...'''), '2.4.4')

    def test_age_restricted(self):
        self.assertFalse(age_restricted(None, 10))  # unrestricted content
        self.assertFalse(age_restricted(1, None))  # unrestricted policy
        self.assertFalse(age_restricted(8, 10))
        self.assertTrue(age_restricted(18, 14))
        self.assertFalse(age_restricted(18, 18))

    def test_is_html(self):
        self.assertFalse(is_html(b'\x49\x44\x43<html'))
        self.assertTrue(is_html(b'<!DOCTYPE foo>\xaaa'))
        self.assertTrue(is_html(  # UTF-8 with BOM
            b'\xef\xbb\xbf<!DOCTYPE foo>\xaaa'))
        self.assertTrue(is_html(  # UTF-16-LE
            b'\xff\xfe<\x00h\x00t\x00m\x00l\x00>\x00\xe4\x00'
        ))
        self.assertTrue(is_html(  # UTF-16-BE
            b'\xfe\xff\x00<\x00h\x00t\x00m\x00l\x00>\x00\xe4'
        ))
        self.assertTrue(is_html(  # UTF-32-BE
            b'\x00\x00\xFE\xFF\x00\x00\x00<\x00\x00\x00h\x00\x00\x00t\x00\x00\x00m\x00\x00\x00l\x00\x00\x00>\x00\x00\x00\xe4'))
        self.assertTrue(is_html(  # UTF-32-LE
            b'\xFF\xFE\x00\x00<\x00\x00\x00h\x00\x00\x00t\x00\x00\x00m\x00\x00\x00l\x00\x00\x00>\x00\x00\x00\xe4\x00\x00\x00'))

    def test_render_table(self):
        self.assertEqual(
            render_table(
                ['a', 'bcd'],
                [[123, 4], [9999, 51]]),
            'a    bcd\n'
            '123  4\n'
            '9999 51')

    def test_match_str(self):
        self.assertRaises(ValueError, match_str, 'xy>foobar', {})
        self.assertFalse(match_str('xy', {'x': 1200}))
        self.assertTrue(match_str('!xy', {'x': 1200}))
        self.assertTrue(match_str('x', {'x': 1200}))
        self.assertFalse(match_str('!x', {'x': 1200}))
        self.assertTrue(match_str('x', {'x': 0}))
        self.assertFalse(match_str('x>0', {'x': 0}))
        self.assertFalse(match_str('x>0', {}))
        self.assertTrue(match_str('x>?0', {}))
        self.assertTrue(match_str('x>1K', {'x': 1200}))
        self.assertFalse(match_str('x>2K', {'x': 1200}))
        self.assertTrue(match_str('x>=1200 & x < 1300', {'x': 1200}))
        self.assertFalse(match_str('x>=1100 & x < 1200', {'x': 1200}))
        self.assertFalse(match_str('y=a212', {'y': 'foobar42'}))
        self.assertTrue(match_str('y=foobar42', {'y': 'foobar42'}))
        self.assertFalse(match_str('y!=foobar42', {'y': 'foobar42'}))
        self.assertTrue(match_str('y!=foobar2', {'y': 'foobar42'}))
        self.assertFalse(match_str(
            'like_count > 100 & dislike_count <? 50 & description',
            {'like_count': 90, 'description': 'foo'}))
        self.assertTrue(match_str(
            'like_count > 100 & dislike_count <? 50 & description',
            {'like_count': 190, 'description': 'foo'}))
        self.assertFalse(match_str(
            'like_count > 100 & dislike_count <? 50 & description',
            {'like_count': 190, 'dislike_count': 60, 'description': 'foo'}))
        self.assertFalse(match_str(
            'like_count > 100 & dislike_count <? 50 & description',
            {'like_count': 190, 'dislike_count': 10}))

    def test_parse_dfxp_time_expr(self):
        self.assertEqual(parse_dfxp_time_expr(None), None)
        self.assertEqual(parse_dfxp_time_expr(''), None)
        self.assertEqual(parse_dfxp_time_expr('0.1'), 0.1)
        self.assertEqual(parse_dfxp_time_expr('0.1s'), 0.1)
        self.assertEqual(parse_dfxp_time_expr('00:00:01'), 1.0)
        self.assertEqual(parse_dfxp_time_expr('00:00:01.100'), 1.1)
        self.assertEqual(parse_dfxp_time_expr('00:00:01:100'), 1.1)

    def test_dfxp2srt(self):
        dfxp_data = '''<?xml version="1.0" encoding="UTF-8"?>
            <tt xmlns="http://www.w3.org/ns/ttml" xml:lang="en" xmlns:tts="http://www.w3.org/ns/ttml#parameter">
            <body>
                <div xml:lang="en">
                    <p begin="0" end="1">The following line contains Chinese characters and special symbols</p>
                    <p begin="1" end="2">第二行<br/>♪♪</p>
                    <p begin="2" dur="1"><span>Third<br/>Line</span></p>
                    <p begin="3" end="-1">Lines with invalid timestamps are ignored</p>
                    <p begin="-1" end="-1">Ignore, two</p>
                    <p begin="3" dur="-1">Ignored, three</p>
                </div>
            </body>
            </tt>'''
        srt_data = '''1
00:00:00,000 --> 00:00:01,000
The following line contains Chinese characters and special symbols

2
00:00:01,000 --> 00:00:02,000
第二行
♪♪

3
00:00:02,000 --> 00:00:03,000
Third
Line

'''
        self.assertEqual(dfxp2srt(dfxp_data), srt_data)

        dfxp_data_no_default_namespace = '''<?xml version="1.0" encoding="UTF-8"?>
            <tt xml:lang="en" xmlns:tts="http://www.w3.org/ns/ttml#parameter">
            <body>
                <div xml:lang="en">
                    <p begin="0" end="1">The first line</p>
                </div>
            </body>
            </tt>'''
        srt_data = '''1
00:00:00,000 --> 00:00:01,000
The first line

'''
        self.assertEqual(dfxp2srt(dfxp_data_no_default_namespace), srt_data)

    def test_cli_option(self):
        self.assertEqual(cli_option({'proxy': '127.0.0.1:3128'}, '--proxy', 'proxy'), ['--proxy', '127.0.0.1:3128'])
        self.assertEqual(cli_option({'proxy': None}, '--proxy', 'proxy'), [])
        self.assertEqual(cli_option({}, '--proxy', 'proxy'), [])

    def test_cli_valueless_option(self):
        self.assertEqual(cli_valueless_option(
            {'downloader': 'external'}, '--external-downloader', 'downloader', 'external'), ['--external-downloader'])
        self.assertEqual(cli_valueless_option(
            {'downloader': 'internal'}, '--external-downloader', 'downloader', 'external'), [])
        self.assertEqual(cli_valueless_option(
            {'nocheckcertificate': True}, '--no-check-certificate', 'nocheckcertificate'), ['--no-check-certificate'])
        self.assertEqual(cli_valueless_option(
            {'nocheckcertificate': False}, '--no-check-certificate', 'nocheckcertificate'), [])
        self.assertEqual(cli_valueless_option(
            {'checkcertificate': True}, '--no-check-certificate', 'checkcertificate', False), [])
        self.assertEqual(cli_valueless_option(
            {'checkcertificate': False}, '--no-check-certificate', 'checkcertificate', False), ['--no-check-certificate'])

    def test_cli_bool_option(self):
        self.assertEqual(
            cli_bool_option(
                {'nocheckcertificate': True}, '--no-check-certificate', 'nocheckcertificate'),
            ['--no-check-certificate', 'true'])
        self.assertEqual(
            cli_bool_option(
                {'nocheckcertificate': True}, '--no-check-certificate', 'nocheckcertificate', separator='='),
            ['--no-check-certificate=true'])
        self.assertEqual(
            cli_bool_option(
                {'nocheckcertificate': True}, '--check-certificate', 'nocheckcertificate', 'false', 'true'),
            ['--check-certificate', 'false'])
        self.assertEqual(
            cli_bool_option(
                {'nocheckcertificate': True}, '--check-certificate', 'nocheckcertificate', 'false', 'true', '='),
            ['--check-certificate=false'])
        self.assertEqual(
            cli_bool_option(
                {'nocheckcertificate': False}, '--check-certificate', 'nocheckcertificate', 'false', 'true'),
            ['--check-certificate', 'true'])
        self.assertEqual(
            cli_bool_option(
                {'nocheckcertificate': False}, '--check-certificate', 'nocheckcertificate', 'false', 'true', '='),
            ['--check-certificate=true'])

    def test_ohdave_rsa_encrypt(self):
        N = 0xab86b6371b5318aaa1d3c9e612a9f1264f372323c8c0f19875b5fc3b3fd3afcc1e5bec527aa94bfa85bffc157e4245aebda05389a5357b75115ac94f074aefcd
        e = 65537

        self.assertEqual(
            ohdave_rsa_encrypt(b'aa111222', e, N),
            '726664bd9a23fd0c70f9f1b84aab5e3905ce1e45a584e9cbcf9bcc7510338fc1986d6c599ff990d923aa43c51c0d9013cd572e13bc58f4ae48f2ed8c0b0ba881')

    def test_encode_base_n(self):
        self.assertEqual(encode_base_n(0, 30), '0')
        self.assertEqual(encode_base_n(80, 30), '2k')

        custom_table = '9876543210ZYXWVUTSRQPONMLKJIHGFEDCBA'
        self.assertEqual(encode_base_n(0, 30, custom_table), '9')
        self.assertEqual(encode_base_n(80, 30, custom_table), '7P')

        self.assertRaises(ValueError, encode_base_n, 0, 70)
        self.assertRaises(ValueError, encode_base_n, 0, 60, custom_table)

    def test_urshift(self):
        self.assertEqual(urshift(3, 1), 1)
        self.assertEqual(urshift(-3, 1), 2147483646)

if __name__ == '__main__':
    unittest.main()
