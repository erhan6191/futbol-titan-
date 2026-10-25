import streamlit as st
import requests
import math
import time
import json
import re
import unicodedata
from difflib import SequenceMatcher
from datetime import datetime, timedelta
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import pandas as pd

st.set_page_config(page_title="Spor Toto AI Pro v8.0", page_icon="🏆", layout="wide")

# --- KOMPAKT VE MODERN ARAYÜZ CSS ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 2.2rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }
        div[data-testid="stMetric"] {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 8px 12px;
            border-radius: 8px;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.25rem !important;
            font-weight: 700 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE BAŞLATMA ---
varsayilan_state = {
    "mac_listesi": [],
    "secilen_15_mac": [],
    "analiz_verisi": None,
    "secilen_mac_idleri": [],
    "uretilen_kuponlar": None,
    "canli_sonuclar": ["⏳ Bekliyor"] * 15,
    "canli_skor_metni": ["-"] * 15
}
for anahtar, deger in varsayilan_state.items():
    if anahtar not in st.session_state:
        st.session_state[anahtar] = deger

# --- SOL MENÜ ---
with st.sidebar:
    st.markdown("## 🏆 Spor Toto AI v8.0")
    api_key = st.text_input("🔑 API-Football Anahtarı:", type="password")

    st.markdown("---")
    st.markdown("### 🎯 1. Garanti ve Bütçe")
    garanti_secimi = st.selectbox(
        "Garanti Hedefi:",
        ["15 Garanti (Tam Kombinasyon)", "14 Garanti (1 Hata Payı)",
         "13 Garanti (2 Hata Payı)", "12 Garanti (3 Hata Payı)"],
        index=1
    )
    garanti_derecesi = int(garanti_secimi.split()[0])
    kolon_fiyati = st.number_input("Kolon Birim Fiyatı (TL):", min_value=1.0, value=10.0, step=1.0)

    butce_aktif = st.toggle("💰 Maksimum Kolon Sınırı Koy", value=False)
    if butce_aktif:
        max_kolon_limiti = st.number_input("Maksimum Kolon:", min_value=1, max_value=50000, value=100, step=10)
        st.caption(f"Maksimum Tutar: **{max_kolon_limiti * kolon_fiyati:,.0f} TL**")
    else:
        max_kolon_limiti = None

    st.markdown("---")
    st.markdown("### ✂️ 2. İleri Seviye Kupon Eleme")
    akilli_merkez = st.toggle("🧠 Maksimum Kapsama Optimizasyonu", value=True)
    entropi_filtresi = st.toggle("🌀 Simetrik/Yapay Dizilim Elemesi", value=True)
    benzerlik_elemesi = st.select_slider(
        "🔍 Kuponlar Arası Min. Farklı Maç:",
        options=[1, 2, 3, 4],
        value=1
    )

    st.markdown("---")
    st.markdown("### 🧠 3. Oyun Stratejisi")
    strateji_modu = st.radio(
        "Yapay Zeka Modu:",
        ["⚖️ Dengeli (Önerilen)", "🛡️ Favori Ağırlıklı", "💎 İkramiye Avcısı (Sürpriz)"]
    )
    tuzak_koruma = st.toggle("🚨 Tuzak Favorileri Yık (Çifteye Çevir)", value=True)
    ai_filtre_modu = st.toggle("🤖 Otonom Filtre", value=True)

    if not ai_filtre_modu:
        with st.expander("⚙️ Manuel Filtre Ayarları"):
            range_1 = st.slider("Ev Sahibi (1)", 0, 15, (4, 9))
            range_x = st.slider("Beraberlik (X)", 0, 15, (1, 5))
            range_2 = st.slider("Deplasman (2)", 0, 15, (2, 7))
            range_puan = st.slider("Puan Aralığı", 300, 1200, (520, 920))
            range_surpriz = st.slider("Sürpriz Sayısı (<%30)", 0, 10, (0, 5))
            max_ardisik_1 = st.slider("Üst Üste '1'", 2, 10, 5)
            max_ardisik_x = st.slider("Üst Üste 'X'", 2, 10, 3)
            max_ardisik_2 = st.slider("Üst Üste '2'", 2, 10, 4)
            banko_siniri = st.number_input("Banko Sınırı (%)", 35, 95, 60)
            cifte_sans_siniri = st.number_input("Çifte Şans Sınırı (%)", 30, 80, 42)
            aktif_blok_filtresi = st.toggle("3'lü Blok Filtresi", value=True)
            max_blok_tekrar = st.slider("3'lü Blok Maks Tekrar", 1, 3, 2)


# ==============================================================================
# LİG HAVUZU VE AKILLI METİN EŞLEŞTİRME MOTORU
# ==============================================================================
# Tek tıkla çekilecek Spor Toto standart ligleri (Süper Lig + Avrupa Ana Ligler)
STANDART_TOTO_LIGLERI = [203, 204, 39, 140, 135, 78, 61, 88, 94, 144, 2, 3, 848]

KATEGORIZE_LIGLER = {
    "🇹🇷 Türkiye": {"Trendyol Süper Lig": 203, "Trendyol 1. Lig": 204, "Türkiye Kupası": 205},
    "🇪🇺 Avrupa Büyükler": {
        "Premier League (İngiltere)": 39, "Championship (İngiltere 2)": 40,
        "La Liga (İspanya)": 140, "Serie A (İtalya)": 135,
        "Bundesliga (Almanya)": 78, "Ligue 1 (Fransa)": 61
    },
    "⭐ Avrupa Kupaları": {
        "UEFA Şampiyonlar Ligi": 2, "UEFA Avrupa Ligi": 3,
        "UEFA Konferans Ligi": 848, "UEFA Uluslar Ligi": 5
    },
    "🌍 Diğer Avrupa": {
        "Eredivisie (Hollanda)": 88, "Primeira Liga (Portekiz)": 94,
        "Pro League (Belçika)": 144, "Super League (İsviçre)": 103,
        "Bundesliga (Avusturya)": 218, "Premiership (İskoçya)": 179,
        "Super League (Yunanistan)": 197, "Super Lig (Danimarka)": 119,
        "Ekstraklasa (Polonya)": 106, "Super Liga (Sırbistan)": 286
    },
    "🌎 Amerika & Diğer": {
        "Série A (Brezilya)": 71, "Liga Profesional (Arjentin)": 128,
        "MLS (ABD)": 253, "Pro League (Suudi Arabistan)": 307
    }
}


def metin_temizle(s):
    """Türkçe karakterleri, kulüp eklerini (FK, SK, AS, FC) temizleyerek saf takım adını bırakır."""
    tr_harita = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    s = s.translate(tr_harita).lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf-8")
    # Kısaltmaları genişlet
    kisaltmalar = {
        "f.bahce": "fenerbahce", "g.saray": "galatasaray", "b.sehir": "basaksehir",
        "karagumruk": "fatih karagumruk", "m.united": "manchester united",
        "m.city": "manchester city", "b.munchen": "bayern munich", "b.dortmund": "borussia dortmund"
    }
    for k, u in kisaltmalar.items():
        s = s.replace(k, u)
    s = re.sub(r"\b(fk|sk|as|fc|ac|sc|cf|cd|ud|rc|rcd|sv|vfb|vfl|tsg|1899|1907|spor|belediyespor|united|city|club)\b", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return " ".join(s.split())


def bulten_metni_eslestir(yapistirilan_metin, havuz_maclari):
    """
    Kullanıcının bahis sitesinden kopyalayıp yapıştırdığı metni satır satır okur
    ve havuzdaki en uygun maçlarla (1'den 15'e sırayla) otomatik eşleştirir.
    """
    satirlar = [s.strip() for s in yapistirilan_metin.splitlines() if len(s.strip()) > 4]
    eslesen_maclar = []
    kullanilan_idler = set()

    for satir in satirlar:
        # Satır başındaki sıra numaralarını (1., 1-, 01 vb.) ve oranları temizle
        temiz_satir = re.sub(r"^\d+[\.\-\)\s]+", "", satir)
        temiz_satir = Metin_Adayi = metin_temizle(temiz_satir)
        if len(Metin_Adayi) < 4:
            continue

        en_iyi_skor = 0.0
        en_iyi_mac = None

        for m in havuz_maclari:
            if m["id"] in kullanilan_idler:
                continue
            ev_temiz = metin_temizle(m["ev"])
            dep_temiz = metin_temizle(m["dep"])
            mac_birlesik = f"{ev_temiz} {dep_temiz}"

            # Genel benzerlik + Ev/Deplasman kelime kapsama skoru
            skor_genel = SequenceMatcher(None, Metin_Adayi, mac_birlesik).ratio()
            ev_var = 0.25 if (ev_temiz and ev_temiz.split()[0] in Metin_Adayi) else 0.0
            dep_var = 0.25 if (dep_temiz and dep_temiz.split()[0] in Metin_Adayi) else 0.0
            toplam_skor = skor_genel + ev_var + dep_var

            if toplam_skor > en_iyi_skor:
                en_iyi_skor = toplam_skor
                en_iyi_mac = m

        if en_iyi_mac and en_iyi_skor >= 0.48:
            eslesen_maclar.append(en_iyi_mac)
            kullanilan_idler.add(en_iyi_mac["id"])
            if len(eslesen_maclar) == 15:
                break

    return eslesen_maclar


@st.cache_data(ttl=3600, show_spinner=False)
def tum_liglerden_maclari_getir(secilen_lig_idleri, api_key, bas_tarih_str, bit_tarih_str):
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "v3.football.api-sports.io"}
    tum_maclar = []
    progress = st.progress(0, text="Lig bültenleri hızlıca taranıyor...")
    for idx, lig_id in enumerate(secilen_lig_idleri):
        url = f"https://v3.football.api-sports.io/fixtures?league={lig_id}&next=20"
        try:
            res = requests.get(url, headers=headers, timeout=8).json()
            if res.get("response"):
                for item in res["response"]:
                    f_id = item["fixture"]["id"]
                    ev = item["teams"]["home"]["name"]
                    dep = item["teams"]["away"]["name"]
                    tarih = item["fixture"]["date"][:10]
                    saat = item["fixture"]["date"][11:16]
                    lig_adi = item["league"]["name"]
                    if bas_tarih_str <= tarih <= bit_tarih_str:
                        tum_maclar.append({
                            "id": f_id,
                            "lig": lig_adi,
                            "tarih": tarih,
                            "saat": saat,
                            "ev": ev,
                            "dep": dep,
                            "karsilasma": f"{ev} - {dep}",
                            "label": f"{ev} - {dep} ({lig_adi} | {tarih})"
                        })
        except Exception:
            pass
        progress.progress((idx + 1) / len(secilen_lig_idleri))
    progress.empty()
    return tum_maclar


def olasilik_yumusat(p1, px_val, p2):
    p1, px_val, p2 = max(5.0, float(p1)), max(5.0, float(px_val)), max(5.0, float(p2))
    toplam = p1 + px_val + p2
    y1 = int(round(p1 * 100 / toplam))
    yx = int(round(px_val * 100 / toplam))
    y2 = int(100 - y1 - yx)
    return y1, yx, y2


def halk_egilimi_simule_et(p1, px_val, p2):
    w1, wx, w2 = (p1 ** 1.55), (px_val ** 1.15), (p2 ** 1.55)
    t = w1 + wx + w2
    h1 = int(round(w1 * 100 / t))
    hx = int(round(wx * 100 / t))
    h2 = int(100 - h1 - hx)
    return h1, hx, h2


@st.cache_data(ttl=3600, show_spinner=False)
def hibrit_tahminleri_al(secilen_maclar, api_key):
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "v3.football.api-sports.io"}
    sonuclar = []
    progress = st.progress(0, text="Hibrit Motor: AI ve Bahis Oranları çekiliyor...")
    for i, mac in enumerate(secilen_maclar):
        f_id = mac["id"]
        ai_1, ai_x, ai_2 = 36.0, 33.0, 31.0
        odds_1, odds_x, odds_2 = None, None, None
        try:
            res_pred = requests.get(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", headers=headers, timeout=6).json()
            if res_pred.get("response") and res_pred["response"][0].get("predictions"):
                t = res_pred["response"][0]["predictions"]["percent"]
                ai_1 = float(t["home"].replace("%", ""))
                ai_x = float(t["draw"].replace("%", ""))
                ai_2 = float(t["away"].replace("%", ""))
        except Exception:
            pass
        try:
            res_odds = requests.get(f"https://v3.football.api-sports.io/odds?fixture={f_id}", headers=headers, timeout=6).json()
            if res_odds.get("response") and res_odds["response"][0].get("bookmakers"):
                buro = res_odds["response"][0]["bookmakers"][0]
                for bahis in buro.get("bets", []):
                    if bahis.get("id") == 1 or bahis.get("name") == "Match Winner":
                        degerler = {v["value"]: float(v["odd"]) for v in bahis.get("values", [])}
                        if "Home" in degerler and "Draw" in degerler and "Away" in degerler:
                            inv_1, inv_x, inv_2 = 1.0 / degerler["Home"], 1.0 / degerler["Draw"], 1.0 / degerler["Away"]
                            inv_top = inv_1 + inv_x + inv_2
                            odds_1 = (inv_1 / inv_top) * 100
                            odds_x = (inv_x / inv_top) * 100
                            odds_2 = (inv_2 / inv_top) * 100
                        break
        except Exception:
            pass

        ham_1 = ((odds_1 * 0.65) + (ai_1 * 0.35)) if odds_1 is not None else ai_1
        ham_x = ((odds_x * 0.65) + (ai_x * 0.35)) if odds_x is not None else ai_x
        ham_2 = ((odds_2 * 0.65) + (ai_2 * 0.35)) if odds_2 is not None else ai_2

        g1, gx, g2 = olasilik_yumusat(ham_1, ham_x, ham_2)
        h1, hx, h2 = halk_egilimi_simule_et(g1, gx, g2)
        sonuclar.append({
            "bulten_no": i + 1,
            "id": f_id,
            "mac": mac["karsilasma"],
            "lig": mac.get("lig", "-"),
            "tarih": mac.get("tarih", "-"),
            "1": g1,
            "X": gx,
            "2": g2,
            "halk_favori": max(h1, hx, h2),
            "tuzak_farki": max(h1, hx, h2) - max(g1, gx, g2)
        })
        progress.progress((i + 1) / len(secilen_maclar))
        time.sleep(0.1)
    progress.empty()
    return sonuclar


def canli_skorlari_cek(fixture_id_listesi, api_key):
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "v3.football.api-sports.io"}
    ids_str = "-".join(str(fid) for fid in fixture_id_listesi)
    url = f"https://v3.football.api-sports.io/fixtures?ids={ids_str}"
    yeni_sonuclar, skor_metinleri = ["⏳ Bekliyor"] * 15, ["-"] * 15
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        if res.get("response"):
            id_haritasi = {item["fixture"]["id"]: item for item in res["response"]}
            for idx, fid in enumerate(fixture_id_listesi):
                if fid in id_haritasi:
                    md = id_haritasi[fid]
                    durum = md["fixture"]["status"]["short"]
                    if durum not in ["NS", "TBD", "PST", "CANC"] and md["goals"]["home"] is not None:
                        eg, dg = md["goals"]["home"], md["goals"]["away"]
                        skor_metinleri[idx] = f"{eg} - {dg} ({durum})"
                        yeni_sonuclar[idx] = "1" if eg > dg else ("X" if eg == dg else "2")
    except Exception:
        pass
    return yeni_sonuclar, skor_metinleri


