import const
import time
import sqlalchemy
import models
import os.path
from models import Click, Keys, Move, Idle

# Create different data file for different sessions
fname = "log.db"
name = "log"
ext = "db"
extnum = 0;

click_list = []
move_list = []
idle_list = []
key_list = []
not_ide_list = []

def add_suffix(path, fname, name, ext, extnum):
	while os.path.isfile(os.path.join(path, fname)):
		extnum += 1
		fname = name+'_'+str(extnum)+'.'+ext
	return fname

path = os.path.expanduser("~/.HBLog")


try:
    os.makedirs(path)
except OSError:
    pass

fname = add_suffix(path,"log.db", "log", "db", extnum)

session_maker = models.initialize(os.path.join(path, fname))
session = session_maker()

def trycommit():
	for _ in range(1000):
		try:
			session.commit()
			break
		except sqlalchemy.exc.OperationalError:
			time.sleep(1)
		except:
			session.rollback()

def store_click(button, x, y, timestamp, *args):
	""" Stores incoming mouse-clicks """
	session.add(Click(button, x, y, timestamp, args))
	trycommit()

def store_move(time, move, timestamp):
	session.add(Move(time, move, timestamp))
	trycommit()

def store_idle(idle_time, mode, timestamp):
	session.add(Idle(idle_time, mode, timestamp))
	trycommit()

def store_key(key, holding, timestamp, *args):
	session.add(Keys(key, holding, timestamp, args))
	trycommit()

def is_special_key(key):
	return key is "Shift" or key is "Alt" or key is "Ctrl" or key is "Win Key"

def set_wheel_constant(wheelFlag=False, wheelDirection=None, wheelStart=0, wheelTime=0):
	return [wheelFlag, wheelDirection, wheelStart, wheelTime]

def translate_combo_state(combo_state):
	finalstring = ""
	# If combo has Ctrl, it must appear first
	if (combo_state[0] == "1"):
		finalstring += "Ctrl+"
	# If combo has Shift or Alt, it might appear in the second place but only one will appear
	if (combo_state[1:4] == "100" or combo_state[1:4] == "010"):
		if combo_state[1:4] == "100":
			finalstring += "Shift+"
		elif combo_state[1:4] == "010":
			finalstring += "Alt+"
	# For combo start with win
	if (combo_state == "0001"):
		finalstring += "Win+"
	return finalstring

def got_mouse_click(category, x, y, timestamp, *args):
	if category <= 3:
		if category == 1:
			print "mouse left down (%d, %d)" % (x, y)
			button = "left"
		elif category == 2:
			print "mouse middle down (%d, %d)" % (x, y)
			button = "middle"
		elif category == 3:
			print "mouse right down (%d, %d)" % (x, y)
			button = "right"
		click_list.append([button, x, y, timestamp, args[0]])
	else:
		if category == 4:
			print "mouse wheel roll up (%d, %d)" % (x, y)
			button = "wheelUp"
		elif category == 5:
			print "mouse wheel roll down (%d, %d)" % (x, y)
			button = "wheelDown"
		elif category == 6:
			print "mouse drag event captured"
			button = "drag"
		click_list.append([button, x, y, timestamp])
			
def got_mouse_move(length, start_time, end_time):
	duration = end_time - start_time
	print "Length: %d, Duration: %fs" % (length, duration)
	move_list.append([duration,length,start_time])

