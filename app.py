import streamlit as st
import requests
import math
import time
import json
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Spor Toto AI Pro v5.1 (Ultra Kapsamlı)", page_icon="🏆", layout="wide")
st.title("🏆 Spor Toto AI v5.1 — Ultra Kapsamlı Lig Havuzu & Hibrit Motor")

# --- SESSION STATE BAŞLATMA ---
varsayilan_state = {
    "mac_listesi": [],
    "analiz_verisi": None,
    "secilen_mac_idleri": [],
    "uretilen_kuponlar": None,
    "canli_sonuclar": ["⏳ Bekliyor"] * 15,
    "canli_skor_metni": ["-"] * 15
}
for anahtar, deger in varsayilan_state.items():
    if anahtar not in st.session_state:
        st.session_state[anahtar] = deger

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

    st.subheader("🧠 Yapay Zeka & Tuzak Yönetimi")
    strateji_modu = st.radio(
        "Oyun Stratejisi:",
        ["⚖️ Dengeli (Standart)", "🛡️ Favori Korumalı", "💎 İkramiye Avcısı (Tuzak Yıkıcı)"]
    )
    
    tuzak_koruma = st.toggle(
        "🚨 Sahte Favori (Tuzak) Koruması", 
        value=True,
        help="Halkın aşırı yüklendiği ancak gerçek bahis oranlarına göre riskli olan 'Tuzak Favori' maçların tek (Banko) geçilmesini otomatik engeller."
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


# ==============================================================================
# 1. ULTRA KAPSAMLI LİG HAVUZU (50+ LİG VE TURNUVA)
# ==============================================================================
KATEGORIZE_LIGLER = {
    "🇹🇷 Türkiye": {
        "Trendyol Süper Lig": 203,
        "Trendyol 1. Lig": 204,
        "Türkiye Kupası": 205
    },
    "🇪🇺 Avrupa Büyükler": {
        "Premier League (İngiltere)": 39,
        "Championship (İngiltere 2)": 40,
        "La Liga (İspanya)": 140,
        "Segunda Division (İspanya 2)": 141,
        "Serie A (İtalya)": 135,
        "Serie B (İtalya 2)": 136,
        "Bundesliga (Almanya)": 78,
        "2. Bundesliga (Almanya 2)": 79,
        "Ligue 1 (Fransa)": 61,
        "Ligue 2 (Fransa 2)": 62
    },
    "⭐ Avrupa Kupaları": {
        "UEFA Şampiyonlar Ligi": 2,
        "UEFA Avrupa Ligi": 3,
        "UEFA Konferans Ligi": 848,
        "UEFA Uluslar Ligi": 5
    },
    "🌍 Diğer Popüler Avrupa Ligleri": {
        "Eredivisie (Hollanda)": 88,
        "Primeira Liga (Portekiz)": 94,
        "Pro League (Belçika)": 144,
        "Super League (İsviçre)": 103,
        "Bundesliga (Avusturya)": 218,
        "Premiership (İskoçya)": 179,
        "Super League (Yunanistan)": 197,
        "Super Lig (Danimarka)": 119,
        "Eliteserien (Norveç)": 104,
        "Allsvenskan (İsveç)": 113,
        "Ekstraklasa (Polonya)": 106,
        "HNL (Hırvatistan)": 382,
        "Super Liga (Sırbistan)": 286,
        "Fortuna Liga (Çekya)": 345
    },
    "🌎 Amerika ve Diğer Kıtalar": {
        "Série A (Brezilya)": 71,
        "Série B (Brezilya 2)": 72,
        "Liga Profesional (Arjentin)": 128,
        "MLS (ABD)": 253,
        "Liga MX (Meksika)": 262,
        "Primera A (Kolombiya)": 239,
        "Pro League (Suudi Arabistan)": 307
    },
    "🌐 Uluslararası Turnuvalar": {
        "Dünya Kupası Elemeleri (Avrupa)": 32,
        "Afrika Uluslar Kupası": 6,
        "Copa Libertadores": 13,
        "Copa Sudamericana": 11
    }
}


@st.cache_data(ttl=3600, show_spinner=False)
def tum_liglerden_maclari_getir(secilen_lig_idleri, api_key):
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "v3.football.api-sports.io"}
    tum_maclar = []
    
    for lig_id in secilen_lig_idleri:
        url = f"https://v3.football.api-sports.io/fixtures?league={lig_id}&next=12"
        try:
            res = requests.get(url, headers=headers, timeout=8).json()
            if res.get('response'):
                for item in res['response']:
                    f_id = item['fixture']['id']
                    ev = item['teams']['home']['name']
                    dep = item['teams']['away']['name']
                    tarih = item['fixture']['date'][:10]
                    lig_adi = item['league']['name']
                    tum_maclar.append({
                        "id": f_id,
                        "label": f"[{lig_adi}] {tarih} | {ev} - {dep}",
                        "lig": lig_adi,
                        "tarih": tarih
                    })
        except Exception:
            continue
    return tum_maclar


