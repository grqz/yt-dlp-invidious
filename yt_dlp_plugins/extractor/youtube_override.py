from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.extractor.youtube import YoutubeIE, YoutubePlaylistIE
from yt_dlp.utils import ExtractorError

from .invidious import InvidiousIE, InvidiousPlaylistIE

_BOTGUARD_ERROR_MSG = 'Sign in to confirm you’re not a bot. This helps protect our community. Learn more'


class InvidiousYoutubeOverrideIE(YoutubeIE, plugin_name='invidious'):
    def _real_extract(self, url):
        try:
            return super()._real_extract(url)
        except ExtractorError as e:
            if e.msg == _BOTGUARD_ERROR_MSG:
                return self.url_result('invidious:' + self._match_id(url))
            raise


class InvidiousYoutubePlaylistOverrideIE(YoutubePlaylistIE, plugin_name='invidious'):
    def _real_extract(self, url):
        try:
            return super()._real_extract(url)
        except ExtractorError as e:
            if e.msg == _BOTGUARD_ERROR_MSG:
                return self.url_result('invidious:' + self._match_id(url))
            raise


class InvidiousForceOverrideIE(InfoExtractor):
    _VALID_URL = r'invidious:(?P<id>.+)'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        for ie in (InvidiousIE, InvidiousPlaylistIE):
            if ie.suitable(video_id):
                return ie(self._downloader).extract(video_id)
        raise ExtractorError('Unsupported video id')
