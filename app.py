import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --------------------------
# 1. Title
# --------------------------
st.set_page_config(page_title="Market Dashboard", layout="wide")
st.title("📊 Market Dashboard")

# --------------------------
# 2. Date Range Selection
# --------------------------
end_date = datetime.today()
start_date = end_date - timedelta(days=90)

st.sidebar.header("Filter Data")
start_date = st.sidebar.date_input("Start Date", start_date)
end_date = st.sidebar.date_input("End Date", end_date)

# --------------------------
# 3. Download Data
# --------------------------
tickers = {
    "Emas (Gold Futures)": "GC=F",
    "Perak (Silver Futures)": "SI=F",
    "Minyak Mentah WTI (Crude Oil Futures)": "CL=F",
    "Platinum": "PL=F",
    "Gas Alam": "NG=F",
    "Tembaga": "HG=F"d
}

# Warna default untuk setiap instrumen
colors = {
    "Emas (Gold Futures)": "gold",
    "Perak (Silver Futures)": "silver",
    "Nikel (Nickel Futures)": "green",
    "Minyak Mentah WTI (Crude Oil Futures)": "yellow"
}

# Dropdown
instrument_name = st.selectbox("Pilih Instrumen", list(tickers.keys()))
ticker_symbol = tickers[instrument_name]

df = yf.download(ticker_symbol, start=start_date, end=end_date, interval="1d")

# Handle jika df memiliki multiindex kolom
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.droplevel(1)

df.reset_index(inplace=True)

# Pastikan kolom yang dibutuhkan ada
required_cols = {"Date", "Close", "Open", "High", "Low"}
if not required_cols.issubset(df.columns):
    st.error("Kolom data tidak lengkap. Pastikan ticker benar dan koneksi internet tersedia.")
    st.stop()

# --------------------------
# 4. Price Change Info
# --------------------------
if len(df) > 1:
    price_change = df["Close"].iloc[-1] - df["Close"].iloc[-2]
    price_pct_change = (price_change / df["Close"].iloc[-2]) * 100

    st.metric(
        label="Last Close Price",
        value=f"${df['Close'].iloc[-1]:,.2f}",
        delta=f"{price_change:,.2f} ({price_pct_change:.2f}%)"
    )

# --------------------------
# 5. Plot Price Chart
# --------------------------
# Hitung indikator teknikal
df["MA20"] = df["Close"].rolling(window=20).mean()
df["MA50"] = df["Close"].rolling(window=50).mean()
df["STD20"] = df["Close"].rolling(window=20).std()
df["UpperBB"] = df["MA20"] + (df["STD20"] * 2)
df["LowerBB"] = df["MA20"] - (df["STD20"] * 2)

# RSI
delta = df["Close"].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()
rs = avg_gain / avg_loss
df["RSI"] = 100 - (100 / (1 + rs))

fig = go.Figure()

fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], mode="lines", name="Close Price"))
fig.add_trace(go.Scatter(x=df["Date"], y=df["MA20"], mode="lines", name="MA20"))
fig.add_trace(go.Scatter(x=df["Date"], y=df["MA50"], mode="lines", name="MA50"))
fig.add_trace(go.Scatter(x=df["Date"], y=df["UpperBB"], mode="lines", name="Upper BB", line=dict(dash="dot")))
fig.add_trace(go.Scatter(x=df["Date"], y=df["LowerBB"], mode="lines", name="Lower BB", line=dict(dash="dot")))

fig.update_layout(
    title=f"{instrument_name} - Close Price + MA + Bollinger Bands",
    xaxis_title="Tanggal",
    yaxis_title="Harga (USD)",
    template="plotly_white",
    hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True)

# --- Grafik RSI ---
fig_rsi = go.Figure()
fig_rsi.add_trace(go.Scatter(x=df["Date"], y=df["RSI"], mode="lines", name="RSI", line=dict(color="purple")))
fig_rsi.add_hline(y=70, line_dash="dot", line_color="red")
fig_rsi.add_hline(y=30, line_dash="dot", line_color="green")
fig_rsi.update_layout(title="RSI (Relative Strength Index)", yaxis_title="RSI")
st.plotly_chart(fig_rsi, use_container_width=True)

# --------------------------
# 6. Show Data Table
# --------------------------
# Tampilkan raw data dengan index mulai dari 1
df_display = df.copy()
df_display.index = df_display.index + 1  # index mulai dari 1
with st.expander("Show Raw Data"):
    st.dataframe(df_display)

# --------------------------
# 7. Download Button
# --------------------------
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Data as CSV",
    data=csv,
    file_name=f"{instrument_name}_data.csv",
    mime="text/csv"
)
