import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
import yaml
from yaml.loader import SafeLoader

# --- KULLANICI AYARLARI (Şimdilik Kod İçinde) ---
# Gerçek projelerde bu bilgiler Secrets veya ayrı bir YAML dosyasında tutulur.
names = ["Kullanıcı 1", "Kullanıcı 2"]
usernames = ["user1", "user2"]
# Şifreleri "hashed" (şifrelenmiş) saklamak güvenlidir. 
# Örnek şifreler: '12345' (test için)
passwords = ["$2b$12$MNRDPK7L0K7/X.n9YfC93e3PZ.8pXqXhKj8/rXW6kXv.O/Bv9pX6W", 
             "$2b$12$MNRDPK7L0K7/X.n9YfC93e3PZ.8pXqXhKj8/rXW6kXv.O/Bv9pX6W"]

authenticator = stauth.Authenticate(
    {"credentials": {"usernames": {u: {"name": n, "password": p} for u, n, p in zip(usernames, names, passwords)}}},
    "tansiyon_cookie", "signature_key", cookie_expiry_days=30
)

# Giriş Formu
name, authentication_status, username = authenticator.login("Giriş Yap", "main")

if authentication_status == False:
    st.error("Kullanıcı adı veya şifre hatalı")
elif authentication_status == None:
    st.warning("Lütfen kullanıcı adı ve şifrenizi giriniz")
elif authentication_status:
    # --- UYGULAMA BURADAN SONRA BAŞLAR ---
    with st.sidebar:
        st.write(f"Hoş geldin, **{name}**")
        authenticator.logout("Çıkış Yap", "sidebar")

    # Mevcut kodunuzun geri kalanı buraya gelecek (DB_FILE vb.)
    DB_FILE = f"tansiyon_{username}.csv" # Her kullanıcının verisi ayrı dosyada tutulur!
    
    # ... (Önceki mesajdaki tüm fonksiyonlar ve arayüz kodları buraya dahil edilecek) ...
    st.title(f"🩺 {name} - Tansiyon Takip")
    # ... (Kaydet, Grafik, Silme bölümleri) ...
