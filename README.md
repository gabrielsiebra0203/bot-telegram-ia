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

| Tecnologia | Finalidade |
|---|---|
| Python 3.13 | Linguagem principal do projeto |
| Google Gemini | Modelo de inteligência artificial |
| OpenAI SDK | Integração com a API compatível do Gemini |
| python-telegram-bot | Comunicação com usuários do Telegram |
| SQLite | Armazenamento de notas e dados meteorológicos |
| JSON | Persistência dos históricos de conversas |
| python-dotenv | Configuração de variáveis de ambiente |
| asyncio | Processamento assíncrono |
| Docker | Containerização da aplicação |
| Docker Compose | Gerenciamento e reinicialização do container |
| Ubuntu Server | Sistema operacional da VPS |
| Contabo VPS | Hospedagem da aplicação |
| Git e GitHub | Versionamento e publicação do código |

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

## 🐳 Executando com Docker

O projeto possui um `Dockerfile` e um arquivo `compose.yaml` para executar o bot em um container Docker, sem a necessidade de instalar as dependências Python diretamente no servidor.

### 1. Configurar as variáveis de ambiente

Crie o arquivo `.env` a partir de `.env.example` e preencha as credenciais do Telegram e do Gemini.

O arquivo `.env` contém informações sensíveis e não deve ser enviado ao GitHub.

### 2. Construir a imagem

```bash
docker build -t bot-telegram-ia:1.0 .
```

A imagem utiliza Python 3.13 e executa a aplicação com um usuário não privilegiado (`botuser`).

### 3. Iniciar o container

```bash
docker compose up -d
```

O bot será iniciado em segundo plano, utilizando o sistema de *polling* do Telegram.

### 4. Verificar o funcionamento

```bash
docker compose ps
docker compose logs --tail=30 bot
```

Para acompanhar os logs em tempo real:

```bash
docker compose logs -f bot
```

Para interromper somente o bot:

```bash
docker compose stop bot
```

## ☁️ Deploy em VPS Contabo

O assistente foi implantado em uma VPS Contabo com Ubuntu Server e Docker, permitindo sua execução independentemente do computador de desenvolvimento.

### Arquitetura de produção

```text
Usuário no Telegram
        |
        v
Telegram Bot API
        |
        v
VPS Contabo (Ubuntu Server)
        |
        v
Docker Compose
        |
        v
Container Python (botuser)
        |
        +----> Google Gemini
        |
        +----> Calculadora
        |
        +----> SQLite (notas e clima)
        |
        +----> JSON (históricos)
        |
        v
Resposta enviada ao Telegram
```

### Processo de implantação

As principais etapas realizadas foram:

1. Configuração do acesso SSH à VPS.
2. Instalação e validação do Docker e Docker Compose.
3. Clonagem do repositório GitHub no servidor.
4. Configuração das variáveis de ambiente.
5. Construção da imagem Docker.
6. Preparação dos diretórios de armazenamento.
7. Validação das permissões de escrita do container.
8. Transferência e verificação do banco de clima SQLite.
9. Inicialização da aplicação com Docker Compose.
10. Testes reais de comunicação com Telegram e Gemini.

### Persistência de dados

O Docker Compose utiliza um volume do tipo *bind mount*:

```yaml
volumes:
  - ./dados:/app/dados
```

Esse mapeamento permite armazenar os dados fora do sistema de arquivos interno do container.

Entre os dados persistidos estão:

- Históricos individuais de conversas em JSON.
- Notas pessoais armazenadas em SQLite.
- Banco meteorológico SQLite.
- Arquivos de log da aplicação.

A persistência foi validada por meio de testes de escrita, leitura e reinicialização do container.

### Reinicialização automática

O serviço utiliza a política:

```yaml
restart: unless-stopped
```

Essa configuração permite que o Docker reinicie o container automaticamente em situações previstas pela política, como falhas do processo ou reinicialização do serviço Docker, desde que ele não tenha sido interrompido manualmente.

### Atualização da aplicação

Para atualizar o código no servidor, é necessário obter a nova versão do repositório, reconstruir a imagem e recriar o container:

```bash
git pull origin main
docker build -t bot-telegram-ia:1.0 .
docker compose up -d --force-recreate
```

Os comandos devem ser executados no diretório do projeto, após verificar as alterações e preservar os arquivos locais de configuração e dados.

**Observação:** o bot utiliza *polling*. Portanto, somente uma instância deve consumir atualizações do Telegram utilizando o mesmo token.

### Segurança da implantação

- Execução do processo Python com usuário não privilegiado.
- Credenciais mantidas em arquivo `.env` fora do Git.
- Diretórios de dados persistidos no servidor.
- Proteção adicional do container com `no-new-privileges`.
- Sem necessidade de expor portas públicas para receber mensagens do Telegram.
- Isolamento da aplicação em relação aos demais serviços da VPS.

A implantação foi realizada como parte de um projeto prático de estudos em Python, inteligência artificial, Docker e infraestrutura Linux.
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

- Implementar monitoramento de disponibilidade e alertas de falhas.
- Persistir os limites de utilização em banco de dados.
- Ampliar os testes automatizados da integração com Telegram.
- Implementar um processo automatizado de deploy (CI/CD).
- Melhorar o gerenciamento de logs e observabilidade.
- Implementar controle de acesso para utilização do bot em produção.

**Desenvolvido como projeto prático de estudos em Python, inteligência artificial e automação.**