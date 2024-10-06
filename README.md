# yt-dlp-invidious
This repository contains a plugin for [yt-dlp](https://github.com/yt-dlp/yt-dlp#readme). See [yt-dlp plugins](https://github.com/yt-dlp/yt-dlp#plugins) for more details.  
The plugin adds native support for Invidious and allows youtube downloads to fallback to Invidious on the error 'Sign in to confirm you’re not a bot. This helps protect our community. Learn more'.  
The code is based on [ytdl-org/youtube-dl#31426](https://github.com/ytdl-org/youtube-dl/pull/31426).

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

### Auto-fallback mode (recommended)

Just use yt-dlp as normal, the plugin will automatically fall back to invidious when YoutubeIE or YoutubePlaylistIE reported 'Sign in to confirm you’re not a bot. This helps protect our community. Learn more'.

### Force override mode

Pass `--ies "Invidious,InvidiousPlaylist"` to yt-dlp. The plugin automatically matches the video id/playlist id so you can just pass a video id/playlist id. For a single video id, use `invidious:<id>` instead of `<id>` to force yt-dlp to use Invidious.

### Extractor arguments
Use something like `--extractor-args "invidious:max_retries=3;retry_interval=3.45" --extractor-args "invidiousplaylist:preferred_instance=inv.nadeko.net"` to pass multiple extractor arguments in a single run.  
See [EXTRACTOR ARGUMENTS](https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#extractor-arguments) for more details.

#### **invidious**
- `max_retries`: maxium retry times. (default: 5)  
    e.g. `infinite` (unrecommended), `3`.
- `retry_interval`: interval between retries (in seconds). (default: 5)  
    e.g. `3.45`.
- `preferred_instance`: netloc of preferred instance (default: `INSTANCES[0]`)  
    e.g. `inv.nadeko.net`.

#### **invidiousplaylist**
- `preferred_instance`: netloc of preferred instance (default: `INSTANCES[0]`)  
    e.g. `inv.nadeko.net`.
