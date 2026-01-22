import streamlit as st
import pandas as pd
import requests
from textblob import TextBlob
from datetime import datetime
import os
import plotly.express as px
import nltk

# --- CORREÇÃO PARA O STREAMLIT CLOUD ---
# Força o download dos pacotes de IA necessários na nuvem
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('brown')
    nltk.download('wordnet')

st.set_page_config(page_title="Financial Data Analytics Terminal", layout="wide")

EXCEL_DB = "currency_data.xlsx"
CURRENCIES = ["USD-BRL", "EUR-BRL", "GBP-BRL", "JPY-BRL"]

def fetch_market_data():
    url = f"https://economia.awesomeapi.com.br/last/{','.join(CURRENCIES)}"
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except:
        return None

def run_sentiment_analysis(pct_change):
    try:
        # CONVERSÃO SEGURA: Transforma o texto da API em número decimal
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
            # Pegamos o valor com segurança
            variacao = info.get('pctChange', 0)
            sentiment, icon = run_sentiment_analysis(variacao)
            
            records.append({
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Asset": info.get('name', 'Unknown').split('/')[0],
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
        
        # Salva no Excel temporário da nuvem
        final_df.to_excel(EXCEL_DB, index=False)
        return final_df
    return None

# --- EXECUÇÃO ---
# Tenta carregar dados existentes ou busca novos
df = None
if os.path.exists(EXCEL_DB):
    try:
        df = pd.read_excel(EXCEL_DB)
    except:
        df = auto_update_data()
else:
    df = auto_update_data()

# Se ainda estiver vazio, tenta uma última atualização
if df is None:
    df = auto_update_data()

st.title("📊 Financial Data Analytics Terminal")
st.caption("Educational Portfolio Project - Real-time Market Data")

if df is not None and not df.empty:
    latest_data = df.groupby('Asset').last().reset_index()
    cols = st.columns(4)
    
    for i, row in latest_data.iterrows():
        with cols[i]:
            st.metric(label=row['Asset'], value=f"R$ {row['Price']:.2f}", delta=f"{row['Change_%']}%")
            st.write(f"Sentiment: {row['Sentiment']}")

    st.markdown("---")
    fig = px.line(df, x="Timestamp", y="Price", color="Asset", 
                 title="Market Volatility Analysis", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Security Warning & Disclaimer"):
        st.warning("This application is for educational purposes only. Do not use this data for actual financial investments. Market data may be delayed.")
else:
    st.info("Sincronizando dados com a API... Por favor, recarregue a página em alguns segundos.")