# Project+ Netplay Music Player

This python program is designed to be a workaround to play customized music during P+ netplay without desyncing.

The way it works is that it hooks onto P+ Dolphin (using [py-dolphin-memory-engine](py-dolphin-memory-engine
)), finds the current P+ tracklist (.tlst) being used in game, reads the corresponding tracklist outside Dolphin and then plays a random song from the tracklist externally using [foobar2000](https://www.foobar2000.org/).

***

# Installation
Note: This application was tested on Python 3.8. It currently only works for Windows.

pip install dolphin-memory-engine   
pip install pynput

Install [foobar2000](https://www.foobar2000.org/) and its [vgmstream plugin](https://www.foobar2000.org/components/view/foo_input_vgmstream). Once foobar2000 is installed, open it and select 'Loop forever' in File -> Preferences -> Playback -> Decoding -> vgmstream. With Preferences still open, navigate to the Shell Integration section and uncheck 'Bring to front when adding new files'.

Set **soundDir** in PPlusNetplayMusicPlayer.json to your custom P+ sound folder (which should contain a tracklist subfolder containing .tlst files and a strm subfolder containing music files/subfolders). The sound folder from P+ can be used to start with.

***

# Usage

pplus_netplay_music_player.py

[Demo](https://imgur.com/a/VpyTcD3)

If foobar2000 is installed and the P+ sound folder is found, then it will hook onto P+ Dolphin as soon as the game loads. On the P+ Netplay window, check 'Client Side Music Off' to turn off in game music.

Left/right arrows adjust the music volume (up/down is used by P+ Dolphin to adjust volume in game). Press ` at any time to quit the application

The tracklists can be edited with BrawlCrate and foobar2000 should be able to support most vgm and music files (although brstm is preferred for looping capabilities and compatibility in game). Please consult the [Project+ Music Modding Guide](https://docs.google.com/document/d/1AC4isXShcu9ufUwM5H34dR2orLmsW0xCZXz_lubhixY/edit) (specifically Method 2) for info about modifying tracklists and the music system.

The name of the track will be updated in game. From testing this does not desync netplay (although sometimes there will be a warning that a possible desync occurred), however if you're worried about desyncs, set **displayTrackName** in PPlusNetplayMusicPlayer.json to _false_

You can set the **tracklist** folder name in PPlusNetplayMusicPlayer.json which makes it easy to have different set of tracklists that reference the same pool of songs, might be handy if you netplay with different builds.

***
# Future Plans

- Victory themes
- Linux support

***

# Acknowledgements

DukeItOut for the very robust P+ music system and tlst file format

soopercool101 for tlst parsing reference from [BrawlCrate](https://github.com/soopercool101/BrawlCrate) and tlst editing

[py-dolphin-memory-engine](https://github.com/henriquegemignani/py-dolphin-memory-engine) and [vgmstream](https://vgmstream.org/) contributors
