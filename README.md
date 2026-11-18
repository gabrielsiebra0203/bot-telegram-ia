# 🤖 Assistente de IA para Telegram | Python + Gemini

Bot inteligente desenvolvido em Python, integrado à API do Google Gemini e ao Telegram, com memória persistente, execução de ferramentas, armazenamento de notas pessoais e controle de utilização.

Projeto desenvolvido durante meus estudos de Python, APIs de modelos de linguagem, automação e *tool calling*.

## 🚀 Funcionalidades

- **Integração com Telegram:** comunicação em tempo real utilizando `python-telegram-bot`.
- **Inteligência artificial:** respostas geradas pelo Google Gemini.
- **Memória persistente:** histórico individual de conversas armazenado em arquivos JSON.
- **Execução de ferramentas:** o agente pode solicitar funções Python para realizar operações.
- **Calculadora:** execução segura de operações matemáticas, sem utilizar `eval`.
- **Consulta de clima:** acesso a dados meteorológicos armazenados em SQLite.
- **Notas pessoais:** armazenamento e consulta de notas em SQLite, separadas por usuário.
- **Controle de utilização:** limite de mensagens por minuto e por dia.
- **Tratamento de erros:** controle de falhas da API, limites de execução e respostas inválidas.
- **Logs:** registro de operações com rotação de arquivos.
- **Testes automatizados:** validação de ferramentas, memória, limites e funcionamento do agente.

## 🛠️ Tecnologias utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python | Linguagem principal |
| Google Gemini | Modelo de inteligência artificial |
| OpenAI SDK | Comunicação com API compatível |
| python-telegram-bot | Integração com Telegram |
| SQLite | Armazenamento de notas e dados meteorológicos |
| JSON | Persistência do histórico de conversas |
| python-dotenv | Gerenciamento de variáveis de ambiente |
| asyncio | Execução de tarefas sem bloquear o bot |
| Git e GitHub | Versionamento e publicação |

## 🧠 Arquitetura

```text
Usuário no Telegram
        |
        v
app/bot_telegram.py
        |
        v
Controle de mensagens e histórico
        |
        v
app/agente.py
        |
        v
Google Gemini
        |
        +----> Calculadora
        |
        +----> Dados de clima (SQLite)
        |
        +----> Salvar notas (SQLite)
        |
        +----> Listar notas (SQLite)
        |
        v
Resposta enviada ao Telegram
```

O agente utiliza *tool calling* para identificar quando uma solicitação precisa de uma ferramenta. O Gemini seleciona a função, o Python executa a operação e o resultado é devolvido ao modelo para produzir a resposta final.

## 📂 Principais arquivos

```text
bot-telegram-ia/
│
├── app/
│   ├── bot_telegram.py
│   ├── agente.py
│   ├── conversa.py
│   ├── ferramentas.py
│   ├── notas.py
│   ├── limites.py
│   ├── llm_config.py
│   ├── comum.py
│   ├── chat_ferramentas.py
│   ├── listar_modelos.py
│   ├── testar_agente.py
│   ├── testar_conversa.py
│   └── testar_ferramentas.py
│
├── dados/                 # Gerado localmente e ignorado pelo Git
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## ⚙️ Instalação e configuração

### 1. Clonar o repositório

```bash
git clone URL_DO_REPOSITORIO
cd bot-telegram-ia
```

Substitua `URL_DO_REPOSITORIO` pelo endereço do projeto no GitHub.

### 2. Criar o ambiente virtual

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar as dependências

```powershell
python -m pip install -r requirements.txt
```

### 4. Configurar as variáveis de ambiente

```powershell
Copy-Item .env.example .env
```

Edite o arquivo `.env` e configure:

```env
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_API_KEY=sua-chave-gemini
LLM_MODELO=nome-do-modelo-disponivel
LLM_REASONING=low

TELEGRAM_BOT_TOKEN=seu-token-do-telegram
```

A chave do Gemini deve ser obtida no Google AI Studio. O token do Telegram deve ser criado por meio do BotFather.

Para consultar os modelos disponíveis:

```powershell
python app/listar_modelos.py flash
```

**Nunca publique suas chaves de API ou seu arquivo `.env`.**

### 5. Executar o bot

```powershell
python app/bot_telegram.py
```

Com o programa em execução, abra seu bot no Telegram e envie `/start`.

O bot utiliza *polling*, portanto o processo Python precisa permanecer executando para receber mensagens.

## 💬 Comandos do Telegram

| Comando | Função |
|---|---|
| `/start` | Inicia a interação com o assistente |
| `/ajuda` | Mostra os comandos disponíveis |
| `/historico` | Exibe mensagens recentes |
| `/limpar` | Apaga o histórico da conversa |

O comando `/limpar` não remove as notas pessoais armazenadas no SQLite.

## 🧪 Testes

O projeto possui testes que podem ser executados sem consumir chamadas da API do Gemini:

```powershell
python app/testar_conversa.py
python app/testar_ferramentas.py
python app/testar_agente.py
```

Também foram realizados testes manuais de integração com o Telegram, incluindo:

- Autenticação do bot.
- Respostas geradas pelo Gemini.
- Persistência do histórico após reiniciar o programa.
- Execução da calculadora.
- Salvamento e recuperação de notas.
- Isolamento de notas entre usuários.
- Comandos do Telegram.
- Limites de mensagens.

## 🔐 Segurança e limites

O projeto implementa medidas para reduzir riscos e controlar o consumo de recursos:

- Identificação dos usuários pelo ID fornecido pelo Telegram.
- Separação de históricos e notas por usuário.
- Consultas parametrizadas ao SQLite.
- Banco meteorológico acessado somente para leitura.
- Calculadora sem utilização de `eval`.
- Limites de tamanho das mensagens e das respostas das ferramentas.
- Limites de rodadas, chamadas de ferramentas e tempo de execução.
- Limite de 6 mensagens por minuto e 150 por dia, por usuário, mantido em memória durante a execução.
- Tratamento de erros e *timeout* de rede.
- Logs com rotação em `dados/agente.log`.

As variáveis sensíveis e os dados locais são excluídos do versionamento pelo `.gitignore`.

**Observação:** este é um projeto de estudos. Os limites de utilização são reiniciados quando o processo é reiniciado. Para disponibilização pública em produção, são recomendadas medidas adicionais de monitoramento, proteção de dados e infraestrutura.

## 📚 Aprendizados

Durante o desenvolvimento, pratiquei:

- Consumo de APIs REST e integração com LLMs.
- Desenvolvimento de agentes com *tool calling*.
- Programação assíncrona com `asyncio`.
- Integração com bots do Telegram.
- Persistência de dados com JSON e SQLite.
- Gerenciamento de variáveis de ambiente.
- Tratamento de exceções e limites de execução.
- Testes automatizados e versionamento com Git.

## 🎯 Próximas melhorias

- Implantação em servidor para funcionamento contínuo.
- Monitoramento de disponibilidade e falhas.
- Persistência dos limites de utilização.
- Testes automatizados específicos da integração com Telegram.
- Melhorias na experiência de interação com o usuário.

---

**Desenvolvido como projeto prático de estudos em Python, inteligência artificial e automação.**