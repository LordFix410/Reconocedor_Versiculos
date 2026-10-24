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
        self.cola = queue.Queue(maxsize=300)

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

    def callback(self, indata, frames, time_info, status):
        # OJO: el parámetro se llama time_info para no tapar
        # al módulo `time` que se importa arriba.

        if status:
            # Overflow / underflow de audio: antes pasaba en silencio.
            print("⚠️ Audio:", status)

        try:
            self.cola.put_nowait(bytes(indata))

        except queue.Full:

            try:
                self.cola.get_nowait()
                self.cola.put_nowait(bytes(indata))

            except queue.Empty:
                pass

    def _seguro(self, nombre, funcion, *args, **kwargs):
        """
        Ejecuta una acción sin dejar que un error (clic fallido,
        e-Sword cerrado, FailSafe del mouse...) mate la escucha.
        """
        try:
            return funcion(*args, **kwargs)

        except Exception as e:
            print(f"❌ Error en {nombre}:", repr(e))
            return None

    def escuchar(self):

        print("🎤 Escuchando...")

        with sd.RawInputStream(
            samplerate=self.samplerate,
            blocksize=2000,
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

                        self._seguro(
                            "controlador",
                            self.controlador.procesar,
                            texto
                        )
                        self._seguro(
                            "versiones",
                            self.versiones.procesar,
                            texto,
                            final=True
                        )

                    else:

                        # Final vacío: cerrar la frase igual, para que
                        # no queden eventos del parcial "pegados".
                        self._seguro(
                            "fin de frase",
                            self.controlador.fin_de_frase
                        )
                        self._seguro(
                            "versiones",
                            self.versiones.procesar,
                            "",
                            final=True
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

                    if (
                        texto
                        and texto != self.ultimo_parcial
                    ):
                        print("⚡ PARCIAL:", texto)

                        self.ultimo_parcial = texto

                        # IMPORTANTE:
                        # Procesamos parciales para
                        # conseguir baja latencia.
                        self._seguro(
                            "controlador (parcial)",
                            self.controlador.procesar_parcial,
                            texto
                        )
                        self._seguro(
                            "versiones (parcial)",
                            self.versiones.procesar,
                            texto
                        )
