import streamlit as st
import pandas as pd
import requests
from textblob import TextBlob
from datetime import datetime
import os
import plotly.express as px
import nltk

# --- CONFIGURAÇÃO DE AMBIENTE IA ---
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('brown')
    nltk.download('wordnet')

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="Alpha Vision Terminal", layout="wide")

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
    if raw_data and isinstance(raw_data, dict):
        records = []
        for key, info in raw_data.items():
            if isinstance(info, dict):
                variacao = info.get('pctChange', '0')
                sentiment, _ = run_sentiment_analysis(variacao)
                
                records.append({
                    "Timestamp": datetime.now().strftime("%H:%M:%S"),
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Asset": info.get('name', '').split('/')[0],
                    "Price": float(info.get('bid', 0)),
                    "Change_Percent": variacao, # Nome padronizado para evitar erro
                    "Sentiment": sentiment
                })
        
        if not records: return None

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

# --- CARREGAMENTO ---
df_completo = None
if not os.path.exists(EXCEL_DB):
    df_completo = auto_update_data()
else:
    try:
        # Tenta ler o Excel; se falhar ou estiver vazio, busca novos dados
        df_completo = pd.read_excel(EXCEL_DB)
        df_novo = auto_update_data()
        if df_novo is not None:
            df_completo = df_novo
    except:
        df_completo = auto_update_data()

# --- INTERFACE ALPHA VISION ---
st.title("🚀 Alpha Vision Terminal")
st.caption(f"Última varredura: {datetime.now().strftime('%H:%M:%S')}")

if df_completo is not None and not df_completo.empty:
    # Pegamos as últimas 4 entradas para garantir que o Dashboard esteja atualizado
    df_recente = df_completo.tail(4).reset_index(drop=True)
    
    # 1. Cards de Métricas
    cols = st.columns(4)
    for i, row in df_recente.iterrows():
        with cols[i]:
            st.metric(
                label=row['Asset'], 
                value=f"R$ {row['Price']:.2f}", 
                delta=f"{row['Change_Percent']}%"
            )
            st.write(f"Análise: {row['Sentiment']}")

    # 2. Gráfico de Comparativo (Apenas o snapshot atual)
    st.markdown("---")
    fig = px.bar(
        df_recente, 
        x="Asset", 
        y="Price", 
        color="Asset", 
        title="Comparativo de Preços - Última Apuração", 
        template="plotly_dark", 
        text_auto='.2f'
    )
    st.plotly_chart(fig, use_container_width=True)

    # 3. Conversor Lateral
    st.sidebar.header("💱 Conversor Alpha")
    input_val = st.sidebar.number_input("BRL (R$)", min_value=1.0, value=10.0)
    
    # Lista única de moedas disponíveis no momento
    moedas_disponiveis = df_recente['Asset'].unique()
    target = st.sidebar.selectbox("Moeda Destino:", moedas_disponiveis)
    
    # Cálculo do conversor
    price_target = df_recente[df_recente['Asset'] == target]['Price'].values[0]
    st.sidebar.subheader(f"{input_val / price_target:.2f} {target}")
    
    # 4. Aviso de Segurança Reduzido
    st.sidebar.markdown("---")
    st.sidebar.caption("⚠️ **Aviso:** Fins educacionais. Não use para investimentos reais.")

    # 5. Log Oculto
    with st.expander("Visualizar Log Oculto"):
        st.dataframe(df_completo.tail(10), use_container_width=True)
else:
    st.error("Falha na sincronização inicial. Verifique sua conexão ou a API de dados.")