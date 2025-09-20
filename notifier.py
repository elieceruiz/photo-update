# notifier.py
import streamlit as st
from twilio.rest import Client

def send_whatsapp(message: str):
    """
    Envía notificación por WhatsApp usando Twilio configurado en secretos.
    """
    client = Client(
        st.secrets["twilio"]["account_sid"],
        st.secrets["twilio"]["auth_token"]
    )
    msg = client.messages.create(
        body=message,
        from_=f"whatsapp:{st.secrets['twilio']['sandbox_number']}",
        to=f"whatsapp:{st.secrets['twilio']['to_number']}"
    )
    return msg.sid
