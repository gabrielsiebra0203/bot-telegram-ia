
"""Bot Telegram integrado ao agente de IA com memória e ferramentas."""

import asyncio
import logging
import os
from pathlib import Path

import openai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from agente import LimiteDoAgenteError, responder
from comum import PASTA_DADOS, configurar_log, mensagem_de_erro
from conversa import Conversa
from limites import LimitesDeUso
from llm_config import criar_cliente


RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=RAIZ / ".env")

PASTA_HISTORICOS = PASTA_DADOS / "telegram"
MAX_MENSAGENS = 20
MAX_CARACTERES = 1000

LIMITES = LimitesDeUso([(6, 60), (150, 86_400)])
CONVERSAS = {}
LOCKS = {}


def obter_lock(usuario):
    if usuario not in LOCKS:
        LOCKS[usuario] = asyncio.Lock()
    return LOCKS[usuario]


def obter_conversa(usuario):
    if usuario not in CONVERSAS:
        conversa = Conversa(max_mensagens=MAX_MENSAGENS)
        conversa.carregar(PASTA_HISTORICOS / f"{usuario}.json")
        CONVERSAS[usuario] = conversa

    return CONVERSAS[usuario]


def salvar_conversa(usuario, conversa):
    conversa.salvar(PASTA_HISTORICOS / f"{usuario}.json")


async def enviar_texto(mensagem, texto):
    """Divide respostas grandes para respeitar o limite do Telegram."""
    for inicio in range(0, len(texto), 4000):
        await mensagem.reply_text(texto[inicio:inicio + 4000])


async def iniciar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Eu sou seu assistente de IA.\n\n"
        "Posso conversar, fazer cálculos, consultar dados de clima "
        "e guardar suas notas.\n\n"
        "Envie uma pergunta para começar!\n"
        "Use /ajuda para ver os comandos."
    )


async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandos disponíveis:\n\n"
        "/start - Iniciar o bot\n"
        "/ajuda - Mostrar esta ajuda\n"
        "/historico - Ver mensagens recentes\n"
        "/limpar - Apagar o histórico da conversa\n\n"
        "Você também pode enviar mensagens normalmente."
    )


async def historico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = str(update.effective_user.id)

    async with obter_lock(usuario):
        conversa = obter_conversa(usuario)
        mensagens = conversa.mensagens[-10:]

        if not mensagens:
            resposta = "Seu histórico está vazio."
        else:
            partes = ["Últimas mensagens:\n"]
            for item in mensagens:
                papel = "Você" if item["role"] == "user" else "IA"
                partes.append(f"{papel}: {item['content'][:500]}")
            resposta = "\n\n".join(partes)

    await enviar_texto(update.message, resposta)


async def limpar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = str(update.effective_user.id)

    async with obter_lock(usuario):
        conversa = obter_conversa(usuario)
        conversa.limpar()
        salvar_conversa(usuario, conversa)

    await update.message.reply_text(
        "Histórico da conversa apagado!\n"
        "Suas notas pessoais continuam salvas."
    )


async def receber_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = str(update.effective_user.id)
    texto = update.message.text.strip()

    if not texto:
        return

    if len(texto) > MAX_CARACTERES:
        await update.message.reply_text(
            f"Sua mensagem é muito longa. Máximo: {MAX_CARACTERES} caracteres."
        )
        return

    async with obter_lock(usuario):
        permitido, espera = LIMITES.permitir(usuario)

        if not permitido:
            await update.message.reply_text(
                f"Limite de mensagens atingido. Tente novamente em {int(espera) + 1}s."
            )
            return

        conversa = obter_conversa(usuario)
        conversa.adicionar_usuario(texto)

        client = context.application.bot_data["client"]
        modelo = context.application.bot_data["modelo"]
        extras = context.application.bot_data["extras"]

        try:
            resultado = await asyncio.to_thread(
                responder,
                client,
                modelo,
                extras,
                conversa,
                {"usuario": usuario},
            )

        except LimiteDoAgenteError as erro:
            conversa.desfazer_ultima()
            await update.message.reply_text(f"Não consegui concluir: {erro}")
            return

        except openai.OpenAIError as erro:
            conversa.desfazer_ultima()
            await update.message.reply_text(mensagem_de_erro(erro))
            return

        except Exception:
            conversa.desfazer_ultima()
            logging.exception("Erro inesperado no agente")
            await update.message.reply_text(
                "Ocorreu um erro inesperado. Tente novamente."
            )
            return

        if not resultado.texto or not resultado.texto.strip():
            conversa.desfazer_ultima()
            await update.message.reply_text(
                "O modelo retornou uma resposta vazia. Tente novamente."
            )
            return

        conversa.adicionar_assistente(resultado.texto)
        salvar_conversa(usuario, conversa)

    await enviar_texto(update.message, resultado.texto)


async def tratar_erro(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(
        "Erro do Telegram",
        exc_info=(
            type(context.error),
            context.error,
            context.error.__traceback__,
        ) if context.error else None,
    )


def main():
    configurar_log()

    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado no .env")

    client, modelo, extras = criar_cliente()

    app = Application.builder().token(token).build()

    app.bot_data["client"] = client
    app.bot_data["modelo"] = modelo
    app.bot_data["extras"] = extras

    app.add_handler(CommandHandler("start", iniciar))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("historico", historico))
    app.add_handler(CommandHandler("limpar", limpar))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, receber_mensagem)
    )

    app.add_error_handler(tratar_erro)

    print(f"Bot iniciado com o modelo: {modelo}")
    print("Aguardando mensagens no Telegram...")

    app.run_polling()


if __name__ == "__main__":
    main()
