# coding: utf-8
from __future__ import unicode_literals

import random
import re
import string
import time

from .common import InfoExtractor
from ..utils import (
    unescapeHTML,
    urlencode_postdata,
)


class JioSaavnIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://(?:www\.)?
                        (?:
                            jiosaavn\.com/song/[^/]+/|
                            saavn.com/s/song/(?:[^/]+/){3}
                        )
                        (?P<id>[\w\d]+)
                   '''
    _TESTS = [{
        'url': 'https://www.jiosaavn.com/song/leja-re/OQsEfQFVUXk',
        'md5': '7b1f70de088ede3a152ea34aece4df42',
        'info_dict': {
            'id': 'OQsEfQFVUXk',
            'ext': 'mp3',
            'title': 'Leja Re',
            'album': 'Leja Re',
        },
    }, {
        'url': 'https://www.saavn.com/s/song/hindi/Saathiya/O-Humdum-Suniyo-Re/KAMiazoCblU',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        audio_id = self._match_id(url)
        fp = ''.join([random.choice(string.hexdigits) for _ in range(32)])

        # A call to this endpoint is a prerequisite for the server to return
        # the auth_url extracted below
        self._download_webpage('https://www.jiosaavn.com/stats.php', audio_id,
                               query={
                                   'ev': 'site:browser:fp',
                                   'fp': fp,
                                   '_t': int(time.time()),
                                   'ct': '00000000',
                               })

        webpage = self._download_webpage(url, audio_id)

        song_data_re = r'window.__INITIAL_DATA__\s*=\s*(?P<json>.+?);*\s*\</script>'

        def sanitize_song_data(song_data):
            new_date_call_re = r'new Date\(.+?\)'
            return re.sub(new_date_call_re, '"%s"' % time.ctime(), unescapeHTML(song_data))

        song_data = self._parse_json(self._search_regex(song_data_re, webpage,
                                                        'song-json'),
                                     audio_id, transform_source=sanitize_song_data)['song']['song']

        def clean_api_json(resp):
            return self._search_regex(r'(?P<json>\{.+?})', resp, 'api-json')

        data = urlencode_postdata({'__call': 'song.generateAuthToken',
                                   '_format': 'json',
                                   'bitrate': '128',
                                   'url': song_data['encrypted_media_url'],
                                   })

        media_url = self._download_json('https://www.jiosaavn.com/api.php',
                                        audio_id, data=data,
                                        transform_source=clean_api_json,
                                        )['auth_url']

        return {
            'id': audio_id,
            'title': song_data['title']['text'],
            'formats': [{
                'url': media_url,
                'ext': 'mp3',
                'format_note': 'MPEG audio',
                'format_id': '128',
                'vcodec': 'none',
            }],
            'album': song_data.get('album', {}).get('text'),
            'thumbnail': song_data.get('image', [None])[0],
        }
