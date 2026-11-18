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
## Segurança e limites

- Ferramentas com o mínimo de poder: o banco de clima é aberto somente para leitura e a
  calculadora não usa `eval`.
- O usuário é identificado pelo programa (contexto), nunca pelo modelo.
- Limites: tamanho da mensagem, requisições por minuto e por dia, rodadas e chamadas de
  ferramenta por turno, tempo por turno, tamanho do resultado das ferramentas e *timeout* de rede.
- Logs com rotação em `dados/agente.log`. Por padrão só metadados; `DEPURAR=1` inclui conteúdo.

## Configuração

| Variável | Descrição |
|---|---|
| `LLM_BASE_URL` | Endereço da API compatível com OpenAI (padrão: Gemini) |
| `LLM_API_KEY` | Chave de API (nunca versionar) |
| `LLM_MODELO` | Nome do modelo (use `python app/listar_modelos.py flash`) |
| `LLM_REASONING` | Opcional: esforço de raciocínio (`low`, `medium`...) |