from Tkinter import *
import tkFont
from subprocess import *
import time
import signal
import random
import os
import cv2
import multiprocessing
from PIL import ImageGrab, Image, ImageTk
import threading
import numpy as np
import math

event = multiprocessing.Event()
screen_event = multiprocessing.Event()
p = None
p_screen = None

# File store location
path = os.path.expanduser("~/.HBLog")

def calculate_fps():
	# Start default camera
	video = cv2.VideoCapture(0);
	# Number of frames to capture
	num_frames = 120;
	# Start time
	start = time.time()
	# Grab a few frames
	for i in xrange(0, num_frames) :
		ret, frame = video.read()
	# End time
	end = time.time()
	# Time elapsed
	seconds = end - start
	# Calculate frames per second
	fps  = num_frames / seconds;
	# Release video
	video.release()
	num_screen_frames = 0
	start = time.time()
	while (True):
		if num_screen_frames == 300:
			break
		img = ImageGrab.grab(bbox=(0,0,1366,768))
		img_np = np.array(img)
		frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
		num_screen_frames+=1
	end = time.time()
	fps_screen = num_screen_frames / (end - start)
	return (fps,fps_screen)

# For video recording
def start_recording(e,fps):
	cap = cv2.VideoCapture(0)
	fourcc = cv2.VideoWriter_fourcc(*'XVID')
	videoname = get_filename('output','avi')
	out = cv2.VideoWriter(os.path.join(os.path.expanduser("~/.HBLog"),videoname),fourcc, fps, (640,480))
	while(cap.isOpened()):
		if e.is_set():
			cap.release()
			out.release()
			cv2.destroyAllWindows()
			e.clear()
		ret, frame = cap.read()
		if ret==True:
			out.write(frame)
		else:
			break

def start_recording_screen(e,fps):
	fourcc = cv2.VideoWriter_fourcc(*'XVID')
	videoname = get_filename('output_screen','avi')
	out = cv2.VideoWriter(os.path.join(os.path.expanduser("~/.HBLog"),videoname),fourcc, fps, (1366,768))
	while (True):
		if e.is_set():
			out.release()
			cv2.destroyAllWindows()
			e.clear()
			break
		img = ImageGrab.grab(bbox=(0,0,1366,768))
		img_np = np.array(img)
		frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
		out.write(frame)

def start_recording_proc(fps,fps_screen):
	global p, p_screen
	p = multiprocessing.Process(target=start_recording, args=(event,fps,))
	p_screen = multiprocessing.Process(target=start_recording_screen, args=(screen_event,fps_screen,))
	p.start()
	p_screen.start()
	time.sleep(2) # For camera to boot

# -------end video capture
def stop_recording():
	global event,screen_event, p, p_screen
	event.set()
	screen_event.set()
	p.join()
	p_screen.join()
	# Reset
	event = multiprocessing.Event()
	screen_event = multiprocessing.Event()
	p = None
	p_screen = None

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
	return fname


