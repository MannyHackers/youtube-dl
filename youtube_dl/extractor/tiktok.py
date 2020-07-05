# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    try_get
)


class TikTokIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tiktok\.com/@.+/video/(?P<id>[0-9]+)+'
    _TESTS = [{
        'url': 'https://www.tiktok.com/@zoey.aune/video/6813765043914624262?lang=en',
        'md5': 'd679cc9a75bce136e5a2be41fd9f77e0',
        'info_dict': {
            'comment_count': int,
            'creator': 'Zoey',
            'description': 'md5:b22dea1b2dd4e18258ebe42cf5571a97',
            'duration': 10,
            'ext': 'mp4',
            'formats': list,
            'width': 576,
            'height': 1024,
            'id': '6813765043914624262',
            'like_count': int,
            'repost_count': int,
            'thumbnail': r're:^https?://[\w\/\.\-]+(~[\w\-]+\.image)?',
            'thumbnails': list,
            'timestamp': 1586453303,
            'title': 'Zoey on TikTok',
            'upload_date': '20200409',
            'uploader': 'zoey.aune',
            'uploader_id': '6651338645989621765',
            'uploader_url': r're:https://www.tiktok.com/@zoey.aune',
            'webpage_url': r're:https://www.tiktok.com/@zoey.aune/(video/)?6813765043914624262',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('https://m.tiktok.com/v/%s.html' % video_id, video_id)

        # The webpage will have a json embedded in a <script id="__NEXT_DATA__"> tag. The JSON holds all the metadata, so fetch that out.
        json_string = self._html_search_regex([r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>'],
                                              webpage, 'next_data')
        json_data = self._parse_json(json_string, video_id)
        video_data = try_get(json_data, lambda x: x['props']['pageProps'], expected_type=dict)

        # The watermarkless video ID is embedded in the first video file, so we need to download it and get the video ID.
        watermarked_url = video_data['videoData']['itemInfos']['video']['urls'][0]
        watermarked_response = self._download_webpage(watermarked_url, video_id)
        idpos = watermarked_response.index("vid:")
        watermarkless_video_id = watermarked_response[idpos + 4:idpos + 36]
        watermarkless_url = "https://api2-16-h2.musical.ly/aweme/v1/play/?video_id={}&vr_type=0&is_play_url=1&source=PackSourceEnum_PUBLISH&media_type=4".format(watermarkless_video_id)

    def _real_extract(self, url):
        user_id = self._match_id(url)
        data = self._download_json(
            'https://m.tiktok.com/h5/share/usr/list/%s/' % user_id, user_id,
            query={'_signature': '_'})
        entries = []
        for aweme in data['aweme_list']:
            try:
                entry = self._extract_aweme(aweme)
            except ExtractorError:
                continue
            entry['extractor_key'] = TikTokIE.ie_key()
            entries.append(entry)
        return self.playlist_result(entries, user_id)


class TikTokWatermarklessIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tiktok\.com/@.+/video/(?P<id>[0-9]+)+'
    _TESTS = [{
        'url': 'https://www.tiktok.com/@zoey.aune/video/6813765043914624262?lang=en',
        'info_dict': {
            'id': 'v09044400000bq7lmc8biaper9qalb50',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('https://m.tiktok.com/v/%s.html' % video_id, video_id)

        next_data_json = self._html_search_regex([r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>'],
                                                 webpage, 'next_data')
        watermarkedURL = self._parse_json(next_data_json, video_id).get('props', {}).get('pageProps', {}).get('videoData', {}).get('itemInfos', {}).get('video', {}).get('urls', {})[0]
        # The vid is embedded in the first video file, so we need to download it (unfortunate!)
        watermarkedVideoResponse = self._download_webpage(watermarkedURL, video_id)
        idpos = watermarkedVideoResponse.index("vid:")
        vidid = watermarkedVideoResponse[idpos + 4:idpos + 36]
        watermarklessURL = "https://api2-16-h2.musical.ly/aweme/v1/play/?video_id={}&vr_type=0&is_play_url=1&source=PackSourceEnum_PUBLISH&media_type=4".format(vidid)

        return {
            'id': vidid,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'url': watermarklessURL,
            'ext': 'mp4',
            'http_headers': {
                'User-Agent': 'okhttp',
            }
        }
