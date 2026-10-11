import time
import unicodedata
import pyautogui

def normalizar_texto(texto):

    texto = texto.lower()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    return texto.strip()


# ============================================================
# CONFIGURACIÓN DE VERSIONES
# ============================================================

VERSIONES = [

    # --------------------------------------------------------
    # PRIMERA TANDA
    # --------------------------------------------------------

    {
        "comandos": [
            "nacar colunga",
            "nácar",
            "colunga",
            "la biblia nacar colunga",
            "nacar",
            "columba"
        ],
        "pos": (913, 389),
    },

    {
        "comandos": [
            "pablo beso",
            "pablo eso",
            "pablo son",
            "pablo fue son",
            "pablo vez son",
            "nuevo testamento pablo besson",
            "ra opcion pablo vi son",
            "besson"
        ],
        "pos": (973, 385),
    },

    {
        "comandos": [
            "biblia al día",
            "biblia el día",
            "producción biblia el día",
            "bad",
            "be a de",
            "al dia", 
            "al día"
        ],
        "pos": (1031, 391),
    },

    {
        "comandos": [
            "junemann",
            "la biblia version junemann",
            "junemann de la septuaginta",
            "june",
            "june manda",
            "june mano"
        ],
        "pos": (1109, 386),
    },

    {
        "comandos": [
            "biblia en lenguaje sencillo",
            "biblia el lenguaje sencillo",
            "bls",
            "be ele ese",
            "lenguaje sencillo"
        ],
        "pos": (1192, 389),
    },

    {
        "comandos": [
            "reina valera 1960",
            "reina valera",
            "rv 1960",
            "sesenta",
            "reina valera mil nueve sesenta",
            "reina valera mil novecientos sesenta"
        ],
        "pos": (1247, 386),
    },

    {
        "comandos": [
            "traducción kadosh",
            "kadosh israelita",
            "kadosh",
            "kadosh israelita mesianica"
        ],
        "pos": (1345, 387),
    },

    {
        "comandos": [
            "biblia castillian",
            "castillian",
            "cab",
            "castilla",
            "castillian 2003",
            "castilian"
        ],
        "pos": (1415, 383),
    },

    {
        "comandos": [
            "dios habla hoy",
            "dhh",
            "de hache hache",
            "de ache ache"
        ],
        "pos": (1472, 386),
    },

    {
        "comandos": [
            "jerusalen",
            "jota e erre",
            "biblia de jerusalen",
            "biblia de jerusalén",
            "jerusalén"
        ],
        "pos": (1521, 393),
    },

    {
        "comandos": [
            "arcas fernandez",
            "nuevo testamento arcas fernandez",
            "arcas",
            "fernandez"
        ],
        "pos": (1589, 387),
    },

    {
        "comandos": [
            "serafìn de ausejo",
            "serafin",
            "fin de",
            "ausejo"
        ],
        "pos": (1650, 387),
    },

    {
        "comandos": [
            "traduccion lenguaje sencillo",
            "tla",
            "te ele a",
            "lenguaje sencillo",
            "te elia",
            "te el dia",
            "pelea",
            "de lear"
        ],
        "pos": (1703, 390),
    },


    # --------------------------------------------------------
    # SEGUNDA TANDA
    # --------------------------------------------------------

    {
        "comandos": [
            "biblia de navarra",
            "eunsa",
            "navarra",
            "e u n s a",
            "eunsa navarra"
        ],
        "pos": (1106, 409),
    },

    {
        "comandos": [
            "biblia latinoamericana",
            "latinoamericana",
            "la latinoamericana"
        ],
        "pos": (1203, 411),
    },

    {
        "comandos": [
            "biblia textual",
            "textual"
        ],
        "pos": (1282, 411),
    },

    {
        "comandos": [
            "el codigo real",
            "codigo real",
            "ecr",
            "e ce erre",
            "codigo regal",
            "código regal"
        ],
        "pos": (1333, 411),
    },

    {
        "comandos": [
            "la biblia de las americas",
            "biblia de las americas",
            "lbla",
            "ele be ele a",
            "de las americas"
        ],
        "pos": (1394, 414),
    },

    {
        "comandos": [
            "el libro del pueblo de dios",
            "pueblo de dios",
            "lpd",
            "ele pe de"
        ],
        "pos": (1459, 407),
    },

    {
        "comandos": [
            "la nueva traducción viviente",
            "traducción viviente",
            "ntv",
            "ene te uve",
            "ene te ve",
            "viviente"
        ],
        "pos": (1527, 412),
    },

    {
        "comandos": [
            "nueva versión internacional",
            "versión internacional",
            "nvi",
            "internacional",
            "ene uve i",
            "ene ve i",
            "en eba"
        ],
        "pos": (1596, 411),
    },

    {
        "comandos": [
            "palabra de dios para todos",
            "pdt",
            "pe de te",
            "para todos",
            "de ti",
            "de te",
            "diste",
            "vedette"
        ],
        "pos": (1693, 414),
    },

    {
        "comandos": [
            "visita",
            "de cita",
            "biblia peshita",
            "pepita",
            "cita"
        ],
        "pos": (1761, 406),
    },

    {
        "comandos": [
            "biblia torres amat",
            "torres amat",
            "torres amad",
            "orres amato"
        ],
        "pos": (1865, 410),
    },
]