def got_key(key, pressing, combo_state, transit, timestamp, false_combo, *args):
	modifiers = []
	keyname = key[0]
	if (combo_state != "0000"):
		if (false_combo):
			asciikey = chr(key[1])
			string = unicode(asciikey)
		else:
			asciikey = key[1]
			string = asciikey
	else:
		asciikey = chr(key[1])
		string = unicode(asciikey)
	keyHoldStart = key[2]
	if keyname in ["Lshift", "Rshift"]:
	    modifiers.append('Shift')
	elif keyname in ["Lmenu", "Rmenu"]:
	    modifiers.append('Alt')
	elif keyname in ["Rcontrol", "Lcontrol"]:
	    modifiers.append('Ctrl')
	elif keyname in ["Rwin", "Lwin"]:
	    modifiers.append('Win Key')
	elif keyname in const.SPECIAL_KEYS_NAME:
	    modifiers.append(keyname)
	# No key holding
	if (combo_state == "0000" or not transit):
		if len(modifiers) >= 1:
			finalstring = ' '.join(modifiers)
		elif len(string) >= 1:
			finalstring = string
	elif (false_combo):
		if is_special_key(key_list[-1][0]) and key_list[-1][0] == translate_combo_state(combo_state).split("+")[0]:
			key_list.pop()
		if len(modifiers) >= 1:
			finalstring = ' '.join(modifiers)
		elif len(string) >= 1:
			finalstring = string
	else:
		# Combo key maybe ongoing
		if len(modifiers) >= 1 and (is_special_key(modifiers[0])):
			if (modifiers[0] == "Ctrl" and not combo_state == "1000"):
				return
			elif (modifiers[0] == "Shift" and not combo_state == "0100"):
				return
			elif (modifiers[0] == "Alt" and not combo_state == "0010"):
				return
			elif (modifiers[0] == "Win Key" and not combo_state == "0001"):
				return
			finalstring = modifiers[0]
		else:
			finalstring = translate_combo_state(combo_state)
			if (finalstring == ""):
				# Illegal combination
				return
			else:
				if len(modifiers) >= 1:
					finalstring += ' '.join(modifiers)
				elif type(string) == int and pressing:
					finalstring = chr(string)
				elif len(string) >= 1:
					finalstring += string
	if not pressing:
		print finalstring
		key_list.append([finalstring, False, timestamp, args[0]])
	# Key holding
	else:
		holdtime = timestamp - keyHoldStart + const.PRESSING_COMPENSATION
		print "Hold <%s> key for %fs" % (finalstring, holdtime)
		# Timestamp is the end time
		key_list.append([finalstring, True, (timestamp - holdtime), holdtime])

def got_key_idle(idle_time, timestamp):
	if idle_time > const.IDLE_THRESHOLD:
		# Let's not record implicit idleness
		print "Keyboard idle for %fs" % (idle_time)
		idle_list.append([idle_time,"keyboard",timestamp])

def got_mouse_idle(idle_time, timestamp):
	if idle_time > const.IDLE_THRESHOLD:
		# Let's not record implicit idleness
		print "Mouse idle for %fs" % (idle_time)
		idle_list.append([idle_time,"mouse",timestamp])

# Write stored data to SQL and close the program
def write_data():
	print("Storing datasets...")
	# Combine wheel event
	wheelFlag,wheelDirection,wheelStart,wheelTime = set_wheel_constant()
	for click in click_list:
		if (click[0] == "wheelUp" or click[0] == "wheelDown"):
			if not wheelFlag:
				wheelFlag, wheelDirection, wheelStart, wheelTime = set_wheel_constant(True, click[0], click[3], click[3])
			if wheelFlag:
				# Same wheel direction
				if (click[0] == wheelDirection):
					# In one wheel action within threshold
					if (click[3] - wheelTime < const.WHEEL_THRESHOLD):
						wheelTime = click[3]
					# In different wheel action (exceed threshold)
					else:
						# Store the wheel action
						wheelFlag = False
						store_click(wheelDirection, 0, 0, wheelStart)	
				# Different wheel direction
				else:
					# Start of a new wheel action, and store the previous one
					store_click(wheelDirection, 0, 0, wheelStart)
					wheelFlag, wheelDirection, wheelStart, wheelTime = set_wheel_constant(True, click[0], click[3], click[3])
		else:
			if (wheelFlag):
				store_click(wheelDirection, 0, 0, wheelStart)
				wheelFlag, wheelDirection, wheelStart, wheelTime = set_wheel_constant()
			if (len(click) == 4):
				store_click(click[0], click[1], click[2], click[3])
			else:
				store_click(click[0], click[1], click[2], click[3], click[4])
	for move in move_list:
		store_move(move[0], move[1], move[2])
	for idx,key in enumerate(key_list):
		# Eliminate first special key record leading the combo
		if (idx < len(key_list) - 1 and is_special_key(key_list[idx][0])):
			combo_list = key_list[idx+1][0].split('+')
			if (len(combo_list) > 1 and key_list[idx][0] in key_list[idx+1][0]):
				continue
		# Eliminate two key record leading the hold event
		if ((idx < len(key_list) - 2 and key_list[idx][0] == key_list[idx+2][0] and key_list[idx+2][1])) or ((idx < len(key_list) - 1 and key_list[idx][0] == key_list[idx+1][0] and key_list[idx+1][1])):
			continue
		store_key(key[0], key[1], key[2], key[3])
	for idle in idle_list:
		store_idle(idle[0], idle[1], idle[2])
	print("Dataset recorded")