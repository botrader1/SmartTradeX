
import streamlit as st
import sqlite3
import pandas as pd
from prophet import Prophet
import yfinance as yf
from datetime import datetime

# Connect to DB
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS trades (username TEXT, asset TEXT, type TEXT, amount REAL, date TEXT)''')
conn.commit()

# Auth functions
def register(username, password):
    c.execute("INSERT INTO users VALUES (?, ?)", (username, password))
    conn.commit()

def login(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone()

# Session state defaults
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Title
st.title("📈 SmartTradeX (Beta)")

if not st.session_state.logged_in:
    menu = ["Login", "Register"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Register":
        st.subheader("Create Account")
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        if st.button("Register"):
            register(new_user, new_pass)
            st.success("Registered! Go to Login.")

    elif choice == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome {username}!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

# Show main app if logged in
if st.session_state.logged_in:
    username = st.session_state.username
    st.sidebar.success(f"Logged in as {username}")

    asset = st.selectbox("Choose Asset", ["AAPL", "TSLA", "BTC-USD", "ETH-USD", "EURUSD=X"])
    data = yf.download(asset, period="1y")
    st.subheader(f"{asset} Price Chart (1Y)")
    st.line_chart(data["Close"])

    df = data.reset_index()[["Date", "Close"]]
    df.columns = ["ds", "y"]
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=7)
    forecast = model.predict(future)
    st.subheader("📉 7-Day Forecast")
    st.line_chart(forecast[["ds", "yhat"]].set_index("ds"))

    st.subheader("🛒 Trade Simulation")
    trade_type = st.selectbox("Buy or Sell", ["Buy", "Sell"])
    amount = st.number_input("Amount", min_value=1.0, value=10.0)
    if st.button("Execute Trade"):
        c.execute("INSERT INTO trades VALUES (?, ?, ?, ?, ?)", (username, asset, trade_type, amount, str(datetime.now())))
        conn.commit()
        st.success("Trade recorded.")

    st.subheader("📜 Your Trade History")
    c.execute("SELECT * FROM trades WHERE username=?", (username,))
    trades = c.fetchall()
    st.table(pd.DataFrame(trades, columns=["User", "Asset", "Type", "Amount", "Date"]))