# ==============================================================================
# OTONOM ANALİZ, ENTROPİ FİLTRESİ VE AĞIRLIKLI GARANTİ MOTORU
# ==============================================================================
def tam_otonom_analiz(mac_verileri, strateji):
    beklenen_1, beklenen_x, beklenen_2, min_puan, max_puan = 0, 0, 0, 0, 0
    en_yuksek = []
    for v in mac_verileri:
        s = sorted([v["1"], v["X"], v["2"]])
        min_puan += s[0]
        max_puan += s[2]
        en_yuksek.append(s[2])
        if v["1"] == s[2]:
            beklenen_1 += 1
        elif v["X"] == s[2]:
            beklenen_x += 1
        else:
            beklenen_2 += 1

    hz = float(np.mean(en_yuksek))
    pf = max(15, max_puan - min_puan)

    if "Favori" in strateji:
        ai_banko, ai_cifte = max(50, int(hz + 2)), max(35, int(hz - 10))
        alt_puan, ust_puan = int(min_puan + (pf * 0.55)), int(max_puan)
        surpriz_aralik = (0, 3)
    elif "İkramiye" in strateji:
        ai_banko, ai_cifte = max(58, int(hz + 8)), max(40, int(hz - 5))
        alt_puan, ust_puan = int(min_puan + (pf * 0.20)), int(min_puan + (pf * 0.78))
        surpriz_aralik = (2, 6)
    else:
        ai_banko, ai_cifte = max(53, int(hz + 5)), max(37, int(hz - 8))
        alt_puan, ust_puan = int(min_puan + (pf * 0.35)), int(min_puan + (pf * 0.92))
        surpriz_aralik = (1, 5)

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
        "max_blok_tekrar": 3 if hz > 62 else 2,
        "zorluk_skoru": hz
    }


