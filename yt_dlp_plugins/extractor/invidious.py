import urllib.parse

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.extractor.youtube import YoutubeIE
from yt_dlp.utils import (
    ExtractorError,
    mimetype2ext,
    traverse_obj,
)

INSTANCES = [
    'invidious.nerdvpn.de',
    'inv.nadeko.net',
    'invidious.jing.rocks',
    'invidious.privacyredirect.com',
]

INSTANCES_HOST_REGEX = '(?:' + '|'.join([instance.replace('.', r'\.') for instance in INSTANCES]) + ')'


class InvidiousIE(InfoExtractor):
    _ENABLED = False
    _VALID_URL = r'https?://(?:www\.)?' + INSTANCES_HOST_REGEX + r'/watch\?v=(?P<id>[0-9A-Za-z_-]{11})'
    _TESTS = [
        {
            'url': 'https://y.com.sb/watch?v=xKTygGa6hg0',
            'info_dict': {
                'id': 'xKTygGa6hg0',
                'ext': 'mp4',
                'title': 'Coding in C++ - Creating a Player Controller - CRYENGINE Summer Academy S1E5 - [Tutorial]',
                'uploader': 'CRYENGINE',
                'uploader_id': 'UCtaXcIVFp8HEpthm7qwtKCQ',
                'description': 'md5:7aa75816d40ffccdbf3e15a90b05fca3',
            },
        },
        {
            'url': 'https://yt.artemislena.eu/watch?v=BaW_jenozKc',
            'md5': '5515885fed58607bfae88f7d2090bc93',
            'info_dict': {
                'id': 'BaW_jenozKc',
                'ext': 'mp4',
                'title': 'youtube-dl test video "\'/\\ä↭𝕐',
                'uploader': 'Philipp Hagemeister',
                'uploader_id': 'UCLqxVugv74EIW3VWh2NOa3Q',
                'channel_id': 'UCLqxVugv74EIW3VWh2NOa3Q',
                'description': 'test chars:  "\'/\\ä↭𝕐\ntest URL: https://github.com/rg3/youtube-dl/issues/1892\n\nThis is a test video for youtube-dl.\n\nFor more information, contact phihag@phihag.de .',
                'tags': ['youtube-dl'],
                'duration': 10,
                'view_count': int,
                'like_count': int,
                'dislike_count': int,
            },
        },
    ]

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        # This function must import everything it needs (except other extractors),
        # so that lazy_extractors works correctly
        return cls._match_valid_url(url) is not None or YoutubeIE.suitable(url)

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
            vcodec = codecs_[0].strip()
            acodec = codecs_[1].strip()
            out.update({
                'acodec': acodec,
                'vcodec': vcodec,
            })
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
        }))
        return out

    def _patch_url(self, url):
        return urllib.parse.urlparse(url)._replace(netloc=self.url_netloc).geturl()

    def _get_formats(self, api_response):
        formats = []

        # Video/audio only
        for format_ in traverse_obj(api_response, 'adaptiveFormats') or []:
            formats.append({
                'url': self._patch_url(format_['url']),
                **InvidiousIE._get_additional_format_data(format_),
            })

        # Both video and audio
        for format_ in traverse_obj(api_response, 'formatStreams') or []:
            formats.append({
                'url': self._patch_url(format_['url']),
                **InvidiousIE._get_additional_format_data(format_, format_stream=True),
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
                'height': thumbnail.get('height')
            })

        return thumbnails

    def _real_extract(self, url):
        video_id = (self._match_valid_url(url) or YoutubeIE._match_valid_url(url)).group('id')

        max_retries = self._configuration_arg('max_retries', ['5'], casesense=True)[0]
        if isinstance(max_retries, str) and max_retries.lower() == 'infinite':
            max_retries = 'inf'
        max_retries = float(max_retries)

        # host_url will contain `http[s]://example.com` where `example.com` is the used invidious instance.
        url_parsed = urllib.parse.urlparse(url)
        url = urllib.parse.urlunparse((
            url_parsed.scheme or 'http',
            url_parsed.netloc or INSTANCES[0],
            url_parsed.path,
            url_parsed.params,
            url_parsed.query,
            url_parsed.fragment,
        ))
        url_parsed = urllib.parse.urlparse(url)
        self.url_netloc = url_parsed.netloc
        host_url = f'{url_parsed.scheme}://{self.url_netloc}'
        webpage = self._download_webpage(url, video_id, fatal=False) or ''

        retries = 0.0
        while retries <= max_retries:
            api_response, api_urlh = self._download_webpage_handle(
                f'{host_url}/api/v1/videos/{video_id}',
                video_id, 'Downloading API response', expected_status=(500, 502))

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

        out = {
            'id': video_id,
            'title': api_response.get('title') or self._og_search_title(webpage),
            'description': api_response.get('description') or self._og_search_description(webpage),

            'release_timestamp': api_response.get('published'),

            'uploader': api_response.get('author'),
            'uploader_id': api_response.get('authorId'),
            'channel': api_response.get('author'),
            'channel_id': api_response.get('authorId'),
            'channel_url': host_url + api_response.get('authorUrl'),

            'duration': api_response.get('lengthSeconds'),

            'view_count': api_response.get('viewCount'),
            'like_count': api_response.get('likeCount'),
            'dislike_count': api_response.get('dislikeCount'),

            # 'isFamilyFriendly': 18 if api_response.get('isFamilyFriendly') == False else None

            'tags': api_response.get('keywords'),
            'is_live': api_response.get('liveNow'),

            'formats': self._get_formats(api_response),
            'thumbnails': self._get_thumbnails(api_response)
        }

        if api_response.get('isFamilyFriendly') is False:
            out['age_limit'] = 18

        return out


class InvidiousPlaylistIE(InfoExtractor):
    _ENABLED = False
    _VALID_URL = r'https?://(?:www\.)?' + INSTANCES_HOST_REGEX + r'/playlist\?list=(?P<id>[\w-]+)'
    _TEST = {
        'url': 'https://yt.artemislena.eu/playlist?list=PLowKtXNTBypGqImE405J2565dvjafglHU',
        'md5': 'de4a9175071169961fe7cf2b6740da12',
        'info_dict': {
            'id': 'HyznrdDSSGM',
            'ext': 'mp4',
            'title': '8-bit computer update',
            'uploader': 'Ben Eater',
            'uploader_id': 'UCS0N5baNlQWJCUrhCEo8WlA',
            'description': 'An update on my plans to build another 8-bit computer from scratch and make videos of the whole process! Buy a kit and build your own! https://eater.net/8bit/kits\n\nSupport me on Patreon: https://www.patreon.com/beneater',
        },
    }

    def _get_entries(self, api_response):
        return [InvidiousIE(self._downloader)._real_extract(self.host_url + '/watch?v=' + video['videoId'])
                for video in api_response['videos']]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        # host_url will contain `http[s]://example.com` where `example.com` is the used invidious instance.
        url_parsed = urllib.parse.urlparse(url)
        self.host_url = url_parsed.scheme + '://' + url_parsed.netloc

        api_response = self._download_json(self.host_url + '/api/v1/playlists/' + playlist_id, playlist_id)
        return {
            **self.playlist_result(
                self._get_entries(api_response), playlist_id, api_response.get('title'), api_response.get('description')),
            'release_timestamp': api_response.get('updated'),
            'uploader': api_response.get('author'),
            'uploader_id': api_response.get('authorId'),
        }
