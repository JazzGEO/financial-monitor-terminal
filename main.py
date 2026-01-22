import streamlit as st
import pandas as pd
import requests
from textblob import TextBlob
from datetime import datetime
import os
import plotly.express as px
import nltk

# --- PREPARAÇÃO DO AMBIENTE DE IA ---
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

def fetch_market_data():
    url = f"https://economia.awesomeapi.com.br/last/{','.join(CURRENCIES)}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def run_sentiment_analysis(pct_change):
    try:
        change = float(pct_change)
        if change > 0.05: return "BULLISH (Otimista)", "🟢"
        elif change < -0.05: return "BEARISH (Pessimista)", "🔴"
        else: return "NEUTRAL", "⚪"
    except:
        return "NEUTRAL", "⚪"

def auto_update_data():
    raw_data = fetch_market_data()
    # Verificação robusta: se raw_data não for um dicionário, ignora o processamento
    if raw_data and isinstance(raw_data, dict):
        records = []
        for key, info in raw_data.items():
            # Verifica se 'info' é realmente um dicionário antes de usar .get()
            if isinstance(info, dict):
                variacao = info.get('pctChange', '0')
                sentiment, icon = run_sentiment_analysis(variacao)
                
                records.append({
                    "Timestamp": datetime.now().strftime("%H:%M:%S"),
                    "Asset": info.get('name', 'Desconhecido').split('/')[0],
                    "Price": float(info.get('bid', 0)),
                    "Change_%": variacao,
                    "Sentiment": sentiment
                })
        
        if not records:
            return None

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

# --- FLUXO DE CARREGAMENTO ---
df = None
if not os.path.exists(EXCEL_DB):
    df = auto_update_data()
else:
    try:
        df = pd.read_excel(EXCEL_DB)
        df_atualizado = auto_update_data()
        if df_atualizado is not None:
            df = df_atualizado
    except:
        df = auto_update_data()

# --- INTERFACE VISUAL ---
st.title("📊 Financial Data Analytics Terminal")
st.markdown(f"**Status:** Operacional | **Data:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

if df is not None and not df.empty:
    # 1. Cards de Métricas
    latest_data = df.groupby('Asset').last().reset_index()
    cols = st.columns(4)
    
    for i, row in latest_data.iterrows():
        with cols[i]:
            st.metric(label=row['Asset'], value=f"R$ {row['Price']:.2f}", delta=f"{row['Change_%']}%")
            st.write(f"Status IA: {row['Sentiment']}")

    # 2. Gráfico de Tendência Histórica
    st.markdown("---")
    fig = px.line(df, x="Timestamp", y="Price", color="Asset", 
                 title="Análise de Volatilidade Histórica", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # 3. Base de Dados
    with st.expander("📄 Visualizar Log de Dados (Excel)"):
        st.dataframe(df.tail(10), use_container_width=True)

    # 4. Conversor Lateral (Restaurado)
    st.sidebar.header("💱 Conversor de Câmbio")
    input_val = st.sidebar.number_input("Valor em Reais (BRL)", min_value=1.0, value=10.0)
    target = st.sidebar.selectbox("Converter para Ativo:", latest_data['Asset'].unique())
    
    price_target = latest_data[latest_data['Asset'] == target]['Price'].values[0]
    conversao = input_val / price_target
    st.sidebar.subheader(f"{conversao:.2f} {target}")
    
    # 5. Disclaimer de Segurança (Restaurado)
    st.sidebar.markdown("---")
    st.sidebar.warning("""
    **AVISO DE SEGURANÇA:**
    Este sistema é estritamente educacional. Não tome decisões de investimento baseando-se nestes dados. O autor não se responsabiliza por perdas financeiras.
    """)
else:
    st.error("Erro ao carregar base de dados. Verifique a conexão com a API e recarregue a página.")