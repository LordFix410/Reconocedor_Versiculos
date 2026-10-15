import time
import pydirectinput


def _hotkey(*teclas):
    for t in teclas:
        pydirectinput.keyDown(t)
        time.sleep(0.04)
    for t in reversed(teclas):
        pydirectinput.keyUp(t)


def mostrar_presentacion():
    # OBS: Ctrl + Shift + F12
    _hotkey("ctrl", "shift", "f12")


def mostrar_biblia():
    # OBS: Ctrl + Shift + F11
    _hotkey("ctrl", "shift", "f11")