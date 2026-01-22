import streamlit as st
import pandas as pd
import requests
from textblob import TextBlob
from datetime import datetime
import os
import plotly.express as px
import nltk

# --- PREPARAÇÃO SILENCIOSA DE AMBIENTE ---
@st.cache_resource
def load_nltk():
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('brown', quiet=True)
        nltk.download('wordnet', quiet=True)
    except:
        pass

load_nltk()

# --- CONFIGURAÇÃO ALPHA VISION ---
st.set_page_config(
    page_title="Alpha Vision",
    layout="wide",
    page_icon="📈"
)

EXCEL_DB = "currency_data.xlsx"
CURRENCIES = ["USD-BRL", "EUR-BRL", "GBP-BRL", "JPY-BRL"]

# Função auxiliar que faltava no seu código
def run_sentiment_analysis(pct_change):
    try:
        change = float(pct_change)
        if change > 0.05:
            return "ALTA FORTE 🟢"
        elif change < -0.05:
            return "BAIXA FORTE 🔴"
        else:
            return "ESTÁVEL ⚪"
    except:
        return "INDETERMINADO ⚪"

def fetch_market_data():
    url = f"https://economia.awesomeapi.com.br/last/{','.join(CURRENCIES)}"
    try:
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def process_and_save_data():
    raw_data = fetch_market_data()
    if not (raw_data and isinstance(raw_data, dict)):
        return None
    
    records = []
    data_atual = datetime.now().strftime("%d/%m/%Y")
    hora_atual = datetime.now().strftime("%H:%M:%S")

    for key, info in raw_data.items():
        if isinstance(info, dict):
            variacao = info.get('pctChange', '0')
            records.append({
                "Timestamp": hora_atual,
                "Data": data_atual,
                "Asset": info.get('name', '').split('/')[0],
                "Price": float(info.get('bid', 0)),
                "Change_Pct": variacao,
                "Sentiment": run_sentiment_analysis(variacao)
            })

    new_df = pd.DataFrame(records)

    if os.path.exists(EXCEL_DB):
        try:
            old_df = pd.read_excel(EXCEL_DB)
            combined_df = pd.concat([old_df, new_df], ignore_index=True).drop_duplicates(subset=['Timestamp', 'Asset'])
            combined_df.to_excel(EXCEL_DB, index=False)
            return combined_df
        except:
            new_df.to_excel(EXCEL_DB, index=False)
            return new_df
    else:
        new_df.to_excel(EXCEL_DB, index=False)
        return new_df

# --- EXECUÇÃO DO FLUXO DE DADOS ---
df_completo = process_and_save_data()

if df_completo is None and os.path.exists(EXCEL_DB):
    try:
        df_completo = pd.read_excel(EXCEL_DB)
    except:
        pass

# --- INTERFACE PÚBLICA ALPHA VISION ---
st.title("♾️ Alpha Vision")
st.caption(f"Última atualização do mercado: {datetime.now().strftime('%H:%M:%S')}")

if df_completo is not None and not df_completo.empty:
    # Filtra as últimas 4 entradas (uma para cada moeda)
    df_recente = df_completo.tail(4).reset_index(drop=True)

    # 1. Painel de Métricas (Cards)
    cols = st.columns(4)
    for i, row in df_recente.iterrows():
        with cols[i]:
            val_pct = row.get('Change_Pct', '0')
            st.metric(
                label=row['Asset'], 
                value=f"R$ {row['Price']:.2f}", 
                delta=f"{val_pct}%"
            )
            st.markdown(f"**Análise:** {row['Sentiment']}")

    # 2. Gráfico de Comparativo
    st.markdown("---")
    fig = px.bar(
        df_recente, x="Asset", y="Price", color="Asset", 
        title="Comparativo de Ativos em Tempo Real", 
        template="plotly_dark", text_auto='.2f'
    )
    st.plotly_chart(fig, use_container_width=True)

    # 3. Sidebar (Barra Lateral)
    with st.sidebar:
        st.header("💱 Conversor Alpha")
        val_brl = st.number_input("Valor em R$", min_value=1.0, value=100.0)
        
        assets_disponiveis = df_recente['Asset'].unique()
        target = st.selectbox("Converter para:", assets_disponiveis)
        
        # Cálculo dinâmico
        price_target = df_recente[df_recente['Asset'] == target]['Price'].values[0]
        st.subheader(f"{val_brl / price_target:.2f} {target}")
        
        st.markdown("---")
        st.caption("""
        ⚠️ **DISCLAIMER:** As informações aqui apresentadas são de caráter exclusivamente informativo.
        """)
else:
    st.error("Conectando aos servidores Alpha Vision... Por favor, aguarde.")
