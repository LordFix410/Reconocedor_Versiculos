from biblia.controlador import Controlador


controlador = Controlador()

print("Escribe frases como:")
print("  juan tres dieciseis")
print("  versiculo dieciocho")
print("  diapositiva")
print("  salir")
print()


while True:

    texto = input("🎤 > ").strip()

    if texto.lower() == "salir":
        break

    controlador.procesar(texto)