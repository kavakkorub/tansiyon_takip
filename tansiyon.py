import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os

# --- KONFİGÜRASYON ---
st.set_page_config(page_title="Tansiyon Takip", layout="centered", page_icon="🩺")

DB_FILE = "tansiyon_verileri.csv"

def verileri_yukle():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Tarih", "Vakit", "Sistolik", "Diyastolik"])

# --- ANA ARAYÜZ ---
st.title("🩺 Tansiyon Takip Sistemi")

# 1. YENİ KAYIT EKLEME
with st.container(border=True):
    st.subheader("➕ Yeni Ölçüm")
    
    col_tarih, col_vakit = st.columns(2)
    with col_tarih: 
        tarih_giris = st.date_input("Tarih Seçin", datetime.now())
    
    with col_vakit: 
        # Liste başında "Sabah" olduğu için her yenilemede "Sabah" seçili gelecek
        vakit_giris = st.selectbox("Vakit", ["Sabah", "Akşam"])
    
    c1, c2 = st.columns(2)
    with c1: sistolik = st.number_input("Büyük", 7, 22, 12)
    with c2: diyastolik = st.number_input("Küçük", 4, 14, 8)
    
    if st.button("KAYDET", use_container_width=True, type="primary"):
        zaman_obj = datetime.combine(tarih_giris, datetime.now().time())
        zaman_str = zaman_obj.strftime("%Y-%m-%d %H:%M")
        
        yeni_veri = pd.DataFrame([[zaman_str, vakit_giris, sistolik, diyastolik]], 
                                 columns=["Tarih", "Vakit", "Sistolik", "Diyastolik"])
        
        df_mevcut = verileri_yukle()
        pd.concat([df_mevcut, yeni_veri], ignore_index=True).to_csv(DB_FILE, index=False)
        
        st.success(f"Kaydedildi: {sistolik}/{diyastolik}")
        # Sayfayı yeniden çalıştırarak tüm inputları (Vakit dahil) başlangıç değerine döndürüyoruz
        st.rerun()

# 2. VERİ LİSTESİ VE DÜZENLEME
df = verileri_yukle()

if not df.empty:
    st.divider()
    st.subheader("📋 Kayıt Yönetimi")
    
    if "editor_key" not in st.session_state:
        st.session_state.editor_key = 0

    edited_df = st.data_editor(
        df, 
        use_container_width=True, 
        num_rows="dynamic",
        key=f"ed_{st.session_state.editor_key}",
        column_config={
            "Tarih": st.column_config.TextColumn("Tarih"), 
            "Vakit": st.column_config.SelectboxColumn("Vakit", options=["Sabah", "Akşam"]),
            "Sistolik": st.column_config.NumberColumn("Büyük", min_value=7, max_value=22),
            "Diyastolik": st.column_config.NumberColumn("Küçük", min_value=4, max_value=14),
        }
    )

    if not edited_df.equals(df):
        st.warning("⚠️ Değişiklikleri onaylıyor musunuz?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Kaydet", type="primary", use_container_width=True):
                edited_df.to_csv(DB_FILE, index=False)
                st.rerun()
        with c2:
            if st.button("❌ İptal", use_container_width=True):
                st.session_state.editor_key += 1
                st.rerun()

    # 3. ANALİZ VE YEDEKLEME
    st.divider()
    st.subheader("📈 Analiz ve Yedekleme")
    fig = px.line(df, x="Tarih", y=["Sistolik", "Diyastolik"], markers=True)
    st.plotly_chart(fig, use_container_width=True)
    
    csv_dosya = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Verileri Bilgisayara Yedekle (CSV)",
        data=csv_dosya,
        file_name=f"tansiyon_yedek_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.info("Henüz kayıt bulunamadı.")
