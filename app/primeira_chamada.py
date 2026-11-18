"""Primeira chamada a um LLM por uma API compatível com OpenAI."""

from llm_config import criar_cliente

client, MODELO, EXTRAS = criar_cliente()

resposta = client.chat.completions.create(
    model=MODELO,
    max_tokens=1000,
    messages=[
        {"role": "user", "content": "Explique em 3 frases o que é uma API, para um iniciante."}
    ],
    **EXTRAS,
)

escolha = resposta.choices[0]
print(escolha.message.content)
print()
print(f"Modelo: {resposta.model}")
print(f"Motivo do fim: {escolha.finish_reason}")
if resposta.usage:
    print(f"Tokens de entrada: {resposta.usage.prompt_tokens}")
    print(f"Tokens de saída: {resposta.usage.completion_tokens}")