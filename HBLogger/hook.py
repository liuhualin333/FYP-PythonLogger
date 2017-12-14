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

def store_click(button, x, y, timestamp):
	""" Stores incoming mouse-clicks """
	session.add(Click(button, x, y, timestamp))
	trycommit()

def store_move(time, move, timestamp):
	session.add(Move(time, move, timestamp))
	trycommit()

def store_idle(idle_time, mode, timestamp):
	session.add(Idle(idle_time, mode, timestamp))
	trycommit()

def store_key(key, asciiCode, holding, timestamp, *args):
	session.add(Keys(key, asciiCode, holding, timestamp, args))
	trycommit()

def got_mouse_click(category, x, y):
	if category == 1:
		print "mouse left down (%d, %d)" % (x, y)
		button = "left"
	elif category == 2:
		print "mouse middle down (%d, %d)" % (x, y)
		button = "middle"
	elif category == 3:
		print "mouse right down (%d, %d)" % (x, y)
		button = "right"
	elif category == 4:
		print "mouse wheel roll up (%d, %d)" % (x, y)
		button = "wheelUp"
	elif category == 5:
		print "mouse wheel roll down (%d, %d)" % (x, y)
		button = "wheelDown"
	elif category == 6:
		print "mouse drag event captured"
		button = "drag"
	click_list.append([button,x,y,time.time()])
	#store_click(button, x, y)

def got_mouse_move(mouse_path, start_time, end_time):
	length = len(mouse_path)
	duration = end_time - start_time
	print "Length: %d, Duration: %fs" % (length, duration)
	move_list.append([duration,length,time.time()])
	#store_move((end_time - start_time), len(mouse_path))

def got_key(key, pressing):
	modifiers = []
	keyname = key[0]
	asciikey = chr(key[1])
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
	string = unicode(asciikey)
	# No key holding
	if len(modifiers) >= 1:
		finalstring = ' '.join(modifiers)
	elif len(string) >= 1:
		finalstring = string

	if pressing == False:
		print finalstring
		key_list.append([finalstring, key[1], False,time.time()])
		#store_key(finalstring, key[1], False)
	# Key holding
	else:
		holdtime = time.time() - keyHoldStart + const.PRESSING_COMPENSATION
		print "Hold <%s> key for %fs" % (finalstring, holdtime)
		key_list.append([finalstring, key[1], True, time.time(), holdtime])
		#store_key(finalstring, key[1], True, holdtime)

def got_key_idle(idle_time):
	if idle_time > const.IDLE_THRESHOLD:
		# Let's not record implicit idleness
		print "Keyboard idle for %fs" % (idle_time)
		idle_list.append([idle_time,"keyboard",time.time()])
		#store_idle(idle_time, "keyboard")

def got_mouse_idle(idle_time):
	if idle_time > const.IDLE_THRESHOLD:
		# Let's not record implicit idleness
		print "Mouse idle for %fs" % (idle_time)
		idle_list.append([idle_time,"mouse",time.time()])
		#store_idle(idle_time, "mouse")

# Write stored data to SQL and close the program
def write_data():
	print("Please do not close the command line interface because we are storing datasets...")
	wheelFlag = False
	wheelDirection = None
	wheelStart = 0
	wheelTime = 0
	for click in click_list:
		if ((click[0] == "wheelUp" or click[0] == "wheelDown") and not wheelFlag):
			wheelFlag = True
			wheelDirection = click[0]
			wheelStart = click[3]
			wheelTime = click[3]
		elif (wheelFlag):
			# Same wheel direction
			if (click[0] == wheelDirection):
				# In one wheel action
				if (click[3] - wheelTime < const.WHEEL_THRESHOLD):
					wheelTime = click[3]
				# In different wheel action
				else:
					# Store the wheel action
					wheelFlag = False
					store_click(wheelDirection, 0, 0, wheelStart)	
			# Different wheel direction
			else:
				# Start of a new wheel action, and store the previous one
				wheelFlag = True
				wheelDirection = click[0]
				wheelStart = click[3]
				wheelTime = click[3]
				store_click(wheelDirection, 0, 0, wheelStart)
		else:
			store_click(click[0], click[1], click[2], click[3])
	for move in move_list:
		store_move(move[0], move[1], move[2])
	for key in key_list:
		if (len(key) < 5):
			store_key(key[0],key[1], key[2], key[3])
		else:
			store_key(key[0],key[1], key[2], key[3], key[4])
	for idle in idle_list:
		store_idle(idle[0], idle[1], idle[2])
	print("Dataset recorded")