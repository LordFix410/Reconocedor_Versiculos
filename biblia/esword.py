import time
import ctypes

import pyautogui
import pygetwindow as gw
import pydirectinput

from biblia.obs import mostrar_biblia


NOMBRE_VENTANA = (
    "e-sword - the Sword of the LORD "
    "with an electronic edge"
)

_ventana = None

pyautogui.PAUSE = 0
pydirectinput.PAUSE = 0


def obtener_ventana():

    global _ventana

    if _ventana is not None:
        try:
            if _ventana.title:
                return _ventana
        except Exception:
            _ventana = None

    ventanas = gw.getWindowsWithTitle(
        NOMBRE_VENTANA
    )

    if not ventanas:
        return None

    _ventana = ventanas[0]

    return _ventana


def buscar(referencia, mostrar_obs=False):

    global _ventana

    ventana = obtener_ventana()

    if ventana is None:
        print("❌ No se encontró e-Sword")
        return False

    try:

        # =====================================
        # 1. OBS
        # =====================================

        if mostrar_obs:

            print("📺 Hotkey OBS → Biblia")

            # Hotkey propio de OBS (Ctrl+Shift+F11),
            # ya NO es Ctrl+L, así que la búsqueda de
            # e-Sword no vuelve a activar la escena.
            mostrar_biblia()

            time.sleep(0.10)

        # =====================================
        # 2. ACTIVAR e-SWORD
        # =====================================

        if ventana.isMinimized:
            ventana.restore()
            time.sleep(0.05)

        try:
            ventana.activate()
        except Exception:
            pass

        hwnd = ventana._hWnd

        try:
            ctypes.windll.user32.SetForegroundWindow(
                hwnd
            )
            if ctypes.windll.user32.GetForegroundWindow() != hwnd:
                print("⚠️ e-Sword no tomó el foco, cancelo")
                return False
        except Exception:
            pass

        time.sleep(0.10)

        # =====================================
        # 3. CTRL + L SOLO PARA e-SWORD
        # =====================================

        print("📖 Abriendo búsqueda e-Sword")

        pyautogui.keyDown("ctrl")
        time.sleep(0.02)

        pyautogui.press("l")
        time.sleep(0.02)

        pyautogui.keyUp("ctrl")

        time.sleep(0.05)

        # =====================================
        # 4. ESCRIBIR CITA
        # =====================================

        pyautogui.write(
            str(referencia),
            interval=0
        )

        pyautogui.press("enter")

        return True

    except Exception as e:

        print("❌ Error e-Sword:", e)

        _ventana = None

        return False