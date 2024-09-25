import urllib.parse

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.extractor.youtube import YoutubeIE, YoutubePlaylistIE
from yt_dlp.utils import (
    ExtractorError,
    mimetype2ext,
    traverse_obj,
)

INSTANCES = [
    'invidious.jing.rocks',
    'invidious.nerdvpn.de',
    'invidious.privacyredirect.com',
    'inv.nadeko.net',
]

INSTANCES_HOST_REGEX = '(?:' + '|'.join([instance.replace('.', r'\.') for instance in INSTANCES]) + ')'


class InvidiousIE(InfoExtractor):
    _ENABLED = False
    _VALID_URL = r'https?://(?:www\.)?' + INSTANCES_HOST_REGEX + r'/watch\?v=(?P<id>[0-9A-Za-z_-]{11})'
    _TESTS = [{
        'url': 'xKTygGa6hg0',
        'info_dict': {
            'id': 'xKTygGa6hg0',
            'ext': 'mp4',
            'title': 'Coding in C++ - Creating a Player Controller - CRYENGINE Summer Academy S1E5 - [Tutorial]',
            'thumbnail': 'https://invidious.jing.rocks/vi/xKTygGa6hg0/maxresdefault.jpg',
            'channel': 'CRYENGINE',
            'dislike_count': int,
            'uploader': 'CRYENGINE',
            'channel_id': 'UCtaXcIVFp8HEpthm7qwtKCQ',
            'like_count': int,
            'release_timestamp': 1727222400,
            'view_count': int,
            'release_date': '20240925',
            'duration': 1591,
            'description': 'md5:7aa75816d40ffccdbf3e15a90b05fca3',
            'uploader_id': 'UCtaXcIVFp8HEpthm7qwtKCQ',
            'channel_url': 'http://invidious.jing.rocks/channel/UCtaXcIVFp8HEpthm7qwtKCQ',
            'tags': 'count:24',
        },
        'expected_warnings': ['retry'],
    }, {
        'url': 'https://invidious.jing.rocks/watch?v=BaW_jenozKc',
        'md5': 'ed845e9970d0c5ef575ff807f9665906',
        'info_dict': {
            'id': 'BaW_jenozKc',
            'ext': 'mp4',
            'title': 'youtube-dl test video "\'/\\ä↭𝕐',
            'release_timestamp': 1727222400,
            'channel_id': 'UCLqxVugv74EIW3VWh2NOa3Q',
            'thumbnail': 'https://invidious.jing.rocks/vi/BaW_jenozKc/maxresdefault.jpg',
            'description': 'md5:8fb536f4877b8a7455c2ec23794dbc22',
            'view_count': int,
            'duration': 10,
            'channel': 'Philipp Hagemeister',
            'channel_url': 'https://invidious.jing.rocks/channel/UCLqxVugv74EIW3VWh2NOa3Q',
            'tags': ['youtube-dl'],
            'like_count': int,
            'release_date': '20240925',
            'dislike_count': int,
            'uploader': 'Philipp Hagemeister',
            'uploader_id': 'UCLqxVugv74EIW3VWh2NOa3Q',
        },
        'expected_warnings': ['retry'],
    }]

    @classmethod
    def suitable(cls, url):
        return super().suitable(url) or YoutubeIE.suitable(url)

    @staticmethod
    def _get_additional_format_data(format_, format_stream=False):
        out = {}

        try:
            format_type = format_.get('type')
            bitrate = float(format_.get('bitrate')) / 1000
            type_and_ext, codecs = format_type.split(';')
            type_ = type_and_ext.split('/')[0]
            codecs_val = codecs.split('"')[1]
        except Exception:
            pass

        out['ext'] = mimetype2ext(type_and_ext)
        out['tbr'] = bitrate

        if format_stream:
            codecs_ = codecs_val.split(',')
            out['vcodec'] = codecs_[0].strip()
            out['acodec'] = codecs_[1].strip()
        elif type_ == 'audio':
            out['acodec'] = codecs_val
            out['vcodec'] = 'none'
        elif type_ == 'video':
            out['vcodec'] = codecs_val
            out['acodec'] = 'none'

        out.update(traverse_obj(format_, {
            'container': 'container',
            'fps': 'fps',
            'resolution': 'size',
            'audio_channels': 'audioChannels',
            'asr': 'audioSampleRate',
            'format_id': 'itag',
            'url': 'url',
        }))
        return out

    def _patch_url(self, url):
        return urllib.parse.urlparse(url)._replace(netloc=self.url_netloc).geturl()

    def _get_formats(self, api_response):
        formats = []

        # Video/audio only
        for format_ in traverse_obj(api_response, 'adaptiveFormats') or []:
            formats.append({
                **InvidiousIE._get_additional_format_data(format_),
                'url': self._patch_url(format_['url']),
            })

        # Both video and audio
        for format_ in traverse_obj(api_response, 'formatStreams') or []:
            formats.append({
                **InvidiousIE._get_additional_format_data(format_, format_stream=True),
                'url': self._patch_url(format_['url']),
            })

        return formats

    def _get_thumbnails(self, api_response):
        thumbnails = []
        video_thumbnails = api_response.get('videoThumbnails') or []

        for inversed_quality, thumbnail in enumerate(video_thumbnails):
            thumbnails.append({
                'id': thumbnail.get('quality'),
                'url': thumbnail.get('url'),
                'quality': len(video_thumbnails) - inversed_quality,
                'width': thumbnail.get('width'),
                'height': thumbnail.get('height'),
            })

        return thumbnails

    def _real_extract(self, url):
        video_id = (self._match_valid_url(url) or YoutubeIE._match_valid_url(url)).group('id')

        # host_url will contain `http[s]://example.com` where `example.com` is the used invidious instance.
        url_parsed = urllib.parse.urlparse(url)
        url = urllib.parse.urlunparse((
            url_parsed.scheme or 'http',
            INSTANCES[0] if url_parsed.netloc not in INSTANCES else url_parsed.netloc,
            url_parsed.path,
            url_parsed.params,
            url_parsed.query,
            url_parsed.fragment,
        ))
        url_parsed = urllib.parse.urlparse(url)
        self.url_netloc = url_parsed.netloc
        host_url = f'{url_parsed.scheme}://{self.url_netloc}'

        max_retries = self._configuration_arg('max_retries', ['5'], casesense=True)[0]
        if isinstance(max_retries, str) and max_retries.lower() == 'infinite':
            max_retries = 'inf'
        max_retries = float(max_retries)

        retries = 0.0
        while retries <= max_retries:
            api_response, api_urlh = self._download_webpage_handle(
                f'{host_url}/api/v1/videos/{video_id}', video_id,
                'Downloading API response', expected_status=(500, 502))

            if api_urlh.status == 502:
                error = 'HTTP Error 502: Bad Gateway'
            else:
                api_response = self._parse_json(api_response, video_id)
                if api_urlh.status == 200:
                    break

                if error := api_response.get('error'):
                    if 'Sign in to confirm your age' in error:
                        raise ExtractorError(error, expected=True)
                else:
                    error = f'HTTP Error {api_urlh.status}: {api_response}'
            error += f' (retry {retries}/{max_retries})'

            if retries + 1 > max_retries:
                raise ExtractorError(error)
            self.report_warning(error)
            self._sleep(5, video_id)
            retries += 1

        self.webpage = ''

        def download_and_call(_func, *args, **kwargs):
            if not self.webpage:
                self.webpage = self._download_webpage(*args, **kwargs)
            return _func(self.webpage)

        return {
            'id': video_id,
            'title': api_response.get('title') or download_and_call(self._og_search_title,
                                                                    url, video_id),
            'description': api_response.get('description') or download_and_call(self._og_search_description,
                                                                                url, video_id, fatal=False),

            'channel_url': host_url + api_response.get('authorUrl'),
            # 'age_limit': 18 if api_response.get('isFamilyFriendly') is False else 0,

            **traverse_obj(api_response, {
                'release_timestamp': 'published',
                'uploader': 'author',
                'uploader_id': 'authorId',
                'channel': 'author',
                'channel_id': 'authorId',
                'duration': 'lengthSeconds',
                'view_count': 'viewCount',
                'like_count': 'likeCount',
                'dislike_count': 'dislikeCount',
                'tags': 'keywords',
                'is_live': 'liveNow',
                'formats': {self._get_formats},
                'thumbnails': {self._get_thumbnails},
            }),
        }


