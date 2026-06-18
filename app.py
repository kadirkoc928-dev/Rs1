import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from io import StringIO

# Page Config
st.set_page_config(page_title="Relative Stärke Scanner", layout="wide")
st.title("🛡️ Aktien-Scanner: RS-Leader finden")

# 1. Daten-Abruf (Wikipedia Scraper)
@st.cache_data(ttl=86400)
def get_tickers(index_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        if index_name == "S&P 500":
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            response = requests.get(url, headers=headers, timeout=10)
            df = pd.read_html(StringIO(response.text))[0]
            return df['Symbol'].tolist(), '^GSPC'
        
        elif index_name == "Nasdaq 100":
            url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
            response = requests.get(url, headers=headers, timeout=10)
            dfs = pd.read_html(StringIO(response.text))
            for df in dfs:
                if 'Ticker' in df.columns:
                    return df['Ticker'].tolist(), '^NDX'
        return [], ''
    except Exception as e:
        st.error(f"Fehler beim Laden der Ticker: {e}")
        return [], ''

# 2. Download der Marktdaten
@st.cache_data(ttl=86400)
def load_data(tickers, benchmark):
    # Limitierung auf eine Auswahl, um Timeouts in der Cloud zu vermeiden
    # Bei 500+ Ticker dauert der Download sonst zu lange
    all_tickers = [benchmark] + tickers[:100] # Lädt Benchmark + erste 100 Ticker
    data = yf.download(all_tickers, period="2y", progress=False)['Close']
    return data

# --- SIDEBAR UI ---
st.sidebar.header("Einstellungen")
index_choice = st.sidebar.selectbox("Index wählen", ["S&P 500", "Nasdaq 100"])
threshold = st.sidebar.slider("Crash-Tage Schwelle (Benchmark %)", -5.0, -1.0, -2.0, step=0.5)
filter_sma = st.sidebar.checkbox("Nur Aktien über 200-Tage-Linie (SMA 200)")

# --- MAIN LOGIC ---
if st.button("Scanner starten"):
    with st.spinner("Lade Daten und analysiere..."):
        tickers, benchmark = get_tickers(index_choice)
        
        if not tickers:
            st.warning("Keine Ticker gefunden. Prüfe die Internetverbindung.")
        else:
            data = load_data(tickers, benchmark)
            
            # 1. Relative Stärke berechnen
            returns = data.pct_change()
            crash_days = returns[returns[benchmark] <= (threshold / 100)]
            
            resilience = {}
            for ticker in tickers:
                if ticker in returns.columns:
                    # RS-Score: Performance an Crash-Tagen
                    diff = crash_days[ticker] - crash_days[benchmark]
                    score = diff.mean()
                    
                    # SMA 200 Filter
                    if filter_sma:
                        sma200 = data[ticker].rolling(window=200).mean().iloc[-1]
                        current_price = data[ticker].iloc[-1]
                        if current_price < sma200:
                            continue
                            
                    resilience[ticker] = score
            
            # Ergebnisse
            results = pd.DataFrame.from_dict(resilience, orient='index', columns=['RS_Score'])
            results = results.sort_values(by='RS_Score', ascending=False)
            
            st.subheader(f"Top 20 Leader im {index_choice}")
            st.dataframe(results.head(20).style.background_gradient(cmap='Greens'))
            st.success("Analyse abgeschlossen!")
