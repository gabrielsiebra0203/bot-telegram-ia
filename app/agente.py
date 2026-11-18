"""Núcleo do agente: conversa com o modelo e executa as ferramentas que ele pedir."""

import logging
import time
from dataclasses import dataclass, field

import openai

from chat import montar_sistema
from ferramentas import FERRAMENTAS, executar_ferramenta

MAX_TOKENS = 1000
MAX_RODADAS = 5
TENTATIVAS = 3

REGRAS_FERRAMENTAS = (
    "Você tem ferramentas para consultar a previsão do tempo guardada no banco de dados "
    "e para fazer cálculos. Use-as sempre que a pergunta depender desses dados ou de contas exatas. "
    "Nunca invente dados: se uma ferramenta não trouxer a informação, diga isso com clareza. "
    "Ao informar uma previsão, mencione de quando são os dados."
)


class LimiteDeRodadasError(Exception):
    """O modelo pediu ferramentas além do limite permitido."""


@dataclass
class Resultado:
    """O que o agente produziu em um turno."""

    texto: str = ""
    finish_reason: str = ""
    tokens_entrada: int = 0
    tokens_saida: int = 0
    ferramentas: list = field(default_factory=list)


def mensagem_do_assistente(mensagem):
    """Converte a mensagem do modelo em dicionário, preservando o extra_content.

    O Gemini 3 coloca a assinatura do raciocínio (thought_signature) em
    tool_calls[].extra_content, e ela precisa voltar na próxima chamada.
    """
    dados = {"role": "assistant"}
    if mensagem.content:
        dados["content"] = mensagem.content

    chamadas = []
    for chamada in mensagem.tool_calls or []:
        item = {
            "id": chamada.id,
            "type": "function",
            "function": {
                "name": chamada.function.name,
                "arguments": chamada.function.arguments,
            },
        }
        extra = getattr(chamada, "extra_content", None)
        if extra:
            item["extra_content"] = extra
        chamadas.append(item)

    if chamadas:
        dados["tool_calls"] = chamadas
    return dados


def chamar_modelo(client, modelo, extras, mensagens):
    """Envia as mensagens e as ferramentas ao modelo. Se o limite for atingido, espera e tenta de novo."""
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            return client.chat.completions.create(
                model=modelo,
                max_tokens=MAX_TOKENS,
                messages=mensagens,
                tools=FERRAMENTAS,
                tool_choice="auto",
                **extras,
            )
        except openai.RateLimitError:
            if tentativa == TENTATIVAS:
                raise
            espera = 2 ** tentativa
            logging.info("(limite atingido, tentando de novo em %ds...)", espera)
            time.sleep(espera)


def responder(client, modelo, extras, conversa):
    """Responde ao último pedido da conversa, executando as ferramentas que o modelo pedir."""
    sistema = f"{montar_sistema()}\n{REGRAS_FERRAMENTAS}"
    mensagens = conversa.para_api(sistema)
    resultado = Resultado()

    for _ in range(MAX_RODADAS):
        resposta = chamar_modelo(client, modelo, extras, mensagens)
        if resposta.usage:
            resultado.tokens_entrada += resposta.usage.prompt_tokens
            resultado.tokens_saida += resposta.usage.completion_tokens

        escolha = resposta.choices[0]
        mensagem = escolha.message

        if not mensagem.tool_calls:
            resultado.texto = mensagem.content or ""
            resultado.finish_reason = escolha.finish_reason
            return resultado

        mensagens.append(mensagem_do_assistente(mensagem))

        for chamada in mensagem.tool_calls:
            nome = chamada.function.name
            argumentos = chamada.function.arguments
            saida = executar_ferramenta(nome, argumentos)
            resultado.ferramentas.append(nome)

            resumo = saida if len(saida) <= 110 else saida[:110] + "..."
            logging.info("  [ferramenta] %s(%s) -> %s", nome, argumentos, resumo)

            mensagens.append({"role": "tool", "tool_call_id": chamada.id, "content": saida})

    raise LimiteDeRodadasError(f"O modelo pediu ferramentas por mais de {MAX_RODADAS} rodadas.")