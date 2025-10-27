# Como Testar os Logs e Dashboard

## Problema Identificado

Os logs **ESTÃO FUNCIONANDO**, mas o arquivo está vazio porque **a API não foi executada ainda**.

## Solução: Execute a API e Teste

### Passo 1: Execute a API Localmente

```bash
# Opção 1: Usando uvicorn direto
uvicorn api.main:app --reload

# Opção 2: Usando o Makefile
make run_api
```

A API vai iniciar em: `http://localhost:8000`

### Passo 2: Execute Algumas Requisições

```bash
# Em outro terminal, execute o script de teste:
python test_logs.py
```

OU execute manualmente:

```bash
# Teste o health check (não requer autenticação)
curl http://localhost:8000/api/v1/health

# Teste endpoint protegido (vai retornar 401)
curl http://localhost:8000/api/v1/books

# Acesse o Swagger
# Abra: http://localhost:8000/docs
```

### Passo 3: Verifique se os Logs Foram Gerados

```bash
# Veja o conteúdo do arquivo de log
cat logs/api.log

# Ou acompanhe em tempo real
tail -f logs/api.log
```

Você deve ver logs em formato JSON como:

```json
{"request_id": "abc123", "method": "GET", "path": "/api/v1/health", "client_host": "127.0.0.1", "event": "request_started", "level": "info", "logger": "api", "timestamp": "2025-10-27T23:00:00.000Z"}
{"request_id": "abc123", "method": "GET", "path": "/api/v1/health", "client_host": "127.0.0.1", "status_code": 200, "process_time_ms": 5.23, "event": "request_finished", "level": "info", "logger": "api", "timestamp": "2025-10-27T23:00:00.005Z"}
```

### Passo 4: Execute o Dashboard

```bash
# Execute o dashboard Streamlit
streamlit run dashboard/dashboard.py

# Ou usando o Makefile
make run_dashboard
```

O dashboard vai abrir em: `http://localhost:8501`

## No Render (Produção)

### Verificar Logs no Render

1. Acesse o dashboard do Render
2. Vá no serviço da API
3. Clique em "Logs" no menu lateral
4. Você verá os logs da aplicação

### O Dashboard no Render

O dashboard no Render está configurado para:
- Ler logs de `./logs/api.log` (se existir)
- Ou ler do PostgreSQL (se DATABASE_URL estiver configurada)

**Importante:** No Render, o sistema de arquivos é **efêmero** (é resetado a cada deploy). Por isso, os logs em arquivo **não persistem entre deploys**.

### Solução para Logs Persistentes no Render

Existem 2 opções:

#### Opção 1: Usar Logs do Render (Recomendado)
- Os logs aparecem no painel "Logs" do Render
- Não precisa fazer nada, já funciona automaticamente

#### Opção 2: Salvar Logs no PostgreSQL
- Modificar o código para gravar logs no banco
- O dashboard já está preparado para ler do PostgreSQL (função `load_logs_from_db()`)

## Resumo

✅ **Logging está configurado corretamente**
✅ **Dashboard está configurado corretamente**
❌ **Você precisa executar a API para gerar logs**

Execute a API → Faça requisições → Logs são gerados → Dashboard mostra os dados! 🎉
