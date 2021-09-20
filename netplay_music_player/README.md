# Project+ Netplay Music Player

This python program is designed to be a workaround to play customized music during P+ netplay without desyncing.

The way it works is that it hooks onto P+ Dolphin (using [py-dolphin-memory-engine](py-dolphin-memory-engine
), finds the current P+ tracklist (.tlst) being used in game, reads the corresponding tracklist outside Dolphin and then plays a random song from the tracklist externally using [foobar2000](https://www.foobar2000.org/).

***

# Installation
Note: This application was tested on Python 3.8. It currently only works for Windows.

pip install dolphin-memory-engine   
pip install pynput

Install [foobar2000](https://www.foobar2000.org/) and its [vgmstream plugin](https://www.foobar2000.org/components/view/foo_input_vgmstream). Once foobar2000 is installed, open it and select 'Loop forever' in File -> Preferences -> Playback -> Decoding -> vgmstream.

Set the sound folder in config.json to your custom P+ sound folder (which should contain a tracklist subfolder containing .tlst files and a strm subfolder containing music files/subfolders). The sound folder from P+ can be used to start with. The tracklists can be edited with BrawlCrate and foobar2000 should be able to support most vgm and music files (although brstm is preferred for looping capabilities and compatibility in game). Please consult the [Project+ Music Modding Guide](https://docs.google.com/document/d/1AC4isXShcu9ufUwM5H34dR2orLmsW0xCZXz_lubhixY/edit) (specifically Method 2) for info about modifying tracklists and the music system.

***

# Usage

pplus_netplay_music_player.py

If foobar2000 is installed and the P+ sound folder is found, then it will hook onto P+ Dolphin as soon as the game loads. On the P+ Netplay, check 'Client Side Music Off' to turn off in game music.

Left/right arrows adjust the music volume (up/down is used by P+ Dolphin to adjust volume in game). Press Q at any time to quit the application

***

# Acknowledgements

DukeItOut for the very robust P+ music system and tlst file format

soopercool101 for tlst parsing reference from [BrawlCrate](https://github.com/soopercool101/BrawlCrate) and tlst editing

[py-dolphin-memory-engine](https://github.com/henriquegemignani/py-dolphin-memory-engine) contributors
