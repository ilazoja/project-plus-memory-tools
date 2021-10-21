
import os
import time
import dolphin_memory_engine
import time

if __name__ == '__main__':

    # config = get_config()

    # tlst_name = "Battlefield_Melee" #"Mushroom_Kingdom_64"
    #
    # with open(os.path.join(config["soundDir"], "tracklist", tlst_name + ".tlst"), "rb") as f:
    #     tlst_bytes = f.read()
    #
    #     i = 12
    #
    #     while(len(tlst_bytes[i:i+2]) == 2):
    #         if tlst_bytes[i:i+2] == b'\x00\x00':






    print("Run P+ in Dolphin to start")
    done = False

    is_loaded = False
    is_ingame = False

    prev_bytes = ""
    while not done:
        if not dolphin_memory_engine.is_hooked():
            dolphin_memory_engine.hook()
            if dolphin_memory_engine.is_hooked():
                print("Hooked to Dolphin, Looking for replays")
        else:
            try:
                pass
                #frames_into_runtime = dolphin_memory_engine.read_word(int("0x805B5014", 0))
                #8053f1f4
                #if frames_into_runtime < 10000000000000000 and frames_into_runtime > 150:

                num_replays = dolphin_memory_engine.read_word(int("0x9017DA00", 0))
                if num_replays == 0:

                    dolphin_memory_engine.write_bytes(int("0x806dd600",0), bytes.fromhex('4BE61BF4')) # b 0x053f1f4 [branch to end of STEX memory]
                    #dolphin_memory_engine.write_bytes(int("0x8053f1f4",0), bytes.fromhex("38951D68")) # addi r4, r21, 0x1884 [for Main Menu scene]
                    dolphin_memory_engine.write_bytes(int("0x8053f1f4", 0), bytes.fromhex("38951884"))  # addi r4, r21, 0x1D68 [for Replay scene]
                    dolphin_memory_engine.write_bytes(int("0x8053f1f8",0), bytes.fromhex("80c60000")) # r6, 0 (r6) [original function]
                    dolphin_memory_engine.write_bytes(int("0x8053f1fc",0), bytes.fromhex("4819E408")) # b 0x06dd604 [branch back]

                    ## Found addresses by looking at register at breakpoint around 0x806DD5F8 (which is where Boot Directly to CSS v4 writes to).
                    # 80701d68 - Main Menu scene string address (sqMenuMain)
                    # 80701b54 - CSS scene string address (sqVsMelee)
                    # 80701884 - Replay scene string address? (sqReplay) (Found by string searching in DME)

                    # define PLAY_INPUT_LOC_START 0x805BC068 //the location of P1's inputs.  Add 4 for the next player during playback
                    # define PLAY_BUTTON_LOC_START 0x805BAD04 //the location of P1's buttons.  Add 0x40 for the next player

                    #dolphin_memory_engine.write_bytes(int("0x806DD5F8", 0), b"38951D68") # addi r4, r21, 0x1D68

                #print(num_replays)
                else:
                    if not is_loaded:
                        print("Replays loaded, starting to record")
                        dolphin_memory_engine.write_bytes(int("0x806dd600", 0), bytes.fromhex('80c60000')) # reset to original behaviour just in case
                        is_loaded = True
                    num_replays = dolphin_memory_engine.read_word(int("0x9017DA00", 0))
                    print(num_replays)

                    for i in range(2):
                        pass
                    #string_start_offset = int.from_bytes(dolphin_memory_engine.read_bytes(int("0x8053F200", 0) + 10, 2), "big", signed = False)
                    #last_string_offset_bytes = dolphin_memory_engine.read_bytes(int("0x8053F200", 0) + 6 + num_entries*16, 2)
                    #last_string_offset = int.from_bytes(last_string_offset_bytes, "big", signed=False)

                    #for i in range(1,num_entries):
                    #    dolphin_memory_engine.write_bytes(int("0x8053F200", 0) + 6 + i*16, last_string_offset_bytes)


                    #dolphin_memory_engine.write_bytes(int("0x8053F200", 0) + string_start_offset + last_string_offset, b"This is a testtt name\00")

                    #prev_bytes = current_bytes

                #last_string_offset = int.from_bytes(last_string_offset, "big", signed = False)
                #print(last_string_offset)
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
