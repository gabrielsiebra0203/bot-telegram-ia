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
```

## Configuração

| Variável | Descrição |
|---|---|
| `LLM_BASE_URL` | Endereço da API compatível com OpenAI (padrão: Gemini) |
| `LLM_API_KEY` | Chave de API (nunca versionar) |
| `LLM_MODELO` | Nome do modelo (use `python app/listar_modelos.py flash`) |
| `LLM_REASONING` | Opcional: esforço de raciocínio (`low`, `medium`...) |