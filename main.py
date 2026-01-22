import streamlit as st
import pandas as pd
import requests
from textblob import TextBlob
from datetime import datetime
import os
import plotly.express as px
import nltk

# --- GARANTIA DE AMBIENTE IA ---
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

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="Alpha Vision Terminal", layout="wide", page_icon="🚀")

EXCEL_DB = "currency_data.xlsx"
CURRENCIES = ["USD-BRL", "EUR-BRL", "GBP-BRL", "JPY-BRL"]

def fetch_market_data():
    url = f"https://economia.awesomeapi.com.br/last/{','.join(CURRENCIES)}"
    try:
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def run_sentiment_analysis(pct_change):
    try:
        change = float(pct_change)
        if change > 0.05: return "BULLISH (Otimista)"
        elif change < -0.05: return "BEARISH (Pessimista)"
        else: return "NEUTRAL"
    except:
        return "NEUTRAL"

def process_and_save_data():
    raw_data = fetch_market_data()
    if not (raw_data and isinstance(raw_data, dict)):
        return None
        
    records = []
    for key, info in raw_data.items():
        if isinstance(info, dict):
            variacao = info.get('pctChange', '0')
            records.append({
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Data": datetime.now().strftime("%d/%m/%Y"),
                "Asset": info.get('name', '').split('/')[0],
                "Price": float(info.get('bid', 0)),
                "Change_Pct": str(variacao),
                "Sentiment": run_sentiment_analysis(variacao)
            })
    
    new_df = pd.DataFrame(records)
    
    # Lógica de Persistência no Excel
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

# --- FLUXO PRINCIPAL ---
df_completo = process_and_save_data()

# Se a API falhar, tenta ler o que já existe no Excel
if df_completo is None and os.path.exists(EXCEL_DB):
    try:
        df_completo = pd.read_excel(EXCEL_DB)
    except:
        pass

# --- RENDERIZAÇÃO DA INTERFACE ---
st.title("🚀 Alpha Vision Terminal")
st.caption(f"Monitoramento de Mercado em Tempo Real | {datetime.now().strftime('%H:%M:%S')}")

if df_completo is not None and not df_completo.empty:
    # Selecionamos estritamente as últimas 4 entradas (as moedas da última varredura)
    df_recente = df_completo.sort_values(by=['Data', 'Timestamp']).tail(4).reset_index(drop=True)
    
    # 1. Cards de Métricas
    st.markdown("### Cotações Atuais")
    cols = st.columns(4)
    for i, row in df_recente.iterrows():
        with cols[i]:
            val_pct = row.get('Change_Pct', '0')
            st.metric(label=row['Asset'], value=f"R$ {row['Price']:.2f}", delta=f"{val_pct}%")
            st.markdown(f"**IA:** {row['Sentiment']}")

    # 2. Gráfico Alpha Vision
    st.markdown("---")
    fig = px.bar(df_recente, x="Asset", y="Price", color="Asset", 
                 title="Diferencial de Preço (Última Apuração)", 
                 template="plotly_dark", text_auto='.2f')
    st.plotly_chart(fig, use_container_width=True)

    # 3. Sidebar e Funcionalidades
    with st.sidebar:
        st.header("💱 Conversor Alpha")
        val_brl = st.number_input("Montante BRL (R$)", min_value=1.0, value=100.0)
        target = st.selectbox("Moeda para Conversão:", df_recente['Asset'].unique())
        
        # Cálculo Seguro
        price_row = df_recente[df_recente['Asset'] == target]['Price']
        if not price_row.empty:
            price_target = price_row.values[0]
            st.subheader(f"{val_brl / price_target:.2f} {target}")
        
        st.markdown("---")
        st.caption("⚠️ **Aviso de Segurança:** Este terminal é um projeto de portfólio para fins educacionais. Não realize investimentos baseados nestes dados.")

    # 4. Log para o Recrutador (Escondido)
    with st.expander("Verificar histórico de extração (Excel)"):
        st.dataframe(df_completo.sort_values(by=['Data', 'Timestamp'], ascending=False), use_container_width=True)

else:
    st.error("Aguardando resposta da API financeira... Por favor, recarregue a página.")