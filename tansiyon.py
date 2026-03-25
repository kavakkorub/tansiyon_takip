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
st.set_page_config(page_title="Tansiyon Takip", layout="centered", page_icon="🩺")

# Email Bilgileri
try:
    GONDEREN_EMAIL = st.secrets["email_ayarlari"]["gonderen"]
    ALICI_EMAIL = st.secrets["email_ayarlari"]["alici"]
    EP_SIFRE = st.secrets["email_ayarlari"]["sifre"]
except:
    GONDEREN_EMAIL = ""
    ALICI_EMAIL = ""
    EP_SIFRE = ""

DB_FILE = "tansiyon_verileri.csv"

def verileri_yukle():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Tarih", "Vakit", "Sistolik", "Diyastolik", "Nabiz"])

def mail_gonder(dosya_yolu):
    try:
        msg = MIMEMultipart()
        msg['From'] = GONDEREN_EMAIL
        msg['To'] = ALICI_EMAIL
        msg['Subject'] = f"Tansiyon Raporu - {datetime.now().strftime('%d/%m/%Y')}"
        body = f"Merhaba,\n\n{datetime.now().strftime('%d/%m/%Y')} tarihli güncel kayıtlar ektedir."
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

# --- ANA ARAYÜZ ---
st.title("🩺 Tansiyon Takip Sistemi")

# 1. VERİ GİRİŞ BÖLÜMÜ
with st.container(border=True):
    st.subheader("➕ Yeni Ölçüm Ekle")
    col1, col2 = st.columns(2)
    with col1: tarih_giris = st.date_input("Tarih", datetime.now())
    with col2: vakit_giris = st.selectbox("Vakit", ["Sabah", "Akşam"])
    
    c1, c2, c3 = st.columns(3)
    with c1: sistolik = st.number_input("Büyük", 70, 220, 120)
    with c2: diyastolik = st.number_input("Küçük", 40, 140, 80)
    with c3: nabiz = st.number_input("Nabız", 40, 200, 70)
    
    if st.button("KAYDET", use_container_width=True, type="primary"):
        zaman_damgasi = datetime.combine(tarih_giris, datetime.now().time()).strftime("%Y-%m-%d %H:%M")
        yeni_veri = pd.DataFrame([[zaman_damgasi, vakit_giris, sistolik, diyastolik, nabiz]], 
                                 columns=["Tarih", "Vakit", "Sistolik", "Diyastolik", "Nabiz"])
        df_mevcut = verileri_yukle()
        df_yeni = pd.concat([df_mevcut, yeni_veri], ignore_index=True)
        df_yeni.to_csv(DB_FILE, index=False)
        st.success("Başarıyla kaydedildi!")
        st.rerun()

# 2. ANALİZ VE LİSTELEME
df = verileri_yukle()

if not df.empty:
    st.divider()
    
    # Grafik
    st.subheader("📈 Değişim Grafiği")
    try:
        fig = px.line(df, x="Tarih", y=["Sistolik", "Diyastolik"], 
                      labels={"value": "Değer", "variable": "Ölçüm"},
                      markers=True, color_discrete_sequence=["#FF4B4B", "#0068C9"])
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.info("Grafik güncelleniyor...")

    # İşlem Butonları
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📧 Raporu Mail At", use_container_width=True):
            with st.spinner("Gönderiliyor..."):
                if mail_gonder(DB_FILE): st.success("Mail iletildi!")
    with col_b:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Excel İndir", data=csv, file_name="tansiyon_yedek.csv", use_container_width=True)

    st.divider()

    # 3. ONAY MEKANİZMALI TABLO ALANI
    st.subheader("📋 Kayıt Yönetimi")
    
    # Düzenlenebilir tabloyu gösteriyoruz
    # num_rows="dynamic" ile satır seçip silmeye izin veriyoruz
    edited_df = st.data_editor(
        df, 
        use_container_width=True, 
        num_rows="dynamic",
        column_config={
            "Tarih": st.column_config.TextColumn("Tarih", disabled=True),
            "Vakit": st.column_config.TextColumn("Vakit", disabled=True),
        }
    )

    # Eğer tablodaki veri değiştiyse (satır silindiyse) onay iste
    if len(edited_df) != len(df):
        st.warning("⚠️ Bir veya daha fazla satır sildiniz. Değişiklikleri kalıcı olarak kaydetmek istiyor musunuz?")
        
        col_onay1, col_onay2 = st.columns(2)
        with col_onay1:
            if st.button("✅ Evet, Silmeyi Onayla", type="primary", use_container_width=True):
                edited_df.to_csv(DB_FILE, index=False)
                st.success("Veriler başarıyla silindi!")
                st.rerun()
        with col_onay2:
            if st.button("❌ Hayır, İptal Et", type="secondary", use_container_width=True):
                st.info("Değişiklikler iptal edildi.")
                st.rerun()

else:
    st.info("Henüz veri girişi yapılmamış.")
