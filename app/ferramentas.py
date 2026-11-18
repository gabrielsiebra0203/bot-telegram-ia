"""Ferramentas que o modelo pode pedir para executar, com suas descrições (schemas)."""

import ast
import json
import logging
import math
import operator
import os
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

import notas
from comum import FORTALEZA

load_dotenv()

logger = logging.getLogger(__name__)

CAMINHO_BANCO = Path(
    os.environ.get("CLIMA_DB") or Path(__file__).resolve().parent.parent / "dados" / "clima.db"
).resolve()
LIMITE_SAIDA = 3000


# ------------------------------- calcular -------------------------------------

OPERADORES_BINARIOS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
OPERADORES_UNARIOS = {ast.USub: operator.neg, ast.UAdd: operator.pos}

LIMITE_EXPOENTE = 100
LIMITE_BITS = 2000
LIMITE_TAMANHO_EXPRESSAO = 200


def _avaliar(no):
    """Avalia um nó da árvore da expressão, aceitando só números e operadores aritméticos."""
    if isinstance(no, ast.Constant) and type(no.value) in (int, float):
        return no.value

    if isinstance(no, ast.BinOp) and type(no.op) in OPERADORES_BINARIOS:
        esquerda = _avaliar(no.left)
        direita = _avaliar(no.right)
        if isinstance(no.op, ast.Pow) and abs(direita) > LIMITE_EXPOENTE:
            raise ValueError("expoente grande demais")
        resultado = OPERADORES_BINARIOS[type(no.op)](esquerda, direita)
    elif isinstance(no, ast.UnaryOp) and type(no.op) in OPERADORES_UNARIOS:
        resultado = OPERADORES_UNARIOS[type(no.op)](_avaliar(no.operand))
    else:
        raise ValueError("expressão não permitida")

    if isinstance(resultado, complex):
        raise ValueError("o resultado não é um número real")
    if isinstance(resultado, float) and not math.isfinite(resultado):
        raise ValueError("resultado fora do alcance")
    if isinstance(resultado, int) and resultado.bit_length() > LIMITE_BITS:
        raise ValueError("resultado grande demais")
    return resultado


def calcular(expressao):
    """Calcula uma expressão aritmética de forma segura (sem usar eval)."""
    if not isinstance(expressao, str) or not expressao.strip():
        return {"erro": "Informe uma expressão matemática."}
    if len(expressao) > LIMITE_TAMANHO_EXPRESSAO:
        return {"erro": "Expressão longa demais."}

    try:
        arvore = ast.parse(expressao.strip(), mode="eval")
        resultado = _avaliar(arvore.body)
    except SyntaxError:
        return {"erro": "Expressão inválida. Use números, + - * / // % ** e parênteses."}
    except ZeroDivisionError:
        return {"erro": "Divisão por zero."}
    except (ValueError, OverflowError, RecursionError) as erro:
        return {"erro": f"Não foi possível calcular: {erro}"}

    if isinstance(resultado, float):
        resultado = round(resultado, 10)
    return {"resultado": resultado}


# ---------------------------- consultas ao banco ------------------------------

def _normalizar(texto):
    """Minúsculas e sem acentos, para comparar nomes de cidades."""
    decomposto = unicodedata.normalize("NFD", texto)
    sem_acentos = "".join(c for c in decomposto if unicodedata.category(c) != "Mn")
    return sem_acentos.lower().strip()


def _consultar(sql, parametros=()):
    """Executa um SELECT no banco de clima, aberto SOMENTE para leitura."""
    if not CAMINHO_BANCO.exists():
        raise FileNotFoundError(CAMINHO_BANCO)
    conexao = sqlite3.connect(f"{CAMINHO_BANCO.as_uri()}?mode=ro", uri=True)
    conexao.row_factory = sqlite3.Row
    try:
        return [dict(linha) for linha in conexao.execute(sql, parametros).fetchall()]
    finally:
        conexao.close()


def _normalizar_dias(dias):
    """Converte 'dias' para inteiro entre 1 e 7. Levanta ValueError se não for número."""
    try:
        valor = int(dias)
    except (TypeError, ValueError):
        raise ValueError("O parâmetro 'dias' deve ser um número inteiro.") from None
    return max(1, min(valor, 7))


