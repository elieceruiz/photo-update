# sections/history.py
import streamlit as st
import pandas as pd
import pytz

def show_access_logs(logs):
    if logs:
        colombia = pytz.timezone("America/Bogota")
        data = []
        for l in logs:
            ts = l["ts"].astimezone(colombia).strftime("%d %b %y %H:%M")
            data.append({
                "Fecha": ts,
                "Lat": f"{l.get('lat'):.6f}" if l.get("lat") else None,
                "Lon": f"{l.get('lon'):.6f}" if l.get("lon") else None,
                "±m": f"{int(l.get('acc'))}" if l.get("acc") else None,
            })
        df = pd.DataFrame(data)
        df.index = range(1, len(df) + 1)
        df = df.iloc[::-1]
        st.subheader("📜 Historial de accesos")
        st.dataframe(df, use_container_width=True)
