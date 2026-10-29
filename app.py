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

st.set_page_config(page_title="Spor Toto AI Pro v10.5 Smart-Eco Syndicate", page_icon="🏆", layout="wide")

# --- KOMPAKT VE MODERN ARAYÜZ CSS ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 3.6rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }
        button[data-baseweb="tab"] {
            font-size: 1rem !important;
            font-weight: 700 !important;
            padding-top: 10px !important;
            padding-bottom: 10px !important;
        }
        div[data-testid="stMetric"] {
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            padding: 8px 12px;
            border-radius: 10px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
            font-weight: 700 !important;
            color: #0f172a;
        }
    </style>
""", unsafe_allow_html=True)

# --- TEK SAYFALIK YAZDIRILABİLİR PDF KILAVUZU HTML ŞABLONU ---
KULLANIM_KILAVUZU_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Spor Toto AI Pro v10.5 - Tek Sayfa Kullanım Kılavuzu</title>
<style>
    @page { size: A4 portrait; margin: 12mm; }
    body { font-family: 'Segoe UI', Arial, sans-serif; color: #0f172a; line-height: 1.38; font-size: 12px; margin: 0; padding: 0; }
    .header { background: #0f172a; color: white; padding: 12px 16px; border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
    .header h1 { margin: 0; font-size: 18px; }
    .header span { font-size: 11px; color: #cbd5e1; }
    .alert { background: #eff6ff; border-left: 4px solid #2563eb; padding: 8px 12px; margin-bottom: 10px; border-radius: 4px; }
    .section { border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px 12px; margin-bottom: 10px; background: #ffffff; }
    .section h2 { margin: 0 0 6px 0; font-size: 14px; color: #1e3a8a; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }
    table { width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 11.5px; }
    th, td { border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; }
    th { background: #f1f5f9; font-weight: 700; }
    .badge { display: inline-block; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 10.5px; background: #dcfce7; color: #166534; }
    .print-btn { background: #dc2626; color: white; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 12px; }
    @media print { .no-print { display: none !important; } }
</style>
</head>
<body>
    <div class="header">
        <div>
            <h1>🏆 Spor Toto AI Pro v10.5 — Tasarruf & Kullanım Kılavuzu</h1>
            <span>Smart-Eco Pareto Kümeleme & EV Optimizasyon Motoru</span>
        </div>
        <button class="print-btn no-print" onclick="window.print()">🖨️ PDF Olarak Kaydet / Yazdır (CTRL+P)</button>
    </div>
    <div class="alert">
        <strong>🌱 Daha Az Kolon ve Maliyet İçin 3 Altın Kural:</strong><br>
        1. Sol menüdeki <strong>"🌱 Akıllı Tasarruf Modu (Pareto Küme Kesme)"</strong> ayarı varsayılan olarak <strong>%88 (Ekonomik)</strong> seçilidir. Bu ayar gereksiz kuyruk kuponlarını keserek <strong>%45 ekstra tasarruf</strong> sağlar.<br>
        2. Tablonun üstündeki <strong>"🌱 Süper Ekonomik (5B-6Ç-4K)"</strong> şablon butonunu kullanırsanız maliyet yarı yarıya düşer.<br>
        3. Net bir bütçeniz varsa (ör. 800 TL = 80 Kolon), sol menüden <strong>"💰 Maksimum Bütçe / Kolon Sınırı"</strong> şalterini açıp 80 yazmanız yeterlidir.
    </div>
</body>
</html>"""

# --- SESSION STATE BAŞLATMA ---
varsayilan_state = {
    "mac_listesi": [],
    "secilen_15_mac": [],
    "analiz_verisi": None,
    "tablo_df": None,
    "secilen_mac_idleri": [],
    "uretilen_kuponlar": None,
    "son_uretim_ozeti": None,
    "canli_sonuclar": ["⏳ Bekliyor"] * 15,
    "canli_skor_metni": ["-"] * 15,
    "kalan_kota": "Bilinmiyor",
    "sema_versiyonu": "10.5"
}
for anahtar, deger in varsayilan_state.items():
    if anahtar not in st.session_state:
        st.session_state[anahtar] = deger

