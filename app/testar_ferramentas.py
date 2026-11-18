"""Testes das ferramentas e da conversão de mensagens. Rode com: python app/testar_ferramentas.py"""

import json
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import ferramentas
from agente import mensagem_do_assistente
from ferramentas import calcular, cidades_monitoradas, executar_ferramenta, previsao_clima


def criar_banco_teste(pasta):
    """Cria um banco pequeno com datas relativas a hoje e aponta as ferramentas para ele."""
    caminho = Path(pasta) / "clima.db"
    hoje = datetime.now(ferramentas.FORTALEZA).date()

    def dia(deslocamento):
        return (hoje + timedelta(days=deslocamento)).isoformat()

    conexao = sqlite3.connect(caminho)
    conexao.executescript(
        """
        CREATE TABLE cidades (id INTEGER PRIMARY KEY, nome TEXT NOT NULL UNIQUE,
                              latitude REAL, longitude REAL);
        CREATE TABLE previsoes (id INTEGER PRIMARY KEY, cidade_id INTEGER NOT NULL, data TEXT NOT NULL,
                                temp_max REAL, temp_min REAL, chuva_mm REAL, coletado_em TEXT NOT NULL);
        INSERT INTO cidades (id, nome) VALUES (1, 'Fortaleza'), (2, 'São Paulo');
        """
    )
    linhas = [
        (1, dia(-1), 30.0, 25.0, 0.0),
        (1, dia(0), 31.0, 26.0, 0.0),
        (1, dia(1), 32.0, 26.5, 4.0),
        (1, dia(2), 30.5, 25.5, 12.0),
        (2, dia(0), 24.0, 15.0, 0.0),
    ]
    for cidade_id, data, t_max, t_min, chuva in linhas:
        conexao.execute(
            "INSERT INTO previsoes (cidade_id, data, temp_max, temp_min, chuva_mm, coletado_em) "
            "VALUES (?, ?, ?, ?, ?, '2026-11-20T12:00:00+00:00')",
            (cidade_id, data, t_max, t_min, chuva),
        )
    conexao.commit()
    conexao.close()

    ferramentas.CAMINHO_BANCO = caminho.resolve()
    return dia(0)


def testar_calcular_basico():
    assert calcular("2 + 2") == {"resultado": 4}
    assert calcular("(3 + 4) * 2") == {"resultado": 14}
    assert calcular("10 / 4") == {"resultado": 2.5}
    assert calcular("2480 * 0.15 + 37.5") == {"resultado": 409.5}


def testar_calcular_recusa_o_que_nao_e_conta():
    assert "erro" in calcular("__import__('os').getcwd()")
    assert "erro" in calcular("open('arquivo.txt')")
    assert "erro" in calcular("2 ** 9999")
    assert "erro" in calcular("(-8) ** 0.5")
    assert "erro" in calcular("1 / 0")
    assert "erro" in calcular("True + 1")
    assert "erro" in calcular("")
    assert "erro" in calcular("9" * 300)


def testar_previsao_filtra_datas_passadas():
    with tempfile.TemporaryDirectory() as pasta:
        hoje = criar_banco_teste(pasta)
        resultado = previsao_clima("Fortaleza", 7)

        assert resultado["cidade"] == "Fortaleza"
        assert len(resultado["previsoes"]) == 3
        assert resultado["previsoes"][0]["data"] == hoje


def testar_previsao_aceita_nome_sem_acento_e_limita_dias():
    with tempfile.TemporaryDirectory() as pasta:
        criar_banco_teste(pasta)
        assert previsao_clima("sao paulo")["cidade"] == "São Paulo"
        assert len(previsao_clima("fortaleza", 2)["previsoes"]) == 2


def testar_previsao_erros_viram_dados():
    with tempfile.TemporaryDirectory() as pasta:
        criar_banco_teste(pasta)

        desconhecida = previsao_clima("Manaus")
        assert "erro" in desconhecida
        assert "Fortaleza" in desconhecida["cidades_disponiveis"]

        assert "erro" in previsao_clima("")
        assert "erro" in previsao_clima("Fortaleza", "abc")


def testar_cidades_monitoradas():
    with tempfile.TemporaryDirectory() as pasta:
        criar_banco_teste(pasta)
        assert cidades_monitoradas() == {"cidades": ["Fortaleza", "São Paulo"]}


def testar_banco_ausente():
    with tempfile.TemporaryDirectory() as pasta:
        ferramentas.CAMINHO_BANCO = (Path(pasta) / "nao_existe.db").resolve()
        assert "erro" in previsao_clima("Fortaleza")
        assert "erro" in cidades_monitoradas()


def testar_executar_ferramenta_protege_contra_argumentos_ruins():
    assert "erro" in json.loads(executar_ferramenta("nao_existe", "{}"))
    assert "erro" in json.loads(executar_ferramenta("calcular", "{isso nao e json"))
    assert "erro" in json.loads(executar_ferramenta("calcular", '{"outro": 1}'))
    assert "erro" in json.loads(executar_ferramenta("calcular", "[1, 2]"))
    assert json.loads(executar_ferramenta("calcular", '{"expressao": "1 + 1"}')) == {"resultado": 2}


def testar_mensagem_preserva_assinatura_de_pensamento():
    chamada = SimpleNamespace(
        id="chamada_1",
        function=SimpleNamespace(name="calcular", arguments='{"expressao": "1 + 1"}'),
        extra_content={"google": {"thought_signature": "assinatura-de-teste"}},
    )
    mensagem = SimpleNamespace(content=None, tool_calls=[chamada])
    dados = mensagem_do_assistente(mensagem)

    assert dados["role"] == "assistant"
    assert "content" not in dados
    assert dados["tool_calls"][0]["id"] == "chamada_1"
    assert dados["tool_calls"][0]["function"]["name"] == "calcular"
    assert (
        dados["tool_calls"][0]["extra_content"]["google"]["thought_signature"]
        == "assinatura-de-teste"
    )


def testar_mensagem_sem_assinatura_tambem_funciona():
    chamada = SimpleNamespace(
        id="chamada_2",
        function=SimpleNamespace(name="cidades_monitoradas", arguments="{}"),
    )
    mensagem = SimpleNamespace(content="Vou consultar.", tool_calls=[chamada])
    dados = mensagem_do_assistente(mensagem)

    assert dados["content"] == "Vou consultar."
    assert "extra_content" not in dados["tool_calls"][0]


TESTES = [
    testar_calcular_basico,
    testar_calcular_recusa_o_que_nao_e_conta,
    testar_previsao_filtra_datas_passadas,
    testar_previsao_aceita_nome_sem_acento_e_limita_dias,
    testar_previsao_erros_viram_dados,
    testar_cidades_monitoradas,
    testar_banco_ausente,
    testar_executar_ferramenta_protege_contra_argumentos_ruins,
    testar_mensagem_preserva_assinatura_de_pensamento,
    testar_mensagem_sem_assinatura_tambem_funciona,
]


def main():
    caminho_original = ferramentas.CAMINHO_BANCO
    falhas = 0
    try:
        for teste in TESTES:
            try:
                teste()
                print(f"OK      {teste.__name__}")
            except AssertionError:
                falhas += 1
                print(f"FALHOU  {teste.__name__}")
    finally:
        ferramentas.CAMINHO_BANCO = caminho_original

    print(f"\n{len(TESTES) - falhas} de {len(TESTES)} testes passaram.")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()