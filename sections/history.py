# sections/history.py
import streamlit as st
import pandas as pd

def render_history(logs, tz):
    if not logs:
        return
    
    data = []
    for l in logs:
        ts = l["ts"].astimezone(tz).strftime("%d %b %y %H:%M")
        data.append({
            "Fecha": ts,
            "Lat": f"{l.get('lat'):.6f}" if l.get("lat") else None,
            "Lon": f"{l.get('lon'):.6f}" if l.get("lon") else None,
            "±m": f"{int(l.get('acc'))}" if l.get("acc") else None,
        })
    
    df = pd.DataFrame(data)
    df.index = range(1, len(df) + 1)
    df = df.iloc[::-1]  # más reciente arriba
    
    st.subheader("📜 Historial de accesos")
    st.dataframe(df, use_container_width=True)