if st.session_state.get("sema_versiyonu") != "10.5":
    st.session_state.uretilen_kuponlar = None
    st.session_state.son_uretim_ozeti = None
    st.session_state.sema_versiyonu = "10.5"

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
# SOL MENÜ: SİSTEM, BÜTÇE VE AKILLI TASARRUF PARAMETRELERİ
# ==============================================================================
with st.sidebar:
    st.markdown("## 🏆 Spor Toto AI v10.5")
    st.caption("Smart-Eco & Precision Syndicate Motoru")

    st.download_button(
        label="📄 Kullanım Kılavuzunu İndir (Tek Sayfa PDF)",
        data=KULLANIM_KILAVUZU_HTML.encode("utf-8"),
        file_name="Spor_Toto_AI_v10_5_Kullanim_Kilavuzu.html",
        mime="text/html",
        use_container_width=True
    )

    api_key = st.text_input("🔑 API-Football Anahtarı:", type="password")
    if api_key:
        st.caption(f"📊 Kalan Günlük API Kotası: **{st.session_state.kalan_kota}**")

    st.markdown("---")
    st.markdown("### 🎯 1. Garanti & Maliyet Tasarrufu")
    garanti_secimi = st.selectbox(
        "Matematiksel Garanti Hedefi:",
        [
            "15 Garanti (Tam Filtreli Sistem)",
            "14 Garanti (1 Maç Hata Payı - %85 Tasarruf)",
            "13 Garanti (2 Maç Hata Payı - %96 Tasarruf)",
            "12 Garanti (3 Maç Hata Payı - %99 Tasarruf)"
        ],
        index=2
    )
    garanti_derecesi = int(garanti_secimi.split()[0])

    tasarruf_profili = st.select_slider(
        "🌱 Akıllı Tasarruf Modu (Pareto Kapsama):",
        options=[
            "🔥 Süper Tasarruf (%80 Kütle - En Az Kolon)",
            "⚖️ Ekonomik Denge (%88 Kütle - Önerilen)",
            "🛡️ Tam Kapsama (%100 Kütle - Klasik)"
        ],
        value="⚖️ Ekonomik Denge (%88 Kütle - Önerilen)",
        help="Filtreli havuzun en alttaki düşük olasılıklı sürpriz kuyruğunu keserek isabet gücünü düşürmeden kolon sayısını %35-%55 azaltır."
    )
    if "80" in tasarruf_profili:
        hedef_kapsama_orani = 80.0
    elif "88" in tasarruf_profili:
        hedef_kapsama_orani = 88.0
    else:
        hedef_kapsama_orani = 100.0

    kolon_fiyati = st.number_input("Kolon Birim Fiyatı (TL):", min_value=1.0, value=10.0, step=1.0)

    butce_aktif = st.toggle("💰 Maksimum Bütçe / Kolon Sınırı", value=False)
    if butce_aktif:
        max_kolon_limiti = st.number_input("Maksimum Kolon Adedi:", min_value=1, max_value=50000, value=100, step=10)
        st.caption(f"Maksimum Ödenecek Tutar: **{max_kolon_limiti * kolon_fiyati:,.0f} TL**")
    else:
        max_kolon_limiti = None

    st.markdown("---")
    st.markdown("### 🧠 2. Sendika & Çift Kademeli Şart Motoru")
    strateji_modu = st.radio(
        "Yapay Zeka Oyun Stili:",
        [
            "⚖️ Dengeli (Optimum EV & Olasılık)",
            "🛡️ Favori Ağırlıklı (Daha Az Kolon / Yüksek İsabet)",
            "💎 İkramiye Avcısı (Anti-Public / Yüksek İkramiye)"
        ]
    )

    ev_katsayisi = st.slider(
        "💰 İkramiye Çarpanı (Anti-Public) Ağırlığı:",
        min_value=0.0, max_value=1.0, value=0.20, step=0.05,
        help="0.15 - 0.25 arası gerçek olasılıkları korurken balon favorilerden dengeli şekilde kaçınır."
    )

    grup_guvence_aktif = st.toggle("🌟 Çift Kademeli Güvence (G1 & G2) Filtresi", value=True)
    if grup_guvence_aktif:
        otonom_grup_limiti = st.checkbox(
            "🤖 G1/G2 Sınırlarını Otomatik Ölçekle",
            value=True
        )
        if not otonom_grup_limiti:
            g1_manuel = st.slider("🌟 G1 (Ağır Favoriler) Min-Maks Hata:", 0, 8, (0, 2))
            g2_manuel = st.slider("🔥 G2 (Plase/Ortada) Min-Maks Sürpriz:", 0, 12, (0, 5))
        else:
            g1_manuel, g2_manuel = None, None
    else:
        otonom_grup_limiti = False
        g1_manuel, g2_manuel = (0, 15), (0, 15)

    st.markdown("---")
    st.markdown("### 🔬 3. İleri Düzey Yapısal Filtreler")
    akilli_merkez = st.toggle("🧮 Olasılık Sadakatli Set-Cover Kümeleme", value=True)
    homojen_bulten = st.toggle("⚖️ Alt/Üst Bülten Homojenlik Filtresi", value=True)
    entropi_filtresi = st.toggle("🌀 Yapay/Simetrik Dizilim Elemesi", value=True)
    tuzak_koruma = st.toggle("🚨 Kırılgan Halk Tuzaklarını Çifteye Al", value=True)
    benzerlik_elemesi = st.select_slider("🔍 Kuponlar Arası Min. Farklı Maç (Hamming):", options=[1, 2, 3, 4], value=1)
    ai_filtre_modu = st.toggle("🤖 Şablon-Duyarlı Otonom İstatistik Sınırları", value=True)

    if not ai_filtre_modu:
        with st.expander("⚙️ Manuel Filtre Ayarları"):
            range_1 = st.slider("Ev Sahibi (1) Adedi", 0, 15, (3, 10))
            range_x = st.slider("Beraberlik (X) Adedi", 0, 15, (1, 7))
            range_2 = st.slider("Deplasman (2) Adedi", 0, 15, (1, 8))
            range_puan = st.slider("Toplam Yüzde Puan Aralığı", 300, 1200, (480, 950))
            range_surpriz = st.slider("Sürpriz Sayısı (<%26)", 0, 10, (0, 6))
            max_ardisik_1 = st.slider("Üst Üste Maks. '1'", 2, 12, 6)
            max_ardisik_x = st.slider("Üst Üste Maks. 'X'", 2, 10, 3)
            max_ardisik_2 = st.slider("Üst Üste Maks. '2'", 2, 10, 4)
            banko_siniri = st.number_input("Banko Sınırı (%)", 35, 95, 58)
            cifte_sans_siniri = st.number_input("Çifte Şans Sınırı (%)", 30, 80, 42)


# ==============================================================================
# API VE METİN EŞLEŞTİRME MOTORU
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
    w1, wx, w2 = (p1 ** 1.38), (px_val ** 1.08), (p2 ** 1.35)
    t = w1 + wx + w2
    h1 = max(1, int(round(w1 * 100 / t)))
    hx = max(1, int(round(wx * 100 / t)))
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

    ham_1 = ((odds_1 * 0.72) + (ai_1 * 0.28)) if odds_1 is not None else ai_1
    ham_x = ((odds_x * 0.72) + (ai_x * 0.28)) if odds_x is not None else ai_x
    ham_2 = ((odds_2 * 0.72) + (ai_2 * 0.28)) if odds_2 is not None else ai_2

    return olasilik_yumusat(ham_1, ham_x, ham_2)


def hibrit_tahminleri_al(secilen_maclar, api_key):
    sonuclar = []
    progress = st.progress(0, text="Maç analizleri hesaplanıyor...")
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
            "h1": h1,
            "hX": hx,
            "h2": h2,
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
# v10.5 SMART-ECO FİLTRE VE PARETO SET-COVER KÜMELEME MOTORU
# ==============================================================================
def akilli_cifte_sec(v):
    s = sorted([(v["1"], "1"), (v["X"], "X"), (v["2"], "2")], reverse=True)
    en_b_oran, en_b_secim = s[0][0], s[0][1]
    ikinci_oran, ikinci_secim = s[1][0], s[1][1]

    if {en_b_secim, ikinci_secim} == {"1", "2"} and v["X"] >= 28 and (en_b_oran - ikinci_oran) >= 7:
        return [en_b_secim, "X"]
    return [en_b_secim, ikinci_secim]


