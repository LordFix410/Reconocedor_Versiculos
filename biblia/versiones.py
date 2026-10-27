import time
import re
import unicodedata
import pyautogui

from biblia.esword import preparar_ventana
from biblia.acciones import enviar

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
            "lenguaje sencillo",
            "sencillo"
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
            "tla",
            "te ele a",
            "te elia",
            "te el dia",
            "pelea",
            "de lear",
            "actual"
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
            "ele pe de",
            "pediste",
            "vedette",
            "puede",
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

        anterior = COMANDOS_NORMALIZADOS.get(comando_normalizado)

        if anterior is not None and anterior is not version:
            # Mismo comando en dos versiones: gana la última.
            print(
                f"⚠️ Comando repetido en VERSIONES: "
                f"'{comando_normalizado}' (gana la última)"
            )

        COMANDOS_NORMALIZADOS[
            comando_normalizado
        ] = version

COMANDOS_PALABRAS = {
    comando: comando.split()
    for comando in COMANDOS_NORMALIZADOS
}

# Más largos primero (para que "reina valera 1960" gane a "reina valera")
COMANDOS_ORDENADOS = sorted(
    COMANDOS_NORMALIZADOS.keys(),
    key=len,
    reverse=True
)


# ============================================================
# AJUSTES DE DETECCIÓN
# ============================================================
#
# REGLA GENERAL: el nombre de una versión funciona SOLO, sin decir
# "versión" ("...la biblia de las americas...", "dios habla hoy").
#
# EXCEPCIONES (necesitan palabra clave pegada):
#   1) "Al Día" y "Jerusalén": se confunden con lectura normal
#      ("hubo un día", "al llegar a Jerusalén").
#   2) Palabras comunes del español que Vosk usa como error de otra
#      versión ("puede", "cita", "sesenta", "actual"...): solas
#      serían un desastre, así que también piden palabra clave.

PALABRAS_CLAVE = {
    "version", "biblia", "traduccion", "lenguaje", "aversion"
}

# Palabras clave que dicen "esto es una versión" sin lugar a dudas.
CLAVES_VERSION = {
    "version", "traduccion", "aversion", "lenguaje"
}

# Máximo de palabras permitidas ENTRE la palabra clave y el comando
# ("la version de reina valera" -> 1 palabra en medio: "de").
MAX_PALABRAS_ENTRE = 2

# Para Al Día y Jerusalén: pegado a la clave, o con UNA de estas
# palabras en medio ("biblia DE jerusalen"). "biblia en jerusalen"
# NO cuenta.
RELLENO_CLAVE = {"de", "la", "del"}

# Posiciones (clic) de las versiones que SIEMPRE exigen palabra clave.
POS_EXIGEN_CLAVE = {
    (1031, 391),   # Biblia al Día
    (1521, 393),   # Biblia de Jerusalén
}


def _norm(lista):
    return {normalizar_texto(x) for x in lista}


# Todos los comandos de Al Día y Jerusalén (se arma solo desde VERSIONES)
REQUIEREN_CLAVE = {
    comando
    for comando, version in COMANDOS_NORMALIZADOS.items()
    if version["pos"] in POS_EXIGEN_CLAVE
}

# Comandos que son palabras comunes (o suenan a otras cosas): solo
# valen PEGADOS a la palabra clave ("version sesenta", "lenguaje actual").
DEBILES = _norm([
    "bad", "be a de", "al dia", "june", "pelea", "de lear",
    "te el dia", "te elia", "actual", "tla", "sesenta", "fin de",
    "de ti", "de te", "cab", "cita", "de cita", "visita", "pepita",
    "puede", "pediste", "vedette", "diste", "castilla",
    "para todos", "sencillo", "internacional", "viviente",
    "arcas", "fernandez", "serafin",
])

# Los más peligrosos ("la biblia puede transformar...") solo valen
# si la palabra clave es "version"/"traduccion", no "biblia".
SOLO_CON_VERSION = _norm([
    "puede", "pediste", "vedette", "diste", "cita", "de cita",
    "visita", "pepita", "pelea", "de ti", "de te", "fin de",
    "bad", "sesenta", "castilla", "june",
])

# Frases normales de sermón que contienen un nombre de versión:
# "el pueblo de Dios" NO debe ser la versión LPD sin palabra clave.
FRASES_COMUNES = _norm([
    "pueblo de dios",
])

# Todo lo que NO puede dispararse sin palabra clave
NECESITA_CLAVE = (
    REQUIEREN_CLAVE | DEBILES | SOLO_CON_VERSION | FRASES_COMUNES
)


# ============================================================
# BUSCAR VERSIÓN
# ============================================================

_ultimo_log = ""


def _buscar_sublista(palabras, frase):
    """Posición donde empieza `frase` dentro de `palabras`, o None."""
    n = len(frase)

    for j in range(len(palabras) - n + 1):
        if palabras[j:j + n] == frase:
            return j

    return None


