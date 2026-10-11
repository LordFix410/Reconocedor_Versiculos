import time

from biblia.esword import buscar
from biblia.obs import mostrar_presentacion


print("1. Abriendo Juan 3:16")

buscar("Juan 3:16")

time.sleep(2)

print("2. Cambiando a presentación")

mostrar_presentacion()