def tam_otonom_analiz(mac_verileri, strateji, aktif_sablon=None):
    en_yuksek = [max(v["1"], v["X"], v["2"]) for v in mac_verileri]
    hz = float(np.mean(en_yuksek))

    if "Favori" in strateji:
        ai_banko, ai_cifte = max(50, int(hz + 2)), max(35, int(hz - 9))
    elif "İkramiye" in strateji:
        ai_banko, ai_cifte = max(58, int(hz + 8)), max(40, int(hz - 4))
    else:
        ai_banko, ai_cifte = max(54, int(hz + 5)), max(37, int(hz - 7))

    if aktif_sablon is None:
        exp_1 = sum(v["1"] / 100.0 for v in mac_verileri)
        exp_x = sum(v["X"] / 100.0 for v in mac_verileri)
        exp_2 = sum(v["2"] / 100.0 for v in mac_verileri)
        min_p = sum(min(v["1"], v["X"], v["2"]) for v in mac_verileri)
        max_p = sum(max(v["1"], v["X"], v["2"]) for v in mac_verileri)
        zorunlu_ard_1, zorunlu_ard_x, zorunlu_ard_2 = 4, 2, 3
        aralik_1 = (max(0, int(round(exp_1)) - 4), min(15, int(round(exp_1)) + 5))
        aralik_x = (max(0, int(round(exp_x)) - 3), min(15, int(round(exp_x)) + 4))
        aralik_2 = (max(0, int(round(exp_2)) - 4), min(15, int(round(exp_2)) + 5))
    else:
        banko_1 = sum(1 for s in aktif_sablon if s == ["1"])
        acik_1 = sum(1 for s in aktif_sablon if "1" in s)
        banko_x = sum(1 for s in aktif_sablon if s == ["X"])
        acik_x = sum(1 for s in aktif_sablon if "X" in s)
        banko_2 = sum(1 for s in aktif_sablon if s == ["2"])
        acik_2 = sum(1 for s in aktif_sablon if "2" in s)

        exp_1 = sum((v["1"] / sum(v[k] for k in s)) for v, s in zip(mac_verileri, aktif_sablon) if "1" in s)
        exp_x = sum((v["X"] / sum(v[k] for k in s)) for v, s in zip(mac_verileri, aktif_sablon) if "X" in s)
        exp_2 = sum((v["2"] / sum(v[k] for k in s)) for v, s in zip(mac_verileri, aktif_sablon) if "2" in s)

        aralik_1 = (max(banko_1, int(math.floor(exp_1)) - 3), min(acik_1, int(math.ceil(exp_1)) + 4))
        aralik_x = (max(banko_x, max(0, int(math.floor(exp_x)) - 2)), min(acik_x, int(math.ceil(exp_x)) + 3))
        aralik_2 = (max(banko_2, int(math.floor(exp_2)) - 3), min(acik_2, int(math.ceil(exp_2)) + 4))

        min_p = sum(min(v[k] for k in s) for v, s in zip(mac_verileri, aktif_sablon))
        max_p = sum(max(v[k] for k in s) for v, s in zip(mac_verileri, aktif_sablon))

        # DÜZELTME: 2. ve 3. maçtaki gibi %38-%39'luk 1-X favorilerinin ardışık filtreye
        # takılıp zorla X'e dönmesini önlemek için şablondaki tüm favori zincirini ölçer!
        def maks_dogal_ardisik(hedef_harf):
            en_uzun, mevcut = 0, 0
            for v, s in zip(mac_verileri, aktif_sablon):
                en_iyi_tercih = max(s, key=lambda k: v[k])
                if s == [hedef_harf] or (hedef_harf in s and en_iyi_tercih == hedef_harf):
                    mevcut += 1
                    en_uzun = max(en_uzun, mevcut)
                else:
                    mevcut = 0
            return en_uzun

        zorunlu_ard_1 = maks_dogal_ardisik("1")
        zorunlu_ard_x = maks_dogal_ardisik("X")
        zorunlu_ard_2 = maks_dogal_ardisik("2")

    pf = max(15, max_p - min_p)
    if "Favori" in strateji:
        alt_puan, ust_puan = int(min_p + (pf * 0.45)), int(max_p + 5)
        surpriz_aralik = (0, 3)
    elif "İkramiye" in strateji:
        alt_puan, ust_puan = int(min_p + (pf * 0.15)), int(min_p + (pf * 0.88))
        surpriz_aralik = (1, 7)
    else:
        alt_puan, ust_puan = int(min_p + (pf * 0.30)), int(max_p + 5)
        surpriz_aralik = (0, 5)

    return {
        "1": aralik_1,
        "X": aralik_x,
        "2": aralik_2,
        "puan": (alt_puan, ust_puan),
        "surpriz": surpriz_aralik,
        "ardisik_1": max(4, zorunlu_ard_1),
        "ardisik_x": max(3, zorunlu_ard_x),
        "ardisik_2": max(4, zorunlu_ard_2),
        "banko_siniri": ai_banko,
        "cifte_siniri": ai_cifte,
        "zorluk_skoru": hz
    }


