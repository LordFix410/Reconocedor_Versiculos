import time

from biblia.detector import (
    detectar_referencia,
    contiene_libro,
)
from biblia.normalizador import normalizar_palabras
from biblia.numeros import convertir_numero


PALABRAS_VERSICULO = {
    "versiculo",
    "versiculos",
    "verso",
    "versos",
}

COMANDOS_BIBLIA = {
    "vamonos",
    "vayamonos",
    "miremos",
    "veamos",
    "busquemos",
    "poneme",
    "pongame",
    "vamos",
}

COMANDOS_PRESENTACION = {
    "miramos aqui",
    "vemos aqui",
    "diapositiva",
    "diapositivas",
    "presentacion",
    "positiva"
}


class Centinela:

    def __init__(self, max_palabras=30):

        self.max_palabras = max_palabras
        self.buffer = []

        self.mostrar_proxima_cita = False
        self.evento_ejecutado_en_parcial = None
        self.ultimo_evento = None
        self.tiempo_ultimo_evento = 0.0
        self.bloqueo_duplicado = 2.0
        self.evento_ejecutado_en_parcial = None

        self.libro_actual = None
        self.capitulo_actual = None
        self.tiempo_capitulo = 0.0
        self.ventana_correccion = 3.0

    # ==========================================
    # DUPLICADOS
    # ==========================================

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

    # ==========================================
    # PARCIALES VOSK
    # ==========================================

    def procesar_parcial(self, texto):

        palabras = normalizar_palabras(texto)

        if not palabras:
            return None

        
        # =====================================
        # VERSÍCULO EXPLÍCITO RÁPIDO
        # "versiculo ocho"
        # =====================================

        for i, palabra in enumerate(palabras):

            if palabra not in PALABRAS_VERSICULO:
                continue

            posicion = i + 1

            # Permitir:
            # "versiculo numero ocho"
            while (
                posicion < len(palabras)
                and palabras[posicion] == "numero"
            ):
                posicion += 1

            numero, _ = convertir_numero(
                palabras[posicion:]
            )

            if numero is None:
                continue

            evento = (
                "VERSICULO",
                numero,
            )

            if self._es_duplicado(evento):
                return None

            mostrar_obs = any(
                p in COMANDOS_BIBLIA
                for p in palabras
            )

            return {
                "tipo": "VERSICULO",
                "versiculo": numero,
                "mostrar_obs": mostrar_obs,
            }
        # Para referencias completas en parciales,
        # exigimos comando de Biblia.
        tiene_comando = any(
            p in COMANDOS_BIBLIA
            for p in palabras
        )

        referencia = detectar_referencia(texto)

        if referencia is None:
            return None

        # No ejecutar capítulo incompleto
        # desde un parcial.
        if referencia["versiculo"] is None:
            return None

        libro = referencia["libro"]
        capitulo = referencia["capitulo"]
        versiculo = referencia["versiculo"]

        # IMPORTANTE:
        # mostrar_obs NO forma parte de la firma
        # anti-duplicados.
        # ¿La frase contiene un comando real para mostrar Biblia?
        tiene_comando = any(
            p in COMANDOS_BIBLIA
            for p in palabras
        )

        evento = (
            "REFERENCIA",
            libro,
            capitulo,
            versiculo,
        )

        # Si esta misma referencia YA fue ejecutada
        # durante este bloque de parciales Vosk,
        # no volver a ejecutarla aunque pasen 2, 10
        # o 30 segundos.
        if evento == self.evento_ejecutado_en_parcial:
            return None

        if self._es_duplicado(evento):
            return None

        # Recordar durante TODO este bloque Vosk
        self.evento_ejecutado_en_parcial = evento
        self.libro_actual = libro
        self.capitulo_actual = capitulo
        self.tiempo_capitulo = time.monotonic()

        # IMPORTANTE:
        # si hubo comando -> OBS
        # si no hubo comando -> solo e-Sword
        return {
            "tipo": "REFERENCIA",
            "libro": libro,
            "capitulo": capitulo,
            "versiculo": versiculo,
            "mostrar_obs": tiene_comando,
        }

    # ==========================================
    # RESULTADOS FINALES VOSK
    # ==========================================

    def procesar(self, texto):

        palabras_nuevas = normalizar_palabras(
            texto
        )

        if not palabras_nuevas:
            return None

        # --------------------------------------
        # PRESENTACIÓN
        # --------------------------------------

        if any(
            p in COMANDOS_PRESENTACION
            for p in palabras_nuevas
        ):

            self.mostrar_proxima_cita = False
            self.buffer.clear()

            return {
                "tipo": "PRESENTACION"
            }

        # --------------------------------------
        # COMANDO BIBLIA
        # --------------------------------------

        if any(
            p in COMANDOS_BIBLIA
            for p in palabras_nuevas
        ):
            self.mostrar_proxima_cita = True

        # --------------------------------------
        # BUFFER
        # --------------------------------------

        self.buffer.extend(
            palabras_nuevas
        )

        self.buffer = self.buffer[
            -self.max_palabras:
        ]

        contexto = " ".join(
            self.buffer
        )

        # ======================================
        # 1. REFERENCIA COMPLETA / CAPÍTULO
        # ======================================

        referencia = detectar_referencia(
            contexto
        )

        if referencia is not None:

            libro = referencia["libro"]
            capitulo = referencia["capitulo"]
            versiculo = referencia["versiculo"]

            mostrar = self.mostrar_proxima_cita

            # Guardamos siempre el capítulo,
            # incluso si el parcial ya ejecutó la cita.
            self.libro_actual = libro
            self.capitulo_actual = capitulo
            self.tiempo_capitulo = time.monotonic()

            if versiculo is None:

                evento = (
                    "CAPITULO",
                    libro,
                    capitulo,
                )

                resultado = {
                    "tipo": "CAPITULO",
                    "libro": libro,
                    "capitulo": capitulo,
                    "mostrar_obs": mostrar,
                }

            else:

                evento = (
                    "REFERENCIA",
                    libro,
                    capitulo,
                    versiculo,
                )

                resultado = {
                    "tipo": "REFERENCIA",
                    "libro": libro,
                    "capitulo": capitulo,
                    "versiculo": versiculo,
                    "mostrar_obs": mostrar,
                }

            self.buffer.clear()
            self.mostrar_proxima_cita = False

            # Si este mismo evento YA se ejecutó
            # durante los parciales de este bloque,
            # el resultado final NO debe repetirlo.
            if evento == self.evento_ejecutado_en_parcial:
                self.evento_ejecutado_en_parcial = None
                return None

            # Cerramos el bloque parcial anterior.
            self.evento_ejecutado_en_parcial = None

            if self._es_duplicado(evento):
                return None

            return resultado

        # ======================================
        # 2. CORRECCIÓN RÁPIDA
        # "Isaias uno" → "uno dieciocho"
        # ======================================

        if (
            self.capitulo_actual is not None
            and
            time.monotonic() - self.tiempo_capitulo
            <= self.ventana_correccion
        ):

            numero1, usadas1 = convertir_numero(
                palabras_nuevas
            )

            if (
                numero1 == self.capitulo_actual
                and usadas1 > 0
            ):

                numero2, _ = convertir_numero(
                    palabras_nuevas[usadas1:]
                )

                if numero2 is not None:

                    evento = (
                        "VERSICULO",
                        numero2,
                    )

                    if self._es_duplicado(evento):
                        return None

                    mostrar = (
                        self.mostrar_proxima_cita
                    )

                    self.mostrar_proxima_cita = False
                    self.buffer.clear()

                    return {
                        "tipo": "VERSICULO",
                        "versiculo": numero2,
                        "mostrar_obs": mostrar,
                    }

        # ======================================
        # 3. "VERSICULO 18"
        # ======================================

        for i, palabra in enumerate(
            palabras_nuevas
        ):

            if palabra not in PALABRAS_VERSICULO:
                continue

            posicion = i + 1

            # "versiculo numero dieciocho"
            while (
                posicion < len(palabras_nuevas)
                and palabras_nuevas[posicion]
                == "numero"
            ):
                posicion += 1

            numero, _ = convertir_numero(
                palabras_nuevas[posicion:]
            )

            if numero is None:
                continue

            evento = (
                "VERSICULO",
                numero,
            )

            if self._es_duplicado(evento):
                return None

            mostrar = self.mostrar_proxima_cita

            self.mostrar_proxima_cita = False
            self.buffer.clear()

            return {
                "tipo": "VERSICULO",
                "versiculo": numero,
                "mostrar_obs": mostrar,
            }

        # ======================================
        # 4. "MIREMOS EL 18"
        # ======================================

        if (
            self.mostrar_proxima_cita
            and not contiene_libro(contexto)
        ):

            for i in range(
                len(palabras_nuevas)
            ):

                numero, _ = convertir_numero(
                    palabras_nuevas[i:]
                )

                if numero is None:
                    continue

                evento = (
                    "VERSICULO",
                    numero,
                )

                if self._es_duplicado(evento):
                    return None

                self.mostrar_proxima_cita = False
                self.buffer.clear()

                return {
                    "tipo": "VERSICULO",
                    "versiculo": numero,
                    "mostrar_obs": True,
                }

        return None