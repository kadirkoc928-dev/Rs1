import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="Relative Stärke Scanner", layout="wide")
st.title("🛡️ Aktien-Scanner: RS-Leader finden")

# 2. Daten-Abruf (Wikipedia Scraper)
@st.cache_data(ttl=86400)
def get_tickers(index_name):
    if index_name == "S&P 500":
        df = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        return df['Symbol'].tolist(), '^GSPC'
    elif index_name == "Nasdaq 100":
        df = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')[4]
        return df['Ticker'].tolist(), '^NDX'
    return [], ''

# 3. Download der Marktdaten
@st.cache_data(ttl=86400)
def load_data(tickers, benchmark):
    # Wir laden 2 Jahre Daten für eine gute statistische Basis
    data = yf.download([benchmark] + tickers, period="2y", progress=False)['Close']
    return data

# --- SIDEBAR UI ---
st.sidebar.header("Einstellungen")
index_choice = st.sidebar.selectbox("Index wählen", ["S&P 500", "Nasdaq 100"])
threshold = st.sidebar.slider("Crash-Tage Schwelle (Benchmark %)", -5.0, -1.0, -2.0, step=0.5)
filter_sma = st.sidebar.checkbox("Nur Aktien über 200-Tage-Linie (SMA 200)")

# --- MAIN LOGIC ---
if st.button("Scanner starten"):
    with st.spinner("Analysiere Daten..."):
        tickers, benchmark = get_tickers(index_choice)
        data = load_data(tickers, benchmark)
        
        # 1. Relative Stärke berechnen
        returns = data.pct_change()
        crash_days = returns[returns[benchmark] <= (threshold / 100)]
        
        # Berechne RS-Score
        resilience = {}
        for ticker in tickers:
            if ticker in returns.columns:
                # Differenz: Aktie vs Markt an schlechten Tagen
                diff = crash_days[ticker] - crash_days[benchmark]
                score = diff.mean()
                
                # 2. SMA 200 Filter (Optional)
                if filter_sma:
                    sma200 = data[ticker].rolling(window=200).mean().iloc[-1]
                    current_price = data[ticker].iloc[-1]
                    if current_price < sma200:
                        continue # Überspringe, wenn Aktie unter SMA200
                
                resilience[ticker] = score
        
        # Ergebnis sortieren
        results = pd.DataFrame.from_dict(resilience, orient='index', columns=['RS_Score'])
        results = results.sort_values(by='RS_Score', ascending=False)
        
        st.subheader(f"Top 20 Leader im {index_choice}")
        st.dataframe(results.head(20).style.background_gradient(cmap='Greens'))