def tablo_verisi_olustur(veriler, limitler, tuzak_aktif=True, mod="ai"):
    satirlar = []
    tum_sirali = sorted(
        [m["id"] for m in veriler],
        key=lambda x: max(
            next(item for item in veriler if item["id"] == x)["1"],
            next(item for item in veriler if item["id"] == x)["X"],
            next(item for item in veriler if item["id"] == x)["2"]
        ),
        reverse=True
    )

    for v in veriler:
        s = sorted([(v["1"], "1"), (v["X"], "X"), (v["2"], "2")], reverse=True)
        en_b_oran, en_b_secim = s[0][0], s[0][1]
        cifte_secim = akilli_cifte_sec(v)
        sira_idx = tum_sirali.index(v["id"])

        kirilgan_tuzak_mi = (44 <= en_b_oran <= 56) and (v.get("tuzak_farki", 0) >= 10)

        if mod == "15_banko":
            secim = [en_b_secim]
            g1, g2 = False, False
        elif mod == "super_eko_5b_6c_4k":
            if sira_idx < 5:
                secim = [en_b_secim]
                g1, g2 = False, False
            elif sira_idx < 11:
                secim = cifte_secim
                g1 = True if sira_idx < 8 else False
                g2 = True if sira_idx >= 8 else False
            else:
                secim = ["1", "X", "2"]
                g1, g2 = False, True
        elif mod == "dengeli_4b_7c_4k":
            if sira_idx < 4:
                secim = [en_b_secim]
                g1, g2 = False, False
            elif sira_idx < 11:
                secim = cifte_secim
                g1 = True if sira_idx < 8 else False
                g2 = True if sira_idx >= 8 else False
            else:
                secim = ["1", "X", "2"]
                g1, g2 = False, True
        elif mod == "sendika_3b_6c_6k":
            if sira_idx < 3:
                secim = [en_b_secim]
                g1, g2 = False, False
            elif sira_idx < 9:
                secim = cifte_secim
                g1 = True if sira_idx < 6 else False
                g2 = True if sira_idx >= 6 else False
            else:
                secim = ["1", "X", "2"]
                g1, g2 = False, True
        else:
            if en_b_oran >= 56 or sira_idx < 4:
                secim = [en_b_secim]
                g1, g2 = False, False
            elif (en_b_oran >= limitler["cifte_siniri"] or sira_idx < 11) and not (tuzak_aktif and kirilgan_tuzak_mi and sira_idx >= 11):
                secim = cifte_secim
                g1 = True if en_b_oran >= 45 else False
                g2 = True if en_b_oran < 45 else False
            else:
                secim = ["1", "X", "2"]
                g1, g2 = False, True

        if en_b_oran >= 56:
            teshis = "🔒 Net Banko"
        elif kirilgan_tuzak_mi:
            teshis = "🚨 Halk Tuzağı"
        elif en_b_oran >= 43:
            teshis = "⚡ Plase"
        else:
            teshis = "💣 Cadı Kazanı"

        satirlar.append({
            "Sıra": v["bulten_no"],
            "ID": v["id"],
            "Lig": v.get("lig", "-"),
            "Karşılaşma": v["mac"],
            "1 (%)": v["1"],
            "X (%)": v["X"],
            "2 (%)": v["2"],
            "Halk (%)": v.get("halk_favori", en_b_oran),
            "Analiz": teshis,
            "1": "1" in secim,
            "X": "X" in secim,
            "2": "2" in secim,
            "🌟 G1": g1,
            "🔥 G2": g2
        })
    return pd.DataFrame(satirlar)


def vektorel_filtrele(
    sablon, mac_verileri, limitler,
    g1_indeksleri, g1_aralik,
    g2_indeksleri, g2_aralik,
    ev_agirligi=0.20,
    entropi_aktif=True,
    homojen_aktif=True
):
    harita = {"1": 0, "X": 1, "2": 2}
    ters = np.array(["1", "X", "2"])
    grids = np.meshgrid(*[[harita[s] for s in m] for m in sablon], indexing="ij")
    ham_matris = np.stack(grids, axis=-1).reshape(-1, 15).astype(np.int8)
    matris = ham_matris

    oran_mat = np.array([[v["1"], v["X"], v["2"]] for v in mac_verileri], dtype=np.float32)
    halk_mat = np.array([[v["h1"], v["hX"], v["h2"]] for v in mac_verileri], dtype=np.float32)
    en_yuksek_oranlar = np.max(oran_mat, axis=1)

    c1 = np.sum(matris == 0, axis=1)
    cx = np.sum(matris == 1, axis=1)
    c2 = np.sum(matris == 2, axis=1)
    maske_1x2 = (
        (c1 >= limitler["1"][0]) & (c1 <= limitler["1"][1]) &
        (cx >= limitler["X"][0]) & (cx <= limitler["X"][1]) &
        (c2 >= limitler["2"][0]) & (c2 <= limitler["2"][1])
    )
    if np.any(maske_1x2):
        matris = matris[maske_1x2]

    if len(g1_indeksleri) > 0 and len(matris) > 0:
        g1_idx = np.array(g1_indeksleri, dtype=int)
        secilen_g1_oran = oran_mat[g1_idx, matris[:, g1_idx]]
        g1_hatalar = np.sum((en_yuksek_oranlar[g1_idx] - secilen_g1_oran) > 4.0, axis=1)
        m_g1 = (g1_hatalar >= g1_aralik[0]) & (g1_hatalar <= g1_aralik[1])
        if np.any(m_g1):
            matris = matris[m_g1]

    if len(g2_indeksleri) > 0 and len(matris) > 0:
        g2_idx = np.array(g2_indeksleri, dtype=int)
        secilen_g2_oran = oran_mat[g2_idx, matris[:, g2_idx]]
        # Sadece en yüksek orandan > %6 düşük olan tercihleri gerçek sürpriz sayar (2. ve 3. maçtaki X şişmesini önler)
        g2_surprizler = np.sum((en_yuksek_oranlar[g2_idx] - secilen_g2_oran) > 6.0, axis=1)
        m_g2 = (g2_surprizler >= g2_aralik[0]) & (g2_surprizler <= g2_aralik[1])
        if np.any(m_g2):
            matris = matris[m_g2]

    secilen_oranlar = oran_mat[np.arange(15), matris]
    puanlar = np.sum(secilen_oranlar, axis=1)
    surpriz_sayisi = np.sum(secilen_oranlar < 26, axis=1)

    maske_puan = (
        (puanlar >= limitler["puan"][0]) & (puanlar <= limitler["puan"][1]) &
        (surpriz_sayisi >= limitler["surpriz"][0]) & (surpriz_sayisi <= limitler["surpriz"][1])
    )
    if np.any(maske_puan):
        matris = matris[maske_puan]

    for deger, anahtar in [(0, "ardisik_1"), (1, "ardisik_x"), (2, "ardisik_2")]:
        max_ard = int(limitler[anahtar])
        if 1 <= max_ard < 15 and len(matris) > 0:
            pencereler = sliding_window_view(matris == deger, window_shape=max_ard + 1, axis=1)
            ardisik_ihlal = np.any(np.all(pencereler, axis=2), axis=1)
            if np.any(~ardisik_ihlal):
                matris = matris[~ardisik_ihlal]

    if homojen_aktif and len(matris) > 0:
        sec_oran_aktif = oran_mat[np.arange(15), matris]
        ilk_yari_surpriz = np.sum(sec_oran_aktif[:, :7] < 26, axis=1)
        son_yari_surpriz = np.sum(sec_oran_aktif[:, 7:] < 26, axis=1)
        homojen_maske = (ilk_yari_surpriz <= 4) & (son_yari_surpriz <= 4)
        if np.any(homojen_maske):
            matris = matris[homojen_maske]

    if entropi_aktif and len(matris) > 0:
        gecis_sayisi = np.sum(matris[:, 1:] != matris[:, :-1], axis=1)
        periyot_3 = np.sum(matris[:, 3:] == matris[:, :-3], axis=1)
        entropi_maske = (gecis_sayisi >= 4) & (gecis_sayisi <= 13) & (periyot_3 <= 10)
        if np.any(entropi_maske):
            matris = matris[entropi_maske]

    secilen_oranlar = oran_mat[np.arange(15), matris]
    secilen_halk = halk_mat[np.arange(15), matris]
    puanlar = np.sum(secilen_oranlar, axis=1)

    log_gercek = np.sum(np.log(np.maximum(secilen_oranlar, 1.0) / 100.0), axis=1)
    log_halk = np.sum(np.log(np.maximum(secilen_halk, 1.0) / 100.0), axis=1)
    kompozit_skor = log_gercek - (ev_agirligi * 0.22 * log_halk)

    idx = np.argsort(kompozit_skor)[::-1]
    return ters[matris[idx]], puanlar[idx], kompozit_skor[idx]


