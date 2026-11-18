"""Cria um banco clima.db com dados FICTÍCIOS, no mesmo formato do coletor, para testar as ferramentas.

Uso:
    python app/criar_dados_exemplo.py            cria dados/clima.db (se ainda não existir)
    python app/criar_dados_exemplo.py --forcar   recria o arquivo, apagando o que existir
"""

import random
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"
ARQUIVO_BANCO = PASTA_DADOS / "clima.db"
FORTALEZA = timezone(timedelta(hours=-3))

# nome, latitude, longitude, (faixa de temperatura), probabilidade de chuva
CIDADES = [
    ("Fortaleza", -3.73, -38.52, (25, 31), 0.35),
    ("São Paulo", -23.55, -46.63, (14, 27), 0.45),
    ("Recife", -8.05, -34.88, (23, 30), 0.50),
]

# Mesmas tabelas criadas pelo coletor-clima.
TABELAS = """
CREATE TABLE IF NOT EXISTS cidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS previsoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cidade_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    temp_max REAL,
    temp_min REAL,
    chuva_mm REAL,
    coletado_em TEXT NOT NULL,
    UNIQUE (cidade_id, data),
    FOREIGN KEY (cidade_id) REFERENCES cidades (id)
);
"""


def main():
    forcar = "--forcar" in sys.argv

    if ARQUIVO_BANCO.exists():
        if not forcar:
            sys.exit(
                f"{ARQUIVO_BANCO} já existe. Não vou sobrescrever (pode ser dado real). "
                "Use --forcar se quiser recriar."
            )
        ARQUIVO_BANCO.unlink()

    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    aleatorio = random.Random(42)
    hoje = datetime.now(FORTALEZA).date()
    coletado_em = datetime.now(timezone.utc).isoformat(timespec="seconds")

    conexao = sqlite3.connect(ARQUIVO_BANCO)
    try:
        conexao.executescript(TABELAS)
        for nome, latitude, longitude, (t_min, t_max), prob_chuva in CIDADES:
            cursor = conexao.execute(
                "INSERT INTO cidades (nome, latitude, longitude) VALUES (?, ?, ?)",
                (nome, latitude, longitude),
            )
            cidade_id = cursor.lastrowid

            for dia in range(7):
                data = (hoje + timedelta(days=dia)).isoformat()
                temp_min = round(t_min + aleatorio.uniform(-1.5, 1.5), 1)
                temp_max = round(t_max + aleatorio.uniform(-1.5, 1.5), 1)
                chuva = round(aleatorio.uniform(0.5, 25), 1) if aleatorio.random() < prob_chuva else 0.0
                conexao.execute(
                    "INSERT INTO previsoes (cidade_id, data, temp_max, temp_min, chuva_mm, coletado_em) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (cidade_id, data, temp_max, temp_min, chuva, coletado_em),
                )
        conexao.commit()
    finally:
        conexao.close()

    print(f"Banco de exemplo criado em {ARQUIVO_BANCO} (dados FICTÍCIOS).")


if __name__ == "__main__":
    main()