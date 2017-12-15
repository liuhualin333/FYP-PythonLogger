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
        self.keyboard_last_key = ["",0,self.keyboard_last_idle_time,"0000"] # [KEY_STATE, ASCII_CODE, TIME, HOLD_STATE]
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

    def CheckSpecialKeyState(self):
        ctrl_pressed = "1" if (pyHook.GetKeyState(pyHook.HookConstants.VKeyToID('VK_CONTROL'))) else "0"
        shift_pressed = "1" if (pyHook.GetKeyState(pyHook.HookConstants.VKeyToID('VK_SHIFT'))) else "0"
        alt_pressed = "1" if (pyHook.GetKeyState(pyHook.HookConstants.VKeyToID('VK_MENU'))) else "0"
        win_pressed = "1" if (pyHook.GetKeyState(pyHook.HookConstants.VKeyToID('VK_LWIN'))) else "0"

        return ctrl_pressed + shift_pressed + alt_pressed + win_pressed

    def CheckComboStateTransit(self, last_state, state):
        if (last_state == "0000" or state == "0000" or last_state == state):
            return True
        elif (last_state == "1000"):
            return (state == "1000" or state == "1100" or state == "1010")
        elif (last_state == "0100"):
            return (state == "0100")
        elif (last_state == "0010"):
            return (state == "0010")
        elif (last_state == "0001"):
            return (state == "0001")

    def ComboStateToKey(self, state):
        keyList = []
        if(state[0] == "1"):
            keyList.append("Ctrl")
        if(state[1] == "1"):
            keyList.append("Shift")
        if(state[2] == "1"):
            keyList.append("Alt")
        if(state[3] == "1"):
            keyList.append("Win Key")
        return keyList


    def UpdateLastKey(self, event, keyVal, current_time, combo_state):
        if (combo_state == "0000"):
            self.keyboard_last_key = [keyVal, event.Ascii, current_time, combo_state]
        else:    
            self.keyboard_last_key = [keyVal, pyHook.HookConstants.IDToName(event.KeyID), current_time, combo_state]

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
        # Check whether it is a combo
        combo_state = self.CheckSpecialKeyState()
        if event.MessageName == 'key down' or event.MessageName == 'key sys down':
            print combo_state
            print 'Ascii:', event.Ascii, chr(event.Ascii)
            # If Transition is wrong
            if (not self.CheckComboStateTransit(self.keyboard_last_key[3], combo_state)):
                print "Transition is wrong"
                self.UpdateLastKey(event, keyVal, current_time, "0000")
                self.key_down_hook(self.keyboard_last_key, self.pressing, "0000")
                self.pressing = False
            # For Key pressing behavior
            if keyVal == self.keyboard_last_key[0] and ((pyHook.HookConstants.IDToName(event.KeyID) == self.keyboard_last_key[1] and combo_state != "0000") or (event.Ascii == self.keyboard_last_key[1] and combo_state == "0000")) and (0 < idle_time < 0.06):
                # HOLD THE KEY
                self.pressing = True
            else:
                self.UpdateLastKey(event, keyVal, current_time, combo_state)
                self.pressing = False
            # Record every key down
            if not self.pressing:
                self.key_down_hook(self.keyboard_last_key, self.pressing, combo_state)
        elif event.MessageName == 'key up':
            if ((keyVal == self.keyboard_last_key[0]) and ((pyHook.HookConstants.IDToName(event.KeyID) == self.keyboard_last_key[1] and combo_state != "0000") or (event.Ascii == self.keyboard_last_key[1] and combo_state == "0000"))) or keyVal in self.ComboStateToKey(self.keyboard_last_key[3]) and self.pressing:
                self.key_down_hook(self.keyboard_last_key, self.pressing, combo_state)
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
            self.drag_flag = False
            self.drag_time = current_time
            self.drag_coord = "0_0"
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