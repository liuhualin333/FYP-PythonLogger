import sniffer
import hook


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