This repository contains a sample plugin package for [yt-dlp](https://github.com/yt-dlp/yt-dlp#readme).

See [yt-dlp plugins](https://github.com/yt-dlp/yt-dlp#plugins) for more details.


## Installation

Requires yt-dlp `2023.01.02` or above.

You can install this package with pip:
```
python3 -m pip install -U https://github.com/yt-dlp/yt-dlp-sample-plugins/archive/master.zip
```

See [installing yt-dlp plugins](https://github.com/yt-dlp/yt-dlp#installing-plugins) for the other methods this plugin package can be installed.


## Development

See the [Plugin Development](https://github.com/yt-dlp/yt-dlp/wiki/Plugin-Development) section of the yt-dlp wiki.
Add required dependencies to the `dependencies` section in the `pyproject.toml`.
From within the plugin, use an import pattern similar to the following:
```py
import sys
import pathlib


import_path = str(pathlib.Path(__file__).parent.parent.parent)

sys.path.insert(0, import_path)
try:
	import some_dependency

except ImportError:
	some_dependency = None

finally:
	sys.path.remove(import_path)
```

## Release

To create a release, simply increment the version in the `pyproject.toml` file.
While convenient, conditional requirements or non pure python modules will most likely not work.
Please edit the `.github/workflows/release.yml` accordingly if you require more control.
