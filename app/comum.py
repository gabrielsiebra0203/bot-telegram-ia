"""Funções compartilhadas: system prompt, mensagens de erro e configuração de log."""

import logging
import os
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

import openai

FORTALEZA = timezone(timedelta(hours=-3))
PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"


def montar_sistema():
    """Monta o system prompt, incluindo a data e a hora atuais em Fortaleza."""
    agora = datetime.now(FORTALEZA).strftime("%d/%m/%Y %H:%M")
    return (
        "Você é um assistente prestativo. Responda sempre em português do Brasil, "
        "de forma clara e concisa. Se não souber algo, diga que não sabe.\n"
        f"Data e hora atuais em Fortaleza: {agora}."
    )


def mensagem_de_erro(erro):
    """Traduz uma exceção da API em uma mensagem amigável."""
    if isinstance(erro, openai.AuthenticationError):
        return "Chave de API inválida. Confira o arquivo .env."
    if isinstance(erro, openai.RateLimitError):
        return "Limite do plano gratuito atingido. Espere um pouco e tente de novo."
    if isinstance(erro, openai.APITimeoutError):
        return "A API demorou demais para responder. Tente de novo."
    if isinstance(erro, openai.APIConnectionError):
        return "Sem conexão com a API. Verifique a internet e o LLM_BASE_URL."
    if isinstance(erro, openai.APIStatusError):
        return f"A API recusou o pedido (código {erro.status_code}): {erro.message}"
    return f"Erro inesperado: {erro}"


def configurar_log(nome_arquivo="agente.log"):
    """Configura o log: tela (só a mensagem) e arquivo com rotação (com data, nível e origem).

    Por padrão registra só metadados. Com a variável de ambiente DEPURAR=1 registra também
    o conteúdo (argumentos e resultados de ferramentas), que pode conter dados pessoais.
    """
    nivel = logging.DEBUG if os.environ.get("DEPURAR") == "1" else logging.INFO

    raiz = logging.getLogger()
    raiz.setLevel(nivel)
    raiz.handlers.clear()

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(message)s"))
    raiz.addHandler(console)

    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    arquivo = RotatingFileHandler(
        PASTA_DADOS / nome_arquivo, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    arquivo.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    raiz.addHandler(arquivo)

    for biblioteca in ("httpx", "httpcore", "openai"):
        logging.getLogger(biblioteca).setLevel(logging.WARNING)