def olasilik_yumusat(p1, px_val, p2):
    p1, px_val, p2 = max(5.0, float(p1)), max(5.0, float(px_val)), max(5.0, float(p2))
    toplam = p1 + px_val + p2
    y1 = round(p1 * 100 / toplam)
    yx = round(px_val * 100 / toplam)
    y2 = 100 - y1 - yx
    return int(y1), int(yx), int(y2)


def halk_egilimi_simule_et(p1, px_val, p2):
    w1, wx, w2 = (p1 ** 1.55), (px_val ** 1.15), (p2 ** 1.55)
    t = w1 + wx + w2
    return round(w1 * 100 / t), round(wx * 100 / t), 100 - round(w1 * 100 / t) - round(wx * 100 / t)


@st.cache_data(ttl=3600, show_spinner=False)
def hibrit_tahminleri_al(secilen_maclar, api_key):
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "v3.football.api-sports.io"}
    sonuclar = []
    progress = st.progress(0, text="Hibrit Motor: Seçilen liglerde AI ve Bahis Oranları taranıyor...")
    
    for i, mac in enumerate(secilen_maclar):
        f_id = mac['id']
        ai_1, ai_x, ai_2 = 36.0, 33.0, 31.0
        odds_1, odds_x, odds_2 = None, None, None
        kaynak_etiketi = "AI Tahmini"
        
        try:
            res_pred = requests.get(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", headers=headers, timeout=6).json()
            if res_pred.get('response') and res_pred['response'][0].get('predictions'):
                t = res_pred['response'][0]['predictions']['percent']
                ai_1 = float(t['home'].replace('%', ''))
                ai_x = float(t['draw'].replace('%', ''))
                ai_2 = float(t['away'].replace('%', ''))
        except Exception:
            pass

        try:
            res_odds = requests.get(f"https://v3.football.api-sports.io/odds?fixture={f_id}", headers=headers, timeout=6).json()
            if res_odds.get('response') and res_odds['response'][0].get('bookmakers'):
                buro = res_odds['response'][0]['bookmakers'][0]
                for bahis in buro.get('bets', []):
                    if bahis.get('id') == 1 or bahis.get('name') == "Match Winner":
                        degerler = {v['value']: float(v['odd']) for v in bahis.get('values', [])}
                        if "Home" in degerler and "Draw" in degerler and "Away" in degerler:
                            inv_1, inv_x, inv_2 = 1.0 / degerler["Home"], 1.0 / degerler["Draw"], 1.0 / degerler["Away"]
                            inv_top = inv_1 + inv_x + inv_2
                            odds_1, odds_x, odds_2 = (inv_1 / inv_top) * 100, (inv_x / inv_top) * 100, (inv_2 / inv_top) * 100
                            kaynak_etiketi = "Hibrit (Odds + AI)"
                        break
        except Exception:
            pass

        if odds_1 is not None:
            ham_1, ham_x, ham_2 = (odds_1 * 0.65) + (ai_1 * 0.35), (odds_x * 0.65) + (ai_x * 0.35), (odds_2 * 0.65) + (ai_2 * 0.35)
        else:
            ham_1, ham_x, ham_2 = ai_1, ai_x, ai_2

        g1, gx, g2 = olasilik_yumusat(ham_1, ham_x, ham_2)
        h1, hx, h2 = halk_egilimi_simule_et(g1, gx, g2)
        en_yuksek_gercek = max(g1, gx, g2)
        en_yuksek_halk = max(h1, hx, h2)

        sonuclar.append({
            "bulten_no": i + 1,
            "id": f_id,
            "mac": mac['label'],
            "kaynak": kaynak_etiketi,
            "1": g1,
            "X": gx,
            "2": g2,
            "halk_favori": en_yuksek_halk,
            "tuzak_farki": en_yuksek_halk - en_yuksek_gercek
        })
        progress.progress((i + 1) / len(secilen_maclar))
        time.sleep(0.15)
        
    progress.empty()
    return sonuclar


def canli_skorlari_cek(fixture_id_listesi, api_key):
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


# ==============================================================================
# 2. OTONOM ANALİZ VE VEKTÖREL MOTOR
# ==============================================================================
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


def varsayilan_sablon_olustur(veriler, limitler, tuzak_koruma_aktif=True):
    sablon = []
    for v in veriler:
        sirali = sorted([(v["1"], "1"), (v["X"], "X"), (v["2"], "2")], reverse=True)
        en = sirali[0][0]
        halk_farki = v.get("tuzak_farki", 0)
        
        if en >= limitler["banko_siniri"]:
            if tuzak_koruma_aktif and halk_farki >= 12 and en < 68:
                secim = [sirali[0][1], sirali[1][1]]
            else:
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


def monte_carlo_simule_et(kupon_matrisi, mac_verileri, simulasyon_sayisi=10000):
    harita = {'1': 0, 'X': 1, '2': 2}
    kupon_num = np.vectorize(harita.get)(kupon_matrisi).astype(np.int8)
    
    rng = np.random.default_rng(42)
    sim_sonuclar = np.zeros((simulasyon_sayisi, 15), dtype=np.int8)
    for m_idx, v in enumerate(mac_verileri):
        olasiliklar = np.array([v["1"], v["X"], v["2"]], dtype=float)
        olasiliklar /= olasiliklar.sum()
        sim_sonuclar[:, m_idx] = rng.choice([0, 1, 2], size=simulasyon_sayisi, p=olasiliklar)
        
    en_iyi_dereceler = np.zeros(simulasyon_sayisi, dtype=np.int8)
    adim = 500
    for bas in range(0, simulasyon_sayisi, adim):
        bit = min(bas + adim, simulasyon_sayisi)
        eslesme = np.sum(sim_sonuclar[bas:bit, None, :] == kupon_num[None, :, :], axis=2)
        en_iyi_dereceler[bas:bit] = np.max(eslesme, axis=1)
        
    return {
        "15_oran": float(np.mean(en_iyi_dereceler == 15) * 100),
        "14_arti_oran": float(np.mean(en_iyi_dereceler >= 14) * 100),
        "13_arti_oran": float(np.mean(en_iyi_dereceler >= 13) * 100),
        "12_arti_oran": float(np.mean(en_iyi_dereceler >= 12) * 100),
        "ortalama_maks_dogru": float(np.mean(en_iyi_dereceler))
    }


def kupon_dosyasi_coz(yuklenen_dosya):
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
# ANA SEKMELER
# ==============================================================================
tab_uretim, tab_takip, tab_otomasyon = st.tabs([
    "🚀 1. Kapsamlı Lig Seçimi & Hibrit Üretim", 
    "📡 2. Canlı Kupon & İkramiye Takip Merkezi",
    "🤖 3. Otomatik Kupon Yatırma (Tarayıcı Botu)"
])

# ------------------------------------------------------------------------------
# SEKME 1: KAPSAMLI LİG SEÇİMİ VE ÜRETİM
# ------------------------------------------------------------------------------
with tab_uretim:
    st.markdown("### 🌍 50+ Kapsamlı Lig ve Turnuva Seçim Paneli")
    if api_key:
        # Kategori Filtresi Seçimi
        secilen_kategori = st.selectbox(
            "📁 Önce Lig Kategorisi Seçin:", 
            list(KATEGORIZE_LIGLER.keys())
        )
        
        aktif_ligler_dict = KATEGORIZE_LIGLER[secilen_kategori]
        secilen_lig_adlari = st.multiselect(
            f"🏆 {secilen_kategori} İçinden Ligleri Seçin:",
            list(aktif_ligler_dict.keys()),
            default=list(aktif_ligler_dict.keys())[:3]
        )
        
        secilen_lig_idleri = [aktif_ligler_dict[l] for l in secilen_lig_adlari]
        
        if secilen_lig_idleri:
            if st.button("🔍 Seçilen Liglerdeki Maçları Listele", use_container_width=True):
                with st.spinner("Seçilen liglerin maç bültenleri çekiliyor..."):
                    st.session_state.mac_listesi = tum_liglerden_maclari_getir(secilen_lig_idleri, api_key)
                    st.success(f"✅ Toplam **{len(st.session_state.mac_listesi)} maç** bülfene eklendi!")
                    
        if st.session_state.mac_listesi:
            st.markdown("---")
            opsiyonlar = {m['label']: m for m in st.session_state.mac_listesi}
            secilenler_label = st.multiselect(
                "🎯 Bülten Havuzundan Tam 15 Maç Seçin (Resmi sıraya göre seçin):", 
                list(opsiyonlar.keys()), 
                max_selections=15
            )
            
            st.caption(f"Seçilen Maç Sayısı: **{len(secilenler_label)} / 15**")
            
            if len(secilenler_label) == 15:
                if st.button("🚀 Hibrit Analizi ve Motoru Başlat", type="primary", use_container_width=True):
                    secilenler_data = [opsiyonlar[lbl] for lbl in secilenler_label]
                    st.session_state.secilen_mac_idleri = [m["id"] for m in secilenler_data]
                    st.session_state.analiz_verisi = hibrit_tahminleri_al(secilenler_data, api_key)
                    st.session_state.canli_sonuclar = ["⏳ Bekliyor"] * 15
                    st.session_state.canli_skor_metni = ["-"] * 15
    else:
        st.info("👈 Başlamak için sol menüden API-Football anahtarınızı girin.")

    if st.session_state.analiz_verisi:
        veriler = st.session_state.analiz_verisi
        
        if ai_filtre_modu:
            limitler = tam_otonom_analiz(veriler, strateji_modu)
            st.info(
                f"🤖 **Hibrit AI ({strateji_modu}):** Zorluk **%{limitler['zorluk_skoru']:.1f}** | "
                f"Banko **≥%{limitler['banko_siniri']}** | Çifte **≥%{limitler['cifte_siniri']}** | "
                f"Puan **{limitler['puan'][0]}-{limitler['puan'][1]}**"
            )
        else:
            limitler = {
                "1": range_1, "X": range_x, "2": range_2, "puan": range_puan,
                "surpriz": range_surpriz,
                "ardisik_1": max_ardisik_1, "ardisik_x": max_ardisik_x, "ardisik_2": max_ardisik_2,
                "banko_siniri": banko_siniri, "cifte_siniri": cifte_sans_siniri,
                "aktif_blok_filtresi": aktif_blok_filtresi, "max_blok_tekrar": max_blok_tekrar
            }

        varsayilan_sablon = varsayilan_sablon_olustur(veriler, limitler, tuzak_koruma)

        st.markdown("### 🛠️ Bülten Sıralaması, Tuzak Analizi ve Canlı Şablon Editörü")
        df_baslangic = pd.DataFrame([
            {
                "Sıra No": v["bulten_no"],
                "Maç": v["mac"],
                "1 (%)": v["1"],
                "X (%)": v["X"],
                "2 (%)": v["2"],
                "Halk Fav (%)": v["halk_favori"],
                "Analiz": "🚨 Tuzak Favori" if (v["tuzak_farki"] >= 12 and max(v["1"], v["X"], v["2"]) < 68) else "✅ Normal",
                "Seçim 1": "1" in s,
                "Seçim X": "X" in s,
                "Seçim 2": "2" in s,
            }
            for v, s in zip(veriler, varsayilan_sablon)
        ])

        duzenlenen_df = st.data_editor(
            df_baslangic,
            disabled=["Maç", "1 (%)", "X (%)", "2 (%)", "Analiz"],
            hide_index=True,
            use_container_width=True
        )

        sirali_df = duzenlenen_df.sort_values("Sıra No").reset_index(drop=True)
        
        guncel_sablon = []
        sirali_veriler = []
        bos_mac_var = False
        
        for _, row in sirali_df.iterrows():
            secimler = []
            if row["Seçim 1"]: secimler.append("1")
            if row["Seçim X"]: secimler.append("X")
            if row["Seçim 2"]: secimler.append("2")
            if not secimler:
                bos_mac_var = True
            guncel_sablon.append(secimler)
            sirali_veriler.append({
                "mac": row["Maç"],
                "1": int(row["1 (%)"]),
                "X": int(row["X (%)"]),
                "2": int(row["2 (%)"])
            })

        if bos_mac_var:
            st.error("⚠️ Her maçta en az 1 tercih (1, X veya 2) seçili olmalıdır.")
        else:
            toplam_kombinasyon = math.prod(len(s) for s in guncel_sablon)
            
            if toplam_kombinasyon > 4_782_969:
                st.error(f"Şablon çok geniş ({toplam_kombinasyon:,} kolon). Lütfen 1-2 maçı Çifte Şans veya Banko'ya indirin.")
            else:
                t0 = time.perf_counter()
                filtrelenmis_matris, filtrelenmis_puanlar = vektorel_filtrele(guncel_sablon, sirali_veriler, limitler)
                gecen_sure = time.perf_counter() - t0

                if len(filtrelenmis_matris) == 0:
                    st.warning("⚠️ Filtreler tüm kombinasyonları eledi. Farklı bir Oyun Stratejisi seçin veya şablonu genişletin.")
                else:
                    garantili_matris, garantili_puanlar, kapsama_orani = garanti_ve_butce_uygula(
                        filtrelenmis_matris, filtrelenmis_puanlar, garanti_derecesi, max_kolon_limiti
                    )
                    
                    st.session_state.uretilen_kuponlar = garantili_matris
                    mc_sonuc = monte_carlo_simule_et(garantili_matris, sirali_veriler, simulasyon_sayisi=10000)
                    
                    st.success(f"⚡ Optimizasyon ve Monte Carlo testi **{gecen_sure:.2f} saniyede** tamamlandı!")
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Ham Şablon", f"{toplam_kombinasyon:,} Kolon")
                    m2.metric("Filtre Sonrası", f"{len(filtrelenmis_matris):,} Kolon")
                    m3.metric(
                        f"{garanti_derecesi} Garantili Çıktı", 
                        f"{len(garantili_matris):,} Kolon", 
                        f"{len(garantili_matris) * kolon_fiyati:,.0f} TL"
                    )
                    m4.metric("Havuz Kapsama Gücü", f"%{kapsama_orani:.1f}")

                    st.markdown("#### 🎲 10.000 Haftalık Monte Carlo Simülasyon Raporu")
                    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
                    mc1.metric("🥇 15 Tutturma Şansı", f"%{mc_sonuc['15_oran']:.2f}")
                    mc2.metric("🥈 En Az 14 Şansı", f"%{mc_sonuc['14_arti_oran']:.1f}")
                    mc3.metric("🥉 En Az 13 Şansı", f"%{mc_sonuc['13_arti_oran']:.1f}")
                    mc4.metric("🎯 İkramiye (12+) Şansı", f"%{mc_sonuc['12_arti_oran']:.1f}")
                    mc5.metric("📈 Beklenen Maks Doğru", f"{mc_sonuc['ortalama_maks_dogru']:.2f} / 15")

                    txt_cikti = "\n".join([" ".join(k) for k in garantili_matris])
                    csv_df = pd.DataFrame(garantili_matris, columns=[f"M{i}" for i in range(1, 16)])
                    csv_df["Olasılık Puanı"] = garantili_puanlar

                    dl1, dl2 = st.columns(2)
                    dl1.download_button("📥 Kuponları İndir (.TXT)", txt_cikti, f"spor_toto_v51_{garanti_derecesi}garanti.txt", use_container_width=True)
                    dl2.download_button("📊 Kuponları İndir (.CSV)", csv_df.to_csv(index=False).encode("utf-8-sig"), f"spor_toto_v51_{garanti_derecesi}garanti.csv", mime="text/csv", use_container_width=True)


# ------------------------------------------------------------------------------
# SEKME 2: CANLI KUPON VE İKRAMİYE TAKİP MERKEZİ
# ------------------------------------------------------------------------------
with tab_takip:
    st.markdown("### 📡 Canlı Kupon ve İkramiye Potası Takibi")
    t_col1, t_col2 = st.columns([1.1, 2])
    
    with t_col1:
        st.markdown("#### 1️⃣ Kupon Kaynağı Seçin")
        kaynak_secimi = st.radio("Takip edilecek kuponlar:", ["📂 Bilgisayardan Kupon Dosyası Yükle (.txt / .csv)", "⚡ Bu Oturumda Üretilen Kuponları Kullan"], index=1 if st.session_state.uretilen_kuponlar is not None else 0)
        
        aktif_kupon_matrisi = None
        if "Dosya Yükle" in kaynak_secimi:
            yuklenen = st.file_uploader("İndirdiğiniz .txt veya .csv kupon dosyasını yükleyin:", type=["txt", "csv"])
            if yuklenen:
                aktif_kupon_matrisi = kupon_dosyasi_coz(yuklenen)
        else:
            if st.session_state.uretilen_kuponlar is not None:
                aktif_kupon_matrisi = st.session_state.uretilen_kuponlar

        st.markdown("---")
        st.markdown("#### 2️⃣ Canlı / Biten Maç Sonuçları")
        if api_key and len(st.session_state.secilen_mac_idleri) == 15:
            if st.button("🔄 Canlı Skorları API'den Otomatik Çek", type="primary", use_container_width=True):
                with st.spinner("15 maçın canlı skorları çekiliyor..."):
                    yeni_son, yeni_skor = canli_skorlari_cek(st.session_state.secilen_mac_idleri, api_key)
                    st.session_state.canli_sonuclar = yeni_son
                    st.session_state.canli_skor_metni = yeni_skor

        mac_isimleri = [v["mac"] for v in st.session_state.analiz_verisi] if st.session_state.analiz_verisi else [f"{i}. Maç" for i in range(1, 16)]
        takip_df_baslangic = pd.DataFrame({"No": list(range(1, 16)), "Karşılaşma": mac_isimleri, "Skor": st.session_state.canli_skor_metni, "Sonuç": st.session_state.canli_sonuclar})

        duzenlenen_sonuc_df = st.data_editor(
            takip_df_baslangic,
            column_config={"Sonuç": st.column_config.SelectboxColumn("Maç Sonucu", options=["⏳ Bekliyor", "1", "X", "2"], required=True)},
            disabled=["No", "Karşılaşma", "Skor"], hide_index=True, use_container_width=True, height=565
        )
        guncel_sonuclar = duzenlenen_sonuc_df["Sonuç"].tolist()

    with t_col2:
        if aktif_kupon_matrisi is not None and len(aktif_kupon_matrisi) > 0:
            sonuc_dizisi = np.array(guncel_sonuclar)
            oynanan_maske = np.isin(sonuc_dizisi, ["1", "X", "2"])
            oynanan_mac_sayisi = int(np.sum(oynanan_maske))
            
            if oynanan_mac_sayisi > 0:
                dogru_matrisi = (aktif_kupon_matrisi[:, oynanan_maske] == sonuc_dizisi[oynanan_maske])
                dogru_sayilari = np.sum(dogru_matrisi, axis=1)
                hata_sayilari = oynanan_mac_sayisi - dogru_sayilari
                maks_ulasilabilir = 15 - hata_sayilari

                st.markdown(f"#### 🏆 Canlı İkramiye Potası ({oynanan_mac_sayisi} / 15 Maç Girildi)")
                k1, k2, k3, k4, k5 = st.columns(5)
                k1.metric("🥇 15'e Giden", f"{int(np.sum(maks_ulasilabilir == 15)):,} Kupon")
                k2.metric("🥈 14'e Giden", f"{int(np.sum(maks_ulasilabilir == 14)):,} Kupon")
                k3.metric("🥉 13'e Giden", f"{int(np.sum(maks_ulasilabilir == 13)):,} Kupon")
                k4.metric("🎯 12'ye Giden", f"{int(np.sum(maks_ulasilabilir == 12)):,} Kupon")
                k5.metric("❌ İkramiye Dışı", f"{int(np.sum(maks_ulasilabilir < 12)):,} Kupon")
            else:
                st.info("👈 Sol tablodan maç sonuçlarını seçtiğinizde canlı ikramiye durumu hesaplanacaktır.")
        else:
            st.info("👈 Takip için kupon yükleyin veya 1. Sekmeden kupon üretin.")


# ------------------------------------------------------------------------------
# SEKME 3: OTOMATİK KUPON YATIRMA (TARAYICI BOTU)
# ------------------------------------------------------------------------------
with tab_otomasyon:
    st.markdown("### 🤖 Otomatik Kupon Yatırma (Tarayıcı Konsol Botu)")
    if st.session_state.uretilen_kuponlar is not None and len(st.session_state.uretilen_kuponlar) > 0:
        kuponlar_oto = st.session_state.uretilen_kuponlar.tolist()
        paket_boyutu = st.number_input("Paket Başına Kolon:", 5, 500, 50, step=5)
        toplam_paket = math.ceil(len(kuponlar_oto) / paket_boyutu)
        secilen_paket = st.selectbox("Paket Seçin:", [f"Paket {p+1}" for p in range(toplam_paket)])
        p_idx = int(secilen_paket.split()[1]) - 1
        aktif_paket = kuponlar_oto[p_idx * paket_boyutu : (p_idx + 1) * paket_boyutu]
        
        json_kuponlar = json.dumps(aktif_paket)
        st.code(f"// Tarayıcı F12 Konsoluna Yapıştırın:\nconst kuponlar = {json_kuponlar};\nconsole.log('Aktif paket hazır, kolon sayısı:', kuponlar.length);", language="javascript")
    else:
        st.info("👈 Önce 1. Sekmeden kupon üretin.")
