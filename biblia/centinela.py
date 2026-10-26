import time

from biblia.detector import (
    detectar_referencia,
    contiene_libro,
)
from biblia.normalizador import normalizar_palabras
from biblia.numeros import (
    convertir_numero, DECENAS, CENTENAS, CIEN_EXACTO
)


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
}

# "positiva" es como Vosk suele oír "diapositiva", pero también existe
# "una actitud positiva". Solo cuenta si es TODO lo que se dijo.
COMANDOS_PRESENTACION_SOLOS = {
    "positiva",
}

# El comando de presentación se dice corto. Si la frase es larga
# ("...y la representación de la diapositiva que...") se ignora.
MAX_PALABRAS_PRESENTACION = 6

VENTANA_COMANDO = 8.0       # seg que el comando "veamos" sigue vigente
VENTANA_VERSICULO = 20.0    # seg para ignorar el mismo versículo repetido
PALABRAS_CERCA = 10         # el comando debe estar en las últimas N palabras
TTL_BUFFER = 10.0           # seg que una palabra vive en el buffer

# ------------------------------------------------------------
# PALABRAS AMBIGUAS: nombres de libro que también son palabras
# o nombres comunes en una prédica ("vamos a cantar dos canciones",
# "Marcos tres veces dijo").
#
#  - ESTRICTAS: solo cuentan si el predicador dijo "capítulo" o
#    hay un comando de Biblia vigente ("veamos...", "miremos...").
#  - NOMBRES: igual, pero SOLO cuando no traen versículo.
#    "Marcos tres dieciseis" sí pasa; "Marcos tres veces" no.
#
# Las claves son la palabra tal como se dijo (como en libros.py).
# ------------------------------------------------------------
CLAVES_ESTRICTAS = {
    "hecho", "cantar", "numeros", "amos",
    "revelacion", "revelaciones", "vivencias",
}

CLAVES_NOMBRES = {
    "marcos", "lucas", "mateo", "daniel", "santiago", "tito",
    "rut", "judas", "ester", "job", "joel", "jonas",
}

# Números que pueden seguir creciendo mientras Vosk aún habla
# ("treinta" -> "treinta y cinco").
# ('cien' ya no puede crecer: 101 es 'ciento uno')
NUMEROS_INCOMPLETOS = (
    set(DECENAS) | (set(CENTENAS) - CIEN_EXACTO) | {"veinte"}
)

# Números que pueden seguir tras una "y" colgando
# ("treinta y ...", "diez y seis").
NUMEROS_ESPERAN_Y = NUMEROS_INCOMPLETOS | {"diez"}


def _contiene_frase(palabras, frase):
    """True si la lista de palabras contiene la frase completa
    (por palabras, no por subcadena)."""
    n = len(frase)
    return any(
        palabras[i:i + n] == frase
        for i in range(len(palabras) - n + 1)
    )


def _termina_incompleto(palabras):
    """
    True si el parcial acaba en un número que aún puede crecer:
    "... treinta"  o  "... treinta y"  (Vosk emite ese 'y' colgando).
    """
    if not palabras:
        return False

    if palabras[-1] in NUMEROS_INCOMPLETOS:
        return True

    return (
        palabras[-1] == "y"
        and len(palabras) > 1
        and palabras[-2] in NUMEROS_ESPERAN_Y
    )


