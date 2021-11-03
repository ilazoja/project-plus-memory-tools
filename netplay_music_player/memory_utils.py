
import os
import time
import dolphin_memory_engine
from utils import get_config

# Referenced CSE.asm [Dantarion, PyotrLuzhin, DukeItOut] in Project+ to replicate pinch functionality, also used All_Data_DME_file.dmw [Eon] for DME for some memory addresses

def isSuperSuddenDeath():
    #  lis r12, 0x9018				# \
    # lbz r0, -0xC88(r12)			# | Super Sudden Death automatically makes the pinch song play!
    # cmpwi r0, 1					# |
    # beq startWithPinch			# /

    return dolphin_memory_engine.read_byte(int("0x9017f378", 0)) == 1 # hex(int("0x90180000", 0) - int("0xC88", 0))

def isStamina():
    # checkStamina:
    # 	lis r12, 0x9018				# \
    # 	lbz r12, -0xC88(r12)		# | Stamina mode has another prerequisite: the player being under 100HP!
    # 	cmpwi r12, 2				# |
    # 	bne+ not_stamina			# /

    return dolphin_memory_engine.read_byte(int("0x9017f378", 0)) == 2 # hex(int("0x90180000", 0) - int("0xC88", 0))

def isWildBrawl():
    #   lbz r0, -0xC82(r12)    		# \
    #   cmpwi r0, 1        			# | The above also applies to Wild Brawl
    #   beq startWithPinch        	# /

    return dolphin_memory_engine.read_byte(int("0x9017f37e", 0)) == 1  # hex(int("0x90180000", 0) - int("0xC82", 0))

def isBombRain():
    #   lbz r0, -0xC81(r12)			# \
    #   cmpwi r0, 1					# | As well as Bomb Rain Mode
    #   bne doNotForce				# /

    return dolphin_memory_engine.read_byte(int("0x9017f37f", 0)) == 1  # hex(int("0x90180000", 0) - int("0xC81", 0))

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

def isPinchStock(stock_count, last_stock_loss_frame, frames_into_current_game):

    min_frames_since_last_stock = 60

    if sum(s > 0 for s in stock_count) == 2:

        is_stamina = isStamina()

        # stamina:
        # 	lis r3, 0x805A				# \
        # 	lwz r3, 0x60(r3)			# |
        # 	lwz r3, 0x4(r3)				# |
        # 	lwz r3, 0x68(r3)			# | Get the stamina health for this port.
        # 	mulli r4, r6, 4				# |
        # 	addi r4, r4, 0xD0			# |
        # 	lwzx r3, r3, r4				# |
        # 	cmpwi r3, 100				# |
        # 	bge+ notBelow100HP			# /
        # not_stamina:
        # 	addi r7, r7, 1				# Increment count of amount of players at 1 stock, currently.
        # notOneStock:
        # notBelow100HP:
        # 	addi r6, r6, 1				# \
        # 	cmpwi r6, 4					# | Do the loop for all four ports
        #   blt stockCheckLoop			# /
        for player_num, (player_stocks, player_last_stock_loss_frame) in enumerate(zip(stock_count, last_stock_loss_frame)):
            if player_stocks == 1:

                if is_stamina: # need buffer period otherwise will use percent from previous stock
                    if frames_into_current_game - player_last_stock_loss_frame >= min_frames_since_last_stock:
                        stamina_address = dolphin_memory_engine.follow_pointers(int("0x805A0060", 0),
                                                                                         [int("0x4", 0), int("0x68", 0)])
                        stamina_address = dolphin_memory_engine.read_word(stamina_address)
                        stamina = dolphin_memory_engine.read_word(4 * player_num + int("0xD0", 0) + stamina_address)
                        if stamina <= 100:
                            return True
                else:
                    return True

    #return (sum(s > 0 for s in stock_count) == 2) and (sum(s == 1 for s in stock_count) > 0) # if 2 players left and at least 1 player has only 1 stock remaining

    return False

def get_stock_count():
    stock_count = [-2, -2, -2, -2]

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
        stock_count[0] = dolphin_memory_engine.read_word(p1_stock_address)
    except RuntimeError:
        pass

    try:
        p2_stock_address = dolphin_memory_engine.follow_pointers(int("0x8062355C", 0), [int("0x44", 0)])
        stock_count[1] = dolphin_memory_engine.read_word(p2_stock_address)
    except RuntimeError:
        pass

    try:
        p3_stock_address = dolphin_memory_engine.follow_pointers(int("0x806237A0", 0), [int("0x44", 0)])
        stock_count[2] = dolphin_memory_engine.read_word(p3_stock_address)
    except RuntimeError:
        pass

    try:
        p4_stock_address = dolphin_memory_engine.follow_pointers(int("0x806239E4", 0), [int("0x44", 0)])
        stock_count[3] = dolphin_memory_engine.read_word(p4_stock_address)
    except RuntimeError:
        pass

    return stock_count

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
        return frames_remaining <= song_switch # if time is enabled and frames remaining is less than song_switch time
        ## Should use frame remaining to end song at TIME
    except RuntimeError:
        pass

    return False

def get_frames_remaining():
    try:
        frames_remaining_address = dolphin_memory_engine.follow_pointers(int("0x805A0060", 0),
                                                                         [int("0x4", 0), int("0x54", 0),
                                                                          int("0xE0", 0)])
        frames_remaining = dolphin_memory_engine.read_word(frames_remaining_address)
        return frames_remaining
    except RuntimeError:
        return 0

def get_frames_into_current_game():
    return dolphin_memory_engine.read_word(int("0x8062B420", 0))

def get_stage_id():
    return dolphin_memory_engine.read_word(int("0x8062B3B4", 0))

def isEndOfGame():
    return dolphin_memory_engine.read_byte(int("0x804953B0", 0)) # Note: also triggers for Zelda/Sheik transformation

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


