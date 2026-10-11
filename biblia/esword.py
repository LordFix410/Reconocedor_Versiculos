import time
import pyautogui
import pygetwindow as gw
import pydirectinput
import ctypes
import win32api
import win32con

KEYEVENTF_KEYUP = 0x0002

VK_CONTROL = 0x11
VK_L = 0x4C


def ctrl_l_global():

    user32 = ctypes.windll.user32

    # CTRL abajo
    user32.keybd_event(
        VK_CONTROL,
        0,
        0,
        0
    )

    time.sleep(0.03)

    # L abajo
    user32.keybd_event(
        VK_L,
        0,
        0,
        0
    )

    time.sleep(0.03)

    # L arriba
    user32.keybd_event(
        VK_L,
        0,
        KEYEVENTF_KEYUP,
        0
    )

    time.sleep(0.03)

    # CTRL arriba
    user32.keybd_event(
        VK_CONTROL,
        0,
        KEYEVENTF_KEYUP,
        0
    )

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

            # IMPORTANTE:
            # Mandarlo ANTES de tocar/focalizar e-Sword.
            ctrl_l_global()

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