class Centinela:

    def __init__(self, max_palabras=30):

        self.max_palabras = max_palabras
        # Lista de (palabra, momento_en_que_llegó)
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
    # FIN DE FRASE (final vacío de Vosk)
    # ==========================================

    def fin_de_frase(self):
        """
        Vosk cerró la frase sin texto: ya no tiene sentido
        recordar qué se ejecutó en el parcial.
        """
        self.evento_ejecutado_en_parcial = None

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

    def _referencia_valida(self, ref):
        """
        Filtra libros ambiguos: ver CLAVES_ESTRICTAS / CLAVES_NOMBRES.
        """
        clave = ref.get("clave_libro")

        if clave in CLAVES_ESTRICTAS:
            exigir = True
        elif clave in CLAVES_NOMBRES and ref["versiculo"] is None:
            exigir = True
        else:
            return True

        return bool(ref.get("con_capitulo")) or self._comando_activo()

    def _numero_incompleto(self, palabras, inicio, usadas):
        """
        True si el parcial termina justo en un número
        que todavía puede crecer:
          "treinta"   -> "treinta y cinco"
          "treinta y" -> "treinta y cinco"   (la 'y' colgando)
        En ese caso esperamos al resultado final.
        """
        fin = inicio + usadas
        resto = palabras[fin:]

        # Si después del número vienen otras palabras, ya terminó.
        if resto and resto != ["y"]:
            return False

        ultima = palabras[fin - 1]

        if resto == ["y"]:
            return ultima in NUMEROS_ESPERAN_Y

        return ultima in NUMEROS_INCOMPLETOS

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
        # Se recorre de atrás hacia adelante: manda el
        # ÚLTIMO "versiculo N" dicho en la frase.
        # =====================================

        for i in range(len(palabras) - 1, -1, -1):

            if palabras[i] not in PALABRAS_VERSICULO:
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

        if not self._referencia_valida(referencia):
            return None

        if referencia["versiculo"] is None:
            return None

        libro = referencia["libro"]
        capitulo = referencia["capitulo"]
        versiculo = referencia["versiculo"]

        # Esperar si el número final aún puede crecer
        # ("treinta" o "treinta y").
        if _termina_incompleto(palabras):
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

        # Guardar lo que ejecutó el parcial y limpiarlo SIEMPRE:
        # un final cierra la frase, pase lo que pase después.
        ejecutado = self.evento_ejecutado_en_parcial
        self.evento_ejecutado_en_parcial = None

        palabras_nuevas = normalizar_palabras(texto)

        if not palabras_nuevas:
            return None

        # --------------------------------------
        # PRESENTACIÓN
        # (por palabras completas, no por subcadena, y solo
        # en frases cortas: el comando se dice solo)
        # --------------------------------------

        es_presentacion = False

        if len(palabras_nuevas) <= MAX_PALABRAS_PRESENTACION:
            es_presentacion = any(
                _contiene_frase(palabras_nuevas, c.split())
                for c in COMANDOS_PRESENTACION
            )

        if not es_presentacion:
            es_presentacion = (
                len(palabras_nuevas) == 1
                and palabras_nuevas[0] in COMANDOS_PRESENTACION_SOLOS
            )

        if es_presentacion:
            self.comando_hasta = 0.0
            self.buffer.clear()

            return {"tipo": "PRESENTACION"}

        # --------------------------------------
        # COMANDO BIBLIA
        # --------------------------------------

        if self._hay_comando_cerca(palabras_nuevas):
            self._armar_comando()

        # --------------------------------------
        # BUFFER (las palabras viejas caducan)
        # --------------------------------------

        ahora = time.monotonic()

        self.buffer = [
            (p, t) for p, t in self.buffer
            if ahora - t <= TTL_BUFFER
        ]
        self.buffer.extend((p, ahora) for p in palabras_nuevas)
        self.buffer = self.buffer[-self.max_palabras:]

        contexto = " ".join(p for p, _ in self.buffer)

        # ======================================
        # 1. REFERENCIA COMPLETA / CAPÍTULO
        # ======================================

        referencia = detectar_referencia(contexto)

        if (
            referencia is not None
            and not self._referencia_valida(referencia)
        ):
            referencia = None

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

            # Ya ejecutado por el parcial: no repetir.
            if evento == ejecutado:
                self.comando_hasta = 0.0
                return None

            if self._es_duplicado(evento):
                return None

            if versiculo is None:
                # e-Sword vuelve al inicio del capítulo: el versículo
                # anterior ya no cuenta como "repetido".
                self.ultimo_versiculo = None
            else:
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
        # (de atrás hacia adelante: manda el último)
        # ======================================

        for i in range(len(palabras_nuevas) - 1, -1, -1):

            if palabras_nuevas[i] not in PALABRAS_VERSICULO:
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