def gelismis_garanti_ve_budama_uygula(
    kolonlar, puanlar, kompozit_skor, hedef,
    max_k=None, akilli_merkez=True, min_fark=1, hedef_kapsama=88.0
):
    """
    v10.5 SMART-ECO PARETO SET-COVER MOTORU:
    - Olasılık kütlesinin hedef_kapsama (%80 veya %88) oranına ulaştığında durur;
      düşük olasılıklı kuyruk için fazladan 70-80 kolon harcamaz!
    """
    if len(kolonlar) == 0:
        return np.empty((0, 15), dtype="<U1"), np.array([]), 0.0

    if hedef == 15:
        nihai = list(range(len(kolonlar)))
        if max_k and len(nihai) > max_k:
            nihai = nihai[:max_k]
        return kolonlar[nihai], puanlar[nihai], 100.0

    MAX_HAVUZ = 6000
    if len(kolonlar) > MAX_HAVUZ:
        kolonlar = kolonlar[:MAX_HAVUZ]
        puanlar = puanlar[:MAX_HAVUZ]
        kompozit_skor = kompozit_skor[:MAX_HAVUZ]

    N = len(kolonlar)
    mat = np.zeros((N, 15), dtype=np.int8)
    mat[kolonlar == "X"] = 1
    mat[kolonlar == "2"] = 2

    one_hot = np.zeros((N, 45), dtype=np.float32)
    satir_idx = np.arange(N)[:, None]
    sutun_ofset = np.arange(15)[None, :] * 3
    one_hot[satir_idx, sutun_ofset + mat] = 1.0

    agirlik = np.exp((kompozit_skor - np.max(kompozit_skor)) * 0.90).astype(np.float32)
    toplam_agirlik = float(np.sum(agirlik))
    esik_eslesme = float(hedef)

    mask = np.ones(N, dtype=bool)
    nihai = []
    kapsama_orani = 0.0

    while np.any(mask):
        if max_k and len(nihai) >= max_k:
            break
        if kapsama_orani >= hedef_kapsama:
            break

        aktif_indeksler = np.where(mask)[0]
        if akilli_merkez and len(aktif_indeksler) > 1:
            aday_say = min(55, len(aktif_indeksler))
            ornek_say = min(1000, len(aktif_indeksler))

            aday_idx = aktif_indeksler[:aday_say]
            ornek_idx = aktif_indeksler[:ornek_say]

            eslesme_mat = one_hot[aday_idx] @ one_hot[ornek_idx].T
            kapsama_mat = (eslesme_mat >= esik_eslesme).astype(np.float32)
            kapsanan_kutle = (kapsama_mat @ agirlik[ornek_idx]) * (agirlik[aday_idx] ** 0.65)
            m_idx = int(aday_idx[int(np.argmax(kapsanan_kutle))])
        else:
            m_idx = int(aktif_indeksler[0])

        nihai.append(m_idx)
        eslesmeler = one_hot[aktif_indeksler] @ one_hot[m_idx]
        mask[aktif_indeksler[eslesmeler >= esik_eslesme]] = False
        kapsama_orani = float(np.sum(agirlik[~mask]) / toplam_agirlik * 100.0)

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


def monte_carlo_simule_et(kuponlar, veriler, sablon):
    if len(kuponlar) == 0:
        return {"sablon_14_arti": 0.0, "sablon_15": 0.0, "genel_12_arti": 0.0, "ikramiye_endeksi": 0.0}

    harita = {"1": 0, "X": 1, "2": 2}
    k_num = np.zeros(kuponlar.shape, dtype=np.int8)
    k_num[kuponlar == "X"] = 1
    k_num[kuponlar == "2"] = 2

    rng = np.random.default_rng(42)
    N_SIM = 2500
    sim_genel = np.zeros((N_SIM, 15), dtype=np.int8)
    sim_sablon = np.zeros((N_SIM, 15), dtype=np.int8)

    for idx, (v, s) in enumerate(zip(veriler, sablon)):
        o_genel = np.array([v["1"], v["X"], v["2"]], dtype=float)
        sim_genel[:, idx] = rng.choice([0, 1, 2], size=N_SIM, p=o_genel / o_genel.sum())

        s_kodlar = [harita[k] for k in s]
        o_sablon = np.array([v[k] for k in s], dtype=float)
        sim_sablon[:, idx] = rng.choice(s_kodlar, size=N_SIM, p=o_sablon / o_sablon.sum())

    kupon_oh = np.zeros((len(kuponlar), 45), dtype=np.float32)
    kupon_oh[np.arange(len(kuponlar))[:, None], np.arange(15)[None, :] * 3 + k_num] = 1.0

    sim_genel_oh = np.zeros((N_SIM, 45), dtype=np.float32)
    sim_genel_oh[np.arange(N_SIM)[:, None], np.arange(15)[None, :] * 3 + sim_genel] = 1.0
    derece_genel = np.max(sim_genel_oh @ kupon_oh.T, axis=1)

    sim_sablon_oh = np.zeros((N_SIM, 45), dtype=np.float32)
    sim_sablon_oh[np.arange(N_SIM)[:, None], np.arange(15)[None, :] * 3 + sim_sablon] = 1.0
    derece_sablon = np.max(sim_sablon_oh @ kupon_oh.T, axis=1)

    halk_mat = np.array([[v["h1"], v["hX"], v["h2"]] for v in veriler], dtype=float)
    secilen_halk_ort = np.mean(halk_mat[np.arange(15), k_num])
    ikramiye_endeksi = max(10.0, min(99.0, 100.0 - secilen_halk_ort))

    return {
        "sablon_15": float(np.mean(derece_sablon >= 14.9) * 100),
        "sablon_14_arti": float(np.mean(derece_sablon >= 13.9) * 100),
        "genel_12_arti": float(np.mean(derece_genel >= 11.9) * 100),
        "ikramiye_endeksi": float(ikramiye_endeksi)
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
    "🎛️ 1. Profesyonel Sendika Masası & Kupon Üretimi",
    "📡 2. Canlı Kupon, Kırılma & Sigorta (Hedge) Takibi",
    "🤖 3. Otomatik Kupon Yatırma & Dışa Aktarım"
])