def _buscar_tras_clave(palabras, indice_clave):
    """
    Busca un comando justo DESPUÉS de la palabra clave
    (máximo MAX_PALABRAS_ENTRE palabras en medio).
    """

    clave = palabras[indice_clave]
    resto = palabras[indice_clave + 1:]

    if not resto:
        return None

    candidatos = []

    for comando in COMANDOS_ORDENADOS:

        frase = COMANDOS_PALABRAS[comando]
        j = _buscar_sublista(resto, frase)

        if j is None:
            continue

        # Demasiado lejos de la palabra clave
        if j > MAX_PALABRAS_ENTRE:
            continue

        # Al Día / Jerusalén: pegado, o con un solo "de/la/del" en medio
        if comando in REQUIEREN_CLAVE:

            if j > 1:
                continue

            if j == 1 and resto[0] not in RELLENO_CLAVE:
                continue

        # Palabras comunes: solo pegadas a la clave
        if comando in DEBILES and j != 0:
            continue

        # Las más peligrosas: solo con "version"/"traduccion"
        if comando in SOLO_CON_VERSION and clave not in CLAVES_VERSION:
            continue

        # "la biblia tiene sesenta y seis libros"
        if comando == "sesenta" and resto[j + 1:j + 2] == ["y"]:
            continue

        candidatos.append((j, -len(comando), comando))

    if not candidatos:
        return None

    # El más cercano a la palabra clave; a igual distancia, el más largo
    _, _, mejor = min(candidatos)

    return COMANDOS_NORMALIZADOS[mejor], mejor


def _buscar_sin_clave(palabras):
    """
    Nombre de versión dicho SOLO ("...la biblia de las americas...").
    Se ignoran los comandos que necesitan palabra clave.
    Gana el último mencionado.
    """

    mejor = None
    mejor_fin = -1

    for comando in COMANDOS_ORDENADOS:

        if comando in NECESITA_CLAVE:
            continue

        frase = COMANDOS_PALABRAS[comando]
        j = _buscar_sublista(palabras, frase)

        if j is None:
            continue

        fin = j + len(frase)

        if fin > mejor_fin:
            mejor_fin = fin
            mejor = comando

    if mejor is None:
        return None

    return COMANDOS_NORMALIZADOS[mejor], mejor


def buscar_version(texto):

    global _ultimo_log

    texto = normalizar_texto(texto)
    palabras = texto.split()

    if not palabras:
        return None

    # --------------------------------------------------------
    # 1) CON PALABRA CLAVE (version / biblia / traduccion...)
    #    Se prueba desde la última aparición hacia atrás.
    # --------------------------------------------------------

    indices_clave = [
        i for i, palabra in enumerate(palabras)
        if palabra in PALABRAS_CLAVE
    ]

    for indice in reversed(indices_clave):

        resultado = _buscar_tras_clave(palabras, indice)

        if resultado is not None:
            return resultado

    # Log de depuración (solo cuando cambia, para no llenar la consola)
    if indices_clave:

        despues = " ".join(palabras[indices_clave[-1] + 1:])

        if despues and despues != _ultimo_log:
            _ultimo_log = despues
            print(f"🔎 Después de {palabras[indices_clave[-1]]}: {despues}")

    # --------------------------------------------------------
    # 2) SIN PALABRA CLAVE: el nombre de la versión basta
    #    (menos Al Día, Jerusalén y las palabras comunes)
    # --------------------------------------------------------

    return _buscar_sin_clave(palabras)


class ControladorVersiones:

    def __init__(self):
        self.click_en_bloque = None

    def procesar(self, texto, final=False):

        resultado = buscar_version(texto)

        if resultado is None:
            if final:
                self.click_en_bloque = None
            return

        version, comando_detectado = resultado
        clave = version["pos"]

        if clave == self.click_en_bloque:
            if final:
                self.click_en_bloque = None
            return

        print(f"🎯 Versión: {comando_detectado}")

        # Si fue en el final, el bloque ya terminó
        self.click_en_bloque = None if final else clave

        # El clic se hace en el hilo de acciones (en orden con las
        # búsquedas de e-Sword, sin bloquear la escucha).
        enviar(
            f"clic versión {comando_detectado}",
            self._hacer_click,
            clave
        )

    def _hacer_click(self, clave):

        # Las coordenadas son de la ventana de e-Sword: buscarla
        # (con reintentos) y ponerla al frente ANTES de hacer clic.
        if preparar_ventana() is None:
            print("⚠️ Sin e-Sword al frente: no se hace clic")

            # Permitir reintentar el mismo clic en este bloque
            if self.click_en_bloque == clave:
                self.click_en_bloque = None
            return

        pyautogui.click(*clave)
