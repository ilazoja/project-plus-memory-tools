
#pip install dolphin_memory_engine
#pip install pynput

import os
import sys
import random
import glob
import subprocess
import atexit
from enum import Enum

import dolphin_memory_engine
from pynput import keyboard
import time

from utils import CONFIG_JSON, BRAWL_BRSTM_DICT, get_config
from memory_utils import *

class PlayStatus(Enum):
    STOPPED = 0
    STAGE_LOADED = 1
    PLAYING = 2
    PINCH = 3
    GAME_ENDED = 4

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

def pick_song(tlst_name, sound_dir, tracklist_folder):
    # parse tlst and pick songs based on frequencies and if song is present

    with open(os.path.join(sound_dir, tracklist_folder, tlst_name + ".tlst"), "rb") as f:

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
        return results_entry#.filepath, b'', 0
    else: # pick song randomly out of available brstms and based on frequency
        entry_indices = range(len(tlst_entries))
        weights = [0]*len(tlst_entries)
        for i, tlst_entry in enumerate(tlst_entries):
            if len(glob.glob(glob.escape(os.path.join(sound_dir, "strm", tlst_entry.filepath)) + ".*")): # if file exists, add its weight
            #if os.path.isfile(os.path.join(sound_dir, "strm", tlst_entry.filepath + ".brstm")):
                weights[i] = tlst_entry.frequency

        chosen_song_entry = tlst_entries[random.choices(entry_indices, weights)[0]] # pick a song
        return chosen_song_entry#.filepath, chosen_song.name, chosen_song.song_delay

