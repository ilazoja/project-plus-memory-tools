
#pip install dolphin_memory_engine
#pip install pynput

import os
import sys
import random
import glob
import subprocess
import atexit

import dolphin_memory_engine
from pynput import keyboard
import time

from utils import BRAWL_BRSTM_DICT, get_config

class TLSTEntryNode:

    def __init__(self, song_id, song_delay, volume, frequency, song_switch, disable_stock_pinch, hidden_from_tracklist, name_offset, filepath_offset):
        self.song_id = song_id
        self.song_delay = song_delay
        self.volume = volume
        self.frequency = frequency
        self.song_switch = song_switch
        self.disable_stock_pinch = disable_stock_pinch
        self.hidden_from_tracklist = hidden_from_tracklist

        self.name_offset = name_offset
        self.filepath_offset = filepath_offset

        self.name = b''
        self.filepath = ""

def pick_song(tlst_name, sound_dir):
    # parse tlst and pick songs based on frequencies and if song is present

    with open(os.path.join(sound_dir, "tracklist", tlst_name + ".tlst"), "rb") as f:

        ## Read header
        f.seek(6)

        num_entries = int.from_bytes(f.read(2), "big", signed = False)
        tlst_entries = [None]*num_entries
        tlst_size = int.from_bytes(f.read(2), "big", signed = False)
        tlst_string_start_offset = int.from_bytes(f.read(2), "big", signed = False) #num_entries*16 + 12
        tlst_string_size = tlst_size - tlst_string_start_offset

        ## Read tlst entries
        for i in range(num_entries):
            f.read(2)
            song_id = f.read(2).hex().upper()
            song_delay = int.from_bytes(f.read(2), "big", signed=True)
            volume = int.from_bytes(f.read(1), "big", signed=False)
            frequency = int.from_bytes(f.read(1), "big", signed=False)
            filepath_offset = f.read(2)
            name_offset = f.read(2)
            song_switch = int.from_bytes(f.read(2), "big", signed=False)
            disable_stock_pinch = bool.from_bytes(f.read(1), "big")
            hidden_from_tracklist = bool.from_bytes(f.read(1), "big")
            tlst_entries[i] = TLSTEntryNode(song_id, song_delay, volume, frequency, song_switch, disable_stock_pinch, hidden_from_tracklist, name_offset, filepath_offset)

        ## start parsing strings (filepath and name) which is found at the end of the tlst
        for i, tlst_entry in enumerate(tlst_entries):
            if tlst_entry.filepath_offset != b'\xff\xff':
                start_index = int.from_bytes(tlst_entry.filepath_offset, "big", signed=False)
                end_index = tlst_string_size - 1
                if tlst_entry.name_offset != b'\xff\xff':
                    end_index = int.from_bytes(tlst_entry.name_offset, "big", signed=False) - 1
                else:
                    for j, future_tlst_entry in enumerate(tlst_entries[i+1:]): # find end_index (i.e. start index of next string)
                        if future_tlst_entry.filepath_offset != b'\xFF\xFF':
                            end_index = int.from_bytes(future_tlst_entry.filepath_offset, "big", signed=False) - 1
                            break
                        elif future_tlst_entry.name_offset != b'\xFF\xFF':
                            end_index = int.from_bytes(future_tlst_entry.name_offset, "big", signed=False) - 1
                            break

                tlst_entry.filepath = f.read(end_index - start_index) # if end_index != -1 else f.read(end_index)[:-1]
                tlst_entry.filepath = str(tlst_entry.filepath, 'utf-8')
                f.read(1)
            else:
                if tlst_entry.song_id[0] != 'F': # if song id starts with F, it is a custom id. If it doesn't then grab Brawl filepath based on song id
                    tlst_entry.filepath = BRAWL_BRSTM_DICT.get(tlst_entry.song_id, "")
            if tlst_entry.name_offset != b'\xff\xff':
                start_index = int.from_bytes(tlst_entry.name_offset, "big", signed=False)
                end_index = tlst_string_size - 1
                for j, future_tlst_entry in enumerate(tlst_entries[i + 1:]): # find end_index (i.e. start index of next string)
                    if future_tlst_entry.filepath_offset != b'\xFF\xFF':
                        end_index = int.from_bytes(future_tlst_entry.filepath_offset, "big", signed=False) - 1
                        break
                    elif future_tlst_entry.name_offset != b'\xFF\xFF':
                        end_index = int.from_bytes(future_tlst_entry.name_offset, "big", signed=False) - 1
                        break


                tlst_entry.name = f.read(end_index - start_index) # if end_index != -1 else f.read(end_index)[:-1]
                #tlst_entry.name = str(tlst_entry.name, 'utf-8')
                f.read(1)

    if tlst_name == "Results": # play ending results song
        results_entry = next((x for x in tlst_entries if x.song_id == "F400"), None)
        return results_entry.filepath, b'', 0
    else: # pick song randomly out of available brstms and based on frequency
        entry_indices = range(len(tlst_entries))
        weights = [0]*len(tlst_entries)
        for i, tlst_entry in enumerate(tlst_entries):
            if len(glob.glob(glob.escape(os.path.join(sound_dir, "strm", tlst_entry.filepath)) + ".*")): # if file exists, add its weight
            #if os.path.isfile(os.path.join(sound_dir, "strm", tlst_entry.filepath + ".brstm")):
                weights[i] = tlst_entry.frequency

        chosen_song = tlst_entries[random.choices(entry_indices, weights)[0]] # pick a song
        return chosen_song.filepath, chosen_song.name, chosen_song.song_delay