def varsayilan_sablon_olustur(veriler, limitler, tuzak_aktif=True):
    sablon = []
    for v in veriler:
        s = sorted([(v["1"], "1"), (v["X"], "X"), (v["2"], "2")], reverse=True)
        if s[0][0] >= limitler["banko_siniri"]:
            if tuzak_aktif and v.get("tuzak_farki", 0) >= 12 and s[0][0] < 68:
                secim = [s[0][1], s[1][1]]
            else:
                secim = [s[0][1]]
        elif s[0][0] >= limitler["cifte_siniri"]:
            secim = [s[0][1], s[1][1]]
        else:
            secim = ["1", "X", "2"]
        sablon.append(secim)

    if limitler.get("aktif_blok_filtresi") and limitler["max_blok_tekrar"] < 3:
        for b in range(0, 15, 3):
            blok_sablon = sablon[b:b+3]
            if all(len(x) == 1 for x in blok_sablon) and (blok_sablon[0][0] == blok_sablon[1][0] == blok_sablon[2][0]):
                en_zayif_idx = min(range(b, b+3), key=lambda idx: max(veriler[idx]["1"], veriler[idx]["X"], veriler[idx]["2"]))
                sirali = sorted([(veriler[en_zayif_idx]["1"], "1"), (veriler[en_zayif_idx]["X"], "X"), (veriler[en_zayif_idx]["2"], "2")], reverse=True)
                sablon[en_zayif_idx] = [sirali[0][1], sirali[1][1]]
    return sablon


