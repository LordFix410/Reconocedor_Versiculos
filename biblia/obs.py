import time
import pydirectinput


def _hotkey(*teclas):
    presionadas = []

    try:
        for t in teclas:
            pydirectinput.keyDown(t)
            presionadas.append(t)
            time.sleep(0.04)
    finally:
        # Pase lo que pase, soltar todas las teclas que se bajaron
        # (si no, Ctrl/Shift se quedan "pegados").
        for t in reversed(presionadas):
            pydirectinput.keyUp(t)


def mostrar_presentacion():
    # OBS: Ctrl + Shift + F12
    _hotkey("ctrl", "shift", "f12")


def mostrar_biblia():
    # OBS: Ctrl + Shift + F11
    _hotkey("ctrl", "shift", "f11")
