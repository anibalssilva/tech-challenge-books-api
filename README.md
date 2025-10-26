# 📚 Tech Challenge - Books API

> **Sistema completo de coleta, processamento e disponibilização de dados sobre livros**
> *Tech Challenge FIAP - Pós Tech | Machine Learning Engineering*

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Sobre o Projeto

Este projeto faz parte do **Tech Challenge FIAP** e consiste em um sistema completo de **pipeline de dados** para extração, processamento e disponibilização de informações sobre livros através de uma **API REST** autenticada.

### 🎯 Objetivos

- **📥 Coleta de Dados**: Web scraping do site [books.toscrape.com](https://books.toscrape.com/)
- **🔄 Processamento**: Limpeza e transformação dos dados brutos
- **🌐 API REST**: Disponibilização dos dados através de endpoints autenticados
- **🔐 Autenticação**: Sistema de autenticação JWT com controle de acesso
- **📊 Dashboard**: Interface de monitoramento com métricas em tempo real
- **⚡ Performance**: Processamento paralelo para otimização

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────┐
│  Web Scraping   │  → Coleta dados de books.toscrape.com
│  (Paralelo)     │     • BeautifulSoup + Requests
└────────┬────────┘     • ThreadPoolExecutor (12 workers)
         │
         ▼
┌─────────────────┐
│  Processamento  │  → Limpa e valida dados
│  (pandas)       │     • Remove duplicatas
└────────┬────────┘     • Trata valores nulos
         │
         ▼
┌─────────────────┐
│  Armazenamento  │  → Salva em CSV e SQLite
│  (CSV + SQLite) │     • books.csv
└────────┬────────┘     • database.db (usuários)
         │
         ▼
┌─────────────────┐
│   API FastAPI   │  → Endpoints REST autenticados
│   (JWT Auth)    │     • CRUD de livros
└────────┬────────┘     • Autenticação JWT
         │              • Logs estruturados
         │
         ├──────────────────────────┐
         ▼                          ▼
┌─────────────────┐      ┌─────────────────┐
│   Dashboard     │      │   Documentação  │
│   (Streamlit)   │      │   (Swagger UI)  │
└─────────────────┘      └─────────────────┘
```

---

## 🚀 Tecnologias Utilizadas

### Backend & API
- **FastAPI** - Framework web moderno e rápido
- **Uvicorn** - Servidor ASGI de alta performance
- **Pydantic** - Validação de dados com type hints
- **SQLModel** - ORM para SQLite
- **PyJWT** - Autenticação JSON Web Token
- **pwdlib** - Hash seguro de senhas (Argon2)

### Web Scraping
- **BeautifulSoup4** - Parsing de HTML
- **Requests** - Cliente HTTP
- **lxml** - Parser XML/HTML rápido

### Processamento de Dados
- **pandas** - Manipulação e análise de dados
- **numpy** - Computação numérica

### Logging & Monitoramento
- **structlog** - Logs estruturados em JSON
- **Streamlit** - Dashboard interativo
- **Plotly** - Visualizações interativas

### Desenvolvimento
- **pytest** - Testes automatizados
- **black** - Formatação de código
- **ruff** - Linter rápido
- **mypy** - Type checking estático

---

## 📁 Estrutura do Projeto

```
tech-challenge-books-api/
├── api/
│   ├── main.py              # Aplicação principal FastAPI
│   └── security.py          # Autenticação e segurança
├── dashboard/
│   └── dashboard.py         # Dashboard Streamlit
├── data/
│   ├── raw/
│   │   └── books.csv        # Dados brutos do scraping
│   └── processed/
│       └── books.csv        # Dados processados e limpos
├── db/
│   └── user.py              # Modelo de dados do usuário
├── logs/
│   └── setup_logging.py     # Configuração de logs estruturados
├── model/
│   ├── create_user.py       # Schema de criação de usuário
│   ├── token.py             # Schema de token JWT
│   ├── refresh_token.py     # Schema de refresh token
│   ├── request_token.py     # Schema de login
│   └── update_user.py       # Schema de atualização
├── scripts/
│   ├── books_scraper.py     # Script de web scraping
│   └── processe_data.py     # Processamento e limpeza
├── .streamlit/
│   └── config.toml          # Configuração do Streamlit
├── config.py                # Configurações da aplicação
├── requirements.txt         # Dependências do projeto
├── start.sh                 # Script de inicialização da API
├── start_dashboard.sh       # Script de inicialização do dashboard
└── create_database_tables.py  # Utilitário para criar tabelas PostgreSQL
```

---

## 🔧 Instalação e Configuração

### Pré-requisitos

- Python 3.11+
- pip (gerenciador de pacotes)
- Git

### 1️⃣ Clonar o Repositório

```bash
git clone https://github.com/anibalssilva/tech-challenge-books-api.git
cd tech-challenge-books-api
```

### 2️⃣ Criar Ambiente Virtual

```bash
# Criar venv
python -m venv venv

# Ativar (Windows)
.\venv\Scripts\activate

# Ativar (Linux/Mac)
source venv/bin/activate
```

### 3️⃣ Instalar Dependências

```bash
pip install -r requirements.txt
```

---

## 🎮 Como Usar

### 📥 1. Coletar Dados (Web Scraping)

```bash
python scripts/books_scraper.py --workers 12 --verbose
```

**Parâmetros disponíveis:**
- `--out`: Caminho do arquivo CSV de saída (padrão: `../data/raw/books.csv`)
- `--workers`: Número de threads paralelas (padrão: `12`)
- `--verbose`: Exibe progresso detalhado
- `--delay`: Atraso entre requisições (ignorado no modo paralelo)

**Saída:**
```
Gathering all product URLs from catalogue...
Found 1000 product URLs.
✅ Process completed in 45.23s (22.1 livros/s)
```

### 🔄 2. Processar Dados

```bash
python scripts/processe_data.py
```

**O que faz:**
- Remove duplicatas de livros
- Trata valores nulos
- Valida formato dos dados
- Salva em `data/processed/books.csv`

### 🌐 3. Executar a API

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Acesse:**
- API: http://localhost:8000
- Documentação: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

### 📊 4. Executar o Dashboard (Opcional)

```bash
streamlit run dashboard/dashboard.py
```

**Acesse:** http://localhost:8501

---

## 🔐 Autenticação e Uso da API

### 1. Registrar Usuário

```bash
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"username": "seu_usuario", "password": "sua_senha"}'
```

### 2. Fazer Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "seu_usuario", "password": "sua_senha"}'
```

