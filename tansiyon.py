import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- 1. GÜVENLİ KULLANICI DOĞRULAMA ---
# Secrets kontrolü ekleyerek hatayı engelleyelim
if "credentials" in st.secrets:
    authenticator = stauth.Authenticate(
        st.secrets["credentials"],
        st.secrets["auth"]["cookie_name"],
        st.secrets["auth"]["key"],
        st.secrets["auth"]["expiry_days"]
    )
else:
    st.error("Hata: Secrets panelinde 'credentials' bulunamadı!")
    st.stop()

# Giriş ekranı
authenticator.login(location='main')

# --- 2. GİRİŞ KONTROLÜ VE UYGULAMA AKIŞI ---
if st.session_state["authentication_status"] == False:
    st.error("Kullanıcı adı veya şifre hatalı!")
elif st.session_state["authentication_status"] == None:
    st.warning("Lütfen kullanıcı adı ve şifrenizle giriş yapın.")
elif st.session_state["authentication_status"]:
    
    # Kullanıcı bilgilerini alalım
    name = st.session_state["name"]
    username = st.session_state["username"]

    # Çıkış butonunu yan menüye koyalım
    with st.sidebar:
        st.write(f"Hoş geldin, **{name}**")
        authenticator.logout("Çıkış Yap", "sidebar")

    # HER KULLANICI İÇİN AYRI DOSYA
    DB_FILE = f"tansiyon_{username}.csv"

    # --- FONKSİYONLAR ---
    def verileri_yukle():
        if os.path.exists(DB_FILE):
            return pd.read_csv(DB_FILE)
        return pd.DataFrame(columns=["Tarih", "Vakit", "Sistolik", "Diyastolik", "Nabiz"])

    def mail_gonder(dosya_yolu):
        try:
            # Secrets'tan mail bilgilerini al (Eğer ayarlı değilse boş döner)
            GONDEREN = st.secrets.get("email_ayarlari", {}).get("gonderen", "")
            ALICI = st.secrets.get("email_ayarlari", {}).get("alici", "")
            SIFRE = st.secrets.get("email_ayarlari", {}).get("sifre", "")
            
            msg = MIMEMultipart()
            msg['From'] = GONDEREN
            msg['To'] = ALICI
            msg['Subject'] = f"Tansiyon Raporu ({name}) - {datetime.now().strftime('%d/%m/%Y')}"
            body = f"Sayın ilgili,\n\n{name} kullanıcısına ait güncel tansiyon kayıtları ektedir."
            msg.attach(MIMEText(body, 'plain'))
            with open(dosya_yolu, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {dosya_yolu}")
                msg.attach(part)
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(GONDEREN, SIFRE)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            st.error(f"E-posta gönderilemedi: {e}")
            return False

    # --- ANA ARAYÜZ ---
    st.title(f"🩺 {name} - Tansiyon Takip")

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
        st.subheader("📈 Değişim Grafiği")
        try:
            fig = px.line(df, x="Tarih", y=["Sistolik", "Diyastolik"], 
                          labels={"value": "Değer", "variable": "Ölçüm"},
                          markers=True, color_discrete_sequence=["#FF4B4B", "#0068C9"])
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.info("Grafik yükleniyor...")

        # İşlem Butonları
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📧 Raporu Mail At", use_container_width=True):
                with st.spinner("Gönderiliyor..."):
                    if mail_gonder(DB_FILE): st.success("Mail iletildi!")
        with col_b:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Excel İndir", data=csv, file_name=f"tansiyon_{username}.csv", use_container_width=True)

        st.divider()

        # 3. ONAY MEKANİZMALI TABLO ALANI
        st.subheader("📋 Kayıt Yönetimi")
        
        if "editor_key" not in st.session_state:
            st.session_state.editor_key = 0

        edited_df = st.data_editor(
            df, 
            use_container_width=True, 
            num_rows="dynamic",
            key=f"editor_{st.session_state.editor_key}",
            column_config={
                "Tarih": st.column_config.TextColumn("Tarih", disabled=True),
                "Vakit": st.column_config.TextColumn("Vakit", disabled=True),
            }
        )

        # Silme/Düzenleme Kontrolü
        if len(edited_df) != len(df):
            st.warning("⚠️ Satır sildiniz. Bu işlemi kalıcı hale getirmek istiyor musunuz?")
            
            c_onay1, c_onay2 = st.columns(2)
            with c_onay1:
                if st.button("✅ Evet, Kaydet", type="primary", use_container_width=True):
                    edited_df.to_csv(DB_FILE, index=False)
                    st.success("Değişiklikler kaydedildi!")
                    st.rerun()
            with c_onay2:
                if st.button("❌ Hayır, Geri Al", type="secondary", use_container_width=True):
                    st.session_state.editor_key += 1
                    st.rerun()
    else:
        st.info("Henüz veri girişi yapılmamış.")
