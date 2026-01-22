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
        nltk.download('punkt')
        nltk.download('brown')
        nltk.download('wordnet')
        nltk.download('punkt_tab')
    except:
        pass

load_nltk()

# --- CONFIGURAÇÃO ALPHA VISION ---
st.set_page_config(
    page_title="Alpha Vision - Terminal Financeiro",
    layout="wide",
    page_icon="♾️"
)

EXCEL_DB = "currency_data.xlsx"
CURRENCIES = ["USD-BRL", "EUR-BRL", "GBP-BRL", "JPY-BRL"]

def fetch_market_data():
    url = f"https://economia.awesomeapi.com.br/last/{','.join(CURRENCIES)}"
    try:
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception:
        return None

def get_market_analysis(pct_change):
    try:
        change = float(pct_change)
        if change > 0:
            return "ALTA", "🟢"
        elif change < 0:
            return "BAIXA", "🔴"
        else:
            return "ESTÁVEL", "⚪"
    except (ValueError, TypeError):
        return "N/A", "⚪"

# --- PROCESSAMENTO DE DADOS ---
data_api = fetch_market_data()
new_rows = []

if data_api:
    for key, value in data_api.items():
        trend, icon = get_market_analysis(value['pctChange'])
        new_rows.append({
            "Timestamp": datetime.now().strftime("%H:%M:%S"),
            "Data": datetime.now().strftime("%d/%m/%Y"),
            "Asset": value['name'].split('/')[0],
            "Price": float(value['bid']),
            "Change_Pct": float(value['pctChange']),
            "Trend": trend,
            "Icon": icon
        })

df_current = pd.DataFrame(new_rows)

# Persistência Simples (Local/Streamlit Cloud Cache)
if not df_current.empty:
    if os.path.exists(EXCEL_DB):
        try:
            df_old = pd.read_excel(EXCEL_DB)
            df_completo = pd.concat([df_old, df_current], ignore_index=True).tail(100) # Mantém as últimas 100 entradas
            df_completo.to_excel(EXCEL_DB, index=False)
        except:
            df_completo = df_current
    else:
        df_current.to_excel(EXCEL_DB, index=False)
        df_completo = df_current
else:
    # Caso a API falhe, tenta carregar o que já existe
    if os.path.exists(EXCEL_DB):
        df_completo = pd.read_excel(EXCEL_DB)
    else:
        df_completo = pd.DataFrame()

# --- INTERFACE STREAMLIT ---
st.title("♾️ Alpha Vision | Terminal de Monitoramento")

if not df_completo.empty:
    # Pegamos os últimos 4 registros únicos (um de cada moeda) para os cards
    df_recente = df_completo.drop_duplicates(subset=['Asset'], keep='last').reset_index(drop=True)
    
    # 1. Cards de Métricas
    cols = st.columns(len(df_recente))
    for i, row in df_recente.iterrows():
        with cols[i]:
            # Delta numérico para cor automática
            st.metric(
                label=row['Asset'], 
                value=f"R$ {row['Price']:.2f}", 
                delta=f"{row['Change_Pct']:.2f}%"
            )
            st.caption(f"Tendência: {row['Icon']} {row['Trend']}")

    st.markdown("---")

    # 2. Visualização de Dados (Gráfico de Histórico ou Comparativo)
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        fig_bar = px.bar(df_recente, x="Asset", y="Price", color="Asset", 
                     title="Cotação Atual (Comparativo)", 
                     template="plotly_dark", text_auto='.2f')
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        # Gráfico de histórico baseado no Excel
        fig_line = px.line(df_completo, x="Timestamp", y="Price", color="Asset",
                          title="Variação nas Últimas Leituras",
                          template="plotly_dark")
        st.plotly_chart(fig_line, use_container_width=True)

    # 3. Sidebar e Conversor
    with st.sidebar:
        st.header("💱 Conversor Alpha")
        val_brl = st.number_input("Valor em R$", min_value=0.0, value=100.0, step=10.0)
        
        assets_disponiveis = df_recente['Asset'].unique()
        target = st.selectbox("Converter para:", assets_disponiveis)
        
        price_target = df_recente[df_recente['Asset'] == target]['Price'].values[0]
        res = val_brl / price_target
        
        st.success(f"**Resultado:** {res:.2f} {target}")
        st.divider()
        st.info("Dados atualizados via AwesomeAPI.")

else:
    st.error("Aguardando conexão com a API ou dados do mercado...")
    if st.button("Tentar Atualizar"):
        st.rerun()