def vektorel_filtrele(sablon, mac_verileri, limitler, entropi_aktif=True):
    harita = {"1": 0, "X": 1, "2": 2}
    ters = np.array(["1", "X", "2"])
    grids = np.meshgrid(*[[harita[s] for s in m] for m in sablon], indexing="ij")
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

    oran_mat = np.array([[v["1"], v["X"], v["2"]] for v in mac_verileri], dtype=np.int16)
    secilen_oranlar = oran_mat[np.arange(15), matris]
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
            pencereler = sliding_window_view(matris == deger, window_shape=max_ard + 1, axis=1)
            ardisik_ihlal = np.any(np.all(pencereler, axis=2), axis=1)
            matris = matris[~ardisik_ihlal]
            puanlar = puanlar[~ardisik_ihlal]

    if entropi_aktif and len(matris) > 0:
        gecis_sayisi = np.sum(matris[:, 1:] != matris[:, :-1], axis=1)
        entropi_maske = (gecis_sayisi >= 5) & (gecis_sayisi <= 12)
        if np.any(entropi_maske):
            matris = matris[entropi_maske]
            puanlar = puanlar[entropi_maske]

    if len(matris) == 0:
        return np.empty((0, 15), dtype=np.int8), np.array([])

    idx = np.argsort(puanlar)[::-1]
    return ters[matris[idx]], puanlar[idx]


