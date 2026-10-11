from biblia.centinela import Centinela


c = Centinela()


pruebas = [
    "vamos a juan",
    "capitulo tres",
    "versiculo dieciseis",

    "tenemos treinta personas",

    "lucas nueve cincuenta y siete",

    # Simular parcial + final repetido
    "lucas nueve cincuenta y siete",

    "diapositiva",
    "juan tres dieciseis",

    "mateo cinco",
    "versiculo cuarenta y ocho",
]


for texto in pruebas:

    resultado = c.procesar(texto)

    print()
    print("🎤", texto)
    print("➡️", resultado)