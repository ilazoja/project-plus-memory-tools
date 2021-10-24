
import os
import time
import subprocess
import getpass

import dolphin_memory_engine
import websocket

import obswebsocket, obswebsocket.requests

def record_match(client):
    stage_id = dolphin_memory_engine.read_word(int("0x8062B3B4", 0))
    if stage_id != 255 and stage_id != 40: # if in a match and it's not the results screen
        ## Start recording in OBS
        try:
            client.call(obswebsocket.requests.StartRecording())
        except websocket._exceptions.WebSocketConnectionClosedException:
            print("Could not connect to OBS")

        while (dolphin_memory_engine.read_word(int("0x8062B3B4", 0)) != 255): # while still in a match (stage id of not 255 means you are still in game)
            pass

        try:
            client.call(obswebsocket.requests.StopRecording())
        except websocket._exceptions.WebSocketConnectionClosedException:
            pass

def hold_A_until_match_started():
    stage_id = dolphin_memory_engine.read_word(int("0x8062B3B4", 0))
    while (stage_id >= 255 or stage_id <= 0): # Stage id of 255 means you are not in game (and are probably in the menu)
        # hold A while the game is still in the menu
        #dolphin_memory_engine.write_bytes(int("0x805BC068",0), bytes.fromhex("8001")) # set player 1 input to 'A'
        dolphin_memory_engine.write_word(int("0x805BAD04", 0), int("0x00000100",0)) # set player 1 button to 'A'
        time.sleep(0.1)
        dolphin_memory_engine.write_word(int("0x805BAD04", 0), int("0x00000000", 0))
        stage_id = dolphin_memory_engine.read_word(int("0x8062B3B4", 0))

def press_right():
    # maybe should nop instruction that writes to button address for consistency?

    for i in range(100): # Hold for a bit since the game will overwrite the button input
        # dolphin_memory_engine.write_bytes(int("0x805BC068", 0), bytes.fromhex("C8C0")) # set player 1 input to 'dpad right'
        dolphin_memory_engine.write_word(int("0x805BAD04", 0), int("0x00000002",0)) # set player 1 input to 'dpad right'

def parse_range(numbers: str):
    for x in numbers.split(','):
        x = x.strip()
        if x.isdigit():
            yield int(x)
        elif x[0] == '<':
            yield from range(1, int(x[1:]))
        elif '-' in x:
            xr = x.split('-')
            yield from range(int(xr[0].strip()), int(xr[1].strip())+1)
        else:
            raise ValueError(f"Unknown range specified: {x}")

