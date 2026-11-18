"""Histórico de uma conversa com o modelo: guarda, limita e persiste as mensagens."""

import json
from pathlib import Path


class Conversa:
    """Guarda as mensagens trocadas (user/assistant) e controla o tamanho do histórico."""

    def __init__(self, max_mensagens=20):
        self.max_mensagens = max_mensagens
        self.mensagens = []

    def adicionar_usuario(self, texto):
        """Registra uma mensagem do usuário e descarta as mais antigas se passar do limite."""
        self.mensagens.append({"role": "user", "content": texto})
        self._limitar()

    def adicionar_assistente(self, texto):
        """Registra a resposta do modelo."""
        self.mensagens.append({"role": "assistant", "content": texto})

    def desfazer_ultima(self):
        """Remove a última mensagem (usado quando a chamada à API falha)."""
        if self.mensagens:
            self.mensagens.pop()

    def limpar(self):
        """Apaga todo o histórico."""
        self.mensagens.clear()

    def _limitar(self):
        """Mantém só as últimas mensagens e garante que o histórico comece por uma do usuário."""
        excesso = len(self.mensagens) - self.max_mensagens
        if excesso > 0:
            del self.mensagens[:excesso]
        while self.mensagens and self.mensagens[0]["role"] != "user":
            self.mensagens.pop(0)

    def para_api(self, sistema):
        """Devolve a lista no formato da API, com o system prompt na frente."""
        return [{"role": "system", "content": sistema}, *self.mensagens]

    def salvar(self, caminho):
        """Grava o histórico em um arquivo JSON."""
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(
            json.dumps(self.mensagens, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def carregar(self, caminho):
        """Carrega o histórico de um arquivo JSON. Arquivo ausente ou inválido é ignorado."""
        caminho = Path(caminho)
        if not caminho.exists():
            return
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        if not isinstance(dados, list):
            return

        self.mensagens = [
            {"role": item["role"], "content": item["content"]}
            for item in dados
            if isinstance(item, dict)
            and item.get("role") in ("user", "assistant")
            and isinstance(item.get("content"), str)
        ]
        self._limitar()