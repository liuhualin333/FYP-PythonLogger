import sys
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

    def on_keypress(self, key):
        try:
            print('alphanumeric key {0} pressed'.format(
                key.char))
            if key == keyboard.Key.esc:
                return False

        except AttributeError:
            print('special key {0} pressed'.format(
                key))
    
    def run(self):

        # Collect events until released
        with mouse.Listener(
                    on_move=self.on_move,
                    on_click=self.on_click,
                    on_scroll=self.on_scroll) as listener, \
                keyboard.Listener(
                    on_press=self.on_keypress) as listener1:
            try:
                while True:
                    listener.join(100)
                    listener1.join(100)
            except:
                listener.stop()
                listener1.stop()
                del listener
                del listener1
    def cancel(self):
        pass