from Tkinter import *
import tkFont
import tkMessageBox
from subprocess import *
import time
import signal
import random

class GUI:
	def __init__ (self, master):
		self.master = master
		master.title("Experiment GUI")
		master.geometry("600x300")

		# Set Default Font
		default_font = tkFont.nametofont("TkDefaultFont")
		default_font.configure(family="Times New Roman",size=15)
		master.option_add("*Font", default_font)
		master.grid_columnconfigure(0,weight=1)
		master.grid_columnconfigure(2,weight=1)
		master.grid_rowconfigure(0,weight=1)
		master.grid_rowconfigure(1,weight=1)
		master.grid_rowconfigure(2,weight=1)
		master.protocol("WM_DELETE_WINDOW", self.on_closing)

		self.sniffer = None # HBLogger wrapper instance
		self.time = 10 # 30 minute timer
		self.session = 0

		self.label = Label(master,text="Please click on start experiment to begin your first task")
		self.label.grid(row=0,column=1)

		self.start_button = Button(master, text="Start Experiment", command=self.experimentCallBack)
		self.start_button.grid(row=1,column=1)
		self.continue_button = Button(master, text="Continue Experiment", command=self.resetWidgetForExperiment)
		self.quit_button = Button(master, text="Quit Program", command=self.on_closing)
		self.survey_button = Button(master, text="Begin Survey", command=self.surveyCallBack)
		self.fast_forward_button = Button(master, text="I have finished the task", command=self.fastforwardCallBack)

		self.scales = [] # list used to store the scale objects
		self.data_labels = [] # Variable used to store labels for data

		self.timer = Label(master,text="")

		self.less_15_flag = False

		self.scale_labels = [Label(master,text=""), Label(master,text="")]

	def createScale(self):
		frust_scale = Scale(self.master, label="Frustration", from_=1, to=5, orient=HORIZONTAL, \
			length=200, showvalue=0, tickinterval=1, resolution=1)
		calm_scale = Scale(self.master, label="Calm", from_=1, to=5, orient=HORIZONTAL, \
			length=200, showvalue=0, tickinterval=1, resolution=1)
		achiev_scale = Scale(self.master, label="Achievement", from_=1, to=5, orient=HORIZONTAL, \
			length=200, showvalue=0, tickinterval=1, resolution=1)
		bored_scale = Scale(self.master, label="Boredom", from_=1, to=5, orient=HORIZONTAL, \
			length=200, showvalue=0, tickinterval=1, resolution=1)
		anxious_scale = Scale(self.master, label="Anxious", from_=1, to=5, orient=HORIZONTAL, \
			length=200, showvalue=0, tickinterval=1, resolution=1)
		scales = [frust_scale,calm_scale,achiev_scale,bored_scale,anxious_scale]
		for scale in scales:
			scale.set(3)
		self.scales.append(scales)

	def addScale(self):
		timescale=["first","last"]
		for idx,ele in enumerate(self.scales):
			self.scale_labels[idx].configure(text="How do you feel when programming in the %s 15 mins" % timescale[idx])
			self.scale_labels[idx].grid(row=3*idx,column=1)
			for index,scale in enumerate(ele):
				scale.grid(row=3*idx+1+index/3,column=index%3)

	def toggleGridConfig(self,mode,number,weight):
		if (mode == "row"):
			for idx,num in enumerate(number):
				self.master.grid_rowconfigure(num,weight=weight[idx])
		elif(mode == "column"):
			for idx,num in enumerate(number):
				self.master.grid_columnconfigure(num,weight=weight[idx])

	def removeScale(self):
		for ele in self.scales:
			for scale in ele:
				scale.grid_forget()
		self.scales = []

	def experimentCallBack(self):
		# run shell command as a new process
		self.sniffer = Popen(["python", "./wrapper.py", "listener"])
		self.configLabelText()
		self.start_button.grid_forget()
		self.timer.grid(row=1,column=1)
		self.fast_forward_button.grid(row=2,column=1)
		self.update_clock()

	def surveyCallBack(self):
		self.master.geometry("900x600")
		self.toggleGridConfig("column",[0,1,2],[0,0,0])
		self.toggleGridConfig("row",[2,3,4,5],[1,1,1,1])
		self.label.grid_forget()
		self.createScale()
		if (self.less_15_flag):
			self.createScale()
			self.less_15_flag = False
		self.addScale()
		self.survey_button.grid_forget()
		self.continue_button.grid(row=6,column=1)

	def fastforwardCallBack(self):
		current_time = self.time
		# If the time is less than 15 mins
		if (current_time < 900):
			self.less_15_flag = True
		self.time = 0


	def resetWidgetForSurvey(self):
		session = ["first", "second", "third"]
		if (self.session < 2):
			self.session += 1
			self.label.configure(text="Dataset stored!\nPlease fill up survey form before you begin your %s task" % session[self.session])
		else:
			self.label.configure(text="Dataset stored!\nPlease fill up survey form before you finish experiment")
		self.timer.grid_forget()
		self.fast_forward_button.grid_forget()
		self.survey_button.grid(row=1,column=1)

	def resetWidgetForExperiment(self):
		labellist = []
		for ele in self.scales:
			for scale in ele:
				labellist.append(scale.get())
		print labellist
		self.data_labels.append(labellist)
		self.master.geometry("600x300")
		for scale_label in self.scale_labels:
			scale_label.grid_forget()
		self.removeScale()
		self.continue_button.grid_forget()
		self.toggleGridConfig("column",[0,1,2],[1,0,1])
		self.toggleGridConfig("row",[2,3,4,5],[1,0,0,0])
		session = ["first", "second", "third"]
		self.label.grid(row=0, column=1)
		if (self.session < 2):
			self.label.configure(text="Please click on start experiment to begin your %s task" % session[self.session])
			self.time = 10
			self.start_button.grid(row=1,column=1)
		else:
			self.label.configure(text="Thank you for your participation. The experiment is over")
			self.quit_button.grid(row=1,column=1)

	def configLabelText(self):
		session = ["first", "second", "third"]
		self.label.configure(text="Finish the %s task within time limit" % session[self.session])

	def closeHBLogger(self):
		# Close the recording
		if (self.sniffer != None):
			Popen(["python", "./wrapper.py", "client"])
			while (self.sniffer.poll() == None):
				pass

	def update_clock(self):
		importantfont=('Times New Roman',20,'bold')
		mins,secs = divmod(self.time,60) # (math.floor(a/b),a%b)
		timeformat = '{:02d}:{:02d}'.format(mins,secs)
		self.timer.configure(text="time remaining: %s" % timeformat)
		if (0 <= self.time < 300):
			if (self.time % 2 == 0):
				self.timer.config(fg="red",font=importantfont)
			else:
				self.timer.config(fg="black",font=importantfont)
			# Jump to foreground
			if (self.time == 0):
				self.label.configure(text="Storing dataset...")
				self.master.lift()
				self.master.attributes('-topmost',True)
				self.master.attributes('-topmost',False)
			self.time -= 1
			self.master.after(1000, self.update_clock)
		elif (self.time < 0):
			self.closeHBLogger()
			self.resetWidgetForSurvey()
		else:
			self.time -= 1
			self.master.after(1000, self.update_clock)

	def on_closing(self):
		if (self.sniffer != None):
			if (self.sniffer.poll() == None):
				self.closeHBLogger()
		root.destroy()	

def exit_signal_handler(signal,frame):
	time.sleep(1)
	print("Ctrl-C received in wrapper")
		
signal.signal(signal.SIGINT, exit_signal_handler)

root = Tk()
gui = GUI(root)
root.mainloop()

