import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime
import json

# Lista de paths que você quer ignorar nos logs
PATHS_TO_IGNORE = [
    '/',
    '/favicon.ico',
    '/apple-touch-icon.png',
    '/apple-touch-icon-precomposed.png',
    '/openapi.json',
    '/api/v1/logs',
    '/api/v1/db-logs'
]

# No render: 'https://tech-challenge-books-api-fxmj.onrender.com'
# Na maquina local: http://127.0.0.1:8000
API_URL = os.getenv('API_URL', 'https://tech-challenge-books-api-fxmj.onrender.com')
DEFAULT_LOG_LIMIT = 1000
DEFAULT_TIMEOUT = 10

def create_filter_section(logs_api_df: pd.DataFrame) -> None:
    st.sidebar.subheader("Filtros da API")
    # Verifica se o DataFrame da API não está vazio
    if 'level' in logs_api_df.columns:
        date_options = logs_api_df['timestamp'].dt.date.unique().tolist()
        # Cria o widget multiselect para a API
        selected_levels_api = st.sidebar.multiselect(
            "Data da requisição:",
            options=date_options,
            default=date_options
        )

        if not selected_levels_api:
            logs_api_df = logs_api_df.copy()
            st.sidebar.caption("Nenhuma data selecionada, mostrando todos os dados.")
        
        else:
            logs_api_df = logs_api_df[logs_api_df['timestamp'].dt.date.isin(selected_levels_api)]

    else:
        logs_api_df = pd.DataFrame()
        st.sidebar.text("Nenhum log da API para filtrar.")

def create_metrics_section(api_requests_df: pd.DataFrame) -> None:
    """Cria a seção de métricas principais da API."""
    col1, col2, col3, col4, col5 = st.columns(5)

    # KPIs da API
    total_requests = len(api_requests_df)
    avg_response_time = api_requests_df['process_time_ms'].astype(float).mean()
    error_rate = (len(api_requests_df[api_requests_df['status_code'] >= 400]) / total_requests * 100) if total_requests > 0 else 0
    avg_response_time_p50 = api_requests_df['process_time_ms'].astype(float).median()
    avg_response_time_p95 = api_requests_df['process_time_ms'].astype(float).quantile(0.95)

    col1.metric("Total de Requisições", f"{total_requests}")
    col2.metric("Tempo Médio de Resposta", f"{avg_response_time:.2f} ms")
    col4.metric("Latência Média (p50)", f"{avg_response_time_p50:.2f} ms")
    col5.metric("Latência p95", f"{avg_response_time_p95:.2f} ms")
    col3.metric("Taxa de Erros", f"{error_rate:.2f}%")

