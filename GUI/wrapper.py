import subprocess, time, signal, sys, os
from multiprocessing.connection import Listener
from multiprocessing.connection import Client

# This file is used to wrap around the HBLogger in order to let it
# receive the SIGINT event from the system

# It depends on mode variable to play the role of client/listener

# Code is adapted from the StackOverflow: 
# https://stackoverflow.com/questions/7085604/sending-c-to-python-subprocess-objects-on-windows

def main(mode):
	def exit_signal_handler(signal,frame):
		print("Terminate signal received")
		time.sleep(1)

	def listen_to_port():
		address = ('localhost', 6000)
		listener = Listener(address, authkey="secret")
		conn = listener.accept()
		print 'connection accepted from', listener.last_accepted
		while True:
			msg = conn.recv()
			# do something with msg
			if (msg=="close"):
				conn.close()
				break

	def send_ctrl_c():
		address = ('localhost', 6000)
		conn = Client(address, authkey="secret")
		conn.send("close")

	if (mode == "listener"):
		signal.signal(signal.SIGINT, exit_signal_handler)

		print("Wrapper.py started")
		subprocess.Popen(["HBLogger"])
		listen_to_port()
		os.kill(0,signal.CTRL_C_EVENT)

	elif (mode == "client"):
		send_ctrl_c()


if __name__ == "__main__":
	mode_string = sys.argv[1]
	main(mode_string)