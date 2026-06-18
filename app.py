import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from io import StringIO

@st.cache_data(ttl=86400)
def get_tickers(index_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    if index_name == "S&P 500":
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        response = requests.get(url, headers=headers)
        df = pd.read_html(StringIO(response.text))[0]
        return df['Symbol'].tolist(), '^GSPC'
        
    elif index_name == "Nasdaq 100":
        url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        response = requests.get(url, headers=headers)
        # Manchmal verschiebt sich der Tabellen-Index, wir suchen die Tabelle mit 'Ticker' Spalte
        dfs = pd.read_html(StringIO(response.text))
        for df in dfs:
            if 'Ticker' in df.columns:
                return df['Ticker'].tolist(), '^NDX'
    return [], ''
