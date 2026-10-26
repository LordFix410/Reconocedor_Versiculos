from biblia.libros import LIBROS
from biblia.normalizador import normalizar_palabras
from biblia.numeros import convertir_numero


ANTES_CAPITULO = {
    "capitulo",
    "capitulos",
    "numero",
    "en",
    "su",
    # Cómo suele oír Vosk la palabra "capítulo":
    "capital",
    "capitul",
    "capitol",
    "capi",
    "cap",
}

# De las anteriores, las que de verdad significan "capítulo"
# (para saber si el predicador lo dijo explícitamente).
PALABRAS_CAPITULO = ANTES_CAPITULO - {"numero", "en", "su"}

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


def _libro_en(palabras, i):
    """
    Busca un libro que EMPIECE en la posición i, o que sea
    la palabra i precedida de su número.

    Devuelve (libro, inicio, longitud, clave) o None.
    `clave` es la palabra tal como se dijo (ej. "hecho", "cantar"),
    para poder tratar distinto las palabras ambiguas.

    Importante: "1 juan" / "2 timoteo" se prefieren sobre
    "juan" / "timoteo" sueltos. Como se recorre de atrás hacia
    adelante, al llegar a la palabra del libro hay que mirar
    una palabra atrás para ver si traía número.
    """

    # Dos palabras que empiezan aquí: "1 juan", "cantar cantares"
    if i + 2 <= len(palabras):

        candidato = " ".join(palabras[i:i + 2])

        if candidato in LIBROS:
            return LIBROS[candidato], i, 2, candidato

    # Una palabra
    if palabras[i] in LIBROS:

        if i > 0:

            previo = f"{palabras[i - 1]} {palabras[i]}"

            if previo in LIBROS:
                return LIBROS[previo], i - 1, 2, previo

        return LIBROS[palabras[i]], i, 1, palabras[i]

    return None


def detectar_referencia(texto):

    palabras = normalizar_palabras(texto)

    # Preferir el libro mencionado más recientemente.
    for i in range(len(palabras) - 1, -1, -1):

        encontrado = _libro_en(palabras, i)

        if encontrado is None:
            continue

        libro, inicio, longitud_libro, clave = encontrado

        posicion = inicio + longitud_libro

        # -------------------------
        # CAPÍTULO
        # -------------------------

        antes = posicion

        posicion = _saltar(
            palabras,
            posicion,
            ANTES_CAPITULO
        )

        # ¿Dijo explícitamente "capítulo"?
        con_capitulo = any(
            p in PALABRAS_CAPITULO
            for p in palabras[antes:posicion]
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
                "clave_libro": clave,
                "con_capitulo": con_capitulo,
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
            "clave_libro": clave,
            "con_capitulo": con_capitulo,
        }

    return None
