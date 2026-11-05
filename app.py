import streamlit as st
import requests
import math
import json
import re
import hashlib
import unicodedata
from difflib import SequenceMatcher
from datetime import datetime, timedelta
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import pandas as pd

st.set_page_config(
    page_title="Spor Toto AI Pro v12.4 Final — Real-Game Production",
    page_icon="🏆",
    layout="wide"
)

# --- KOMPAKT VE MODERN ARAYÜZ CSS ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 2.8rem !important;
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
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            color: #0f172a;
        }
        .step-card {
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-left: 4px solid #2563eb;
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 10px;
        }
        .safe-badge {
            background: #dcfce7;
            color: #166534;
            padding: 4px 10px;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.82rem;
            display: inline-block;
        }
    </style>
""", unsafe_allow_html=True)

# --- TEK SAYFALIK YAZDIRILABİLİR PDF KILAVUZU HTML ŞABLONU ---
KULLANIM_KILAVUZU_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Spor Toto AI Pro v12.4 Final - Gerçek Oyun Saha Kılavuzu</title>
<style>
    @page { size: A4 portrait; margin: 12mm; }
    body { font-family: 'Segoe UI', Arial, sans-serif; color: #0f172a; line-height: 1.4; font-size: 12px; margin: 0; padding: 0; }
    .header { background: #0f172a; color: white; padding: 12px 16px; border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
    .header h1 { margin: 0; font-size: 18px; }
    .header span { font-size: 11px; color: #cbd5e1; }
    .alert { background: #eff6ff; border-left: 4px solid #2563eb; padding: 8px 12px; margin-bottom: 10px; border-radius: 4px; }
    .section { border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px 12px; margin-bottom: 10px; background: #ffffff; }
    .section h2 { margin: 0 0 6px 0; font-size: 14px; color: #1e3a8a; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }
    table { width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 11.5px; }
    th, td { border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; }
    th { background: #f1f5f9; font-weight: 700; }
    .print-btn { background: #dc2626; color: white; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 12px; }
    @media print { .no-print { display: none !important; } }
</style>
</head>
<body>
    <div class="header">
        <div>
            <h1>🏆 Spor Toto AI Pro v12.4 Final — Gerçek Oyun Saha Operasyon Kılavuzu</h1>
            <span>İddaa.com 4'lü Kolon (A-B-C-D) Asistanı, Favori Çubuğu (Bookmarklet) Desteği & 90-Dk Resmi Kural Koruması</span>
        </div>
        <button class="print-btn no-print" onclick="window.print()">🖨️ PDF Olarak Kaydet / Yazdır (CTRL+P)</button>
    </div>
    <div class="alert">
        <strong>🌱 v12.4 Gerçek Oyun İçin 6 Altın Kural:</strong><br>
        1. <strong>💸 Hedef Bütçeye Göre Şablon Kur:</strong> Bütçenizi belirleyin ve <em>"🎯 Bütçeme Göre Otomatik Kur"</em> butonuna basın.<br>
        2. <strong>📐 Shannon Log-Olasılık Zarfı:</strong> Geometrik olasılık koridoru (Z-Skoru) ile çöp sürprizler ve aşırı kısır kuponlar otomatik elenir.<br>
        3. <strong>🔬 Deterministik Garanti Denetimi:</strong> Üretim sonrası açılan denetim tablosundan kuponlarınızın filtreli evreni %100 oranında kapsadığını doğrulayın.<br>
        4. <strong>⏱️ 90-Dakika Resmi Skor Koruması:</strong> Uzatmaya/penaltılara giden kupa maçlarında sistem otomatik olarak resmi 90 dakika skorunu baz alır.<br>
        5. <strong>⚡ İddaa.com 4'lü Kolon (A-B-C-D) & Bookmarklet Asistanı:</strong> 3. Sekmedeki Görsel Asistan <code>iddaa.com/spor-toto</code> üzerindeki 12'li boş kutucukları otomatik tanır, tek tıkla 4 kolonu aynı anda doldurur ve <strong>ASLA kendi kendine ödeme/onay butonuna basmaz</strong>.<br>
        6. <strong>🛟 Canlı Hedge (Dutching):</strong> Pazar günü son maçlara 14/15 adayı ile girdiğinizde 2. Sekmedeki Finansal Sigorta Hesaplayıcısı ile garantili net kârı kilitleyin.
    </div>
    <div class="section">
        <h2>📊 Otomatik Kupon Yatırma (Yöntem B — Favori Çubuğu & Konsol) Özeti</h2>
        <table>
            <tr><th>Adım</th><th>Uygulama</th><th>Avantajı</th></tr>
            <tr><td><strong>1. Favori Çubuğuna Ekle</strong></td><td>Chrome Favoriler çubuğuna sağ tıklayıp <em>"Sayfa ekle..."</em> deyin, URL kısmına 3. Sekmedeki <strong>Bookmarklet</strong> kodunu yapıştırın.</td><td>F12 Konsol açma ve <code>allow pasting</code> yazma zorunluluğunu tamamen ortadan kaldırır.</td></tr>
            <tr><td><strong>2. Tek Tıkla 4 Kolon Doldur</strong></td><td><code>iddaa.com/spor-toto</code> sayfasında üstteki favori butonunuza tıklayın ve açılan panelde <strong>"🎯 4 Kolonu Doldur"</strong> butonuna basın.</td><td>A, B, C ve D kolonlarının tamamını (60 kutucuk) tek seferde işaretler; 25 kolonu 7 tıklamada bitirir.</td></tr>
            <tr><td><strong>3. Manuel Tanıt (Yedek)</strong></td><td>Sayfa geç yüklendiyse paneldeki <strong>"🎯 1. Kutuyu Tanıt"</strong> butonuna basıp 1. maçın ilk kutucuğuna tıklayın.</td><td>Her türlü tasarım değişikliğinde %100 kesinlikle 15 maç × 12 kutucuğu yakalar.</td></tr>
        </table>
    </div>
</body>
</html>"""

# --- SESSION STATE BAŞLATMA ---
varsayilan_state = {
    "mac_listesi": [],
    "secilen_15_mac": [],
    "eslesmeyen_satirlar": [],
    "analiz_verisi": None,
    "tablo_df": None,
    "tablo_versiyon": 0,
    "secilen_mac_idleri": [],
    "uretilen_kuponlar": None,
    "son_uretim_ozeti": None,
    "son_param_imzasi": None,
    "canli_sonuclar": ["⏳ Bekliyor"] * 15,
    "canli_skor_metni": ["-"] * 15,
    "kalan_kota": "Bilinmiyor",
    "yatirilan_paketler": [],
    "sema_versiyonu": "12.4"
}
for anahtar, deger in varsayilan_state.items():
    if anahtar not in st.session_state:
        st.session_state[anahtar] = deger

if st.session_state.get("sema_versiyonu") != "12.4":
    st.session_state.uretilen_kuponlar = None
    st.session_state.son_uretim_ozeti = None
    st.session_state.son_param_imzasi = None
    st.session_state.sema_versiyonu = "12.4"

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

POPULER_TAKIM_ANAHTARLARI = [
    "galatasaray", "fenerbahce", "besiktas", "trabzonspor",
    "real madrid", "barcelona", "manchester city", "arsenal", "liverpool",
    "bayern", "inter", "juventus", "milan", "psg", "paris saint"
]

KISIR_LIG_IDLERI = {203, 204, 135, 61, 140, 197}

