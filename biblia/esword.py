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

# Si el título exacto cambia (otra versión de e-Sword),
# se busca cualquier ventana cuyo título EMPIECE con esto.
PREFIJO_VENTANA = "e-sword"

# Cuántas veces intentar encontrar y poner al frente e-Sword
# antes de rendirse (cada intento ~0.1-0.25 s).
REINTENTOS_VENTANA = 6
ESPERA_SIN_VENTANA = 0.15

_ventana = None

pyautogui.PAUSE = 0
pydirectinput.PAUSE = 0


def _ventana_viva(v):
    """True si el objeto ventana guardado sigue siendo válido."""
    try:
        return bool(v.title)
    except Exception:
        return False


def obtener_ventana():
    """Devuelve la ventana de e-Sword (la cacheada o una nueva)."""

    global _ventana

    if _ventana is not None:
        if _ventana_viva(_ventana):
            return _ventana
        _ventana = None

    # 1) Título exacto de siempre
    try:
        ventanas = gw.getWindowsWithTitle(NOMBRE_VENTANA)
    except Exception:
        ventanas = []

    # 2) Respaldo: cualquier ventana que empiece con "e-sword"
    if not ventanas:
        try:
            ventanas = [
                w for w in gw.getWindowsWithTitle(PREFIJO_VENTANA)
                if (w.title or "").lower().startswith(PREFIJO_VENTANA)
            ]
        except Exception:
            ventanas = []

    if not ventanas:
        return None

    _ventana = ventanas[0]

    return _ventana


def _en_primer_plano(ventana):
    try:
        return (
            ctypes.windll.user32.GetForegroundWindow()
            == ventana._hWnd
        )
    except Exception:
        # Si no se puede comprobar, no bloquear el flujo.
        return True


def preparar_ventana():
    """
    Busca e-Sword y la deja al frente. NO se rinde a la primera:
    reintenta (e-Sword puede estar abierta pero minimizada, cargando,
    o Windows puede negar el cambio de foco una vez).

    Devuelve la ventana lista, o None si de verdad no se pudo.
    Es la que usan tanto buscar() como el clic de versiones.
    """

    global _ventana

    for intento in range(REINTENTOS_VENTANA):

        ventana = obtener_ventana()

        if ventana is None:
            time.sleep(ESPERA_SIN_VENTANA)
            continue

        try:
            if ventana.isMinimized:
                ventana.restore()
                time.sleep(0.05)
        except Exception:
            # La ventana se cerró o cambió: buscarla de nuevo.
            _ventana = None
            continue

        try:
            ventana.activate()
        except Exception:
            pass

        try:
            ctypes.windll.user32.SetForegroundWindow(
                ventana._hWnd
            )
        except Exception:
            pass

        time.sleep(0.10)

        if _en_primer_plano(ventana):
            return ventana

    print("❌ No se pudo encontrar / poner al frente e-Sword")
    return None


def buscar(referencia, mostrar_obs=False):

    global _ventana

    try:

        # =====================================
        # 1. OBS (Ctrl + Shift + F11)
        # =====================================

        if mostrar_obs:

            print("📺 Hotkey OBS → Biblia")

            mostrar_biblia()

            time.sleep(0.10)

        # =====================================
        # 2. ENCONTRAR Y ACTIVAR e-SWORD
        #    (con reintentos; si no hay ventana
        #    NO se teclea nada en otra aplicación)
        # =====================================

        ventana = preparar_ventana()

        if ventana is None:
            return False

        # =====================================
        # 3. CTRL + L (comando de e-Sword)
        # =====================================

        print("📖 Abriendo búsqueda e-Sword")

        pyautogui.keyDown("ctrl")

        try:
            time.sleep(0.02)
            pyautogui.press("l")
            time.sleep(0.02)
        finally:
            pyautogui.keyUp("ctrl")

        time.sleep(0.05)

        # =====================================
        # 4. ESCRIBIR CITA
        #    (solo si e-Sword sigue al frente)
        # =====================================

        if not _en_primer_plano(ventana):
            print("⚠️ e-Sword perdió el foco, no se escribe la cita")
            return False

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
