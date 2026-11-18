"""Limita quantas requisições cada usuário pode fazer, em uma ou mais janelas de tempo."""

import time
from collections import deque


class LimitesDeUso:
    """Controle em memória: cada regra é (máximo de requisições, janela em segundos).

    Exemplo: LimitesDeUso([(6, 60), (150, 86400)]) permite 6 por minuto e 150 por dia.
    Os registros somem quando o programa reinicia.
    """

    def __init__(self, regras, relogio=time.monotonic):
        self.regras = regras
        self._relogio = relogio
        self._registros = {}

    def permitir(self, usuario):
        """Registra uma requisição se couber nos limites. Devolve (permitido, segundos_de_espera)."""
        agora = self._relogio()
        maior_janela = max(janela for _, janela in self.regras)
        fila = self._registros.setdefault(usuario, deque())

        while fila and agora - fila[0] >= maior_janela:
            fila.popleft()

        espera = 0.0
        for maximo, janela in self.regras:
            recentes = [instante for instante in fila if agora - instante < janela]
            if len(recentes) >= maximo:
                espera = max(espera, janela - (agora - recentes[0]))

        if espera > 0:
            return False, espera

        fila.append(agora)
        return True, 0.0