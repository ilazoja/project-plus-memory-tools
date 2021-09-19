# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

#pip install dolphin_memory_engine
#pip install pynput

import os
import sys
import random
import glob
import subprocess

import dolphin_memory_engine
from pynput import keyboard
import time


from utils import BRAWL_BRSTM_DICT

SOUND_DIR = "C:/Users/Ilir/Documents/Games/Brawl/Project+ Modding/Experimental/SD/Project+/pf/sound/"
FOOBAR_PATH = "C:/Program Files (x86)/foobar2000/foobar2000.exe"

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

        self.name = ""
        self.filepath = ""

def pick_song(tlst_name):
    # parse tlst and pick songs based on frequencies and if song is present

    with open(os.path.join(SOUND_DIR, "tracklist", tlst_name + ".tlst"), "rb") as f:
        f.seek(12) # skip header

        tlst_entries = []

        while (current_bytes := f.read(2)): # read each tlst entry
            if current_bytes == b'\x00\x00': # entries start with 0000
                song_id = f.read(2).hex().upper()
                song_delay = int.from_bytes(f.read(2), "big", signed=True)
                volume = int.from_bytes(f.read(1), "big", signed=False)
                frequency = int.from_bytes(f.read(1), "big", signed=False)
                filepath_offset = f.read(2)
                name_offset = f.read(2)
                song_switch = int.from_bytes(f.read(2), "big", signed=False)
                disable_stock_pinch = bool.from_bytes(f.read(1), "big")
                hidden_from_tracklist = bool.from_bytes(f.read(1), "big")

                tlst_entries.append(TLSTEntryNode(song_id, song_delay, volume, frequency, song_switch, disable_stock_pinch, hidden_from_tracklist, name_offset, filepath_offset))

            else:
                break
        f.seek(-2, 1)

        # start parsing strings (filepath and name) which is found at the end of the tlst
        for i, tlst_entry in enumerate(tlst_entries):
            if tlst_entry.filepath_offset != b'\xff\xff':
                start_index = int.from_bytes(tlst_entry.filepath_offset, "big", signed=False)
                end_index = -1
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

                tlst_entry.filepath = f.read(end_index - start_index) if end_index != -1 else f.read(end_index)[:-1]
                tlst_entry.filepath = str(tlst_entry.filepath, 'utf-8')
                f.read(1)
            else:
                if tlst_entry.song_id[0] != 'F': # if song id starts with F, it is a custom id. If it doesn't then grab Brawl filepath based on song id
                    tlst_entry.filepath = BRAWL_BRSTM_DICT.get(tlst_entry.song_id, "")
            if tlst_entry.name_offset != b'\xff\xff':
                start_index = int.from_bytes(tlst_entry.name_offset, "big", signed=False)
                end_index = -1
                for j, future_tlst_entry in enumerate(tlst_entries[i + 1:]): # find end_index (i.e. start index of next string)
                    if future_tlst_entry.filepath_offset != b'\xFF\xFF':
                        end_index = int.from_bytes(future_tlst_entry.filepath_offset, "big", signed=False) - 1
                        break
                    elif future_tlst_entry.name_offset != b'\xFF\xFF':
                        end_index = int.from_bytes(future_tlst_entry.name_offset, "big", signed=False) - 1
                        break


                tlst_entry.name = f.read(end_index - start_index) if end_index != -1 else f.read(end_index)[:-1]
                tlst_entry.name = str(tlst_entry.name, 'utf-8')
                f.read(1)

    if tlst_name == "Results": # play ending results song
        results_entry = next((x for x in tlst_entries if x.song_id == "F400"), None)
        return results_entry.filepath
    else: # pick song randomly out of available brstms and based on frequency
        entry_indices = range(len(tlst_entries))
        weights = [0]*len(tlst_entries)
        for i, tlst_entry in enumerate(tlst_entries):
            if len(glob.glob(os.path.join(SOUND_DIR, "strm", tlst_entry.filepath + ".*"))): # if file exists, add its weight
            #if os.path.isfile(os.path.join(SOUND_DIR, "strm", tlst_entry.filepath + ".brstm")):
                weights[i] = tlst_entry.frequency

        return tlst_entries[random.choices(entry_indices, weights)[0]].filepath # pick a song

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    prev_tlst = ""
    subprocess.Popen([FOOBAR_PATH])

    done = False
    print("Not hooked to Dolphin")
    while not done:
        if not dolphin_memory_engine.is_hooked():
            dolphin_memory_engine.hook()
            if dolphin_memory_engine.is_hooked():
                print("Hooked to Dolphin")
        else:
            try:
                tlst_bytes = dolphin_memory_engine.read_bytes(2152984620, 50) # 8053F02C tlst memory address in int
                current_tlst = str(tlst_bytes, 'utf-8').split("\x00", 1)[0]
                if current_tlst != '' and current_tlst != prev_tlst:
                    print(f"Current tlst: {current_tlst}")
                    chosen_song = pick_song(current_tlst)
                    song_filepaths = glob.glob(os.path.join(SOUND_DIR, "strm", chosen_song + ".*"))
                    if len(song_filepaths):
                        print(f"Now playing {os.path.basename(song_filepaths[0])}")
                        subprocess.Popen([FOOBAR_PATH, song_filepaths[0]])

                    prev_tlst = current_tlst

            except RuntimeError:
                dolphin_memory_engine.un_hook()
                subprocess.Popen([FOOBAR_PATH, "/pause"])
                prev_tlst = ""
                print("Unhooked to Dolphin")


        with keyboard.Events() as events:
            event = events.get(0.5)
            if event is None:
                pass
            elif event.key == keyboard.Key.esc:
                done = True

    dolphin_memory_engine.un_hook()

    subprocess.Popen([FOOBAR_PATH, "/exit"])

    # (install vgmstream component for foobar)
    # (set path of foorbar3000.exe to config) C:\Program Files (x86)\foobar2000
    # (set foobar to loop forever in Playback -> Decoding -> vgmstream)



        #print(tlst_entries)



            # Do stuff with byte.



# See PyCharm help at https://www.jetbrains.com/help/pycharm/

# Check if brstm exists before adding to random