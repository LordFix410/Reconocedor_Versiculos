import time


class PruebaCentinela:

    def __init__(self):
        self.evento_ejecutado_en_parcial = None

        self.ultimo_evento = None
        self.tiempo_ultimo_evento = 0.0
        self.bloqueo_duplicado = 2.0

    def _es_duplicado(self, evento):

        ahora = time.monotonic()

        if (
            evento == self.ultimo_evento
            and
            ahora - self.tiempo_ultimo_evento
            < self.bloqueo_duplicado
        ):
            return True

        self.ultimo_evento = evento
        self.tiempo_ultimo_evento = ahora

        return False

    def parcial(self, evento):

        # NUEVA PROTECCIÓN
        if evento == self.evento_ejecutado_en_parcial:
            print("🚫 IGNORADO:", evento)
            return

        if self._es_duplicado(evento):
            print("⏱️ IGNORADO POR TIEMPO:", evento)
            return

        self.evento_ejecutado_en_parcial = evento

        print("✅ EJECUTAR:", evento)

    def final(self, evento):

        # El FINAL pertenece al mismo bloque Vosk.
        if evento == self.evento_ejecutado_en_parcial:
            print("🚫 FINAL IGNORADO:", evento)

            # Cerramos el bloque
            self.evento_ejecutado_en_parcial = None
            return

        self.evento_ejecutado_en_parcial = None

        if self._es_duplicado(evento):
            print("⏱️ FINAL IGNORADO POR TIEMPO:", evento)
            return

        print("✅ FINAL EJECUTAR:", evento)


centinela = PruebaCentinela()

evento = (
    "REFERENCIA",
    "2 Pedro",
    1,
    5
)

print("\n===== MISMO BLOQUE DURANTE 10 SEGUNDOS =====\n")

for segundo in range(10):

    print(f"Segundo {segundo}: ", end="")
    centinela.parcial(evento)

    time.sleep(1)


print("\n===== LLEGA EL RESULTADO FINAL =====\n")

centinela.final(evento)


print("\n===== NUEVO BLOQUE VOSK =====\n")

# Esperamos para simular que después el predicador
# realmente vuelve a mencionar 2 Pedro 1:5.
time.sleep(3)

centinela.parcial(evento)