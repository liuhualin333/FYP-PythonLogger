import subprocess, time, signal, sys, os
from multiprocessing.connection import Listener
from multiprocessing.connection import Client

# This file is used to wrap around the HBLogger and FFmpeg in order to let it
# receive the SIGINT event from the system

# It depends on mode variable to play the role of client/listener

# Code is adapted from the StackOverflow: 
# https://stackoverflow.com/questions/7085604/sending-c-to-python-subprocess-objects-on-windows

def main(mode):
	def exit_signal_handler(signal,frame):
		pass

	def listen_to_port(port_num):
		address = ('localhost', port_num)
		listener = Listener(address, authkey="secret")
		conn = listener.accept()
		#print 'connection accepted from', listener.last_accepted
		while True:
			msg = conn.recv()
			# do something with msg
			if (msg=="close"):
				conn.close()
				break

	def send_ctrl_c(port_num):
		address = ('localhost', port_num)
		conn = Client(address, authkey="secret")
		conn.send("close")
		conn.close()

	if (mode == "listener"):
		signal.signal(signal.SIGINT, exit_signal_handler)
		print("Logger started")
		subprocess.Popen(["HBLogger"])
		listen_to_port(6000)
		os.kill(0,signal.CTRL_C_EVENT)

	elif (mode == "client"):
		send_ctrl_c(6000)
	elif (mode == "record_vid"):
		print("Video Recording")
		subprocess.Popen(["ffmpeg", "-v", "0", "-f", "dshow", "-video_size", "640x480", "-i", "video=C922 Pro Stream Webcam",\
		 "-b:v", "4M", "-preset:v", "ultrafast", "-filter:v", "setpts=0.5*PTS", sys.argv[2]])
	elif (mode == "record_screen"):
		print("Screen Recording")
		subprocess.Popen(["ffmpeg", "-v", "0", "-f", "dshow", "-i", "video=screen-capture-recorder", "-b:v", "4M", "-preset:v", "ultrafast", "-filter:v", "setpts=0.5*PTS", sys.argv[2]])

if __name__ == "__main__":
	mode_string = sys.argv[1]
	main(mode_string)