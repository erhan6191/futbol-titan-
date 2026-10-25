import streamlit as st
import requests
import itertools
import math
import time
import numpy as np
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Spor Toto Tam Otonom AI v2", page_icon="⚽", layout="wide")
st.title("🏆 Spor Toto AI & Vektörel Blok Filtreleme (v2.0)")

with st.sidebar:
    st.header("⚙️ Sistem Ayarları")
    api_key = st.text_input("API-Football Anahtarı:", type="password")
    kolon_fiyati = st.number_input("Kolon Birim Fiyatı (TL):", min_value=1.0, value=10.0, step=1.0)
    
    st.subheader("🎯 Garanti Sistemi")
    garanti_secimi = st.selectbox(
        "Hedeflenen Garanti:", 
        ["15 Garanti (Tam Kombinasyon)", "14 Garanti (1 Hata Payı)", 
         "13 Garanti (2 Hata Payı)", "12 Garanti (3 Hata Payı)"]
    )
    garanti_derecesi = int(garanti_secimi.split()[0])
    
    st.subheader("🧠 Yapay Zeka Yönetimi")
    ai_filtre_modu = st.toggle(
        "🤖 Tam Otonom Mod (Tavsiye Edilen)", 
        value=True, 
        help="Tüm limitleri, ardışık engelleri ve blok filtrelerini haftanın zorluğuna göre AI kendi ayarlar."
    )
    
    if not ai_filtre_modu:
        st.markdown("**(Min - Max) Manuel Değerler:**")
        range_1 = st.slider("Ev Sahibi (1)", 0, 15, (4, 9))
        range_x = st.slider("Beraberlik (X)", 0, 15, (1, 5))
        range_2 = st.slider("Deplasman (2)", 0, 15, (2, 7))
        range_puan = st.slider("Puan (Sürpriz-Favori)", 300, 1200, (550, 900))
        max_ardisik_1 = st.slider("Üst Üste '1'", 2, 10, 5)
        max_ardisik_x = st.slider("Üst Üste 'X'", 2, 10, 3)
        max_ardisik_2 = st.slider("Üst Üste '2'", 2, 10, 4)
        banko_siniri = st.number_input("Banko Sınırı (%)", min_value=35, max_value=95, value=60)
        cifte_sans_siniri = st.number_input("Çifte Şans Sınırı (%)", min_value=30, max_value=80, value=42)
        
        st.subheader("🔗 Manuel Blok Filtresi")
        aktif_blok_filtresi = st.toggle("Blok Sonuç Sınırlandırma", value=True)
        max_blok_tekrar = st.slider("3'lü Blokta Aynı Sonuç Maksimum Tekrarı", 1, 3, 2)


@st.cache_data(ttl=3600, show_spinner=False)
def maclari_getir(api_key):
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "v3.football.api-sports.io"}
    ligler = [203, 39, 140, 135, 78, 61, 2, 3, 848, 204, 40, 88, 94, 144, 71]
    tum_maclar = []
    
    for lig in ligler:
        url = f"https://v3.football.api-sports.io/fixtures?league={lig}&next=10"
        try:
            res = requests.get(url, headers=headers, timeout=10).json()
            if res.get('response'):
                for item in res['response']:
                    f_id = item['fixture']['id']
                    ev = item['teams']['home']['name']
                    dep = item['teams']['away']['name']
                    tarih = item['fixture']['date'][:10]
                    tum_maclar.append({"id": f_id, "label": f"{tarih} | {ev} - {dep}"})
        except Exception:
            continue
    return tum_maclar


@st.cache_data(ttl=3600, show_spinner=False)
def tahminleri_al(secilen_maclar, api_key):
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "v3.football.api-sports.io"}
    sonuclar = []
    progress = st.progress(0, text="Yapay Zeka maç verilerini çekiyor...")
    
    for i, mac in enumerate(secilen_maclar):
        url = f"https://v3.football.api-sports.io/predictions?fixture={mac['id']}"
        try:
            res = requests.get(url, headers=headers, timeout=10).json()
            if res.get('response') and res['response'][0].get('predictions'):
                t = res['response'][0]['predictions']['percent']
                sonuclar.append({
                    "mac": mac['label'],
                    "1": int(t['home'].replace('%', '')),
                    "X": int(t['draw'].replace('%', '')),
                    "2": int(t['away'].replace('%', ''))
                })
            else:
                # API'de tahmin verisi yoksa dengeli varsayılan değer ata (Çökmeyi önler)
                sonuclar.append({"mac": mac['label'], "1": 35, "X": 33, "2": 32})
        except Exception:
            sonuclar.append({"mac": mac['label'], "1": 35, "X": 33, "2": 32})
            
        progress.progress((i + 1) / len(secilen_maclar))
        time.sleep(0.25)
        
    progress.empty()
    return sonuclar


