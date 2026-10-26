import streamlit as st
import requests
import math
import json
import re
import unicodedata
from difflib import SequenceMatcher
from datetime import datetime, timedelta
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import pandas as pd

st.set_page_config(page_title="Spor Toto AI Pro v9.0 Syndicate", page_icon="🏆", layout="wide")

# --- KOMPAKT VE MODERN ARAYÜZ CSS ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }
        div[data-testid="stMetric"] {
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            padding: 10px 14px;
            border-radius: 10px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.25rem !important;
            font-weight: 700 !important;
            color: #0f172a;
        }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE BAŞLATMA ---
varsayilan_state = {
    "mac_listesi": [],
    "secilen_15_mac": [],
    "analiz_verisi": None,
    "tablo_df": None,
    "secilen_mac_idleri": [],
    "uretilen_kuponlar": None,
    "canli_sonuclar": ["⏳ Bekliyor"] * 15,
    "canli_skor_metni": ["-"] * 15,
    "kalan_kota": "Bilinmiyor"
}
for anahtar, deger in varsayilan_state.items():
    if anahtar not in st.session_state:
        st.session_state[anahtar] = deger

# --- DESTEKLENEN SPOR TOTO LİG HAVUZU ---
DESTEKLENEN_LIGLER = {
    203: "🇹🇷 Süper Lig", 204: "🇹🇷 1. Lig", 205: "🇹🇷 Türkiye Kupası",
    39: "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League", 40: "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship",
    140: "🇪🇸 La Liga", 135: "🇮🇹 Serie A", 78: "🇩🇪 Bundesliga", 61: "🇫🇷 Ligue 1",
    2: "⭐ Şampiyonlar Ligi", 3: "⭐ Avrupa Ligi", 848: "⭐ Konferans Ligi", 5: "⭐ Uluslar Ligi",
    88: "🇳🇱 Eredivisie", 94: "🇵🇹 Primeira Liga", 144: "🇧🇪 Pro League",
    103: "🇨🇭 Super League", 218: "🇦🇹 Bundesliga", 179: "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Premiership",
    197: "🇬🇷 Super League", 119: "🇩🇰 Superliga", 106: "🇵🇱 Ekstraklasa",
    71: "🇧🇷 Série A", 128: "🇦🇷 Liga Prof.", 253: "🇺🇸 MLS", 307: "🇸🇦 Pro League"
}

# ==============================================================================
# SOL MENÜ: SİSTEM, BÜTÇE VE PROFESYONEL DARALTMA PARAMETRELERİ
# ==============================================================================
with st.sidebar:
    st.markdown("## 🏆 Spor Toto AI v9.0")
    st.caption("Profesyonel Sendika & Daraltma Motoru")
    api_key = st.text_input("🔑 API-Football Anahtarı:", type="password")
    if api_key:
        st.caption(f"📊 Kalan Günlük API Kotası: **{st.session_state.kalan_kota}**")

    st.markdown("---")
    st.markdown("### 🎯 1. Garanti & Maliyet Optimizasyonu")
    garanti_secimi = st.selectbox(
        "Matematiksel Garanti Hedefi:",
        [
            "15 Garanti (Tam Filtreli Sistem)",
            "14 Garanti (1 Maç Hata Payı - %80 Tasarruf)",
            "13 Garanti (2 Maç Hata Payı - %93 Tasarruf)",
            "12 Garanti (3 Maç Hata Payı - %98 Tasarruf)"
        ],
        index=1
    )
    garanti_derecesi = int(garanti_secimi.split()[0])
    kolon_fiyati = st.number_input("Kolon Birim Fiyatı (TL):", min_value=1.0, value=10.0, step=1.0)

    butce_aktif = st.toggle("💰 Maksimum Bütçe / Kolon Sınırı", value=False)
    if butce_aktif:
        max_kolon_limiti = st.number_input("Maksimum Kolon Adedi:", min_value=1, max_value=50000, value=100, step=10)
        st.caption(f"Maksimum Ödenecek Tutar: **{max_kolon_limiti * kolon_fiyati:,.0f} TL**")
    else:
        max_kolon_limiti = None

    st.markdown("---")
    st.markdown("### 🧠 2. Maliyet Düşürücü Akıllı Filtreler")
    strateji_modu = st.radio(
        "Yapay Zeka Oyun Stili:",
        ["⚖️ Dengeli (Optimum EV)", "🛡️ Favori Ağırlıklı", "💎 İkramiye Avcısı (Sürprizli)"]
    )
    
    # YENİ: Grup Güvencesi (Pivot) Sistemi
    grup_guvence_aktif = st.toggle("🌟 Güvence (G) Grubu Filtresi (%50+ Tasarruf)", value=True, help="Tabloda 'G' işaretlediğiniz favorilerin aynı anda hepsinin birden patlamayacağı varsayımıyla gereksiz sürpriz kombinasyonlarını siler.")
    if grup_guvence_aktif:
        grup_max_hata = st.slider("🌟 'G' İşaretli Maçlarda Maks. Sürpriz (Hata):", 0, 4, 1, help="Örn: 4 maça 'G' işareti koydunuz ancak Çifte/Kapalı açtınız. Burayı 1 yaparsanız, bu 4 favoriden en fazla 1 tanesinin puan kaybedebileceği tüm kuponları tutar, 2 ve üzeri favorinin aynı anda yıkıldığı gereksiz kolonları siler.")
    else:
        grup_max_hata = 15

    akilli_merkez = st.toggle("🧮 Set-Cover Kümeleme (Daha Az Kolon)", value=True, help="Tek bir kolonla en fazla komşu kombinasyonu kapatan merkezleri seçerek %25 daha az kolonla aynı garantiyi sağlar.")
    entropi_filtresi = st.toggle("🌀 Yapay/Simetrik Dizilim Elemesi", value=True, help="1-1-1-1-1 veya 1-X-2-1-X-2 gibi gerçek hayatta çıkma ihtimali çok düşük dizilimleri eler.")
    tuzak_koruma = st.toggle("🚨 Tuzak Favorileri Otomatik Çifteye Al", value=True)
    benzerlik_elemesi = st.select_slider("🔍 Kuponlar Arası Min. Farklı Maç:", options=[1, 2, 3, 4], value=1)
    ai_filtre_modu = st.toggle("🤖 Otonom İstatistik Sınırları", value=True)

    if not ai_filtre_modu:
        with st.expander("⚙️ Manuel Filtre Ayarları"):
            range_1 = st.slider("Ev Sahibi (1) Adedi", 0, 15, (4, 9))
            range_x = st.slider("Beraberlik (X) Adedi", 0, 15, (1, 5))
            range_2 = st.slider("Deplasman (2) Adedi", 0, 15, (2, 7))
            range_puan = st.slider("Toplam Yüzde Puan Aralığı", 300, 1200, (520, 920))
            range_surpriz = st.slider("Sürpriz Sayısı (<%28)", 0, 10, (0, 4))
            max_ardisik_1 = st.slider("Üst Üste Maks. '1'", 2, 10, 5)
            max_ardisik_x = st.slider("Üst Üste Maks. 'X'", 2, 10, 3)
            max_ardisik_2 = st.slider("Üst Üste Maks. '2'", 2, 10, 4)
            banko_siniri = st.number_input("Banko Sınırı (%)", 35, 95, 58)
            cifte_sans_siniri = st.number_input("Çifte Şans Sınırı (%)", 30, 80, 42)


