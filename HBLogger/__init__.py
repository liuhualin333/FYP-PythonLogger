import hook
import sys
import platform
import functool
import signal

if platform.system() == 'Windows':
    from HBLogger import sniffer_Win as sniffer
else:
    sys.exit(0)

sniffer1 = None

def exit_signal_handler(signal,frame):
	print("Terminate signal received")
	if (sniffer1 != None):
		sniffer1.cancel()
		
signal.signal(signal.SIGINT, exit_signal_handler)

def main():
	global sniffer1
	try:
		sniffer1 = sniffer.Sniffer()
		sniffer1.key_down_hook = hook.got_key
		sniffer1.mouse_button_hook = hook.got_mouse_click
		sniffer1.mouse_move_hook = hook.got_mouse_move
		sniffer1.key_idle_hook = hook.got_key_idle
		sniffer1.mouse_idle_hook = hook.got_mouse_idle
		sniffer1.write_data_hook = hook.write_data
		sniffer1.run()

	except SystemExit:
		sniffer1.cancel()

	except KeyboardInterrupt:
		sniffer1.cancel()
		pass
if __name__ == '__main__':
	main()