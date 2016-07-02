# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    xpath_text,
    find_xpath_attr,
    determine_ext,
    int_or_none,
    unified_strdate,
    xpath_element,
    ExtractorError,
)


class RadioCanadaIE(InfoExtractor):
    IE_NAME = 'radiocanada'
    _VALID_URL = r'(?:radiocanada:|https?://ici\.radio-canada\.ca/widgets/mediaconsole/)(?P<app_code>[^:/]+)[:/](?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://ici.radio-canada.ca/widgets/mediaconsole/medianet/7184272',
        'info_dict': {
            'id': '7184272',
            'ext': 'flv',
            'title': 'Le parcours du tireur capté sur vidéo',
            'description': 'Images des caméras de surveillance fournies par la GRC montrant le parcours du tireur d\'Ottawa',
            'upload_date': '20141023',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        app_code, video_id = re.match(self._VALID_URL, url).groups()

        formats = []
        # TODO: extract m3u8 and f4m formats
        # m3u8 formats can be extracted using ipad device_type return 403 error code when ffmpeg try to download segements
        # f4m formats can be extracted using flashhd device_type but they produce unplayable file
        for device_type in ('flash',):
            v_data = self._download_xml(
                'http://api.radio-canada.ca/validationMedia/v1/Validation.ashx',
                video_id, note='Downloading %s XML' % device_type, query={
                    'appCode': app_code,
                    'idMedia': video_id,
                    'connectionType': 'broadband',
                    'multibitrate': 'true',
                    'deviceType': device_type,
                    # paysJ391wsHjbOJwvCs26toz and bypasslock are used to bypass geo-restriction
                    'paysJ391wsHjbOJwvCs26toz': 'CA',
                    'bypasslock': 'NZt5K62gRqfc',
                })
            v_url = xpath_text(v_data, 'url')
            if not v_url:
                continue
            if v_url == 'null':
                raise ExtractorError('%s said: %s' % (
                    self.IE_NAME, xpath_text(v_data, 'message')), expected=True)
            ext = determine_ext(v_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    v_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(v_url, video_id, f4m_id='hds', fatal=False))
            else:
                ext = determine_ext(v_url)
                bitrates = xpath_element(v_data, 'bitrates')
                for url_e in bitrates.findall('url'):
                    tbr = int_or_none(url_e.get('bitrate'))
                    if not tbr:
                        continue
                    formats.append({
                        'format_id': 'rtmp-%d' % tbr,
                        'url': re.sub(r'\d+\.%s' % ext, '%d.%s' % (tbr, ext), v_url),
                        'ext': 'flv',
                        'protocol': 'rtmp',
                        'width': int_or_none(url_e.get('width')),
                        'height': int_or_none(url_e.get('height')),
                        'tbr': tbr,
                    })
        self._sort_formats(formats)

        metadata = self._download_xml(
            'http://api.radio-canada.ca/metaMedia/v1/index.ashx',
            video_id, note='Downloading metadata XML', query={
                'appCode': app_code,
                'idMedia': video_id,
            })

        def get_meta(name):
            el = find_xpath_attr(metadata, './/Meta', 'name', name)
            return el.text if el is not None else None

        return {
            'id': video_id,
            'title': get_meta('Title'),
            'description': get_meta('Description') or get_meta('ShortDescription'),
            'thumbnail': get_meta('imageHR') or get_meta('imageMR') or get_meta('imageBR'),
            'duration': int_or_none(get_meta('length')),
            'series': get_meta('Emission'),
            'season_number': int_or_none('SrcSaison'),
            'episode_number': int_or_none('SrcEpisode'),
            'upload_date': unified_strdate(get_meta('Date')),
            'formats': formats,
        }


class RadioCanadaAudioVideoIE(InfoExtractor):
    'radiocanada:audiovideo'
    _VALID_URL = r'https?://ici\.radio-canada\.ca/audio-video/media-(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://ici.radio-canada.ca/audio-video/media-7527184/barack-obama-au-vietnam',
        'info_dict': {
            'id': '7527184',
            'ext': 'flv',
            'title': 'Barack Obama au Vietnam',
            'description': 'Les États-Unis lèvent l\'embargo sur la vente d\'armes qui datait de la guerre du Vietnam',
            'upload_date': '20160523',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        return self.url_result('radiocanada:medianet:%s' % self._match_id(url))
