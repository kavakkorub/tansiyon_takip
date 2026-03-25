import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os

# Sayfa Yapılandırması (Mobil uyumlu görünüm için)
st.set_page_config(page_title="Tansiyon Takip", layout="centered")

# Veri Dosyası Kontrolü
DB_FILE = "tansiyon_verileri.csv"

def verileri_yukle():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Tarih", "Vakit", "Sistolik (Büyük)", "Diyastolik (Küçük)", "Nabız"])

# Başlık
st.title("🩺 Tansiyon Takip Sistemi")

# Veri Giriş Alanı
with st.expander("➕ Yeni Ölçüm Ekle", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        tarih = st.date_input("Tarih", datetime.now())
    with col2:
        vakit = st.selectbox("Vakit", ["Sabah", "Akşam"])
    
    sistolik = st.number_input("Büyük Tansiyon (Sistolik)", min_value=50, max_value=250, value=120)
    diyastolik = st.number_input("Küçük Tansiyon (Diyastolik)", min_value=30, max_value=150, value=80)
    nabiz = st.number_input("Nabız", min_value=30, max_value=200, value=70)

    if st.button("Kaydet"):
        yeni_veri = pd.DataFrame([[tarih, vakit, sistolik, diyastolik, nabiz]], 
                                 columns=["Tarih", "Vakit", "Sistolik (Büyük)", "Diyastolik (Küçük)", "Nabız"])
        df = verileri_yukle()
        df = pd.concat([df, yeni_veri], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.success("Veri başarıyla kaydedildi!")

# Veri Listeleme ve Görselleştirme
df = verileri_yukle()

if not df.empty:
    st.divider()
    st.subheader("📊 Tansiyon Analizi")
    
    # Grafik Çizimi
    fig = px.line(df, x="Tarih", y=["Sistolik (Büyük)", "Diyastolik (Küçük)"], 
                  title="Zaman İçindeki Değişim", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    # Geçmiş Veriler Tablosu
    st.subheader("📋 Geçmiş Ölçümler")
    st.dataframe(df.sort_values(by="Tarih", ascending=False), use_container_width=True)
    
    # Mail Gönderim Bölümü (Arayüz Taslağı)
    st.divider()
    if st.button("📧 Haftalık Raporu Mail At"):
        st.info("E-posta gönderim modülü buraya entegre edilecek (smtplib).")
else:
    st.info("Henüz veri girilmemiş. İlk ölçümünüzü yukarıdan ekleyebilirsiniz.")