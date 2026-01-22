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
    page_title="Alpha Vision",
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
    except:
        return None

# Função ajustada para remover o Bullish/Bearish e usar luzinhas
def get_market_analysis(pct_change):
    try:
        change = float(pct_change)
        if change > 0.05: 
            return "ALTA", "🟢"
        elif change < -0.05: 
            return "BAIXA", "🔴"
        else: 
            return "ESTÁVEL", "⚪"
    except:
        return "INDETERMINADO", "⚪"

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
            tendencia, luzinha = get_market_analysis(variacao)
            
            records.append({
                "Timestamp": hora_atual,
                "Data": data_atual,
                "Asset": info.get('name', '').split('/')[0],
                "Price": float(info.get('bid', 0)),
                "Change_Pct": str(variacao),
                "Trend": tendencia,
                "Icon": luzinha
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

# --- EXECUÇÃO ---
df_completo = process_and_save_data()

if df_completo is None and os.path.exists(EXCEL_DB):
    try:
        df_completo = pd.read_excel(EXCEL_DB)
    except:
        pass

# --- INTERFACE PÚBLICA ALPHA VISION ---
st.title("♾️ Alpha Vision")
st.caption(f"Inteligência de Mercado Ativa | {datetime.now().strftime('%H:%M:%S')}")

if df_completo is not None and not df_completo.empty:
    df_recente = df_completo.tail(4).reset_index(drop=True)
    
    # 1. Cards de Métricas com as "Luzinhas"
    cols = st.columns(4)
    for i, row in df_recente.iterrows():
        with cols[i]:
            val_pct = row.get('Change_Pct', '0')
            st.metric(label=row['Asset'], value=f"R$ {row['Price']:.2f}", delta=f"{val_pct}%")
            st.markdown(f"**Tendência:** {row['Icon']} {row['Trend']}")

    # 2. Gráfico de Comparativo
    st.markdown("---")
    fig = px.bar(df_recente, x="Asset", y="Price", color="Asset", 
                 title="Comparativo de Ativos em Tempo Real", 
                 template="plotly_dark", text_auto='.2f')
    st.plotly_chart(fig, use_container_width=True)

    # 3. Sidebar
    with st.sidebar:
        st.header("💱 Conversor Alpha")
        val_brl = st.number_input("Valor em R$", min_value=1.0, value=100.0)
        target = st.selectbox("Converter para:", df_recente['Asset'].unique())
        
        price_target = df_recente[df_recente['Asset'] == target]['Price'].values[0]
        st.subheader(f"{val_brl / price_target:.2f} {target}")
        
        st.markdown("---")
        st.caption("""
        ⚠️ **DISCLAIMER:** As informações aqui apresentadas são de caráter exclusivamente informativo e demonstrativo. 
        O uso destes dados para operações de mercado é de inteira responsabilidade do usuário.
        """)

else:
    st.error("Estabelecendo conexão com Alpha Vision...")