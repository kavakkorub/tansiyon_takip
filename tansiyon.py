import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- KONFİGÜRASYON ---
st.set_page_config(page_title="Tansiyon Takip v2", layout="centered", page_icon="🩺")

# Streamlit Secrets üzerinden güvenli giriş (Canlıda çalışması için)
# Yerelde çalışırken hata almamak için kontrol ekliyoruz
try:
    GONDEREN_EMAIL = st.secrets["email_ayarlari"]["gonderen"]
    ALICI_EMAIL = st.secrets["email_ayarlari"]["alici"]
    EP_SIFRE = st.secrets["email_ayarlari"]["sifre"]
except:
    # Yerelde test ederken buraya kendi bilgilerinizi geçici yazabilirsiniz
    # AMA GITHUB'A YÜKLERKEN BOŞ BIRAKIN VEYA SECRETS KULLANIN
    GONDEREN_EMAIL = "ornek@gmail.com"
    ALICI_EMAIL = "doktor@gmail.com"
    EP_SIFRE = "uygulama_sifresi"

DB_FILE = "tansiyon_verileri.csv"

def mail_gonder(dosya_yolu):
    try:
        msg = MIMEMultipart()
        msg['From'] = GONDEREN_EMAIL
        msg['To'] = ALICI_EMAIL
        msg['Subject'] = f"Tansiyon Raporu - {datetime.now().strftime('%d/%m/%Y')}"

        body = f"Merhaba,\n\n{datetime.now().strftime('%d/%m/%Y')} tarihli güncel tansiyon kayıtları ekte sunulmuştur."
        msg.attach(MIMEText(body, 'plain'))

        with open(dosya_yolu, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {dosya_yolu}")
            msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GONDEREN_EMAIL, EP_SIFRE)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"E-posta Hatası: {e}")
        return False

def verileri_yukle():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Tarih", "Vakit", "Sistolik", "Diyastolik", "Nabiz"])

# --- ARAYÜZ ---
st.title("🩺 Tansiyon Takip Sistemi")

# Veri Girişi (Sidebar)
with st.sidebar:
    st.header("➕ Yeni Kayıt")
    vakit = st.selectbox("Vakit", ["Sabah", "Akşam"])
    sistolik = st.number_input("Büyük (Sistolik)", 70, 220, 120)
    diyastolik = st.number_input("Küçük (Diyastolik)", 40, 140, 80)
    nabiz = st.number_input("Nabız", 40, 200, 70)
    
    if st.button("Veriyi Kaydet"):
        yeni_veri = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), vakit, sistolik, diyastolik, nabiz]], 
                                 columns=["Tarih", "Vakit", "Sistolik", "Diyastolik", "Nabiz"])
        df = verileri_yukle()
        df = pd.concat([df, yeni_veri], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.success("Başarıyla kaydedildi!")
        st.rerun()

# Ana Sayfa İçeriği
df = verileri_yukle()

if not df.empty:
    # Grafik Alanı
    st.subheader("📊 Tansiyon Analiz Grafiği")
    fig = px.line(df, x="Tarih", y=["Sistolik", "Diyastolik"], 
                  labels={"value": "Değer", "variable": "Ölçüm"},
                  markers=True, color_discrete_sequence=["#FF4B4B", "#0068C9"])
    st.plotly_chart(fig, use_container_width=True)

    # İşlem Butonları
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📧 Raporu Mail At"):
            with st.spinner("Gönderiliyor..."):
                if mail_gonder(DB_FILE):
                    st.success("Mail başarıyla gönderildi!")
    
    with col2:
        # Manuel yedek alma butonu
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Excel Olarak İndir", data=csv, file_name="tansiyon_yedek.csv", mime="text/csv")

    # Liste
    st.subheader("📋 Geçmiş Kayıtlar")
    st.dataframe(df.sort_values(by="Tarih", ascending=False), use_container_width=True)
else:
    st.info("Henüz veri bulunmuyor. Sol menüden ilk kaydınızı girebilirsiniz.")