**Resposta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Usar Token nos Endpoints

```bash
# Listar livros
curl http://localhost:8000/api/v1/books \
  -H "Authorization: Bearer SEU_TOKEN"

# Buscar por categoria
curl "http://localhost:8000/api/v1/books/search?category=Fiction" \
  -H "Authorization: Bearer SEU_TOKEN"

# Estatísticas gerais
curl http://localhost:8000/api/v1/stats/overview \
  -H "Authorization: Bearer SEU_TOKEN"
```

---

## 📡 Endpoints da API

### 🔓 Públicos (Sem Autenticação)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/health` | Health check da API |
| POST | `/api/v1/users/register` | Registrar novo usuário |
| POST | `/api/v1/auth/login` | Fazer login e obter token |
| POST | `/api/v1/auth/refresh` | Renovar token expirado |

### 🔒 Autenticados (Requer Token)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/books` | Listar todos os livros |
| GET | `/api/v1/books/{id}` | Buscar livro por ID |
| GET | `/api/v1/books/search` | Buscar por título/categoria |
| GET | `/api/v1/categories` | Listar todas as categorias |
| GET | `/api/v1/books/top-rated` | Livros mais bem avaliados |
| GET | `/api/v1/books/price-range` | Filtrar por faixa de preço |
| GET | `/api/v1/stats/overview` | Estatísticas gerais |
| GET | `/api/v1/stats/categories` | Estatísticas por categoria |

### 👑 Admin (Requer Permissão)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/users/admin` | Promover usuário a admin |
| POST | `/api/v1/users/disable` | Desabilitar usuário |

---

## 📊 Dashboard de Monitoramento

O dashboard oferece visualizações em tempo real:

### Métricas Disponíveis

- **📈 Performance**: Latência, tempo de resposta (média, p50, p95)
- **🌐 Tráfego**: Requisições por minuto/hora (RPM/RPH)
- **🔍 Endpoints**: Análise de uso, endpoints mais lentos
- **❗ Erros**: Taxa de erros, distribuição de status codes
- **👥 Clientes**: Top clientes por requisições
- **📜 Logs**: Últimos 100 logs em tempo real

