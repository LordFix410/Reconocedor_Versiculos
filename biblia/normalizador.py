import unicodedata


REEMPLAZOS = {
    "primera": "1",
    "primer": "1",
    "primero": "1",
    "segunda": "2",
    "segundo": "2",
    "tercera": "3",
    "tercer": "3",
    "tercero": "3",
}


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
    "pablo"
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


def normalizar_palabras(texto):

    texto = quitar_tildes(texto)

    palabras = texto.split()

    resultado = []

    for palabra in palabras:

        # primera -> 1, segunda -> 2...
        if palabra in REEMPLAZOS:
            resultado.append(
                REEMPLAZOS[palabra]
            )
            continue

        # Ignorar palabras decorativas
        if palabra in PALABRAS_RELLENO:
            continue

        resultado.append(palabra)

    return resultado