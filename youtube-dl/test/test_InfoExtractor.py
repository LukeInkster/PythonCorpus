#!/usr/bin/env python

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeYDL
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.extractor import YoutubeIE, get_info_extractor
from youtube_dl.utils import encode_data_uri, strip_jsonp, ExtractorError, RegexNotFoundError


class TestIE(InfoExtractor):
    pass


class TestInfoExtractor(unittest.TestCase):
    def setUp(self):
        self.ie = TestIE(FakeYDL())

    def test_ie_key(self):
        self.assertEqual(get_info_extractor(YoutubeIE.ie_key()), YoutubeIE)

    def test_html_search_regex(self):
        html = '<p id="foo">Watch this <a href="http://www.youtube.com/watch?v=BaW_jenozKc">video</a></p>'
        search = lambda re, *args: self.ie._html_search_regex(re, html, *args)
        self.assertEqual(search(r'<p id="foo">(.+?)</p>', 'foo'), 'Watch this video')

    def test_opengraph(self):
        ie = self.ie
        html = '''
            <meta name="og:title" content='Foo'/>
            <meta content="Some video's description " name="og:description"/>
            <meta property='og:image' content='http://domain.com/pic.jpg?key1=val1&amp;key2=val2'/>
            <meta content='application/x-shockwave-flash' property='og:video:type'>
            <meta content='Foo' property=og:foobar>
            <meta name="og:test1" content='foo > < bar'/>
            <meta name="og:test2" content="foo >//< bar"/>
            '''
        self.assertEqual(ie._og_search_title(html), 'Foo')
        self.assertEqual(ie._og_search_description(html), 'Some video\'s description ')
        self.assertEqual(ie._og_search_thumbnail(html), 'http://domain.com/pic.jpg?key1=val1&key2=val2')
        self.assertEqual(ie._og_search_video_url(html, default=None), None)
        self.assertEqual(ie._og_search_property('foobar', html), 'Foo')
        self.assertEqual(ie._og_search_property('test1', html), 'foo > < bar')
        self.assertEqual(ie._og_search_property('test2', html), 'foo >//< bar')

    def test_html_search_meta(self):
        ie = self.ie
        html = '''
            <meta name="a" content="1" />
            <meta name='b' content='2'>
            <meta name="c" content='3'>
            <meta name=d content='4'>
            <meta property="e" content='5' >
            <meta content="6" name="f">
        '''

        self.assertEqual(ie._html_search_meta('a', html), '1')
        self.assertEqual(ie._html_search_meta('b', html), '2')
        self.assertEqual(ie._html_search_meta('c', html), '3')
        self.assertEqual(ie._html_search_meta('d', html), '4')
        self.assertEqual(ie._html_search_meta('e', html), '5')
        self.assertEqual(ie._html_search_meta('f', html), '6')
        self.assertEqual(ie._html_search_meta(('a', 'b', 'c'), html), '1')
        self.assertEqual(ie._html_search_meta(('c', 'b', 'a'), html), '3')
        self.assertEqual(ie._html_search_meta(('z', 'x', 'c'), html), '3')
        self.assertRaises(RegexNotFoundError, ie._html_search_meta, 'z', html, None, fatal=True)
        self.assertRaises(RegexNotFoundError, ie._html_search_meta, ('z', 'x'), html, None, fatal=True)

    def test_download_json(self):
        uri = encode_data_uri(b'{"foo": "blah"}', 'application/json')
        self.assertEqual(self.ie._download_json(uri, None), {'foo': 'blah'})
        uri = encode_data_uri(b'callback({"foo": "blah"})', 'application/javascript')
        self.assertEqual(self.ie._download_json(uri, None, transform_source=strip_jsonp), {'foo': 'blah'})
        uri = encode_data_uri(b'{"foo": invalid}', 'application/json')
        self.assertRaises(ExtractorError, self.ie._download_json, uri, None)
        self.assertEqual(self.ie._download_json(uri, None, fatal=False), None)

if __name__ == '__main__':
    unittest.main()
