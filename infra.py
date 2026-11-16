"""Errors i exceptions de l'aplicació del magatzem."""

import json


class AppError(Exception):
    """Excepció controlada de l'aplicació amb codi i missatge estructurats.

    El codi s'utilitza per identificar el tipus d'error (per exemple:
    PENDENT_IMPLEMENTACIO, INVENTARI_NO_TROBAT, INFORME_INVALID...) i el
    missatge descrit el problema per a l'usuari o el client.
    """

    def __init__(self, codi, missatge):
        self.codi = codi
        self.missatge = missatge
        super().__init__(missatge)

    def as_dict(self):
        """Retorna l'error com a diccionari serialitzable a JSON."""
        return {"codi": self.codi, "missatge": self.missatge}

    def __str__(self):
        return f"[{self.codi}] {self.missatge}"