def create_performance_charts(api_requests_df: pd.DataFrame) -> None:
    # --- Gráficos da API ---   
    # --- Métricas de Performance (Latência) ---

    st.header("📉 Latência ao Longo do Tempo")
    fig_latency = px.line(
        api_requests_df,
        x='timestamp',
        y='process_time_ms',
        title='Latência das Requisições ao Longo do Tempo',
        labels={'process_time_ms': 'Tempo de Processamento (ms)', 'timestamp': 'Timestamp'}
    )
    st.plotly_chart(fig_latency, use_container_width=True)

    st.header("📊 Endpoints Mais Lentos")
    slowest_endpoints = api_requests_df.groupby('path')['process_time_ms'].mean().reset_index().sort_values(by='process_time_ms', ascending=False).head(10)
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
        api_requests_df,
        x='process_time_ms',
        nbins=50,
        title='Distribuição da Latência das Requisições',
        labels={'process_time_ms': 'Tempo de Processamento (ms)'}
    )
    st.plotly_chart(fig_dist_latency, use_container_width=True)

    # --- Métricas de Uso e Tráfego ---
    st.header("🌐 Requisições por Minuto (RPS/RPM)")
    api_requests_df['minute'] = api_requests_df['timestamp'].dt.floor('T')
    rps = api_requests_df.groupby('minute').size().reset_index(name='requests_per_minute')
    fig_rps = px.line(rps, x='minute', y='requests_per_minute', title='Requisições por Minuto (RPM)', labels={'requests_per_minute': 'Requisições por Minuto', 'minute': 'Minute'})
    st.plotly_chart(fig_rps, use_container_width=True)

    st.header("🔍 Requisições por Endpoint")
    reqs_per_endpoint = api_requests_df['path'].value_counts().reset_index()
    reqs_per_endpoint.columns = ['Endpoint', 'Contagem']
    fig1 = px.bar(reqs_per_endpoint, x='Endpoint', y='Contagem', title='Requisições por Endpoint')
    st.plotly_chart(fig1, use_container_width=True)

    st.header("🔧 Requisições por Método HTTP")
    reqs_per_method = api_requests_df['method'].value_counts().reset_index()
    reqs_per_method.columns = ['Método', 'Contagem']
    fig_method = px.pie(reqs_per_method, names='Método', values='Contagem', title='Requisições por Método HTTP')
    st.plotly_chart(fig_method, use_container_width=True)

    st.header("👥 Top Clientes por Requisições")
    top_clients = api_requests_df['client_host'].value_counts().reset_index().head(10)
    top_clients.columns = ['Client Host', 'Contagem']
    fig_clients = px.bar(top_clients, x='Client Host', y='Contagem', title='Top 10 Clientes por Requisições')
    st.plotly_chart(fig_clients, use_container_width=True)

    # --- Metricas de Erro ---
    st.header("❗ Erros ao longo do tempo")
    errors_over_time = api_requests_df[api_requests_df['status_code'] >= 400].groupby(api_requests_df['timestamp'].dt.floor('T')).size().reset_index(name='error_count')
    fig_errors_time = px.line(errors_over_time, x='timestamp', y='error_count', title='Erros ao Longo do Tempo', labels={'error_count': 'Número de Erros', 'timestamp': 'Timestamp'})
    st.plotly_chart(fig_errors_time, use_container_width=True)

    st.header("🚦 Endpoints com Mais Erros")
    errors_per_endpoint = api_requests_df[api_requests_df['status_code'] >= 400]['path'].value_counts().reset_index()
    errors_per_endpoint.columns = ['Endpoint', 'Contagem de Erros']
    fig_errors_endpoint = px.bar(errors_per_endpoint, x='Endpoint', y='Contagem de Erros', title='Endpoints com Mais Erros')
    st.plotly_chart(fig_errors_endpoint, use_container_width=True)

    st.header("📋 Requisições por Status Code")
    reqs_per_status = api_requests_df['status_code'].value_counts().reset_index()
    reqs_per_status.columns = ['Status Code', 'Contagem']
    fig_status = px.bar(reqs_per_status, x='Status Code', y='Contagem', title='Requisições por Status Code')
    st.plotly_chart(fig_status, use_container_width=True)


    # --- Logs recentes ---
    st.header("📜 Logs Recentes API")
    st.dataframe(api_requests_df[['timestamp', 'level', 'message', 'method','path', 'status_code']].tail(100))

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or 'path' in df.columns:
        return df
    return df[~df['path'].isin(PATHS_TO_IGNORE)]

def display_empty_state():
    print("⚠️ Nenhum log disponível para exibição no dashboard.")
    st.warning("⚠️ Nenhum log disponível.")
    st.info("💡 **Dica**: Execute algumas requisições na API para gerar logs e visualizar dados no dashboard.")
    st.stop()

# Função para carregar logs do endpoint HTTP (para Render)
def load_logs_from_api(limit: int = 1000):
    """
    Busca os logs mais recentes da API no endpoint do banco de dados
    e armazena o resultado em cache por 60 segundos.
    """
    endpoint = f"{API_URL}/api/v1/db-logs?limit={limit}"
    
    try:
        response = requests.get(endpoint, timeout=10)
        
        if response.status_code == 200:
            logs_data = response.json()

            df = pd.DataFrame(logs_data.get("logs", []))
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                return df
            
            return pd.DataFrame()
        
    # MODIFICAÇÃO 5: Handlers de erro mais claros para o usuário
    except requests.exceptions.HTTPError as e:
        st.error(f"Erro na API: {e.response.status_code} - {e.response.text}")
        return pd.DataFrame()
    except requests.exceptions.ConnectionError:
        st.error(f"Erro de conexão: Não foi possível se conectar à API em {API_URL}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Um erro inesperado ocorreu ao carregar os logs: {e}")
        return pd.DataFrame()

def main():
    # Configuração da página
    st.set_page_config(page_title="Dashboard de Monitoramento", layout="wide")
    st.title("📊 Dashboard de Monitoramento API")
    # Carrega os logs da API
    logs_api_df = load_logs_from_api()
    if logs_api_df.empty:
        display_empty_state()
        return
    
    # Aplica filtros nos DataFrame
    filtered_df = filter_dataframe(logs_api_df)

    # Cria a seção de filtros
    create_filter_section(filtered_df)

    # Cria a seção de métricas principais
    create_metrics_section(filtered_df)
    create_performance_charts(filtered_df)

if __name__ == "__main__":
    main()
