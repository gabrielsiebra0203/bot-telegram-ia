"""Chat no terminal com memória: reenvia o histórico a cada pergunta."""

import time
from pathlib import Path

import openai

from conversa import Conversa
from llm_config import criar_cliente
from comum import mensagem_de_erro, montar_sistema

MAX_TOKENS = 1000
MAX_MENSAGENS = 20
TENTATIVAS = 3
ARQUIVO_HISTORICO = Path(__file__).resolve().parent.parent / "dados" / "historico.json"


def chamar_modelo(client, modelo, extras, conversa):
    """Envia o histórico ao modelo. Se o limite for atingido, espera e tenta de novo."""
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            return client.chat.completions.create(
                model=modelo,
                max_tokens=MAX_TOKENS,
                messages=conversa.para_api(montar_sistema()),
                **extras,
            )
        except openai.RateLimitError:
            if tentativa == TENTATIVAS:
                raise
            espera = 2 ** tentativa
            print(f"(limite atingido, tentando de novo em {espera}s...)")
            time.sleep(espera)


def mostrar_historico(conversa):
    """Mostra o que está guardado na memória da conversa."""
    print(f"\nHistórico: {len(conversa.mensagens)} mensagem(ns) (máximo {conversa.max_mensagens})")
    for mensagem in conversa.mensagens:
        texto = mensagem["content"].replace("\n", " ")
        if len(texto) > 70:
            texto = texto[:70] + "..."
        print(f"  {mensagem['role']:<10} {texto}")


def main():
    client, modelo, extras = criar_cliente()

    conversa = Conversa(max_mensagens=MAX_MENSAGENS)
    conversa.carregar(ARQUIVO_HISTORICO)

    print(f"Modelo: {modelo}")
    print("Comandos: /historico, /limpar, /sair")
    if conversa.mensagens:
        print(f"(conversa anterior carregada: {len(conversa.mensagens)} mensagens)")

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
            resposta = chamar_modelo(client, modelo, extras, conversa)
        except openai.OpenAIError as erro:
            conversa.desfazer_ultima()
            print(mensagem_de_erro(erro))
            if isinstance(erro, openai.AuthenticationError):
                break
            continue

        escolha = resposta.choices[0]
        texto = escolha.message.content or ""
        if not texto.strip():
            conversa.desfazer_ultima()
            print("O modelo devolveu uma resposta vazia. Tente de novo ou aumente o MAX_TOKENS.")
            continue

        conversa.adicionar_assistente(texto)
        conversa.salvar(ARQUIVO_HISTORICO)

        print(f"\nIA: {texto}")
        if escolha.finish_reason == "length":
            print("(aviso: a resposta foi cortada pelo limite de tokens)")
        if resposta.usage:
            print(
                f"[tokens: {resposta.usage.prompt_tokens} de entrada, "
                f"{resposta.usage.completion_tokens} de saída | "
                f"{len(conversa.mensagens)} mensagens na memória]"
            )


if __name__ == "__main__":
    main()