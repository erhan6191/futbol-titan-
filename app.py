import streamlit as st
import requests
import math
import time
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Spor Toto AI Pro v4.0", page_icon="⚽", layout="wide")
st.title("🏆 Spor Toto AI v4.0 — Kupon Üretim & Canlı Takip Merkezi")

# --- SESSION STATE BAŞLATMA ---
if "mac_listesi" not in st.session_state:
    st.session_state.mac_listesi = []
if "analiz_verisi" not in st.session_state:
    st.session_state.analiz_verisi = None
if "secilen_mac_idleri" not in st.session_state:
    st.session_state.secilen_mac_idleri = []
if "uretilen_kuponlar" not in st.session_state:
    st.session_state.uretilen_kuponlar = None
if "canli_sonuclar" not in st.session_state:
    st.session_state.canli_sonuclar = ["⏳ Bekliyor"] * 15
if "canli_skor_metni" not in st.session_state:
    st.session_state.canli_skor_metni = ["-"] * 15

# --- YAN MENÜ (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Sistem ve Bütçe Ayarları")
    api_key = st.text_input("API-Football Anahtarı:", type="password")
    kolon_fiyati = st.number_input("Kolon Birim Fiyatı (TL):", min_value=1.0, value=10.0, step=1.0)
    
    st.subheader("🎯 Garanti ve Bütçe Limiti")
    garanti_secimi = st.selectbox(
        "Hedeflenen Garanti:", 
        ["15 Garanti (Tam Kombinasyon)", "14 Garanti (1 Hata Payı)", 
         "13 Garanti (2 Hata Payı)", "12 Garanti (3 Hata Payı)"],
        index=1
    )
    garanti_derecesi = int(garanti_secimi.split()[0])
    
    butce_aktif = st.toggle("💰 Maksimum Kolon / Bütçe Sınırı Koy", value=False)
    if butce_aktif:
        max_kolon_limiti = st.number_input(
            "Maksimum Kolon Sayısı:", min_value=1, max_value=50000, value=100, step=10
        )
        st.caption(f"Maksimum Bütçe: **{max_kolon_limiti * kolon_fiyati:,.0f} TL**")
    else:
        max_kolon_limiti = None

    st.subheader("🧠 Yapay Zeka Yönetimi")
    strateji_modu = st.radio(
        "Oyun Stratejisi:",
        ["⚖️ Dengeli (Standart)", "🛡️ Favori Korumalı", "💎 İkramiye Avcısı (Sürpriz Odaklı)"]
    )
    
    ai_filtre_modu = st.toggle("🤖 Tam Otonom Filtre (Tavsiye Edilen)", value=True)
    
    if not ai_filtre_modu:
        st.markdown("**(Min - Max) Manuel Değerler:**")
        range_1 = st.slider("Ev Sahibi (1)", 0, 15, (4, 9))
        range_x = st.slider("Beraberlik (X)", 0, 15, (1, 5))
        range_2 = st.slider("Deplasman (2)", 0, 15, (2, 7))
        range_puan = st.slider("Puan (Sürpriz-Favori)", 300, 1200, (550, 900))
        range_surpriz = st.slider("Sürpriz Maç Sayısı (Oran <%30)", 0, 10, (0, 5))
        max_ardisik_1 = st.slider("Üst Üste '1'", 2, 10, 5)
        max_ardisik_x = st.slider("Üst Üste 'X'", 2, 10, 3)
        max_ardisik_2 = st.slider("Üst Üste '2'", 2, 10, 4)
        banko_siniri = st.number_input("Banko Sınırı (%)", 35, 95, 60)
        cifte_sans_siniri = st.number_input("Çifte Şans Sınırı (%)", 30, 80, 42)
        aktif_blok_filtresi = st.toggle("3'lü Blok Sonuç Sınırlandırma", value=True)
        max_blok_tekrar = st.slider("3'lü Blokta Maksimum Aynı Sonuç", 1, 3, 2)