class GUI:
	def __init__ (self, master):
		self.master = master
		master.title("Experiment GUI")
		master.geometry("600x300")

		# Set default font
		self.default_font = tkFont.nametofont("TkDefaultFont")
		self.default_font.configure(family="Times New Roman",size=15)
		master.option_add("*Font", self.default_font)
		# Set grid layout
		self.toggle_grid_config("column",[0,1,2],[1,0,1])
		self.toggle_grid_config("row",[0,1,2],[1,1,1])
		# Set exit behaviour
		master.protocol("WM_DELETE_WINDOW", self.on_closing)
		# File store location
		self.path = os.path.expanduser("~/.HBLog")
		self.fps,self.fps_screen = calculate_fps()

		self.sniffer = None # HBLogger wrapper instance
		self.video_survey = None
		self.time = 1800 # 30 minute timer
		self.TIME_EXPERIMENT = 1800
		self.session = 0
		self.session_text = ["first","second","third"]

		self.label = Label(master,text="Please click on start experiment to begin your first task")
		self.label.grid(row=0,column=1)

		self.start_button = Button(master, text="Start Experiment", command=self.experiment_callback)
		self.start_button.grid(row=1,column=1)
		self.quit_button = Button(master, text="Quit Program", command=self.on_closing)
		self.survey_button = Button(master, text="Begin Survey", command=self.survey_callback)
		self.fast_forward_button = Button(master, text="I have finished the task", command=self.fast_forward_callback)

		self.video_names = []
		self.data_labels = [] # Variable used to store labels for data
		self.threads = []
		self.timer = Label(master,text="")


	def toggle_grid_config(self,mode,number,weight):
		if (mode == "row"):
			for idx,num in enumerate(number):
				self.master.grid_rowconfigure(num,weight=weight[idx])
		elif(mode == "column"):
			for idx,num in enumerate(number):
				self.master.grid_columnconfigure(num,weight=weight[idx])

	def experiment_callback(self):
		# run shell command as a new process
		if (len(self.video_names) != 0):
			self.video_names= []
		self.video_names.append(os.path.join(self.path,get_filename('output_screen','avi')))
		self.video_names.append(os.path.join(self.path,get_filename('output','avi')))
		start_recording_proc(self.fps,self.fps_screen)
		self.sniffer = Popen(["python", "./wrapper.py", "listener"])
		filename = get_filename("exp_q"+str(self.session+1), "py")
		filename = os.path.join(self.path,filename)
		open(filename,"w").close()
		self.file = Popen(["subl", "-n", filename])
		self.label.configure(text="Finish the %s task within time limit" % self.session_text[self.session])
		self.start_button.grid_forget()
		self.timer.grid(row=1,column=1)
		self.fast_forward_button.grid(row=2,column=1)
		self.update_clock()

	def survey_callback(self):
		self.video_survey = Popen(["python", "./label_gui.py", self.video_names[1],self.video_names[0]])
		self.label.grid_forget()
		self.survey_button.grid_forget()
		self.reset_widget_for_experiment()

	def fast_forward_callback(self):
		current_time = self.time
		# If the time is less than 15 mins
		if (current_time >= 900):
			self.less_15_flag = True
		self.time = 0

	def reset_widget_for_survey(self):
		if (self.session < 2):
			self.label.configure(text="Dataset stored!\nPlease watch the video and fill up survey form\n before you begin your %s task\nEvery video clip is about 5 mins long" % self.session_text[self.session+1])
		else:
			self.label.configure(text="Dataset stored!\nPlease watch the video and fill up survey form\n before you finish experiment\nEvery video clip is about 5 mins long")
		self.session += 1
		self.timer.grid_forget()
		self.fast_forward_button.grid_forget()
		self.survey_button.grid(row=1,column=1)

	def reset_widget_for_experiment(self):
		self.master.geometry("600x300")
		self.toggle_grid_config("column",[0,1,2],[1,0,1])
		self.toggle_grid_config("row",[2,3,4,5],[1,0,0,0])
		self.label.grid(row=0, column=1)
		if (self.session <= 2):
			self.label.configure(text="Please click on start experiment to begin your %s task" % self.session_text[self.session])
			self.time = self.TIME_EXPERIMENT
			self.timer.config(fg="black",font=self.default_font)
			self.start_button.grid(row=1,column=1)
		else:
			self.label.configure(text="Thank you for your participation. The experiment is over")
			self.quit_button.grid(row=1,column=1)

	def close_hblogger(self):
		# Close the recording
		if (self.sniffer != None):
			Popen(["python", "./wrapper.py", "client"])
			while (self.sniffer.poll() == None):
				pass
		self.sniffer == None

	def jump_to_foreground(self):
		self.master.lift()
		self.master.attributes('-topmost',True)
		self.master.attributes('-topmost',False)

	def update_clock(self):
		importantfont=('Times New Roman',20,'bold')
		mins,secs = divmod(self.time,60) # (math.floor(a/b),a%b)
		timeformat = '{:02d}:{:02d}'.format(mins,secs)
		self.timer.configure(text="time remaining: %s" % timeformat)
		if (0 <= self.time < 900):
			if (self.time % 2 == 0):
				self.timer.config(fg="red",font=importantfont)
			else:
				self.timer.config(fg="black",font=importantfont)
			# Jump to foreground
			if (self.time == 0):
				stop_recording()
				self.label.configure(text="Storing dataset...")
				self.jump_to_foreground()
			self.time -= 1
			self.master.after(1000, self.update_clock)
		elif (self.time < 0):
			self.close_hblogger()
			self.reset_widget_for_survey()
		else:
			# Remind them 15 mins remaining
			if (self.time == 900):
				self.jump_to_foreground()
			self.time -= 1
			self.master.after(1000, self.update_clock)

	def on_closing(self):
		if (self.sniffer != None and self.sniffer.poll() == None):
			self.close_hblogger()
		root.destroy()

def exit_signal_handler(signal,frame):
	pass

if __name__ == "__main__":		
	signal.signal(signal.SIGINT, exit_signal_handler)
	root = Tk()
	gui = GUI(root)
	root.mainloop()