# 📚 tech-challenge-books-api

> **Pipeline de dados + API pública para consulta de livros**  
> *Tech Challenge FIAP*

---

## 📖 Sobre o Projeto

Este projeto faz parte do **Tech Challenge FIAP** e consiste em um pipeline completo de dados para extração, processamento e disponibilização de informações sobre livros através de uma API pública.

### 🎯 **Objetivos**

- **Coleta de Dados**: Realizar web scraping do site [books.toscrape.com](https://books.toscrape.com/) para extrair informações detalhadas sobre livros
- **Processamento**: Transformar os dados brutos em um formato estruturado e limpo
- **Disponibilização**: Criar uma API pública para consulta dos dados coletados
- **Performance**: Implementar técnicas de processamento paralelo para otimizar a coleta

### 🔍 **O que é extraído**

O sistema coleta as seguintes informações de cada livro:

- **📝 Informações Básicas**: Título, categoria, descrição
- **💰 Dados Financeiros**: Preços com e sem impostos, valor dos impostos
- **⭐ Avaliações**: Rating em estrelas (1-5)
- **📊 Estoque**: Quantidade disponível
- **🖼️ Mídia**: URL da imagem de capa
- **🔢 Identificação**: Código UPC único do produto

### 🏗️ **Arquitetura**

O projeto segue uma arquitetura de pipeline de dados:

```
📥 COLETA → 🔄 PROCESSAMENTO → 💾 ARMAZENAMENTO → 🌐 API
    ↓              ↓                ↓              ↓
Web Scraping   Limpeza/Validação   CSV/DB      Endpoints REST
```

### 🎓 **Contexto Acadêmico**

Este projeto é desenvolvido como parte do **Tech Challenge FIAP**, uma competição que visa aplicar conhecimentos de:

- **Machine Learning Engineering**
- **Data Pipeline Development**
- **Web Scraping Techniques**
- **API Development**
- **Performance Optimization**

---

## 🚀 Como rodar o projeto

É altamente recomendado usar um ambiente virtual (venv) para isolar as dependências do projeto.

### 1️⃣ **Crie o ambiente virtual**

```bash
python -m venv venv
```

### 2️⃣ **Ative o ambiente virtual**

**No Windows:**
```bash
.\venv\Scripts\activate
```

**No macOS/Linux:**
```bash
source venv/bin/activate
```

### 3️⃣ **Instale as dependências**

Uma vez com o ambiente ativado, instale os pacotes necessários:

```bash
pip install -r requirements.txt
```

### 4️⃣ **Execute o scraper**

```bash
python .\scripts\books_scraper.py
```

---

## 📋 Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)

## 📁 Estrutura do Projeto

```
tech-challenge-books-api/
├── scripts/
│   └── books_scraper.py    # Script principal de web scraping
├── data/
│   └── raw/
│       └── books.csv       # Dados extraídos (gerado automaticamente)
├── requirements.txt        # Dependências do projeto
└── README.md              # Este arquivo
```

## 🔧 Opções de Execução

O script `books_scraper.py` aceita os seguintes parâmetros:

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `--out` | Caminho do arquivo CSV de saída | `../data/raw/books.csv` |
| `--workers` | Número de threads paralelas | `12` |
| `--verbose` | Exibe progresso detalhado | `False` |
| `--delay` | Atraso entre requisições (ignorado no modo paralelo) | `0.1` |

### Exemplos de uso:

```bash
# Execução básica
python .\scripts\books_scraper.py

# Com mais threads e modo verboso
python .\scripts\books_scraper.py --workers 16 --verbose

# Especificando arquivo de saída
python .\scripts\books_scraper.py --out dados/meus_livros.csv
```

---

## 📊 Sobre o Projeto

Este projeto realiza web scraping do site [books.toscrape.com](https://books.toscrape.com/) para extrair informações sobre livros e salvá-las em formato CSV. O scraper utiliza processamento paralelo para melhor performance e inclui tratamento robusto de erros.

### ✨ Características

- 🔄 **Processamento Paralelo**: Utiliza ThreadPoolExecutor para melhor performance
- 🛡️ **Tratamento de Erros**: Retry automático e tratamento de falhas
- 📈 **Monitoramento**: Modo verboso para acompanhar o progresso
- 🎯 **Ordem Preservada**: Mantém a ordem original dos produtos do catálogo
- 📝 **Dados Completos**: Extrai título, categoria, preço, avaliação, disponibilidade, etc.

---

## 🤝 Contribuição

Este é um projeto do Tech Challenge FIAP. Para contribuições ou dúvidas, entre em contato com a equipe do projeto:

### 👥 **Equipe de Desenvolvimento**

- **Aníbal dos Santos Silva**  
  📧 anibal.sant@gmail.com

- **Bruno Henrique Martins da Fonseca**  
  📧 bruhhmx@gmail.com

- **Caio Breno Dantas Leite**  
  📧 caio.bndantas@gmail.com

- **Juliana Agra Cardoso**  
  📧 juliana.agra@hotmail.com

- **Thiago Fernando Lima de Morais**  
  📧 tf_lima@terra.com.br

---

*Desenvolvido para o Tech Challenge FIAP*