# ==============================================================================
# ULTRA DÜŞÜK TÜKETİMLİ API VE METİN EŞLEŞTİRME MOTORU
# ==============================================================================
def api_istegi_at(url, api_key, timeout=8):
    headers = {"x-apisports-key": api_key}
    res = requests.get(url, headers=headers, timeout=timeout)
    kalan = res.headers.get("x-ratelimit-requests-remaining")
    if kalan is not None:
        st.session_state.kalan_kota = kalan
    return res.json()


@st.cache_data(ttl=21600, show_spinner=False)
def gunluk_bulten_cek_cacheli(tarih_str, api_key, sadece_toto_ligleri=True):
    url = f"https://v3.football.api-sports.io/fixtures?date={tarih_str}&timezone=Europe/Istanbul"
    gunun_maclari = []
    try:
        data = api_istegi_at(url, api_key, timeout=10)
        for item in data.get("response", []):
            lig_id = item["league"]["id"]
            if sadece_toto_ligleri and lig_id not in DESTEKLENEN_LIGLER:
                continue
            f_id = item["fixture"]["id"]
            ev = item["teams"]["home"]["name"]
            dep = item["teams"]["away"]["name"]
            saat = item["fixture"]["date"][11:16]
            lig_etiket = DESTEKLENEN_LIGLER.get(lig_id, f"{item['league']['country']} - {item['league']['name']}")
            gunun_maclari.append({
                "id": f_id,
                "lig_id": lig_id,
                "lig": lig_etiket,
                "tarih": tarih_str,
                "saat": saat,
                "ev": ev,
                "dep": dep,
                "karsilasma": f"{ev} - {dep}",
                "label": f"[{lig_etiket}] {ev} - {dep} ({tarih_str} {saat})"
            })
    except Exception:
        pass
    return gunun_maclari


def tarih_araligi_maclarini_getir(bas_tarih, bit_tarih, api_key, sadece_toto_ligleri=True):
    tum_maclar = []
    gun_sayisi = (bit_tarih - bas_tarih).days + 1
    progress = st.progress(0, text="Bülten günleri taranıyor (Önbellek destekli)...")
    for i in range(gun_sayisi):
        g_str = (bas_tarih + timedelta(days=i)).strftime("%Y-%m-%d")
        maclar = gunluk_bulten_cek_cacheli(g_str, api_key, sadece_toto_ligleri)
        tum_maclar.extend(maclar)
        progress.progress((i + 1) / gun_sayisi)
    progress.empty()
    tum_maclar.sort(key=lambda x: (0 if x["lig_id"] in [203, 204] else 1, x["tarih"], x["saat"]))
    return tum_maclar


