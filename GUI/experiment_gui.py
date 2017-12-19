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

		master.protocol("WM_DELETE_WINDOW", self.on_closing)

		self.sniffer = None # HBLogger wrapper instance
		self.time = 30 # 30 minute timer
		self.session = 0

		self.label = Label(master,text="Please click on start experiment to begin your first task")
		self.label.pack(fill="none",expand=True)

		self.start_button = Button(master, text="Start Experiment", command=self.helloCallBack)
		self.start_button.pack(fill="none",expand=True)

		self.quit_button = Button(master, text="Quit Program", command=self.on_closing)

		self.timer = Label(master,text="")


	def helloCallBack(self):
		# run shell command as a new process
		self.sniffer = Popen(["python", "./wrapper.py", "listener"])
		self.configLabelText()
		self.start_button.pack_forget()
		self.timer.pack(fill="none",expand=True)
		self.update_clock()

	def resetWidget(self):
		session = ["first", "second", "third"]
		if (self.session < 2):
			self.session += 1
			self.label.configure(text="Please click on start experiment to begin your %s task" % session[self.session])
			self.time = 30
			self.timer.pack_forget()
			self.start_button.pack(fill="none",expand=True)
		else:
			self.label.configure(text="Thank you for your attention. The experiment is over")
			self.timer.pack_forget()
			self.quit_button.pack(fill="none",expand=True)

	def configLabelText(self):
		session = ["first", "second", "third"]
		self.label.configure(text="Finish the %s task within time limit" % session[self.session])

	def closeHBLogger(self):
		# Close the recording
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
				self.master.lift()
				self.master.attributes('-topmost',True)
				self.master.attributes('-topmost',False)
			self.time -= 1
			self.master.after(1000, self.update_clock)
		elif (self.time < 0):
			self.closeHBLogger()
			self.resetWidget()
		else:
			self.time -= 1
			self.master.after(1000, self.update_clock)

	def on_closing(self):
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

