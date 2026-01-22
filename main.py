import streamlit as st
import pandas as pd
import requests
from textblob import TextBlob
from datetime import datetime
import os
import plotly.express as px
import nltk

# --- CORREÇÃO TÉCNICA PARA O AMBIENTE NUVEM ---
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('brown')
    nltk.download('wordnet')

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="Financial Data Analytics Terminal", layout="wide")

EXCEL_DB = "currency_data.xlsx"
CURRENCIES = ["USD-BRL", "EUR-BRL", "GBP-BRL", "JPY-BRL"]

# --- FUNÇÕES TÉCNICAS (COM TRATAMENTO DE ERRO) ---
def fetch_market_data():
    url = f"https://economia.awesomeapi.com.br/last/{','.join(CURRENCIES)}"
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except:
        return None

def run_sentiment_analysis(pct_change):
    try:
        # Conversão segura para evitar o TypeError
        change = float(pct_change)
        if change > 0.05: return "BULLISH (Otimista)", "🟢"
        elif change < -0.05: return "BEARISH (Pessimista)", "🔴"
        else: return "NEUTRAL", "⚪"
    except:
        return "NEUTRAL", "⚪"

def auto_update_data():
    raw_data = fetch_market_data()
    if raw_data:
        records = []
        for key, info in raw_data.items():
            variacao = info.get('pctChange', '0')
            sentiment, icon = run_sentiment_analysis(variacao)
            
            records.append({
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Asset": info.get('name', 'Desconhecido').split('/')[0],
                "Price": float(info.get('bid', 0)),
                "Change_%": variacao,
                "Sentiment": sentiment
            })
        
        new_df = pd.DataFrame(records)
        if os.path.exists(EXCEL_DB):
            try:
                old_df = pd.read_excel(EXCEL_DB)
                final_df = pd.concat([old_df, new_df], ignore_index=True).drop_duplicates()
            except:
                final_df = new_df
        else:
            final_df = new_df
        
        final_df.to_excel(EXCEL_DB, index=False)
        return final_df
    return None

# --- EXECUÇÃO DE DADOS ---
if not os.path.exists(EXCEL_DB):
    df = auto_update_data()
else:
    df = pd.read_excel(EXCEL_DB)
    df_atualizado = auto_update_data()
    if df_atualizado is not None:
        df = df_atualizado

# --- INTERFACE PRINCIPAL ---
st.title("📊 Financial Data Analytics Terminal")
st.markdown(f"**Status:** Operacional | **Atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

if df is not None and not df.empty:
    # 1. Cards de Métricas
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

    # 3. Tabela de Dados (Histórico Excel)
    with st.expander("📄 Visualizar Base de Dados (Excel)"):
        st.dataframe(df.tail(10), use_container_width=True)

    # 4. Conversor na Barra Lateral (RESTAURADO)
    st.sidebar.header("💱 Conversor Rápido")
    input_val = st.sidebar.number_input("Valor em Reais (BRL)", min_value=1.0, value=10.0)
    target = st.sidebar.selectbox("Converter para:", latest_data['Asset'].unique())
    
    price_target = latest_data[latest_data['Asset'] == target]['Price'].values[0]
    conversao = input_val / price_target
    st.sidebar.subheader(f"{conversao:.2f} {target}")
    
    # 5. Alerta de Segurança e Disclaimer
    st.sidebar.markdown("---")
    st.sidebar.warning("""
    **AVISO DE SEGURANÇA:**
    Este sistema é para fins educacionais. Não tome decisões financeiras ou investimentos baseando-se apenas nestes dados.
    """)

else:
    st.error("Conecte-se à internet para carregar os dados financeiros.")