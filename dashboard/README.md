# Dashboard de Monitoramento da API

Dashboard interativo criado com Streamlit para monitorar métricas e logs da API de livros.

## Funcionalidades

- 📈 **Performance da API**: Métricas de tempo de resposta, latência (p50, p95)
- 🌐 **Tráfego**: Requisições por minuto/hora (RPM/RPH)
- 🔍 **Análise de Endpoints**: Requisições por endpoint e endpoints mais lentos
- ❗ **Monitoramento de Erros**: Taxa de erros, erros ao longo do tempo
- 👥 **Análise de Clientes**: Top clientes por requisições
- 📋 **Status Codes**: Distribuição de códigos de resposta HTTP
- 📜 **Logs Recentes**: Visualização dos últimos 100 logs

## Como Executar Localmente

### Pré-requisitos

- Python 3.10+
- API rodando e gerando logs em `./logs/api.log`

### Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

### Execução

2. Execute o dashboard:
```bash
streamlit run dashboard/dashboard.py
```

3. O dashboard abrirá automaticamente no navegador em: `http://localhost:8501`

## Estrutura dos Logs

O dashboard espera logs em formato JSON com os seguintes campos:

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

## Filtros Disponíveis

- **Data da Requisição**: Filtre logs por data específica
- **Paths Ignorados**: Automaticamente ignora `/`, `/favicon.ico`, etc.

## Métricas Exibidas

### KPIs Principais
- Total de Requisições
- Tempo Médio de Resposta
- Taxa de Erros (%)
- Latência p50 e p95

### Gráficos
- Latência ao longo do tempo
- Top 10 endpoints mais lentos
- Distribuição de latência
- Requisições por minuto/hora
- Requisições por endpoint
- Requisições por método HTTP
- Top 10 clientes
- Erros ao longo do tempo
- Endpoints com mais erros
- Distribuição de status codes