# --- API FONKSİYONLARI ---
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
    progress = st.progress(0, text="Yapay Zeka maç tahminlerini analiz ediyor...")
    
    for i, mac in enumerate(secilen_maclar):
        url = f"https://v3.football.api-sports.io/predictions?fixture={mac['id']}"
        try:
            res = requests.get(url, headers=headers, timeout=10).json()
            if res.get('response') and res['response'][0].get('predictions'):
                t = res['response'][0]['predictions']['percent']
                p1 = int(t['home'].replace('%', ''))
                px_val = int(t['draw'].replace('%', ''))
                p2 = int(t['away'].replace('%', ''))
                toplam = max(1, p1 + px_val + p2)
                sonuclar.append({
                    "id": mac['id'],
                    "mac": mac['label'],
                    "1": round(p1 * 100 / toplam),
                    "X": round(px_val * 100 / toplam),
                    "2": 100 - round(p1 * 100 / toplam) - round(px_val * 100 / toplam)
                })
            else:
                sonuclar.append({"id": mac['id'], "mac": mac['label'], "1": 36, "X": 33, "2": 31})
        except Exception:
            sonuclar.append({"id": mac['id'], "mac": mac['label'], "1": 36, "X": 33, "2": 31})
            
        progress.progress((i + 1) / len(secilen_maclar))
        time.sleep(0.2)
        
    progress.empty()
    return sonuclar


def canli_skorlari_cek(fixture_id_listesi, api_key):
    """15 maçın tamamını tek bir API isteğiyle (ids=id1-id2-...) sorgular."""
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "v3.football.api-sports.io"}
    ids_str = "-".join(str(fid) for fid in fixture_id_listesi)
    url = f"https://v3.football.api-sports.io/fixtures?ids={ids_str}"
    
    yeni_sonuclar = ["⏳ Bekliyor"] * 15
    skor_metinleri = ["-"] * 15
    
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        if res.get("response"):
            id_haritasi = {item["fixture"]["id"]: item for item in res["response"]}
            for idx, fid in enumerate(fixture_id_listesi):
                if fid in id_haritasi:
                    mac_detay = id_haritasi[fid]
                    durum = mac_detay["fixture"]["status"]["short"]
                    ev_gol = mac_detay["goals"]["home"]
                    dep_gol = mac_detay["goals"]["away"]
                    
                    # Maç başladıysa veya bittiyse (NS: Başlamadı, TBD: Belirsiz, PST: Ertelendi)
                    if durum not in ["NS", "TBD", "PST", "CANC"] and ev_gol is not None and dep_gol is not None:
                        skor_metinleri[idx] = f"{ev_gol} - {dep_gol} ({durum})"
                        if ev_gol > dep_gol:
                            yeni_sonuclar[idx] = "1"
                        elif ev_gol == dep_gol:
                            yeni_sonuclar[idx] = "X"
                        else:
                            yeni_sonuclar[idx] = "2"
                    else:
                        skor_metinleri[idx] = f"Başlamadı ({durum})"
    except Exception as e:
        st.error(f"Canlı skorlar çekilirken hata oluştu: {e}")
        
    return yeni_sonuclar, skor_metinleri


