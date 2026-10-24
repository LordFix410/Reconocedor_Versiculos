from biblia.centinela import Centinela
from biblia.esword import buscar
from biblia.obs import mostrar_presentacion


class Controlador:


    def __init__(self):

        self.centinela = Centinela()

    def procesar(self, texto):

        evento = self.centinela.procesar(
            texto
        )

        self._ejecutar(
            evento,
            rapido=False
        )

    def procesar_parcial(self, texto):

        evento = (
            self.centinela.procesar_parcial(
                texto
            )
        )

        self._ejecutar(
            evento,
            rapido=True
        )

    def fin_de_frase(self):
        """Vosk cerró una frase sin texto."""
        self.centinela.fin_de_frase()

    def _ejecutar(
        self,
        evento,
        rapido=False
    ):

        if evento is None:
            return

        tipo = evento["tipo"]

        # -------------------------
        # PRESENTACIÓN
        # -------------------------

        if tipo == "PRESENTACION":

            print("🖥️ Presentación")

            mostrar_presentacion()
            return

        # -------------------------
        # CAPÍTULO
        # -------------------------

        if tipo == "CAPITULO":

            cita = (
                f'{evento["libro"]} '
                f'{evento["capitulo"]}'
            )

        # -------------------------
        # CITA COMPLETA
        # -------------------------

        elif tipo == "REFERENCIA":

            cita = (
                f'{evento["libro"]} '
                f'{evento["capitulo"]}:'
                f'{evento["versiculo"]}'
            )

        # -------------------------
        # VERSÍCULO
        # -------------------------

        elif tipo == "VERSICULO":

            cita = str(
                evento["versiculo"]
            )

        else:
            return

        if rapido:
            print("⚡", cita)
        else:
            print("📖", cita)

        buscar(
            cita,
            mostrar_obs=evento["mostrar_obs"]
        )
