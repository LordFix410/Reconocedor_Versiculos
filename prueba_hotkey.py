import time
from biblia.esword import ctrl_l_global

print("En 3 segundos mando Ctrl+L...")
time.sleep(3)

ctrl_l_global()

print("Enviado")