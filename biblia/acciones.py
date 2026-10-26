"""
Cola de acciones físicas (teclado, ratón, OBS, e-Sword).

Antes, voz.py esperaba a que e-Sword terminara cada búsqueda
(sleeps, reintentos de ventana) y mientras tanto no leía el audio
de Vosk. Ahora las acciones se ejecutan en un hilo aparte, EN ORDEN
(no se descarta ninguna: si un capítulo se saltara, el versículo
siguiente caería en el capítulo equivocado), y la escucha sigue libre.

Como todas pasan por el mismo hilo, nunca se pisan entre sí
(por ejemplo un clic de versión en medio de un Ctrl+L).
"""

import queue
import threading
import time


# Muestra cuánto tardó cada acción (en cola + ejecución).
# Útil para saber dónde se va el tiempo. Ponlo en False para silenciar.
MOSTRAR_TIEMPOS = True


class Trabajador:

    def __init__(self):

        self._cola = queue.Queue()

        self._hilo = threading.Thread(
            target=self._bucle,
            name="acciones-biblia",
            daemon=True,
        )
        self._hilo.start()

    def enviar(self, nombre, funcion, *args, **kwargs):
        self._cola.put(
            (nombre, funcion, args, kwargs, time.monotonic())
        )

    def _bucle(self):

        while True:

            nombre, funcion, args, kwargs, t_envio = self._cola.get()

            inicio = time.monotonic()

            try:
                funcion(*args, **kwargs)

            except Exception as e:
                print(f"❌ Error en acción '{nombre}':", repr(e))

            fin = time.monotonic()

            if MOSTRAR_TIEMPOS:
                print(
                    f"⏱️ {nombre}: "
                    f"{(inicio - t_envio) * 1000:.0f} ms en cola + "
                    f"{(fin - inicio) * 1000:.0f} ms"
                )


_trabajador = Trabajador()


def enviar(nombre, funcion, *args, **kwargs):
    """Encola una acción para el hilo de acciones."""
    _trabajador.enviar(nombre, funcion, *args, **kwargs)
