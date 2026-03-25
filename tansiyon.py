import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from datetime import datetime
import plotly.express as px
import os

# --- 1. KULLANICI DOĞRULAMA AYARLARI ---
# Not: Gerçek şifreleriniz burada 'hashed' olarak tutulur.
# admin şifresi: sifre123 | user1 şifresi: test456
credentials = {
    "usernames": {
        "admin": {
            "name": "Yönetici",
            "password": "$2b$12$MNRDPK7L0K7/X.n9YfC93e3PZ.8pXqXhKj8/rXW6kXv.O/Bv9pX6W"
        },
        "user1": {
            "name": "Misafir Kullanıcı",
            "password": "$2b$12$MNRDPK7L0K7/X.n9YfC93e3PZ.8pXqXhKj8/rXW6kXv.O/Bv9pX6W"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "tansiyon_takip_cerez", # Çerez adı
    "abcdef",              # Anahtar (rastgele olabilir)
    cookie_expiry_days=30
)

# Giriş ekranını ana sayfada göster
name, authentication_status, username = authenticator.login("Giriş Yap", "main")

if authentication_status == False:
    st.error("Kullanıcı adı veya şifre hatalı!")
elif authentication_status == None:
    st.warning("Lütfen giriş yapın.")
elif authentication_status:
    # --- 2. UYGULAMA BURADAN SONRA BAŞLAR ---
    
    # Çıkış butonunu yan menüye (sidebar) koyalım
    with st.sidebar:
        st.write(f"Hoş geldin, **{name}**")
        authenticator.logout("Çıkış Yap", "sidebar")

    # HER KULLANICI İÇİN AYRI DOSYA
    # Bu sayede admin kendi verilerini, user1 kendi verilerini görür.
    DB_FILE = f"tansiyon_{username}.csv"

    # --- (Buradan aşağısı senin mevcut çalışan kodun olacak) ---
    def verileri_yukle():
        if os.path.exists(DB_FILE):
            return pd.read_csv(DB_FILE)
        return pd.DataFrame(columns=["Tarih", "Vakit", "Sistolik", "Diyastolik", "Nabiz"])

    st.title("🩺 Tansiyon Takip Sistemi")

    # ... (Buraya mevcut veri giriş, grafik ve silme kodlarını yapıştırabilirsin) ...
    # Önemli: Fonksiyonların ve değişkenlerin (DB_FILE gibi) 
    # 'if authentication_status:' bloğunun içinde (sağda) kaldığından emin ol!