# ============================================================
# PREPARAR COMANDOS NORMALIZADOS
# ============================================================

COMANDOS_NORMALIZADOS = {}

for version in VERSIONES:

    for comando in version["comandos"]:

        comando_normalizado = normalizar_texto(
            comando
        )

        COMANDOS_NORMALIZADOS[
            comando_normalizado
        ] = version


# ============================================================
# ORDENAR COMANDOS
# ============================================================

COMANDOS_ORDENADOS = sorted(
    COMANDOS_NORMALIZADOS.keys(),
    key=len,
    reverse=True
)

# ============================================================
# BUSCAR VERSIÓN
# ============================================================

def buscar_version(texto):

    texto = normalizar_texto(
        texto
    )

    palabras = texto.split()


    # --------------------------------------------------------
    # SOLAMENTE ACTIVAR SI DIJO "VERSION"
    # --------------------------------------------------------

    if "version" not in palabras:

        return None


    # --------------------------------------------------------
    # TOMAR LA ÚLTIMA APARICIÓN DE "VERSION"
    # --------------------------------------------------------

    indice_version = (
        len(palabras)
        - 1
        - palabras[::-1].index("version")
    )


    # --------------------------------------------------------
    # TEXTO DESPUÉS DE "VERSION"
    # --------------------------------------------------------

    despues_version = " ".join(
        palabras[indice_version + 1:]
    ).strip()


    if not despues_version:

        return None


    print(
        f"🔎 Después de versión: {despues_version}"
    )


    # --------------------------------------------------------
    # BUSCAR COMANDO
    # --------------------------------------------------------

    for comando in COMANDOS_ORDENADOS:

        if comando in despues_version:

            return (
                COMANDOS_NORMALIZADOS[comando],
                comando
            )


    return None
class ControladorVersiones:

    def __init__(self):
        self.ultimo_click = None
        self.tiempo_ultimo_click = 0.0

    def procesar(self, texto):

        resultado = buscar_version(texto)

        if resultado is None:
            return

        version, comando_detectado = resultado

        clave = version["pos"]
        ahora = time.monotonic()

        # Evitar parcial + final duplicado
        if (
            clave == self.ultimo_click
            and ahora - self.tiempo_ultimo_click < 2
        ):
            return

        self.ultimo_click = clave
        self.tiempo_ultimo_click = ahora

        x, y = version["pos"]

        print(
            f"🎯 Versión: {comando_detectado}"
        )

        pyautogui.click(
            x,
            y
        )