def gelismis_garanti_ve_budama_uygula(kolonlar, puanlar, hedef, max_k=None, akilli_merkez=True, min_fark=1):
    if len(kolonlar) == 0:
        return np.empty((0, 15)), np.array([]), 0.0

    harita = {"1": 0, "X": 1, "2": 2}
    mat = np.vectorize(harita.get)(kolonlar).astype(np.int8)

    if hedef == 15:
        nihai = list(range(len(kolonlar)))
        kapsama_orani = 100.0
    else:
        fark = 15 - hedef
        mask = np.ones(len(kolonlar), dtype=bool)
        nihai = []

        while np.any(mask):
            if max_k and len(nihai) >= max_k:
                break

            aktif_indeksler = np.where(mask)[0]
            if akilli_merkez and len(aktif_indeksler) > 1:
                aday_havuzu = aktif_indeksler[:min(60, len(aktif_indeksler))]
                orneklem = aktif_indeksler[:min(2500, len(aktif_indeksler))]
                mesafe_mat = np.sum(mat[aday_havuzu, None, :] != mat[None, orneklem, :], axis=2)
                kapsama_skorlari = np.sum(mesafe_mat <= fark, axis=1) * (puanlar[aday_havuzu] / np.max(puanlar[aday_havuzu]))
                m_idx = int(aday_havuzu[int(np.argmax(kapsama_skorlari))])
            else:
                m_idx = int(aktif_indeksler[0])

            nihai.append(m_idx)
            mesafeler = np.sum(mat[aktif_indeksler] != mat[m_idx], axis=1)
            mask[aktif_indeksler[mesafeler <= fark]] = False

        kapsama_orani = float(np.sum(puanlar[~mask]) / np.sum(puanlar) * 100)

    if min_fark > 1 and len(nihai) > 1:
        budanmis_nihai = []
        for idx in nihai:
            if not budanmis_nihai:
                budanmis_nihai.append(idx)
            else:
                mevcut_mat = mat[budanmis_nihai]
                en_yakin_mesafe = np.min(np.sum(mevcut_mat != mat[idx], axis=1))
                if en_yakin_mesafe >= min_fark:
                    budanmis_nihai.append(idx)
        nihai = budanmis_nihai

    if max_k and len(nihai) > max_k:
        nihai = nihai[:max_k]

    return kolonlar[nihai], puanlar[nihai], kapsama_orani


def monte_carlo_simule_et(kuponlar, veriler):
    harita = {"1": 0, "X": 1, "2": 2}
    k_num = np.vectorize(harita.get)(kuponlar).astype(np.int8)
    rng = np.random.default_rng(42)
    sim = np.zeros((3000, 15), dtype=np.int8)
    for idx, v in enumerate(veriler):
        o = np.array([v["1"], v["X"], v["2"]], dtype=float)
        sim[:, idx] = rng.choice([0, 1, 2], size=3000, p=o / o.sum())
    dereceler = np.max(np.sum(sim[:, None, :] == k_num[None, :, :], axis=2), axis=1)
    return {
        "15_oran": float(np.mean(dereceler == 15) * 100),
        "14_arti_oran": float(np.mean(dereceler >= 14) * 100),
        "12_arti_oran": float(np.mean(dereceler >= 12) * 100)
    }


def kupon_dosyasi_coz(dosya):
    if dosya is None:
        return None
    try:
        satirlar = dosya.getvalue().decode("utf-8-sig").strip().splitlines()
        k = [["X" if h == "0" else h.upper() for h in s.replace(",", " ").replace(";", " ").split() if h.upper() in ["1", "X", "2", "0"]] for s in satirlar]
        k_15 = [s[:15] for s in k if len(s) >= 15]
        return np.array(k_15) if k_15 else None
    except Exception:
        return None


# ==============================================================================
# ANA SEKMELER
# ==============================================================================
tab_uretim, tab_takip, tab_otomasyon = st.tabs([
    "🚀 1. Hızlı Bülten Eşleştirme & Kupon Üretim",
    "📡 2. Canlı Kupon Takibi",
    "🤖 3. Otomatik Yatırma"
])