def _localizar_cidade(nome):
    """Procura a cidade pelo nome. Devolve (cidade, None) ou (None, dicionário de erro)."""
    cidades = _consultar("SELECT id, nome FROM cidades ORDER BY nome")
    procurada = _normalizar(nome)
    encontradas = [c for c in cidades if procurada in _normalizar(c["nome"])]

    if not encontradas:
        return None, {
            "erro": f"Cidade '{nome}' não encontrada no banco.",
            "cidades_disponiveis": [c["nome"] for c in cidades],
        }
    if len(encontradas) > 1:
        return None, {
            "erro": "Mais de uma cidade corresponde ao nome informado.",
            "opcoes": [c["nome"] for c in encontradas],
        }
    return encontradas[0], None


def _previsoes_futuras(cidade_id, dias):
    """Devolve as previsões de hoje em diante (no horário de Fortaleza)."""
    hoje = datetime.now(FORTALEZA).date().isoformat()
    return _consultar(
        """
        SELECT data, temp_min, temp_max, chuva_mm, coletado_em
        FROM previsoes
        WHERE cidade_id = ? AND data >= ?
        ORDER BY data
        LIMIT ?
        """,
        (cidade_id, hoje, dias),
    )


def cidades_monitoradas():
    """Lista as cidades que têm previsão no banco."""
    try:
        cidades = _consultar("SELECT nome FROM cidades ORDER BY nome")
    except FileNotFoundError:
        return {"erro": "Banco de dados de clima não encontrado."}
    except sqlite3.Error as erro:
        return {"erro": f"Falha ao ler o banco de dados: {erro}"}
    return {"cidades": [cidade["nome"] for cidade in cidades]}


def previsao_clima(cidade, dias=3):
    """Devolve a previsão (a partir de hoje) de uma cidade do banco."""
    if not isinstance(cidade, str) or not cidade.strip():
        return {"erro": "Informe o nome da cidade."}
    try:
        dias = _normalizar_dias(dias)
    except ValueError as erro:
        return {"erro": str(erro)}

    try:
        escolhida, problema = _localizar_cidade(cidade)
        if problema:
            return problema
        linhas = _previsoes_futuras(escolhida["id"], dias)
    except FileNotFoundError:
        return {"erro": "Banco de dados de clima não encontrado."}
    except sqlite3.Error as erro:
        return {"erro": f"Falha ao ler o banco de dados: {erro}"}

    if not linhas:
        return {
            "cidade": escolhida["nome"],
            "previsoes": [],
            "aviso": "Não há previsões futuras registradas para esta cidade.",
        }

    return {
        "cidade": escolhida["nome"],
        "coletado_em_utc": max(linha["coletado_em"] for linha in linhas),
        "previsoes": [
            {
                "data": linha["data"],
                "temp_min_c": linha["temp_min"],
                "temp_max_c": linha["temp_max"],
                "chuva_mm": linha["chuva_mm"],
            }
            for linha in linhas
        ],
    }


def resumo_chuva(cidade, dias=7):
    """Resume a chuva prevista (total, dias com chuva e dia mais chuvoso) para uma cidade."""
    if not isinstance(cidade, str) or not cidade.strip():
        return {"erro": "Informe o nome da cidade."}
    try:
        dias = _normalizar_dias(dias)
    except ValueError as erro:
        return {"erro": str(erro)}

    try:
        escolhida, problema = _localizar_cidade(cidade)
        if problema:
            return problema
        linhas = _previsoes_futuras(escolhida["id"], dias)
    except FileNotFoundError:
        return {"erro": "Banco de dados de clima não encontrado."}
    except sqlite3.Error as erro:
        return {"erro": f"Falha ao ler o banco de dados: {erro}"}

    if not linhas:
        return {
            "cidade": escolhida["nome"],
            "aviso": "Não há previsões futuras registradas para esta cidade.",
        }

    chuvas = [(linha["data"], linha["chuva_mm"] or 0.0) for linha in linhas]
    data_maxima, chuva_maxima = max(chuvas, key=lambda item: item[1])

    return {
        "cidade": escolhida["nome"],
        "periodo": {"de": linhas[0]["data"], "ate": linhas[-1]["data"]},
        "total_chuva_mm": round(sum(chuva for _, chuva in chuvas), 1),
        "dias_com_chuva": sum(1 for _, chuva in chuvas if chuva > 0),
        "dia_mais_chuvoso": (
            {"data": data_maxima, "chuva_mm": chuva_maxima} if chuva_maxima > 0 else None
        ),
        "coletado_em_utc": max(linha["coletado_em"] for linha in linhas),
    }


# ------------------------ descrição das ferramentas ---------------------------

