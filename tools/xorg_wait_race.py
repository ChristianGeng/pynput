"""Reproduce: a key sent right after Listener.wait() can be lost on Xorg.

Run under a throwaway X server, for example:

    xvfb-run -a python tools/xorg_wait_race.py 200

Each trial starts a keyboard listener, waits for it with ``wait()``, and
immediately sends one key press and release through XTEST. It counts the
trials in which the listener never saw the press.
"""

import sys
import threading

from Xlib import X, XK, display
from Xlib.ext import xtest

from pynput import keyboard


def trial(d, keycode):
    pressed = threading.Event()
    listener = keyboard.Listener(on_press=lambda key: pressed.set())
    listener.start()
    try:
        listener.wait()
        xtest.fake_input(d, X.KeyPress, keycode)
        xtest.fake_input(d, X.KeyRelease, keycode)
        d.sync()
        return pressed.wait(2)
    finally:
        listener.stop()
        # The listener notices stop() at its next event: send one to end it.
        xtest.fake_input(d, X.KeyPress, keycode)
        xtest.fake_input(d, X.KeyRelease, keycode)
        d.sync()
        listener.join(5)


def main():
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    d = display.Display()
    keycode = d.keysym_to_keycode(XK.string_to_keysym("F12"))
    lost = sum(not trial(d, keycode) for _ in range(trials))
    print(f"lost {lost} of {trials} key presses sent right after wait()")
    d.close()
    return 1 if lost else 0


if __name__ == "__main__":
    sys.exit(main())
