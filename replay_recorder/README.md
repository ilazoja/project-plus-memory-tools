# Project+ Replay Recorder

This python program will automatically go through each replay and tell OBS to start/stop recording.

The way it works is that it hooks onto P+ Dolphin (using [py-dolphin-memory-engine](https://github.com/henriquegemignani/py-dolphin-memory-engine
)), forces the game to start in the replay menu, and simulates button inputs to go through and select each replay. Using [obs-websocket](https://github.com/Palakis/obs-websocket), the program will start the recording in OBS when a replay starts and stop when the replay ends. 

***

# Installation
Note: This application was tested on Python 3.8. It has only been tested on Windows but should also work on Linux.

pip install dolphin-memory-engine   
pip install obs-websocket-py

Install [OBS](https://obsproject.com/) and [obs-websocket](https://github.com/Palakis/obs-websocket/releases/tag/4.9.1).

***

# Usage

pplus_replay_recorder.py

The program will hook onto P+ Dolphin as soon as the game loads. If OBS and obs-websocket is installed and you type your passcode set in Tools -> Websockets Server Settings (if authentication is enabled), it will connect to OBS. When the program starts, you have the option to record replays or record live matches.

Starting P+ with this program active (and record replays was selected) will take you straight to the replay menu. You may set up your OBS scene at this point. From there the program will ask you for the replay indices that you want to skip (e.g. 3,4,7). Once entered, the program will automatically go through and play each replay. If connected to OBS, the program will prompt OBS to record only while in a replay.

Use Bird's Replay Manager (included in P+ Dolphin) to manage replays from netplay sessions. Follow mawwwk's [replays managing guide](https://docs.google.com/document/d/1MQzQpu4H41lhwrimu3pTKmBjxZZa_A1xth1WLpExZY4/edit) for more info about replays and information of how to transfer Wii replays to Dolphin. 

***
# Future Plans

- Detect desyncs that will stall the replay recording
- ???

***

# Acknowledgements

mawwwk for the replay managing guide and the image recognition based [replay screen recorder](https://github.com/markymawk/replays-screen-recorder/releases). Mac users should use this since py-dolphin-memory-engine does not work on Mac.

PyotrLuzhin for [Legacy TE] Boot Directly to CSS v4 which was used to reference how to make the game start at a certain screen, as well as DesiacX for having a boot to menu variant which was also referenced.

Fracture for the button memory address location which was used to simulate button inputs to automatically control the game.

[py-dolphin-memory-engine](https://github.com/henriquegemignani/py-dolphin-memory-engine) contributors and [obs-websocket-py](https://github.com/Elektordi/obs-websocket-py) contributors
