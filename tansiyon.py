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

DB_FILE = "tansiyon_verileri.csv"

def verileri_yukle():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    # Sadece Tarih, Vakit, Sistolik ve Diyastolik sütunları
    return pd.DataFrame(columns=["Tarih", "Vakit", "Sistolik", "Diyastolik"])

def mail_gonder(dosya_yolu):
    try:
        email_konf = st.secrets.get("email_ayarlari", {})
        msg = MIMEMultipart()
        msg['From'] = email_konf.get("gonderen", "")
        msg['To'] = email_konf.get("alici", "")
        msg['Subject'] = f"Tansiyon Raporu - {datetime.now().strftime('%d/%m/%Y')}"
        body = "Güncel tansiyon kayıtları (Büyük/Küçük) ektedir."
        msg.attach(MIMEText(body, 'plain'))
        with open(dosya_yolu, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {dosya_yolu}")
            msg.attach(part)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_konf.get("gonderen", ""), email_konf.get("sifre", ""))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"E-posta Hatası: {e}")
        return False

# --- ANA ARAYÜZ ---
st.title("🩺 Sade Tansiyon Takip")

# 1. YENİ KAYIT EKLEME (Nabızsız)
with st.container(border=True):
    st.subheader("➕ Yeni Ölçüm")
    col1, col2 = st.columns(2)
    with col1: tarih_giris = st.date_input("Tarih", datetime.now())
    with col2: vakit_giris = st.selectbox("Vakit", ["Sabah", "Akşam"])
    
    # Nabız sütununu sildik, sadece 2 sütun kaldı
    c1, c2 = st.columns(2)
    with c1: sistolik = st.number_input("Büyük (Sistolik)", 7, 22, 12)
    with c2: diyastolik = st.number_input("Küçük (Diyastolik)", 4, 14, 8)
    
    if st.button("KAYDET", use_container_width=True, type="primary"):
        zaman = datetime.combine(tarih_giris, datetime.now().time()).strftime("%Y-%m-%d %H:%M")
        yeni_veri = pd.DataFrame([[zaman, vakit_giris, sistolik, diyastolik]], 
                                 columns=["Tarih", "Vakit", "Sistolik", "Diyastolik"])
        df_mevcut = verileri_yukle()
        pd.concat([df_mevcut, yeni_veri], ignore_index=True).to_csv(DB_FILE, index=False)
        st.success(f"Başarıyla kaydedildi: {sistolik}/{diyastolik}")
        st.rerun()

# 2. ANALİZ
df = verileri_yukle()

if not df.empty:
    st.divider()
    st.subheader("📈 Analiz Grafiği")
    fig = px.line(df, x="Tarih", y=["Sistolik", "Diyastolik"], 
                  markers=True, color_discrete_sequence=["#FF4B4B", "#0068C9"],
                  labels={"value": "Değer", "variable": "Ölçüm"})
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📧 Rapor Gönder", use_container_width=True):
            if mail_gonder(DB_FILE): st.success("E-posta iletildi!")
    with col_b:
        st.download_button("📥 Excel Olarak Al", data=df.to_csv(index=False).encode('utf-8'), 
                           file_name="tansiyon_rapor.csv", use_container_width=True)

    st.divider()
    
    # 3. YÖNETİM
    st.subheader("📋 Kayıtlar")
    
    if "editor_key" not in st.session_state:
        st.session_state.editor_key = 0

    edited_df = st.data_editor(
        df, 
        use_container_width=True, 
        num_rows="dynamic",
        key=f"ed_{st.session_state.editor_key}",
        column_config={
            "Tarih": st.column_config.TextColumn("Tarih", disabled=True),
            "Vakit": st.column_config.TextColumn("Vakit", disabled=True),
            "Sistolik": st.column_config.NumberColumn("Büyük", min_value=7, max_value=22),
            "Diyastolik": st.column_config.NumberColumn("Küçük", min_value=4, max_value=14),
        }
    )

    if len(edited_df) != len(df):
        st.warning("⚠️ Değişiklik yapıldı. Kaydetmek istiyor musunuz?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Onayla", type="primary", use_container_width=True):
                edited_df.to_csv(DB_FILE, index=False)
                st.rerun()
        with c2:
            if st.button("❌ Vazgeç", use_container_width=True):
                st.session_state.editor_key += 1
                st.rerun()
else:
    st.info("Henüz veri yok.")
