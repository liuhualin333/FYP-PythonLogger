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

class SnifferThread(threading.Thread):
    def __init__(self, hook):
        threading.Thread.__init__(self)
        self.daemon = True # Daemon Thread left when main thread left
        self.encoding = sys.stdin.encoding
        self.ditrigraph_hook = lambda x: True
        self.key_down_hook = lambda x: True
        self.key_idle_hook = lambda x: True
        self.mouse_button_hook = lambda x: True
        self.mouse_idle_hook = lambda x: True
        self.mouse_move_hook = lambda x: True

        self.hm = hook
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

    def run(self):
        self.hm.KeyAll = self.OnKeyboardEvent
        self.hm.MouseAllButtonsDown = self.OnMouseClick
        self.hm.MouseMove = self.OnMouseMove
        self.hm.MouseWheel = self.OnMouseWheel
        self.hm.HookKeyboard()
        self.hm.HookMouse()
        pythoncom.PumpMessages()

    def UpdateLastKey(self, event, keyVal):
        self.keyboard_last_key[0] = keyVal
        self.keyboard_last_key[1] = event.Ascii
        self.keyboard_last_key[2] = time.time()

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
        if (not self.CheckProcess(event)):
            self.keyboard_last_idle_time = time.time()
            return True
        keyVal = self.IdentifyNonPrintChar(event)
        if event.MessageName == 'key down' or event.MessageName == 'key sys down':
            print 'Ascii:', event.Ascii, chr(event.Ascii)
            # For Keyboard idleness
            idle_time = time.time() - self.keyboard_last_idle_time
            self.key_idle_hook(idle_time)
            self.keyboard_last_idle_time = time.time()
            # For Key pressing behavior
            if keyVal == self.keyboard_last_key[0] and event.Ascii == self.keyboard_last_key[1] and (0 < idle_time < 0.1):
                # HOLD THE KEY
                self.pressing = True
            else:
                # Not affected by the previous key sequence when di/trigraph is found
                if self.trigraph_found == True:
                    self.keyseq = deque(["", "", ""])
                    self.trigraph_found = False
                elif self.digraph_found == True:
                    self.keyseq = deque(["", "", self.keyseq[2]])
                    self.digraph_found = False
                # Not counted when other special char is entered
                if keyVal not in const.SPECIAL_KEYS_NAME:
                    self.keyseq.popleft()
                    self.keyseq.append(keyVal)
                else:
                    self.keyseq = deque(["", "", ""])
                potential_seq = self.keyseq[0] + self.keyseq[1] + self.keyseq[2]
                potential_di_1 = self.keyseq[0] + self.keyseq[1]
                print potential_seq
                print potential_di_1  
                if potential_seq.lower() in const.TRIGRAPH_LIST:
                    self.ditrigraph_hook(potential_seq, "trigraph")
                    self.trigraph_found = True
                elif potential_di_1.lower() in const.DIGRAPH_LIST:
                    self.ditrigraph_hook(potential_di_1, "digraph")
                    self.digraph_found = True
                self.UpdateLastKey(event, keyVal)
                self.pressing = False
            # Record every key down
            if self.pressing == False:
                self.key_down_hook(self.keyboard_last_key, self.pressing)
        if event.MessageName == 'key up':
            if keyVal == self.keyboard_last_key[0] and event.Ascii == self.keyboard_last_key[1] and self.pressing:
                self.key_down_hook(self.keyboard_last_key, self.pressing)
                self.keyboard_last_key[2] = time.time()
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
        if (not self.CheckProcess(event)):
            self.mouse_last_idle_time = time.time()
            return True
        idle_time = time.time() - self.mouse_last_idle_time
        self.mouse_idle_hook(idle_time)
        self.mouse_last_idle_time = time.time()
        loc = event.Position
        if event.MessageName == "mouse right down":
            self.mouse_button_hook(3, loc[0], loc[1])
        if event.MessageName == "mouse left down":
            self.mouse_button_hook(1, loc[0], loc[1])
        if event.MessageName == "mouse middle down":
            self.mouse_button_hook(2, loc[0], loc[1])
        return True

    def OnMouseMove(self, event):
        # print 'Position:',event.Position
        # print '---'
        if (not self.CheckProcess(event)):
            self.mouse_last_idle_time = time.time()
            return True
        idle_time = time.time() - self.mouse_last_idle_time
        self.mouse_idle_hook(idle_time)
        self.mouse_last_idle_time = time.time()
        # print idle_time
        if idle_time < const.MOUSE_IDLE_THRESHOLD:
            # Mouse is moving
            if len(self.mouse_path) == 0:
                self.mouse_path_start_time = time.time()
            self.mouse_path.append(event.Position)
        elif len(self.mouse_path) != 0:
            self.mouse_path_end_time = time.time() - idle_time
            self.mouse_move_hook(self.mouse_path, self.mouse_path_start_time, self.mouse_path_end_time)
            self.mouse_path = []
        return True

    def OnMouseWheel(self, event):
        if (not self.CheckProcess(event)):
            self.mouse_last_idle_time = time.time()
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
        self.ditrigraph_hook = lambda x: True

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
            self.thread.ditrigraph_hook = self.ditrigraph_hook
            self.thread.start()
            while True:
                self.thread.join(100)
        except:
            self.cancel()

    def cancel(self):
        potential_di_2 = self.thread.keyseq[1] + self.thread.keyseq[2]
        if potential_di_2.lower() in const.DIGRAPH_LIST:
            self.thread.ditrigraph_hook(potential_di_2, "digraph")
            self.thread.digraph_found = True
        ctypes.windll.user32.PostQuitMessage(0)
        self.hm.UnhookKeyboard()
        self.hm.UnhookMouse()
        del self.thread
        del self.hm