def olasilik_yumusat(p1, px_val, p2):
    p1, px_val, p2 = max(5.0, float(p1)), max(5.0, float(px_val)), max(5.0, float(p2))
    toplam = p1 + px_val + p2
    y1 = int(round(p1 * 100 / toplam))
    yx = int(round(px_val * 100 / toplam))
    y2 = max(1, 100 - y1 - yx)
    fark = 100 - (y1 + yx + y2)
    if fark != 0:
        if y1 >= y2 and y1 >= yx:
            y1 += fark
        elif y2 >= y1 and y2 >= yx:
            y2 += fark
        else:
            yx += fark
    return y1, yx, y2


def halk_egilimi_simule_et(p1, px_val, p2):
    w1, wx, w2 = (p1 ** 1.55), (px_val ** 1.15), (p2 ** 1.55)
    t = w1 + wx + w2
    h1 = int(round(w1 * 100 / t))
    hx = int(round(wx * 100 / t))
    h2 = max(1, 100 - h1 - hx)
    return h1, hx, h2


@st.cache_data(ttl=43200, show_spinner=False)
def tek_mac_analiz_cek(f_id, api_key):
    ai_1, ai_x, ai_2 = 36.0, 32.0, 32.0
    odds_1, odds_x, odds_2 = None, None, None
    try:
        res_pred = api_istegi_at(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", api_key, timeout=6)
        if res_pred.get("response") and res_pred["response"][0].get("predictions"):
            t = res_pred["response"][0]["predictions"]["percent"]
            ai_1 = float(t["home"].replace("%", ""))
            ai_x = float(t["draw"].replace("%", ""))
            ai_2 = float(t["away"].replace("%", ""))
    except Exception:
        pass

    try:
        res_odds = api_istegi_at(f"https://v3.football.api-sports.io/odds?fixture={f_id}", api_key, timeout=6)
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

    ham_1 = ((odds_1 * 0.68) + (ai_1 * 0.32)) if odds_1 is not None else ai_1
    ham_x = ((odds_x * 0.68) + (ai_x * 0.32)) if odds_x is not None else ai_x
    ham_2 = ((odds_2 * 0.68) + (ai_2 * 0.32)) if odds_2 is not None else ai_2

    return olasilik_yumusat(ham_1, ham_x, ham_2)


def hibrit_tahminleri_al(secilen_maclar, api_key):
    sonuclar = []
    progress = st.progress(0, text="Maç analizleri ve oran modelleri hesaplanıyor...")
    for i, mac in enumerate(secilen_maclar):
        f_id = mac["id"]
        g1, gx, g2 = tek_mac_analiz_cek(f_id, api_key)
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
    progress.empty()
    return sonuclar


def metin_temizle(s):
    tr_harita = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    s = s.translate(tr_harita).lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf-8")
    kisaltmalar = {
        "f.bahce": "fenerbahce", "g.saray": "galatasaray", "b.sehir": "basaksehir",
        "karagumruk": "fatih karagumruk", "m.united": "manchester united",
        "m.city": "manchester city", "b.munchen": "bayern munich", "b.dortmund": "borussia dortmund",
        "c.rizespor": "rizespor", "g.antep": "gaziantep"
    }
    for k, u in kisaltmalar.items():
        s = s.replace(k, u)
    s = re.sub(r"\b(fk|sk|as|fc|ac|sc|cf|cd|ud|rc|rcd|sv|vfb|vfl|tsg|1899|1907|spor|belediyespor|united|city|club|caykur|atakas|rams|bellona|iklimlendirme|corendon|eyupspor)\b", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return " ".join(s.split())


def bulten_metni_eslestir(yapistirilan_metin, havuz_maclari):
    satirlar = [s.strip() for s in yapistirilan_metin.splitlines() if len(s.strip()) > 2]
    eslesen_maclar = []
    kullanilan_idler = set()

    for satir in satirlar:
        temiz_satir = re.sub(r"^\d+[\.\-\)\s]+", "", satir)
        metin_adayi = metin_temizle(temiz_satir)
        if len(metin_adayi) < 3:
            continue

        en_iyi_skor = 0.0
        en_iyi_mac = None

        for m in havuz_maclari:
            if m["id"] in kullanilan_idler:
                continue
            ev_temiz = metin_temizle(m["ev"])
            dep_temiz = metin_temizle(m["dep"])
            mac_birlesik = f"{ev_temiz} {dep_temiz}"

            skor_genel = SequenceMatcher(None, metin_adayi, mac_birlesik).ratio()
            ev_var = 0.35 if (ev_temiz and ev_temiz.split()[0] in metin_adayi) else 0.0
            dep_var = 0.35 if (dep_temiz and dep_temiz.split()[0] in metin_adayi) else 0.0
            toplam_skor = skor_genel + ev_var + dep_var

            if toplam_skor > en_iyi_skor:
                en_iyi_skor = toplam_skor
                en_iyi_mac = m

        if en_iyi_mac and en_iyi_skor >= 0.42:
            eslesen_maclar.append(en_iyi_mac)
            kullanilan_idler.add(en_iyi_mac["id"])
            if len(eslesen_maclar) == 15:
                break

    return eslesen_maclar


def canli_skorlari_cek(fixture_id_listesi, api_key):
    ids_str = "-".join(str(fid) for fid in fixture_id_listesi)
    url = f"https://v3.football.api-sports.io/fixtures?ids={ids_str}"
    yeni_sonuclar, skor_metinleri = ["⏳ Bekliyor"] * 15, ["-"] * 15
    try:
        res = api_istegi_at(url, api_key, timeout=10)
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
# MATEMATİKSEL FİLTRELEME, LOG-OLASILIK VE KÜME KAPSAMA (SET COVER) MOTORU
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
        ai_banko, ai_cifte = max(50, int(hz + 1)), max(35, int(hz - 10))
        alt_puan, ust_puan = int(min_puan + (pf * 0.52)), int(max_puan)
        surpriz_aralik = (0, 3)
    elif "İkramiye" in strateji:
        ai_banko, ai_cifte = max(57, int(hz + 7)), max(40, int(hz - 5))
        alt_puan, ust_puan = int(min_puan + (pf * 0.22)), int(min_puan + (pf * 0.80))
        surpriz_aralik = (2, 6)
    else:
        ai_banko, ai_cifte = max(53, int(hz + 4)), max(37, int(hz - 8))
        alt_puan, ust_puan = int(min_puan + (pf * 0.35)), int(min_puan + (pf * 0.94))
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
        "zorluk_skoru": hz
    }


def tablo_verisi_olustur(veriler, limitler, tuzak_aktif=True, mod="ai"):
    satirlar = []
    for v in veriler:
        s = sorted([(v["1"], "1"), (v["X"], "X"), (v["2"], "2")], reverse=True)
        en_b_oran, en_b_secim = s[0][0], s[0][1]
        ikinci_secim = s[1][1]

        if mod == "15_banko":
            secim = [en_b_secim]
            guvence = False
        elif mod == "dengeli_4b_7c_4k":
            # Tüm maçları favori oranına göre sıralayıp ilk 4'ü Banko, orta 7'yi Çifte, son 4'ü Kapalı yapar
            tum_sirali = sorted([m["id"] for m in veriler], key=lambda x: max( next(item for item in veriler if item["id"] == x)["1"], next(item for item in veriler if item["id"] == x)["X"], next(item for item in veriler if item["id"] == x)["2"] ), reverse=True)
            sira_idx = tum_sirali.index(v["id"])
            if sira_idx < 4:
                secim = [en_b_secim]
                guvence = False
            elif sira_idx < 11:
                secim = [en_b_secim, ikinci_secim]
                guvence = True if sira_idx < 8 else False
            else:
                secim = ["1", "X", "2"]
                guvence = False
        else:
            # AI Önerisi
            if en_b_oran >= limitler["banko_siniri"]:
                if tuzak_aktif and v.get("tuzak_farki", 0) >= 12 and en_b_oran < 68:
                    secim = [en_b_secim, ikinci_secim]
                    guvence = True
                else:
                    secim = [en_b_secim]
                    guvence = False
            elif en_b_oran >= limitler["cifte_siniri"]:
                secim = [en_b_secim, ikinci_secim]
                guvence = True if en_b_oran >= 46 else False
            else:
                secim = ["1", "X", "2"]
                guvence = False

        tuzak_mi = (v.get("tuzak_farki", 0) >= 12 and en_b_oran < 68)
        satirlar.append({
            "Sıra": v["bulten_no"],
            "ID": v["id"],
            "Lig": v.get("lig", "-"),
            "Karşılaşma": v["mac"],
            "1 (%)": v["1"],
            "X (%)": v["X"],
            "2 (%)": v["2"],
            "Analiz": "🚨 Tuzak" if tuzak_mi else ("🔒 Banko Adayı" if en_b_oran >= 55 else "⚖️ Ortada"),
            "1": "1" in secim,
            "X": "X" in secim,
            "2": "2" in secim,
            "🌟 G": guvence
        })
    return pd.DataFrame(satirlar)


def vektorel_filtrele(sablon, mac_verileri, limitler, guvence_indeksleri, max_guvence_hata, entropi_aktif=True):
    harita = {"1": 0, "X": 1, "2": 2}
    ters = np.array(["1", "X", "2"])
    grids = np.meshgrid(*[[harita[s] for s in m] for m in sablon], indexing="ij")
    matris = np.stack(grids, axis=-1).reshape(-1, 15).astype(np.int8)

    # 1. Toplam 1-X-2 Adet Filtresi
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
        return np.empty((0, 15), dtype="<U1"), np.array([]), np.array([])

    # 2. YENİ: Grup Güvencesi (Pivot) Filtresi (%50+ Tasarruf Sağlar)
    oran_mat = np.array([[v["1"], v["X"], v["2"]] for v in mac_verileri], dtype=np.float32)
    favori_indeksleri = np.argmax(oran_mat, axis=1)  # Her maçın favorisi (0, 1 veya 2)

    if len(guvence_indeksleri) > 0 and max_guvence_hata < len(guvence_indeksleri):
        g_idx = np.array(guvence_indeksleri, dtype=int)
        g_favoriler = favori_indeksleri[g_idx]
        # Güvence grubundaki maçlarda favori gelmeyenlerin (hataların) sayısı
        g_hatalar = np.sum(matris[:, g_idx] != g_favoriler, axis=1)
        matris = matris[g_hatalar <= max_guvence_hata]
        if len(matris) == 0:
            return np.empty((0, 15), dtype="<U1"), np.array([]), np.array([])

    # 3. Gerçek Çarpımsal (Log-Olasılık) ve Toplam Puan Filtresi
    secilen_oranlar = oran_mat[np.arange(15), matris]
    puanlar = np.sum(secilen_oranlar, axis=1)
    # Log-Olasılık (Bağımsız olayların çarpımının logaritması): Gerçek olasılık sıralaması verir!
    log_olasilik = np.sum(np.log(np.maximum(secilen_oranlar, 1.0) / 100.0), axis=1)
    surpriz_sayisi = np.sum(secilen_oranlar < 28, axis=1)

    maske_puan = (
        (puanlar >= limitler["puan"][0]) & (puanlar <= limitler["puan"][1]) &
        (surpriz_sayisi >= limitler["surpriz"][0]) & (surpriz_sayisi <= limitler["surpriz"][1])
    )
    matris = matris[maske_puan]
    puanlar = puanlar[maske_puan]
    log_olasilik = log_olasilik[maske_puan]
    if len(matris) == 0:
        return np.empty((0, 15), dtype="<U1"), np.array([]), np.array([])

    # 4. Ardışık Tekrar Filtresi
    for deger, anahtar in [(0, "ardisik_1"), (1, "ardisik_x"), (2, "ardisik_2")]:
        max_ard = int(limitler[anahtar])
        if 1 <= max_ard < 15 and len(matris) > 0:
            pencereler = sliding_window_view(matris == deger, window_shape=max_ard + 1, axis=1)
            ardisik_ihlal = np.any(np.all(pencereler, axis=2), axis=1)
            matris = matris[~ardisik_ihlal]
            puanlar = puanlar[~ardisik_ihlal]
            log_olasilik = log_olasilik[~ardisik_ihlal]

    # 5. Entropi & Yapay Simetri Filtresi
    if entropi_aktif and len(matris) > 0:
        gecis_sayisi = np.sum(matris[:, 1:] != matris[:, :-1], axis=1)
        # Periyodik simetri kontrolü (1-X-2-1-X-2 gibi tekrarları eler)
        periyot_3 = np.sum(matris[:, 3:] == matris[:, :-3], axis=1)
        entropi_maske = (gecis_sayisi >= 5) & (gecis_sayisi <= 12) & (periyot_3 <= 9)
        if np.any(entropi_maske):
            matris = matris[entropi_maske]
            puanlar = puanlar[entropi_maske]
            log_olasilik = log_olasilik[entropi_maske]

    if len(matris) == 0:
        return np.empty((0, 15), dtype="<U1"), np.array([]), np.array([])

    # GERÇEK OLASILIK SIRALAMASI (Log-olasilik en yüksekten düşüğe)
    idx = np.argsort(log_olasilik)[::-1]
    return ters[matris[idx]], puanlar[idx], log_olasilik[idx]


def gelismis_garanti_ve_budama_uygula(kolonlar, puanlar, log_olasilik, hedef, max_k=None, akilli_merkez=True, min_fark=1):
    """
    Ağırlıklı Küme Kapsama (Weighted Greedy Set-Cover) Algoritması:
    Daha az kolonla daha geniş kombinasyon uzayını kapatır.
    """
    if len(kolonlar) == 0:
        return np.empty((0, 15), dtype="<U1"), np.array([]), 0.0

    mat = np.zeros(kolonlar.shape, dtype=np.int8)
    mat[kolonlar == "X"] = 1
    mat[kolonlar == "2"] = 2

    gercek_olasilik_agirligi = np.exp(log_olasilik - np.max(log_olasilik))

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
                # Set-Cover: En çok kapsanmamış olasılık kütlesini tek seferde kapatan merkezi seçer
                aday_havuzu = aktif_indeksler[:min(120, len(aktif_indeksler))]
                orneklem = aktif_indeksler[:min(3500, len(aktif_indeksler))]
                mesafe_mat = np.sum(mat[aday_havuzu, None, :] != mat[None, orneklem, :], axis=2)
                kapsanan_kutle = np.dot((mesafe_mat <= fark).astype(np.float32), gercek_olasilik_agirligi[orneklem])
                m_idx = int(aday_havuzu[int(np.argmax(kapsanan_kutle))])
            else:
                m_idx = int(aktif_indeksler[0])

            nihai.append(m_idx)
            mesafeler = np.sum(mat[aktif_indeksler] != mat[m_idx], axis=1)
            mask[aktif_indeksler[mesafeler <= fark]] = False

        kapsama_orani = float(np.sum(gercek_olasilik_agirligi[~mask]) / np.sum(gercek_olasilik_agirligi) * 100)

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
    if len(kuponlar) == 0:
        return {"15_oran": 0.0, "14_arti_oran": 0.0, "12_arti_oran": 0.0}
    k_num = np.zeros(kuponlar.shape, dtype=np.int8)
    k_num[kuponlar == "X"] = 1
    k_num[kuponlar == "2"] = 2

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
    "🎛️ 1. Gelişmiş Maç Kontrol Paneli & Kupon Üretimi",
    "📡 2. Canlı Kupon & İkramiye Takibi",
    "🤖 3. Otomatik Kupon Yatırma Botu"
])

