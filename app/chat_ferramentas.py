"""Chat no terminal com memória, ferramentas, limites de uso e logs."""

import openai

from agente import LimiteDoAgenteError, responder
from chat import mostrar_historico
from comum import PASTA_DADOS, configurar_log, mensagem_de_erro
from conversa import Conversa
from limites import LimitesDeUso
from llm_config import criar_cliente

USUARIO = "terminal"
MAX_MENSAGENS = 20
MAX_CARACTERES_ENTRADA = 1000
ARQUIVO_HISTORICO = PASTA_DADOS / "historico_ferramentas.json"

# 6 mensagens por minuto e 150 por dia. Ajuste conforme os limites do seu plano gratuito.
LIMITES = LimitesDeUso([(6, 60), (150, 86_400)])


def main():
    configurar_log()
    client, modelo, extras = criar_cliente()

    conversa = Conversa(max_mensagens=MAX_MENSAGENS)
    conversa.carregar(ARQUIVO_HISTORICO)

    print(f"Modelo: {modelo}")
    print("Ferramentas: calcular, previsao_clima, resumo_chuva, cidades_monitoradas, salvar_nota, listar_notas")
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

        if len(entrada) > MAX_CARACTERES_ENTRADA:
            print(f"Mensagem longa demais ({len(entrada)} caracteres). O máximo é {MAX_CARACTERES_ENTRADA}.")
            continue

        permitido, espera = LIMITES.permitir(USUARIO)
        if not permitido:
            print(f"Você está enviando mensagens rápido demais. Tente de novo em {int(espera) + 1}s.")
            continue

        conversa.adicionar_usuario(entrada)
        try:
            resultado = responder(client, modelo, extras, conversa, {"usuario": USUARIO})
        except LimiteDoAgenteError as erro:
            conversa.desfazer_ultima()
            print(f"Não consegui concluir: {erro}")
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