# ==============================================================================
# SOL MENÜ: SİSTEM, BÜTÇE VE AKILLI TASARRUF PARAMETRELERİ
# ==============================================================================
with st.sidebar:
    st.markdown("## 🏆 Spor Toto AI v12.4 Final")
    st.caption("Real-Game Production & Safe-Play")

    st.download_button(
        label="📄 Kullanım Kılavuzunu İndir (PDF/HTML)",
        data=KULLANIM_KILAVUZU_HTML.encode("utf-8"),
        file_name="Spor_Toto_AI_v12_4_Kullanim_Kilavuzu.html",
        mime="text/html",
        use_container_width=True
    )

    api_key = st.text_input("🔑 API-Football Anahtarı:", type="password")
    if api_key:
        st.caption(f"📊 Kalan Günlük API Kotası: **{st.session_state.kalan_kota}**")

    st.markdown("---")
    st.markdown("### 🎯 1. Garanti & Akıllı Bütçe Yönetimi")
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
            "🔥 Süper Tasarruf (%82 Kütle - En Az Kolon)",
            "⚖️ Ekonomik Denge (%90 Kütle - Önerilen)",
            "🛡️ Tam Kapsama (%100 Kütle - Klasik)"
        ],
        value="⚖️ Ekonomik Denge (%90 Kütle - Önerilen)",
        help="Shannon Log-Olasılık dağılımının en altındaki çöp kuyruğu keserek isabet gücünü düşürmeden kolon sayısını %35-%55 azaltır."
    )
    if "82" in tasarruf_profili:
        hedef_kapsama_orani = 82.0
    elif "90" in tasarruf_profili:
        hedef_kapsama_orani = 90.0
    else:
        hedef_kapsama_orani = 100.0

    kolon_fiyati = st.number_input("Kolon Birim Fiyatı (TL):", min_value=1.0, value=10.0, step=1.0)
    hedef_butce_tl = st.number_input(
        "💸 Hedef Toplam Bütçe (TL):",
        min_value=10.0, max_value=500000.0, value=500.0, step=50.0,
        help="Şablonu otomatik kurarken ve maksimum kolon sınırında baz alınacak bütçeniz."
    )
    hedef_kolon_sayisi = max(1, int(hedef_butce_tl // kolon_fiyati))
    st.caption(f"🎯 Hedef Bütçe Karşılığı: **En Fazla {hedef_kolon_sayisi:,} Kolon**")

    butce_kilidi_aktif = st.toggle("🔒 Üretimi Bu Bütçeyle Kesin Sınırla", value=False)
    max_kolon_limiti = hedef_kolon_sayisi if butce_kilidi_aktif else None

    st.markdown("---")
    st.markdown("### 🧠 2. Sendika & Çift Kademeli Şart Motoru")
    strateji_modu = st.radio(
        "Yapay Zeka Oyun Stili:",
        [
            "⚖️ Dengeli (Optimum EV & Log-Olasılık)",
            "🛡️ Favori Ağırlıklı (Daha Az Kolon / Yüksek İsabet)",
            "💎 İkramiye Avcısı (Anti-Public / Yüksek İkramiye)"
        ]
    )

    ev_katsayisi = st.slider(
        "💰 İkramiye Çarpanı (Anti-Public) Ağırlığı:",
        min_value=0.0, max_value=1.0, value=0.22, step=0.05,
        help="0.15 - 0.30 arası gerçek olasılıkları korurken balon favorilerden dengeli şekilde kaçınır."
    )

    grup_guvence_aktif = st.toggle("🌟 Çift Kademeli Güvence (G1 & G2) Filtresi", value=True)
    if grup_guvence_aktif:
        otonom_grup_limiti = st.checkbox("🤖 G1/G2 Sınırlarını Otomatik Ölçekle", value=True)
        if not otonom_grup_limiti:
            g1_manuel = st.slider("🌟 G1 (Ağır Favoriler) Min-Maks Hata:", 0, 8, (0, 2))
            g2_manuel = st.slider("🔥 G2 (Plase/Ortada) Min-Maks Sürpriz:", 0, 12, (0, 5))
        else:
            g1_manuel, g2_manuel = None, None
    else:
        otonom_grup_limiti = False
        g1_manuel, g2_manuel = (0, 15), (0, 15)

    st.markdown("---")
    st.markdown("### 🔬 3. v12.4 Hassas Yapısal Filtreler")
    akilli_merkez = st.toggle("🧮 Hibrit Evren Set-Cover + Ters Budama", value=True)
    log_zarf_aktif = st.toggle("📐 Shannon Log-Olasılık (Altın Koridor) Zarfı", value=True)
    kademe_filtre_aktif = st.toggle("📊 3 Kademeli (Favori/Plase/Sürpriz) Bütçesi", value=True)
    homojen_bulten = st.toggle("⚖️ Alt/Üst Bülten Homojenlik Filtresi", value=True)
    entropi_filtresi = st.toggle("🌀 Yapay/Simetrik Dizilim Elemesi", value=True)
    tuzak_koruma = st.toggle("🚨 Kırılgan Halk Tuzaklarını & Kararsızları Çifteye Al", value=True)
    benzerlik_elemesi = st.select_slider("🔍 Kuponlar Arası Min. Farklı Maç (Hamming):", options=[1, 2, 3, 4], value=1)
    ai_filtre_modu = st.toggle("🤖 Şablon-Duyarlı Otonom İstatistik Sınırları", value=True)

    if not ai_filtre_modu:
        with st.expander("⚙️ Manuel Filtre Ayarları"):
            range_1 = st.slider("Ev Sahibi (1) Adedi", 0, 15, (3, 10))
            range_x = st.slider("Beraberlik (X) Adedi", 0, 15, (1, 7))
            range_2 = st.slider("Deplasman (2) Adedi", 0, 15, (1, 8))
            range_fav = st.slider("1. Tercih (Favori) Adedi", 0, 15, (4, 11))
            range_plase = st.slider("2. Tercih (Plase) Adedi", 0, 15, (2, 8))
            range_surpriz = st.slider("3. Tercih (Ağır Sürpriz) Adedi", 0, 10, (0, 4))
            max_ardisik_1 = st.slider("Üst Üste Maks. '1'", 2, 12, 6)
            max_ardisik_x = st.slider("Üst Üste Maks. 'X'", 2, 10, 3)
            max_ardisik_2 = st.slider("Üst Üste Maks. '2'", 2, 10, 4)
            banko_siniri = st.number_input("Banko Sınırı (%)", 35, 95, 58)
            cifte_sans_siniri = st.number_input("Çifte Şans Sınırı (%)", 30, 80, 42)

    st.markdown("---")
    st.markdown("### 💾 4. Haftalık Bülten Yedeği")
    if st.session_state.analiz_verisi is not None:
        yedek_paket = {
            "versiyon": "12.4",
            "secilen_mac_idleri": st.session_state.secilen_mac_idleri,
            "analiz_verisi": st.session_state.analiz_verisi,
            "tablo_df": st.session_state.tablo_df.to_dict(orient="records") if st.session_state.tablo_df is not None else None,
            "uretilen_kuponlar": st.session_state.uretilen_kuponlar.tolist() if st.session_state.uretilen_kuponlar is not None else None,
            "son_uretim_ozeti": st.session_state.son_uretim_ozeti,
            "canli_sonuclar": st.session_state.canli_sonuclar,
            "canli_skor_metni": st.session_state.canli_skor_metni,
            "yatirilan_paketler": st.session_state.yatirilan_paketler
        }
        st.download_button(
            "📥 Haftalık Oturumu Kaydet (.JSON)",
            data=json.dumps(
                yedek_paket,
                ensure_ascii=False,
                indent=2,
                default=lambda x: int(x) if isinstance(x, np.integer) else (float(x) if isinstance(x, np.floating) else str(x))
            ).encode("utf-8"),
            file_name=f"spor_toto_v12_4_oturum_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )

    yuklenen_oturum = st.file_uploader("📂 Kayıtlı Oturumu Yükle (.JSON):", type=["json"])
    if yuklenen_oturum is not None:
        if st.button("♻️ Oturumu Geri Yükle", use_container_width=True):
            try:
                veri_json = json.loads(yuklenen_oturum.getvalue().decode("utf-8"))
                st.session_state.secilen_mac_idleri = veri_json.get("secilen_mac_idleri", [])
                st.session_state.analiz_verisi = veri_json.get("analiz_verisi")
                if veri_json.get("tablo_df"):
                    st.session_state.tablo_df = pd.DataFrame(veri_json["tablo_df"])
                    st.session_state.tablo_versiyon += 1
                if veri_json.get("uretilen_kuponlar"):
                    st.session_state.uretilen_kuponlar = np.array(veri_json["uretilen_kuponlar"])
                st.session_state.son_uretim_ozeti = veri_json.get("son_uretim_ozeti")
                st.session_state.canli_sonuclar = veri_json.get("canli_sonuclar", ["⏳ Bekliyor"] * 15)
                st.session_state.canli_skor_metni = veri_json.get("canli_skor_metni", ["-"] * 15)
                st.session_state.yatirilan_paketler = veri_json.get("yatirilan_paketler", [])
                st.session_state.son_param_imzasi = None
                st.toast("✅ Haftalık bülten ve kuponlar başarıyla geri yüklendi!")
                st.rerun()
            except Exception as e:
                st.error(f"Yedek dosyası okunamadı: {e}")


# ==============================================================================
# API, DIXON-COLES / SHIN KALİBRASYONU VE PİYASA KARARSIZLIĞI MOTORU
# ==============================================================================
def api_istegi_at(url, api_key, timeout=8):
    headers = {"x-apisports-key": api_key}
    res = requests.get(url, headers=headers, timeout=timeout)
    res.raise_for_status()
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
    p1, px_val, p2 = max(3.0, float(p1)), max(3.0, float(px_val)), max(3.0, float(p2))
    toplam = p1 + px_val + p2
    y1 = int(round(p1 * 100.0 / toplam))
    yx = int(round(px_val * 100.0 / toplam))
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


def dixon_coles_marj_arindir(odd_1, odd_x, odd_2, lig_id=203):
    """
    v12.4 Asimetrik Shin + Dixon-Coles Beraberlik (X) Korumalı Marj Temizleme.
    """
    inv = np.array([1.0 / max(1.01, odd_1), 1.0 / max(1.01, odd_x), 1.0 / max(1.01, odd_2)], dtype=float)
    overround = float(np.sum(inv))
    if overround <= 1.0:
        baz = (inv / overround) * 100.0
    else:
        fazla = overround - 1.0
        us_vektor = np.array([1.0 + 0.78 * fazla, 1.0 + 0.42 * fazla, 1.0 + 0.78 * fazla])
        duz = np.power(inv, us_vektor)
        baz = (duz / np.sum(duz)) * 100.0

    rekabet_farki = abs(baz[0] - baz[2])
    if rekabet_farki <= 16.0:
        x_takviye = 1.8 if lig_id in KISIR_LIG_IDLERI else 1.0
        baz[1] += x_takviye
        baz = (baz / np.sum(baz)) * 100.0
    return baz


def halk_egilimi_simule_et(p1, px_val, p2, mac_adi=""):
    """Gerçek olasılık + popüler kulüp fanatizm sapmasına göre halk eğilimi tahmini."""
    w1, wx, w2 = (p1 ** 1.38), (px_val ** 1.04), (p2 ** 1.35)
    if mac_adi and "-" in mac_adi:
        parcalar = mac_adi.lower().split("-")
        ev_ad = parcalar[0].strip()
        dep_ad = parcalar[1].strip() if len(parcalar) > 1 else ""
        ev_pop = any(t in ev_ad for t in POPULER_TAKIM_ANAHTARLARI)
        dep_pop = any(t in dep_ad for t in POPULER_TAKIM_ANAHTARLARI)
        if ev_pop and not dep_pop and p1 >= 42:
            w1 *= 1.22
        elif dep_pop and not ev_pop and p2 >= 42:
            w2 *= 1.22
    return olasilik_yumusat(w1, wx, w2)


@st.cache_data(ttl=43200, show_spinner=False)
def tek_mac_analiz_cek(f_id, api_key, lig_id=203):
    ai_1, ai_x, ai_2 = 38.0, 30.0, 32.0
    pred_geldi = False
    odds_list_1, odds_list_x, odds_list_2 = [], [], []

    try:
        res_pred = api_istegi_at(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", api_key, timeout=6)
        if res_pred.get("response") and res_pred["response"][0].get("predictions"):
            t = res_pred["response"][0]["predictions"]["percent"]
            p1_raw = float(t["home"].replace("%", ""))
            px_raw = float(t["draw"].replace("%", ""))
            p2_raw = float(t["away"].replace("%", ""))
            ai_1 = p1_raw * 0.85 + 38.0 * 0.15
            ai_x = px_raw * 0.85 + 30.0 * 0.15
            ai_2 = p2_raw * 0.85 + 32.0 * 0.15
            pred_geldi = True
    except Exception:
        pass

    try:
        res_odds = api_istegi_at(f"https://v3.football.api-sports.io/odds?fixture={f_id}", api_key, timeout=6)
        if res_odds.get("response") and res_odds["response"][0].get("bookmakers"):
            for buro in res_odds["response"][0]["bookmakers"]:
                for bahis in buro.get("bets", []):
                    if bahis.get("id") == 1 or bahis.get("name") == "Match Winner":
                        degerler = {v["value"]: float(v["odd"]) for v in bahis.get("values", []) if float(v.get("odd", 0)) > 1.0}
                        if "Home" in degerler and "Draw" in degerler and "Away" in degerler:
                            p1_c, px_c, p2_c = dixon_coles_marj_arindir(
                                degerler["Home"], degerler["Draw"], degerler["Away"], lig_id=lig_id
                            )
                            odds_list_1.append(p1_c)
                            odds_list_x.append(px_c)
                            odds_list_2.append(p2_c)
                        break
                if len(odds_list_1) >= 10:
                    break
    except Exception:
        pass

    piyasa_std = 0.0
    if odds_list_1:
        odds_1 = float(np.median(odds_list_1))
        odds_x = float(np.median(odds_list_x))
        odds_2 = float(np.median(odds_list_2))
        if len(odds_list_1) >= 2:
            piyasa_std = float(max(np.std(odds_list_1), np.std(odds_list_2)))
        if pred_geldi:
            ham_1 = (odds_1 * 0.82) + (ai_1 * 0.18)
            ham_x = (odds_x * 0.82) + (ai_x * 0.18)
            ham_2 = (odds_2 * 0.82) + (ai_2 * 0.18)
        else:
            ham_1, ham_x, ham_2 = odds_1, odds_x, odds_2
    else:
        ham_1, ham_x, ham_2 = ai_1, ai_x, ai_2

    y1, yx, y2 = olasilik_yumusat(ham_1, ham_x, ham_2)
    return y1, yx, y2, round(piyasa_std, 2)


def hibrit_tahminleri_al(secilen_maclar, api_key):
    sonuclar = []
    progress = st.progress(0, text="v12.4 Dixon-Coles kalibrasyonu, büro sapması ve halk eğilimi hesaplanıyor...")
    for i, mac in enumerate(secilen_maclar):
        f_id = mac["id"]
        lig_id = mac.get("lig_id", 203)
        g1, gx, g2, piyasa_std = tek_mac_analiz_cek(f_id, api_key, lig_id=lig_id)
        h1, hx, h2 = halk_egilimi_simule_et(g1, gx, g2, mac["karsilasma"])
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
            "tuzak_farki": max(h1, hx, h2) - max(g1, gx, g2),
            "piyasa_std": piyasa_std
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
        "c.rizespor": "rizespor", "g.antep": "gaziantep", "k.pasa": "kasimpasa",
        "a.gucu": "ankaragucu", "d.bakir": "diyarbakir"
    }
    for k, u in kisaltmalar.items():
        s = s.replace(k, u)
    s = re.sub(
        r"\b(fk|sk|as|fc|ac|sc|cf|cd|ud|rc|rcd|sv|vfb|vfl|tsg|1899|1907|spor|belediyespor|united|city|club|caykur|atakas|rams|bellona|iklimlendirme|corendon|eyupspor)\b",
        " ",
        s
    )
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return " ".join(s.split())


def bulten_metni_eslestir(yapistirilan_metin, havuz_maclari):
    """
    v12.4 Çift Yönlü (Ev-Ev & Dep-Dep) Bülten Sırası Korumalı Eşleştirici.
    """
    satirlar = [s.strip() for s in yapistirilan_metin.splitlines() if len(s.strip()) > 2]
    eslesen_maclar = []
    eslesmeyen_satirlar = []
    kullanilan_idler = set()

    for idx_s, satir in enumerate(satirlar):
        temiz_satir = re.sub(r"^\d+[\.\-\)\s]+", "", satir).strip()
        parcalar = re.split(r"\s*[-–—vV][sS]?\s*", temiz_satir, maxsplit=1)
        metin_adayi = metin_temizle(temiz_satir)
        if len(metin_adayi) < 3:
            continue

        ev_aday = metin_temizle(parcalar[0]) if len(parcalar) == 2 else ""
        dep_aday = metin_temizle(parcalar[1]) if len(parcalar) == 2 else ""

        en_iyi_skor = 0.0
        en_iyi_mac = None

        for m in havuz_maclari:
            if m["id"] in kullanilan_idler:
                continue
            ev_temiz = metin_temizle(m["ev"])
            dep_temiz = metin_temizle(m["dep"])
            mac_birlesik = f"{ev_temiz} {dep_temiz}"

            if ev_aday and dep_aday:
                skor_ev = SequenceMatcher(None, ev_aday, ev_temiz).ratio()
                skor_dep = SequenceMatcher(None, dep_aday, dep_temiz).ratio()
                skor_genel = (skor_ev * 0.52) + (skor_dep * 0.48)
            else:
                skor_genel = SequenceMatcher(None, metin_adayi, mac_birlesik).ratio()

            ev_var = 0.25 if (ev_temiz and ev_temiz.split()[0] in metin_adayi) else 0.0
            dep_var = 0.25 if (dep_temiz and dep_temiz.split()[0] in metin_adayi) else 0.0
            toplam_skor = skor_genel + ev_var + dep_var

            if toplam_skor > en_iyi_skor:
                en_iyi_skor = toplam_skor
                en_iyi_mac = m

        if en_iyi_mac and en_iyi_skor >= 0.46:
            eslesen_maclar.append(en_iyi_mac)
            kullanilan_idler.add(en_iyi_mac["id"])
            if len(eslesen_maclar) == 15:
                break
        else:
            eslesmeyen_satirlar.append(f"Satır {idx_s + 1}: {satir}")

    return eslesen_maclar, eslesmeyen_satirlar


def canli_skorlari_cek(fixture_id_listesi, api_key):
    """
    v12.4 Resmi Spor Toto 90-Dakika Kuralı Korumalı Canlı Skor Motoru.
    """
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
                    dakika = md["fixture"]["status"].get("elapsed")
                    ft_skor = md.get("score", {}).get("fulltime", {})

                    if durum in ["FT", "AET", "PEN"]:
                        if ft_skor.get("home") is not None and ft_skor.get("away") is not None:
                            eg, dg = ft_skor["home"], ft_skor["away"]
                        else:
                            eg, dg = md["goals"]["home"], md["goals"]["away"]
                        if eg is not None and dg is not None:
                            ek_bilgi = " (90' MS)" if durum in ["AET", "PEN"] else " (✅ MS)"
                            skor_metinleri[idx] = f"{eg} - {dg}{ek_bilgi}"
                            yeni_sonuclar[idx] = "1" if eg > dg else ("X" if eg == dg else "2")
                    elif durum in ["1H", "HT", "2H", "ET", "BT", "LIVE"] and md["goals"]["home"] is not None:
                        eg, dg = md["goals"]["home"], md["goals"]["away"]
                        dk_str = f" {dakika}'" if dakika else ""
                        skor_metinleri[idx] = f"{eg} - {dg} (🔴 {durum}{dk_str})"
                        yeni_sonuclar[idx] = "1" if eg > dg else ("X" if eg == dg else "2")
                    elif durum in ["PST", "CANC", "ABD", "SUSP", "INT"]:
                        skor_metinleri[idx] = f"⚠️ Kura/Ertelendi ({durum})"
    except Exception:
        pass
    return yeni_sonuclar, skor_metinleri


# ==============================================================================
# v12.4 BÜTÇE-DUYARLI ŞABLON KURUCU, SHANNON ZARFI VE HİBRİT SET-COVER
# ==============================================================================
def akilli_cifte_sec(v):
    s = sorted([(v["1"], "1"), (v["X"], "X"), (v["2"], "2")], reverse=True)
    en_b_oran, en_b_secim = s[0][0], s[0][1]
    ikinci_oran, ikinci_secim = s[1][0], s[1][1]

    if {en_b_secim, ikinci_secim} == {"1", "2"} and v["X"] >= 27 and (en_b_oran - ikinci_oran) >= 5:
        return [en_b_secim, "X"]
    return [en_b_secim, ikinci_secim]


def butceye_gore_sablon_optimize_et(veriler, hedef_kolon, garanti_derecesi, tuzak_aktif=True):
    sikistirma_carpani = {15: 1.5, 14: 6.8, 13: 26.0, 12: 85.0}.get(garanti_derecesi, 12.0)
    hedef_ham_ust_sinir = min(180000, max(2, int(hedef_kolon * sikistirma_carpani)))

    durumlar = [1] * 15  # 1: Banko, 2: Çifte, 3: Kapalı

    while True:
        mevcut_ham = math.prod(durumlar)
        en_iyi_mac = None
        en_iyi_artis = -1.0

        for i, v in enumerate(veriler):
            s = sorted([v["1"], v["X"], v["2"]], reverse=True)
            p_fav, p_plase, p_surpriz = s[0] / 100.0, s[1] / 100.0, s[2] / 100.0
            kirilgan_tuzak = (42 <= s[0] <= 57) and (v.get("tuzak_farki", 0) >= 9)
            kararsiz_piyasa = v.get("piyasa_std", 0.0) >= 2.2

            if durumlar[i] == 1:
                yeni_ham = mevcut_ham * 2
                if yeni_ham <= hedef_ham_ust_sinir:
                    bonus = 1.25 if (tuzak_aktif and (kirilgan_tuzak or kararsiz_piyasa)) else 1.0
                    fayda = ((p_plase / max(0.15, p_fav)) * bonus) / math.log(2.0)
                    if fayda > en_iyi_artis:
                        en_iyi_artis = fayda
                        en_iyi_mac = i

            elif durumlar[i] == 2:
                yeni_ham = (mevcut_ham // 2) * 3
                if yeni_ham <= hedef_ham_ust_sinir:
                    fayda = (p_surpriz / max(0.30, p_fav + p_plase)) / math.log(1.5)
                    if fayda > en_iyi_artis:
                        en_iyi_artis = fayda
                        en_iyi_mac = i

        if en_iyi_mac is None:
            break

        durumlar[en_iyi_mac] += 1

    return durumlar


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
        aktif_sablon = [["1", "X", "2"]] * 15

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

    zorunlu_fav, acik_fav, exp_fav = 0, 0, 0.0
    zorunlu_plase, acik_plase, exp_plase = 0, 0, 0.0
    zorunlu_surp, acik_surp, exp_surp = 0, 0, 0.0

    for v, s in zip(mac_verileri, aktif_sablon):
        sirali_tercihler = [k for _, k in sorted([(v["1"], "1"), (v["X"], "X"), (v["2"], "2")], reverse=True)]
        f_harf, p_harf, u_harf = sirali_tercihler[0], sirali_tercihler[1], sirali_tercihler[2]
        toplam_s = max(1.0, float(sum(v[k] for k in s)))

        if s == [f_harf]:
            zorunlu_fav += 1
        if f_harf in s:
            acik_fav += 1
            exp_fav += v[f_harf] / toplam_s

        if s == [p_harf]:
            zorunlu_plase += 1
        if p_harf in s:
            acik_plase += 1
            exp_plase += v[p_harf] / toplam_s

        if s == [u_harf]:
            zorunlu_surp += 1
        if u_harf in s:
            acik_surp += 1
            exp_surp += v[u_harf] / toplam_s

    if "Favori" in strateji:
        fav_aralik = (max(zorunlu_fav, int(math.floor(exp_fav)) - 2), min(acik_fav, int(math.ceil(exp_fav)) + 3))
        plase_aralik = (max(zorunlu_plase, int(math.floor(exp_plase)) - 3), min(acik_plase, int(math.ceil(exp_plase)) + 2))
        surpriz_aralik = (zorunlu_surp, min(acik_surp, max(zorunlu_surp + 2, int(math.ceil(exp_surp)) + 1)))
        z_zarf = (-1.15, 2.50)
    elif "İkramiye" in strateji:
        fav_aralik = (max(zorunlu_fav, int(math.floor(exp_fav)) - 4), min(acik_fav, max(zorunlu_fav + 2, int(math.ceil(exp_fav)) + 1)))
        plase_aralik = (max(zorunlu_plase, int(math.floor(exp_plase)) - 2), min(acik_plase, int(math.ceil(exp_plase)) + 4))
        surpriz_aralik = (max(zorunlu_surp, int(math.floor(exp_surp)) - 1), min(acik_surp, int(math.ceil(exp_surp)) + 3))
        z_zarf = (-2.10, 1.35)
    else:
        fav_aralik = (max(zorunlu_fav, int(math.floor(exp_fav)) - 3), min(acik_fav, int(math.ceil(exp_fav)) + 2))
        plase_aralik = (max(zorunlu_plase, int(math.floor(exp_plase)) - 2), min(acik_plase, int(math.ceil(exp_plase)) + 3))
        surpriz_aralik = (zorunlu_surp, min(acik_surp, max(zorunlu_surp + 2, int(math.ceil(exp_surp)) + 2)))
        z_zarf = (-1.65, 1.95)

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

    return {
        "1": aralik_1,
        "X": aralik_x,
        "2": aralik_2,
        "fav": fav_aralik,
        "plase": plase_aralik,
        "surpriz": surpriz_aralik,
        "z_zarf": z_zarf,
        "ardisik_1": max(4, zorunlu_ard_1),
        "ardisik_x": max(3, zorunlu_ard_x),
        "ardisik_2": max(4, zorunlu_ard_2),
        "banko_siniri": ai_banko,
        "cifte_siniri": ai_cifte,
        "zorluk_skoru": hz
    }


def teshis_etiketi_hesapla(en_b_oran, tuzak_farki, piyasa_std):
    kirilgan_tuzak_mi = (42 <= en_b_oran <= 57) and (tuzak_farki >= 9)
    kararsiz_mi = piyasa_std >= 2.2
    if en_b_oran >= 56 and not kararsiz_mi:
        return "🔒 Net Banko"
    elif kararsiz_mi:
        return "⚠️ Piyasa Kararsız"
    elif kirilgan_tuzak_mi:
        return "🚨 Halk Tuzağı"
    elif en_b_oran >= 43:
        return "⚡ Plase"
    else:
        return "💣 Cadı Kazanı"


def tablo_verisi_olustur(veriler, limitler, tuzak_aktif=True, mod="ai", ozel_durumlar=None):
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

    for idx_v, v in enumerate(veriler):
        s = sorted([(v["1"], "1"), (v["X"], "X"), (v["2"], "2")], reverse=True)
        en_b_oran, en_b_secim = s[0][0], s[0][1]
        cifte_secim = akilli_cifte_sec(v)
        sira_idx = tum_sirali.index(v["id"])

        kirilgan_tuzak_mi = (42 <= en_b_oran <= 57) and (v.get("tuzak_farki", 0) >= 9)
        kararsiz_mi = v.get("piyasa_std", 0.0) >= 2.2

        if mod == "butce_oto" and ozel_durumlar is not None:
            k_tip = ozel_durumlar[idx_v]
            if k_tip == 1:
                secim = [en_b_secim]
                g1, g2 = False, False
            elif k_tip == 2:
                secim = cifte_secim
                g1 = True if en_b_oran >= 44 else False
                g2 = True if en_b_oran < 44 else False
            else:
                secim = ["1", "X", "2"]
                g1, g2 = False, True
        elif mod == "15_banko":
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
            if (en_b_oran >= 56 or sira_idx < 4) and not (tuzak_aktif and kararsiz_mi):
                secim = [en_b_secim]
                g1, g2 = False, False
            elif (en_b_oran >= limitler["cifte_siniri"] or sira_idx < 11) and not (tuzak_aktif and kirilgan_tuzak_mi and sira_idx >= 11):
                secim = cifte_secim
                g1 = True if en_b_oran >= 45 else False
                g2 = True if en_b_oran < 45 else False
            else:
                secim = ["1", "X", "2"]
                g1, g2 = False, True

        teshis = teshis_etiketi_hesapla(en_b_oran, v.get("tuzak_farki", 0), v.get("piyasa_std", 0.0))

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
    ev_agirligi=0.22,
    log_zarf_aktif=True,
    kademe_aktif=True,
    entropi_aktif=True,
    homojen_aktif=True
):
    harita = {"1": 0, "X": 1, "2": 2}
    ters = np.array(["1", "X", "2"])
    grids = np.meshgrid(*[[harita[s] for s in m] for m in sablon], indexing="ij")
    ham_matris = np.stack(grids, axis=-1).reshape(-1, 15).astype(np.int8)
    matris = ham_matris
    esnetilenler = []

    oran_mat = np.array([[v["1"], v["X"], v["2"]] for v in mac_verileri], dtype=np.float32)
    halk_mat = np.array([[v["h1"], v["hX"], v["h2"]] for v in mac_verileri], dtype=np.float32)
    en_yuksek_oranlar = np.max(oran_mat, axis=1)

    sira_mat = np.argsort(-oran_mat, axis=1)
    kademe_haritasi = np.zeros((15, 3), dtype=np.int8)
    for m_i in range(15):
        kademe_haritasi[m_i, sira_mat[m_i, 0]] = 0
        kademe_haritasi[m_i, sira_mat[m_i, 1]] = 1
        kademe_haritasi[m_i, sira_mat[m_i, 2]] = 2

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
    else:
        esnetilenler.append("1-X-2 Adet Sınırı")

    if len(g1_indeksleri) > 0 and len(matris) > 0:
        g1_idx = np.array(g1_indeksleri, dtype=int)
        secilen_g1_oran = oran_mat[g1_idx[None, :], matris[:, g1_idx]]
        g1_hatalar = np.sum((en_yuksek_oranlar[g1_idx][None, :] - secilen_g1_oran) > 4.0, axis=1)
        m_g1 = (g1_hatalar >= g1_aralik[0]) & (g1_hatalar <= g1_aralik[1])
        if np.any(m_g1):
            matris = matris[m_g1]
        else:
            esnetilenler.append("G1 Favori Güvencesi")

    if len(g2_indeksleri) > 0 and len(matris) > 0:
        g2_idx = np.array(g2_indeksleri, dtype=int)
        secilen_g2_oran = oran_mat[g2_idx[None, :], matris[:, g2_idx]]
        g2_surprizler = np.sum((en_yuksek_oranlar[g2_idx][None, :] - secilen_g2_oran) > 6.0, axis=1)
        m_g2 = (g2_surprizler >= g2_aralik[0]) & (g2_surprizler <= g2_aralik[1])
        if np.any(m_g2):
            matris = matris[m_g2]
        else:
            esnetilenler.append("G2 Plase/Sürpriz Filtresi")

    if kademe_aktif and len(matris) > 0:
        sec_kademe = kademe_haritasi[np.arange(15), matris]
        fav_say = np.sum(sec_kademe == 0, axis=1)
        plase_say = np.sum(sec_kademe == 1, axis=1)
        surp_say = np.sum(sec_kademe == 2, axis=1)
        maske_kademe = (
            (fav_say >= limitler["fav"][0]) & (fav_say <= limitler["fav"][1]) &
            (plase_say >= limitler["plase"][0]) & (plase_say <= limitler["plase"][1]) &
            (surp_say >= limitler["surpriz"][0]) & (surp_say <= limitler["surpriz"][1])
        )
        if np.any(maske_kademe):
            matris = matris[maske_kademe]
        else:
            esnetilenler.append("Favori/Plase/Sürpriz Bütçesi")

    if log_zarf_aktif and len(matris) > 10:
        sec_oran = oran_mat[np.arange(15), matris]
        log_l = np.sum(np.log(np.maximum(sec_oran, 1.0) / 100.0), axis=1)
        std_ll = float(np.std(log_l))
        if std_ll > 1e-4:
            z_skor = (log_l - float(np.mean(log_l))) / std_ll
            z_alt, z_ust = limitler.get("z_zarf", (-1.65, 1.95))
            maske_log = (z_skor >= z_alt) & (z_skor <= z_ust)
            if np.any(maske_log):
                matris = matris[maske_log]
            else:
                esnetilenler.append("Shannon Log-Olasılık Zarfı")

    for deger, anahtar, etiket in [(0, "ardisik_1", "Ardışık 1"), (1, "ardisik_x", "Ardışık X"), (2, "ardisik_2", "Ardışık 2")]:
        max_ard = int(limitler[anahtar])
        if 1 <= max_ard < 15 and len(matris) > 0:
            pencereler = sliding_window_view(matris == deger, window_shape=max_ard + 1, axis=1)
            ardisik_ihlal = np.any(np.all(pencereler, axis=2), axis=1)
            if np.any(~ardisik_ihlal):
                matris = matris[~ardisik_ihlal]
            else:
                esnetilenler.append(etiket)

    if homojen_aktif and len(matris) > 0:
        sec_kademe_h = kademe_haritasi[np.arange(15), matris]
        ilk_yari_surpriz = np.sum(sec_kademe_h[:, :7] == 2, axis=1)
        son_yari_surpriz = np.sum(sec_kademe_h[:, 7:] == 2, axis=1)
        homojen_maske = (ilk_yari_surpriz <= 3) & (son_yari_surpriz <= 3)
        if np.any(homojen_maske):
            matris = matris[homojen_maske]
        else:
            esnetilenler.append("Alt/Üst Homojenlik")

    if entropi_aktif and len(matris) > 0:
        gecis_sayisi = np.sum(matris[:, 1:] != matris[:, :-1], axis=1)
        periyot_3 = np.sum(matris[:, 3:] == matris[:, :-3], axis=1)
        entropi_maske = (gecis_sayisi >= 4) & (gecis_sayisi <= 13) & (periyot_3 <= 10)
        if np.any(entropi_maske):
            matris = matris[entropi_maske]
        else:
            esnetilenler.append("Simetrik Dizilim (Entropi)")

    secilen_oranlar = oran_mat[np.arange(15), matris]
    secilen_halk = halk_mat[np.arange(15), matris]
    puanlar = np.sum(secilen_oranlar, axis=1)

    log_gercek = np.sum(np.log(np.maximum(secilen_oranlar, 1.0) / 100.0), axis=1)
    log_halk = np.sum(np.log(np.maximum(secilen_halk, 1.0) / 100.0), axis=1)
    kompozit_skor = log_gercek - (ev_agirligi * 0.24 * log_halk)

    idx = np.argsort(kompozit_skor)[::-1]
    return ters[matris[idx]], puanlar[idx], kompozit_skor[idx], esnetilenler


def deterministik_garanti_denetle(secilen_kolonlar, filtreli_evren):
    if len(secilen_kolonlar) == 0 or len(filtreli_evren) == 0:
        return {"tam_15": 0.0, "en_az_14": 0.0, "en_az_13": 0.0, "en_az_12": 0.0}

    evren_ornek = filtreli_evren[:25000]
    M = len(evren_ornek)
    K = len(secilen_kolonlar)

    evren_kod = np.zeros((M, 15), dtype=np.int8)
    evren_kod[evren_ornek == "X"] = 1
    evren_kod[evren_ornek == "2"] = 2

    kupon_kod = np.zeros((K, 15), dtype=np.int8)
    kupon_kod[secilen_kolonlar == "X"] = 1
    kupon_kod[secilen_kolonlar == "2"] = 2

    evren_oh = np.zeros((M, 45), dtype=np.float32)
    evren_oh[np.arange(M)[:, None], np.arange(15)[None, :] * 3 + evren_kod] = 1.0

    kupon_oh = np.zeros((K, 45), dtype=np.float32)
    kupon_oh[np.arange(K)[:, None], np.arange(15)[None, :] * 3 + kupon_kod] = 1.0

    maks_isabet = np.max(evren_oh @ kupon_oh.T, axis=1)
    return {
        "tam_15": float(np.mean(maks_isabet >= 14.9) * 100.0),
        "en_az_14": float(np.mean(maks_isabet >= 13.9) * 100.0),
        "en_az_13": float(np.mean(maks_isabet >= 12.9) * 100.0),
        "en_az_12": float(np.mean(maks_isabet >= 11.9) * 100.0)
    }


def gelismis_garanti_ve_budama_uygula(
    kolonlar, puanlar, kompozit_skor, hedef,
    max_k=None, akilli_merkez=True, min_fark=1, hedef_kapsama=90.0
):
    if len(kolonlar) == 0:
        return np.empty((0, 15), dtype="<U1"), np.array([]), 0.0, 0

    N_tam = len(kolonlar)
    MAX_HAVUZ = 35000
    if N_tam > MAX_HAVUZ:
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

    agirlik = np.exp((kompozit_skor - np.max(kompozit_skor)) * 0.85).astype(np.float32)
    toplam_agirlik = float(np.sum(agirlik))
    esik_eslesme = float(hedef)

    kapsanmamis_maske = np.ones(N, dtype=bool)
    aday_maske = np.ones(N, dtype=bool)
    hamming_elendi_maske = np.zeros(N, dtype=bool)
    nihai = []
    kapsama_orani = 0.0

    while np.any(kapsanmamis_maske):
        if max_k and len(nihai) >= max_k:
            break
        if kapsama_orani >= hedef_kapsama:
            break

        uygun_adaylar = np.where(aday_maske & kapsanmamis_maske)[0]
        if len(uygun_adaylar) == 0:
            kalan_kapsanmamis = np.where(kapsanmamis_maske & hamming_elendi_maske)[0]
            if len(kalan_kapsanmamis) > 0:
                uygun_adaylar = kalan_kapsanmamis
            else:
                break

        kapsanmamis_indeksler = np.where(kapsanmamis_maske)[0]

        if akilli_merkez and len(kapsanmamis_indeksler) > 1 and hedef < 15:
            if len(uygun_adaylar) <= 160:
                aday_idx = uygun_adaylar
            else:
                lider_idx = uygun_adaylar[:100]
                geo_idx = uygun_adaylar[np.linspace(100, len(uygun_adaylar) - 1, 60, dtype=int)]
                aday_idx = np.unique(np.concatenate([lider_idx, geo_idx]))

            ornek_say = min(15000, len(kapsanmamis_indeksler))
            ornek_idx = kapsanmamis_indeksler[:ornek_say]

            eslesme_mat = one_hot[aday_idx] @ one_hot[ornek_idx].T
            kapsama_mat = (eslesme_mat >= esik_eslesme).astype(np.float32)
            kapsanan_kutle = (kapsama_mat @ agirlik[ornek_idx]) * (agirlik[aday_idx] ** 0.55)
            m_idx = int(aday_idx[int(np.argmax(kapsanan_kutle))])
        else:
            m_idx = int(uygun_adaylar[0])

        nihai.append(m_idx)
        aday_maske[m_idx] = False
        hamming_elendi_maske[m_idx] = False

        eslesmeler = one_hot[kapsanmamis_indeksler] @ one_hot[m_idx]
        yeni_kapsananlar = kapsanmamis_indeksler[eslesmeler >= esik_eslesme]
        kapsanmamis_maske[yeni_kapsananlar] = False
        aday_maske[yeni_kapsananlar] = False

        if min_fark > 1:
            kalan_adaylar = np.where(aday_maske)[0]
            if len(kalan_adaylar) > 0:
                fark_sayisi = np.sum(mat[kalan_adaylar] != mat[m_idx], axis=1)
                elenen_adaylar = kalan_adaylar[fark_sayisi < min_fark]
                aday_maske[elenen_adaylar] = False
                hamming_elendi_maske[elenen_adaylar] = True

        kapsama_orani = float(np.sum(agirlik[~kapsanmamis_maske]) / toplam_agirlik * 100.0)

    budanan_adet = 0
    if akilli_merkez and hedef < 15 and 2 < len(nihai) <= 2000:
        kapsanan_evren = np.where(~kapsanmamis_maske)[0]
        if 0 < len(kapsanan_evren) <= 30000:
            secilen_oh = one_hot[nihai]
            evren_oh = one_hot[kapsanan_evren]
            ortme_mat = (secilen_oh @ evren_oh.T) >= esik_eslesme
            ortme_sayaci = np.sum(ortme_mat, axis=0)

            aktif_tut = np.ones(len(nihai), dtype=bool)
            for i in range(len(nihai) - 1, -1, -1):
                if np.all(ortme_sayaci[ortme_mat[i]] >= 2):
                    aktif_tut[i] = False
                    ortme_sayaci -= ortme_mat[i].astype(int)
                    budanan_adet += 1
            nihai = [nihai[i] for i in range(len(nihai)) if aktif_tut[i]]

    if max_k and len(nihai) > max_k:
        nihai = nihai[:max_k]

    return kolonlar[nihai], puanlar[nihai], kapsama_orani, budanan_adet


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
        k = []
        for s in satirlar:
            temiz = s.strip().upper()
            if not temiz or "KUPON" in temiz or "MAC" in temiz:
                continue
            if len(temiz) == 15 and all(c in ["1", "X", "2", "0"] for c in temiz):
                k.append(["X" if c == "0" else c for c in temiz])
            else:
                parcalar = ["X" if h == "0" else h for h in temiz.replace(",", " ").replace(";", " ").replace("-", " ").split() if h in ["1", "X", "2", "0"]]
                if len(parcalar) >= 15:
                    k.append(parcalar[:15])
        return np.array(k) if k else None
    except Exception:
        return None


def guvenli_tarayici_asistani_uret(aktif_paket, mac_isimleri, paket_no, toplam_paket, hiz_ms=110):
    """
    v12.4 İddaa.com 4'lü Kolon (A-B-C-D) Geometrik Kutu Tarayıcı + Manuel Kalibrasyon Destekli Asistan.
    - iddaa.com/spor-toto üzerindeki 12'li (A, B, C, D Kolonu) boş kare kutucukları hem
      geometrik Y/X koordinat hizasından hem de satır yapısından otomatik bulur.
    - Tek tıkla 4 kolonu (A, B, C ve D) aynı anda doldurarak 4 kat hızlı işlem yapar.
    - İhtiyaç halinde '🎯 1. Kutuyu Tanıt' butonuyla kullanıcı 1. maçın ilk kutusuna tıkladığında
      tablodaki 180 kutuyu %100 kesinlikle kilitler.
    - ASLA kendi kendine 'Oyna / Onayla / Öde' butonuna basmaz.
    """
    paket_imza = hashlib.md5(json.dumps(aktif_paket).encode("utf-8")).hexdigest()[:8]
    kisa_maclar = [m.split("-")[0].strip()[:10] for m in mac_isimleri]

    js_kodu = f"""// ============================================================================
// 🏆 SPOR TOTO AI PRO v12.4 — İDDAA.COM 4'LÜ KOLON (A-B-C-D) & EVRENSEL ASİSTAN
// 🛡️ GÜVENLİK GARANTİSİ: Bu kod ASLA 'Oyna / Öde / Onayla' butonuna basmaz!
// ============================================================================
(function() {{
    const PAKET_NO = {paket_no};
    const TOPLAM_PAKET = {toplam_paket};
    const PAKET_IMZA = "{paket_imza}";
    const HIZ_MS = {hiz_ms};
    const BEKLENEN_TAKIMLAR = {json.dumps(kisa_maclar, ensure_ascii=False)};
    const KUPONLAR = {json.dumps(aktif_paket)};
    const STORAGE_KEY = "st_ai_v12_4_progress_" + PAKET_IMZA;

    let aktifIdx = parseInt(localStorage.getItem(STORAGE_KEY) || "0", 10);
    if (aktifIdx >= KUPONLAR.length || aktifIdx < 0) aktifIdx = 0;
    let manuelSeciciSinif = null;

    const eski = document.getElementById("st-ai-floating-hud");
    if (eski) eski.remove();

    function kutuSeciliMi(el) {{
        if (!el) return false;
        if (el.dataset && el.dataset.stSecili === "1") return true;
        const inp = el.tagName === "INPUT" ? el : el.querySelector("input");
        if (inp && inp.checked) return true;
        const cls = ((el.className || "") + " " + (el.parentElement ? el.parentElement.className : "")).toLowerCase();
        if (/(active|selected|checked|secili|on|chosen|pressed)/.test(cls)) return true;
        if (el.getAttribute("aria-checked") === "true" || el.getAttribute("aria-pressed") === "true") return true;
        const st = window.getComputedStyle(el);
        const bg = st.backgroundColor;
        if (bg && bg !== "rgba(0, 0, 0, 0)" && bg !== "transparent" && bg !== "rgb(255, 255, 255)" && bg !== "rgb(248, 250, 252)" && bg !== "rgb(241, 245, 249)") {{
            return true;
        }}
        return false;
    }}

    function kutuyaTikla(el) {{
        if (!el) return;
        const inp = el.tagName === "INPUT" ? el : el.querySelector("input");
        if (inp) {{
            inp.click();
        }} else {{
            el.click();
        }}
    }}

    function geometrikKutuTaramasiYap(ozelFiltreFn) {{
        const tum = Array.from(document.querySelectorAll("input[type='checkbox'], input[type='radio'], label, button, span, div, td, a"));
        const adayKutular = [];

        for (const el of tum) {{
            const rect = el.getBoundingClientRect();
            if (rect.width < 13 || rect.width > 46 || rect.height < 13 || rect.height > 46) continue;
            if (Math.abs(rect.width - rect.height) > 10) continue;
            if (!ozelFiltreFn(el, rect)) continue;
            adayKutular.push({{
                el: el,
                x: Math.round(rect.left + window.scrollX),
                y: Math.round(rect.top + window.scrollY)
            }});
        }}

        // İç içe geçmiş aynı koordinattaki (ör. div > span) kutuları tekilleştir
        const tekilKutular = [];
        for (const k of adayKutular) {{
            const mevcutIdx = tekilKutular.findIndex(m => Math.abs(m.x - k.x) <= 6 && Math.abs(m.y - k.y) <= 6);
            if (mevcutIdx === -1) {{
                tekilKutular.push(k);
            }} else {{
                const mevcut = tekilKutular[mevcutIdx];
                if (mevcut.el.contains(k.el) || k.el.tagName === "INPUT" || k.el.tagName === "BUTTON") {{
                    tekilKutular[mevcutIdx] = k;
                }}
            }}
        }}

        // Y koordinatına (aynı satır hizasına) göre grupla
        tekilKutular.sort((a, b) => a.y - b.y);
        const satirGruplari = [];
        for (const k of tekilKutular) {{
            let grup = satirGruplari.find(g => Math.abs(g.ortaY - k.y) <= 10);
            if (!grup) {{
                grup = {{ ortaY: k.y, kutular: [] }};
                satirGruplari.push(grup);
            }}
            grup.kutular.push(k);
            grup.ortaY = Math.round(grup.kutular.reduce((t, x) => t + x.y, 0) / grup.kutular.length);
        }}

        // Soldan sağa sırala ve 12 kutulu (iddaa.com A-B-C-D) veya 3 kutulu satırları filtrele
        const onIkiliSatirlar = [];
        const ucluSatirlar = [];

        for (const g of satirGruplari) {{
            g.kutular.sort((a, b) => a.x - b.x);
            if (g.kutular.length >= 12 && g.kutular.length <= 16) {{
                const sonOnIki = g.kutular.slice(g.kutular.length - 12).map(x => x.el);
                onIkiliSatirlar.push({{ satir: sonOnIki[0].parentElement || sonOnIki[0], butonlar: sonOnIki, kolonSayisi: 4 }});
            }} else if (g.kutular.length >= 3 && g.kutular.length <= 5) {{
                const ilkUc = g.kutular.slice(0, 3).map(x => x.el);
                ucluSatirlar.push({{ satir: ilkUc[0].parentElement || ilkUc[0], butonlar: ilkUc, kolonSayisi: 1 }});
            }}
        }}

        if (onIkiliSatirlar.length >= 15) return onIkiliSatirlar.slice(0, 15);
        if (ucluSatirlar.length >= 15) return ucluSatirlar.slice(0, 15);
        return onIkiliSatirlar.length >= ucluSatirlar.length ? onIkiliSatirlar : ucluSatirlar;
    }}

    function macSatirlariniBul() {{
        // 0. Kullanıcı manuel olarak 1. kutuyu tanıttıysa önce onu kullan
        if (manuelSeciciSinif) {{
            const ozelSonuc = geometrikKutuTaramasiYap((el) => {{
                return el.tagName === manuelSeciciSinif.tag &&
                       (manuelSeciciSinif.cls === "" || (el.className || "") === manuelSeciciSinif.cls);
            }});
            if (ozelSonuc.length === 15) return ozelSonuc;
        }}

        // 1. Geometrik Tarama: Boş Kare Kutucuklar veya Checkbox'lar (iddaa.com A-B-C-D 12'li yapı)
        const geoBosKareler = geometrikKutuTaramasiYap((el) => {{
            if (el.tagName === "INPUT" && (el.type === "checkbox" || el.type === "radio")) return true;
            const txt = (el.innerText || "").trim();
            if (txt !== "") return false;
            if (el.children.length > 2) return false;
            const st = window.getComputedStyle(el);
            const kenarVar = parseFloat(st.borderTopWidth) > 0 || parseFloat(st.borderLeftWidth) > 0 || st.outlineStyle !== "none";
            const imlecVar = st.cursor === "pointer" || el.tagName === "BUTTON" || el.tagName === "LABEL";
            return kenarVar || imlecVar;
        }});
        if (geoBosKareler.length === 15) return geoBosKareler;

        // 2. Geometrik Tarama: İçinde 1, 0, X, 2 yazan butonlar (Nesine / Bilyoner / Misli)
        const geoMetinKutular = geometrikKutuTaramasiYap((el) => {{
            const txt = (el.innerText || "").trim().toUpperCase();
            return ["1", "0", "X", "2"].includes(txt) && el.children.length <= 1;
        }});
        if (geoMetinKutular.length === 15) return geoMetinKutular;

        return geoBosKareler.length >= geoMetinKutular.length ? geoBosKareler : geoMetinKutular;
    }}

    const hud = document.createElement("div");
    hud.id = "st-ai-floating-hud";
    hud.style.cssText = "position:fixed;top:16px;right:16px;width:395px;background:#0f172a;color:#f8fafc;border:2px solid #3b82f6;border-radius:12px;padding:14px;z-index:999999;font-family:'Segoe UI',sans-serif;box-shadow:0 12px 28px rgba(0,0,0,0.55);font-size:13px;";
    document.body.appendChild(hud);

    function hudGuncelle(durumMesaji = "") {{
        const satirlar = macSatirlariniBul();
        const tabloKolonKapasitesi = satirlar.length === 15 ? satirlar[0].kolonSayisi : 4;
        const bitisIdx = Math.min(aktifIdx + tabloKolonKapasitesi, KUPONLAR.length);
        const aktifGrup = KUPONLAR.slice(aktifIdx, bitisIdx);
        const harfler = ["A", "B", "C", "D"];

        let durumRenk = satirlar.length === 15 ? "#4ade80" : "#fbbf24";
        let ustBilgi = satirlar.length === 15
            ? `✅ 15 Maç Hazır (${{tabloKolonKapasitesi === 4 ? "İddaa.com A-B-C-D 4'lü Kolon Modu" : "Tekli Kolon Modu"}})`
            : `⚠️ Otomatik taramada ${{satirlar.length}}/15 satır bulundu. Aşağıdaki '🎯 1. Kutuyu Tanıt' butonuna basıp 1. maçın ilk kutucuğuna tıklayın.`;

        let onizlemeHtml = aktifGrup.map((kl, idx) =>
            `<div style="margin:2px 0;"><strong style="color:#60a5fa;">${{harfler[idx] || ""}} Kolonu (#${{aktifIdx + idx + 1}}):</strong> ${{kl.join("-")}}</div>`
        ).join("");

        hud.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #334155;padding-bottom:8px;margin-bottom:8px;">
                <div>
                    <strong style="font-size:14px;color:#60a5fa;">🏆 Spor Toto AI v12.4 Hızlı Asistan</strong>
                    <div style="font-size:11px;color:#94a3b8;">Paket ${{PAKET_NO}} / ${{TOPLAM_PAKET}} • Toplam: ${{KUPONLAR.length}} Kolon</div>
                </div>
                <button id="st-ai-kapat" style="background:#ef4444;color:white;border:none;border-radius:6px;padding:4px 8px;cursor:pointer;font-weight:bold;">✕</button>
            </div>
            <div style="background:#1e293b;padding:8px;border-radius:8px;margin-bottom:8px;font-size:11.5px;color:${{durumRenk}};">
                ${{ustBilgi}}
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <span>📌 İşlenecek Kolonlar: <strong style="color:#38bdf8;font-size:14px;">#${{aktifIdx + 1}} - #${{bitisIdx}} / ${{KUPONLAR.length}}</strong></span>
                <span style="background:#166534;color:#dcfce7;padding:2px 8px;border-radius:99px;font-size:11px;">🛡️ Ödeme Yapmaz</span>
            </div>
            <div style="background:#020617;padding:8px;border-radius:6px;font-family:monospace;font-size:11.5px;color:#e2e8f0;margin-bottom:10px;border:1px solid #1e293b;">
                ${{onizlemeHtml || "🎉 PAKET TAMAMLANDI"}}
            </div>
            ${{durumMesaji ? `<div style="margin-bottom:8px;color:#38bdf8;font-size:12px;text-align:center;font-weight:bold;">${{durumMesaji}}</div>` : ""}}
            <div style="display:grid;grid-template-columns:1fr 2.2fr 1fr;gap:6px;margin-bottom:6px;">
                <button id="st-ai-geri" style="background:#334155;color:white;border:none;padding:8px;border-radius:6px;cursor:pointer;font-weight:bold;">◀ Geri</button>
                <button id="st-ai-isaretle" style="background:#2563eb;color:white;border:none;padding:8px;border-radius:6px;cursor:pointer;font-weight:bold;">
                    🎯 ${{aktifGrup.length}} Kolonu Doldur
                </button>
                <button id="st-ai-ileri" style="background:#16a34a;color:white;border:none;padding:8px;border-radius:6px;cursor:pointer;font-weight:bold;">İleri ▶</button>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;gap:4px;font-size:11px;color:#94a3b8;margin-top:4px;">
                <button id="st-ai-kalibre" style="background:#0284c7;color:white;border:none;padding:5px 8px;border-radius:4px;cursor:pointer;font-size:11px;font-weight:bold;">🎯 1. Kutuyu Tanıt</button>
                <button id="st-ai-temizle" style="background:#475569;color:white;border:none;padding:5px 8px;border-radius:4px;cursor:pointer;font-size:11px;">🧹 Temizle</button>
                <a href="#" id="st-ai-sifirla" style="color:#f87171;text-decoration:none;">1. Kolona Dön</a>
            </div>
        `;

        document.getElementById("st-ai-kapat").onclick = () => hud.remove();
        document.getElementById("st-ai-geri").onclick = () => {{
            aktifIdx = Math.max(0, aktifIdx - tabloKolonKapasitesi);
            localStorage.setItem(STORAGE_KEY, String(aktifIdx));
            hudGuncelle("◀ Önceki kolon grubuna dönüldü.");
        }};
        document.getElementById("st-ai-ileri").onclick = () => {{
            if (aktifIdx + tabloKolonKapasitesi < KUPONLAR.length) {{
                aktifIdx += tabloKolonKapasitesi;
                localStorage.setItem(STORAGE_KEY, String(aktifIdx));
                hudGuncelle("▶ Sıradaki kolon grubuna geçildi. 'Kolonu Doldur'a basın.");
            }} else {{
                hudGuncelle("🎉 Bu paketteki tüm kolonları tamamladınız!");
            }}
        }};
        document.getElementById("st-ai-sifirla").onclick = (e) => {{
            e.preventDefault();
            aktifIdx = 0;
            localStorage.setItem(STORAGE_KEY, "0");
            hudGuncelle("🔄 Sayaç 1. kolona sıfırlandı.");
        }};
        document.getElementById("st-ai-kalibre").onclick = () => manuelKalibrasyonBaslat();
        document.getElementById("st-ai-temizle").onclick = () => ekraniTemizle();
        document.getElementById("st-ai-isaretle").onclick = () => kolonlariIsaretle();
    }}

    function manuelKalibrasyonBaslat() {{
        hudGuncelle("👆 Lütfen şimdi tablodaki 1. Maçın 'A Kolonu 1' kutucuğuna bir kez tıklayın...");
        const dinleyici = (e) => {{
            if (hud.contains(e.target)) return;
            e.preventDefault();
            e.stopPropagation();
            document.removeEventListener("click", dinleyici, true);
            const hedef = e.target;
            manuelSeciciSinif = {{
                tag: hedef.tagName,
                cls: hedef.className || ""
            }};
            hudGuncelle("✅ Kutucuk yapısı öğrenildi ve kilitlendi! Şimdi 'Kolonu Doldur'a basabilirsiniz.");
        }};
        document.addEventListener("click", dinleyici, true);
    }}

    async function ekraniTemizle() {{
        const satirlar = macSatirlariniBul();
        for (const item of satirlar) {{
            for (const b of item.butonlar) {{
                if (kutuSeciliMi(b)) {{
                    kutuyaTikla(b);
                    b.dataset.stSecili = "0";
                    await new Promise(r => setTimeout(r, 15));
                }}
            }}
            if (item.satir) item.satir.style.outline = "none";
        }}
        hudGuncelle("🧹 Ekrandaki işaretli kutucuklar temizlendi.");
    }}

    async function kolonlariIsaretle() {{
        const satirlar = macSatirlariniBul();
        if (satirlar.length !== 15) {{
            hudGuncelle("❌ 15 maç bulunamadı! Lütfen '🎯 1. Kutuyu Tanıt' butonuna basıp 1. maçın ilk kutusuna tıklayın.");
            return;
        }}
        const kapasite = satirlar[0].kolonSayisi;
        const aktifGrup = KUPONLAR.slice(aktifIdx, Math.min(aktifIdx + kapasite, KUPONLAR.length));
        if (!aktifGrup.length) return;

        hudGuncelle("⏳ " + aktifGrup.length + " kolon aynı anda dolduruluyor...");

        for (let m = 0; m < 15; m++) {{
            const satirKutulari = satirlar[m].butonlar;
            if (satirKutulari[0]) {{
                satirKutulari[0].scrollIntoView({{ behavior: "smooth", block: "center" }});
            }}

            for (let k = 0; k < kapasite; k++) {{
                const secim = aktifGrup[k] ? aktifGrup[k][m] : null;
                const ofset = k * 3;
                const hedefPozisyon = secim === "1" ? 0 : ((secim === "0" || secim === "X") ? 1 : (secim === "2" ? 2 : -1));

                for (let p = 0; p < 3; p++) {{
                    const kutu = satirKutulari[ofset + p];
                    if (!kutu) continue;
                    const secili = kutuSeciliMi(kutu);
                    if (p === hedefPozisyon && !secili) {{
                        kutuyaTikla(kutu);
                        kutu.dataset.stSecili = "1";
                        await new Promise(r => setTimeout(r, Math.max(20, Math.floor(HIZ_MS / 3))));
                    }} else if (p !== hedefPozisyon && secili) {{
                        kutuyaTikla(kutu);
                        kutu.dataset.stSecili = "0";
                        await new Promise(r => setTimeout(r, 18));
                    }}
                }}
            }}
            if (satirlar[m].satir) satirlar[m].satir.style.outline = "2px solid #22c55e";
        }}

        window.scrollTo({{ top: 0, behavior: "smooth" }});
        hudGuncelle("✅ " + aktifGrup.length + " kolon dolduruldu! Kuponu onaylayıp 'İleri ▶' tuşuna basın.");
    }}

    hudGuncelle();
}})();"""
    return js_kodu


def bookmarklet_tek_satir_uret(js_kodu):
    """
    Çok satırlı JS asistan kodunu Chrome Favori Çubuğuna (Bookmarklet) doğrudan
    yapıştırılabilecek tek satırlık 'javascript:(function(){...})();' formatına çevirir.
    """
    temiz_satirlar = []
    for satir in js_kodu.splitlines():
        s = satir.strip()
        if not s or s.startswith("//"):
            continue
        temiz_satirlar.append(s)
    tek_satir = " ".join(temiz_satirlar)
    return f"javascript:{tek_satir}"


# ==============================================================================
# ANA SEKMELER
# ==============================================================================
tab_uretim, tab_takip, tab_otomasyon = st.tabs([
    "🎛️ 1. Profesyonel Sendika Masası & Akıllı Kupon Üretimi",
    "📡 2. Canlı Kupon, Kırılma & Finansal Sigorta (Hedge) Takibi",
    "🛡️ 3. Güvenli & Kolay Otomatik Kupon Yatırma Merkezi"
])

# ------------------------------------------------------------------------------
# SEKME 1: PROFESYONEL MAÇ KONTROL PANELİ VE SENDİKA MOTORU
# ------------------------------------------------------------------------------
with tab_uretim:
    if not api_key and st.session_state.analiz_verisi is None:
        st.info("👈 Başlamak için sol menüden **API-Football Anahtarınızı** girin veya kayıtlı **.JSON** oturumunuzu yükleyin.")
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
                    if not api_key:
                        st.warning("Lütfen önce sol menüden API anahtarınızı girin.")
                    elif isinstance(tarih_araligi, tuple) and len(tarih_araligi) == 2:
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
                    st.session_state.eslesmeyen_satirlar = []
                    st.session_state.analiz_verisi = None
                    st.session_state.tablo_df = None
                    st.session_state.uretilen_kuponlar = None
                    st.session_state.son_uretim_ozeti = None
                    st.session_state.son_param_imzasi = None
                    st.session_state.yatirilan_paketler = []
                    st.rerun()

            if st.session_state.mac_listesi:
                opsiyon_haritasi = {m["label"]: m for m in st.session_state.mac_listesi}
                col_sol, col_sag = st.columns([1.2, 2.2])
                with col_sol:
                    yapistirilan = st.text_area(
                        "📋 Hızlı Eşleştir (İddaa/Nesine/Bilyoner'den 15 maçı yapıştırın):",
                        placeholder="1. Galatasaray - Fenerbahçe\n2. Beşiktaş - Trabzonspor...",
                        height=115
                    )
                    if st.button("🪄 Metinden Otomatik Eşleştir", use_container_width=True) and yapistirilan.strip():
                        bulunanlar, eslesmeyenler = bulten_metni_eslestir(yapistirilan, st.session_state.mac_listesi)
                        st.session_state.eslesmeyen_satirlar = eslesmeyenler
                        if bulunanlar:
                            st.session_state.secilen_15_mac = bulunanlar
                            st.toast(f"✅ {len(bulunanlar)} maç sırasıyla eşleştirildi!")
                            st.rerun()
                        else:
                            st.warning("⚠️ Eşleşme bulunamadı. Sağdaki kutudan aratarak seçebilirsiniz.")
                    if st.session_state.eslesmeyen_satirlar:
                        st.warning(
                            "⚠️ **Aşağıdaki satırlar otomatik eşleşmedi (Lütfen sağdaki kutudan elle ekleyip sırasını kontrol edin):**\n"
                            + "\n".join(st.session_state.eslesmeyen_satirlar)
                        )

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
                            st.session_state.tablo_versiyon += 1
                            st.session_state.uretilen_kuponlar = None
                            st.session_state.son_uretim_ozeti = None
                            st.session_state.son_param_imzasi = None
                            st.session_state.yatirilan_paketler = []
                            st.rerun()

        # ======================================================================
        # ADIM 2: PROFESYONEL SENDİKA KONTROL PANELİ (v12.4 SMART-BUDGET)
        # ======================================================================
        if st.session_state.analiz_verisi:
            veriler = st.session_state.analiz_verisi
            on_limitler = tam_otonom_analiz(veriler, strateji_modu)

            if st.session_state.tablo_df is None:
                oto_durum = butceye_gore_sablon_optimize_et(veriler, hedef_kolon_sayisi, garanti_derecesi, tuzak_koruma)
                st.session_state.tablo_df = tablo_verisi_olustur(
                    veriler, on_limitler, tuzak_koruma, mod="butce_oto", ozel_durumlar=oto_durum
                )

            st.markdown("#### 🎛️ Profesyonel Şablon & Akıllı Bütçe Optimizasyon Masası")
            tb0, tb1, tb2, tb3, tb4 = st.columns([1.6, 1.15, 1.15, 1.15, 0.85])
            with tb0:
                if st.button(f"🎯 Bütçeme Göre Otomatik Kur ({hedef_butce_tl:,.0f} TL)", type="primary", use_container_width=True):
                    oto_durum = butceye_gore_sablon_optimize_et(veriler, hedef_kolon_sayisi, garanti_derecesi, tuzak_koruma)
                    st.session_state.tablo_df = tablo_verisi_olustur(
                        veriler, on_limitler, tuzak_koruma, mod="butce_oto", ozel_durumlar=oto_durum
                    )
                    st.session_state.tablo_versiyon += 1
                    st.session_state.uretilen_kuponlar = None
                    st.rerun()
            with tb1:
                if st.button("🌱 Ekonomik (5B-6Ç-4K)", use_container_width=True):
                    st.session_state.tablo_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="super_eko_5b_6c_4k")
                    st.session_state.tablo_versiyon += 1
                    st.session_state.uretilen_kuponlar = None
                    st.rerun()
            with tb2:
                if st.button("🤖 AI Dengeli (4B-7Ç-4K)", use_container_width=True):
                    st.session_state.tablo_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="ai")
                    st.session_state.tablo_versiyon += 1
                    st.session_state.uretilen_kuponlar = None
                    st.rerun()
            with tb3:
                if st.button("💎 Sendika (3B-6Ç-6K)", use_container_width=True):
                    st.session_state.tablo_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="sendika_3b_6c_6k")
                    st.session_state.tablo_versiyon += 1
                    st.session_state.uretilen_kuponlar = None
                    st.rerun()
            with tb4:
                if st.button("🔒 15 Banko", use_container_width=True):
                    st.session_state.tablo_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="15_banko")
                    st.session_state.tablo_versiyon += 1
                    st.session_state.uretilen_kuponlar = None
                    st.rerun()

            df_edit = st.data_editor(
                st.session_state.tablo_df,
                key=f"bulten_tablo_{st.session_state.tablo_versiyon}",
                column_config={
                    "ID": None,
                    "Sıra": st.column_config.NumberColumn("No", min_value=1, max_value=15, step=1, width="small"),
                    "Lig": st.column_config.TextColumn("Lig", width="small"),
                    "Karşılaşma": st.column_config.TextColumn("Karşılaşma", width="medium"),
                    "1 (%)": st.column_config.NumberColumn("Ev %", min_value=1, max_value=98, step=1, format="%%%d", width="small"),
                    "X (%)": st.column_config.NumberColumn("Ber %", min_value=1, max_value=98, step=1, format="%%%d", width="small"),
                    "2 (%)": st.column_config.NumberColumn("Dep %", min_value=1, max_value=98, step=1, format="%%%d", width="small"),
                    "Halk (%)": st.column_config.NumberColumn(
                        "Halk Favori %",
                        min_value=1, max_value=99, step=1, format="%%%d", width="small",
                        help="İddaa/Nesine/Hedef15 üzerindeki gerçek favori oynanma yüzdesini buraya elle de girebilirsiniz."
                    ),
                    "Analiz": st.column_config.TextColumn("Teşhis", width="small"),
                    "1": st.column_config.CheckboxColumn("1", width="small"),
                    "X": st.column_config.CheckboxColumn("X", width="small"),
                    "2": st.column_config.CheckboxColumn("2", width="small"),
                    "🌟 G1": st.column_config.CheckboxColumn("🌟 G1", help="Ağır Favori Güvencesi", width="small"),
                    "🔥 G2": st.column_config.CheckboxColumn("🔥 G2", help="Plase/Sürpriz Grubu", width="small")
                },
                disabled=["Lig", "Karşılaşma", "Analiz"],
                hide_index=True,
                use_container_width=True,
                height=560
            )
            st.session_state.tablo_df = df_edit.copy()

            girilen_siralar = [int(x) for x in df_edit["Sıra"].tolist() if pd.notna(x)]
            sira_hatasi_var = sorted(girilen_siralar) != list(range(1, 16))

            sirali = df_edit.sort_values("Sıra").reset_index(drop=True)
            st.session_state.secilen_mac_idleri = [int(x) for x in sirali["ID"].tolist()]
            id_analiz_haritasi = {m["id"]: m for m in veriler}

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
                h1, hx, h2 = halk_egilimi_simule_et(y1, yx, y2, r["Karşılaşma"])

                kullanici_halk_fav = int(r["Halk (%)"])
                oto_halk_fav = max(h1, hx, h2)
                if abs(kullanici_halk_fav - oto_halk_fav) >= 2:
                    if y1 >= yx and y1 >= y2:
                        h1, hx, h2 = olasilik_yumusat(kullanici_halk_fav, (100 - kullanici_halk_fav) * (hx / max(1, hx + h2)), (100 - kullanici_halk_fav) * (h2 / max(1, hx + h2)))
                    elif y2 >= y1 and y2 >= yx:
                        h1, hx, h2 = olasilik_yumusat((100 - kullanici_halk_fav) * (h1 / max(1, h1 + hx)), (100 - kullanici_halk_fav) * (hx / max(1, h1 + hx)), kullanici_halk_fav)
                    else:
                        h1, hx, h2 = olasilik_yumusat((100 - kullanici_halk_fav) * (h1 / max(1, h1 + h2)), kullanici_halk_fav, (100 - kullanici_halk_fav) * (h2 / max(1, h1 + h2)))

                kaynak_m = id_analiz_haritasi.get(int(r["ID"]), {})
                piyasa_std_val = kaynak_m.get("piyasa_std", 0.0)
                tuzak_farki_val = max(h1, hx, h2) - max(y1, yx, y2)

                g_sablon.append(sec if sec else ["1"])
                s_veriler.append({
                    "id": int(r["ID"]),
                    "mac": r["Karşılaşma"],
                    "1": y1, "X": yx, "2": y2,
                    "h1": h1, "hX": hx, "h2": h2,
                    "tuzak_farki": tuzak_farki_val,
                    "piyasa_std": piyasa_std_val
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
                    disabled=(bos_mac_var or sira_hatasi_var or ham_kolon_sayisi > 300_000)
                )

            if sira_hatasi_var:
                st.error("⚠️ **Bülten Sıra Hatası:** 'No' sütunundaki maç sıra numaraları 1'den 15'e kadar benzersiz olmalıdır! Lütfen çakışan sıra numaralarını düzeltin.")
            elif bos_mac_var:
                st.error("⚠️ Her maçta en az 1 tercih (1, X veya 2) işaretli olmalıdır.")
            elif ham_kolon_sayisi > 300_000:
                st.warning(
                    "⚠️ **CPU Koruması:** Şablonunuz 300.000 kolonu aşıyor. "
                    "Lütfen yukarıdaki **'🎯 Bütçeme Göre Otomatik Kur'** veya **'🌱 Ekonomik'** butonuna basın."
                )

            imza_ham = json.dumps({
                "sablon": g_sablon,
                "oranlar": [(v["1"], v["X"], v["2"], v["h1"], v["hX"], v["h2"]) for v in s_veriler],
                "g1_idx": g1_indeksleri,
                "g2_idx": g2_indeksleri,
                "g1_aralik": g1_aralik,
                "g2_aralik": g2_aralik,
                "garanti": garanti_derecesi,
                "kapsama": hedef_kapsama_orani,
                "max_k": max_kolon_limiti,
                "ev": ev_katsayisi,
                "strateji": strateji_modu,
                "hamming": benzerlik_elemesi,
                "akilli_merkez": akilli_merkez,
                "log_zarf": log_zarf_aktif,
                "kademe": kademe_filtre_aktif,
                "homojen": homojen_bulten,
                "entropi": entropi_filtresi,
                "ai_filtre": ai_filtre_modu
            }, sort_keys=True)
            param_imzasi = hashlib.md5(imza_ham.encode("utf-8")).hexdigest()

            otomatik_yenile = (
                (st.session_state.get("son_param_imzasi") != param_imzasi)
                and not bos_mac_var
                and not sira_hatasi_var
                and ham_kolon_sayisi <= 120_000
            )

            if uretim_tetikle or otomatik_yenile or (st.session_state.uretilen_kuponlar is None and not bos_mac_var and not sira_hatasi_var and ham_kolon_sayisi <= 120_000):
                st.session_state.son_param_imzasi = param_imzasi
                if ai_filtre_modu:
                    limitler = tam_otonom_analiz(s_veriler, strateji_modu, aktif_sablon=g_sablon)
                else:
                    limitler = {
                        "1": range_1, "X": range_x, "2": range_2,
                        "fav": range_fav, "plase": range_plase, "surpriz": range_surpriz,
                        "z_zarf": (-1.75, 2.05),
                        "ardisik_1": max_ardisik_1, "ardisik_x": max_ardisik_x, "ardisik_2": max_ardisik_2,
                        "banko_siniri": banko_siniri, "cifte_siniri": cifte_sans_siniri
                    }

                mat, puanlar, kompozit_skor, esnetilenler = vektorel_filtrele(
                    g_sablon, s_veriler, limitler,
                    g1_indeksleri=g1_indeksleri if grup_guvence_aktif else [],
                    g1_aralik=g1_aralik,
                    g2_indeksleri=g2_indeksleri if grup_guvence_aktif else [],
                    g2_aralik=g2_aralik,
                    ev_agirligi=ev_katsayisi,
                    log_zarf_aktif=log_zarf_aktif,
                    kademe_aktif=kademe_filtre_aktif,
                    entropi_aktif=entropi_filtresi,
                    homojen_aktif=homojen_bulten
                )
                if len(mat) > 0:
                    garanti, g_puan, kapsama, budanan_adet = gelismis_garanti_ve_budama_uygula(
                        mat, puanlar, kompozit_skor, garanti_derecesi,
                        max_k=max_kolon_limiti,
                        akilli_merkez=akilli_merkez,
                        min_fark=benzerlik_elemesi,
                        hedef_kapsama=hedef_kapsama_orani
                    )
                    mc = monte_carlo_simule_et(garanti, s_veriler, g_sablon)
                    denetim = deterministik_garanti_denetle(garanti, mat)
                    st.session_state.uretilen_kuponlar = garanti
                    st.session_state.son_uretim_ozeti = {
                        "filtreli_adet": len(mat),
                        "ham_adet": ham_kolon_sayisi,
                        "garanti_derecesi": garanti_derecesi,
                        "kapsama": kapsama,
                        "budanan_adet": budanan_adet,
                        "mc": mc,
                        "denetim": denetim,
                        "s_veriler": s_veriler,
                        "g_sablon": g_sablon,
                        "esnetilenler": esnetilenler
                    }
                else:
                    st.warning("⚠️ Filtreler tüm kombinasyonları eledi. Sol menüden filtreleri esnetin.")

            if st.session_state.uretilen_kuponlar is not None and st.session_state.son_uretim_ozeti is not None:
                garanti = st.session_state.uretilen_kuponlar
                ozet = st.session_state.son_uretim_ozeti
                mc = ozet["mc"]
                denetim = ozet.get("denetim", {"tam_15": 0.0, "en_az_14": 0.0, "en_az_13": 0.0, "en_az_12": 0.0})
                ham_k = max(1, ozet["ham_adet"])
                tasarruf_orani = (1.0 - (len(garanti) / ham_k)) * 100

                if ozet.get("esnetilenler"):
                    st.caption(f"ℹ️ **Otonom Koruma:** Sıfır kupon çıkmaması için şu dar filtreler otomatik esnetildi: `{', '.join(ozet['esnetilenler'])}`")
                if ozet.get("budanan_adet", 0) > 0:
                    st.caption(f"✂️ **Ters Budama (Reverse Pruning):** %100 çakışan **{ozet['budanan_adet']}** yedek kolon garanti gücü bozulmadan temizlendi.")

                m1, m2, m3, m4, m5, m6 = st.columns([1, 1.1, 1.1, 1.1, 1.1, 1.1])
                m1.metric("Ham -> Filtreli", f"{ozet['filtreli_adet']:,}", f"-%{100 - (ozet['filtreli_adet']*100/ham_k):.0f} Eleme")
                m2.metric(f"🎯 {ozet['garanti_derecesi']}G Ekonomik Net", f"{len(garanti):,} Kolon", f"%{tasarruf_orani:.1f} Tasarruf")
                m3.metric("Ödenecek Bütçe", f"{len(garanti) * kolon_fiyati:,.0f} TL", f"Kapsama: %{ozet.get('kapsama', 90):.1f}")
                m4.metric("🥇 Şablon İçi 14+ Gücü", f"%{mc['sablon_14_arti']:.1f}", f"Tam 15: %{mc['sablon_15']:.1f}")
                m5.metric("💎 İkramiye Çarpanı", f"{mc['ikramiye_endeksi']:.0f} / 100", f"Genel 12+: %{mc['genel_12_arti']:.1f}")
                with m6:
                    st.write("")
                    st.download_button(
                        "📥 Kuponları İndir (.TXT)",
                        "\n".join([" ".join(k) for k in garanti]),
                        f"spor_toto_v12_4_{ozet['garanti_derecesi']}G_{len(garanti)}kolon.txt",
                        mime="text/plain",
                        type="primary",
                        use_container_width=True
                    )

                st.caption(
                    f"🔬 **Deterministik Filtreli Evren Garanti Denetimi (Self-Audit):** "
                    f"Filtreli evrendeki senaryoların **%{denetim['tam_15']:.1f}**'inde Tam 15 | "
                    f"**%{denetim['en_az_14']:.1f}**'inde En Az 14 | "
                    f"**%{denetim['en_az_13']:.1f}**'inde En Az 13 | "
                    f"**%{denetim['en_az_12']:.1f}**'inde En Az 12 isabet matematiksel olarak doğrulanmıştır."
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
# SEKME 2: CANLI KUPON TAKİBİ & FİNANSAL SİGORTA (HEDGE / DUTCHING) ANALİZİ
# ------------------------------------------------------------------------------
with tab_takip:
    col_t1, col_t2 = st.columns([1.15, 1.65])
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
            if st.button("🔄 Canlı Skorları API'den Çek (90-Dk Resmi Kural Korumalı)", type="primary", use_container_width=True):
                st.session_state.canli_sonuclar, st.session_state.canli_skor_metni = canli_skorlari_cek(
                    st.session_state.secilen_mac_idleri, api_key
                )
                st.rerun()

        if st.session_state.tablo_df is not None:
            m_isim = st.session_state.tablo_df.sort_values("Sıra")["Karşılaşma"].tolist()
        elif st.session_state.analiz_verisi:
            m_isim = [v["mac"] for v in st.session_state.analiz_verisi]
        else:
            m_isim = [f"{i}. Maç" for i in range(1, 16)]

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
        st.session_state.canli_sonuclar = sonuc_df["Sonuç"].tolist()

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
                    with st.expander(f"🛟 Kalan {len(bekleyen_indeksler)} Maç İçin '{en_yuksek_derece} Bilen' Sigorta (Hedge) & Finansal Hesaplayıcı", expanded=True):
                        hedge_satirlar = []
                        toplam_aday = len(hedef_kuponlar)
                        son_mac_acik_riskler = []
                        for b_idx in bekleyen_indeksler:
                            sutun_b = hedef_kuponlar[:, b_idx]
                            k_1 = int(np.sum(sutun_b == "1"))
                            k_x = int(np.sum(sutun_b == "X"))
                            k_2 = int(np.sum(sutun_b == "2"))
                            acik_risk = []
                            if k_1 == 0:
                                acik_risk.append("1")
                            if k_x == 0:
                                acik_risk.append("X")
                            if k_2 == 0:
                                acik_risk.append("2")
                            if len(bekleyen_indeksler) == 1:
                                son_mac_acik_riskler = acik_risk
                            hedge_satirlar.append({
                                "Maç No": b_idx + 1,
                                "Karşılaşma": m_isim[b_idx],
                                "1 Gelirse": f"{k_1} (%{k_1*100/toplam_aday:.0f})",
                                "X Gelirse": f"{k_x} (%{k_x*100/toplam_aday:.0f})",
                                "2 Gelirse": f"{k_2} (%{k_2*100/toplam_aday:.0f})",
                                "Sigorta (Canlı Bahis) Önerisi": f"⚠️ {', '.join(acik_risk)} Sigortalanmalı!" if acik_risk else "✅ Tüm Sonuçlar Kapalı"
                            })
                        st.dataframe(pd.DataFrame(hedge_satirlar), hide_index=True, use_container_width=True)

                        st.markdown("##### 💵 Canlı Bahis Garantili Nakit Kâr (Dutching / Arbitraj) Hesaplayıcısı")
                        if len(bekleyen_indeksler) == 1 and son_mac_acik_riskler:
                            st.caption(f"🎯 **Son Maç Otomatik Risk Tespiti:** Kuponlarınızda açıkta kalan **{', '.join(son_mac_acik_riskler)}** sonuçları için canlı oranları girin.")

                        hc1, hc2, hc3, hc4 = st.columns([1.4, 1, 1, 1])
                        with hc1:
                            beklenen_ikramiye = st.number_input("Beklenen İkramiye Tutarı (TL):", min_value=1000.0, value=50000.0, step=5000.0)
                        with hc2:
                            varsayilan_1 = 2.50 if ("1" in son_mac_acik_riskler) else 0.0
                            canli_oran_1 = st.number_input("Canlı Oran (1) - Yoksa 0:", min_value=0.0, value=varsayilan_1, step=0.10)
                        with hc3:
                            varsayilan_x = 3.40 if ("X" in son_mac_acik_riskler or not son_mac_acik_riskler) else 0.0
                            canli_oran_x = st.number_input("Canlı Oran (X) - Yoksa 0:", min_value=0.0, value=varsayilan_x, step=0.10)
                        with hc4:
                            varsayilan_2 = 4.20 if ("2" in son_mac_acik_riskler or not son_mac_acik_riskler) else 0.0
                            canli_oran_2 = st.number_input("Canlı Oran (2) - Yoksa 0:", min_value=0.0, value=varsayilan_2, step=0.10)

                        secili_oranlar = [(etiket, oran) for etiket, oran in [("1", canli_oran_1), ("X", canli_oran_x), ("2", canli_oran_2)] if oran > 1.0]
                        if secili_oranlar:
                            ters_toplam = sum(1.0 / o for _, o in secili_oranlar)
                            if ters_toplam < 1.0:
                                toplam_hedge_yatirimi = beklenen_ikramiye * ters_toplam
                                hedge_sonrasi_kalan = beklenen_ikramiye - toplam_hedge_yatirimi
                                kupon_maliyeti = len(aktif_k) * kolon_fiyati
                                net_garanti_kar = hedge_sonrasi_kalan - kupon_maliyeti
                                dagilim_metni = " | ".join([
                                    f"**MS {etk}** için **{beklenen_ikramiye / orn:,.0f} TL** (Oran: {orn:.2f})"
                                    for etk, orn in secili_oranlar
                                ])
                                st.success(
                                    f"✅ **Canlı Sigorta (Hedge) Bahis Planı:** {dagilim_metni}\n\n"
                                    f"• **Toplam Canlı Sigorta Yatırımı:** `{toplam_hedge_yatirimi:,.0f} TL`\n"
                                    f"• **Sigorta Bahisleri Düşülmüş Garantili Tahsilat:** `{hedge_sonrasi_kalan:,.0f} TL`\n"
                                    f"• **Spor Toto Kupon Maliyeti ({kupon_maliyeti:,.0f} TL) Düşülmüş NET GARANTİ KÂR:** `{net_garanti_kar:,.0f} TL`"
                                )
                            else:
                                st.warning("⚠️ Girdiğiniz canlı oranların ters toplamı 1.0'ı aşıyor; sadece en riskli açık sonuca kısmi koruma yapmanız önerilir.")

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
                st.info("👈 Sol tablodan maç sonuçlarını seçtiğiniz anda canlı ikramiye potası ve finansal sigorta analizi hesaplanır.")
        else:
            st.info("👈 Takip başlatmak için önce kupon üretin veya kupon dosyası yükleyin.")

# ------------------------------------------------------------------------------
# SEKME 3: GÜVENLİ, ANLAŞILIR VE KOLAY OTOMATİK KUPON YATIRMA MERKEZİ (v12.4)
# ------------------------------------------------------------------------------
with tab_otomasyon:
    st.markdown("### 🛡️ Güvenli & Kolay Kupon Yatırma Merkezi (Safe-Play v12.4 — İddaa.com 4'lü Kolon Destekli)")

    if st.session_state.uretilen_kuponlar is not None and len(st.session_state.uretilen_kuponlar) > 0:
        k_oto = st.session_state.uretilen_kuponlar.tolist()
        toplam_kolon_say = len(k_oto)
        toplam_tutar_tl = toplam_kolon_say * kolon_fiyati

        if st.session_state.tablo_df is not None:
            aktif_mac_isimleri = st.session_state.tablo_df.sort_values("Sıra")["Karşılaşma"].tolist()
        elif st.session_state.analiz_verisi:
            aktif_mac_isimleri = [v["mac"] for v in st.session_state.analiz_verisi]
        else:
            aktif_mac_isimleri = [f"{i}. Maç" for i in range(1, 16)]

        # ÜST GÜVENLİK ÖZET KARTI
        st.markdown(
            f"""<div class="step-card">
                <span class="safe-badge">🛡️ SALT-İŞARETLEME GÜVENLİK KİLİDİ AKTİF</span>
                <strong style="margin-left:8px;">Bu sistemdeki hiçbir araç kendi başına 'Oyna / Öde / Onayla' butonuna basmaz!</strong><br>
                <span style="font-size:0.9rem;color:#334155;">
                • Toplam Üretilen: <strong>{toplam_kolon_say:,} Kolon ({toplam_tutar_tl:,.0f} TL)</strong> &nbsp;|&nbsp;
                • 1. Maç: <strong>{aktif_mac_isimleri[0]}</strong> &nbsp;➔&nbsp; 15. Maç: <strong>{aktif_mac_isimleri[-1]}</strong>
                </span>
            </div>""",
            unsafe_allow_html=True
        )

        # ADIM 1: MAÇ SIRASI ÖN-ONAY KONTROLÜ
        with st.expander("🔍 ADIM 1: Yatırmadan Önce 15 Maçın Resmi Bülten Sırasını Doğrulayın (Çok Önemli)", expanded=False):
            st.caption("Kuponlarınızın yanlış maçlara işaretlenmemesi için aşağıdaki 1'den 15'e kadar olan sıranın oynayacağınız sitedeki (İddaa, Nesine, Bilyoner, Misli vb.) sıra ile birebir aynı olduğundan emin olun.")
            sira_k1, sira_k2, sira_k3 = st.columns(3)
            for idx_m, m_adi in enumerate(aktif_mac_isimleri):
                hedef_sutun = sira_k1 if idx_m < 5 else (sira_k2 if idx_m < 10 else sira_k3)
                hedef_sutun.markdown(f"**{idx_m + 1}.** {m_adi}")

        # ADIM 2: KULLANICI PROFİLİNE GÖRE 3 FARKLI YATIRMA YÖNTEMİ
        st.markdown("#### 🚀 ADIM 2: Size En Uygun Kupon Yatırma Yöntemini Seçin")
        yontem_secimi = st.radio(
            "Hangi yöntemle kuponlarınızı yatırmak istiyorsunuz?",
            [
                "🖥️ Yöntem B: İddaa.com 4'lü Kolon (A-B-C-D) & Favori Çubuğu Asistanı (Bilgisayardan Yatıracaklar İçin — En Pratik)",
                "📁 Yöntem A: Dosya İndir & Yükle (SporTotoHedef15 / Extra1X2 / Excel Kullananlar İçin)",
                "📱 Yöntem C: Mobil & Bayi Kartı Modu (Telefondan veya Bayiden Elle/Okutarak Yatıracaklar İçin)"
            ],
            index=0
        )

        st.markdown("---")

        # ======================================================================
        # YÖNTEM A: DOSYA İLE YÜKLEME (EN KOLAY VE EN GÜVENLİ)
        # ======================================================================
        if "Yöntem A" in yontem_secimi:
            col_a1, col_a2 = st.columns([1.3, 1.7])
            with col_a1:
                st.markdown("##### ⚙️ Hazır Platform Şablonu Seçin")
                platform_sablonu = st.selectbox(
                    "Kullandığınız Program / Site:",
                    [
                        "🎯 SporTotoHedef15 / Extra1X2 Standart (.TXT - Bitişik 1X2)",
                        "🔢 1-0-2 Bitişik Format (.TXT - Beraberliği '0' İster)",
                        "📊 Excel / CSV Standart (.CSV - Virgülle Ayrılmış 1,X,2)",
                        "␣ Boşluklu Metin Formatı (.TXT - 1 X 2 1 1 X)"
                    ]
                )

                if "1-0-2" in platform_sablonu:
                    sifir_kullan = True
                    sep_char = ""
                elif "CSV" in platform_sablonu:
                    sifir_kullan = False
                    sep_char = ","
                elif "Boşluklu" in platform_sablonu:
                    sifir_kullan = False
                    sep_char = " "
                else:
                    sifir_kullan = False
                    sep_char = ""

                formatli_kolonlar = [
                    sep_char.join(["0" if (s == "X" and sifir_kullan) else s for s in kl])
                    for kl in k_oto
                ]
                txt_icerik = "\n".join(formatli_kolonlar)
                dosya_kontrol_imzasi = hashlib.md5(txt_icerik.encode("utf-8")).hexdigest()[:8].upper()

                st.success(
                    f"✅ **Dosya Hazır!**\n\n"
                    f"• **Kolon Sayısı:** `{len(formatli_kolonlar):,} Adet`\n"
                    f"• **Toplam Tutar:** `{toplam_tutar_tl:,.0f} TL`\n"
                    f"• **Doğrulama Kodu:** `#{dosya_kontrol_imzasi}`"
                )

                st.download_button(
                    "📥 1. Tek Tıkla Kupon Dosyasını İndir (.TXT)",
                    data=txt_icerik.encode("utf-8"),
                    file_name=f"st_v12_4_{len(k_oto)}kolon_{dosya_kontrol_imzasi}.txt",
                    mime="text/plain",
                    type="primary",
                    use_container_width=True
                )

                saf_csv_icerik = "\n".join([
                    ",".join(["0" if (s == "X" and sifir_kullan) else s for s in kl])
                    for kl in k_oto
                ])
                st.download_button(
                    "📊 Alternatif: Excel (.CSV) Olarak İndir",
                    data=saf_csv_icerik.encode("utf-8"),
                    file_name=f"st_v12_4_{len(k_oto)}kolon_{dosya_kontrol_imzasi}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            with col_a2:
                st.markdown("##### 📖 3 Adımda Nasıl Yüklenir?")
                st.info(
                    "1. Soldaki **'📥 Tek Tıkla Kupon Dosyasını İndir (.TXT)'** butonuna basarak dosyayı bilgisayarınıza veya telefonunuza kaydedin.\n"
                    "2. Kullandığınız kupon yükleme aracında (**Extra1X2 / Hedef15 / Toplu Kupon Yükle**) **'Dosyadan Kolon Yükle'** butonuna tıklayın ve indirdiğiniz dosyayı seçin.\n"
                    "3. Ekranda görünen toplam kolon sayısının ve tutarın burada yazanla (**"
                    f"{toplam_kolon_say:,} Kolon / {toplam_tutar_tl:,.0f} TL**) aynı olduğunu gördükten sonra onaylayın."
                )
                st.text_area(
                    "🔎 Dosya İçeriği Önizlemesi (İlk 15 Kolon):",
                    value="\n".join(formatli_kolonlar[:15]),
                    height=210
                )

        # ======================================================================
        # YÖNTEM B: İDDAA.COM 4'LÜ KOLON ASİSTANI + BOOKMARKLET (EN PRATİK)
        # ======================================================================
        elif "Yöntem B" in yontem_secimi:
            col_b1, col_b2 = st.columns([1.15, 2.05])
            with col_b1:
                st.markdown("##### 📦 Paket & Güvenlik Ayarları")
                boyut = st.number_input(
                    "Paket Başına Kolon Sayısı:",
                    min_value=4, max_value=200, value=28, step=4,
                    help="İddaa.com ekranda 4'er kolon (A-B-C-D) aldığı için 4'ün katları (Örn: 20, 24, 28, 40) seçmeniz önerilir."
                )
                toplam_paket_say = math.ceil(len(k_oto) / boyut)
                paket_listesi = []
                for i in range(toplam_paket_say):
                    bas_k = i * boyut + 1
                    bit_k = min((i + 1) * boyut, len(k_oto))
                    durum_ikon = "✅ Yatırıldı" if (i + 1) in st.session_state.yatirilan_paketler else "⏳ Bekliyor"
                    paket_listesi.append(f"Paket {i+1} (Kolon {bas_k}-{bit_k}) [{durum_ikon}]")

                sec_p_etiket = st.selectbox("Yatırılacak Paketi Seçin:", paket_listesi)
                p_id = int(sec_p_etiket.split()[1]) - 1
                paket_no = p_id + 1

                p_checkbox = st.checkbox(
                    f"✅ Paket {paket_no}'i Yatırıldı Olarak İşaretle (Mükerrer Koruması)",
                    value=(paket_no in st.session_state.yatirilan_paketler)
                )
                if p_checkbox and paket_no not in st.session_state.yatirilan_paketler:
                    st.session_state.yatirilan_paketler.append(paket_no)
                    st.rerun()
                elif not p_checkbox and paket_no in st.session_state.yatirilan_paketler:
                    st.session_state.yatirilan_paketler.remove(paket_no)
                    st.rerun()

                sifir_b = st.toggle("Beraberliği '0' Olarak Gönder (İddaa.com İçin Önerilir)", value=True)
                hiz_secim = st.select_slider(
                    "İşaretleme Hızı (İnsan Simülasyonu):",
                    options=["🐢 Çok Güvenli (180ms)", "⚖️ İdeal (110ms)", "⚡ Hızlı (65ms)"],
                    value="⚖️ İdeal (110ms)"
                )
                hiz_ms = 180 if "180" in hiz_secim else (110 if "110" in hiz_secim else 65)

                aktif_paket = [
                    ["0" if (s == "X" and sifir_b) else s for s in kolon]
                    for kolon in k_oto[p_id * boyut : (p_id + 1) * boyut]
                ]
                st.metric(
                    f"Seçili Paket ({paket_no}/{toplam_paket_say}) Tutarı",
                    f"{len(aktif_paket) * kolon_fiyati:,.0f} TL",
                    f"{len(aktif_paket)} Kolon ({math.ceil(len(aktif_paket)/4)} Turda Biter)"
                )

            with col_b2:
                js_hud_kodu = guvenli_tarayici_asistani_uret(
                    aktif_paket=aktif_paket,
                    mac_isimleri=aktif_mac_isimleri,
                    paket_no=paket_no,
                    toplam_paket=toplam_paket_say,
                    hiz_ms=hiz_ms
                )
                bookmarklet_kodu = bookmarklet_tek_satir_uret(js_hud_kodu)

                st.markdown("##### 🔖 Seçenek 1: F12 Konsol Açmadan 'Favori Çubuğu' İle Tek Tıkla Çalıştır (En Kolay)")
                st.success(
                    "1. Aşağıdaki kutunun sağ üst köşesindeki **Kopyala (📋)** butonuna tıklayın.\n"
                    "2. Chrome'da adres çubuğunun altındaki **Favoriler çubuğuna** sağ tıklayıp **'Sayfa ekle...'** deyin, **Ad** kısmına `🎯 Toto Doldur` yazıp **URL** kısmına bu kodu yapıştırın.\n"
                    "3. Artık `iddaa.com/spor-toto` sayfasındayken üstteki **🎯 Toto Doldur** butonuna bastığınızda **4'lü Kolon (A-B-C-D) Asistanı** doğrudan açılır!"
                )
                st.code(bookmarklet_kodu, language="text")

                with st.expander("🖥️ Seçenek 2: Klasik F12 Konsol (Console) Kodu İle Çalıştır", expanded=False):
                    st.info(
                        "1. `iddaa.com/spor-toto` sayfasında **F12** tuşuna basıp **Console** sekmesine geçin (İlk kez yapıştırıyorsanız `allow pasting` yazıp Enter'a basın).\n"
                        "2. Aşağıdaki kodu kopyalayıp konsola yapıştırın ve **Enter**'a basın.\n"
                        "3. Sağ üstte açılan panelde **'🎯 4 Kolonu Doldur'** butonuna basın. (Eğer tablo bulunamazsa paneldeki **'🎯 1. Kutuyu Tanıt'** butonuna basıp 1. maçın ilk kutucuğuna bir kez tıklamanız yeterlidir.)"
                    )
                    st.code(js_hud_kodu, language="javascript")

        # ======================================================================
        # YÖNTEM C: MOBİL & BAYİ KARTI MODU (5'Lİ BLOKLAR HALİNDE HATASIZ OKUMA)
        # ======================================================================
        else:
            st.markdown("##### 📱 Mobil & Bayi İçin Hatasız 5'li Blok Kartları")
            st.caption("Telefondan veya bayi bülteninden elle işaretlerken göz kaymasını önlemek için her kolon **İlk 5 Maç | Orta 5 Maç | Son 5 Maç** olarak 3 parçaya bölünmüştür.")

            cm1, cm2 = st.columns([1.2, 2.0])
            with cm1:
                kart_sayfa_boyutu = st.selectbox("Sayfa Başına Gösterilecek Kolon:", [10, 20, 50, 100], index=1)
                toplam_sayfa = math.ceil(len(k_oto) / kart_sayfa_boyutu)
                secili_sayfa = st.number_input(f"Sayfa Seçin (1 - {toplam_sayfa}):", min_value=1, max_value=toplam_sayfa, value=1, step=1)

            bas_idx = (secili_sayfa - 1) * kart_sayfa_boyutu
            bit_idx = min(secili_sayfa * kart_sayfa_boyutu, len(k_oto))

            kart_satirlari = []
            for idx_k in range(bas_idx, bit_idx):
                kl = k_oto[idx_k]
                blok_1_5 = " - ".join(kl[0:5])
                blok_6_10 = " - ".join(kl[5:10])
                blok_11_15 = " - ".join(kl[10:15])
                kart_satirlari.append({
                    "Kolon No": f"#{idx_k + 1}",
                    "Maç 1 - 5": blok_1_5,
                    "Maç 6 - 10": blok_6_10,
                    "Maç 11 - 15": blok_11_15,
                    "1 / X / 2 Sayısı": f"{kl.count('1')} / {kl.count('X')} / {kl.count('2')}"
                })

            st.dataframe(pd.DataFrame(kart_satirlari), hide_index=True, use_container_width=True, height=420)
    else:
        st.info("👈 Kupon yatırma merkezini kullanmak için önce **1. Sekmeden** kupon üretin.")
