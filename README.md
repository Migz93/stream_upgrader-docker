# Stream Upgrader for Plex
[![Docker Image CI](https://github.com/Migz93/stream_upgrader-docker/actions/workflows/main.yml/badge.svg)](https://github.com/Migz93/stream_upgrader-docker/actions/workflows/main.yml)  
Basically a docker version of https://github.com/Casvt/Plex-scripts/blob/main/stream_control/stream_upgrader.py

* Download `stream_upgrader_config.py.example` manually.
* Fill out options within `stream_upgrader_config.py.example`
* Rename `stream_upgrader_config.py.example` to `stream_ugprader_config.py`
* Mount directory with `stream_ugprader_config.py` as `/config` for container.

# Docker Command
```bash
docker run -d \
  --name stream_upgrader \
  -v /mnt/user/appdata/stream_upgrader:/config \
  miguel1993/stream_upgrader
```

# Versions
* 30/08/2022 - Initial release.  

# Credits
https://github.com/Casvt  

# Notes
The dockerised version of the script is mainly made for myself.  
This does not currently have the audio upgrade function, video only.  
This has a hardcoded reference to my NVIDIA Shields, please avoid using "Lounge SHIELD" or "Bedroom SHIELD" as your player name.  