def cleanup(foobar_path):
    #subprocess.Popen([config["foobarPath"], "/command:Remove Playlist"]) # ends up removing every playlist
    subprocess.Popen([foobar_path, "/exit"])

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    config = get_config()

    prev_rel_name = ""
    done = False
    print("Welcome to the (Unofficial) P+ Netplay Music Player! (press ` to exit at any time)")
    print("")

    if not os.path.isfile(config["foobarPath"]):
        print("Error: foobar2000 installation not detected")
        print("Please install foobar2000 (as well as its vgmstream plugin) to be able to play vgm music files (and other music files)")
        while not os.path.isfile(config["foobarPath"]):
            config = get_config()
            with keyboard.Events() as events:
                event = events.get(1)
                if event is None:
                    pass
                elif event.key == keyboard.KeyCode.from_char('q'):
                    sys.exit()

    print("foobar2000 installation detected. Ensure to install the vgmstream plugin on foobar2000 if you haven't yet in order to play brstms.")
    print("Also ensure to select 'Loop forever' in File->Preferences->Playback->Decoding->vgmstream")
    print("")
    if not os.path.isdir(os.path.join(config["soundDir"], "tracklist")) and not os.path.isdir(os.path.join(config["soundDir"], "strm")):
        print("Error: sound folder given in config is invalid")
        print("Please set soundDir in config.json to a your custom sound folder containing a tracklist subfolder (containing tlsts) and a strm subfolder (containing music files). The sound folder from P+ can be used to start with")
        while not os.path.isdir(os.path.join(config["soundDir"], "tracklist")) and not os.path.isdir(os.path.join(config["soundDir"], "strm")):
            config = get_config()
            with keyboard.Events() as events:
                event = events.get(1)
                if event is None:
                    pass
                elif event.key == keyboard.KeyCode.from_char('q'):
                    sys.exit()
    print("Valid sound folder detected. Reminder you can edit tracklists using BrawlCrate and drop music files in the strm folder (as well as subfolders)")

    atexit.register(cleanup, config["foobarPath"])
    subprocess.Popen([config["foobarPath"]])
    #subprocess.Popen([config["foobarPath"], "/command:New Playlist"])
    #subprocess.Popen([config["foobarPath"], "/hide"]) # doesn't stay hidden

    min_song_switch_time = 1.5
    last_played_timestamp = time.time()

    print("")
    print("To begin, please start P+ Netplay (reminder to check 'Client Side Music Off' to turn off in game music). Use left/right arrows to adjust volume")
    while not done:
        if not dolphin_memory_engine.is_hooked():
            dolphin_memory_engine.hook()
            if dolphin_memory_engine.is_hooked():
                print("Hooked to Dolphin")
        else:
            try:
                stex_bytes = dolphin_memory_engine.read_bytes(int(config["stexMemAddress"], 0), 512)  # read all stex bytes at once just in case stuff updates in between reading
                #stex_header_bytes = dolphin_memory_engine.read_bytes(int(config["stexMemAddress"],0), 12)#config["readSize"])
                if stex_bytes[0:4] == b'STEX':
                    stex_string_start_offset = int.from_bytes(stex_bytes[4:8], "big", signed=False)
                    stex_size = int.from_bytes(stex_bytes[8:12], "big", signed=False)
                    rel_name_offset = stex_bytes[32:36]   #dolphin_memory_engine.read_bytes(int(config["stexMemAddress"],0) + 32, 4)
                    rel_name_offset = 0 if rel_name_offset == b'\xff\xff\xff\xff' else int.from_bytes(rel_name_offset, "big", signed=False)
                    current_rel_name = stex_bytes[stex_string_start_offset + rel_name_offset:stex_string_start_offset + rel_name_offset + stex_size - rel_name_offset - stex_string_start_offset]  #dolphin_memory_engine.read_bytes(int(config["stexMemAddress"], 0) + stex_string_start_offset + rel_name_offset, stex_size - rel_name_offset - stex_string_start_offset )
                    #print(current_tlst_bytes)
                    if (prev_rel_name != current_rel_name):
                        stage_name_offset = int.from_bytes(stex_bytes[28:32], "big", signed=False) #int.from_bytes(dolphin_memory_engine.read_bytes(int(config["stexMemAddress"], 0) + 28, 4), "big", signed=False)
                        current_tlst_name = str(stex_bytes[stex_string_start_offset:stex_string_start_offset + stage_name_offset - 1], 'utf-8')#str(dolphin_memory_engine.read_bytes(int(config["stexMemAddress"], 0) + stex_string_start_offset, stage_name_offset - 1), 'utf-8')

                        print(f"Current tlst: {current_tlst_name}")
                        if os.path.isfile(os.path.join(config["soundDir"], "tracklist", current_tlst_name + ".tlst")):
                            chosen_song, song_name, song_delay = pick_song(current_tlst_name, config["soundDir"])
                            song_filepaths = glob.glob(glob.escape(os.path.join(config["soundDir"], "strm", chosen_song)) + ".*")
                            if len(song_filepaths):
                                if (config["displayTrackName"]):
                                    num_entries = int.from_bytes(
                                        dolphin_memory_engine.read_bytes(int(config["tlstMemAddress"], 0) + 6, 2), "big", signed=False)
                                    string_start_offset = int.from_bytes(
                                        dolphin_memory_engine.read_bytes(int(config["tlstMemAddress"], 0) + 10, 2), "big", signed=False)
                                    last_string_offset_bytes = dolphin_memory_engine.read_bytes(
                                        int("0x8053F200", 0) + 6 + num_entries * 16, 2)
                                    last_string_offset = int.from_bytes(last_string_offset_bytes, "big", signed=False)

                                    for i in range(1, num_entries):
                                        dolphin_memory_engine.write_bytes(int(config["tlstMemAddress"], 0) + 6 + i * 16,
                                                                          last_string_offset_bytes)

                                    dolphin_memory_engine.write_bytes(
                                        int(config["tlstMemAddress"], 0) + string_start_offset + last_string_offset, song_name + b"\00")

                                subprocess.Popen([config["foobarPath"], "/stop"])
                                subprocess.Popen([config["foobarPath"], "/command:Clear"])
                                print(f"Now playing: {str(song_name, 'utf-8')} ({os.path.basename(song_filepaths[0])})")

                                current_timestamp = time.time()

                                # play song (delay if there is a set delay)
                                if song_delay == -1 and config['useDelay']: # start song at end of countdown
                                    time.sleep(3)  # assume no lag (takes around 3 seconds from start to end of countdown)
                                elif song_delay <= 0 or not config['useDelay']:
                                    if (current_timestamp - last_played_timestamp < min_song_switch_time):
                                        time.sleep(min_song_switch_time - (current_timestamp - last_played_timestamp)) # delay for switching songs (otherwise songs will get added together)
                                    else:
                                        time.sleep(0.1) # minimum delay otherwise commands happen to fast and added song will start stopped
                                else: # start song after desired number of frames
                                    if (song_delay/60 < min_song_switch_time) and (current_timestamp - last_played_timestamp < min_song_switch_time):
                                        time.sleep(min_song_switch_time - (current_timestamp - last_played_timestamp)) # delay for switching songs (otherwise songs will get added together
                                    else:
                                        time.sleep(max(0.1, song_delay / 60))  # song_delay is in frames, Brawl runs 60fps, assume no lag

                                subprocess.Popen([config["foobarPath"], song_filepaths[0]])

                                last_played_timestamp = current_timestamp

                        prev_rel_name = current_rel_name

            except RuntimeError:
                dolphin_memory_engine.un_hook()
                subprocess.Popen([config["foobarPath"], "/stop"])
                prev_rel_name = ""
                print("Unhooked to Dolphin")


        with keyboard.Events() as events:
            event = events.get(config["readFreq"])
            if event is None:
                pass
            elif event.key == keyboard.Key.left:
                subprocess.Popen([config["foobarPath"], "/command:Down"])
            elif event.key == keyboard.Key.right:
                subprocess.Popen([config["foobarPath"], "/command:Up"])
            elif event.key == keyboard.KeyCode.from_char('`'):
                done = True

    dolphin_memory_engine.un_hook()

    cleanup(config["foobarPath"])


    # (install vgmstream component for foobar)
    # (set path of foorbar3000.exe to config) C:\Program Files (x86)\foobar2000
    # (set foobar to loop forever in Playback -> Decoding -> vgmstream)

    ## Fixed Spear Pillar, Shadow Moses Island, Castle Siege, Lylat Cruise, Mushroomy Kingdom

    # TODO: Fix playback not playing / stacking instead

    # TODO: Switch to dedicated playlist (to avoid overwriting other active playlists)

    # TODO: support pinch

    # TODO: Support stage params so new tlsts can be added

    # TODO: Cross platform (py-dme doesn't support mac however) (also need to consider controls)

    # TODO: change in game song text to song being played (find address, write to it and see if it causes a desync)
    # At 8053F200 according to ASM code in MyMusic.asm, exact same structure as tlst, need to reorganize the strings (or what if you just dumped the tlst to the memory address), or just make a single entry. Might have to replace strings of every entry unless can find which entry was picked

    # TODO: support volume? use percentage of current volume?

    # TODO: redo it in lua to be part of m-overlay?

    # TODO: try to write brstm stream bytes in-game?

    # TODO: override MyMusic?? might happen too fast, maybe would have to add a delay in assembly but then would cause desync.


