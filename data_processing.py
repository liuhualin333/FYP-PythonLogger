from HBLogger import models
import os
import sys
import time
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# This file serves to turn down granularity of the low level data

path = os.path.expanduser("~/.HBLog")
def get_filename(name,ext):
    # Create different data file for different sessions
    fname = name+"."+ext
    extnum = 0;
    try:
        os.makedirs(path)
    except OSError:
        pass
    while os.path.isfile(os.path.join(path, fname)):
        extnum += 1
    	fname = name+'_'+str(extnum)+'.'+ext
    fname = name+"_"+str(extnum-1)+"."+ext
    return fname

def initialize_log(filename):
	path = os.path.expanduser("~/.HBLog")
	orig_fname = filename
	fname = os.path.join(path, orig_fname)
	engine = create_engine('sqlite:///%s' % fname)
	Session = sessionmaker(bind=engine)
	session = Session()
	ops_list = []

	for click in session.query(models.Click).order_by(models.Click.id):
		ops_list.append([click, click.timestamp])
	for move in session.query(models.Move).order_by(models.Move.id):
		ops_list.append([move, move.timestamp])
	for idle in session.query(models.Idle).order_by(models.Idle.id):
		ops_list.append([idle, idle.timestamp])
	for keys in session.query(models.Keys).order_by(models.Keys.id):
		ops_list.append([keys, keys.timestamp])

	def timeStamp(list):
		return list[1]

	ops_list.sort(key=timeStamp)

	return ops_list, orig_fname, session

def get_start_time(ops_list):
	return ops_list[0][1]

def write_data(file, feature_arr, labelfile):
	for idx,item in enumerate(feature_arr):
		feature_arr[idx] = str(item)
	file.write(",".join(feature_arr)+","+labelfile.readline().split(",")[0]+"\n")

def main(filename, labelfile):
	ops_list, fname, session = initialize_log(filename)
	start_time = get_start_time(ops_list)
	print("Start Time: %f" % start_time)

	keys_num = 0
	hold_keys = 0
	backspace_typed = 0
	backspace_held = 0
	space_typed = 0
	space_held = 0
	copy_typed = 0
	undo_typed = 0
	combo_typed = 0
	mouse_moved_num = 0
	mouse_left_click = 0
	mouse_right_click = 0
	mouse_wheel_action = 0
	keyboard_idle_times_less_60 = 0
	mouse_idle_times_less_60 = 0
	keyboard_idle_times_more_60 = 0
	mouse_idle_times_more_60 = 0

	current_minute = 0
	current_timespot = start_time

	file = open(os.path.join(path, fname.split(".")[0]+"_processed.csv"), 'w')
	label = open(os.path.join(path, labelfile), 'r')

	for activity in ops_list:
		if (activity[1] - current_timespot > 60):
			# TODO: Write data
			feature_arr = [current_minute, keys_num, hold_keys, backspace_typed, backspace_held, space_typed, space_held, copy_typed, undo_typed, combo_typed,\
			mouse_moved_num, mouse_left_click, mouse_right_click, mouse_wheel_action, keyboard_idle_times_less_60, mouse_idle_times_less_60,\
			keyboard_idle_times_more_60, mouse_idle_times_more_60]
			write_data(file,feature_arr,label)

			keys_num = 0
			hold_keys = 0
			backspace_typed = 0
			backspace_held = 0
			space_typed = 0
			space_held = 0
			copy_typed = 0
			undo_typed = 0
			combo_typed = 0
			mouse_moved_num = 0
			mouse_left_click = 0
			mouse_right_click = 0
			mouse_wheel_action = 0
			keyboard_idle_times_less_60 = 0
			mouse_idle_times_less_60 = 0
			keyboard_idle_times_more_60 = 0
			mouse_idle_times_more_60 = 0

			current_minute += 1
			current_timespot += 60

		class_type = activity[0].__class__.__name__
		if (class_type == 'Idle'):
			if (activity[0].mode == "keyboard"):
				if (activity[0].idle_time <= 60):
					keyboard_idle_times_less_60 += 1
				else:
					keyboard_idle_times_more_60 += 1
			else:
				if (activity[0].idle_time <= 60):
					mouse_idle_times_less_60 += 1
				else:
					mouse_idle_times_more_60 += 1
		elif(class_type == 'Keys'):
			keys_num += 1
			if activity[0].holding:
				hold_keys+=1
			if (activity[0].text == "Back"):
				if (activity[0].holding):
					backspace_held += 1
				else:
					backspace_typed += 1
			elif (activity[0].text == "Space" or activity[0].text == ""):
				if (activity[0].holding):
					space_held += 1
				else:
					space_typed += 1
			elif (len(activity[0].text.split('+')) > 1):
				combo_typed += 1
				if (activity[0].text == "Ctrl+C"):
					copy_typed += 1
				elif (activity[0].text == "Ctrl+Z"):
					undo_typed += 1
		elif (class_type == "Move"):
			mouse_moved_num += 1
		elif (class_type == "Click"):
			if (activity[0].button == "left"):
				mouse_left_click+=1
			elif(activity[0].button == "right"):
				mouse_right_click+=1
			elif (activity[0].button == "wheelUp" or activity[0].button == "wheelDown"):
				mouse_wheel_action+=1
	fname = get_filename("log", "db")
	os.remove(os.path.join(path,fname))
if __name__ == "__main__":
	main(sys.argv[1], sys.argv[2])