import time
import pydirectinput


def mostrar_presentacion():

    # Hotkey configurado en OBS:
    # Ctrl + Shift + F12

    pydirectinput.keyDown("ctrl")
    time.sleep(0.04)

    pydirectinput.keyDown("shift")
    time.sleep(0.04)

    pydirectinput.keyDown("f12")
    time.sleep(0.04)

    pydirectinput.keyUp("f12")
    pydirectinput.keyUp("shift")
    pydirectinput.keyUp("ctrl")