# ------------------------------------------------------------------------------
# SEKME 1: 5 SANİYEDE KOPYALA-YAPIŞTIR BÜLTEN SEÇİCİ VE DERİN ELEME
# ------------------------------------------------------------------------------
with tab_uretim:
    if not api_key:
        st.info("👈 Başlamak için sol menüden **API-Football Anahtarınızı** girin.")
    else:
        acik_kal = st.session_state.analiz_verisi is None
        with st.expander("⚡ ADIM 1: Hızlı Bülten Seçimi (Kopyala-Yapıştır veya Tek Tıkla Havuz)", expanded=acik_kal):
            bugun = datetime.now().date()
            varsayilan_bitis = bugun + timedelta(days=5)

            ust_c1, ust_c2, ust_c3 = st.columns([1.4, 1.8, 0.8])
            with ust_c1:
                tarih_araligi = st.date_input(
                    "📅 Bülten Tarih Aralığı:",
                    value=(bugun, varsayilan_bitis)
                )
            with ust_c2:
                st.write("")
                if st.button("⚡ Tek Tıkla Tüm Spor Toto Liglerini Getir (Önerilen)", type="primary", use_container_width=True):
                    if isinstance(tarih_araligi, tuple) and len(tarih_araligi) == 2:
                        bas_str = tarih_araligi[0].strftime("%Y-%m-%d")
                        bit_str = tarih_araligi[1].strftime("%Y-%m-%d")
                        yeni = tum_liglerden_maclari_getir(STANDART_TOTO_LIGLERI, api_key, bas_str, bit_str)
                        mevcut = {m["id"] for m in st.session_state.mac_listesi}
                        for m in yeni:
                            if m["id"] not in mevcut:
                                st.session_state.mac_listesi.append(m)
            with ust_c3:
                st.write("")
                if st.button("🗑️ Havuzu Temizle", use_container_width=True):
                    st.session_state.mac_listesi = []
                    st.session_state.secilen_15_mac = []
                    st.session_state.analiz_verisi = None
                    st.rerun()

            with st.expander("➕ Farklı Bir Lig veya Kupa Eklemek İsterseniz Tıklayın"):
                ek_c1, ek_c2, ek_c3 = st.columns([1.2, 2, 1])
                with ek_c1:
                    kat = st.selectbox("Bölge:", list(KATEGORIZE_LIGLER.keys()), key="k1")
                with ek_c2:
                    ligler = st.multiselect("Ligler:", list(KATEGORIZE_LIGLER[kat].keys()), key=f"lig_{kat}")
                with ek_c3:
                    st.write("")
                    if st.button("📥 Seçili Ligleri Ekle", use_container_width=True) and ligler:
                        bas_str = tarih_araligi[0].strftime("%Y-%m-%d")
                        bit_str = tarih_araligi[1].strftime("%Y-%m-%d")
                        yeni = tum_liglerden_maclari_getir([KATEGORIZE_LIGLER[kat][l] for l in ligler], api_key, bas_str, bit_str)
                        mevcut = {m["id"] for m in st.session_state.mac_listesi}
                        for m in yeni:
                            if m["id"] not in mevcut:
                                st.session_state.mac_listesi.append(m)

            if st.session_state.mac_listesi:
                st.markdown("---")
                secim_yontemi = st.radio(
                    "🎯 15 Maçı Nasıl Seçmek İstersiniz?",
                    [
                        "🪄 Yöntem A: Bahis Sitesinden Kopyala-Yapıştır ile Otomatik Bul (5 Saniye)",
                        "🔍 Yöntem B: Arama Kutusuyla Sırayla Yazarak Seç"
                    ],
                    horizontal=True
                )

                opsiyon_haritasi = {m["label"]: m for m in st.session_state.mac_listesi}
                varsayilan_etiketler = [m["label"] for m in st.session_state.secilen_15_mac if m["label"] in opsiyon_haritasi]

                if "Yöntem A" in secim_yontemi:
                    y_col1, y_col2 = st.columns([2.5, 1.2])
                    with y_col1:
                        yapistirilan = st.text_area(
                            "📋 Nesine / Bilyoner / Misli sayfasındaki 15 maçı fareyle seçip buraya yapıştırın (Ctrl+V):",
                            placeholder="Örnek:\n1. Çaykur Rizespor - Trabzonspor\n2. Beşiktaş - Başakşehir\n3. Galatasaray - Fenerbahçe...",
                            height=130
                        )
                    with y_col2:
                        st.write("")
                        st.write("")
                        if st.button("🪄 Metindeki Maçları Otomatik Eşleştir", use_container_width=True):
                            if yapistirilan.strip():
                                bulunanlar = bulten_metni_eslestir(yapistirilan, st.session_state.mac_listesi)
                                st.session_state.secilen_15_mac = bulunanlar
                                varsayilan_etiketler = [m["label"] for m in bulunanlar]
                                st.success(f"✅ Metinden **{len(bulunanlar)} maç** sırasıyla otomatik eşleştirildi!")

                # Her iki yöntemde de klavyeyle anında yazılıp tamamlanabilen hızlı kutu
                secilen_etiketler = st.multiselect(
                    f"✅ Seçilen Bülten Maçları ({len(st.session_state.mac_listesi)} maçlık havuzda takım adını klavyeyle yazıp Enter'a basabilirsiniz):",
                    options=list(opsiyon_haritasi.keys()),
                    default=varsayilan_etiketler,
                    max_selections=15
                )
                st.session_state.secilen_15_mac = [opsiyon_haritasi[e] for e in secilen_etiketler]

                alt_b1, alt_b2 = st.columns([3, 1.2])
                with alt_b1:
                    s_sayi = len(st.session_state.secilen_15_mac)
                    if s_sayi == 15:
                        st.success("🎯 **15 / 15 Maç Hazır!** Sağdaki butona basarak analizi başlatabilirsiniz.")
                    else:
                        st.warning(f"📌 Şu an **{s_sayi} / 15** maç seçili. Eksik maç varsa yukarıdaki kutuya takım adını yazıp seçebilirsiniz.")
                with alt_b2:
                    if len(st.session_state.secilen_15_mac) == 15:
                        if st.button("🚀 Analizi Başlat", type="primary", use_container_width=True):
                            st.session_state.secilen_mac_idleri = [m["id"] for m in st.session_state.secilen_15_mac]
                            st.session_state.analiz_verisi = hibrit_tahminleri_al(st.session_state.secilen_15_mac, api_key)
                            st.rerun()

        # ADIM 2: KAYDIRMASIZ TEK EKRAN ŞABLON VE DERİN ELEME SONUÇ PANELİ
        if st.session_state.analiz_verisi:
            veriler = st.session_state.analiz_verisi
            if ai_filtre_modu:
                limitler = tam_otonom_analiz(veriler, strateji_modu)
            else:
                limitler = {
                    "1": range_1, "X": range_x, "2": range_2, "puan": range_puan,
                    "surpriz": range_surpriz, "ardisik_1": max_ardisik_1,
                    "ardisik_x": max_ardisik_x, "ardisik_2": max_ardisik_2,
                    "banko_siniri": banko_siniri, "cifte_siniri": cifte_sans_siniri,
                    "aktif_blok_filtresi": aktif_blok_filtresi, "max_blok_tekrar": max_blok_tekrar
                }

            sablon = varsayilan_sablon_olustur(veriler, limitler, tuzak_koruma)

            df_edit = st.data_editor(
                pd.DataFrame([{
                    "Sıra": v["bulten_no"],
                    "ID": v["id"],
                    "Lig": v.get("lig", "-"),
                    "Tarih": v.get("tarih", "-"),
                    "Karşılaşma": v["mac"],
                    "1 (%)": v["1"],
                    "X (%)": v["X"],
                    "2 (%)": v["2"],
                    "Halk (%)": v["halk_favori"],
                    "Durum": "🚨 Tuzak Favori" if (v["tuzak_farki"] >= 12 and max(v["1"], v["X"], v["2"]) < 68) else "✅ Normal",
                    "1": "1" in s,
                    "X": "X" in s,
                    "2": "2" in s
                } for v, s in zip(veriler, sablon)]),
                column_config={"ID": None},
                disabled=["Lig", "Tarih", "Karşılaşma", "1 (%)", "X (%)", "2 (%)", "Halk (%)", "Durum"],
                hide_index=True,
                use_container_width=True,
                height=560
            )

            sirali = df_edit.sort_values("Sıra").reset_index(drop=True)
            st.session_state.secilen_mac_idleri = [int(x) for x in sirali["ID"].tolist()]

            g_sablon, s_veriler = [], []
            bos_mac_var = False
            for _, r in sirali.iterrows():
                sec = [k for k, b in [("1", r["1"]), ("X", r["X"]), ("2", r["2"])] if b]
                if not sec:
                    bos_mac_var = True
                g_sablon.append(sec if sec else ["1"])
                s_veriler.append({"mac": r["Karşılaşma"], "1": int(r["1 (%)"]), "X": int(r["X (%)"]), "2": int(r["2 (%)"])})

            if bos_mac_var:
                st.error("⚠️ Her maçta en az 1 tercih (1, X veya 2) işaretli olmalıdır.")
            elif math.prod(len(s) for s in g_sablon) > 4_782_969:
                st.error("⚠️ Şablon çok geniş! Lütfen 1-2 maçı Çifte Şans veya Banko'ya indirin.")
            else:
                mat, puanlar = vektorel_filtrele(g_sablon, s_veriler, limitler, entropi_aktif=entropi_filtresi)
                if len(mat) == 0:
                    st.warning("⚠️ Filtreler tüm kombinasyonları eledi. Sol menüden farklı bir Strateji seçin veya şablonda 1-2 maç açın.")
                else:
                    garanti, g_puan, kapsama = gelismis_garanti_ve_budama_uygula(
                        mat, puanlar, garanti_derecesi,
                        max_k=max_kolon_limiti,
                        akilli_merkez=akilli_merkez,
                        min_fark=benzerlik_elemesi
                    )
                    st.session_state.uretilen_kuponlar = garanti
                    mc = monte_carlo_simule_et(garanti, s_veriler)

                    m1, m2, m3, m4, m5, m6 = st.columns([1, 1, 1, 1, 1, 1.3])
                    m1.metric("Filtre Sonrası", f"{len(mat):,}")
                    m2.metric(f"{garanti_derecesi} Garantili (Net)", f"{len(garanti):,} Kolon")
                    m3.metric("Toplam Bütçe", f"{len(garanti) * kolon_fiyati:,.0f} TL")
                    m4.metric("🥇 15 Şansı", f"%{mc['15_oran']:.1f}")
                    m5.metric("🎯 İkramiye (12+)", f"%{mc['12_arti_oran']:.1f}")
                    with m6:
                        st.write("")
                        st.download_button(
                            "📥 Kuponları İndir (.TXT)",
                            "\n".join([" ".join(k) for k in garanti]),
                            f"spor_toto_v8_{garanti_derecesi}G.txt",
                            type="primary",
                            use_container_width=True
                        )

                    with st.expander("📊 Üretilen Nihai Kuponların Maç Bazlı 1-X-2 Dağılım Kontrolü"):
                        toplam_k = len(garanti)
                        dagilim_satirlari = []
                        for m_i, v_m in enumerate(s_veriler):
                            sutun = garanti[:, m_i]
                            s1, sx, s2 = int(np.sum(sutun == "1")), int(np.sum(sutun == "X")), int(np.sum(sutun == "2"))
                            dagilim_satirlari.append({
                                "Maç No": m_i + 1,
                                "Karşılaşma": v_m["mac"],
                                "1 Adet (%)": f"{s1} (%{s1*100/toplam_k:.0f})",
                                "X Adet (%)": f"{sx} (%{sx*100/toplam_k:.0f})",
                                "2 Adet (%)": f"{s2} (%{s2*100/toplam_k:.0f})"
                            })
                        st.dataframe(pd.DataFrame(dagilim_satirlari), hide_index=True, use_container_width=True)

