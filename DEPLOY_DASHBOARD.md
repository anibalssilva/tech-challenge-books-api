# Deploy do Dashboard no Render 📊

Guia completo para fazer deploy do dashboard de monitoramento no Render.

## 📋 Pré-requisitos

- Conta no Render (gratuita): https://render.com
- Repositório Git atualizado com os arquivos necessários
- API já deployada no Render (opcional, mas recomendado)

## 🚀 Opção 1: Deploy Standalone (Dashboard Independente)

Esta opção é ideal para visualizar o dashboard sem dados reais, ou para desenvolvimento.

### Passo 1: Criar Web Service no Render

1. Acesse https://dashboard.render.com
2. Clique em **"New +"** → **"Web Service"**
3. Conecte seu repositório:
   - Autorize o Render no GitHub
   - Selecione: `anibalssilva/tech-challenge-books-api`

### Passo 2: Configurar o Web Service

Preencha os seguintes campos:

| Campo | Valor |
|-------|-------|
| **Name** | `tech-challenge-dashboard` |
| **Region** | Oregon (US West) ou outra |
| **Branch** | `main` |
| **Root Directory** | (deixe vazio) |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `bash start_dashboard.sh` |
| **Instance Type** | `Free` |

### Passo 3: Variáveis de Ambiente (Opcional)

Clique em **"Advanced"** → **"Add Environment Variable"**:

| Key | Value | Descrição |
|-----|-------|-----------|
| `LOG_FILE_PATH` | `./logs/api.log` | Caminho do arquivo de log (padrão) |
| `PORT` | `10000` | Porta do servidor (automático) |

### Passo 4: Deploy

1. Clique em **"Create Web Service"**
2. Aguarde o build (5-10 minutos no primeiro deploy)
3. Quando aparecer **"Live"**, seu dashboard está no ar! 🎉

### Passo 5: Acessar o Dashboard

URL do dashboard: `https://tech-challenge-dashboard.onrender.com`

**⚠️ Nota:** Como está rodando sem a API, o dashboard mostrará:
- Mensagem: "Arquivo de log não encontrado"
- Interface vazia esperando por dados
- Isso é normal e esperado!

---

## 🔗 Opção 2: Dashboard + API Integrados (Recomendado para Produção)

Para ter dados reais no dashboard, você precisa integrar com a API.

### Arquitetura Recomendada

```
┌─────────────────┐         ┌──────────────────┐
│   API Service   │────────▶│  PostgreSQL DB   │
│  (FastAPI)      │         │   (Logs/Data)    │
└────────┬────────┘         └──────────────────┘
         │
         │ (grava logs)
         │
         ▼
┌─────────────────┐
│   Dashboard     │
│  (Streamlit)    │────────▶ Lê logs do DB
└─────────────────┘
```

### Implementação com PostgreSQL

Para fazer o dashboard funcionar com dados reais no Render:

#### 1. Criar PostgreSQL Database

1. No Render Dashboard, clique em **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name:** `tech-challenge-db`
   - **Database:** `books_api_logs`
   - **User:** (gerado automaticamente)
   - **Region:** Mesma da API
   - **Instance Type:** `Free`

3. Anote a **Internal Database URL** (formato: `postgresql://...`)

#### 2. Modificar API para Gravar Logs no PostgreSQL

Você precisará modificar o código para gravar logs no banco ao invés de arquivo:

```python
# Adicionar no requirements.txt
# psycopg2-binary==2.9.9

# Criar tabela de logs
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
    client_host VARCHAR(100)
);
```

#### 3. Modificar Dashboard para Ler do PostgreSQL

```python
# No dashboard/dashboard.py
import psycopg2
import os

def load_logs_from_db():
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        query = "SELECT * FROM api_logs ORDER BY timestamp DESC LIMIT 10000"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao conectar ao banco: {e}")
        return pd.DataFrame()
```

#### 4. Adicionar Variável de Ambiente

No dashboard service, adicione:
- **DATABASE_URL:** (cole a Internal Database URL do PostgreSQL)

---

## 🎯 Opção 3: Deploy Local para Desenvolvimento

Para desenvolver e testar localmente:

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Executar API e Dashboard em Paralelo

**Terminal 1 - API:**
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Dashboard:**
```bash
streamlit run dashboard/dashboard.py
```

**Terminal 3 - Gerar Tráfego (Opcional):**
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Criar usuário
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"username": "teste", "password": "senha123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "teste", "password": "senha123"}'
```

### 3. Acessar Dashboard

Abra o navegador em: `http://localhost:8501`

---

## 📊 Recursos do Dashboard

O dashboard oferece:

- 📈 **Métricas de Performance**: Latência, tempo de resposta médio
- 🔍 **Análise de Endpoints**: Requisições por endpoint, endpoints mais lentos
- ❗ **Monitoramento de Erros**: Taxa de erros, distribuição de status codes
- 🌐 **Análise de Tráfego**: Requisições por minuto/hora (RPM/RPH)
- 👥 **Análise de Clientes**: Top clientes por requisições
- 📜 **Logs Recentes**: Últimos 100 logs em tempo real

---

## 🔧 Troubleshooting

### Dashboard mostra "Arquivo de log não encontrado"

**Causa:** O dashboard não consegue acessar o arquivo de log da API.

**Soluções:**
1. **Local:** Verifique se a API está rodando e gerando logs em `./logs/api.log`
2. **Render:** Implemente a Opção 2 com PostgreSQL
3. **Temporário:** O dashboard funcionará sem dados (modo demo)

### Dashboard não carrega/timeout

**Causa:** Plano Free do Render "hiberna" após inatividade.

**Solução:**
- Primeira requisição após hibernação demora 30-60 segundos
- Para produção, considere plano pago para manter sempre ativo

### Erro "Port already in use"

**Causa:** Porta já está sendo usada por outro processo.

**Solução:**
```bash
# Encontrar processo usando a porta
lsof -i :8501  # ou :8000 para API

# Matar o processo
kill -9 <PID>
```

---

## 💰 Custos e Limitações

### Plano Free (Render)

- ✅ 750 horas/mês gratuitas
- ✅ Deploy ilimitados
- ⚠️ Serviço hiberna após 15min de inatividade
- ⚠️ Primeira requisição após hibernação: 30-60s
- ⚠️ Sistema de arquivos efêmero (dados perdidos após restart)

### Recomendações

- **Desenvolvimento:** Use localmente (100% gratuito e sem limitações)
- **Produção:** Considere Render Starter ($7/mês) ou implemente PostgreSQL
- **Alternativa:** Use serviços de monitoramento como Datadog, New Relic (têm planos free)

---

## 📚 Próximos Passos

Depois do deploy bem-sucedido:

1. ✅ **Testar Dashboard:** Acesse a URL e verifique funcionamento
2. ✅ **Integrar com API:** Implemente logs em PostgreSQL (Opção 2)
3. ✅ **Configurar Alertas:** Configure notificações para erros críticos
4. ✅ **Monitorar Performance:** Acompanhe métricas regularmente
5. ✅ **Otimizar Queries:** Indexe tabelas de logs para melhor performance

---

## 🆘 Precisa de Ajuda?

- 📖 **Documentação Render:** https://render.com/docs
- 📖 **Documentação Streamlit:** https://docs.streamlit.io
- 🐛 **Issues do Projeto:** https://github.com/anibalssilva/tech-challenge-books-api/issues

---

**✨ Dica Final:** Para melhor experiência em produção, recomendo implementar a Opção 2 (PostgreSQL) para ter persistência de logs e métricas em tempo real! 🚀