### Como Funciona

O dashboard lê logs estruturados em JSON do arquivo `./logs/api.log` e gera visualizações interativas com Plotly.

---

## 🔍 Dados Coletados

### Informações por Livro

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `title` | string | Título do livro |
| `category` | string | Categoria (Fiction, Poetry, etc.) |
| `image_url` | string | URL da imagem de capa |
| `description` | string | Descrição/sinopse |
| `rating` | integer | Avaliação em estrelas (1-5) |
| `upc` | string | Código UPC único |
| `product_type` | string | Tipo do produto |
| `price_excl_tax` | float | Preço sem impostos |
| `price_incl_tax` | float | Preço com impostos |
| `tax` | float | Valor do imposto |
| `availability` | integer | Quantidade em estoque |

### Exemplo de Dados

```json
{
  "title": "A Light in the Attic",
  "category": "Poetry",
  "image_url": "https://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg",
  "description": "It's hard to imagine a world without A Light in the Attic...",
  "rating": 3,
  "upc": "a897fe39b1053632",
  "product_type": "Books",
  "price_excl_tax": 51.77,
  "price_incl_tax": 51.77,
  "tax": 0.00,
  "availability": 22
}
```

---

## 🚀 Deploy

### Deploy no Render

A aplicação está configurada para deploy no Render:

**API:** https://tech-challenge-books-api.onrender.com
**Docs:** https://tech-challenge-books-api.onrender.com/docs

#### Variáveis de Ambiente Necessárias

```bash
SECRET_KEY=3a8f48a734afa31827f42e90d0ce20ffab1dfcc4e7168e16e84ead8c8f4f931d
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
PORT=10000
```

#### Comandos de Build e Start

```bash
# Build
pip install -r requirements.txt

# Start API
bash start.sh

# Start Dashboard
bash start_dashboard.sh
```

---

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Com cobertura
pytest --cov=api --cov=scripts

# Testes específicos
pytest tests/test_api.py -v
```

---

## 📈 Performance

### Web Scraping

- **1000 livros** em ~45 segundos
- **22 livros/segundo** com 12 workers
- Processamento paralelo com ThreadPoolExecutor
- Retry automático em caso de falha

### API

- **Tempo de resposta**: <100ms (média)
- **Latência p95**: <200ms
- **Throughput**: 1000+ req/s (testes locais)
- Validação com Pydantic para segurança

---

## 🛡️ Segurança

- ✅ Autenticação JWT com tokens expirantes
- ✅ Senhas com hash Argon2
- ✅ Validação de entrada com Pydantic
- ✅ Rate limiting (configurável)
- ✅ HTTPS no deploy (Render)
- ✅ Secrets em variáveis de ambiente

---

## 📝 Logs

Logs estruturados em formato JSON:

```json
{
  "timestamp": "2025-10-26T10:30:00",
  "level": "info",
  "event": "request_finished",
  "logger": "api",
  "method": "GET",
  "path": "/api/v1/books",
  "status_code": 200,
  "process_time_ms": 45.23,
  "client_host": "127.0.0.1"
}
```

**Localização:** `./logs/api.log`

---

## 🤝 Contribuição

### Equipe de Desenvolvimento

👤 **Aníbal dos Santos Silva**
📧 anibal.sant@gmail.com

👤 **Bruno Henrique Martins da Fonseca**
📧 bruhhmx@gmail.com

👤 **Caio Breno Dantas Leite**
📧 caio.bndantas@gmail.com

👤 **Juliana Agra Cardoso**
📧 juliana.agra@hotmail.com

👤 **Thiago Fernando Lima de Morais**
📧 tf_lima@terra.com.br

---

## 📄 Licença

Este projeto foi desenvolvido para fins acadêmicos como parte do **Tech Challenge FIAP**.

---

## 🔗 Links Úteis

- **Documentação FastAPI**: https://fastapi.tiangolo.com
- **Streamlit Docs**: https://docs.streamlit.io
- **Render Deploy**: https://render.com/docs
- **Books to Scrape**: https://books.toscrape.com

---

<div align="center">

**Desenvolvido com ❤️ para o Tech Challenge FIAP**

*Pós Tech | Machine Learning Engineering*

</div>