# ------------------------------------------------------------------------------
# SEKME 2: CANLI KUPON TAKİBİ
# ------------------------------------------------------------------------------
with tab_takip:
    col_t1, col_t2 = st.columns([1.1, 1.6])
    with col_t1:
        kaynak = st.radio(
            "Takip Kaynağı:",
            ["📂 Dosya Yükle (.txt/.csv)", "⚡ Oturumdaki Kuponlar"],
            index=1 if st.session_state.uretilen_kuponlar is not None else 0,
            horizontal=True
        )
        if "Dosya" in kaynak:
            yuklenen_dosya = st.file_uploader("Kupon Dosyası:", type=["txt", "csv"])
            aktif_k = kupon_dosyasi_coz(yuklenen_dosya)
        else:
            aktif_k = st.session_state.uretilen_kuponlar

        if api_key and len(st.session_state.secilen_mac_idleri) == 15:
            if st.button("🔄 Canlı Skorları API'den Otomatik Çek", type="primary", use_container_width=True):
                st.session_state.canli_sonuclar, st.session_state.canli_skor_metni = canli_skorlari_cek(
                    st.session_state.secilen_mac_idleri, api_key
                )

        m_isim = [v["mac"] for v in st.session_state.analiz_verisi] if st.session_state.analiz_verisi else [f"{i}. Maç" for i in range(1, 16)]
        sonuc_df = st.data_editor(
            pd.DataFrame({
                "No": list(range(1, 16)),
                "Maç": m_isim,
                "Skor": st.session_state.canli_skor_metni,
                "Sonuç": st.session_state.canli_sonuclar
            }),
            column_config={
                "Sonuç": st.column_config.SelectboxColumn("Sonuç", options=["⏳ Bekliyor", "1", "X", "2"], required=True)
            },
            disabled=["No", "Maç", "Skor"],
            hide_index=True,
            use_container_width=True,
            height=560
        )

    with col_t2:
        if aktif_k is not None and len(aktif_k) > 0:
            res = np.array(sonuc_df["Sonuç"].tolist())
            mask = np.isin(res, ["1", "X", "2"])
            oynanan = int(np.sum(mask))
            if oynanan > 0:
                dogru = np.sum(aktif_k[:, mask] == res[mask], axis=1)
                hata = oynanan - dogru
                maks_h = 15 - hata

                st.markdown(f"### 🏆 Canlı İkramiye Potası ({oynanan} / 15 Maç Girildi)")
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("🥇 15'e Giden", f"{int(np.sum(maks_h == 15)):,}")
                k2.metric("🥈 14'e Giden", f"{int(np.sum(maks_h == 14)):,}")
                k3.metric("🥉 13'e Giden", f"{int(np.sum(maks_h == 13)):,}")
                k4.metric("🎯 12'ye Giden", f"{int(np.sum(maks_h == 12)):,}")

                sirali_idx = np.argsort(maks_h)[::-1][:200]
                st.dataframe(
                    pd.DataFrame([{
                        "Kupon": f"#{i+1}",
                        "Hedef": f"🏆 {int(maks_h[i])} Adayı" if maks_h[i] >= 12 else "❌ Elendi",
                        "Doğru": int(dogru[i]),
                        "Hata": int(hata[i]),
                        "Dizilim": " ".join(aktif_k[i])
                    } for i in sirali_idx]),
                    hide_index=True,
                    use_container_width=True,
                    height=440
                )
            else:
                st.info("👈 Sol tablodan maç sonuçlarını (1, X, 2) seçtiğiniz anda canlı ikramiye potası hesaplanır.")
        else:
            st.info("👈 Takip başlatmak için önce 1. Sekmeden kupon üretin veya sol taraftan kupon dosyası (.txt) yükleyin.")

