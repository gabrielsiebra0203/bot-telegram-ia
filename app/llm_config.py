"""Configuração do cliente de LLM, lida do ambiente. Reaproveitada pelos outros scripts."""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OBRIGATORIAS = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODELO")


def criar_cliente():
    """Devolve (cliente, modelo, parametros_extras) a partir das variáveis de ambiente."""
    faltando = [nome for nome in OBRIGATORIAS if not os.environ.get(nome)]
    if faltando:
        sys.exit(f"Variáveis ausentes no .env: {', '.join(faltando)} (veja .env.example).")

    client = OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
    )

    extras = {}
    esforco = os.environ.get("LLM_REASONING", "").strip()
    if esforco:
        extras["reasoning_effort"] = esforco

    return client, os.environ["LLM_MODELO"], extras