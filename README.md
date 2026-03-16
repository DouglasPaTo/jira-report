# Jira Reports

Sistema de geração de relatórios de tickets do Jira com filtros e exportação HTML.

> **Compatibilidade**: Desenvolvido e testado em **Ubuntu Linux**. Pode funcionar em outras distribuições Linux, mas não foi testado em Windows ou macOS.

## Quick Start

```bash
# Primeira vez: Setup inicial
./setup.sh

# Iniciar o servidor
./start.sh

# Parar o servidor
./stop.sh

# Reiniciar o servidor
./restart.sh

# Acessar
http://localhost:8000
```

## Requisitos

- Ubuntu Linux (ou distribuição Linux baseada em Debian)
- Python 3.10+
- Acesso à internet (para API do Jira)

## Configuração

1. Edite o arquivo `.env` com suas credenciais do Jira:
   - `JIRA_URL` - URL do Jira (ex: https://kingit.atlassian.net)
   - `JIRA_EMAIL` - Seu email
   - `JIRA_API_TOKEN` - Token API do Jira
   - `JIRA_PROJECT` - Key do projeto no Jira (padrão: SUP)
   - `SECRET_KEY` - Chave para sessões (opcional)

2. Execute `./setup.sh` se for a primeira vez

**Nota**: O sistema busca tickets do projeto configurado em `JIRA_PROJECT`. O projeto precisa existir no Jira e deve ter tickets com status "Done".

## Uso

1. Acesse http://localhost:8000
2. Faça login (padrão: admin/admin)
3. Use os filtros para selecionar tickets
4. Clique em "Atualizar Tudo" para buscar tickets do Jira
5. Exporte para HTML com "Exportar HTML"

## Estrutura do Projeto

```
new-jreport/
├── app/                    # Código fonte
│   ├── main.py            # Entry point do FastAPI
│   ├── routers/          # Rotas (web.py, auth.py)
│   ├── services/         # Integração Jira
│   ├── db/               # Banco de dados SQLite
│   ├── templates/        # Templates HTML
│   ├── static/           # CSS, imagens, favicon
│   └── jira_reports.db  # Banco de dados
├── .env                  # Variáveis de ambiente
├── setup.sh             # Setup inicial (primeira vez)
├── start.sh             # Iniciar servidor
├── stop.sh              # Parar servidor
└── restart.sh           # Reiniciar servidor
```

## Scripts

| Script | Descrição |
|--------|-----------|
| `./setup.sh` | Configura ambiente virtual e dependências (execute uma vez) |
| `./start.sh` | Inicia o servidor na porta 8000 |
| `./stop.sh` | Para o servidor |
| `./restart.sh` | Reinicia o servidor |

## Customização (Opcional)

Se quiser personalizar o sistema com sua logo e favicon:

- **Logo**: Coloque em `app/static/logo.png` (dimensão recomendada: 200x50px)
- **Favicon**: Coloque em `app/static/favicon/favicon.ico` (dimensão recomendada: 32x32px)

O sistema detecta automaticamente se esses arquivos existirem e exibe no relatório, converte em binário e sobe nos templates.