import pyHook
import pythoncom
import sys
import threading
import ctypes
import time
import const
from collections import deque
import win32gui
import win32process
import psutil
import Queue

class SnifferThread(threading.Thread):
    def __init__(self, hook):
        threading.Thread.__init__(self)
        self.daemon = True # Daemon Thread left when main thread left
        self.encoding = sys.stdin.encoding
        self.key_down_hook = lambda x: True
        self.key_idle_hook = lambda x: True
        self.mouse_button_hook = lambda x: True
        self.mouse_idle_hook = lambda x: True
        self.mouse_move_hook = lambda x: True

        self.hm = hook
        self.keyboard_last_idle_time = time.time()
        self.keyboard_last_key = ["",0,self.keyboard_last_idle_time] # [KEY_STATE, ASCII_CODE, TIME]
        self.mouse_last_idle_time = self.keyboard_last_idle_time
        self.mouse_path_start_time = self.keyboard_last_idle_time
        self.mouse_path_end_time = self.keyboard_last_idle_time
        self.pressing = False
        self.mouse_path = [] # A list of coordinates of mouse for one movement
        self.keyseq = deque(["", "", ""]) # Record the last key sequence
        self.drag_flag = False # Drag flag
        self.drag_time = self.keyboard_last_idle_time
        self.drag_coord = "0_0"

    def run(self):
        self.hm.KeyAll = self.OnKeyboardEvent
        self.hm.MouseAllButtons = self.OnMouseClick
        self.hm.MouseMove = self.OnMouseMove
        self.hm.MouseWheel = self.OnMouseWheel
        self.hm.HookKeyboard()
        self.hm.HookMouse()
        pythoncom.PumpMessages()

    def UpdateLastKey(self, event, keyVal, current_time):
        self.keyboard_last_key[0] = keyVal
        self.keyboard_last_key[1] = event.Ascii
        self.keyboard_last_key[2] = current_time

    # Record the event only on specific program
    def CheckProcess(self, event):
        fgWindow = win32gui.GetForegroundWindow()
        threadID, ProcessID = win32process.GetWindowThreadProcessId(fgWindow)
        try:
            procname = psutil.Process(ProcessID)
        except:
            return False
        if procname.name() == "pythonw.exe":
            return True
        else:
            return False

    # Handle the update of idle variable and run idle hook
    def HandleIdleEvent(self, event, mode):
        # Base time stamp for this particular event
        current_time = time.time()
        idle_time = 0
        if (mode == "keyboard"):
            # For the keyboard idle time to be updated outside the IDE
            if (not self.CheckProcess(event)):
                self.keyboard_last_idle_time = current_time
                return "", "", False 

            idle_time = current_time - self.keyboard_last_idle_time
            self.key_idle_hook(idle_time)
            self.keyboard_last_idle_time = current_time

        elif (mode == "mouse"):
            # For the mouse idle time to be updated outside the IDE
            if (not self.CheckProcess(event)):
                self.mouse_last_idle_time = current_time
                return "","",False

            idle_time = current_time - self.mouse_last_idle_time
            self.mouse_idle_hook(idle_time)
            self.mouse_last_idle_time = current_time

        return current_time, idle_time, True

    def IdentifyNonPrintChar(self, event):
        keyname = event.Key
        keyAscii = event.Ascii
        finalkey = event.Key
        if keyname in ["Lshift", "Rshift"]:
            finalkey = 'Shift'
        elif keyname in ["Lmenu", "Rmenu"]:
            finalkey = 'Alt'
        elif keyname in ["Rcontrol", "Lcontrol"]:
            finalkey = 'Ctrl'
        elif keyname in ["Rwin", "Lwin"]:
            finalkey = 'Win Key'
        elif keyname in const.SPECIAL_KEYS_NAME:
            finalkey = keyname
        else:
            finalkey = keyname
        return finalkey

    def OnKeyboardEvent(self, event):
        #For keyboard hold and keyboard idleness and record keydown
        # print 'MessageName:',event.MessageName
        # print 'Message:',event.Message
        # print 'Ascii:', event.Ascii, chr(event.Ascii)
        # print 'Key:', event.Key
        # print 'KeyID:', event.KeyID
        # print '---'

        current_time, idle_time, is_IDE = self.HandleIdleEvent(event, "keyboard")

        if (is_IDE == False):
            return True
        keyVal = self.IdentifyNonPrintChar(event)
        if event.MessageName == 'key down' or event.MessageName == 'key sys down':
            print 'Ascii:', event.Ascii, chr(event.Ascii)
            
            # For Key pressing behavior
            if keyVal == self.keyboard_last_key[0] and event.Ascii == self.keyboard_last_key[1] and (0 < idle_time < 0.06):
                # HOLD THE KEY
                self.pressing = True
            else:
                # Not counted when other special char is entered
                if keyVal not in const.SPECIAL_KEYS_NAME:
                    self.keyseq.popleft()
                    self.keyseq.append(keyVal)
                else:
                    self.keyseq = deque(["", "", ""])
                potential_seq = self.keyseq[0] + self.keyseq[1] + self.keyseq[2]
                print potential_seq 
                self.UpdateLastKey(event, keyVal, current_time)
                self.pressing = False
            # Record every key down
            if self.pressing == False:
                self.key_down_hook(self.keyboard_last_key, self.pressing)
        elif event.MessageName == 'key up':
            if keyVal == self.keyboard_last_key[0] and event.Ascii == self.keyboard_last_key[1] and self.pressing:
                self.key_down_hook(self.keyboard_last_key, self.pressing)
                self.keyboard_last_key[2] = current_time
                self.pressing = False
        return True

    def OnMouseClick(self, event):
        # print 'MessageName:',event.MessageName
        # print 'Message:',event.Message
        # print 'Time:',event.Time
        # print 'Position:',event.Position
        # print 'Wheel:',event.Wheel
        # print 'Injected:',event.Injected
        # print '---'

        current_time, _, is_IDE = self.HandleIdleEvent(event, "mouse")

        if (is_IDE == False):
            return True
        loc = event.Position
        if event.MessageName == "mouse right down":
            self.mouse_button_hook(3, loc[0], loc[1])
        elif event.MessageName == "mouse left down":
            self.drag_flag = True
            self.drag_time = current_time
            self.drag_coord = str(loc[0])+"_"+str(loc[1])
            self.mouse_button_hook(1, loc[0], loc[1])
        elif event.MessageName == "mouse left up":
            # Drag event recorder
            if (self.drag_flag and (current_time - self.drag_time) > const.DRAG_THRESHOLD and not self.drag_coord == str(loc[0])+"_"+str(loc[1])):
                self.mouse_button_hook(6,0,0)
            self.drag_flag = False
            self.drag_time = current_time
            self.drag_coord = "0_0"
        elif event.MessageName == "mouse middle down":
            self.mouse_button_hook(2, loc[0], loc[1])
        return True

    def OnMouseMove(self, event):
        # print 'Position:',event.Position
        # print '---'

        current_time, idle_time, is_IDE = self.HandleIdleEvent(event, "mouse")

        if (is_IDE == False):
            return True
        # print idle_time
        if idle_time < const.MOUSE_IDLE_THRESHOLD:
            # Mouse is moving
            if len(self.mouse_path) == 0:
                self.mouse_path_start_time = current_time
            self.mouse_path.append(event.Position)
        elif len(self.mouse_path) != 0:
            self.mouse_path_end_time = current_time - idle_time
            self.mouse_move_hook(self.mouse_path, self.mouse_path_start_time, self.mouse_path_end_time)
            self.mouse_path = []
        return True

    def OnMouseWheel(self, event):
        current_time, _, is_IDE = self.HandleIdleEvent(event, "mouse")

        if (is_IDE == False):
            return True
        loc = event.Position
        if event.MessageName == "mouse wheel":
            if event.Wheel == -1:
                self.mouse_button_hook(5, loc[0], loc[1])
            elif event.Wheel == 1:
                self.mouse_button_hook(4, loc[0], loc[1])
        return True

class Sniffer:
    """Winning!"""
    def __init__(self):
        self.encoding = sys.stdin.encoding
        self.key_down_hook = lambda x: True
        self.mouse_button_hook = lambda x: True
        self.mouse_move_hook = lambda x: True
        self.key_idle_hook = lambda x: True
        self.mouse_idle_hook = lambda x: True
        self.write_data_hook = lambda x: True

    def run(self):
        try:
            self.hm = pyHook.HookManager()
            self.thread = SnifferThread(self.hm)
            # pythoncom.PumpMessages needs to be in the same thread as the events
            self.thread.mouse_button_hook = self.mouse_button_hook
            self.thread.mouse_move_hook = self.mouse_move_hook
            self.thread.key_down_hook = self.key_down_hook
            self.thread.key_idle_hook = self.key_idle_hook
            self.thread.mouse_idle_hook = self.mouse_idle_hook
            self.thread.start()
            while True:
                self.thread.join(100)
        except:
            self.cancel()

    def cancel(self):
        self.write_data_hook()
        ctypes.windll.user32.PostQuitMessage(0)
        self.hm.UnhookKeyboard()
        self.hm.UnhookMouse()
        del self.thread
        del self.hm