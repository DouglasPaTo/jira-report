# 🚀 Jira Reports

Sistema para geração de relatórios de tickets do Jira com filtros e exportação HTML.

## ✨ Por que usar o Jira Reports?

- **🔒 Seguro**: Desenvolvido com FastAPI, um dos frameworks mais modernos e seguros do Python. Autenticação robusta com senhas criptografadas.
- **⚡ Rápido**: Python é sinônimo de velocidade. O sistema processa milhares de tickets em segundos.
- **💾 Robusto**: Banco de dados SQLite significa zero complexidade, mas com poder de crescer, você pode começar simples e escalar quando precisar.
- **🎯 Flexível**: Filtros por projeto, status, organização, responsável, data e muito mais.
- **📊 Profissional**: Relatórios HTML limpos e prontos para impressão ou envio.

## 🎯 Para quem é?

Perfeito para gestores, líderes de equipe e analistas que precisam de relatórios claros e rápidos dos tickets de suporte ou projetos no Jira.

## 📋 Como Configurar

### 1. Credenciais do Jira

Edite o arquivo `.env` com seus dados:

```env
JIRA_URL=https://suaempresa.atlassian.net
JIRA_EMAIL=seu@email.com
JIRA_API_TOKEN=seu_token_aqui
```

### 2. Gerando o Token API

1. Acesse: https://id.atlassian.com/manage-profile/security/api-tokens
2. Clique em "Create API token"
3. Dê um nome (ex: "Jira Reports")
4. Copie o token gerado e cole no `.env`

### 3. Pronto!

Execute `./setup.sh` uma vez e `./restart.sh` para iniciar.

## 💡 Como Usar

1. **Acesse** o sistema pelo navegador
2. **Faça login** com suas credenciais
3. **Atualize** os tickets com os botões "Atualizar Tudo" ou "Atualizar Recentes"
4. **Filtre** pelos campos desejados (projeto, status, organização, responsável, datas)
5. **Exporte** para HTML com um clique

## 🛠️ Stack Tecnológica

| Componente | Tecnologia | Por que? |
|------------|-----------|-----------|
| **Backend** | FastAPI (Python) | Moderno, ultra-rápido, segurança nativa |
| **Banco de Dados** | SQLite | Simples, confiável, não precisa de complexidade |
| **Frontend** | HTML + TailwindCSS | Limpo e responsivo |
| **Servidor** | Uvicorn | Performance industrial-grade |

**Python**: Linguagem mais popular do mundo, conhecida por sua confiabilidade e vasto ecossistema de bibliotecas.

## 📁 Estrutura do Projeto

```
jira-calls/
├── app/
│   ├── main.py              # Entrada do servidor
│   ├── routers/             # Rotas da aplicação
│   │   ├── web.py          # Dashboard e relatórios
│   │   └── auth.py         # Autenticação
│   ├── services/            # Integração com Jira
│   ├── db/                  # Modelos do banco
│   ├── templates/           # Páginas HTML
│   └── static/              # CSS, logo, favicon
├── .env                     # Suas credenciais
├── setup.sh                 # Configuração inicial
├── restart.sh               # Iniciar/reiniciar
└── README.md               # Este arquivo
```

## ⚙️ Scripts Disponíveis

| Comando | O que faz |
|---------|-----------|
| `./setup.sh` | Instala tudo que precisa (Python, dependências) |
| `./start.sh` | Inicia o servidor |
| `./stop.sh` | Para o servidor |
| `./restart.sh` | Reinicia o servidor |

## 🎨 Customização

### Logo do Relatório
Coloque sua logo em: `app/static/logo.png` (200x50px recomendado)

### Favicon
Coloque seu ícone em: `app/static/favicon/favicon.ico` (32x32px recomendado)

O sistema detecta automaticamente!

## 🔐 Segurança

- Senhas criptografadas com BCrypt
- Sessões seguras com chave secreta
- Proteção contra ataques comuns
- Credenciais em arquivo separado
- **Controle de acesso por organizações**: Usuários comuns só veem tickets das organizações designadas

## 👥 Controle de Acesso por Organizações

O sistema permite criar dois tipos de usuários:

### Usuário Admin
- Acesso completo a todas as funcionalidades
- Pode criar e gerenciar outros usuários
- Vê todos os tickets e relatórios
- Relatórios incluem coluna "Valor/h"

### Usuário Comum (Cliente)
- Acesso limitado às organizações designadas
- Não pode acessar a página de gerenciamento de usuários
- Vê apenas tickets das organizações que tem permissão
- Relatórios **não** incluem coluna "Valor/h" (informação confidencial oculta)

#### Criando usuários com acesso limitado

1. Faça login como admin
2. Acesse "Usuários" no menu
3. No campo "Organizações", selecione:
   - **"TODAS as organizações"**: Acesso a todas as organizações atuais e futuras
   - Organizações específicas: Selecione uma ou mais organizações individuais
4. Finalize a criação

Isso é ideal para compartilhar relatórios com clientes, permitindo que vejam apenas os atendimentos realizados para a empresa deles.

## 📝 Requisitos

- Linux (testado no Ubuntu)
- Python 3.10+
- Acesso à internet (para API do Jira)

## Dashboard

- Interface fácil de usar
- Lista completa de tickets
<img width="1335" height="578" alt="jira1" src="https://github.com/user-attachments/assets/a1ddfefd-a8ef-4c74-af78-afff080bf8ff" /> 
 
## Relatório

- Relatório simples e objetivo
- Informações fáceis de entender
- Cálculo de custo em tipos diferentes de atendimento
- Imprimiu (PDF), enviou
<img width="1216" height="900" alt="jira2" src="https://github.com/user-attachments/assets/239786d3-6305-4a9b-84a0-15977de5628a" />

## Observação
- O campo Descrição busca apenas o último comentário gerado no Jira

## 📄 Licença

MIT License - Use, modifique e distribua à vontade!
