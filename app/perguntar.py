"""Pergunta ao modelo pelo terminal, com tratamento dos erros mais comuns da API."""

import time

import openai

from llm_config import criar_cliente

MAX_TOKENS = 1000
TENTATIVAS = 3
SISTEMA = (
    "Você é um assistente prestativo. "
    "Responda sempre em português do Brasil, de forma clara e concisa."
)


def perguntar(client, modelo, extras, pergunta):
    """Envia uma pergunta isolada. Se o limite do plano gratuito for atingido, espera e tenta de novo."""
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = client.chat.completions.create(
                model=modelo,
                max_tokens=MAX_TOKENS,
                messages=[
                    {"role": "system", "content": SISTEMA},
                    {"role": "user", "content": pergunta},
                ],
                **extras,
            )
            return resposta.choices[0].message.content or "", resposta.usage
        except openai.RateLimitError:
            if tentativa == TENTATIVAS:
                raise
            espera = 2 ** tentativa
            print(f"(limite atingido, tentando de novo em {espera}s...)")
            time.sleep(espera)


def main():
    client, modelo, extras = criar_cliente()
    print(f"Modelo: {modelo}. Digite 'sair' para encerrar.")

    while True:
        pergunta = input("\nVocê: ").strip()
        if pergunta.lower() == "sair":
            print("Até logo!")
            break
        if not pergunta:
            continue

        try:
            texto, uso = perguntar(client, modelo, extras, pergunta)
        except openai.AuthenticationError:
            print("Chave de API inválida. Confira o arquivo .env.")
            break
        except openai.RateLimitError:
            print("Limite do plano gratuito atingido. Espere um pouco e tente de novo.")
            continue
        except openai.APIConnectionError:
            print("Sem conexão com a API. Verifique a internet e o LLM_BASE_URL.")
            continue
        except openai.APIStatusError as erro:
            print(f"A API recusou o pedido (código {erro.status_code}): {erro.message}")
            continue

        print(f"\nIA: {texto}")
        if uso:
            print(f"[tokens: {uso.prompt_tokens} de entrada, {uso.completion_tokens} de saída]")


if __name__ == "__main__":
    main()