import time

from biblia.detector import (
    detectar_referencia,
    contiene_libro,
)
from biblia.normalizador import normalizar_palabras
from biblia.numeros import convertir_numero, DECENAS, CENTENAS


PALABRAS_VERSICULO = {
    "versiculo",
    "versiculos",
    "verso",
    "versos"
}

# Quité "vamos": es demasiado común al hablar normal.
COMANDOS_BIBLIA = {
    "vamonos",
    "vayamonos",
    "miremos",
    "veamos",
    "busquemos",
    "poneme",
    "pongame"
}

COMANDOS_PRESENTACION = {
    "miramos aqui",
    "vemos aqui",
    "diapositiva",
    "diapositivas",
    "presentacion",
    "positiva"
}

VENTANA_COMANDO = 8.0       # seg que el comando "veamos" sigue vigente
VENTANA_VERSICULO = 20.0    # seg para ignorar el mismo versículo repetido
PALABRAS_CERCA = 10         # el comando debe estar en las últimas N palabras

# Números que pueden seguir creciendo mientras Vosk aún habla
# ("treinta" -> "treinta y cinco").
NUMEROS_INCOMPLETOS = set(DECENAS) | set(CENTENAS) | {"veinte"}


class Centinela:

    def __init__(self, max_palabras=30):

        self.max_palabras = max_palabras
        self.buffer = []

        self.comando_hasta = 0.0
        self.evento_ejecutado_en_parcial = None
        self.ultimo_evento = None
        self.tiempo_ultimo_evento = 0.0
        self.bloqueo_duplicado = 2.0

        self.ultimo_versiculo = None
        self.tiempo_versiculo = 0.0

        self.libro_actual = None
        self.capitulo_actual = None
        self.tiempo_capitulo = 0.0
        self.ventana_correccion = 3.0

    # ==========================================
    # COMANDO DE BIBLIA (con caducidad)
    # ==========================================

    def _armar_comando(self):
        self.comando_hasta = time.monotonic() + VENTANA_COMANDO

    def _comando_activo(self):
        return time.monotonic() < self.comando_hasta

    def _consumir_comando(self):
        activo = self._comando_activo()
        self.comando_hasta = 0.0
        return activo

    def _hay_comando_cerca(self, palabras):
        return any(
            p in COMANDOS_BIBLIA
            for p in palabras[-PALABRAS_CERCA:]
        )

    # ==========================================
    # DUPLICADOS
    # ==========================================

    def _es_duplicado(self, evento):

        ahora = time.monotonic()

        if (
            evento == self.ultimo_evento
            and ahora - self.tiempo_ultimo_evento
            < self.bloqueo_duplicado
        ):
            return True

        self.ultimo_evento = evento
        self.tiempo_ultimo_evento = ahora

        return False

    def _versiculo_repetido(self, numero):
        """
        Ignora el mismo versículo repetido durante 20 s
        (se extiende mientras lo sigan repitiendo).
        """
        ahora = time.monotonic()

        if (
            numero == self.ultimo_versiculo
            and ahora - self.tiempo_versiculo
            < VENTANA_VERSICULO
        ):
            self.tiempo_versiculo = ahora
            return True

        self.ultimo_versiculo = numero
        self.tiempo_versiculo = ahora
        return False

    def _nuevo_capitulo(self, libro, capitulo):
        # Solo reiniciar si de verdad es otro capítulo
        if (libro, capitulo) != (self.libro_actual, self.capitulo_actual):
            self.ultimo_versiculo = None

        self.libro_actual = libro
        self.capitulo_actual = capitulo
        self.tiempo_capitulo = time.monotonic()
        
    def _numero_incompleto(self, palabras, inicio, usadas):
        """
        True si el parcial termina justo en un número
        que todavía puede crecer ("treinta" -> "treinta y cinco").
        En ese caso esperamos al resultado final.
        """
        if inicio + usadas < len(palabras):
            return False

        return palabras[inicio + usadas - 1] in NUMEROS_INCOMPLETOS

    # ==========================================
    # PARCIALES VOSK
    # ==========================================

    def procesar_parcial(self, texto):

        palabras = normalizar_palabras(texto)

        if not palabras:
            return None

        # Armar comando solo si está cerca del final del parcial.
        if self._hay_comando_cerca(palabras):
            self._armar_comando()

        # =====================================
        # "versiculo ocho"
        # =====================================

        for i, palabra in enumerate(palabras):

            if palabra not in PALABRAS_VERSICULO:
                continue

            posicion = i + 1

            while (
                posicion < len(palabras)
                and palabras[posicion] == "numero"
            ):
                posicion += 1

            numero, usadas = convertir_numero(
                palabras[posicion:]
            )

            if numero is None:
                continue

            if self._numero_incompleto(
                palabras, posicion, usadas
            ):
                return None

            # ¿Ya dijo libro + capítulo en esta misma frase?
            # "lucas once ... y empieza el versiculo dos"
            ref = detectar_referencia(texto)

            if ref is not None:

                evento = (
                    "REFERENCIA",
                    ref["libro"],
                    ref["capitulo"],
                    numero,
                )

                if evento == self.evento_ejecutado_en_parcial:
                    return None

                if self._es_duplicado(evento):
                    return None

                self.evento_ejecutado_en_parcial = evento
                self._nuevo_capitulo(
                    ref["libro"], ref["capitulo"]
                )
                self.ultimo_versiculo = numero
                self.tiempo_versiculo = time.monotonic()

                return {
                    "tipo": "REFERENCIA",
                    "libro": ref["libro"],
                    "capitulo": ref["capitulo"],
                    "versiculo": numero,
                    "mostrar_obs": self._consumir_comando(),
                }

            # Solo versículo
            evento = ("VERSICULO", numero)

            if evento == self.evento_ejecutado_en_parcial:
                return None

            if self._versiculo_repetido(numero):
                return None

            self.evento_ejecutado_en_parcial = evento

            return {
                "tipo": "VERSICULO",
                "versiculo": numero,
                "mostrar_obs": self._consumir_comando(),
            }

        # =====================================
        # REFERENCIA COMPLETA ("juan tres dieciseis")
        # =====================================

        referencia = detectar_referencia(texto)

        if referencia is None:
            return None

        if referencia["versiculo"] is None:
            return None

        libro = referencia["libro"]
        capitulo = referencia["capitulo"]
        versiculo = referencia["versiculo"]

        # Esperar si el número final aún puede crecer.
        if palabras[-1] in NUMEROS_INCOMPLETOS:
            return None

        evento = (
            "REFERENCIA",
            libro,
            capitulo,
            versiculo,
        )

        if evento == self.evento_ejecutado_en_parcial:
            return None

        if self._es_duplicado(evento):
            return None

        self.evento_ejecutado_en_parcial = evento
        self._nuevo_capitulo(libro, capitulo)
        self.ultimo_versiculo = versiculo
        self.tiempo_versiculo = time.monotonic()

        return {
            "tipo": "REFERENCIA",
            "libro": libro,
            "capitulo": capitulo,
            "versiculo": versiculo,
            "mostrar_obs": self._consumir_comando(),
        }

    # ==========================================
    # RESULTADOS FINALES VOSK
    # ==========================================

    def procesar(self, texto):

        palabras_nuevas = normalizar_palabras(texto)

        if not palabras_nuevas:
            return None

        # --------------------------------------
        # PRESENTACIÓN
        # --------------------------------------
        texto_norm = " ".join(palabras_nuevas)
        if any(
            c in texto_norm
            for c in COMANDOS_PRESENTACION
        ):
            self.comando_hasta = 0.0
            self.buffer.clear()
            self.evento_ejecutado_en_parcial = None

            return {"tipo": "PRESENTACION"}

        # --------------------------------------
        # COMANDO BIBLIA
        # --------------------------------------

        if self._hay_comando_cerca(palabras_nuevas):
            self._armar_comando()

        # --------------------------------------
        # BUFFER
        # --------------------------------------

        self.buffer.extend(palabras_nuevas)
        self.buffer = self.buffer[-self.max_palabras:]

        contexto = " ".join(self.buffer)

        ejecutado = self.evento_ejecutado_en_parcial

        # ======================================
        # 1. REFERENCIA COMPLETA / CAPÍTULO
        # ======================================

        referencia = detectar_referencia(contexto)

        if referencia is not None:

            libro = referencia["libro"]
            capitulo = referencia["capitulo"]
            versiculo = referencia["versiculo"]

            self._nuevo_capitulo(libro, capitulo)

            # El parcial ya mandó libro+capítulo+versículo:
            # el final de solo "capítulo" no debe pisarlo.
            if (
                versiculo is None
                and ejecutado is not None
                and ejecutado[0] == "REFERENCIA"
                and ejecutado[1] == libro
                and ejecutado[2] == capitulo
            ):
                self.evento_ejecutado_en_parcial = None
                self.comando_hasta = 0.0
                self.buffer.clear()
                return None

            if versiculo is None:
                evento = ("CAPITULO", libro, capitulo)
                resultado = {
                    "tipo": "CAPITULO",
                    "libro": libro,
                    "capitulo": capitulo,
                }
            else:
                evento = (
                    "REFERENCIA", libro, capitulo, versiculo
                )
                resultado = {
                    "tipo": "REFERENCIA",
                    "libro": libro,
                    "capitulo": capitulo,
                    "versiculo": versiculo,
                }

            self.buffer.clear()
            self.evento_ejecutado_en_parcial = None

            # Ya ejecutado por el parcial: no repetir.
            if evento == ejecutado:
                self.comando_hasta = 0.0
                return None

            if self._es_duplicado(evento):
                return None

            if versiculo is not None:
                self.ultimo_versiculo = versiculo
                self.tiempo_versiculo = time.monotonic()

            resultado["mostrar_obs"] = self._consumir_comando()
            return resultado

        # ======================================
        # 2. CORRECCIÓN RÁPIDA
        # "Isaias uno" -> "uno dieciocho"
        # ======================================

        if (
            self.capitulo_actual is not None
            and time.monotonic() - self.tiempo_capitulo
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

                    self.evento_ejecutado_en_parcial = None

                    if self._versiculo_repetido(numero2):
                        return None

                    self.buffer.clear()

                    return {
                        "tipo": "VERSICULO",
                        "versiculo": numero2,
                        "mostrar_obs": self._consumir_comando(),
                    }

        # ======================================
        # 3. "VERSICULO 18"
        # ======================================

        for i, palabra in enumerate(palabras_nuevas):

            if palabra not in PALABRAS_VERSICULO:
                continue

            posicion = i + 1

            while (
                posicion < len(palabras_nuevas)
                and palabras_nuevas[posicion] == "numero"
            ):
                posicion += 1

            numero, _ = convertir_numero(
                palabras_nuevas[posicion:]
            )

            if numero is None:
                continue

            evento = ("VERSICULO", numero)

            self.buffer.clear()
            self.evento_ejecutado_en_parcial = None

            # Ya ejecutado en el parcial o repetido.
            if evento == ejecutado:
                self.comando_hasta = 0.0
                return None

            if self._versiculo_repetido(numero):
                return None

            return {
                "tipo": "VERSICULO",
                "versiculo": numero,
                "mostrar_obs": self._consumir_comando(),
            }

        # ======================================
        # 4. "MIREMOS EL 18"
        # Solo con comando vigente, sin libro, y el número
        # tiene que estar al inicio de la frase (no en
        # cualquier parte).
        # ======================================

        if (
            self._comando_activo()
            and not contiene_libro(" ".join(palabras_nuevas))
        ):

            for i in range(min(3, len(palabras_nuevas))):

                numero, _ = convertir_numero(
                    palabras_nuevas[i:]
                )

                if numero is None:
                    continue

                if self._versiculo_repetido(numero):
                    return None

                self.buffer.clear()

                return {
                    "tipo": "VERSICULO",
                    "versiculo": numero,
                    "mostrar_obs": self._consumir_comando(),
                }

        return None