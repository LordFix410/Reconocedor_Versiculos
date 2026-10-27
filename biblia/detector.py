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

# Palabras que dicen "versículo" de forma explícita
PALABRAS_VERSICULO_EXPL = {
    "versiculo",
    "versiculos",
    "verso",
    "versos",
}

# Cuántas palabras hacia atrás se mira buscando "capítulo N" antes
# del libro ("capitulo cinco de exodo", "versiculo tres del capitulo
# cinco de exodo").
MAX_ATRAS = 8

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


def _numero_exacto(palabras, desde, hasta):
    """
    Número formado por TODAS las palabras palabras[desde:hasta]
    (ej. ["treinta","y","cinco"] -> 35), o None si no encaja justo.
    """
    if desde >= hasta:
        return None

    numero, usadas = convertir_numero(palabras[desde:hasta])

    if numero is None or desde + usadas != hasta:
        return None

    return numero


def _numeros_despues(palabras, posicion):
    """
    Forma clásica: el libro va PRIMERO ("exodo capitulo cinco",
    "juan tres dieciseis").

    `posicion` es donde termina el libro. Devuelve un diccionario
    con capitulo / versiculo / con_capitulo, o None si no hay número.
    """

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
        return None

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
            "capitulo": capitulo,
            "versiculo": None,
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
        "capitulo": capitulo,
        "versiculo": versiculo,
        "con_capitulo": con_capitulo,
    }


def _capitulo_antes_del_libro(palabras, inicio, fin_libro):
    """
    Forma invertida: el capítulo se dice ANTES que el libro.

        "capitulo cinco de exodo"
        "capitulo cinco versiculo tres de exodo"
        "versiculo tres del capitulo cinco de exodo"
        "capitulo cinco de exodo versiculo tres"

    (las palabras "de", "del", "el", "libro"... ya las quitó el
    normalizador). Exige la palabra "capítulo" de forma explícita,
    para no confundir "tres exodo" con una cita.

    Devuelve {"capitulo", "versiculo"} o None.
    """

    minimo = max(0, inicio - MAX_ATRAS)

    for j in range(inicio - 1, minimo - 1, -1):

        if palabras[j] not in PALABRAS_CAPITULO:
            continue

        # "capitulo <N> [versiculo <V>] <libro>"
        capitulo, usadas = convertir_numero(palabras[j + 1:inicio])

        if capitulo is None:
            continue

        pos = j + 1 + usadas
        versiculo = None

        if pos != inicio:

            # ¿lo que sobra es "versiculo <V>" justo antes del libro?
            pos2 = _saltar(
                palabras, pos,
                PALABRAS_VERSICULO_EXPL | {"numero"}
            )

            if pos2 == pos:
                continue

            versiculo = _numero_exacto(palabras, pos2, inicio)

            if versiculo is None:
                continue

        # "versiculo <V> [del] capitulo <N> <libro>"
        if versiculo is None:

            for m in range(j - 1, max(-1, j - 5), -1):

                if palabras[m] in PALABRAS_VERSICULO_EXPL:

                    versiculo = _numero_exacto(palabras, m + 1, j)

                    if versiculo is not None:
                        break

        # "capitulo <N> <libro> versiculo <V>"
        if versiculo is None:

            pos3 = _saltar(
                palabras, fin_libro,
                PALABRAS_VERSICULO_EXPL | {"numero"}
            )

            if pos3 > fin_libro:

                v, _ = convertir_numero(palabras[pos3:])

                if v is not None:
                    versiculo = v

        return {
            "capitulo": capitulo,
            "versiculo": versiculo,
        }

    return None


def detectar_referencia(texto):

    palabras = normalizar_palabras(texto)

    # Preferir el libro mencionado más recientemente.
    for i in range(len(palabras) - 1, -1, -1):

        encontrado = _libro_en(palabras, i)

        if encontrado is None:
            continue

        libro, inicio, longitud_libro, clave = encontrado

        fin_libro = inicio + longitud_libro

        # Forma clásica: libro primero ("exodo cinco", "juan 3 16")
        despues = _numeros_despues(palabras, fin_libro)

        # Se queda con la forma clásica si dijo "capítulo" después
        # del libro, o si dio capítulo Y versículo.
        usar_despues = (
            despues is not None
            and (
                despues["con_capitulo"]
                or despues["versiculo"] is not None
            )
        )

        if not usar_despues:

            # Forma invertida: "capitulo cinco de exodo"
            antes = _capitulo_antes_del_libro(
                palabras, inicio, fin_libro
            )

            if antes is not None:

                return {
                    "libro": libro,
                    "capitulo": antes["capitulo"],
                    "versiculo": antes["versiculo"],
                    "clave_libro": clave,
                    # dijo "capítulo" explícitamente
                    "con_capitulo": True,
                }

            if despues is None:
                continue

        return {
            "libro": libro,
            "capitulo": despues["capitulo"],
            "versiculo": despues["versiculo"],
            "clave_libro": clave,
            "con_capitulo": despues["con_capitulo"],
        }

    return None
