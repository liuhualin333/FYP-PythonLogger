from Tkinter import *
import tkFont
import tkMessageBox
from subprocess import *
import time
import signal
import random
import os

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

		self.sniffer = None # HBLogger wrapper instance
		self.time = 10 # 30 minute timer
		self.TIME_EXPERIMENT = 10
		self.session = 0
		self.session_text = ["first","second","third"]

		self.label = Label(master,text="Please click on start experiment to begin your first task")
		self.label.grid(row=0,column=1)

		self.start_button = Button(master, text="Start Experiment", command=self.experiment_callback)
		self.start_button.grid(row=1,column=1)
		self.continue_button = Button(master, text="Continue Experiment", command=self.reset_widget_for_experiment)
		self.quit_button = Button(master, text="Quit Program", command=self.on_closing)
		self.survey_button = Button(master, text="Begin Survey", command=self.survey_callback)
		self.fast_forward_button = Button(master, text="I have finished the task", command=self.fast_forward_callback)

		self.scales = [] # list used to store the scale objects
		self.scale_labels = [Label(master,text=""), Label(master,text="")]

		self.data_labels = [] # Variable used to store labels for data

		self.timer = Label(master,text="")

		self.less_15_flag = False # Flag indicating time less than 15 mins

	def create_scale(self):
		labels = ["Frustration", "Calm", "Achievement", "Boredom", "Anxious"]
		scales = []
		for label in labels:
			scales.append(Scale(self.master, label=label, from_=1, to=5, orient=HORIZONTAL, \
			length=200, showvalue=0, tickinterval=1, resolution=1))
		for scale in scales:
			scale.set(1)
		self.scales.append(scales)

	def add_scale(self):
		timescale=["first","last"]
		for idx,ele in enumerate(self.scales):
			self.scale_labels[idx].configure(text="How do you feel when programming in the %s 15 mins" % timescale[idx])
			self.scale_labels[idx].grid(row=3*idx,column=1)
			for index,scale in enumerate(ele):
				scale.grid(row=3*idx+1+index/3,column=index%3)

	def toggle_grid_config(self,mode,number,weight):
		if (mode == "row"):
			for idx,num in enumerate(number):
				self.master.grid_rowconfigure(num,weight=weight[idx])
		elif(mode == "column"):
			for idx,num in enumerate(number):
				self.master.grid_columnconfigure(num,weight=weight[idx])

	def remove_scale(self):
		for ele in self.scales:
			for scale in ele:
				scale.grid_forget()
		self.scales = []

	def experiment_callback(self):
		# run shell command as a new process
		self.sniffer = Popen(["python", "./wrapper.py", "listener"])
		filename = self.get_filename("exp_q"+str(self.session+1), "py")
		filename = os.path.join(self.path,filename)
		open(filename,"w").close()
		self.file = Popen(["pycharm", filename])
		self.config_label_text()
		self.start_button.grid_forget()
		self.timer.grid(row=1,column=1)
		self.fast_forward_button.grid(row=2,column=1)
		self.update_clock()

	def survey_callback(self):
		self.master.geometry("900x600")
		self.toggle_grid_config("column",[0,1,2],[0,0,0])
		self.toggle_grid_config("row",[2,3,4,5],[1,1,1,1])
		self.label.grid_forget()
		self.create_scale()
		if (not self.less_15_flag):
			self.create_scale()
			self.less_15_flag = False
		self.add_scale()
		self.survey_button.grid_forget()
		self.continue_button.grid(row=6,column=1)

	def fast_forward_callback(self):
		current_time = self.time
		# If the time is less than 15 mins
		if (current_time >= 900):
			self.less_15_flag = True
		self.time = 0

	def reset_widget_for_survey(self):
		if (self.session < 2):
			self.label.configure(text="Dataset stored!\nPlease fill up survey form before you begin your %s task" % self.session_text[self.session])
		else:
			self.label.configure(text="Dataset stored!\nPlease fill up survey form before you finish experiment")
		self.session += 1
		self.timer.grid_forget()
		self.fast_forward_button.grid_forget()
		self.survey_button.grid(row=1,column=1)

	def reset_widget_for_experiment(self):
		labellist = []
		for ele in self.scales:
			for scale in ele:
				labellist.append(scale.get())
		self.data_labels.append(labellist)
		self.master.geometry("600x300")
		for scale_label in self.scale_labels:
			scale_label.grid_forget()
		self.remove_scale()
		self.continue_button.grid_forget()
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

	def config_label_text(self):
		self.label.configure(text="Finish the %s task within time limit" % self.session_text[self.session])

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
		if (len(self.data_labels) == 3):
			fname = self.get_filename("label","txt")
			label_file = open(os.path.join(self.path, fname), "w")
			for labels in self.data_labels:
				label_file.write(str(labels)+"\n")
			label_file.close()
		if (self.sniffer != None and self.sniffer.poll() == None):
			self.close_hblogger()
		root.destroy()

	def get_filename(self,name,ext):
		# Create different data file for different sessions
		fname = name+"."+ext
		extnum = 0;
		try:
		    os.makedirs(self.path)
		except OSError:
		    pass
		while os.path.isfile(os.path.join(self.path, fname)):
			extnum += 1
			fname = name+'_'+str(extnum)+'.'+ext
		return fname

def exit_signal_handler(signal,frame):
	pass
		
signal.signal(signal.SIGINT, exit_signal_handler)

root = Tk()
gui = GUI(root)
root.mainloop()