def cleanup(foobar_path):
    #subprocess.Popen([config["foobarPath"], "/command:Remove Playlist"]) # ends up removing every playlist
    subprocess.Popen([foobar_path, "/exit"])

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    config = get_config()

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
    print("Also ensure to select 'Loop forever' in File->Preferences->Playback->Decoding->vgmstream and uncheck 'Bring to front when adding new files' in File->Preferences->Shell Integration")
    print("")
    if not os.path.isdir(os.path.join(config["soundDir"], config["tracklistFolder"])) and not os.path.isdir(os.path.join(config["soundDir"], "strm")):
        print("Error: sound folder given in config is invalid")
        print(f"Please set soundDir in {CONFIG_JSON} to a your custom sound folder containing a tracklist subfolder (containing tlsts) and a strm subfolder (containing music files). The sound folder from P+ can be used to start with")
        while not os.path.isdir(os.path.join(config["soundDir"], config["tracklistFolder"])) and not os.path.isdir(os.path.join(config["soundDir"], "strm")):
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
    time.sleep(1)
    subprocess.Popen([config["foobarPath"], "/stop"])
    subprocess.Popen([config["foobarPath"], "/command:Clear"])
    #subprocess.Popen([config["foobarPath"], "/command:New Playlist"])
    #subprocess.Popen([config["foobarPath"], "/hide"]) # doesn't stay hidden

    min_song_switch_time = 1.5
    chosen_song_entry = None
    song_filepaths = []
    use_pinch = False
    play_status = PlayStatus.STOPPED
    prev_rel_name = ""
    prev_stage_name = ""
    prev_stage_id = -1
    last_played_timestamp = time.time()
    done = False

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
                if stex_bytes[0:4] == b'STEX': # check if game loaded (an stex param file got loaded)
                    stex_string_start_offset = int.from_bytes(stex_bytes[4:8], "big", signed=False)
                    stex_size = int.from_bytes(stex_bytes[8:12], "big", signed=False)
                    rel_name_offset = stex_bytes[32:36]   #dolphin_memory_engine.read_bytes(int(config["stexMemAddress"],0) + 32, 4)
                    rel_name_offset = 0 if rel_name_offset == b'\xff\xff\xff\xff' else int.from_bytes(rel_name_offset, "big", signed=False)
                    current_rel_name = stex_bytes[stex_string_start_offset + rel_name_offset:stex_string_start_offset + rel_name_offset + stex_size - rel_name_offset - stex_string_start_offset - 1]  #dolphin_memory_engine.read_bytes(int(config["stexMemAddress"], 0) + stex_string_start_offset + rel_name_offset, stex_size - rel_name_offset - stex_string_start_offset )
                    #print(current_tlst_bytes)
                    stage_name_offset = int.from_bytes(stex_bytes[28:32], "big", signed=False)  # int.from_bytes(dolphin_memory_engine.read_bytes(int(config["stexMemAddress"], 0) + 28, 4), "big", signed=False)
                    current_stage_name = str(stex_bytes[stex_string_start_offset + stage_name_offset:stex_string_start_offset + rel_name_offset - 1], 'utf-8')
                    if (prev_rel_name != current_rel_name or prev_stage_name != current_stage_name): # if rel name changed, that means stage changed
                        current_tlst_name = str(stex_bytes[stex_string_start_offset:stex_string_start_offset + stage_name_offset - 1], 'utf-8')#str(dolphin_memory_engine.read_bytes(int(config["stexMemAddress"], 0) + stex_string_start_offset, stage_name_offset - 1), 'utf-8')

                        print(f"Current tlst: {current_tlst_name}")
                        if os.path.isfile(os.path.join(config["soundDir"], config["tracklistFolder"], current_tlst_name + ".tlst")):
                            chosen_song_entry = pick_song(current_tlst_name, config["soundDir"], config["tracklistFolder"])
                            song_filepaths = glob.glob(glob.escape(os.path.join(config["soundDir"], "strm", chosen_song_entry.filepath)) + ".*")
                            if len(song_filepaths):
                                subprocess.Popen([config["foobarPath"], "/stop"])
                                #subprocess.Popen([config["foobarPath"], "/command:Clear"]) # only will clear on focus
                                #subprocess.Popen([config["foobarPath"], "/add", "/immediate", song_filepaths[0]])
                                print(f"Now playing: {str(chosen_song_entry.name, 'utf-8')} ({os.path.basename(song_filepaths[0])})")
                                play_status = play_status.STOPPED
                                use_pinch = False
                                num_players = -1
                                prev_stock_count = [-2, -2, -2, -2]
                                last_stock_loss_frame = [-1, -1, -1, -1]

                                if (config["displayTrackName"]):
                                    # Hijack each tlst entries' trackname offset in memory to point to the last tlst entry's trackname string
                                    # Then overwrite the last entry's trackname string
                                    # When the game looks for the track name to display, every tlst entry will point to the same track name

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

                                    # shorten just in case title goes over memory limit for tlst
                                    if string_start_offset + last_string_offset + len(chosen_song_entry.name) < 3920:
                                        song_name = chosen_song_entry.name[0:3920 - string_start_offset - last_string_offset - len(chosen_song_entry.name)]
                                    else:
                                        song_name = b''

                                    dolphin_memory_engine.write_bytes(
                                        int(config["tlstMemAddress"], 0) + string_start_offset + last_string_offset, song_name + b"\00")

                                time.sleep(0.1) # neccessary to prevent stop and start occurring simultaneously causing song to be added and then stopped

                        prev_rel_name = current_rel_name
                        prev_stage_name = current_stage_name

                    frames_into_current_game = get_frames_into_current_game()
                    if frames_into_current_game > 0:
                        stock_count = get_stock_count()
                        if num_players == -1:
                            num_players = sum((s > 0 or s == -1) for s in stock_count)
                        for player_num, (prev_player_stocks, player_stocks) in enumerate(zip(prev_stock_count, stock_count)):
                            if player_stocks < prev_player_stocks:
                                last_stock_loss_frame[player_num] = frames_into_current_game

                        prev_stock_count = stock_count

                    ## Detect pinch
                    if not use_pinch and chosen_song_entry.song_switch:
                        pinch_song_filepaths = glob.glob(glob.escape(os.path.join(config["soundDir"], "strm", chosen_song_entry.filepath + "_b")) + ".*")
                        if len(pinch_song_filepaths):
                            if isSuperSuddenDeath() or isBombRain() or isWildBrawl() or isSuddenDeath():
                                print("PINCH")
                                use_pinch = True
                                song_filepaths = pinch_song_filepaths
                            elif chosen_song_entry and frames_into_current_game > 0: # did match start (i.e. frames into match > 0)
                                if isPinchTime(chosen_song_entry.song_switch):
                                    print("PINCH")
                                    use_pinch = True
                                    song_filepaths = pinch_song_filepaths
                                elif not chosen_song_entry.disable_stock_pinch and isPinchStock(stock_count, last_stock_loss_frame, frames_into_current_game):
                                    print("PINCH")
                                    use_pinch = True
                                    song_filepaths = pinch_song_filepaths

                    # TODO: don't play results song if No Contest, detect if results, detect winner and play theme until duration of song (if it's not a looping song) then switch to results song

                    ## FSM to keep track of music playing / game state
                    stage_id = get_stage_id()
                    current_timestamp = time.time()
                    if play_status == PlayStatus.STOPPED:
                        if (stage_id != 255 and stage_id != prev_stage_id) or current_rel_name == b'st_config.rel': # Check if stage loaded or menu loaded
                            play_status = PlayStatus.STAGE_LOADED
                            prev_stage_id = stage_id
                            stage_loaded_timestamp = time.time()
                    if play_status == PlayStatus.STAGE_LOADED:
                        # play song (delay if there is a set delay)
                        if isEndOfGame():
                            play_status = PlayStatus.GAME_ENDED
                        elif use_pinch or not config['useDelay'] or chosen_song_entry.song_delay != -1:
                            if (current_timestamp - last_played_timestamp >= min_song_switch_time) and (use_pinch or current_timestamp - stage_loaded_timestamp >= chosen_song_entry.song_delay / 60):
                                # delay for switching songs otherwise songs will get added together as well as song delay to delay after match is staarted, song_delay is in frames, Brawl runs 60fps, assume no lag.
                                subprocess.Popen([config["foobarPath"], "/immediate", song_filepaths[0]])  # "/next"])
                                play_status = PlayStatus.PINCH if use_pinch else PlayStatus.PLAYING
                                last_played_timestamp = current_timestamp
                                prev_stage_id = stage_id
                        elif chosen_song_entry.song_delay == -1:  # start song at end of countdown
                            if frames_into_current_game > 0: # if Frames Into Current Game is greater than 0 i.e. game started
                                subprocess.Popen([config["foobarPath"], "/immediate", song_filepaths[0]]) #"/next"])
                                play_status = PlayStatus.PINCH if use_pinch else PlayStatus.PLAYING
                                last_played_timestamp = current_timestamp
                                prev_stage_id = stage_id
                    if play_status == play_status.PLAYING:
                        if isEndOfGame() and not isStamina(): # detect end of game, will get triggered if stock is lost during stamina so made stamina mode check
                            subprocess.Popen([config["foobarPath"], "/stop"])
                            play_status = PlayStatus.GAME_ENDED
                            time.sleep(0.1)
                        elif (current_timestamp - last_played_timestamp >= min_song_switch_time and use_pinch):
                            subprocess.Popen([config["foobarPath"], "/immediate", song_filepaths[0]])  # "/next"])
                            play_status = PlayStatus.PINCH
                            last_played_timestamp = current_timestamp
                    if play_status == play_status.PINCH:
                        if isEndOfGame() and not isStamina():  # detect end of game, will get triggered if stock is lost during stamina so made stamina mode check
                            subprocess.Popen([config["foobarPath"], "/stop"])
                            play_status = PlayStatus.GAME_ENDED
                            time.sleep(0.1)
                    if play_status == PlayStatus.GAME_ENDED:
                        current_num_players_remaining = sum((s > 0 or s == -1) for s in stock_count)
                        if current_timestamp - last_played_timestamp >= min_song_switch_time and (not isEndOfGame() and num_players == current_num_players_remaining):
                            subprocess.Popen([config["foobarPath"], "/immediate", song_filepaths[0]]) # "/next"])
                            play_status = PlayStatus.PINCH if use_pinch else PlayStatus.PLAYING
                            last_played_timestamp = current_timestamp


            except RuntimeError:
                dolphin_memory_engine.un_hook()
                subprocess.Popen([config["foobarPath"], "/stop"])
                prev_stage_id = -1
                play_status = play_status.STOPPED
                prev_rel_name = ""
                prev_stage_name = ""
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

    # TODO: Switch to dedicated playlist (to avoid overwriting other active playlists)

    ## Supports pinch
    # at mem address 805A7B18 shows song currently playing, check if song changes. Won't work, pinch might be select by tlst outside, not every tlst in game has a pinch
    # or check pinch asm to see what addresses to look for in requirements
    # check DME address file

    # TODO: Support stage params so new tlsts can be added
    # Use stageid, but might have to figure out which out which button combo was picked (maybe determine by .pac, only limitation would be if two alts share the saame.pac)
    # if param / stage id doesn't exist then use tlst name loaded in game
    # Problem is that when the stage id changes, perhaps track name would already be loaded

    # TODO: Cross platform (py-dme doesn't support mac however) (also need to consider controls)

    ## change in game song text to song being played (found tlst address and wrote to it). Doesn't seem to cause a desync
    # tlst is at 8053F200 according to ASM code in MyMusic.asm, exact same structure as tlst.

    # TODO: support volume? use percentage of current volume?

    # TODO: Support victory themes
    # Find using Song ID

    # TODO: Switch menu tracks as you enter CSS just like in game
    # When you leave CSS (from backing out), and when you enter CSS
    # Make optional

    # TODO: Handle edge cases like single player modes where tlst doesn't get loaded e.g. Master Hand. Check if song id changes while tlst doesn't change


    # TODO: redo it in lua to be part of m-overlay?

    # TODO: try to write brstm stream bytes in-game?

    # TODO: override MyMusic?? might happen too fast, maybe would have to add a delay in assembly but then would cause desync.