class InvidiousPlaylistIE(InfoExtractor):
    _ENABLED = False
    _VALID_URL = r'https?://(?:www\.)?' + INSTANCES_HOST_REGEX + r'/playlist\?list=(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'PLowKtXNTBypGqImE405J2565dvjafglHU',
        'md5': 'f28a429de8d5e2ca2b6a7ad84bb38139',
        'info_dict': {
            'id': 'HyznrdDSSGM',
            'ext': 'mp4',
            'title': '8-bit computer update',
            'description': 'md5:c54543163f50447f8cf0bb1ae4cb35ed',
            'uploader': 'Ben Eater',
            'uploader_id': 'UCS0N5baNlQWJCUrhCEo8WlA',
            'channel_url': 'http://invidious.jing.rocks/channel/UCS0N5baNlQWJCUrhCEo8WlA',
            'like_count': int,
            'dislike_count': int,
            'tags': [],
            'thumbnail': 'https://invidious.jing.rocks/vi/HyznrdDSSGM/maxresdefault.jpg',
            'release_timestamp': 1727222400,
            'duration': 413,
            'view_count': int,
            'release_date': '20240925',
            'channel_id': 'UCS0N5baNlQWJCUrhCEo8WlA',
            'channel': 'Ben Eater',
        },
        'expected_warnings': ['retry'],
    }, {
        'url': 'PLtuQtEgOYpLMBnyVgQBUxF4bFSnBqIEbC',
        'playlist_count': 15,
        'info_dict': {
            'id': 'PLtuQtEgOYpLMBnyVgQBUxF4bFSnBqIEbC',
            'title': 'Aya Nakamura - AYA (Official playlist)',
            'release_date': '20210317',
            'description': 'md5:22c0ebf2c22063207422487cf428665a',
            'uploader_id': 'UC-69vhXlCa3XHbF8JHCQHfg',
            'uploader': 'Aya Nakamura',
            'release_timestamp': 1615993200,
        },
        'expected_warnings': ['retry'],
    }]

    @classmethod
    def suitable(cls, url):
        return super().suitable(url) or YoutubePlaylistIE.suitable(url)

    def _get_entries(self, api_response):
        return [self.url_result(f'{self.host_url}/watch?v={videoId}', InvidiousIE)
                for videoId in traverse_obj(api_response, ('videos', ..., 'videoId'))]

    def _real_extract(self, url):
        playlist_id = (self._match_valid_url(url) or YoutubePlaylistIE._match_valid_url(url)).group('id')

        # host_url will contain `http[s]://example.com` where `example.com` is the used invidious instance.
        url_parsed = urllib.parse.urlparse(url)
        if url_parsed.netloc in INSTANCES:
            netloc = url_parsed.netloc
        else:
            netloc = INSTANCES[0]

        self.host_url = f'{url_parsed.scheme or "http"}://{netloc}'

        api_response = self._download_json(f'{self.host_url}/api/v1/playlists/{playlist_id}', playlist_id)
        return self.playlist_result(
            self._get_entries(api_response), playlist_id,
            **traverse_obj(api_response, {
                'playlist_title': 'title',
                'playlist_description': 'description',

                'release_timestamp': 'updated',
                'uploader': 'author',
                'uploader_id': 'authorId',
                # TODO: more metadata fields
            }))