def tam_otonom_analiz(mac_verileri):
    beklenen_1, beklenen_x, beklenen_2, min_puan, max_puan = 0, 0, 0, 0, 0
    en_yuksek_ihtimaller = []
    
    for v in mac_verileri:
        sirali = sorted([v["1"], v["X"], v["2"]])
        min_puan += sirali[0]
        max_puan += sirali[2]
        en_yuksek_ihtimaller.append(sirali[2])
        
        if v["1"] == sirali[2]: beklenen_1 += 1
        elif v["X"] == sirali[2]: beklenen_x += 1
        else: beklenen_2 += 1

    hafta_zorlugu = float(np.mean(en_yuksek_ihtimaller))
    
    # Çok fazla kapalı maç açılıp RAM'i şişirmemesi için dengeli eşikler
    ai_banko = max(52, int(hafta_zorlugu + 5))
    ai_cifte = max(36, int(hafta_zorlugu - 8))
    ai_blok_tekrar = 3 if hafta_zorlugu > 62 else 2

    # Puan aralığını min_puan ve max_puan arasındaki farka göre güvenli hesapla
    puan_farki = max(10, max_puan - min_puan)
    alt_puan = int(min_puan + (puan_farki * 0.35))
    ust_puan = int(min_puan + (puan_farki * 0.92))

    ai_limitler = {
        "1": (max(0, beklenen_1 - 3), min(15, beklenen_1 + 4)),
        "X": (max(0, beklenen_x - 1), min(15, beklenen_x + 5)),
        "2": (max(0, beklenen_2 - 2), min(15, beklenen_2 + 4)),
        "puan": (alt_puan, ust_puan),
        "ardisik_1": max(3, (beklenen_1 // 2) + 2),
        "ardisik_x": max(2, (beklenen_x // 2) + 2),
        "ardisik_2": max(3, (beklenen_2 // 2) + 2),
        "banko_siniri": ai_banko,
        "cifte_siniri": ai_cifte,
        "aktif_blok_filtresi": True,
        "max_blok_tekrar": ai_blok_tekrar,
        "zorluk_skoru": hafta_zorlugu
    }
    return ai_limitler


def sablon_olustur(veriler, limitler):
    sablon = []
    for v in veriler:
        sirali = sorted([(v["1"], "1"), (v["X"], "X"), (v["2"], "2")], reverse=True)
        en = sirali[0][0]
        if en >= limitler["banko_siniri"]:
            sablon.append([sirali[0][1]])
        elif en >= limitler["cifte_siniri"]:
            sablon.append([sirali[0][1], sirali[1][1]])
        else:
            sablon.append(["1", "X", "2"])
            
    # Eğer 3'lü bir blokta 3 maç da aynı Banko ise, blok filtresinin tüm kuponları
    # sıfırlamaması için en düşük yüzdeli bankoyu çifte şansa çevir
    if limitler.get("aktif_blok_filtresi") and limitler["max_blok_tekrar"] < 3:
        for b in range(0, 15, 3):
            blok_sablon = sablon[b:b+3]
            if all(len(s) == 1 for s in blok_sablon):
                if blok_sablon[0][0] == blok_sablon[1][0] == blok_sablon[2][0]:
                    # Bloktaki en düşük oranlı bankoyu bul ve 2. ihtimali ekle
                    en_zayif_idx = min(range(b, b+3), key=lambda idx: max(veriler[idx]["1"], veriler[idx]["X"], veriler[idx]["2"]))
                    sirali = sorted([(veriler[en_zayif_idx]["1"], "1"), (veriler[en_zayif_idx]["X"], "X"), (veriler[en_zayif_idx]["2"], "2")], reverse=True)
                    sablon[en_zayif_idx] = [sirali[0][1], sirali[1][1]]
    return sablon


def max_ardisik_bul(kupon, hedef):
    max_say = 0
    guncel = 0
    for s in kupon:
        if s == hedef:
            guncel += 1
            if guncel > max_say:
                max_say = guncel
        else:
            guncel = 0
    return max_say


def kolonlari_filtrele(sablon, mac_verileri, limitler):
    gecerli = []
    puanlar = []
    
    min_1, max_1 = limitler["1"]
    min_x, max_x = limitler["X"]
    min_2, max_2 = limitler["2"]
    min_p, max_p = limitler["puan"]
    ard_1, ard_x, ard_2 = limitler["ardisik_1"], limitler["ardisik_x"], limitler["ardisik_2"]
    blok_aktif = limitler.get("aktif_blok_filtresi", False)
    max_blok = limitler.get("max_blok_tekrar", 3)

    # list() kullanmadan doğrudan generator üzerinden bellek dostu iterasyon
    for kupon in itertools.product(*sablon):
        c1, cx, c2 = kupon.count('1'), kupon.count('X'), kupon.count('2')
        if not (min_1 <= c1 <= max_1 and min_x <= cx <= max_x and min_2 <= c2 <= max_2):
            continue
            
        puan = sum(mac_verileri[i][t] for i, t in enumerate(kupon))
        if not (min_p <= puan <= max_p):
            continue

        if max_ardisik_bul(kupon, '1') > ard_1: continue
        if max_ardisik_bul(kupon, 'X') > ard_x: continue
        if max_ardisik_bul(kupon, '2') > ard_2: continue
        
        if blok_aktif and max_blok < 3:
            blok_ihlali = False
            for b in range(0, 15, 3):
                b1, b2, b3 = kupon[b], kupon[b+1], kupon[b+2]
                if (max_blok == 2 and b1 == b2 == b3) or (max_blok == 1 and (b1 == b2 or b2 == b3 or b1 == b3)):
                    blok_ihlali = True
                    break
            if blok_ihlali:
                continue

        gecerli.append(kupon)
        puanlar.append(puan)
        
    # Kuponları en yüksek olasılık puanından en düşüğe doğru sırala (Garanti kalitesi için)
    sirali_indeksler = np.argsort(puanlar)[::-1]
    return [gecerli[i] for i in sirali_indeksler]


def garanti_sistemi_uygula(kolonlar, hedef):
    if hedef == 15 or not kolonlar:
        return kolonlar
        
    fark = 15 - hedef
    harita = {'1': 0, 'X': 1, '2': 2}
    
    # NumPy Vektörel Hamming Mesafesi Hesaplama (Klasik döngüden ~100x daha hızlı)
    matris = np.array([[harita[s] for s in k] for k in kolonlar], dtype=np.int8)
    aktif_maske = np.ones(len(kolonlar), dtype=bool)
    nihai_indeksler = []
    
    with st.spinner('Vektörel garanti algoritması çalışıyor...'):
        while np.any(aktif_maske):
            # Aktif olanlar arasından en yüksek puanlı (ilk sıradaki) kolonu merkez seç
            merkez_idx = int(np.argmax(aktif_maske))
            nihai_indeksler.append(merkez_idx)
            merkez_vektor = matris[merkez_idx]
            
            # Sadece hala aktif olan kolonlarla olan Hamming mesafesini hesapla
            aktif_indeksler = np.where(aktif_maske)[0]
            mesafeler = np.sum(matris[aktif_indeksler] != merkez_vektor, axis=1)
            
            # Mesafesi 'fark' veya daha az olanları kapsanmış olarak işaretle
            kapsanan_indeksler = aktif_indeksler[mesafeler <= fark]
            aktif_maske[kapsanan_indeksler] = False
            
    return [kolonlar[i] for i in nihai_indeksler]


# --- ARAYÜZ ---
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🌍 Global Maç Bülteni")
    if api_key:
        if "mac_listesi" not in st.session_state:
            with st.spinner("Ligler çekiliyor..."):
                st.session_state.mac_listesi = maclari_getir(api_key)
        
        opsiyonlar = {m['label']: m for m in st.session_state.mac_listesi}
        secilenler_label = st.multiselect(
            "Bültenden Tam 15 Maç Seçin:", 
            list(opsiyonlar.keys()), 
            max_selections=15
        )
        
        if len(secilenler_label) == 15:
            baslat = st.button("🚀 Analizi ve Motoru Başlat", type="primary", use_container_width=True)
        else:
            st.caption(f"Seçilen maç sayısı: **{len(secilenler_label)} / 15**")
            baslat = False
    else:
        st.info("API Anahtarınızı sol menüden girdiğinizde ligler otomatik yüklenecektir.")
        baslat = False

if api_key and len(secilenler_label) == 15 and baslat:
    secilenler_data = [opsiyonlar[lbl] for lbl in secilenler_label]
    with col2:
        veriler = tahminleri_al(secilenler_data, api_key)
        
        if ai_filtre_modu:
            limitler = tam_otonom_analiz(veriler)
            st.info(
                f"🤖 **Otonom Durum Raporu:** Haftanın Zorluk Derecesi **%{limitler['zorluk_skoru']:.1f}** | "
                f"Banko Sınırı **%{limitler['banko_siniri']}** | Çifte Şans **%{limitler['cifte_siniri']}** | "
                f"Puan Aralığı **{limitler['puan'][0]}-{limitler['puan'][1]}** | "
                f"3'lü Blok Tekrar Limiti **{limitler['max_blok_tekrar']}**"
            )
        else:
            limitler = {
                "1": range_1, "X": range_x, "2": range_2, "puan": range_puan,
                "ardisik_1": max_ardisik_1, "ardisik_x": max_ardisik_x, "ardisik_2": max_ardisik_2,
                "banko_siniri": banko_siniri, "cifte_siniri": cifte_sans_siniri,
                "aktif_blok_filtresi": aktif_blok_filtresi, "max_blok_tekrar": max_blok_tekrar
            }
        
        sablon = sablon_olustur(veriler, limitler)
        toplam_kombinasyon = math.prod(len(s) for s in sablon)
        
        # Maç ve Şablon Özeti Tablosu
        with st.expander("📋 Üretilen Maç Şablonunu ve Oranları Gör", expanded=True):
            tablo_verisi = []
            for idx, (v, s) in enumerate(zip(veriler, sablon), 1):
                tip = "🔒 Banko" if len(s) == 1 else ("⚖️ Çifte Şans" if len(s) == 2 else "🌐 Kapalı (1X2)")
                tablo_verisi.append({
                    "No": idx,
                    "Maç": v["mac"],
                    "1 (%)": v["1"],
                    "X (%)": v["X"],
                    "2 (%)": v["2"],
                    "Şablon Tercihi": "".join(s),
                    "Kategori": tip
                })
            st.dataframe(pd.DataFrame(tablo_verisi), use_container_width=True, hide_index=True)

        if toplam_kombinasyon > 2_000_000:
            st.warning(f"⚠️ Şablon {toplam_kombinasyon:,} kombinasyon üretiyor. İşlem süresi uzayabilir; Banko/Çifte sınırlarını düşürmeyi düşünebilirsiniz.")
            
        filtrelenmis = kolonlari_filtrele(sablon, veriler, limitler)
        
        if not filtrelenmis:
            st.error("Filtreler tüm kombinasyonları eledi. Manuel modda sınırları genişletin veya maç seçimini kontrol edin.")
        else:
            garantili = garanti_sistemi_uygula(filtrelenmis, garanti_derecesi)
            st.success("Optimizasyon Başarıyla Tamamlandı!")
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Ham Şablon", f"{toplam_kombinasyon:,} Kolon")
            m2.metric("Filtre Sonrası", f"{len(filtrelenmis):,} Kolon")
            m3.metric(
                f"{garanti_derecesi} Garantili", 
                f"{len(garantili):,} Kolon", 
                f"{len(garantili) * kolon_fiyati:,.0f} TL"
            )
            
            st.download_button(
                "📥 Kuponları İndir (.txt)", 
                "\n".join([" ".join(k) for k in garantili]), 
                f"spor_toto_ai_{garanti_derecesi}.txt",
                use_container_width=True
            )
            
            st.markdown("### 📊 Yapay Zeka Risk ve Dağılım Raporu")
            toplam_1 = sum(k.count('1') for k in garantili)
            toplam_x = sum(k.count('X') for k in garantili)
            toplam_2 = sum(k.count('2') for k in garantili)
            
            fig = px.pie(
                names=['Ev Sahibi (1)', 'Beraberlik (X)', 'Deplasman (2)'], 
                values=[toplam_1, toplam_x, toplam_2], 
                title="Nihai Kuponlardaki Genel İhtimal Dağılımı",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig, use_container_width=True)
