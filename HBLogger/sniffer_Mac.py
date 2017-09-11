import sys
import time
import const
from collections import deque
from pynput import keyboard
from pynput import mouse

class Sniffer:
    """Winning!"""
    def __init__(self):
        self.encoding = sys.stdin.encoding
        self.key_down_hook = lambda x: True
        self.mouse_button_hook = lambda x: True
        self.mouse_move_hook = lambda x: True
        self.key_idle_hook = lambda x: True
        self.mouse_idle_hook = lambda x: True
        self.ditrigraph_hook = lambda x: True

        #mouse/keyboard variables initialization
        self.keyboard_last_idle_time = time.time()
        self.keyboard_last_key = ["",0,time.time()] # [KEY_STATE, ASCII_CODE, TIME]
        self.mouse_last_idle_time = time.time()
        self.mouse_path_start_time = time.time()
        self.mouse_path_end_time = time.time()
        self.pressing = False
        self.mouse_path = [] # A list of coordinates of mouse for one movement
        self.digraph_found = False # Flag for finding the digraph
        self.trigraph_found = False # Flag for finding the trigraph
        self.keyseq = deque(["", "", ""]) # Record the last key sequence

    def UpdateLastKey(self, keyVal):
        self.keyboard_last_key[0] = keyVal
        self.keyboard_last_key[1] = event.Ascii
        self.keyboard_last_key[2] = time.time()

    def on_move(self, x, y):
        print('Pointer moved to {0}'.format(
            (x, y)))

    def on_click(self, x, y, button, pressed):
        print('{0} at {1}'.format(
            'Pressed' if pressed else 'Released',
            (x, y)))

    def on_scroll(self, x, y, dx, dy):
        print('Scrolled {0} at {1}'.format(
            'down' if dy < 0 else 'up',
            (x, y)))

    def on_release(self, key):
      print('{0} release'.format(
        key))

    def on_keypress(self, key):
        try:
            print('alphanumeric key {0} pressed'.format(
                key.char))

        except AttributeError:
            print('special key {0} pressed'.format(
                key))
    
    def run(self):

        # Collect events until released
        self.listener = mouse.Listener(
                on_move=self.on_move,
                on_click=self.on_click,
                on_scroll=self.on_scroll)
        self.listener1 = keyboard.Listener(
                on_press=self.on_keypress,
                on_release=self.on_release)
        self.listener.start()
        self.listener1.start()
        self.listener.wait()
        self.listener1.wait()
        while True:
            self.listener.join(100)
            self.listener1.join(100)
        
    def cancel(self):
        self.listener.stop()
        self.listener1.stop()
        del self.listener
        del self.listener1