# ------------------------------------------------------------------------------
# SEKME 1: PROFESYONEL MAÇ KONTROL PANELİ VE SENDİKA MOTORU
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
                    st.session_state.uretilen_kuponlar = None
                    st.session_state.son_uretim_ozeti = None
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
                            st.session_state.uretilen_kuponlar = None
                            st.session_state.son_uretim_ozeti = None
                            st.rerun()

        # ======================================================================
        # ADIM 2: PROFESYONEL SENDİKA KONTROL PANELİ (v10.5 SMART-ECO)
        # ======================================================================
        if st.session_state.analiz_verisi:
            veriler = st.session_state.analiz_verisi
            on_limitler = tam_otonom_analiz(veriler, strateji_modu)

            if st.session_state.tablo_df is None:
                st.session_state.tablo_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="ai")

            st.markdown("#### 🎛️ Profesyonel Şablon & Çift Kademeli Güvence (G1 / G2) Masası")
            tb1, tb2, tb3, tb4 = st.columns([1.25, 1.35, 1.25, 1.0])
            with tb1:
                if st.button("🌱 Süper Ekonomik (5B-6Ç-4K)", use_container_width=True):
                    st.session_state.tablo_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="super_eko_5b_6c_4k")
                    st.session_state.uretilen_kuponlar = None
                    st.rerun()
            with tb2:
                if st.button("🤖 AI Dengeli (4B-7Ç-4K)", use_container_width=True):
                    st.session_state.tablo_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="ai")
                    st.session_state.uretilen_kuponlar = None
                    st.rerun()
            with tb3:
                if st.button("💎 Sendika (3B-6Ç-6K)", use_container_width=True):
                    st.session_state.tablo_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="sendika_3b_6c_6k")
                    st.session_state.uretilen_kuponlar = None
                    st.rerun()
            with tb4:
                if st.button("🔒 15 Banko", use_container_width=True):
                    st.session_state.tablo_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="15_banko")
                    st.session_state.uretilen_kuponlar = None
                    st.rerun()

            df_edit = st.data_editor(
                st.session_state.tablo_df,
                column_config={
                    "ID": None,
                    "Sıra": st.column_config.NumberColumn("No", min_value=1, max_value=15, step=1, width="small"),
                    "Lig": st.column_config.TextColumn("Lig", width="small"),
                    "Karşılaşma": st.column_config.TextColumn("Karşılaşma", width="medium"),
                    "1 (%)": st.column_config.NumberColumn("Ev %", min_value=1, max_value=98, step=1, format="%%%d", width="small"),
                    "X (%)": st.column_config.NumberColumn("Ber %", min_value=1, max_value=98, step=1, format="%%%d", width="small"),
                    "2 (%)": st.column_config.NumberColumn("Dep %", min_value=1, max_value=98, step=1, format="%%%d", width="small"),
                    "Halk (%)": st.column_config.ProgressColumn("Halk Yük.", format="%%%d", min_value=0, max_value=100, width="small"),
                    "Analiz": st.column_config.TextColumn("Teşhis", width="small"),
                    "1": st.column_config.CheckboxColumn("1", width="small"),
                    "X": st.column_config.CheckboxColumn("X", width="small"),
                    "2": st.column_config.CheckboxColumn("2", width="small"),
                    "🌟 G1": st.column_config.CheckboxColumn("🌟 G1", help="Ağır Favori Güvencesi", width="small"),
                    "🔥 G2": st.column_config.CheckboxColumn("🔥 G2", help="Plase/Sürpriz Grubu", width="small")
                },
                disabled=["Lig", "Karşılaşma", "Halk (%)", "Analiz"],
                hide_index=True,
                use_container_width=True,
                height=560
            )

            sirali = df_edit.sort_values("Sıra").reset_index(drop=True)
            st.session_state.secilen_mac_idleri = [int(x) for x in sirali["ID"].tolist()]

            g_sablon, s_veriler, g1_indeksleri, g2_indeksleri = [], [], [], []
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

                if r["🌟 G1"] and len(sec) > 1:
                    g1_indeksleri.append(idx_r)
                if r["🔥 G2"] and len(sec) > 1:
                    g2_indeksleri.append(idx_r)

                y1, yx, y2 = olasilik_yumusat(r["1 (%)"], r["X (%)"], r["2 (%)"])
                h1, hx, h2 = halk_egilimi_simule_et(y1, yx, y2)

                g_sablon.append(sec if sec else ["1"])
                s_veriler.append({
                    "mac": r["Karşılaşma"],
                    "1": y1, "X": yx, "2": y2,
                    "h1": h1, "hX": hx, "h2": h2
                })

            if grup_guvence_aktif:
                if otonom_grup_limiti:
                    g1_say = len(g1_indeksleri)
                    g2_say = len(g2_indeksleri)
                    g1_aralik = (0, max(1, int(math.ceil(g1_say * 0.45)))) if g1_say > 0 else (0, 15)
                    g2_aralik = (0, max(2, int(math.ceil(g2_say * 0.65)))) if g2_say > 0 else (0, 15)
                else:
                    g1_aralik, g2_aralik = g1_manuel, g2_manuel
            else:
                g1_aralik, g2_aralik = (0, 15), (0, 15)

            ham_kolon_sayisi = math.prod(len(s) for s in g_sablon)

            col_ozet, col_buton = st.columns([2.2, 1.2])
            with col_ozet:
                st.info(
                    f"📌 **Şablon Özeti:** **{banko_say}** Banko | **{cifte_say}** Çifte | **{kapali_say}** Kapalı | "
                    f"**🌟 G1:** {len(g1_indeksleri)} Maç ({g1_aralik[0]}-{g1_aralik[1]}) | "
                    f"**🔥 G2:** {len(g2_indeksleri)} Maç ({g2_aralik[0]}-{g2_aralik[1]})\n\n"
                    f"🧮 **Ham Kombinasyon:** `{ham_kolon_sayisi:,} Kolon ({ham_kolon_sayisi * kolon_fiyati:,.0f} TL)`"
                )
            with col_buton:
                st.write("")
                uretim_tetikle = st.button(
                    "⚡ FİLTRELİ KUPONLARI ŞİMDİ ÜRET",
                    type="primary",
                    use_container_width=True,
                    disabled=(bos_mac_var or ham_kolon_sayisi > 300_000)
                )

            if bos_mac_var:
                st.error("⚠️ Her maçta en az 1 tercih (1, X veya 2) işaretli olmalıdır.")
            elif ham_kolon_sayisi > 300_000:
                st.warning(
                    "⚠️ **CPU Koruması:** Şablonunuz 300.000 kolonu aşıyor. "
                    "Lütfen yukarıdaki **'🌱 Süper Ekonomik'** veya **'🤖 AI Dengeli'** butonuna basın."
                )

            param_imzasi = f"{garanti_derecesi}_{hedef_kapsama_orani}_{max_kolon_limiti}_{ev_katsayisi}_{strateji_modu}_{benzerlik_elemesi}_{ham_kolon_sayisi}"
            otomatik_yenile = (st.session_state.get("son_param_imzasi") != param_imzasi) and not bos_mac_var and ham_kolon_sayisi <= 100_000

            if uretim_tetikle or otomatik_yenile or (st.session_state.uretilen_kuponlar is None and not bos_mac_var and ham_kolon_sayisi <= 100_000):
                st.session_state.son_param_imzasi = param_imzasi
                if ai_filtre_modu:
                    limitler = tam_otonom_analiz(s_veriler, strateji_modu, aktif_sablon=g_sablon)
                else:
                    limitler = {
                        "1": range_1, "X": range_x, "2": range_2, "puan": range_puan,
                        "surpriz": range_surpriz, "ardisik_1": max_ardisik_1,
                        "ardisik_x": max_ardisik_x, "ardisik_2": max_ardisik_2,
                        "banko_siniri": banko_siniri, "cifte_siniri": cifte_sans_siniri
                    }

                mat, puanlar, kompozit_skor = vektorel_filtrele(
                    g_sablon, s_veriler, limitler,
                    g1_indeksleri=g1_indeksleri if grup_guvence_aktif else [],
                    g1_aralik=g1_aralik,
                    g2_indeksleri=g2_indeksleri if grup_guvence_aktif else [],
                    g2_aralik=g2_aralik,
                    ev_agirligi=ev_katsayisi,
                    entropi_aktif=entropi_filtresi,
                    homojen_aktif=homojen_bulten
                )
                if len(mat) > 0:
                    garanti, g_puan, kapsama = gelismis_garanti_ve_budama_uygula(
                        mat, puanlar, kompozit_skor, garanti_derecesi,
                        max_k=max_kolon_limiti,
                        akilli_merkez=akilli_merkez,
                        min_fark=benzerlik_elemesi,
                        hedef_kapsama=hedef_kapsama_orani
                    )
                    mc = monte_carlo_simule_et(garanti, s_veriler, g_sablon)
                    st.session_state.uretilen_kuponlar = garanti
                    st.session_state.son_uretim_ozeti = {
                        "filtreli_adet": len(mat),
                        "ham_adet": ham_kolon_sayisi,
                        "garanti_derecesi": garanti_derecesi,
                        "kapsama": kapsama,
                        "mc": mc,
                        "s_veriler": s_veriler,
                        "g_sablon": g_sablon
                    }
                else:
                    st.warning("⚠️ Filtreler tüm kombinasyonları eledi. Sol menüden filtreleri esnetin.")

            if st.session_state.uretilen_kuponlar is not None and st.session_state.son_uretim_ozeti is not None:
                garanti = st.session_state.uretilen_kuponlar
                ozet = st.session_state.son_uretim_ozeti
                mc = ozet["mc"]
                ham_k = max(1, ozet["ham_adet"])
                tasarruf_orani = (1.0 - (len(garanti) / ham_k)) * 100

                m1, m2, m3, m4, m5, m6 = st.columns([1, 1.1, 1.1, 1.1, 1.1, 1.1])
                m1.metric("Ham -> Filtreli", f"{ozet['filtreli_adet']:,}", f"-%{100 - (ozet['filtreli_adet']*100/ham_k):.0f} Eleme")
                m2.metric(f"🎯 {ozet['garanti_derecesi']}G Ekonomik Net", f"{len(garanti):,} Kolon", f"%{tasarruf_orani:.1f} Tasarruf")
                m3.metric("Ödenecek Bütçe", f"{len(garanti) * kolon_fiyati:,.0f} TL", f"Kapsama: %{ozet.get('kapsama', 88):.0f}")
                m4.metric("🥇 Şablon İçi 14+ Gücü", f"%{mc['sablon_14_arti']:.1f}", f"Tam 15: %{mc['sablon_15']:.1f}")
                m5.metric("💎 İkramiye Çarpanı", f"{mc['ikramiye_endeksi']:.0f} / 100", f"Genel 12+: %{mc['genel_12_arti']:.1f}")
                with m6:
                    st.write("")
                    st.download_button(
                        "📥 Kuponları İndir (.TXT)",
                        "\n".join([" ".join(k) for k in garanti]),
                        f"spor_toto_v10_5_{ozet['garanti_derecesi']}G_{len(garanti)}kolon.txt",
                        type="primary",
                        use_container_width=True
                    )

                with st.expander("📊 Üretilen Nihai Kuponların Maç Bazlı 1-X-2 Dağılım & Gerçek Olasılık Kontrolü", expanded=True):
                    toplam_k = len(garanti)
                    dagilim_satirlari = []
                    for m_i, v_m in enumerate(ozet["s_veriler"]):
                        sutun = garanti[:, m_i]
                        s1, sx, s2 = int(np.sum(sutun == "1")), int(np.sum(sutun == "X")), int(np.sum(sutun == "2"))
                        dagilim_satirlari.append({
                            "Maç No": m_i + 1,
                            "Karşılaşma": v_m["mac"],
                            "Şablon": "-".join(ozet["g_sablon"][m_i]),
                            "Kuponlarda 1 (%)": f"{s1} (%{s1*100/toplam_k:.0f}) | Model: %{v_m['1']}",
                            "Kuponlarda X (%)": f"{sx} (%{sx*100/toplam_k:.0f}) | Model: %{v_m['X']}",
                            "Kuponlarda 2 (%)": f"{s2} (%{s2*100/toplam_k:.0f}) | Model: %{v_m['2']}"
                        })
                    st.dataframe(pd.DataFrame(dagilim_satirlari), hide_index=True, use_container_width=True)

