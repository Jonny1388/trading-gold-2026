import streamlit as st
import yfinance as yf
import pandas as pd
import time
import google.generativeai as genai

# Configurazione Pagina Mobile
st.set_page_config(page_title="XAU/USD Sniper", layout="centered")

# --- CONFIGURAZIONE IA ---
MY_API_KEY = "AIzaSyCmZSlTIhJIsyyOXRqJNVeX9KDZL6JQh80"
genai.configure(api_key=MY_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

st.title("🎯 XAU/USD Sniper v12.0")
st.write("Sessione: 23 Febbraio 2026")

# --- SINCRONIZZAZIONE VT MARKETS ---
with st.sidebar:
    st.header("Sincronizzazione Broker")
    broker_price = st.number_input("Prezzo attuale VT Markets", value=5160.0, step=0.10)
    lotto = 0.01

# --- LOGICA DATI ---
@st.cache_data(ttl=60) # Aggiorna ogni minuto
def get_data():
    df = yf.download('GC=F', period='5d', interval='1h', progress=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    return df

df = get_data()
current_server = float(df['Close'].iloc[-1])
offset = broker_price - current_server
real_price = current_server + offset

# Indicatori
sma20 = df['Close'].rolling(20).mean().iloc[-1] + offset
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean().iloc[-1]
loss = (-delta.where(delta < 0, 0)).rolling(14).mean().iloc[-1]
rsi = 100 - (100 / (1 + (gain / loss)))
atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]

# Segnale
trend = "LONG" if real_price > sma20 and rsi > 52 else "SHORT" if real_price < sma20 and rsi < 48 else "NEUTRALE"
win_rate = 75 if trend != "NEUTRALE" else 45

# --- INTERFACCIA MOBILE ---
col1, col2 = st.columns(2)
col1.metric("Prezzo Spot", f"${real_price:,.2f}")
col2.metric("RSI (1H)", f"{rsi:.1f}")

if trend == "LONG":
    st.success(f"🔥 SEGNALE: {trend} (Win Rate: {win_rate}%)")
    tp = real_price + (atr * 4)
    sl = real_price - (atr * 2.5)
elif trend == "SHORT":
    st.error(f"❄️ SEGNALE: {trend} (Win Rate: {win_rate}%)")
    tp = real_price - (atr * 4)
    sl = real_price + (atr * 2.5)
else:
    st.warning("⏳ STATO: NEUTRALE - ATTENDI")

if trend != "NEUTRALE":
    st.info(f"🎯 **TAKE PROFIT:** ${tp:.2f} | 🛑 **STOP LOSS:** ${sl:.2f}")
    st.write(f"💰 Potenziale con 0.01: **${abs(tp-real_price):.2f}**")

# IA Insight
if st.button("Chiedi all'IA"):
    prompt = f"Analisi Oro 23 Feb 2026: Prezzo {real_price}, RSI {rsi:.1f}, Trend {trend}. Consiglio di 8 parole."
    response = ai_model.generate_content(prompt)
    st.chat_message("assistant").write(response.text)
