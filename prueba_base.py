from biblia.detector import detectar_referencia


pruebas = [
    "juan tres dieciseis",
    "vamos a juan tres dieciseis",
    "lucas nueve cincuenta y siete",
    "salmos ciento treinta y cinco uno",
    "primera carta del apostol pedro cinco ocho",
    "segunda carta a los corintios cuatro catorce",
    "jeremias diez",
    "tenemos treinta personas",
]


for texto in pruebas:

    resultado = detectar_referencia(texto)

    print()
    print(texto)
    print("->", resultado)