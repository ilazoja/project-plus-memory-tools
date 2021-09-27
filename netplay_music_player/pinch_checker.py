
import os
import time
import dolphin_memory_engine
from utils import get_config

def isSuperSuddenDeath():
    #  lis r12, 0x9018				# \
    # lbz r0, -0xC88(r12)			# | Super Sudden Death automatically makes the pinch song play!
    # cmpwi r0, 1					# |
    # beq startWithPinch			# /

    return dolphin_memory_engine.read_byte(int("0x9017f378", 0)) # hex(int("0x90180000", 0) - int("0xC88", 0))

def isWildBrawl():
    #   lbz r0, -0xC82(r12)    		# \
    #   cmpwi r0, 1        			# | The above also applies to Wild Brawl
    #   beq startWithPinch        	# /

    return dolphin_memory_engine.read_byte(int("0x9017f37e", 0))  # hex(int("0x90180000", 0) - int("0xC82", 0))

def isBombRain():
    #   lbz r0, -0xC81(r12)			# \
    #   cmpwi r0, 1					# | As well as Bomb Rain Mode
    #   bne doNotForce				# /

    return dolphin_memory_engine.read_byte(int("0x9017f37f", 0))  # hex(int("0x90180000", 0) - int("0xC81", 0))

def isSuddenDeath():
    #   lis r12, 0x805A				# \
    # 	lwz r12, 0x60(r12)			# |
    # 	lwz r12, 0x4(r12)			# |
    # 	lwz r12, 0x4C(r12)			# |
    # 	cmpwi r12, 0				# |
    # 	beq doNotForce				# |
    # 	lwz r12, 0x40(r12)			# |\
    # 	cmpwi r12, 0				# ||Check if in Sudden Death
    # 	bne startWithPinch			# //

    # check if in sudden death different in other hook for some reason

    try:
        is_sudden_death_address = dolphin_memory_engine.follow_pointers(int("0x805A0060", 0), [int("0x4", 0), int("0x4C", 0), int("0x40", 0)])
    except RuntimeError:
        return 0

    return dolphin_memory_engine.read_byte(is_sudden_death_address)

def isPinchStock():
    stock_count = [-1, -1, -1, -1]

    # {
    #     "watchList": [
    #         {
    #             "address": "80623318",
    #             "baseIndex": 0,
    #             "label": "P1",
    #             "pointerOffsets": [
    #                 "44"
    #             ],
    #             "typeIndex": 2,
    #             "unsigned": false
    #         }
    #     ]
    # }

    try:
        p1_stock_address = dolphin_memory_engine.follow_pointers(int("0x80623318", 0), [int("0x44", 0)])
        stock_count[0] = int.from_bytes(dolphin_memory_engine.read_bytes(p1_stock_address, 4), "big", signed=False)
    except RuntimeError:
        pass

    try:
        p2_stock_address = dolphin_memory_engine.follow_pointers(int("0x8062355C", 0), [int("0x44", 0)])
        stock_count[1] = int.from_bytes(dolphin_memory_engine.read_bytes(p2_stock_address, 4), "big", signed=False)
    except RuntimeError:
        pass

    try:
        p3_stock_address = dolphin_memory_engine.follow_pointers(int("0x806237A0", 0), [int("0x44", 0)])
        stock_count[2] = int.from_bytes(dolphin_memory_engine.read_bytes(p3_stock_address, 4), "big", signed=False)
    except RuntimeError:
        pass

    try:
        p4_stock_address = dolphin_memory_engine.follow_pointers(int("0x806239E4", 0), [int("0x44", 0)])
        stock_count[3] = int.from_bytes(dolphin_memory_engine.read_bytes(p4_stock_address, 4), "big", signed=False)
    except RuntimeError:
        pass

    return (sum(s > 0 for s in stock_count) == 2) and (sum(s == 1 for s in stock_count) > 0) # if 2 players left and at least 1 player has only 1 stock remaining
    ## can maybe use to detect end of GAME

def isPinchTime(song_switch):

    # at 80577a5c in P+ 2.29 (in checkTime in CSE.asm which initial hook is at 806D2164)
    # checkTime:
        # 	lis r12, 0x805A				# \
        # 	lwz r12, 0x60(r12)			# |
        # 	lwz r12, 0x4(r12)			# | Get decrementing stage timer
        # 	lwz r12, 0x54(r12)			# |
        # 	lwz r12, 0xE0(r12)			# /
        # 	lis r4, 0x8054				# \ Get the timer for changing that the song uses
        # 	lhz r4, -0x1054(r4)			# /
        # 	cmpwi r12, 0				# \ Ignore time if disabled.
        # 	beq skipToggle				# /
        # 	cmpw r12, r4				# \ Check if the timer is less than the change position
        # 	bge+ skipToggle				# / if not, don't activate.

    # {
    #     "watchList": [
    #         {
    #             "address": "805A0060",
    #             "baseIndex": 0,
    #             "label": "Frames Remaining",
    #             "pointerOffsets": [
    #                 "4",
    #                 "54",
    #                 "E0"
    #             ],
    #             "typeIndex": 2,
    #             "unsigned": false
    #         }
    #     ]
    # }

    #song_switch = 7.5*60*60
    try:
        frames_remaining_address = dolphin_memory_engine.follow_pointers(int("0x805A0060", 0),
                                                                         [int("0x4", 0), int("0x54", 0),
                                                                          int("0xE0", 0)])
        frames_remaining = dolphin_memory_engine.read_word(frames_remaining_address)
        return frames_remaining != 0 and frames_remaining <= song_switch # if time is enabled and frames remaining is less than song_switch time
        ## Should use frame remaining to end song at TIME
    except RuntimeError:
        pass

    return False

if __name__ == '__main__':

    config = get_config()

    print("Run P+ in Dolphin to start")
    done = False

    while not done:
        if not dolphin_memory_engine.is_hooked():
            dolphin_memory_engine.hook()
            if dolphin_memory_engine.is_hooked():
                print("Hooked to Dolphin")
        else:
            try:
                pass

                #print(isSuperSuddenDeath())
                #print(isWildBrawl())
                #print(isBombRain())
                #print(isSuddenDeath())
                #print(isPinchStock(7.5*60*60))
                #print(isPinchTime())

                #tlst_bytes = dolphin_memory_engine.read_bytes(int("0x8053F200", 0), 3920)


                ## Only should PINCH after GO!
                # Use frames into current game (should be > 0)









                #print(current_bytes)

                #print(curren)
                #if current_bytes[0:4] == b"TLST" and current_bytes != prev_bytes:

                #last_string_offset = int.from_bytes(last_string_offset, "big", signed = False)
                #print(last_string_offset)
            except RuntimeError:
                dolphin_memory_engine.un_hook()
                print("Unhooked to Dolphin")


        #time.sleep(0.1)

### Notes





## Use DME file

## 80577990 checkStockMatch


## Selecting Wild/Super Sudden Death/Bomb Rain should pinch even the menu