# ------------------------------------------------------------------------------
# SEKME 3: OTOMATİK YATIRMA
# ------------------------------------------------------------------------------
with tab_otomasyon:
    st.markdown("### 🤖 Otomatik Kupon Yatırma (Tarayıcı F12 Botu)")
    if st.session_state.uretilen_kuponlar is not None and len(st.session_state.uretilen_kuponlar) > 0:
        k_oto = st.session_state.uretilen_kuponlar.tolist()
        c_o1, c_o2 = st.columns([1, 2.5])
        with c_o1:
            boyut = st.number_input("Paket Başına Kolon:", 10, 500, 50, step=10)
            sec_p = st.selectbox("Paket Seç:", [f"Paket {i+1}" for i in range(math.ceil(len(k_oto) / boyut))])
            p_id = int(sec_p.split()[1]) - 1
            sifir_kullan = st.toggle("Beraberliği '0' Olarak Kodla", value=True)
        with c_o2:
            aktif_paket = [
                ["0" if (s == "X" and sifir_kullan) else s for s in kolon]
                for kolon in k_oto[p_id * boyut : (p_id + 1) * boyut]
            ]
            st.code(
                f"// Bahis sitesinde F12 -> Console sekmesine yapıştırın:\nconst kuponlar = {json.dumps(aktif_paket)};\nconsole.log('Paket hazır, kolon sayısı:', kuponlar.length);",
                language="javascript"
            )
            st.text_area("Hızlı Kopyala-Yapıştır Dizilimi:", value="\n".join(["".join(k) for k in aktif_paket]), height=220)
    else:
        st.info("👈 Önce 1. Sekmeden kupon üretin.")
