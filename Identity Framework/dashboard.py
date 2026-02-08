import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time

st.set_page_config(page_title="MoI Command Center", layout="wide")
st.title("🛡️ MoI Identity & Byzantine Defense Dashboard")

def load_logs():
    if not os.path.exists("logs/moi_simulation.log"): return pd.DataFrame()
    data = []
    with open("logs/moi_simulation.log", "r") as f:
        for line in f:
            entry = {p.split('=')[0]: p.split('=')[1].strip('"\n ') for p in line.split(', ')}
            data.append(entry)
    return pd.DataFrame(data)

df = load_logs()

if not df.empty:
    df['reputation'] = pd.to_numeric(df['reputation'])
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Node Reputation Status")
        latest = df.groupby('office').last().reset_index()
        st.plotly_chart(px.bar(latest, x='office', y='reputation', color='reputation', range_y=[0,105]), use_container_width=True)
    
    with col2:
        st.subheader("Mathematical Outlier (Krum)")
        if os.path.exists("logs/krum_scores.csv"):
            k_df = pd.read_csv("logs/krum_scores.csv")
            st.plotly_chart(px.line(k_df, x='office', y='krum_score', markers=True), use_container_width=True)

    st.subheader("Audit Trail")
    st.table(df.tail(10))

time.sleep(2)
st.rerun()