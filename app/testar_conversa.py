"""Testes simples da classe Conversa. Rode com: python app/testar_conversa.py"""

import sys
import tempfile
from pathlib import Path

from conversa import Conversa


def testar_limite_e_inicio_por_usuario():
    conversa = Conversa(max_mensagens=4)
    for i in range(5):
        conversa.adicionar_usuario(f"pergunta {i}")
        conversa.adicionar_assistente(f"resposta {i}")
    conversa.adicionar_usuario("pergunta final")

    assert len(conversa.mensagens) <= 4
    assert conversa.mensagens[0]["role"] == "user"
    assert conversa.mensagens[-1]["content"] == "pergunta final"


def testar_desfazer_ultima():
    conversa = Conversa()
    conversa.adicionar_usuario("oi")
    conversa.desfazer_ultima()
    assert conversa.mensagens == []


def testar_para_api_coloca_sistema_na_frente():
    conversa = Conversa()
    conversa.adicionar_usuario("oi")
    mensagens = conversa.para_api("regras")

    assert mensagens[0] == {"role": "system", "content": "regras"}
    assert mensagens[1] == {"role": "user", "content": "oi"}


def testar_salvar_e_carregar():
    with tempfile.TemporaryDirectory() as pasta:
        caminho = Path(pasta) / "historico.json"

        original = Conversa()
        original.adicionar_usuario("oi")
        original.adicionar_assistente("olá")
        original.salvar(caminho)

        copia = Conversa()
        copia.carregar(caminho)
        assert copia.mensagens == original.mensagens


def testar_arquivo_corrompido_e_ignorado():
    with tempfile.TemporaryDirectory() as pasta:
        caminho = Path(pasta) / "historico.json"
        caminho.write_text("{isso não é json", encoding="utf-8")

        conversa = Conversa()
        conversa.carregar(caminho)
        assert conversa.mensagens == []


TESTES = [
    testar_limite_e_inicio_por_usuario,
    testar_desfazer_ultima,
    testar_para_api_coloca_sistema_na_frente,
    testar_salvar_e_carregar,
    testar_arquivo_corrompido_e_ignorado,
]


def main():
    falhas = 0
    for teste in TESTES:
        try:
            teste()
            print(f"OK      {teste.__name__}")
        except AssertionError:
            falhas += 1
            print(f"FALHOU  {teste.__name__}")

    print(f"\n{len(TESTES) - falhas} de {len(TESTES)} testes passaram.")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()