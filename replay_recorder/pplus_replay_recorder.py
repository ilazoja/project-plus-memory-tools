
import os
import dolphin_memory_engine
import time

def record_replay():

    ## TODO: Activate OBS

    while (dolphin_memory_engine.read_word(int("0x8062B3B4", 0)) != 255): # while still in a match
        pass

def hold_A_until_match_started():
    stage_id = dolphin_memory_engine.read_word(int("0x8062B3B4", 0))
    while (stage_id >= 255 or stage_id <= 0):
        # hold A while the game is still in the menu
        #dolphin_memory_engine.write_bytes(int("0x805BC068",0), bytes.fromhex("8001")) # set player 1 input to 'A'
        dolphin_memory_engine.write_word(int("0x805BAD04", 0), int("0x00000100",0)) # set player 1 button to 'A'
        time.sleep(0.1)
        dolphin_memory_engine.write_word(int("0x805BAD04", 0), int("0x00000000", 0))
        stage_id = dolphin_memory_engine.read_word(int("0x8062B3B4", 0))

def press_right():
    # maybe should nop instruction that writes to button address for consistency?

    for i in range(100):
        # dolphin_memory_engine.write_bytes(int("0x805BC068", 0), bytes.fromhex("C8C0")) # set player 1 input to 'dpad right'
        dolphin_memory_engine.write_word(int("0x805BAD04", 0), int("0x00000002",0)) # set player 1 input to 'dpad right'

if __name__ == '__main__':

    print("Run P+ in Dolphin to start")
    done = False

    is_loaded = False
    is_ingame = False
    current_replay = 0

    while not done:
        if not dolphin_memory_engine.is_hooked():
            dolphin_memory_engine.hook()
            if dolphin_memory_engine.is_hooked():
                print("Hooked to Dolphin, looking for replays...")
        else:
            try:
                pass
                #frames_into_runtime = dolphin_memory_engine.read_word(int("0x805B5014", 0))
                num_replays = dolphin_memory_engine.read_word(int("0x815C3D20", 0))

                if num_replays == 0 or num_replays > 100000:

                    dolphin_memory_engine.write_word(int("0x806dd600",0), int('0x4BE61BF4',0)) # b 0x053f1f4 [branch to end of STEX memory]
                    #dolphin_memory_engine.write_bytes(int("0x8053f1f4",0), bytes.fromhex("38951D68")) # addi r4, r21, 0x1884 [for Main Menu scene]
                    dolphin_memory_engine.write_word(int("0x8053f1f4", 0), int("0x38951884",0))  # addi r4, r21, 0x1D68 [for Replay scene]
                    dolphin_memory_engine.write_word(int("0x8053f1f8",0), int("0x80c60000",0)) # r6, 0 (r6) [original function]
                    dolphin_memory_engine.write_word(int("0x8053f1fc",0), int("0x4819E408",0)) # b 0x06dd604 [branch back]

                    ## Found addresses by looking at register at breakpoint around 0x806DD5F8 (which is where Boot Directly to CSS v4 writes to).
                    # 80701d68 - Main Menu scene string address (sqMenuMain)
                    # 80701b54 - CSS scene string address (sqVsMelee)
                    # 80701884 - Replay scene string address? (sqReplay) (Found by string searching in DME)

                else:
                    if not is_loaded:
                        print("Replays loaded, starting to record")
                        dolphin_memory_engine.write_bytes(int("0x806dd600", 0), bytes.fromhex('80c60000')) # reset to original behaviour just in case
                        is_loaded = True

                    # TODO: Have functionality to start at a certain replay index (scroll to start) and end a certain replay index

                    test = dolphin_memory_engine.read_bytes(int("0x9017DA00", 0), 4)[1:4]
                    for i in range(current_replay, num_replays):
                        current_replay = i

                        hold_A_until_match_started()
                        time.sleep(1)
                        print(f"Recording Replay ({current_replay + 1}/{num_replays})...")
                        record_replay()
                        time.sleep(5)
                        press_right()
                    print("Recorded all replays")
                    break


            except RuntimeError:
                dolphin_memory_engine.un_hook()
                is_loaded = False
                print("Unhooked to Dolphin")


        #time.sleep(0.1)

### Steps taken
# Investigated [Legacy TE] Boot Directly to CSS v4  [PyotrLuzhin] code
# Investigated difference between above and Skip Opening Song/Title and go to Main Menu [PyotrLuzhin, Desi]. (Used codewrite to convert hex to asm and vice versa, can start as a C2 code even though it is a 06 code)
# Difference was the first line, memory address offset was different
# Tried changing the asm using Dolphin Memory Address at 0x806DD5F8 to Main Menu variant however gecko kept overwriting the code
# Opted to instead branch after to the end of STEX memory and write ASM there (which is how C2 codes in Gecko works) which worked
# Through breakpointing at around 0x806DD5F8, at looking at the r4 register, it was realized that the address being held points to the name of the scene (e.g.0x80701d68 - sqMenuMain)
# Using Dolphin Memory Engine string search, I searched "Replay" and found sqReplay at 0x80701884

# Found number of Replay address through DME (kept searching for int of exact value of how many replays, and kept changing number of replays)