# ------------------------------------------------------------------------------
# SEKME 1: YENİLENMİŞ MAÇ KONTROL PANELİ VE MALİYET DÜŞÜRÜCÜ MOTOR
# ------------------------------------------------------------------------------
with tab_uretim:
    if not api_key:
        st.info("👈 Başlamak için sol menüden **API-Football Anahtarınızı** girin.")
    else:
        acik_kal = st.session_state.analiz_verisi is None
        with st.expander("⚡ ADIM 1: Bülten Maçlarını Seçin veya Yapıştırın (Önbellek Korumalı)", expanded=acik_kal):
            bugun = datetime.now().date()
            varsayilan_bitis = bugun + timedelta(days=3)

            c_ust1, c_ust2, c_ust3, c_ust4 = st.columns([1.5, 1.1, 1.4, 0.8])
            with c_ust1:
                tarih_araligi = st.date_input("📅 Bülten Günleri:", value=(bugun, varsayilan_bitis))
            with c_ust2:
                st.write("")
                sadece_toto = st.checkbox("Sadece Popüler Ligler", value=True)
            with c_ust3:
                st.write("")
                if st.button("📥 Seçili Günlerin Maçlarını Yükle", type="primary", use_container_width=True):
                    if isinstance(tarih_araligi, tuple) and len(tarih_araligi) == 2:
                        st.session_state.mac_listesi = tarih_araligi_maclarini_getir(
                            tarih_araligi[0], tarih_araligi[1], api_key, sadece_toto
                        )
                    else:
                        st.warning("Lütfen başlangıç ve bitiş tarihini birlikte seçin.")
            with c_ust4:
                st.write("")
                if st.button("🗑️ Sıfırla", use_container_width=True):
                    st.session_state.mac_listesi = []
                    st.session_state.secilen_15_mac = []
                    st.session_state.analiz_verisi = None
                    st.session_state.tablo_df = None
                    st.rerun()

            if st.session_state.mac_listesi:
                opsiyon_haritasi = {m["label"]: m for m in st.session_state.mac_listesi}
                col_sol, col_sag = st.columns([1.2, 2.2])
                with col_sol:
                    yapistirilan = st.text_area(
                        "📋 Hızlı Eşleştir (Nesine/Bilyoner/Misli'den 15 maçı yapıştırın):",
                        placeholder="1. Galatasaray - Fenerbahçe\n2. Beşiktaş - Trabzonspor...",
                        height=115
                    )
                    if st.button("🪄 Metinden Otomatik Eşleştir", use_container_width=True) and yapistirilan.strip():
                        bulunanlar = bulten_metni_eslestir(yapistirilan, st.session_state.mac_listesi)
                        if bulunanlar:
                            st.session_state.secilen_15_mac = bulunanlar
                            st.toast(f"✅ {len(bulunanlar)} maç sırasıyla eşleştirildi!")
                            st.rerun()
                        else:
                            st.warning("⚠️ Eşleşme bulunamadı. Sağdaki kutudan aratarak seçebilirsiniz.")

                with col_sag:
                    varsayilan_secimler = [m["label"] for m in st.session_state.secilen_15_mac if m["label"] in opsiyon_haritasi]
                    secilen_etiketler = st.multiselect(
                        f"🎯 15 Bülten Maçı ({len(st.session_state.mac_listesi)} maç bulundu):",
                        options=list(opsiyon_haritasi.keys()),
                        default=varsayilan_secimler,
                        max_selections=15,
                        placeholder="Takım veya lig adı yazın..."
                    )
                    st.session_state.secilen_15_mac = [opsiyon_haritasi[e] for e in secilen_etiketler]

                    s_sayi = len(st.session_state.secilen_15_mac)
                    b_col1, b_col2 = st.columns([2, 1.2])
                    with b_col1:
                        if s_sayi == 15:
                            st.success("✅ **15 / 15 Maç Hazır!** Analizi başlatabilirsiniz.")
                        else:
                            st.info(f"📌 Şu an **{s_sayi} / 15** maç seçili.")
                    with b_col2:
                        if st.button("🚀 Analizi Başlat", type="primary", disabled=(s_sayi != 15), use_container_width=True):
                            st.session_state.secilen_mac_idleri = [m["id"] for m in st.session_state.secilen_15_mac]
                            st.session_state.analiz_verisi = hibrit_tahminleri_al(st.session_state.secilen_15_mac, api_key)
                            st.session_state.tablo_df = None
                            st.rerun()

        # ======================================================================
        # ADIM 2: YENİ NESİL HIZLI MAÇ KONTROL PANELİ (TOOLBAR + CANLI SAYAÇ)
        # ======================================================================
        if st.session_state.analiz_verisi:
            veriler = st.session_state.analiz_verisi
            if ai_filtre_modu:
                limitler = tam_otonom_analiz(veriler, strateji_modu)
            else:
                limitler = {
                    "1": range_1, "X": range_x, "2": range_2, "puan": range_puan,
                    "surpriz": range_surpriz, "ardisik_1": max_ardisik_1,
                    "ardisik_x": max_ardisik_x, "ardisik_2": max_ardisik_2,
                    "banko_siniri": banko_siniri, "cifte_siniri": cifte_sans_siniri
                }

            if st.session_state.tablo_df is None:
                st.session_state.tablo_df = tablo_verisi_olustur(veriler, limitler, tuzak_koruma, mod="ai")

            # --- HIZLI ŞABLON ARAÇ ÇUBUĞU (TEK TIKLA KOLAY KONTROL) ---
            st.markdown("#### 🎛️ Hızlı Şablon & Maç Kontrol Paneli")
            tb1, tb2, tb3, tb4 = st.columns([1.3, 1.5, 1.2, 2.2])
            with tb1:
                if st.button("🤖 AI İdeal Şablonunu Uygula", use_container_width=True):
                    st.session_state.tablo_df = tablo_verisi_olustur(veriler, limitler, tuzak_koruma, mod="ai")
                    st.rerun()
            with tb2:
                if st.button("⚖️ Ekonomik (4 Banko - 7 Çifte - 4 Kapalı)", use_container_width=True):
                    st.session_state.tablo_df = tablo_verisi_olustur(veriler, limitler, tuzak_koruma, mod="dengeli_4b_7c_4k")
                    st.rerun()
            with tb3:
                if st.button("🔒 Tümünü Favori Banko Yap", use_container_width=True):
                    st.session_state.tablo_df = tablo_verisi_olustur(veriler, limitler, tuzak_koruma, mod="15_banko")
                    st.rerun()
            with tb4:
                st.info("💡 **Tasarruf İpucu:** Çifte/Kapalı açtığınız sağlam favorilere **🌟 G** işareti koyun. Sistem hepsinin aynı anda patladığı çöp kolonları silip **%50+ tasarruf** sağlar!")

            df_edit = st.data_editor(
                st.session_state.tablo_df,
                column_config={
                    "ID": None,
                    "Sıra": st.column_config.NumberColumn("No", min_value=1, max_value=15, step=1, width="small"),
                    "Lig": st.column_config.TextColumn("Lig", width="medium"),
                    "Karşılaşma": st.column_config.TextColumn("Karşılaşma", width="medium"),
                    "1 (%)": st.column_config.ProgressColumn("Ev (1)", format="%%%d", min_value=0, max_value=100),
                    "X (%)": st.column_config.ProgressColumn("Ber (X)", format="%%%d", min_value=0, max_value=100),
                    "2 (%)": st.column_config.ProgressColumn("Dep (2)", format="%%%d", min_value=0, max_value=100),
                    "Analiz": st.column_config.TextColumn("AI Teşhisi", width="small"),
                    "1": st.column_config.CheckboxColumn("1", width="small"),
                    "X": st.column_config.CheckboxColumn("X", width="small"),
                    "2": st.column_config.CheckboxColumn("2", width="small"),
                    "🌟 G": st.column_config.CheckboxColumn("🌟 G (Güvence)", help="Bu maçta sürpriz aradınız ama favorisine de güveniyorsanız işaretleyin.", width="small")
                },
                disabled=["Lig", "Karşılaşma", "1 (%)", "X (%)", "2 (%)", "Analiz"],
                hide_index=True,
                use_container_width=True,
                height=565
            )

            sirali = df_edit.sort_values("Sıra").reset_index(drop=True)
            st.session_state.secilen_mac_idleri = [int(x) for x in sirali["ID"].tolist()]

            g_sablon, s_veriler, guvence_indeksleri = [], [], []
            banko_say, cifte_say, kapali_say = 0, 0, 0
            bos_mac_var = False

            for idx_r, r in sirali.iterrows():
                sec = [k for k, b in [("1", r["1"]), ("X", r["X"]), ("2", r["2"])] if b]
                if not sec:
                    bos_mac_var = True
                elif len(sec) == 1:
                    banko_say += 1
                elif len(sec) == 2:
                    cifte_say += 1
                else:
                    kapali_say += 1

                if r["🌟 G"] and len(sec) > 1:
                    guvence_indeksleri.append(idx_r)

                g_sablon.append(sec if sec else ["1"])
                s_veriler.append({"mac": r["Karşılaşma"], "1": int(r["1 (%)"]), "X": int(r["X (%)"]), "2": int(r["2 (%)"])})

            ham_kolon_sayisi = math.prod(len(s) for s in g_sablon)

            # Canlı Şablon Özeti Barı
            st.caption(
                f"📌 **Şablon Özeti:** **{banko_say}** Banko | **{cifte_say}** Çifte Şans | **{kapali_say}** Kapalı (Üçlü) | "
                f"**🌟 {len(guvence_indeksleri)}** Güvence Maçı  ➡️  "
                f"**Ham Kombinasyon:** `{ham_kolon_sayisi:,} Kolon ({ham_kolon_sayisi * kolon_fiyati:,.0f} TL)`"
            )

            if bos_mac_var:
                st.error("⚠️ Her maçta en az 1 tercih (1, X veya 2) işaretli olmalıdır.")
            elif ham_kolon_sayisi > 1_594_323:
                st.error("⚠️ Ham şablon 1.5 milyon kolonu aşıyor! Hızlı hesaplama için lütfen 1-2 Kapalı maçı Çifte Şans veya Banko'ya indirin.")
            else:
                mat, puanlar, log_olasilik = vektorel_filtrele(
                    g_sablon, s_veriler, limitler,
                    guvence_indeksleri=guvence_indeksleri if grup_guvence_aktif else [],
                    max_guvence_hata=grup_max_hata,
                    entropi_aktif=entropi_filtresi
                )
                if len(mat) == 0:
                    st.warning("⚠️ Filtreler tüm kombinasyonları eledi. Sol menüden 'G' hata payını artırın veya farklı bir Strateji seçin.")
                else:
                    garanti, g_puan, kapsama = gelismis_garanti_ve_budama_uygula(
                        mat, puanlar, log_olasilik, garanti_derecesi,
                        max_k=max_kolon_limiti,
                        akilli_merkez=akilli_merkez,
                        min_fark=benzerlik_elemesi
                    )
                    st.session_state.uretilen_kuponlar = garanti
                    mc = monte_carlo_simule_et(garanti, s_veriler)

                    tasarruf_orani = (1.0 - (len(garanti) / max(1, ham_kolon_sayisi))) * 100

                    m1, m2, m3, m4, m5, m6 = st.columns([1, 1.1, 1.1, 1, 1, 1.3])
                    m1.metric("Ham -> Filtreli", f"{len(mat):,}", f"-%{100 - (len(mat)*100/max(1, ham_kolon_sayisi)):.0f} Eleme")
                    m2.metric(f"🎯 {garanti_derecesi} Garantili Net", f"{len(garanti):,} Kolon", f"%{tasarruf_orani:.1f} Tasarruf")
                    m3.metric("Ödenecek Bütçe", f"{len(garanti) * kolon_fiyati:,.0f} TL", f"Ham: {ham_kolon_sayisi * kolon_fiyati:,.0f} TL")
                    m4.metric("🥇 15 Yakalama", f"%{mc['15_oran']:.1f}", f"14+: %{mc['14_arti_oran']:.1f}")
                    m5.metric("💰 İkramiye (12+)", f"%{mc['12_arti_oran']:.1f}", f"Kapsama: %{kapsama:.0f}")
                    with m6:
                        st.write("")
                        st.download_button(
                            "📥 Kuponları İndir (.TXT)",
                            "\n".join([" ".join(k) for k in garanti]),
                            f"spor_toto_v90_{garanti_derecesi}G_{len(garanti)}kolon.txt",
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
            if st.button("🔄 Canlı Skorları API'den Çek (Sadece 1 İstek Harcar)", type="primary", use_container_width=True):
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

                st.markdown(f"### 🏆 Canlı İkramiye Potası ({oynanan} / 15 Maç Tamamlandı)")
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("🥇 15'e Giden", f"{int(np.sum(maks_h == 15)):,}")
                k2.metric("🥈 14'e Giden", f"{int(np.sum(maks_h == 14)):,}")
                k3.metric("🥉 13'e Giden", f"{int(np.sum(maks_h == 13)):,}")
                k4.metric("🎯 12'ye Giden", f"{int(np.sum(maks_h == 12)):,}")

                sirali_idx = np.argsort(maks_h)[::-1][:200]
                st.dataframe(
                    pd.DataFrame([{
                        "Kupon": f"#{i+1}",
                        "Durum": f"🏆 {int(maks_h[i])} Adayı" if maks_h[i] >= 12 else "❌ Elendi",
                        "Doğru": int(dogru[i]),
                        "Hata": int(hata[i]),
                        "Dizilim": " ".join(aktif_k[i])
                    } for i in sirali_idx]),
                    hide_index=True,
                    use_container_width=True,
                    height=440
                )
            else:
                st.info("👈 Sol tablodan maç sonuçlarını seçtiğiniz anda canlı ikramiye potası hesaplanır.")
        else:
            st.info("👈 Takip başlatmak için önce kupon üretin veya kupon dosyası yükleyin.")

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
