import hook
import sys
import platform

if platform.system() == 'Darwin':
    from HBLogger import sniffer_Mac as sniffer
elif platform.system() == 'Windows':
    from HBLogger import sniffer as sniffer
else:
    sys.exit(0)

def main():
	try:
		sniffer1 = sniffer.Sniffer()
		sniffer1.key_down_hook = hook.got_key
		sniffer1.mouse_button_hook = hook.got_mouse_click
		sniffer1.mouse_move_hook = hook.got_mouse_move
		sniffer1.key_idle_hook = hook.got_key_idle
		sniffer1.mouse_idle_hook = hook.got_mouse_idle
		sniffer1.ditrigraph_hook = hook.got_ditrigraph
		sniffer1.run()

	except SystemExit:
		sniffer1.cancel()

	except KeyboardInterrupt:
		pass
if __name__ == '__main__':
	main()