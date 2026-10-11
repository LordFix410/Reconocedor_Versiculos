import os

from biblia.voz import BibliaVoz


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MODELO = os.path.join(
    BASE_DIR,
    "modelo"
)


biblia = BibliaVoz(
    modelo=MODELO,
    dispositivo=None
)

try:
    biblia.escuchar()

except KeyboardInterrupt:
    print("\n👋 Finalizado.")