# tech-challenge-books-api
Pipeline de dados + API pública para consulta de livros (Tech Challenge FIAP)

## Como rodar o projeto

É altamente recomendado usar um ambiente virtual (venv) para isolar as dependências do projeto.

### Crie o ambiente virtual:

```bash
python -m venv venv
```

### Ative o ambiente virtual:

**No Windows:**
```bash
.\venv\Scripts\activate
```

**No macOS/Linux:**
```bash
source venv/bin/activate
```

### Instale as dependências:

Uma vez com o ambiente ativado, instale os pacotes necessários:

```bash
pip install -r requirements.txt
```

### Rodar o scrape:

```bash
python .\scripts\books_scraper.py
```