FERRAMENTAS = [
    {
        "type": "function",
        "function": {
            "name": "calcular",
            "description": (
                "Calcula uma expressão matemática com exatidão. Use sempre que a resposta "
                "depender de uma conta. Aceita números (use ponto como separador decimal), "
                "+ - * / // % ** e parênteses. Porcentagens devem ser escritas como "
                "multiplicação, por exemplo 15% de 200 = 200 * 0.15."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expressao": {
                        "type": "string",
                        "description": "A expressão matemática, por exemplo: (12.5 + 3) * 4",
                    }
                },
                "required": ["expressao"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "previsao_clima",
            "description": (
                "Consulta a previsão do tempo (temperatura mínima e máxima em °C e chuva em mm) "
                "de uma cidade, dia a dia, a partir de hoje, usando os dados já coletados e "
                "guardados no banco de dados. Só funciona para as cidades monitoradas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cidade": {"type": "string", "description": "Nome da cidade, por exemplo: Fortaleza"},
                    "dias": {
                        "type": "integer",
                        "description": "Quantidade de dias de previsão, de 1 a 7. Padrão: 3.",
                    },
                },
                "required": ["cidade"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resumo_chuva",
            "description": (
                "Resume a chuva prevista para uma cidade: total em mm, quantidade de dias com "
                "chuva e o dia mais chuvoso. Use para perguntas como 'vai chover muito esta semana?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cidade": {"type": "string", "description": "Nome da cidade, por exemplo: Recife"},
                    "dias": {
                        "type": "integer",
                        "description": "Quantidade de dias a considerar, de 1 a 7. Padrão: 7.",
                    },
                },
                "required": ["cidade"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cidades_monitoradas",
            "description": "Lista as cidades para as quais existe previsão do tempo no banco de dados.",
        },
    },
    {
        "type": "function",
        "function": {
            "name": "salvar_nota",
            "description": (
                "Guarda uma nota curta (até 300 caracteres) do usuário para consulta futura. "
                "Use SOMENTE quando o usuário pedir explicitamente para anotar ou lembrar de algo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "O texto da nota."}
                },
                "required": ["texto"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_notas",
            "description": "Lista as notas que o usuário guardou anteriormente, da mais recente para a mais antiga.",
        },
    },
]

FUNCOES = {
    "calcular": calcular,
    "previsao_clima": previsao_clima,
    "resumo_chuva": resumo_chuva,
    "cidades_monitoradas": cidades_monitoradas,
    "salvar_nota": notas.salvar_nota,
    "listar_notas": notas.listar_notas,
}

# Ferramentas que precisam saber QUEM está pedindo. O contexto é montado pelo programa.
COM_CONTEXTO = {"salvar_nota", "listar_notas"}


def _json(dados):
    return json.dumps(dados, ensure_ascii=False)


def executar_ferramenta(nome, argumentos_json, contexto=None):
    """Executa a ferramenta pedida pelo modelo e devolve o resultado como texto JSON.

    O contexto (por exemplo, {"usuario": "123"}) vem do programa e é entregue só às
    ferramentas que precisam dele. O modelo não consegue informá-lo nem sobrescrevê-lo.
    Nunca levanta exceção: qualquer problema vira {"erro": "..."}.
    """
    funcao = FUNCOES.get(nome)
    if funcao is None:
        return _json({"erro": f"Ferramenta desconhecida: {nome}"})

    try:
        argumentos = json.loads(argumentos_json or "{}")
    except json.JSONDecodeError:
        return _json({"erro": "Os argumentos não são um JSON válido."})
    if not isinstance(argumentos, dict):
        return _json({"erro": "Os argumentos devem ser um objeto JSON."})
    if "contexto" in argumentos:
        return _json({"erro": "Argumento não permitido: contexto."})

    try:
        if nome in COM_CONTEXTO:
            resultado = funcao(**argumentos, contexto=contexto or {})
        else:
            resultado = funcao(**argumentos)
    except TypeError:
        return _json({"erro": "Argumentos inválidos para esta ferramenta."})
    except Exception:
        logger.exception("Falha inesperada na ferramenta %s", nome)
        return _json({"erro": "Falha interna ao executar a ferramenta."})

    texto = _json(resultado)
    if len(texto) > LIMITE_SAIDA:
        texto = _json(
            {"aviso": "Resultado truncado por ser muito longo.", "parcial": texto[:LIMITE_SAIDA]}
        )
    return texto