# --- OTONOM ANALİZ VE VEKTÖREL MOTOR ---
def tam_otonom_analiz(mac_verileri, strateji):
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
    puan_farki = max(15, max_puan - min_puan)

    if "Favori" in strateji:
        ai_banko = max(50, int(hafta_zorlugu + 2))
        ai_cifte = max(35, int(hafta_zorlugu - 10))
        alt_puan = int(min_puan + (puan_farki * 0.55))
        ust_puan = int(max_puan)
        surpriz_aralik = (0, 3)
    elif "İkramiye" in strateji:
        ai_banko = max(58, int(hafta_zorlugu + 8))
        ai_cifte = max(40, int(hafta_zorlugu - 5))
        alt_puan = int(min_puan + (puan_farki * 0.20))
        ust_puan = int(min_puan + (puan_farki * 0.78))
        surpriz_aralik = (2, 6)
    else:
        ai_banko = max(53, int(hafta_zorlugu + 5))
        ai_cifte = max(37, int(hafta_zorlugu - 8))
        alt_puan = int(min_puan + (puan_farki * 0.35))
        ust_puan = int(min_puan + (puan_farki * 0.92))
        surpriz_aralik = (1, 5)

    ai_blok_tekrar = 3 if hafta_zorlugu > 62 else 2

    return {
        "1": (max(0, beklenen_1 - 3), min(15, beklenen_1 + 4)),
        "X": (max(0, beklenen_x - 1), min(15, beklenen_x + 5)),
        "2": (max(0, beklenen_2 - 2), min(15, beklenen_2 + 4)),
        "puan": (alt_puan, ust_puan),
        "surpriz": surpriz_aralik,
        "ardisik_1": max(3, (beklenen_1 // 2) + 2),
        "ardisik_x": max(2, (beklenen_x // 2) + 2),
        "ardisik_2": max(3, (beklenen_2 // 2) + 2),
        "banko_siniri": ai_banko,
        "cifte_siniri": ai_cifte,
        "aktif_blok_filtresi": True,
        "max_blok_tekrar": ai_blok_tekrar,
        "zorluk_skoru": hafta_zorlugu
    }


def varsayilan_sablon_olustur(veriler, limitler):
    sablon = []
    for v in veriler:
        sirali = sorted([(v["1"], "1"), (v["X"], "X"), (v["2"], "2")], reverse=True)
        en = sirali[0][0]
        if en >= limitler["banko_siniri"]:
            secim = [sirali[0][1]]
        elif en >= limitler["cifte_siniri"]:
            secim = [sirali[0][1], sirali[1][1]]
        else:
            secim = ["1", "X", "2"]
        sablon.append(secim)
        
    if limitler.get("aktif_blok_filtresi") and limitler["max_blok_tekrar"] < 3:
        for b in range(0, 15, 3):
            blok_sablon = sablon[b:b+3]
            if all(len(s) == 1 for s in blok_sablon) and (blok_sablon[0][0] == blok_sablon[1][0] == blok_sablon[2][0]):
                en_zayif_idx = min(range(b, b+3), key=lambda idx: max(veriler[idx]["1"], veriler[idx]["X"], veriler[idx]["2"]))
                sirali = sorted([(veriler[en_zayif_idx]["1"], "1"), (veriler[en_zayif_idx]["X"], "X"), (veriler[en_zayif_idx]["2"], "2")], reverse=True)
                sablon[en_zayif_idx] = [sirali[0][1], sirali[1][1]]
    return sablon


def vektorel_filtrele(sablon, mac_verileri, limitler):
    harita = {'1': 0, 'X': 1, '2': 2}
    ters_harita = np.array(['1', 'X', '2'])
    sablon_num = [[harita[s] for s in mac_secim] for mac_secim in sablon]
    
    grids = np.meshgrid(*sablon_num, indexing='ij')
    matris = np.stack(grids, axis=-1).reshape(-1, 15).astype(np.int8)
    
    c1 = np.sum(matris == 0, axis=1)
    cx = np.sum(matris == 1, axis=1)
    c2 = np.sum(matris == 2, axis=1)
    
    maske = (
        (c1 >= limitler["1"][0]) & (c1 <= limitler["1"][1]) &
        (cx >= limitler["X"][0]) & (cx <= limitler["X"][1]) &
        (c2 >= limitler["2"][0]) & (c2 <= limitler["2"][1])
    )
    matris = matris[maske]
    if len(matris) == 0:
        return np.empty((0, 15), dtype=np.int8), np.array([])

    oran_matrisi = np.array([[v["1"], v["X"], v["2"]] for v in mac_verileri], dtype=np.int16)
    secilen_oranlar = oran_matrisi[np.arange(15), matris]
    puanlar = np.sum(secilen_oranlar, axis=1)
    surpriz_sayisi = np.sum(secilen_oranlar < 30, axis=1)
    
    maske_puan = (
        (puanlar >= limitler["puan"][0]) & (puanlar <= limitler["puan"][1]) &
        (surpriz_sayisi >= limitler["surpriz"][0]) & (surpriz_sayisi <= limitler["surpriz"][1])
    )
    matris = matris[maske_puan]
    puanlar = puanlar[maske_puan]
    if len(matris) == 0:
        return np.empty((0, 15), dtype=np.int8), np.array([])

    if limitler.get("aktif_blok_filtresi") and limitler["max_blok_tekrar"] < 3:
        bloklar = matris.reshape(-1, 5, 3)
        b0, b1, b2 = bloklar[:, :, 0], bloklar[:, :, 1], bloklar[:, :, 2]
        if limitler["max_blok_tekrar"] == 2:
            ihlal = np.any((b0 == b1) & (b1 == b2), axis=1)
        else:
            ihlal = np.any((b0 == b1) | (b1 == b2) | (b0 == b2), axis=1)
        matris = matris[~ihlal]
        puanlar = puanlar[~ihlal]
        if len(matris) == 0:
            return np.empty((0, 15), dtype=np.int8), np.array([])

    for deger, anahtar in [(0, "ardisik_1"), (1, "ardisik_x"), (2, "ardisik_2")]:
        max_ard = limitler[anahtar]
        if max_ard < 15 and len(matris) > 0:
            pencere_boyutu = max_ard + 1
            pencereler = sliding_window_view(matris == deger, window_shape=pencere_boyutu, axis=1)
            ardisik_ihlal = np.any(np.all(pencereler, axis=2), axis=1)
            matris = matris[~ardisik_ihlal]
            puanlar = puanlar[~ardisik_ihlal]

    if len(matris) == 0:
        return np.empty((0, 15), dtype=np.int8), np.array([])

    sirali_idx = np.argsort(puanlar)[::-1]
    return ters_harita[matris[sirali_idx]], puanlar[sirali_idx]


def garanti_ve_butce_uygula(kolon_matrisi, puanlar, hedef, max_kolon=None):
    toplam_kolon = len(kolon_matrisi)
    if toplam_kolon == 0:
        return [], [], 0.0

    if hedef == 15:
        if max_kolon and toplam_kolon > max_kolon:
            kapsama = (np.sum(puanlar[:max_kolon]) / np.sum(puanlar)) * 100
            return kolon_matrisi[:max_kolon], puanlar[:max_kolon], kapsama
        return kolon_matrisi, puanlar, 100.0

    fark = 15 - hedef
    harita = {'1': 0, 'X': 1, '2': 2}
    sayisal_matris = np.vectorize(harita.get)(kolon_matrisi).astype(np.int8)
    
    aktif_maske = np.ones(toplam_kolon, dtype=bool)
    nihai_indeksler = []
    
    with st.spinner("Vektörel Garanti ve Bütçe Optimizasyonu çalışıyor..."):
        while np.any(aktif_maske):
            if max_kolon and len(nihai_indeksler) >= max_kolon:
                break
                
            merkez_idx = int(np.argmax(aktif_maske))
            nihai_indeksler.append(merkez_idx)
            merkez_vektor = sayisal_matris[merkez_idx]
            
            aktif_indeksler = np.where(aktif_maske)[0]
            mesafeler = np.sum(sayisal_matris[aktif_indeksler] != merkez_vektor, axis=1)
            
            kapsanan_indeksler = aktif_indeksler[mesafeler <= fark]
            aktif_maske[kapsanan_indeksler] = False

    kapsanan_agirlik = np.sum(puanlar[~aktif_maske]) / np.sum(puanlar) * 100
    return kolon_matrisi[nihai_indeksler], puanlar[nihai_indeksler], float(kapsanan_agirlik)


def kupon_dosyasi_coz(yuklenen_dosya):
    """TXT veya CSV dosyasından 15'li kupon matrisini okur."""
    icerik = yuklenen_dosya.getvalue().decode("utf-8-sig").strip().splitlines()
    kuponlar = []
    for satir in icerik:
        temiz = satir.replace(",", " ").replace(";", " ").split()
        secimler = [h.upper() for h in temiz if h.upper() in ["1", "X", "2", "0"]]
        secimler = ["X" if s == "0" else s for s in secimler]
        if len(secimler) >= 15:
            kuponlar.append(secimler[:15])
    return np.array(kuponlar) if kuponlar else None


# ==============================================================================
# ANA SEKMELER (TABS)
# ==============================================================================
tab_uretim, tab_takip = st.tabs([
    "🚀 1. Kupon Üretim ve Optimizasyon Motoru", 
    "📡 2. Canlı Kupon & İkramiye Takip Merkezi"
])

# ------------------------------------------------------------------------------
# SEKME 1: KUPON ÜRETİM MOTORU
# ------------------------------------------------------------------------------
with tab_uretim:
    col1, col2 = st.columns([1, 2.2])

    with col1:
        st.markdown("### 🌍 Global Maç Bülteni")
        if api_key:
            if not st.session_state.mac_listesi:
                with st.spinner("Lig bültenleri çekiliyor..."):
                    st.session_state.mac_listesi = maclari_getir(api_key)
            
            opsiyonlar = {m['label']: m for m in st.session_state.mac_listesi}
            secilenler_label = st.multiselect(
                "Bültenden Tam 15 Maç Seçin:", 
                list(opsiyonlar.keys()), 
                max_selections=15
            )
            
            st.caption(f"Seçilen Maç Sayısı: **{len(secilenler_label)} / 15**")
            
            if len(secilenler_label) == 15:
                if st.button("🚀 Maçları Analiz Et ve Şablon Kur", type="primary", use_container_width=True):
                    secilenler_data = [opsiyonlar[lbl] for lbl in secilenler_label]
                    st.session_state.secilen_mac_idleri = [m["id"] for m in secilenler_data]
                    st.session_state.analiz_verisi = tahminleri_al(secilenler_data, api_key)
                    st.session_state.canli_sonuclar = ["⏳ Bekliyor"] * 15
                    st.session_state.canli_skor_metni = ["-"] * 15
        else:
            st.info("👈 Bülteni çekmek için sol menüden API-Football anahtarınızı girin. (Sadece kupon kontrolü yapacaksanız 2. Sekmeye geçebilirsiniz.)")

    with col2:
        if st.session_state.analiz_verisi:
            veriler = st.session_state.analiz_verisi
            
            if ai_filtre_modu:
                limitler = tam_otonom_analiz(veriler, strateji_modu)
                st.info(
                    f"🤖 **Otonom AI ({strateji_modu}):** Zorluk **%{limitler['zorluk_skoru']:.1f}** | "
                    f"Banko **≥%{limitler['banko_siniri']}** | Çifte **≥%{limitler['cifte_siniri']}** | "
                    f"Puan **{limitler['puan'][0]}-{limitler['puan'][1]}** | "
                    f"Sürpriz Sayısı **{limitler['surpriz'][0]}-{limitler['surpriz'][1]}**"
                )
            else:
                limitler = {
                    "1": range_1, "X": range_x, "2": range_2, "puan": range_puan,
                    "surpriz": range_surpriz,
                    "ardisik_1": max_ardisik_1, "ardisik_x": max_ardisik_x, "ardisik_2": max_ardisik_2,
                    "banko_siniri": banko_siniri, "cifte_siniri": cifte_sans_siniri,
                    "aktif_blok_filtresi": aktif_blok_filtresi, "max_blok_tekrar": max_blok_tekrar
                }

            varsayilan_sablon = varsayilan_sablon_olustur(veriler, limitler)

            st.markdown("### 🛠️ Canlı Şablon ve Oran Editörü")
            df_baslangic = pd.DataFrame([
                {
                    "No": idx + 1,
                    "Maç": v["mac"],
                    "1 (%)": v["1"],
                    "X (%)": v["X"],
                    "2 (%)": v["2"],
                    "Seçim 1": "1" in s,
                    "Seçim X": "X" in s,
                    "Seçim 2": "2" in s,
                }
                for idx, (v, s) in enumerate(zip(veriler, varsayilan_sablon))
            ])

            duzenlenen_df = st.data_editor(
                df_baslangic,
                disabled=["No", "Maç", "1 (%)", "X (%)", "2 (%)"],
                hide_index=True,
                use_container_width=True
            )

            guncel_sablon = []
            bos_mac_var = False
            for _, row in duzenlenen_df.iterrows():
                secimler = []
                if row["Seçim 1"]: secimler.append("1")
                if row["Seçim X"]: secimler.append("X")
                if row["Seçim 2"]: secimler.append("2")
                if not secimler:
                    bos_mac_var = True
                guncel_sablon.append(secimler)

            if bos_mac_var:
                st.error("⚠️ Her maçta en az 1 tercih (1, X veya 2) seçili olmalıdır.")
            else:
                toplam_kombinasyon = math.prod(len(s) for s in guncel_sablon)
                
                if toplam_kombinasyon > 4_782_969:
                    st.error(f"Şablon çok geniş ({toplam_kombinasyon:,} kolon). Lütfen 1-2 maçı Çifte Şans veya Banko'ya indirin.")
                else:
                    t0 = time.perf_counter()
                    filtrelenmis_matris, filtrelenmis_puanlar = vektorel_filtrele(guncel_sablon, veriler, limitler)
                    gecen_sure = time.perf_counter() - t0

                    if len(filtrelenmis_matris) == 0:
                        st.warning("⚠️ Filtreler tüm kombinasyonları eledi. Farklı bir Oyun Stratejisi seçin veya şablonu genişletin.")
                    else:
                        garantili_matris, garantili_puanlar, kapsama_orani = garanti_ve_butce_uygula(
                            filtrelenmis_matris, filtrelenmis_puanlar, garanti_derecesi, max_kolon_limiti
                        )
                        
                        # Üretilen kuponları 2. sekmede anında kullanabilmek için hafızaya kaydet
                        st.session_state.uretilen_kuponlar = garantili_matris
                        
                        st.success(f"⚡ Optimizasyon **{gecen_sure:.2f} saniyede** tamamlandı! Kuponlarınız **Canlı Takip** sekmesine otomatik aktarıldı.")
                        
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Ham Şablon", f"{toplam_kombinasyon:,} Kolon")
                        m2.metric("Filtre Sonrası", f"{len(filtrelenmis_matris):,} Kolon")
                        m3.metric(
                            f"{garanti_derecesi} Garantili Çıktı", 
                            f"{len(garantili_matris):,} Kolon", 
                            f"{len(garantili_matris) * kolon_fiyati:,.0f} TL"
                        )
                        m4.metric("Kapsama Gücü", f"%{kapsama_orani:.1f}")

                        txt_cikti = "\n".join([" ".join(k) for k in garantili_matris])
                        csv_df = pd.DataFrame(garantili_matris, columns=[f"M{i}" for i in range(1, 16)])
                        csv_df["Olasılık Puanı"] = garantili_puanlar

                        dl1, dl2 = st.columns(2)
                        dl1.download_button(
                            "📥 Kuponları İndir (.TXT)",
                            txt_cikti,
                            f"spor_toto_v4_{garanti_derecesi}garanti.txt",
                            use_container_width=True
                        )
                        dl2.download_button(
                            "📊 Kuponları İndir (.CSV / Excel)",
                            csv_df.to_csv(index=False).encode("utf-8-sig"),
                            f"spor_toto_v4_{garanti_derecesi}garanti.csv",
                            mime="text/csv",
                            use_container_width=True
                        )


# ------------------------------------------------------------------------------
# SEKME 2: CANLI KUPON VE İKRAMİYE TAKİP MERKEZİ
# ------------------------------------------------------------------------------
with tab_takip:
    st.markdown("### 📡 Canlı Kupon ve İkramiye Potası Takibi")
    
    t_col1, t_col2 = st.columns([1.1, 2])
    
    with t_col1:
        st.markdown("#### 1️⃣ Kupon Kaynağı Seçin")
        kaynak_secimi = st.radio(
            "Takip edilecek kuponlar:",
            ["📂 Bilgisayardan Kupon Dosyası Yükle (.txt / .csv)", "⚡ Bu Oturumda Üretilen Kuponları Kullan"],
            index=1 if st.session_state.uretilen_kuponlar is not None else 0
        )
        
        aktif_kupon_matrisi = None
        if "Dosya Yükle" in kaynak_secimi:
            yuklenen = st.file_uploader("İndirdiğiniz .txt veya .csv kupon dosyasını sürükleyin:", type=["txt", "csv"])
            if yuklenen:
                aktif_kupon_matrisi = kupon_dosyasi_coz(yuklenen)
                if aktif_kupon_matrisi is not None:
                    st.success(f"✅ Dosyadan **{len(aktif_kupon_matrisi):,} adet** geçerli kupon yüklendi.")
                else:
                    st.error("Dosya formatı okunamadı. Her satırda 15 adet (1, X, 2) sonucu bulunduğundan emin olun.")
        else:
            if st.session_state.uretilen_kuponlar is not None:
                aktif_kupon_matrisi = st.session_state.uretilen_kuponlar
                st.success(f"✅ Hafızadaki **{len(aktif_kupon_matrisi):,} adet** kupon takip ediliyor.")
            else:
                st.warning("Henüz bu oturumda kupon üretmediniz. 1. Sekmeden kupon üretin veya dosya yükleme seçeneğini kullanın.")

        st.markdown("---")
        st.markdown("#### 2️⃣ Canlı / Biten Maç Sonuçları")
        
        # API ile Otomatik Skor Güncelleme Butonu
        if api_key and len(st.session_state.secilen_mac_idleri) == 15:
            if st.button("🔄 Canlı Skorları API'den Otomatik Çek", type="primary", use_container_width=True):
                with st.spinner("15 maçın canlı skorları çekiliyor..."):
                    yeni_son, yeni_skor = canli_skorlari_cek(st.session_state.secilen_mac_idleri, api_key)
                    st.session_state.canli_sonuclar = yeni_son
                    st.session_state.canli_skor_metni = yeni_skor

        # Maç İsimlerini Belirle
        if st.session_state.analiz_verisi:
            mac_isimleri = [v["mac"] for v in st.session_state.analiz_verisi]
        else:
            mac_isimleri = [f"{i}. Maç" for i in range(1, 16)]

        # Manuel / Canlı Düzenlenebilir Maç Sonuç Tablosu
        takip_df_baslangic = pd.DataFrame({
            "No": list(range(1, 16)),
            "Karşılaşma": mac_isimleri,
            "Skor": st.session_state.canli_skor_metni,
            "Sonuç": st.session_state.canli_sonuclar
        })

        duzenlenen_sonuc_df = st.data_editor(
            takip_df_baslangic,
            column_config={
                "Sonuç": st.column_config.SelectboxColumn(
                    "Maç Sonucu",
                    help="Maç devam ediyorsa veya bittiyse sonucu (1, X, 2) seçin.",
                    options=["⏳ Bekliyor", "1", "X", "2"],
                    required=True
                )
            },
            disabled=["No", "Karşılaşma", "Skor"],
            hide_index=True,
            use_container_width=True,
            height=565
        )
        guncel_sonuclar = duzenlenen_sonuc_df["Sonuç"].tolist()

    # --- SAĞ PANEL: VEKTÖREL CANLI PERFORMANS ANALİZİ ---
    with t_col2:
        if aktif_kupon_matrisi is not None and len(aktif_kupon_matrisi) > 0:
            sonuc_dizisi = np.array(guncel_sonuclar)
            oynanan_maske = np.isin(sonuc_dizisi, ["1", "X", "2"])
            oynanan_mac_sayisi = int(np.sum(oynanan_maske))
            kalan_mac_sayisi = 15 - oynanan_mac_sayisi

            if oynanan_mac_sayisi == 0:
                st.info("👈 Sol tablodan tamamlanan veya devam eden maçların sonuçlarını (**1, X, 2**) seçtiğiniz anda kuponlarınızın ikramiye durumu burada canlı hesaplanacaktır.")
            else:
                # Vektörel Doğru / Hata / Maksimum Hedef Hesabı
                dogru_matrisi = (aktif_kupon_matrisi[:, oynanan_maske] == sonuc_dizisi[oynanan_maske])
                dogru_sayilari = np.sum(dogru_matrisi, axis=1)
                hata_sayilari = oynanan_mac_sayisi - dogru_sayilari
                maks_ulasilabilir = 15 - hata_sayilari  # Kuponun ulaşabileceği en yüksek ikramiye basamağı

                giden_15 = int(np.sum(maks_ulasilabilir == 15))
                giden_14 = int(np.sum(maks_ulasilabilir == 14))
                giden_13 = int(np.sum(maks_ulasilabilir == 13))
                giden_12 = int(np.sum(maks_ulasilabilir == 12))
                elenenler = int(np.sum(maks_ulasilabilir < 12))

                st.markdown(f"#### 🏆 Canlı İkramiye Potası ({oynanan_mac_sayisi} / 15 Maç Girildi)")
                
                k1, k2, k3, k4, k5 = st.columns(5)
                k1.metric("🥇 15'e Giden", f"{giden_15:,} Kupon", delta="Tam İsabet" if giden_15 > 0 else None)
                k2.metric("🥈 14'e Giden", f"{giden_14:,} Kupon")
                k3.metric("🥉 13'e Giden", f"{giden_13:,} Kupon")
                k4.metric("🎯 12'ye Giden", f"{giden_12:,} Kupon")
                k5.metric("❌ İkramiye Dışı", f"{elenenler:,} Kupon")

                # Kalan Maçlar İçin "Ne Lazım?" Kırılım Analizi
                if kalan_mac_sayisi > 0:
                    st.markdown("#### 🔮 Kalan Maçlarda Kuponlarınız Ne Bekliyor?")
                    hedef_filtre = st.selectbox(
                        "Hangi potadaki kuponların kalan maç analizini görmek istiyorsunuz?",
                        ["En Yüksek Potadaki Kuponlar (Önerilen)", "15'e Gidenler", "14 ve Üzeri Gidenler", "İkramiye Potasındakiler (12+ Gidenler)"]
                    )
                    
                    if hedef_filtre == "15'e Gidenler":
                        analiz_maske = (maks_ulasilabilir == 15)
                    elif hedef_filtre == "14 ve Üzeri Gidenler":
                        analiz_maske = (maks_ulasilabilir >= 14)
                    elif "12+" in hedef_filtre:
                        analiz_maske = (maks_ulasilabilir >= 12)
                    else:
                        en_iyi_derece = int(np.max(maks_ulasilabilir))
                        analiz_maske = (maks_ulasilabilir == en_iyi_derece)

                    canli_kuponlar = aktif_kupon_matrisi[analiz_maske]
                    
                    if len(canli_kuponlar) > 0:
                        beklenti_listesi = []
                        for m_idx in np.where(~oynanan_maske)[0]:
                            m_sutun = canli_kuponlar[:, m_idx]
                            n_1 = int(np.sum(m_sutun == '1'))
                            n_x = int(np.sum(m_sutun == 'X'))
                            n_2 = int(np.sum(m_sutun == '2'))
                            toplam_k = len(canli_kuponlar)
                            beklenti_listesi.append({
                                "Maç No": m_idx + 1,
                                "Kalan Karşılaşma": mac_isimleri[m_idx],
                                "1 Bekleyen": f"{n_1} (%{n_1*100/toplam_k:.0f})",
                                "X Bekleyen": f"{n_x} (%{n_x*100/toplam_k:.0f})",
                                "2 Bekleyen": f"{n_2} (%{n_2*100/toplam_k:.0f})"
                            })
                        st.dataframe(pd.DataFrame(beklenti_listesi), hide_index=True, use_container_width=True)
                    else:
                        st.warning("Seçilen potada devam eden kupon bulunmuyor.")

                # Detaylı Kupon Sıralama Tablosu
                st.markdown("#### 📋 Kuponların Canlı Performans Sıralaması")
                sirali_indeksler = np.argsort(maks_ulasilabilir)[::-1]
                gosterim_limiti = min(500, len(sirali_indeksler))
                
                detay_satirlar = []
                for s_idx in sirali_indeksler[:gosterim_limiti]:
                    hedef_derece = int(maks_ulasilabilir[s_idx])
                    durum_etiketi = f"🏆 {hedef_derece} Adayı" if hedef_derece >= 12 else "❌ Elendi"
                    satir_sozluk = {
                        "Kupon No": f"#{s_idx + 1}",
                        "Durum": durum_etiketi,
                        "Doğru": int(dogru_sayilari[s_idx]),
                        "Hata": int(hata_sayilari[s_idx]),
                        "Kalan": kalan_mac_sayisi,
                        "Kupon Dizilimi": " ".join(aktif_kupon_matrisi[s_idx])
                    }
                    detay_satirlar.append(satir_sozluk)

                st.dataframe(pd.DataFrame(detay_satirlar), hide_index=True, use_container_width=True)
                if len(sirali_indeksler) > 500:
                    st.caption(f"Performansı en yüksek ilk 500 kupon listelenmektedir (Toplam: {len(sirali_indeksler):,} kupon).")
        else:
            st.info("👈 Takip ekranını başlatmak için sol taraftan kupon dosyanızı yükleyin veya 1. Sekmeden kupon üretin.")
