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
    c1, c2 = st.columns(2)
    with c1: sistolik = st.number_input("Büyük", 7, 22, 12)
    with c2: diyastolik = st.number_input("Küçük", 4, 14, 8)
    
    if st.button("KAYDET", use_container_width=True, type="primary"):
        zaman = datetime.now().strftime("%Y-%m-%d %H:%M")
        vakit = "Sabah" if datetime.now().hour < 12 else "Akşam"
        yeni_veri = pd.DataFrame([[zaman, vakit, sistolik, diyastolik]], 
                                 columns=["Tarih", "Vakit", "Sistolik", "Diyastolik"])
        df_mevcut = verileri_yukle()
        pd.concat([df_mevcut, yeni_veri], ignore_index=True).to_csv(DB_FILE, index=False)
        st.success("Kaydedildi!")
        st.rerun()

# 2. VERİ LİSTESİ VE DÜZENLEME
df = verileri_yukle()

if not df.empty:
    st.divider()
    st.subheader("📋 Kayıt Yönetimi")
    st.info("💡 Tablodaki rakamların üzerine çift tıklayarak değerleri değiştirebilirsiniz.")
    
    if "editor_key" not in st.session_state:
        st.session_state.editor_key = 0

    # DÜZENLENEBİLİR TABLO
    edited_df = st.data_editor(
        df, 
        use_container_width=True, 
        num_rows="dynamic", # Satır silmeye izin verir
        key=f"ed_{st.session_state.editor_key}",
        column_config={
            "Tarih": st.column_config.TextColumn("Tarih", disabled=True), # Değiştirilemez
            "Vakit": st.column_config.TextColumn("Vakit", disabled=True), # Değiştirilemez
            "Sistolik": st.column_config.NumberColumn("Büyük", min_value=7, max_value=22, required=True),
            "Diyastolik": st.column_config.NumberColumn("Küçük", min_value=4, max_value=14, required=True),
        }
    )

    # Değişiklik Kontrolü (Hem silme hem de değer düzeltme için)
    # pandas.equals() kullanarak tablodaki herhangi bir hücre değişti mi diye bakıyoruz
    if not edited_df.equals(df):
        st.warning("⚠️ Tabloda değişiklik yaptınız (değer düzeltme veya silme).")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Değişiklikleri Kaydet", type="primary", use_container_width=True):
                edited_df.to_csv(DB_FILE, index=False)
                st.success("Güncellendi!")
                st.rerun()
        with c2:
            if st.button("❌ İptal Et / Geri Al", use_container_width=True):
                st.session_state.editor_key += 1
                st.rerun()

    # 3. ANALİZ GRAFİĞİ (En altta)
    st.divider()
    st.subheader("📈 Analiz")
    fig = px.line(df, x="Tarih", y=["Sistolik", "Diyastolik"], markers=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Henüz veri yok.")
