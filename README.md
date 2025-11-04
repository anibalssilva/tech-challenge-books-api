# 📚 Books API - Tech Challenge FIAP

**Sistema Completo de Pipeline de Dados para Coleta, Processamento e Disponibilização de Informações sobre Livros**

*Tech Challenge FIAP - Pós Tech | Machine Learning Engineering - Fase 1*

[📖 Documentação](https://tech-challenge-books-api-fxmj.onrender.com/docs)

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Arquitetura](#-arquitetura-do-sistema)
- [Tecnologias](#-stack-tecnológico)
- [Funcionalidades](#-funcionalidades-principais)
- [Instalação](#-instalação-e-configuração)
- [Como Usar](#-guia-de-uso)
- [API Reference](#-api-reference)
- [Dashboard](#-dashboard-de-monitoramento)
- [Deploy](#-deploy-em-produção)
- [Performance](#-métricas-de-performance)
- [Segurança](#-segurança)
- [Equipe](#-equipe-de-desenvolvimento)

---

## 🎯 Sobre o Projeto

### Contexto

O **Books API** é um projeto desenvolvido para o **Tech Challenge da FIAP** (Pós Tech - Machine Learning Engineering), que consiste na criação de um pipeline completo de dados, desde a coleta até a disponibilização via API REST, com foco em **boas práticas de engenharia de software** e **arquitetura de dados**.

### Objetivos do Projeto

1. **📥 Extração de Dados (Web Scraping)**
   - Coletar dados de 1000+ livros do site [books.toscrape.com](https://books.toscrape.com/)
   - Implementar processamento paralelo para otimização
   - Aplicar técnicas de retry e error handling

2. **🔄 Processamento e Qualidade de Dados**
   - Limpeza e transformação de dados brutos
   - Remoção de duplicatas e tratamento de valores nulos
   - Validação de integridade dos dados

3. **🌐 API REST com Autenticação**
   - Disponibilização de endpoints RESTful
   - Sistema de autenticação JWT
   - Controle de acesso por níveis (user/admin)
   - Documentação OpenAPI (Swagger)

4. **📊 Monitoramento e Observabilidade**
   - Logging estruturado em JSON
   - Dashboard em tempo real
   - Métricas de performance e SLA
   - Persistência de logs em PostgreSQL

5. **🚀 Deploy em Produção**
   - Aplicação containerizada e escalável
   - Deployment no Render (PaaS)
   - Monitoramento contínuo

### Diferenciais do Projeto

- ✨ **Arquitetura Moderna**: Utilização de FastAPI, structlog e async/await
- ✨ **Segurança**: JWT + Argon2 para hash de senhas
- ✨ **Observabilidade**: Logs estruturados + Dashboard com 10+ métricas
- ✨ **Performance**: Scraping paralelo (22 livros/s) + API sub-100ms
- ✨ **Qualidade**: Type hints, validação Pydantic, testes automatizados
- ✨ **Produção**: Deploy automatizado, logs persistentes, alta disponibilidade

---

## 🏗️ Arquitetura do Sistema

### Visão Geral

```
┌──────────────────────────────────────────────────────────────────────┐
│                       CAMADA DE COLETA                                │
├──────────────────────────────────────────────────────────────────────┤
│  Web Scraping (books.toscrape.com)                                   │
│  • BeautifulSoup4 + Requests                                          │
│  • ThreadPoolExecutor (12 workers)                                    │
│  • Retry automático com exponential backoff                           │
│  • Performance: 22 livros/segundo                                     │
└────────────────────┬─────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  CAMADA DE PROCESSAMENTO                              │
├──────────────────────────────────────────────────────────────────────┤
│  Pandas + Numpy                                                       │
│  • Remove duplicatas por título                                       │
│  • Trata valores nulos e inconsistências                              │
│  • Validação de tipos e formatos                                      │
│  • Output: data/processed/books.csv                                   │
└────────────────────┬─────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   CAMADA DE ARMAZENAMENTO                             │
├──────────────────────────────────────────────────────────────────────┤
│  SQLite (desenvolvimento)          PostgreSQL (produção)              │
│  • Usuários e autenticação         • Logs estruturados                │
│  • Tabela: user                    • Tabela: api_logs                 │
│  • SQLModel ORM                    • 3 índices para performance       │
└────────────────────┬─────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     CAMADA DE APLICAÇÃO                               │
├──────────────────────────────────────────────────────────────────────┤
│  FastAPI + Uvicorn                                                    │
│  • 17+ endpoints REST                                                 │
│  • Autenticação JWT (HS256)                                           │
│  • Validação Pydantic                                                 │
│  • Middleware de logging                                              │
│  • CORS configurável                                                  │
│  • OpenAPI/Swagger autodocumentado                                    │
└──────────────────┬─────────────────────┬──────────────────────────────┘
                   │                     │
                   ▼                     ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│  DASHBOARD (Streamlit)   │  │  DOCUMENTAÇÃO (Swagger)  │
├──────────────────────────┤  ├──────────────────────────┤
│  • Métricas em tempo     │  │  • Swagger UI            │
│    real                   │  │  • ReDoc                 │
│  • 10+ visualizações     │  │  • OpenAPI 3.0 spec      │
│  • Plotly interativo     │  │  • Try it out!           │
│  • Filtros por data      │  │  • Autenticação          │
└──────────────────────────┘  └──────────────────────────┘
```

### Componentes Principais

| Componente | Responsabilidade | Tecnologia | Linhas de Código |
|------------|------------------|------------|------------------|
| **Web Scraper** | Coleta dados do site fonte | BeautifulSoup + ThreadPool | 813 |
| **Data Processor** | Limpeza e validação | pandas + numpy | 150 |
| **API Server** | Endpoints REST | FastAPI + Uvicorn | 338 |
| **Auth System** | Segurança e JWT | pwdlib + PyJWT | 214 |
| **Logging System** | Observabilidade | structlog + PostgreSQL | 127 |
| **Dashboard** | Visualização de métricas | Streamlit + Plotly | 216 |

---

## 🛠️ Stack Tecnológico

### Backend e API

| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| **Python** | 3.11+ | Linguagem principal |
| **FastAPI** | 0.116.1 | Framework web assíncrono |
| **Uvicorn** | 0.35.0 | Servidor ASGI de produção |
| **Pydantic** | 2.11.7 | Validação de dados e schemas |
| **SQLModel** | 0.0.22 | ORM para SQLite/PostgreSQL |
| **PyJWT** | 2.10.1 | JSON Web Tokens |
| **pwdlib[argon2]** | 0.2.1 | Hash seguro de senhas |

### Web Scraping

| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| **BeautifulSoup4** | 4.14.2 | Parsing de HTML |
| **requests** | 2.32.5 | Cliente HTTP |
| **lxml** | 6.0.2 | Parser XML/HTML rápido |

### Data Engineering

| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| **pandas** | 2.2.3 | Manipulação de dados |
| **numpy** | 2.3.3 | Computação numérica |

### Logging & Monitoramento

| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| **structlog** | 25.4.0 | Logs estruturados em JSON |
| **psycopg2-binary** | 2.9.9+ | Driver PostgreSQL |
| **Streamlit** | 1.41.1 | Dashboard interativo |
| **Plotly** | 5.24.1 | Visualizações interativas |

---

## ✨ Funcionalidades Principais

### 1. Web Scraping Paralelo

- 🚀 **Performance**: 22 livros por segundo
- 🔄 **Paralelização**: ThreadPoolExecutor com 12 workers
- 🛡️ **Resiliência**: Retry automático com backoff exponencial
- 📊 **Progresso**: Barra de progresso em tempo real
- 💾 **Output**: CSV com 11 campos por livro

**Dados Coletados por Livro:**
- Título, categoria, descrição
- Imagem de capa (URL)
- Avaliação (1-5 estrelas)
- Preço com/sem impostos
- Código UPC único
- Disponibilidade em estoque

### 2. API REST com Autenticação JWT

#### Autenticação
- 🔐 **JWT Token**: Expiração configurável (30min)
- 🔑 **Password Hashing**: Argon2 (OWASP recomendado)
- 🔄 **Token Refresh**: Renovação automática
- 👑 **Níveis de Acesso**: User e Admin
- 🚫 **Disable Users**: Desativação sem exclusão

#### Endpoints Principais
- **4 endpoints públicos** (registro, login, health, refresh)
- **8 endpoints autenticados** (livros, busca, estatísticas)
- **2 endpoints admin** (promoção, desativação)
- **2 endpoints de monitoramento** (logs file e database)

### 3. Sistema de Logs Estruturados

- 📝 **Formato**: JSON estruturado (structlog)
- 💾 **Persistência Dual**: Arquivo + PostgreSQL
- 🔍 **Rastreabilidade**: Request ID (UUID)
- ⚡ **Performance**: Flush imediato, sem buffer
- 📊 **Métricas**: Timestamp, latência, status code, método, path

### 4. Dashboard de Monitoramento

- 📈 **10+ Visualizações**: Plotly interativo
- ⏱️ **Tempo Real**: Atualização via PostgreSQL
- 🎯 **Métricas SLA**: p50, p95, error rate
- 🔍 **Filtros**: Data, endpoint, status code
- 👥 **Análise de Tráfego**: Top clientes, métodos HTTP

---

## 🚀 Instalação e Configuração

### Pré-requisitos

- **Python** 3.11 ou superior
- **pip** (gerenciador de pacotes Python)
- **Git** (controle de versão)
- **PostgreSQL** 16+ (produção) ou SQLite (desenvolvimento)

### Instalação Passo a Passo

#### 1. Clonar o Repositório

```bash
git clone https://github.com/anibalssilva/tech-challenge-books-api.git
cd tech-challenge-books-api
```

#### 2. Criar Ambiente Virtual

**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

#### 4. Configurar Variáveis de Ambiente (Opcional)

Crie um arquivo `.env` na raiz do projeto:

```env
# JWT Configuration
JWT_SECRET_KEY=sua_chave_secreta_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database (PostgreSQL para produção)
DB_NAME=books_api_db
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
```

#### 5. Inicializar Banco de Dados PostgreSQL (Opcional)

```bash
python create_database_tables.py
```

---

## 📖 Guia de Uso

### Passo 1: Coletar Dados (Web Scraping)

```bash
python scripts/books_scraper.py --workers 12 --verbose
```

**Parâmetros disponíveis:**
- `--out`: Arquivo CSV de saída (padrão: `../data/raw/books.csv`)
- `--workers`: Número de threads paralelas (padrão: `12`)
- `--verbose`: Exibir progresso detalhado
- `--delay`: Delay entre requests em modo serial (padrão: `1`)

**Saída esperada:**
```
Gathering all product URLs from catalogue...
Found 1000 product URLs.
Scraping books: 100%|████████████| 1000/1000 [00:45<00:00, 22.1 livros/s]
✅ Process completed in 45.23s (22.1 livros/s)
```

### Passo 2: Processar e Limpar Dados

```bash
python scripts/processe_data.py
```

**O que o script faz:**
1. ✅ Carrega o CSV bruto
2. ✅ Remove duplicatas por título
3. ✅ Trata valores nulos
4. ✅ Valida tipos de dados
5. ✅ Salva em `data/processed/books.csv`

### Passo 3: Executar a API

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Endpoints disponíveis:**
- 🏥 **Health Check**: http://localhost:8000/api/v1/health
- 📚 **Documentação Swagger**: http://localhost:8000/docs
- 📖 **Documentação ReDoc**: http://localhost:8000/redoc

### Passo 4: Executar o Dashboard

```bash
streamlit run dashboard/dashboard.py
```

**Acesse:** http://localhost:8501

---

## 📡 API Reference

### Autenticação

Todos os endpoints protegidos requerem um token JWT no header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 🔓 Endpoints Públicos

#### 1. Health Check
```http
GET /api/v1/health
```

#### 2. Registrar Usuário
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "seu_usuario",
  "password": "sua_senha"
}
```

#### 3. Login
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=seu_usuario&password=sua_senha
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 4. Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "access_token": "token_expirado"
}
```

### 🔒 Endpoints Autenticados

#### 5. Listar Todos os Livros
```http
GET /api/v1/books
Authorization: Bearer {token}
```

#### 6. Buscar Livro por ID
```http
GET /api/v1/books/{id}
Authorization: Bearer {token}
```

#### 7. Buscar por Título ou Categoria
```http
GET /api/v1/books/search?title=Light&category=Poetry
Authorization: Bearer {token}
```

#### 8. Listar Categorias
```http
GET /api/v1/categories
Authorization: Bearer {token}
```

#### 9. Top Livros por Avaliação
```http
GET /api/v1/books/top-rated?limit=10
Authorization: Bearer {token}
```

#### 10. Filtrar por Faixa de Preço
```http
GET /api/v1/books/price-range?min=20&max=50
Authorization: Bearer {token}
```

#### 11. Estatísticas Gerais
```http
GET /api/v1/stats/overview
Authorization: Bearer {token}
```

#### 12. Estatísticas por Categoria
```http
GET /api/v1/stats/categories
Authorization: Bearer {token}
```

### 👑 Endpoints Admin

#### 13. Promover Usuário a Admin
```http
PUT /api/v1/auth/update/admin
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "username": "usuario_a_promover"
}
```

#### 14. Desabilitar Usuário
```http
PUT /api/v1/auth/update/disable
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "username": "usuario_a_desabilitar"
}
```

### 📊 Endpoints de Monitoramento

#### 15. Logs (File-based)
```http
GET /api/v1/logs?limit=100
```

#### 16. Logs (Database)
```http
GET /api/v1/db-logs?limit=1000
```

---

## 📊 Dashboard de Monitoramento

### Métricas Disponíveis

#### 1. KPIs Principais
- **Total de Requisições**: Contagem total de requests
- **Tempo Médio de Resposta**: Latência média em ms
- **Latência p50**: Mediana de latência
- **Latência p95**: 95º percentil (SLA)
- **Taxa de Erros**: % de status code >= 400

#### 2. Gráficos de Performance
- Latência ao Longo do Tempo (line chart)
- Top 10 Endpoints Mais Lentos (bar chart)
- Distribuição da Latência (histogram)

#### 3. Análise de Tráfego
- Requisições por Minuto (RPM)
- Requisições por Endpoint
- Requisições por Método HTTP (pie chart)
- Top 10 Clientes

#### 4. Monitoramento de Erros
- Erros ao Longo do Tempo
- Endpoints com Mais Erros
- Distribuição de Status Codes

---

## 🚀 Deploy em Produção

### Render PaaS

A aplicação está configurada para deploy no Render:

**API:** https://tech-challenge-books-api-fxmj.onrender.com

#### Variáveis de Ambiente Necessárias

```bash
JWT_SECRET_KEY=sua_chave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
PORT=10000
DB_NAME=database_name
DB_USER=database_user
DB_PASSWORD=database_password
DB_HOST=database_host
DB_PORT=5432
```

#### Scripts de Deploy

**start.sh (API):**
```bash
#!/bin/bash
mkdir -p logs
[ ! -f logs/api.log ] && touch logs/api.log
uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-10000}
```

**start_dashboard.sh (Dashboard):**
```bash
#!/bin/bash
streamlit run dashboard/dashboard.py \
  --server.port=${PORT:-10000} \
  --server.address=0.0.0.0
```

---

## 📈 Métricas de Performance

### Web Scraping
- **Throughput**: 22 livros/segundo
- **Tempo Total**: ~45 segundos (1000 livros)
- **Workers**: 12 threads paralelas

### API REST
- **Latência Média**: <100ms
- **Latência p95**: <200ms
- **Throughput**: 1000+ req/s (local)
- **Error Rate**: <1%

---

## 🛡️ Segurança

### Autenticação e Autorização
- ✅ JWT (JSON Web Tokens) com algoritmo HS256
- ✅ Senhas com hash Argon2
- ✅ Tokens expirantes (30 minutos)
- ✅ Refresh token automático
- ✅ Validação de entrada com Pydantic

### Proteções Implementadas
- ✅ SQL Injection (Pydantic validation + ORM)
- ✅ XSS (FastAPI auto-escape)
- ✅ CSRF (CORS configurável)
- ✅ HTTPS em produção (Render)

---

## 👥 Equipe de Desenvolvimento

<table>
  <tr>
    <td align="center">
      <strong>Aníbal dos Santos Silva</strong><br>
      <sub>Tech Lead</sub><br>
      📧 anibal.sant@gmail.com
    </td>
    <td align="center">
      <strong>Bruno Henrique Martins da Fonseca</strong><br>
      <sub>Backend Developer</sub><br>
      📧 bruhhmx@gmail.com
    </td>
    <td align="center">
      <strong>Caio Breno Dantas Leite</strong><br>
      <sub>Data Engineer</sub><br>
      📧 caio.bndantas@gmail.com
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Juliana Agra Cardoso</strong><br>
      <sub>Frontend Developer</sub><br>
      📧 juliana.agra@hotmail.com
    </td>
    <td align="center">
      <strong>Thiago Fernando Lima de Morais</strong><br>
      <sub>DevOps Engineer</sub><br>
      📧 tf_lima@terra.com.br
    </td>
    <td></td>
  </tr>
</table>

---

## 📊 Estatísticas do Projeto

- **Total de Arquivos Python**: 15
- **Total de Linhas de Código**: ~1.581
- **Dependências**: 57 pacotes
- **Livros Coletados**: 1.000+
- **Categorias**: 51
- **Endpoints**: 17

---

## 🔗 Links Úteis

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Render Documentation](https://render.com/docs)

---

## 📄 Licença

Este projeto foi desenvolvido para fins **acadêmicos** como parte do **Tech Challenge FIAP - Pós Tech | Machine Learning Engineering**.

---

<div align="center">

## 🏆 Desenvolvido com Excelência para o Tech Challenge FIAP

**Pós Tech | Machine Learning Engineering - Fase 1**

*"Transformando dados em conhecimento através de engenharia de qualidade"*

[![FIAP](https://img.shields.io/badge/FIAP-Tech%20Challenge-red)](https://www.fiap.com.br/)
[![Status](https://img.shields.io/badge/Status-Em%20Produção-success)](https://tech-challenge-books-api-fxmj.onrender.com/docs)

---

**Acesse a API em Produção:** [tech-challenge-books-api-fxmj.onrender.com](https://tech-challenge-books-api-fxmj.onrender.com/docs)

</div>
