import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import re
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Dashboard de Monitoramento", layout="wide")
st.title("📊 Dashboard de Monitoramento API")

LOG_FILE_API = './logs/api.log'

# Função para carregar os logs
def load_logs(file_path):
    try:
        df = pd.read_json(file_path, lines=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except FileNotFoundError:
        st.error(f"Arquivo de log não encontrado: {file_path}")
        return pd.DataFrame()
    except ValueError:
        st.warning("Arquivo de log está vazio ou mal formatado.")
        return pd.DataFrame()

# Carrega os dados
logs_api_df = load_logs(LOG_FILE_API)

# Paths para ignorar
# Lista de paths que você quer ignorar
paths_para_ignorar = [
    '/',
    '/favicon.ico',
    '/apple-touch-icon.png',
    '/apple-touch-icon-precomposed.png'
]

# Filtra os logs para remover os paths indesejados
if not logs_api_df.empty and 'path' in logs_api_df.columns:
    logs_api_df = logs_api_df[~logs_api_df['path'].isin(paths_para_ignorar)]

# --- Filtro para Logs da API ---

st.sidebar.subheader("Filtros da API")
# Verifica se o DataFrame da API não está vazio
if not logs_api_df.empty and 'level' in logs_api_df.columns:
    date_options = logs_api_df['timestamp'].dt.date.unique().tolist()
    # Cria o widget multiselect para a API
    selected_levels_api = st.sidebar.multiselect(
         "Data da requisição:",
         options=date_options,
         default=date_options
    )

    if not selected_levels_api:
        api_logs_filtered = logs_api_df.copy()
        st.sidebar.caption("Nenhuma data selecionada, mostrando todos os dados.")
    
    else:
        api_logs_filtered = logs_api_df[logs_api_df['timestamp'].dt.date.isin(selected_levels_api)]

else:
    api_logs_filtered = pd.DataFrame()
    st.sidebar.text("Nenhum log da API para filtrar.")

# # Separa logs da API e do Scraper
api_logs = api_logs_filtered[api_logs_filtered['logger'] == 'api']

# --- Seção de Métricas da API ---
st.header("📈 Performance da API")
col1, col2, col3, col4, col5 = st.columns(5)

if not api_logs.empty:
    # KPIs da API
    total_requests = len(api_logs['event'] == 'request_finished')
    avg_response_time = api_logs['process_time_ms'].astype(float).mean()
    error_rate = (len(api_logs[api_logs['status_code'] >= 400]) / total_requests * 100) if total_requests > 0 else 0
    avg_response_time_p50 = api_logs['process_time_ms'].astype(float).median()
    avg_response_time_p95 = api_logs['process_time_ms'].astype(float).quantile(0.95)

    col1.metric("Total de Requisições", f"{total_requests}")
    col2.metric("Tempo Médio de Resposta", f"{avg_response_time:.2f} ms")
    col4.metric("Latência Média (p50)", f"{avg_response_time_p50:.2f} ms")
    col5.metric("Latência p95", f"{avg_response_time_p95:.2f} ms")
    col3.metric("Taxa de Erros", f"{error_rate:.2f}%")

# --- Gráficos da API ---   
    # --- Métricas de Performance (Latência) ---

    st.header("📉 Latência ao Longo do Tempo")
    fig_latency = px.line(
        api_logs,
        x='timestamp',
        y='process_time_ms',
        title='Latência das Requisições ao Longo do Tempo',
        labels={'process_time_ms': 'Tempo de Processamento (ms)', 'timestamp': 'Timestamp'}
    )
    st.plotly_chart(fig_latency, use_container_width=True)

    st.header("📊 Endpoints Mais Lentos")
    slowest_endpoints = api_logs.groupby('path')['process_time_ms'].mean().reset_index().sort_values(by='process_time_ms', ascending=False).head(10)
    fig_slowest = px.bar(
        slowest_endpoints,
        x='path',
        y='process_time_ms',
        title='Top 10 Endpoints Mais Lentos',
        labels={'process_time_ms': 'Tempo Médio de Processamento (ms)', 'path': 'Endpoint'}
    )
    st.plotly_chart(fig_slowest, use_container_width=True)

    st.header("📈 Distribuição da Latência")
    fig_dist_latency = px.histogram(
        api_logs,
        x='process_time_ms',
        nbins=50,
        title='Distribuição da Latência das Requisições',
        labels={'process_time_ms': 'Tempo de Processamento (ms)'}
    )
    st.plotly_chart(fig_dist_latency, use_container_width=True)

    # --- Métricas de Uso e Tráfego ---
    st.header("🌐 Requisições por Minuto/Hora (RPS/RPM)")
    api_logs['minute'] = api_logs['timestamp'].dt.floor('T')
    api_logs['hour'] = api_logs['timestamp'].dt.floor('H')
    rps = api_logs.groupby('minute').size().reset_index(name='requests_per_minute')
    rpm = api_logs.groupby('hour').size().reset_index(name='requests_per_hour')
    fig_rps = px.line(rps, x='minute', y='requests_per_minute', title='Requisições por Minuto (RPM)', labels={'requests_per_minute': 'Requisições por Minuto', 'minute': 'Minute'})
    fig_rpm = px.line(rpm, x='hour', y='requests_per_hour', title='Requisições por Hora (RPH)', labels={'requests_per_hour': 'Requisições por Hora', 'hour': 'Hour'})
    st.plotly_chart(fig_rps, use_container_width=True)
    st.plotly_chart(fig_rpm, use_container_width=True)

    st.header("🔍 Requisições por Endpoint")
    reqs_per_endpoint = api_logs['path'].value_counts().reset_index()
    reqs_per_endpoint.columns = ['Endpoint', 'Contagem']
    fig1 = px.bar(reqs_per_endpoint, x='Endpoint', y='Contagem', title='Requisições por Endpoint')
    st.plotly_chart(fig1, use_container_width=True)

    st.header("🔧 Requisições por Método HTTP")
    reqs_per_method = api_logs['method'].value_counts().reset_index()
    reqs_per_method.columns = ['Método', 'Contagem']
    fig_method = px.pie(reqs_per_method, names='Método', values='Contagem', title='Requisições por Método HTTP')
    st.plotly_chart(fig_method, use_container_width=True)

    st.header("👥 Top Clientes por Requisições")
    top_clients = api_logs['client_host'].value_counts().reset_index().head(10)
    top_clients.columns = ['Client Host', 'Contagem']
    fig_clients = px.bar(top_clients, x='Client Host', y='Contagem', title='Top 10 Clientes por Requisições')
    st.plotly_chart(fig_clients, use_container_width=True)

    # --- Metricas de Erro ---
    st.header("❗ Erros ao longo do tmpo")
    errors_over_time = api_logs[api_logs['status_code'] >= 400].groupby(api_logs['timestamp'].dt.floor('T')).size().reset_index(name='error_count')
    fig_errors_time = px.line(errors_over_time, x='timestamp', y='error_count', title='Erros ao Longo do Tempo', labels={'error_count': 'Número de Erros', 'timestamp': 'Timestamp'})
    st.plotly_chart(fig_errors_time, use_container_width=True)

    st.header("🚦 Endpoints com Mais Erros")
    errors_per_endpoint = api_logs[api_logs['status_code'] >= 400]['path'].value_counts().reset_index()
    errors_per_endpoint.columns = ['Endpoint', 'Contagem de Erros']
    fig_errors_endpoint = px.bar(errors_per_endpoint, x='Endpoint', y='Contagem de Erros', title='Endpoints com Mais Erros')
    st.plotly_chart(fig_errors_endpoint, use_container_width=True)

    st.header("📋 Requisições por Status Code")
    reqs_per_status = api_logs['status_code'].value_counts().reset_index()
    reqs_per_status.columns = ['Status Code', 'Contagem']
    fig_status = px.bar(reqs_per_status, x='Status Code', y='Contagem', title='Requisições por Status Code')
    st.plotly_chart(fig_status, use_container_width=True)


# --- Logs recentes ---
    st.header("📜 Logs Recentes API")
    st.dataframe(api_logs[['timestamp', 'level', 'event', 'method','path', 'status_code']].tail(100))
    
