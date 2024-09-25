# yt-dlp-invidious
This repository contains a plugin for [yt-dlp](https://github.com/yt-dlp/yt-dlp#readme).  
See [yt-dlp plugins](https://github.com/yt-dlp/yt-dlp#plugins) for more details.  
The plugin adds two extractors: `InvidiousIE` and `InvidiousPlaylistIE`.  
The code is based on https://github.com/ytdl-org/youtube-dl/pull/31426.

## Installation

Requires yt-dlp `2023.01.02` or above.

### pip/pipx

If yt-dlp is installed through `pip` or `pipx`, you can install the plugin with the following:

```shell
pipx inject yt-dlp yt-dlp-invidious
```
or

```shell
python3 -m pip install -U yt-dlp-invidious
```

### Manual install

1. Download the latest release zip from [releases](https://github.com/grqz/yt-dlp-invidious/releases)

2. Add the zip to one of the [yt-dlp plugin locations](https://github.com/yt-dlp/yt-dlp#installing-plugins)

    - User Plugins
        - `${XDG_CONFIG_HOME}/yt-dlp/plugins` (recommended on Linux/MacOS)
        - `~/.yt-dlp/plugins/`
        - `${APPDATA}/yt-dlp/plugins/` (recommended on Windows)

    - System Plugins
       -  `/etc/yt-dlp/plugins/`
       -  `/etc/yt-dlp-plugins/`

    - Executable location
        - Binary: where `<root-dir>/yt-dlp.exe`, `<root-dir>/yt-dlp-plugins/`

For more locations and methods, see [installing yt-dlp plugins](https://github.com/yt-dlp/yt-dlp#installing-plugins)

## Usage
Pass `--ies "Invidious,InvidiousPlaylist,default,-youtube,-youtubeplaylist"` to yt-dlp. The plugin automatically matches the video id/playlist id so you can just pass a YouTube link or even just a video id/playlist id.

### Extractor arguments
`InvidiousIE`:
- `max_retries`: maxium retry times.  
	e.g. `--extractor-args "Invidious:max_retries=infinite"` (unrecommended),  
	`--extractor-args "Invidious:max_retries=3"`, etc.
