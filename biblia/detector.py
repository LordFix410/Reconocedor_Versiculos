from biblia.libros import LIBROS
from biblia.normalizador import normalizar_palabras
from biblia.numeros import convertir_numero


ANTES_CAPITULO = {
    "capitulo",
    "capitulos",
    "numero",
    "en",
    "su",
}

ANTES_VERSICULO = {
    "versiculo",
    "versiculos",
    "verso",
    "versos",
    "numero",
    "en",
    "su",
    "y",
}


def _saltar(palabras, posicion, permitidas):

    while (
        posicion < len(palabras)
        and palabras[posicion] in permitidas
    ):
        posicion += 1

    return posicion


def contiene_libro(texto):

    palabras = normalizar_palabras(texto)

    for i in range(len(palabras)):

        for cantidad in (2, 1):

            candidato = " ".join(
                palabras[i:i + cantidad]
            )

            if candidato in LIBROS:
                return True

    return False


def detectar_referencia(texto):

    palabras = normalizar_palabras(texto)

    # Preferir el libro mencionado más recientemente.
    for i in range(len(palabras) - 1, -1, -1):

        libro = None
        longitud_libro = 0

        for cantidad in (2, 1):

            if i + cantidad > len(palabras):
                continue

            candidato = " ".join(
                palabras[i:i + cantidad]
            )

            if candidato in LIBROS:

                libro = LIBROS[candidato]
                longitud_libro = cantidad
                break

        if libro is None:
            continue

        posicion = i + longitud_libro

        # -------------------------
        # CAPÍTULO
        # -------------------------

        posicion = _saltar(
            palabras,
            posicion,
            ANTES_CAPITULO
        )

        capitulo, usadas = convertir_numero(
            palabras[posicion:]
        )

        if capitulo is None:
            continue

        posicion += usadas

        # -------------------------
        # VERSÍCULO
        # -------------------------

        posicion = _saltar(
            palabras,
            posicion,
            ANTES_VERSICULO
        )

        versiculo, usadas = convertir_numero(
            palabras[posicion:]
        )

        if versiculo is None:

            return {
                "libro": libro,
                "capitulo": capitulo,
                "versiculo": None,
            }

        posicion += usadas

        # Corrección natural:
        #
        # "Isaias uno ... uno dieciocho"
        # puede terminar como 1:18.
        posicion_extra = _saltar(
            palabras,
            posicion,
            ANTES_VERSICULO
        )

        extra, _ = convertir_numero(
            palabras[posicion_extra:]
        )

        if (
            extra is not None
            and versiculo == capitulo
        ):
            versiculo = extra

        return {
            "libro": libro,
            "capitulo": capitulo,
            "versiculo": versiculo,
        }

    return None