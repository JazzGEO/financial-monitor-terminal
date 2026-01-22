import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import os
import plotly.express as px
import nltk

# ------------------ PREPARAÇÃO SILENCIOSA ------------------
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

# ------------------ CONFIGURAÇÃO DA PÁGINA ------------------
st.set_page_config(
    page_title="Alpha Vision",
    layout="wide"
)

# ------------------ CONSTANTES ------------------
EXCEL_DB = "currency_data.xlsx"
CURRENCIES = ["USD-BRL", "EUR-BRL", "GBP-BRL", "JPY-BRL"]

# ------------------ FUNÇÕES DE DADOS ------------------
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
        if change > 0.05:
            return "BULLISH (Otimista)"
        elif change < -0.05:
            return "BEARISH (Pessimista)"
        else:
            return "NEUTRAL"
    except:
        return "NEUTRAL"

def process_and_save_data():
    raw_data = fetch_market_data()
    if not raw_data:
        return None

    records = []
    agora = datetime.now()
    data_atual = agora.strftime("%d/%m/%Y")
    hora_atual = agora.strftime("%H:%M:%S")

    for _, info in raw_data.items():
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
        old_df = pd.read_excel(EXCEL_DB)
        df = pd.concat([old_df, new_df], ignore_index=True)
        df = df.drop_duplicates(subset=['Timestamp', 'Asset'])
        df.to_excel(EXCEL_DB, index=False)
        return df
    else:
        new_df.to_excel(EXCEL_DB, index=False)
        return new_df

# ------------------ EXECUÇÃO ------------------
df_completo = process_and_save_data()

if df_completo is None and os.path.exists(EXCEL_DB):
    df_completo = pd.read_excel(EXCEL_DB)

# ------------------ FUNÇÃO DOS CARDS PREMIUM ------------------
def financial_card(asset, price, pct, sentiment):
    pct_val = float(pct)
    color = "#16a34a" if pct_val > 0 else "#dc2626" if pct_val < 0 else "#9ca3af"

    return f"""
    <div style="
        background: linear-gradient(145deg, #0b0f14, #111827);
        border-radius: 16px;
        padding: 22px;
        border: 1px solid rgba(255,255,255,0.06);
        transition: all 0.3s ease;
        cursor: pointer;
    "
    onmouseover="this.style.transform='translateY(-6px)';
                 this.style.border='1px solid {color}'"
    onmouseout="this.style.transform='translateY(0)';
                this.style.border='1px solid rgba(255,255,255,0.06)'">

        <h4 style="color:#9ca3af; margin-bottom:8px;">{asset}</h4>

        <h2 style="color:white; margin:0; font-size:34px;">
            R$ {price:.2f}
        </h2>

        <span style="
            display:inline-block;
            margin-top:12px;
            padding:6px 14px;
            border-radius:999px;
            background:{color}20;
            color:{color};
            font-weight:600;
            font-size:14px;
        ">
            {pct}%
        </span>

        <p style="
            color:#d1d5db;
            margin-top:14px;
            font-size:14px;
        ">
            {sentiment}
        </p>
    </div>
    """

# ------------------ INTERFACE ------------------
st.title("♾️ Alpha Vision")
st.caption(f"Última atualização do mercado: {datetime.now().strftime('%H:%M:%S')}")

if df_completo is not None and not df_completo.empty:
    df_recente = df_completo.tail(4).reset_index(drop=True)

    # -------- CARDS --------
    st.markdown(
        "<div style='display:grid; grid-template-columns: repeat(4, 1fr); gap:20px;'>",
        unsafe_allow_html=True
    )

    for _, row in df_recente.iterrows():
        st.markdown(
            financial_card(
                row['Asset'],
                row['Price'],
                row['Change_Pct'],
                row['Sentiment']
            ),
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # -------- GRÁFICO --------
    st.markdown("---")
    fig = px.bar(
        df_recente,
        x="Asset",
        y="Price",
        color="Asset",
        template="plotly_dark",
        title="Comparativo de Ativos"
    )
    st.plotly_chart(fig, use_container_width=True)

    # -------- SIDEBAR --------
    with st.sidebar:
        st.header("Conversor Alpha")
        val_brl = st.number_input("Valor em R$", min_value=1.0, value=100.0)
        target = st.selectbox("Converter para:", df_recente['Asset'].unique())
        price_target = df_recente[df_recente['Asset'] == target]['Price'].values[0]
        st.subheader(f"{val_brl / price_target:.2f} {target}")

        st.markdown("---")
        st.caption("""
        ⚠️ DISCLAIMER: As informações aqui apresentadas são apenas informativas.
        O uso para operações financeiras é de inteira responsabilidade do usuário.
        """)

else:
    st.error("Conectando aos servidores Alpha Vision...")
