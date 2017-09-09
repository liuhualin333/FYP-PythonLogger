import const
import time
import sqlalchemy
import models
import os.path
from models import Click, Keys, Move, Idle, Ditrigraph

# Create different data file for different sessions
fname = "log.db"
name = "log"
ext = "db"
extnum = 0;
if os.path.isfile(fname):
	while os.path.isfile(fname):
		extnum += 1
		fname = name+'_'+str(extnum)+'.'+ext
session_maker = models.initialize(fname)
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

def store_click(button, x, y):
	""" Stores incoming mouse-clicks """
	session.add(Click(button, x, y))
	trycommit()

def store_move(time, move):
	session.add(Move(time, move))
	trycommit()

def store_idle(idle_time, mode):
	session.add(Idle(idle_time, mode))
	trycommit()

def store_ditrigraph (ditrigraph, mode):
	session.add(Ditrigraph(ditrigraph, mode))
	trycommit()

def store_key(key, asciiCode, holding, *args):
	session.add(Keys(key, asciiCode, holding, args))
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
	store_click(button, x, y)

def got_mouse_move(mouse_path, start_time, end_time):
	print "Length: %d, Duration: %fs" % (len(mouse_path), (end_time - start_time))
	store_move((end_time - start_time), len(mouse_path))

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
		store_key(finalstring, key[1], False)
	# Key holding
	else:
		holdtime = time.time() - keyHoldStart + const.PRESSING_COMPENSATION
		print "Hold <%s> key for %fs" % (finalstring, holdtime)
		store_key(finalstring, key[1], True, holdtime)

def got_key_idle(idle_time):
	if idle_time > const.IDLE_THRESHOLD:
		# Let's not record implicit idleness
		print "Keyboard idle for %fs" % (idle_time)
		store_idle(idle_time, "keyboard")

def got_mouse_idle(idle_time):
	if idle_time > const.IDLE_THRESHOLD:
		# Let's not record implicit idleness
		print "Mouse idle for %fs" % (idle_time)
		store_idle(idle_time, "mouse")

def got_ditrigraph(ditrigraph, mode):
	print "Got %s : %s" % (mode, ditrigraph)
	store_ditrigraph(ditrigraph, mode)