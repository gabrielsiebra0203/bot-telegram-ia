"""Chat no terminal com memória e ferramentas (cálculos e previsão do tempo)."""

import logging
import os
from pathlib import Path

import openai

from agente import LimiteDeRodadasError, responder
from chat import mensagem_de_erro, mostrar_historico
from conversa import Conversa
from llm_config import criar_cliente

MAX_MENSAGENS = 20
ARQUIVO_HISTORICO = Path(__file__).resolve().parent.parent / "dados" / "historico_ferramentas.json"


def configurar_log():
    """Mostra no terminal cada ferramenta usada. Com DEPURAR=1 mostra mais detalhes."""
    nivel = logging.DEBUG if os.environ.get("DEPURAR") == "1" else logging.INFO
    logging.basicConfig(level=nivel, format="%(message)s")
    for biblioteca in ("httpx", "httpcore", "openai"):
        logging.getLogger(biblioteca).setLevel(logging.WARNING)


def main():
    configurar_log()
    client, modelo, extras = criar_cliente()

    conversa = Conversa(max_mensagens=MAX_MENSAGENS)
    conversa.carregar(ARQUIVO_HISTORICO)

    print(f"Modelo: {modelo} | ferramentas: calcular, previsao_clima, cidades_monitoradas")
    print("Comandos: /historico, /limpar, /sair")

    while True:
        entrada = input("\nVocê: ").strip()
        comando = entrada.lower()

        if comando in ("/sair", "sair"):
            print("Até logo!")
            break
        if comando == "/limpar":
            conversa.limpar()
            conversa.salvar(ARQUIVO_HISTORICO)
            print("Memória apagada.")
            continue
        if comando == "/historico":
            mostrar_historico(conversa)
            continue
        if not entrada:
            continue

        conversa.adicionar_usuario(entrada)
        try:
            resultado = responder(client, modelo, extras, conversa)
        except LimiteDeRodadasError as erro:
            conversa.desfazer_ultima()
            print(f"O agente travou num ciclo de ferramentas. {erro}")
            continue
        except openai.OpenAIError as erro:
            conversa.desfazer_ultima()
            print(mensagem_de_erro(erro))
            if isinstance(erro, openai.AuthenticationError):
                break
            continue

        if not resultado.texto.strip():
            conversa.desfazer_ultima()
            print("O modelo devolveu uma resposta vazia. Tente de novo.")
            continue

        conversa.adicionar_assistente(resultado.texto)
        conversa.salvar(ARQUIVO_HISTORICO)

        print(f"\nIA: {resultado.texto}")
        if resultado.finish_reason == "length":
            print("(aviso: a resposta foi cortada pelo limite de tokens)")
        usadas = ", ".join(resultado.ferramentas) if resultado.ferramentas else "nenhuma"
        print(
            f"[ferramentas: {usadas} | tokens: {resultado.tokens_entrada} de entrada, "
            f"{resultado.tokens_saida} de saída]"
        )


if __name__ == "__main__":
    main()