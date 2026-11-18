# Bot de Telegram com IA

Agente de IA com ferramentas próprias, acessível pelo Telegram.

> Projeto em construção, feito durante os estudos de APIs de LLM e tool calling.

## Como rodar

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cp .env.example .env          # no PowerShell: Copy-Item .env.example .env
python app/listar_modelos.py flash
python app/perguntar.py
python app/chat.py             # chat com memória
python app/testar_conversa.py  # testes (não usam a API)
python app/criar_dados_exemplo.py   # banco de clima com dados fictícios, para testes
python app/testar_ferramentas.py    # testes das ferramentas (não usam a API)
python app/chat_ferramentas.py      # chat com ferramentas (calculadora e previsão do tempo)
python app/chat_ferramentas.py   # agente com ferramentas, limites de uso e logs
python app/testar_agente.py      # testes dos limites, das notas e do loop do agente (sem API)
```

## Configuração

| Variável | Descrição |
|---|---|
| `LLM_BASE_URL` | Endereço da API compatível com OpenAI (padrão: Gemini) |
| `LLM_API_KEY` | Chave de API (nunca versionar) |
| `LLM_MODELO` | Nome do modelo (use `python app/listar_modelos.py flash`) |
| `LLM_REASONING` | Opcional: esforço de raciocínio (`low`, `medium`...) |