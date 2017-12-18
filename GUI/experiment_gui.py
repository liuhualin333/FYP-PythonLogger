from Tkinter import *
import tkMessageBox
from subprocess import *
import time
import signal


class GUI:
	def __init__ (self, master):
		self.master = master
		master.title("Experiment GUI")
		master.geometry("400x300")

		self.sniffer = None
		self.time = 1800 # 30 minute timer

		self.label = Label(master,text="Please click on start experiment to begin your first task")
		self.label.pack()

		self.start_button = Button(master, text="Start Experiment", command=self.helloCallBack)
		self.start_button.pack()

		self.timer = Label(master,text="")


	def helloCallBack(self):
		# run shell command as a new process
		current_time = time.time()
		self.sniffer = Popen(["python", "./wrapper.py", "listener"])
		self.timer.pack()
		self.update_clock()

	def update_clock(self):
		mins,secs = divmod(self.time,60) # (math.floor(a/b),a%b)
		timeformat = '{:02d}:{:02d}'.format(mins,secs)
		self.timer.configure(text="time remaining: %s" % timeformat)
		self.time -= 1
		self.master.after(1000, self.update_clock)

	def on_closing(self):
		if (self.sniffer != None):
			self.sniffer = Popen(["python", "./wrapper.py", "client"])		

def exit_signal_handler(signal,frame):
	time.sleep(1)
	print("Ctrl-C received in wrapper")
	root.destroy()
		
signal.signal(signal.SIGINT, exit_signal_handler)

root = Tk()
gui = GUI(root)

root.protocol("WM_DELETE_WINDOW", gui.on_closing)

root.mainloop()

