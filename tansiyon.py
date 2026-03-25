import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- KONFİGÜRASYON ---
st.set_page_config(page_title="Tansiyon Takip", layout="centered", page_icon="🩺")

# Google Sheets Bağlantısı
conn = st.connection("gsheets", type=GSheetsConnection)

# Secrets Kontrolü (Email ve Tablo Linki için)
try:
    SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
    GONDEREN_EMAIL = st.secrets["email_ayarlari"]["gonderen"]
    ALICI_EMAIL = st.secrets["email_ayarlari"]["alici"]
    EP_SIFRE = st.secrets["email_ayarlari"]["sifre"]
except:
    st.error("Lütfen Secrets ayarlarını tamamlayın!")
    st.stop()

def mail_gonder(df):
    try:
        # Geçici bir CSV oluşturup mail atalım
        dosya_adi = "tansiyon_rapor.csv"
        df.to_csv(dosya_adi, index=False)
        
        msg = MIMEMultipart()
        msg['From'] = GONDEREN_EMAIL
        msg['To'] = ALICI_EMAIL
        msg['Subject'] = f"Tansiyon Raporu - {datetime.now().strftime('%d/%m/%Y')}"
        
        body = f"Merhaba,\n\n{datetime.now().strftime('%d/%m/%Y')} tarihli güncel kayıtlar ektedir."
        msg.attach(MIMEText(body, 'plain'))
        
        with open(dosya_adi, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {dosya_adi}")
            msg.attach(part)
            
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GONDEREN_EMAIL, EP_SIFRE)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Mail hatası: {e}")
        return False

# --- ARAYÜZ ---
st.title("🩺 Akıllı Tansiyon Takip")

# Verileri Google Sheets'ten Çek
df = conn.read(spreadsheet=SHEET_URL)

# Veri Giriş Formu
with st.container(border=True):
    st.subheader("➕ Yeni Ölçüm")
    c1, c2 = st.columns(2)
    with c1: tarih_giris = st.date_input("Tarih", datetime.now())
    with c2: vakit_giris = st.selectbox("Vakit", ["Sabah", "Akşam"])
    
    col1, col2, col3 = st.columns(3)
    with col1: sistolik = st.number_input("Büyük", 70, 220, 120)
    with col2: diyastolik = st.number_input("Küçük", 40, 140, 80)
    with col3: nabiz = st.number_input("Nabız", 40, 200, 70)
    
    if st.button("KAYDET VE BULUTA GÖNDER", use_container_width=True, type="primary"):
        zaman = datetime.combine(tarih_giris, datetime.now().time()).strftime("%Y-%m-%d %H:%M")
        yeni_satir = pd.DataFrame([[zaman, vakit_giris, sistolik, diyastolik, nabiz]], 
                                  columns=["Tarih", "Vakit", "Sistolik", "Diyastolik", "Nabiz"])
        
        # Mevcut veriye ekle ve geri yaz
        df_guncel = pd.concat([df, yeni_satir], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, data=df_guncel)
        st.success("Bulut veritabanı güncellendi!")
        st.rerun()

# Analiz ve Liste
if not df.empty:
    st.divider()
    st.subheader("📈 Analiz")
    fig = px.line(df, x="Tarih", y=["Sistolik", "Diyastolik"], markers=True)
    st.plotly_chart(fig, use_container_width=True)

    if st.button("📧 Raporu Mail At", use_container_width=True):
        if mail_gonder(df): st.success("Mail gönderildi!")

    st.subheader("📋 Geçmiş")
    st.dataframe(df.sort_values(by="Tarih", ascending=False), use_container_width=True)
