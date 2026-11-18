"""Lista os modelos disponíveis no provedor configurado (se ele suportar a listagem).

Uso:
    python app/listar_modelos.py            lista tudo
    python app/listar_modelos.py flash      lista só os nomes que contêm 'flash'
"""

import sys

import openai

from llm_config import criar_cliente


def main():
    filtro = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    client, _, _ = criar_cliente()

    try:
        nomes = sorted(modelo.id for modelo in client.models.list())
    except openai.OpenAIError as erro:
        sys.exit(f"Não foi possível listar os modelos: {erro}")

    for nome in nomes:
        if filtro in nome.lower():
            print(nome)


if __name__ == "__main__":
    main()