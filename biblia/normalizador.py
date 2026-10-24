import unicodedata


REEMPLAZOS = {
    "primera": "1",
    "primer": "1",
    "primero": "1",
    "segunda": "2",
    "segundo": "2",
    # Vosk a veces oye "segunda" como "segun" ("segun timoteo tres dieciseis").
    # Solo se convierte si lo que sigue es un libro numerado (ver abajo).
    "segun": "2",
    "tercera": "3",
    "tercer": "3",
    "tercero": "3",
}

# "segun juan 3:16" casi siempre es "según Juan" (el evangelio),
# no "2 Juan", así que con "segun" no se convierte antes de estos libros.
EXCEPCIONES_SEGUN = {"juan"}


PALABRAS_RELLENO = {
    "libro",
    "carta",
    "epistola",
    "apostol",
    "san",
    "santo",
    "de",
    "del",
    "la",
    "las",
    "el",
    "los",
    "a",
    "pablo",
    "apostoles"
}


def quitar_tildes(texto):

    texto = unicodedata.normalize(
        "NFD",
        texto.lower()
    )

    return "".join(
        letra
        for letra in texto
        if unicodedata.category(letra) != "Mn"
    )


LIBROS_NUMERADOS = {
    "samuel", "reyes", "cronicas", "corintios",
    "tesalonicenses", "timoteo", "pedro", "juan",
}


def normalizar_palabras(texto):

    palabras = quitar_tildes(texto).split()
    resultado = []

    for i, palabra in enumerate(palabras):

        if palabra in REEMPLAZOS:

            # Solo convertir si lo que sigue es un libro numerado
            siguiente = next(
                (p for p in palabras[i + 1:]
                 if p not in PALABRAS_RELLENO),
                None
            )

            convertir = siguiente in LIBROS_NUMERADOS

            if palabra == "segun" and siguiente in EXCEPCIONES_SEGUN:
                convertir = False

            resultado.append(
                REEMPLAZOS[palabra]
                if convertir
                else palabra
            )
            continue

        if palabra in PALABRAS_RELLENO:
            continue

        resultado.append(palabra)

    return resultado
