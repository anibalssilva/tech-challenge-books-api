# 🗄️ Como Criar Tabelas no PostgreSQL do Render

Guia passo-a-passo para criar as tabelas necessárias no banco de dados.

---

## 🚀 Método Mais Fácil: Script Python Automatizado

### Passo 1: Obter a URL do Banco de Dados

1. Acesse: https://dashboard.render.com
2. Clique no seu **PostgreSQL Database**
3. Vá na aba **"Info"**
4. Role até a seção **"Connections"**
5. Procure por **"External Database URL"**
6. Clique no ícone de **"Copy"** (📋)

A URL terá este formato:
```
postgresql://usuario:senha@host.render.com/database_name
```

**⚠️ IMPORTANTE:** Esta URL contém a senha do banco! Não compartilhe publicamente.

---

### Passo 2: Executar o Script

No terminal/prompt de comando, execute:

```bash
python create_database_tables.py
```

### Passo 3: Colar a URL

Quando o script pedir:
```
🔗 Cole a DATABASE_URL aqui:
```

Cole a URL que você copiou no Passo 1 e pressione **Enter**.

### Passo 4: Aguardar

O script irá:
- ✅ Instalar psycopg2 se necessário
- ✅ Conectar ao banco
- ✅ Criar a tabela `api_logs`
- ✅ Criar índices para melhor performance
- ✅ Mostrar a estrutura da tabela

**Saída esperada:**
```
✅ Conectado com sucesso!

📊 Criando tabela 'api_logs'...
🔍 Criando índices...

✅ Tabela 'api_logs' criada com sucesso!

📋 Estrutura da tabela:
--------------------------------------------------
  • id                   integer
  • timestamp            timestamp without time zone
  • level                character varying
  • event                character varying
  • logger               character varying
  • method               character varying
  • path                 character varying
  • status_code          integer
  • process_time_ms      double precision
  • client_host          character varying
  • created_at           timestamp without time zone
--------------------------------------------------

📊 Total de registros: 0

🎉 Processo concluído com sucesso!
```

---

## 🔍 Troubleshooting

### Erro: "psycopg2 não encontrado"

**Solução:** O script instala automaticamente, mas se falhar:
```bash
pip install psycopg2-binary
```

### Erro: "URL inválida"

**Causa:** A URL não está no formato correto.

**Solução:** Verifique se copiou a URL completa:
- ✅ Correto: `postgresql://user:pass@host.render.com/dbname`
- ❌ Errado: `host.render.com` (só o host)
- ❌ Errado: `psql -h host...` (comando PSQL)

### Erro: "Connection refused" ou "timeout"

**Possíveis causas:**
1. Database não está "Available" (verde) no Render
2. URL expirada ou incorreta
3. Firewall bloqueando a conexão

**Soluções:**
1. Verifique no Render se o database está ativo (verde)
2. Gere uma nova URL no Render (às vezes expira)
3. Tente de outra rede (use hotspot do celular para testar)

### Erro: "Database does not exist"

**Solução:** Certifique-se de que copiou a "External Database URL" e não outra URL.

---

## 🎯 Método Alternativo: DBeaver (Interface Gráfica)

Se preferir interface gráfica:

### 1. Instalar DBeaver

Baixe em: https://dbeaver.io/download/

### 2. Criar Nova Conexão

1. Abra o DBeaver
2. Clique em **"Nova Conexão"** (ou Database > New Database Connection)
3. Selecione **PostgreSQL**
4. Clique **"Avançar"**

### 3. Configurar Conexão

Pegue as informações no Render (Info > Connections):

```
Host:     xxxxxx.render.com
Port:     5432
Database: seu_database_name
Username: seu_username
Password: sua_senha
```

Marque **"Salvar senha"** e clique **"Testar Conexão"**.

### 4. Executar SQL

1. Conecte ao banco (duplo clique na conexão)
2. Clique com botão direito na conexão > **SQL Editor** > **New SQL Script**
3. Cole o SQL:

```sql
CREATE TABLE api_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    level VARCHAR(50),
    event VARCHAR(100),
    logger VARCHAR(50),
    method VARCHAR(10),
    path VARCHAR(500),
    status_code INTEGER,
    process_time_ms FLOAT,
    client_host VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhor performance
CREATE INDEX idx_api_logs_timestamp ON api_logs(timestamp);
CREATE INDEX idx_api_logs_path ON api_logs(path);
CREATE INDEX idx_api_logs_status_code ON api_logs(status_code);
```

4. Execute: **Ctrl+Enter** ou clique no botão ▶
5. Verifique na árvore de navegação: **Tables** > **api_logs**

---

## ✅ Verificar se Funcionou

Depois de criar a tabela, você pode verificar executando:

### Via Script Python

Crie `test_connection.py`:
```python
import psycopg2

DATABASE_URL = "postgresql://..."  # Cole sua URL

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("SELECT * FROM api_logs LIMIT 5;")
print("✅ Tabela existe!")
print(f"📊 Registros: {cur.rowcount}")

cur.close()
conn.close()
```

Execute:
```bash
python test_connection.py
```

### Via SQL (DBeaver ou script)

```sql
-- Ver estrutura
\d api_logs

-- Contar registros
SELECT COUNT(*) FROM api_logs;

-- Ver primeiros registros
SELECT * FROM api_logs LIMIT 10;
```

---

## 📚 Próximos Passos

Depois de criar a tabela:

1. ✅ **Configurar API** para gravar logs no PostgreSQL
2. ✅ **Configurar Dashboard** para ler logs do PostgreSQL
3. ✅ **Adicionar variável** `DATABASE_URL` nos serviços do Render

Veja [DEPLOY_DASHBOARD.md](DEPLOY_DASHBOARD.md) para detalhes de implementação.

---

## 🆘 Ainda com Problemas?

Se nenhuma das soluções funcionou:

1. **Copie e cole aqui:**
   - A mensagem de erro completa
   - O comando que você executou
   - Tipo de sistema operacional (Windows/Mac/Linux)

2. **Informações úteis:**
   - O database está verde (Available) no Render?
   - Consegue ver a "External Database URL" no Render?
   - Qual método tentou usar?

Vou te ajudar a resolver! 💪
