import json
import queue
import sounddevice as sd
import os
import sys
import time
import subprocess

from vosk import Model, KaldiRecognizer
from biblia.controlador import Controlador
from biblia.versiones import ControladorVersiones


class BibliaVoz:

    def __init__(
        self,
        modelo,
        dispositivo=None,
        samplerate=16000
    ):
        self.cola = queue.Queue(maxsize=10)

        self.modelo = Model(modelo)

        self.reconocedor = KaldiRecognizer(
            self.modelo,
            samplerate
        )

        self.samplerate = samplerate
        self.dispositivo = dispositivo

        self.controlador = Controlador()
        self.versiones = ControladorVersiones()

        # Evita procesar el mismo parcial
        # repetidamente.
        self.ultimo_parcial = ""
        # Reinicio completo cada hora para liberar RAM
        self.tiempo_inicio = time.monotonic()
        self.intervalo_reinicio = 60 * 60

    def callback(self, indata, frames, time, status):

        try:
            self.cola.put_nowait(bytes(indata))

        except queue.Full:

            try:
                self.cola.get_nowait()
                self.cola.put_nowait(bytes(indata))

            except queue.Empty:
                pass

    def escuchar(self):

        print("🎤 Escuchando...")

        with sd.RawInputStream(
            samplerate=self.samplerate,
            blocksize=500,
            device=self.dispositivo,
            dtype="int16",
            channels=1,
            callback=self.callback,
        ):

            while True:

                datos = self.cola.get()

                # ==========================================
                # REINICIO AUTOMÁTICO CADA HORA
                # ==========================================

                if (
                    time.monotonic() - self.tiempo_inicio
                    >= self.intervalo_reinicio
                ):
                    print(
                        "\n♻️ Tiempo de reinicio alcanzado."
                        "\n♻️ Reiniciando para liberar memoria..."
                    )

                    if getattr(sys, "frozen", False):

                        # Cuando esté empaquetado como .exe
                        subprocess.Popen([
                            sys.executable,
                            *sys.argv[1:]
                        ])

                    else:

                        # Mientras ejecutamos con Python
                        subprocess.Popen([
                            sys.executable,
                            os.path.abspath(sys.argv[0]),
                            *sys.argv[1:]
                        ])

                    sys.exit(0)

                if self.reconocedor.AcceptWaveform(datos):

                    resultado = json.loads(
                        self.reconocedor.Result()
                    )

                    texto = resultado.get(
                        "text",
                        ""
                    ).strip()

                    if texto:

                        print(
                            "\n🎤",
                            texto
                        )

                        self.controlador.procesar(
                            texto
                        )
                        self.versiones.procesar(
                            texto
                        )

                    self.ultimo_parcial = ""

                else:

                    parcial = json.loads(
                        self.reconocedor.PartialResult()
                    )

                    texto = parcial.get(
                        "partial",
                        ""
                    ).strip()
                    if texto and texto != self.ultimo_parcial:
                        print("⚡ PARCIAL:", texto)

                    if (
                        texto
                        and texto != self.ultimo_parcial
                    ):
                        self.ultimo_parcial = texto

                        # IMPORTANTE:
                        # Procesamos parciales para
                        # conseguir baja latencia.
                        self.controlador.procesar_parcial(
                            texto
                        )
                        self.versiones.procesar(
                            texto
                        )