# ------------------------------------------------------------------------------
# SEKME 2: CANLI KUPON TAKİBİ & SİGORTA (HEDGE) ANALİZİ
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

                en_yuksek_derece = int(np.max(maks_h))
                hedef_kuponlar = aktif_k[maks_h == en_yuksek_derece]
                bekleyen_indeksler = np.where(~mask)[0]

                if len(bekleyen_indeksler) > 0 and len(hedef_kuponlar) > 0:
                    with st.expander(f"🛟 Kalan {len(bekleyen_indeksler)} Maç İçin '{en_yuksek_derece} Bilen' Sigorta (Hedge) Tablosu", expanded=True):
                        hedge_satirlar = []
                        for b_idx in bekleyen_indeksler:
                            sutun_b = hedef_kuponlar[:, b_idx]
                            k_1 = int(np.sum(sutun_b == "1"))
                            k_x = int(np.sum(sutun_b == "X"))
                            k_2 = int(np.sum(sutun_b == "2"))
                            acik_risk = []
                            if k_1 == 0: acik_risk.append("1")
                            if k_x == 0: acik_risk.append("X")
                            if k_2 == 0: acik_risk.append("2")
                            hedge_satirlar.append({
                                "Maç No": b_idx + 1,
                                "Karşılaşma": m_isim[b_idx],
                                "1 Gelirse": f"{k_1} Kupon",
                                "X Gelirse": f"{k_x} Kupon",
                                "2 Gelirse": f"{k_2} Kupon",
                                "Sigorta (Canlı Bahis) Önerisi": f"⚠️ {', '.join(acik_risk)} Sigortalanmalı!" if acik_risk else "✅ Tüm Sonuçlar Kapalı"
                            })
                        st.dataframe(pd.DataFrame(hedge_satirlar), hide_index=True, use_container_width=True)

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
                    height=340
                )
            else:
                st.info("👈 Sol tablodan maç sonuçlarını seçtiğiniz anda canlı ikramiye potası ve sigorta analizi hesaplanır.")
        else:
            st.info("👈 Takip başlatmak için önce kupon üretin veya kupon dosyası yükleyin.")

