UNIDADES = {
    "cero": 0,
    "uno": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
}

ESPECIALES = {
    "diez": 10,
    "once": 11,
    "doce": 12,
    "trece": 13,
    "catorce": 14,
    "quince": 15,
    "dieciseis": 16,
    "diecisiete": 17,
    "dieciocho": 18,
    "diecinueve": 19,
}

VEINTIS = {
    "veinte": 20,
    "veintiuno": 21,
    "veintidos": 22,
    "veintitres": 23,
    "veinticuatro": 24,
    "veinticinco": 25,
    "veintiseis": 26,
    "veintisiete": 27,
    "veintiocho": 28,
    "veintinueve": 29,
    "veintiun": 21,
    "veintiuna": 21,
}

DECENAS = {
    "treinta": 30,
    "cuarenta": 40,
    "cincuenta": 50,
    "sesenta": 60,
    "setenta": 70,
    "ochenta": 80,
    "noventa": 90,
}

CENTENAS = {
    "cien": 100,
    "ciento": 100,
    "doscientos": 200,
    "trescientos": 300,
    "cuatrocientos": 400,
    "quinientos": 500,
    "seiscientos": 600,
    "setecientos": 700,
    "ochocientos": 800,
    "novecientos": 900,
}


def convertir_numero(palabras):
    """
    Recibe una lista de palabras.

    Devuelve:
        (numero, palabras_consumidas)

    Ejemplo:
        ["ciento", "treinta", "y", "cinco"]
        -> (135, 4)
    """

    if not palabras:
        return None, 0

    primera = palabras[0].lower()

    # Dígitos: "135"
    if primera.isdigit():
        return int(primera), 1

    # 0 - 9
    if primera in UNIDADES:
        return UNIDADES[primera], 1

    # "diez y seis", "veinte y cinco" (algunos modelos de Vosk
    # lo escriben así en vez de "dieciseis" / "veinticinco")
    if primera in ("diez", "veinte"):
        if (
            len(palabras) >= 3
            and palabras[1].lower() == "y"
            and UNIDADES.get(palabras[2].lower(), 0) > 0
        ):
            base = 10 if primera == "diez" else 20
            return base + UNIDADES[palabras[2].lower()], 3

    # 10 - 19
    if primera in ESPECIALES:
        return ESPECIALES[primera], 1

    # 20 - 29
    if primera in VEINTIS:
        return VEINTIS[primera], 1

    # 30, 40, 50...
    if primera in DECENAS:

        valor = DECENAS[primera]

        # treinta y cinco
        if (
            len(palabras) >= 3
            and palabras[1].lower() == "y"
            and palabras[2].lower() in UNIDADES
        ):
            return (
                valor + UNIDADES[palabras[2].lower()],
                3
            )

        return valor, 1

    # 100, 200, 300...
    if primera in CENTENAS:

        valor = CENTENAS[primera]

        if len(palabras) == 1:
            return valor, 1

        resto, consumidas = convertir_numero(
            palabras[1:]
        )

        if resto is not None:
            return valor + resto, consumidas + 1

        return valor, 1

    return None, 0