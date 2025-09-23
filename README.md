# tech-challenge-books-api
Pipeline de dados + API pública para consulta de livros (Tech Challenge FIAP)

## Como rodar o projeto

É altamente recomendado usar um ambiente virtual (`venv`) para isolar as dependências do projeto.

1. **Crie o ambiente virtual:**
   ```bash
   python -m venv venv
   ```

2. **Ative o ambiente virtual:**
   - **No Windows:**
     ```powershell
     .\venv\Scripts\activate
     ```
   - **No macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

3. **Instale as dependências:**
   Uma vez com o ambiente ativado, instale os pacotes necessários:
   ```bash
   pip install -r requirements.txt
   ```
4. **Rodar o scrape:**
   ```bash
   python .\scripts\books_scraper.py
   ```