if __name__ == '__main__':
    print("Welcome to the P+ Replay Recorder! This program will automatically go through every replay in your P+ Dolphin and tell OBS to record")
    print("Make sure you have OBS and OBS Websocket installed and have OBS open")

    ## Connect to OBS
    try:
        client = obswebsocket.obsws("localhost", 4444, getpass.getpass("If authentication is enabled on OBS Websocket (set in Tools -> WebSockets Server Settings in OBS), enter passcode: ")) # for some reason will hang when pressing run with pycharm, works with debug though
        client.connect()
        client.call(obswebsocket.requests.GetVersion()).getObsWebsocketVersion()
        print("Connected to OBS")
    except obswebsocket.exceptions.ConnectionFailure:
        print("Could not connect to OBS. Make sure you installed OBS and the OBS Websocket and that OBS is open if you want to use OBS to record as well as ensure that you put the right passcode from Tools -> WebSockets Server Settings if authentication is enabled.")

    print("")
    mode = input("Type whether you want to record replays or live gameplay (Replay [r], Live [l]): ").lower()
    print("Run P+ in Dolphin to start")
    done = False

    current_replay = 0

    while not done:
        if not dolphin_memory_engine.is_hooked():
            dolphin_memory_engine.hook()
            if dolphin_memory_engine.is_hooked():
                if mode == 'replay' or mode == 'r':
                    print("Hooked to Dolphin, waiting for replays to be loaded...")
                else:
                    print("Hooked to Dolphin, will record matches...")
        else:
            try:
                pass
                frames_into_runtime = dolphin_memory_engine.read_word(int("0x805B5014", 0))
                #num_replays = dolphin_memory_engine.read_word(int("0x815C3D20", 0))

                if mode == 'replay' or mode == 'r':
                    num_replays = dolphin_memory_engine.read_word(int("0x815E8398", 0))

                    if (num_replays == 0 or num_replays > 100000) or (frames_into_runtime < 300):

                        ## makeshift gecko hook to tell the game to start at replay scene

                        dolphin_memory_engine.write_word(int("0x806dd600",0), int('0x4BE61BF4',0)) # b 0x053f1f4 [branch to end of STEX memory]
                        #dolphin_memory_engine.write_bytes(int("0x8053f1f4",0), bytes.fromhex("38951D68")) # addi r4, r21, 0x1884 [for Main Menu scene]
                        dolphin_memory_engine.write_word(int("0x8053f1f4", 0), int("0x38951884",0))  # addi r4, r21, 0x1D68 [for Replay scene]
                        dolphin_memory_engine.write_word(int("0x8053f1f8",0), int("0x80c60000",0)) # r6, 0 (r6) [original function]
                        dolphin_memory_engine.write_word(int("0x8053f1fc",0), int("0x4819E408",0)) # b 0x06dd604 [branch back]

                        ## Found addresses by looking at register at breakpoint around 0x806DD5F8 (which is where Boot Directly to CSS v4 writes to).
                        # 80701d68 - Main Menu scene string address (sqMenuMain)
                        # 80701b54 - CSS scene string address (sqVsMelee)
                        # 80701884 - Replay scene string address (sqReplay) (Found by string searching in DME)

                    else:
                        dolphin_memory_engine.write_bytes(int("0x806dd600", 0), bytes.fromhex('80c60000')) # reset to original behaviour just in case
                        print("Replays loaded")
                        print("")

                        ## Get user input for replays to skip and what to
                        print("Set up scene in OBS, then in the in-game replay menu select 'SD Card -> Check Content' if you want to obtain the replays from the virtual sd card.")

                        replays_to_skip = input("Once ready, type any replay indices you want to skip (e.g. <3,5-7,9) and press enter to begin recording: ")
                        replays_to_skip = list(parse_range(replays_to_skip))

                        num_replays = dolphin_memory_engine.read_word(int("0x815E8398", 0))

                        ## Automatically go through each replay
                        for i in range(num_replays):
                            current_replay = i + 1
                            if current_replay in replays_to_skip:
                                print(f"Skipping Replay ({current_replay}/{num_replays})...")
                                time.sleep(2)
                            else:
                                hold_A_until_match_started()
                                time.sleep(0.5)
                                print(f"Recording Replay ({current_replay}/{num_replays})...")
                                record_match(client)
                                time.sleep(4)

                            press_right()
                        print("Recorded all replays")
                        break

                else:
                    record_match(client)


            except RuntimeError:
                dolphin_memory_engine.un_hook()
                print("Unhooked to Dolphin")


        #time.sleep(0.1)

## TODO: detect desync matches that stall

## TODO: Is it possible to display the length of a replay when scrolling through? (not if file is in sd.raw though)

### Steps taken
# Investigated [Legacy TE] Boot Directly to CSS v4  [PyotrLuzhin] code
# Investigated difference between above and Skip Opening Song/Title and go to Main Menu [PyotrLuzhin, Desi]. (Used codewrite to convert hex to asm and vice versa, can start as a C2 code even though it is a 06 code)
# Difference was the first line, memory address offset was different
# Tried changing the asm using Dolphin Memory Address at 0x806DD5F8 to Main Menu variant however gecko kept overwriting the code
# Opted to instead branch after to the end of STEX memory and write ASM there (which is how C2 codes in Gecko works) which worked
# Through breakpointing at around 0x806DD5F8, at looking at the r4 register, it was realized that the address being held points to the name of the scene (e.g.0x80701d68 - sqMenuMain)
# Using Dolphin Memory Engine string search, I searched "Replay" and found sqReplay at 0x80701884

# Found number of Replay address through DME (kept searching for int of exact value of how many replays, and kept changing number of replays)
