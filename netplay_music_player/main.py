# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import dolphin_memory_engine


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    dolphin_memory_engine.hook()
    while(dolphin_memory_engine.is_hooked()):
        tlst_bytes = dolphin_memory_engine.read_bytes(2152984620, 60) # 8053F02C tlst memory address in int
        print(tlst_bytes)

    dolphin_memory_engine.un_hook()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
