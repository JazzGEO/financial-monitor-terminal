import streamlit as st
import pandas as pd
import requests
from textblob import TextBlob
from datetime import datetime
import os
import plotly.express as px

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="Financial Data Analytics Terminal", layout="wide")

EXCEL_DB = "currency_data.xlsx"
CURRENCIES = ["USD-BRL", "EUR-BRL", "GBP-BRL", "JPY-BRL"]

# --- FUNÇÕES TÉCNICAS ---
def fetch_market_data():
    """Consome dados em tempo real da AwesomeAPI"""
    url = f"https://economia.awesomeapi.com.br/last/{','.join(CURRENCIES)}"
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except:
        return None

def run_sentiment_analysis(pct_change):
    """Lógica de IA para sentimento"""
    change = float(pct_change)
    if change > 0.05: return "BULLISH (Otimista)", "🟢"
    elif change < -0.05: return "BEARISH (Pessimista)", "🔴"
    else: return "NEUTRAL", "⚪"

def auto_update_data():
    """Busca dados e salva no Excel automaticamente"""
    raw_data = fetch_market_data()
    if raw_data:
        records = []
        for key, info in raw_data.items():
            sentiment, icon = run_sentiment_analysis(info['pctChange'])
            records.append({
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Asset": info['name'].split('/')[0],
                "Price": float(info['bid']),
                "Change_%": info['pctChange'],
                "Sentiment": sentiment
            })
        
        new_df = pd.DataFrame(records)
        if os.path.exists(EXCEL_DB):
            old_df = pd.read_excel(EXCEL_DB)
            final_df = pd.concat([old_df, new_df], ignore_index=True).drop_duplicates()
        else:
            final_df = new_df
        final_df.to_excel(EXCEL_DB, index=False)
        return final_df
    return None

# --- EXECUÇÃO AUTOMÁTICA AO ABRIR ---
# O sistema tenta carregar o que já existe ou busca novos dados
if not os.path.exists(EXCEL_DB):
    df = auto_update_data()
else:
    df = pd.read_excel(EXCEL_DB)
    # Atualiza com dados novos toda vez que a página recarrega
    df_atualizado = auto_update_data()
    if df_atualizado is not None:
        df = df_atualizado

# --- INTERFACE PRINCIPAL (O QUE O RECRUTADOR VÊ) ---
st.title("📊 Financial Data Analytics Terminal")
st.markdown(f"**Status do Sistema:** Operacional | **Última Atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

if df is not None and not df.empty:
    # 1. Cards de Métricas (Já aparecem prontos)
    latest_data = df.groupby('Asset').last().reset_index()
    cols = st.columns(4)
    
    for i, row in latest_data.iterrows():
        with cols[i]:
            st.metric(label=row['Asset'], value=f"R$ {row['Price']:.2f}", delta=f"{row['Change_%']}%")
            st.write(f"{row['Sentiment']}")

    # 2. Gráfico de Tendência
    st.markdown("---")
    fig = px.line(df, x="Timestamp", y="Price", color="Asset", 
                 title="Análise de Volatilidade em Tempo Real", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # 3. Tabela de Dados (Para mostrar que você tem um banco de dados)
    with st.expander("📄 Visualizar Base de Dados (Excel)"):
        st.dataframe(df.tail(10), use_container_width=True)

    # 4. Conversor na Lateral (Limpo, sem botões feios)
    st.sidebar.header("💱 Conversor Rápido")
    input_val = st.sidebar.number_input("Valor (BRL)", min_value=1.0, value=10.0)
    target = st.sidebar.selectbox("Moeda:", latest_data['Asset'].unique())
    price = latest_data[latest_data['Asset'] == target]['Price'].values[0]
    st.sidebar.subheader(f"{input_val / price:.2f} {target}")

else:
    st.error("Conecte-se à internet para a primeira carga de dados.")