# ------------------------------------------------------------------------------
# SEKME 3: OTOMATİK YATIRMA VE DIŞA AKTARIM
# ------------------------------------------------------------------------------
with tab_otomasyon:
    st.markdown("### 🤖 Otomatik Kupon Yatırma (Tarayıcı F12 Botu & Excel/CSV)")
    if st.session_state.uretilen_kuponlar is not None and len(st.session_state.uretilen_kuponlar) > 0:
        k_oto = st.session_state.uretilen_kuponlar.tolist()
        c_o1, c_o2 = st.columns([1, 2.5])
        with c_o1:
            boyut = st.number_input("Paket Başına Kolon:", 10, 500, 50, step=10)
            sec_p = st.selectbox("Paket Seç:", [f"Paket {i+1}" for i in range(math.ceil(len(k_oto) / boyut))])
            p_id = int(sec_p.split()[1]) - 1
            sifir_kullan = st.toggle("Beraberliği '0' Olarak Kodla", value=True)

            csv_icerik = "Kupon_No," + ",".join([f"Mac_{i}" for i in range(1, 16)]) + "\n"
            for idx_k, kl in enumerate(k_oto, 1):
                csv_icerik += f"{idx_k}," + ",".join(kl) + "\n"
            st.download_button(
                "📊 Tüm Kuponları Excel/CSV İndir",
                csv_icerik,
                f"spor_toto_v10_5_excel_{len(k_oto)}kolon.csv",
                mime="text/csv",
                use_container_width=True
            )

        with c_o2:
            aktif_paket = [
                ["0" if (s == "X" and sifir_kullan) else s for s in kolon]
                for kolon in k_oto[p_id * boyut : (p_id + 1) * boyut]
            ]
            js_kodu = f"""// 1. Bahis sitesinde Spor Toto sayfasını açıp F12 -> Console sekmesine yapıştırın:
const kuponPaketi = {json.dumps(aktif_paket)};
console.log("✅ Paket yüklendi! Toplam Kolon:", kuponPaketi.length);
window.kolonBas = function(kolonIndex) {{
    const secimler = kuponPaketi[kolonIndex];
    console.log((kolonIndex + 1) + ". Kolon İşaretleniyor:", secimler.join("-"));
}};
window.kolonBas(0);"""
            st.code(js_kodu, language="javascript")
            st.text_area("Hızlı Kopyala-Yapıştır Dizilimi:", value="\n".join(["".join(k) for k in aktif_paket]), height=200)
    else:
        st.info("👈 Önce 1. Sekmeden kupon üretin.")
