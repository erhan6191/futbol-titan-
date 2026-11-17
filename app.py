import streamlit as st
import requests
import math
import json
import re
import hashlib
import unicodedata
import urllib.parse
import io
import csv
import zipfile
import itertools
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from datetime import datetime, timedelta
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import pandas as pd

st.set_page_config(
    page_title="Spor Toto AI Pro v15.1 — SECURE AUTO PLAY INTEGRATION — ÇEVRİMDIŞI DENETİM",
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
KULLANIM_KILAVUZU_HTML = """<html lang='tr'><meta charset='utf-8'><h1>Spor Toto AI Pro v15.1</h1><p>Matematiksel kapsama yalnızca belirtilen senaryo evreni içinde geçerlidir. Gerçek sonuç veya gelir garantisi değildir.</p><p>1. Bülten ve takımları doğrula. 2. Kaynak kalitesini kontrol et. 3. Şablon ve bütçe belirle. 4. Doğrulama raporunu incele. 5. Üçüncü sekmede bütün kolonları tek seferde doğrula. Platform etiketi seç ve kontrol raporunu incele. Yetkili sağlayıcı bağlantısı mevcut değildir; hesap bağlantısı veya ödeme yapılmaz.</p></html>"""

# --- SESSION STATE BAŞLATMA ---
varsayilan_state = {
    "mac_listesi": [],
    "secilen_15_mac": [],
    "eslesmeyen_satirlar": [],
    "analiz_verisi": None,
    "tablo_baz_df": None,      # st.data_editor için sabit referans (zıplamayı önler)
    "tablo_df": None,          # Kullanıcının anlık düzenlediği güncel tablo
    "tablo_versiyon": 0,
    "secilen_mac_idleri": [],
    "uretilen_kuponlar": None,
    "son_uretim_ozeti": None,
    "son_param_imzasi": None,
    "son_sol_menu_imzasi": None,
    "canli_sonuclar": ["⏳ Bekliyor"] * 15,
    "canli_skor_metni": ["-"] * 15,
    "kalan_kota": "Bilinmiyor",
    "yatirilan_paketler": [],
    "aktarim_kontrol15": {},
    "sema_versiyonu": "15.1"
}
for anahtar, deger in varsayilan_state.items():
    if anahtar not in st.session_state:
        st.session_state[anahtar] = deger

if st.session_state.get("sema_versiyonu") != "15.1":
    st.session_state.uretilen_kuponlar = None
    st.session_state.son_uretim_ozeti = None
    st.session_state.son_param_imzasi = None
    st.session_state.son_sol_menu_imzasi = None
    st.session_state.sema_versiyonu = "15.1"

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
    st.markdown("## 🏆 Spor Toto AI v15.1 Pro")
    st.caption("SECURE AUTO PLAY INTEGRATION — ÇEVRİMDIŞI DENETİM")
    st.warning("Deneysel analiz: matematiksel kapsama, gerçek maç isabeti veya kâr garantisi değildir.")

    st.download_button(
        label="📄 Kullanım Kılavuzunu İndir (HTML)",
        data=KULLANIM_KILAVUZU_HTML.encode("utf-8"),
        file_name="Spor_Toto_AI_v15_0_Kullanim_Kilavuzu.html",
        mime="text/html",
        use_container_width=True
    )

    api_key = st.text_input("🔑 API-Football Anahtarı:", type="password")
    if api_key:
        st.caption(f"📊 Kalan Günlük API Kotası: **{st.session_state.kalan_kota}**")

    st.markdown("---")
    st.markdown("### 🎯 1. Garanti & Ekonomik Daraltma Motoru")
    garanti_secimi = st.selectbox(
        "Matematiksel Garanti Hedefi:",
        [
            "15 hedef (tam eşleşme)",
            "14 hedef (1 hata)",
            "13 hedef (2 hata)",
            "12 hedef (3 hata)"
        ],
        index=0
    )
    garanti_derecesi = int(garanti_secimi.split()[0])

    kapsama_evreni_modu = st.radio(
        "🔒 Garanti Kapsama Evreni:",
        [
            "🛡️ Kesin Şablon Evreni (tam kapsama hedefi)",
            "🧬 Hibrit Ekonomi (G2 koşullu evren)",
            "📐 Filtreli & Şartlı Evren (yalnız kalan senaryolar)"
        ],
        index=0,
        help="Kesin şablon: ham senaryolar. Hibrit: yalnız G2 koşullu evren. Filtreli: kalan senaryolar. Bütçe modunda üst sınır geçerlidir; analiz modlarında maliyet yalnız raporlanır. Hedef ancak bağımsız denetimle doğrulanır."
    )
    mutlak_sablon_garantisi = ("Kesin Şablon" in kapsama_evreni_modu)
    hibrit_ekonomi_modu = ("Hibrit Ekonomi" in kapsama_evreni_modu)

    if garanti_derecesi == 15 and mutlak_sablon_garantisi:
        hedef_kapsama_orani = 100.0
        st.caption("🛡️ **15 Garanti Koruması:** Kesin Şablon modunda kapsama oranı otomatik olarak **%100 Tam Kapsama**'ya kilitlenmiştir.")
    else:
        tasarruf_profili = st.select_slider(
            "🌱 Akıllı Tasarruf Modu (Kapsama Oranı):",
            options=[
                "🔥 %85 koşullu olasılık kütlesi hedefi",
                "⚖️ %93 koşullu olasılık kütlesi hedefi",
                "🛡️ Tam Kapsama (%100 hedef)"
            ],
            value="🛡️ Tam Kapsama (%100 hedef)",
            help="%85/%93: model altında koşullu olasılık kütlesi. %100: evrendeki tüm senaryolar. Bütçe hedefi engelleyebilir."
        )
        if "85" in tasarruf_profili:
            hedef_kapsama_orani = 85.0
        elif "93" in tasarruf_profili:
            hedef_kapsama_orani = 93.0
        else:
            hedef_kapsama_orani = 100.0

    uretim_modu = st.radio("Üretim modu", ["Bütçe kontrollü", "Matematiksel minimum (analiz)", "12–15 karşılaştırma (analiz)"], index=0,
        help="Minimum ve karşılaştırma yalnızca maliyet/kapsama analizi yapar; bütçe sınırı yoktur. Optimum yalnızca ispat varsa gösterilir.")
    kolon_fiyati = st.number_input("Kolon Birim Fiyatı (TL):", min_value=1.0, value=10.0, step=1.0)
    hedef_butce_tl = st.number_input("Üst bütçe / şablon kurma referansı (TL):", min_value=0.0,max_value=500000.0,value=2500.0,step=50.0)
    hedef_kolon_sayisi = int(hedef_butce_tl // kolon_fiyati)
    butce_kilidi_aktif = uretim_modu == "Bütçe kontrollü"
    max_kolon_limiti = hedef_kolon_sayisi if butce_kilidi_aktif else None
    limit_metni = f"En fazla {max_kolon_limiti:,} kolon" if max_kolon_limiti is not None else "Bütçesiz analiz (oynama talimatı değildir)"
    st.caption(limit_metni)
    arsiv_upload = st.file_uploader("İsteğe bağlı geçmiş maç arşivi (CSV)", type=["csv"], key="history14", help="date,home,away,hg,ag; yalnız tamamlanmış maçlar, takım adları API ile aynı olmalıdır. Her lig için ayrı model önerilir.")
    st.caption("Kolon fiyatı ve oynanma oranları otomatik doğrulanmaz. Arşiv yoksa piyasa/API; arşiv varsa DC/Elo deneysel model. Ağırlıklar kalibre edilmemiştir.")

    aninda_otomatik_hesapla = st.toggle(
        "⚡ Tablo & Menü Değişikliklerinde Anında Senkronize Et (<= 4.000 Ham Kolon)",
        value=False,
        help="Açık olduğunda 4.000 kolona kadar olan şablonlarda yaptığınız değişiklikler anında hesaplanır. Daha geniş şablonlarda arayüzün takılmaması için '⚡ KAPSAMA HESAPLA' butonuna basarak tek tıkla üretebilirsiniz."
    )

    st.markdown("---")
    st.markdown("### 🧠 2. Sendika & Çift Kademeli Şart Motoru")
    strateji_modu = st.radio(
        "Yapay Zeka Oyun Stili:",
        [
            "⚖️ Dengeli (Log-Olasılık)",
            "🛡️ Favori Ağırlıklı (Daha Az Kolon / Yüksek İsabet)",
            "💎 İkramiye senaryosu (halk eğilimi varsayımı)"
        ]
    )

    ev_katsayisi = st.slider(
        "Simüle halk eğilimi sıralama ağırlığı:",
        min_value=0.0, max_value=1.0, value=0.20, step=0.05,
        help="Sıralama sezgisidir. Gerçek oynanma yüzdesi ve EV değildir."
    )

    grup_guvence_aktif = st.toggle("🌟 Çift Kademeli Güvence (G1 & G2) Filtresi", value=True)
    if grup_guvence_aktif:
        otonom_grup_limiti = st.checkbox("🤖 G1/G2 Sınırlarını Otomatik Ölçekle", value=True)
        if not otonom_grup_limiti:
            g1_manuel = st.slider("🌟 G1 (Ağır Favoriler) Min-Maks Sürpriz:", 0, 10, (0, 3))
            g2_manuel = st.slider("🔥 G2 (Plase/Ortada) Min-Maks Sürpriz:", 0, 12, (0, 5))
        else:
            g1_manuel, g2_manuel = None, None
    else:
        otonom_grup_limiti = False
        g1_manuel, g2_manuel = (0, 15), (0, 15)

    st.markdown("---")
    st.markdown("### 🔬 3. v15.1 Ekonomik Sıkıştırma & Yapısal Filtreler")
    ortogonal_anahtar_aktif = st.toggle(
        "🔑 Karma örtme (GF(2)/GF(3)) + kaynak sınırlı yedek",
        value=True,
        help="Tam Kartezyen evrende karma koset araması; kaynak sınırında yedek yöntem. Filtreli evrende mevcut motor kullanılır; optimum yalnızca ispatla gösterilir."
    )
    akilli_merkez = st.toggle("🧮 MILP (küçük evren) + karma örtme / yerel arama", value=True)
    arama_derinligi = st.radio("Matematiksel arama profili", ["Dengeli", "Derin"], index=0, help="Derin profil daha çok karma alfabe ve yerel arama denemesi yapar. Süre sınırlıdır; minimum ispatı yalnız doğrulanmış alt sınır veya kesin çözümle verilir.")
    log_zarf_aktif = st.toggle("📐 Normalize Shannon Log-Olasılık (Altın Koridor) Zarfı", value=True)
    kademe_filtre_aktif = st.toggle("📊 3 Kademeli (Favori/Plase/Sürpriz) Bütçesi", value=True)
    kati_filtre_kilidi = st.toggle(
        "🔒 Katı Filtre Kilidi (esnetme yok)",
        value=False,
        help="Açık olduğunda, çok dar filtreler girdiğinizde sistem filtreyi sessizce devre dışı bırakıp kupon sayısını şişirmez; seçtiğiniz şartlara sadık kalır."
    )
    homojen_bulten = st.toggle("⚖️ Alt/Üst Bülten Homojenlik Filtresi", value=False)
    entropi_filtresi = st.toggle("🌀 Yapay/Simetrik Dizilim Elemesi", value=False)
    tuzak_koruma = st.toggle("🚨 Kırılgan Halk Tuzaklarını & Kararsızları Çifteye Al", value=True)

    if garanti_derecesi == 15:
        benzerlik_elemesi = 1
        st.caption("🔒 15 hedefinde Hamming alt sınırı 1.")
    else:
        benzerlik_elemesi = st.select_slider(
            "🔍 Kuponlar Arası Min. Farklı Maç (Hamming):",
            options=[1, 2, 3, 4],
            value=1,
            help="Tam matematiksel garanti (%100 örtme ve en az kolon) için '1' önerilir. 2 veya üzeri seçildiğinde kuponlar birbirinden uzaklaşır ancak yakın kombinasyonlar elenebilir."
        )

    ai_filtre_modu = st.toggle("🤖 Şablon-Duyarlı Otonom İstatistik Sınırları", value=True)

    range_1, range_x, range_2 = (3, 10), (1, 7), (1, 8)
    range_fav, range_plase, range_surpriz = (5, 13), (1, 8), (0, 5)
    max_ardisik_1, max_ardisik_x, max_ardisik_2 = 6, 4, 4
    banko_siniri, cifte_sans_siniri = 58, 42

    if not ai_filtre_modu:
        with st.expander("⚙️ Manuel Filtre Ayarları", expanded=True):
            range_1 = st.slider("Ev Sahibi (1) Adedi", 0, 15, (3, 10))
            range_x = st.slider("Beraberlik (X) Adedi", 0, 15, (1, 7))
            range_2 = st.slider("Deplasman (2) Adedi", 0, 15, (1, 8))
            range_fav = st.slider("1. Tercih (Favori) Adedi", 0, 15, (5, 13))
            range_plase = st.slider("2. Tercih (Plase) Adedi", 0, 15, (1, 8))
            range_surpriz = st.slider("3. Tercih (Ağır Sürpriz) Adedi", 0, 10, (0, 5))
            max_ardisik_1 = st.slider("Üst Üste Maks. '1'", 2, 15, 6)
            max_ardisik_x = st.slider("Üst Üste Maks. 'X'", 2, 15, 4)
            max_ardisik_2 = st.slider("Üst Üste Maks. '2'", 2, 15, 4)
            banko_siniri = st.number_input("Banko Sınırı (%)", 35, 95, 58)
            cifte_sans_siniri = st.number_input("Çifte Şans Sınırı (%)", 30, 80, 42)

    st.markdown("---")
    st.markdown("### 💾 4. Haftalık Bülten Yedeği")
    if st.session_state.analiz_verisi is not None:
        yedek_paket = {
            "versiyon": "15.1",
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
            file_name=f"spor_toto_v15_1_oturum_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )

    yuklenen_oturum = st.file_uploader("📂 Kayıtlı Oturumu Yükle (.JSON):", type=["json"])
    if yuklenen_oturum is not None:
        if st.button("♻️ Oturumu Geri Yükle", use_container_width=True):
            try:
                veri_json = json.loads(yuklenen_oturum.getvalue().decode("utf-8"))
                ids=veri_json.get('secilen_mac_idleri',[]); av=veri_json.get('analiz_verisi') or []
                if len(ids)!=15 or len(set(ids))!=15 or len(av)!=15 or set(ids)!={v['id'] for v in av}: raise ValueError('Bülten kimlikleri geçersiz.')
                if veri_json.get('uretilen_kuponlar'):
                    arr=np.asarray(veri_json['uretilen_kuponlar']);
                    if arr.ndim!=2 or arr.shape[1]!=15 or not np.isin(arr,['1','X','2']).all(): raise ValueError('Geçersiz kolon kaydı')
                st.session_state.uretilen_kuponlar=None
                st.session_state.tablo_df=None;st.session_state.tablo_baz_df=None

                st.session_state.secilen_mac_idleri = veri_json.get("secilen_mac_idleri", [])
                st.session_state.analiz_verisi = veri_json.get("analiz_verisi")
                if veri_json.get("tablo_df"):
                    yuklenen_df = pd.DataFrame(veri_json["tablo_df"])
                    st.session_state.tablo_baz_df = yuklenen_df.copy()
                    st.session_state.tablo_df = yuklenen_df.copy()
                    st.session_state.tablo_versiyon += 1
                if veri_json.get("uretilen_kuponlar"):
                    st.session_state.uretilen_kuponlar = None  # eski üretimi yeniden hesapla
                st.session_state.son_uretim_ozeti = veri_json.get("son_uretim_ozeti")
                st.session_state.canli_sonuclar = veri_json.get("canli_sonuclar", ["⏳ Bekliyor"] * 15)
                st.session_state.canli_skor_metni = veri_json.get("canli_skor_metni", ["-"] * 15)
                st.session_state.yatirilan_paketler = veri_json.get("yatirilan_paketler", [])
                st.session_state.son_param_imzasi = None
                st.session_state.son_sol_menu_imzasi = None
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
    payload=res.json()
    if payload.get("errors"):
        raise RuntimeError(f"API hatası: {payload['errors']}")
    return payload


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
    except Exception as exc:
        st.warning(f"Bülten alınamadı ({tarih_str}): {exc}")
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
    p1, px_val, p2 = max(1.0, float(p1)), max(1.0, float(px_val)), max(1.0, float(p2))
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


def marj_arindir(odd_1, odd_x, odd_2, lig_id=203):
    odds=np.array([odd_1,odd_x,odd_2],float)
    if not np.isfinite(odds).all() or np.any(odds<=1): raise ValueError('Geçersiz oran')
    inv=1/odds
    return 100*inv/inv.sum()


def _model_birlestir(market, api, model=None, bureau=0, spread=0.):
    # Bunlar öğrenilmiş katsayılar değil; kaynak kalitesine bağlı başlangıç hipotezi.
    src=[]; w=[]
    if market is not None: src.append(np.asarray(market,float)); w.append(max(.40,min(.85,.55+.03*bureau-.02*spread)))
    if api is not None: src.append(np.asarray(api,float)); w.append(.22)
    if model is not None: src.append(np.asarray(model,float)); w.append(.25)
    if not w: return np.array([38.,30.,32.]),'VERİ YOK / varsayım'
    p=np.average([x/x.sum() for x in src],axis=0,weights=w)*100
    return p,' + '.join(k for k,x in [('Piyasa',market),('API',api),('DC/Elo',model)] if x is not None)


def _dc_elo_tahmin(arsiv, home, away, cutoff):
    # Arşiv yalnızca maç öncesinde bitmiş kayıtları içermelidir.
    from scipy.optimize import minimize
    from scipy.stats import poisson
    end=pd.to_datetime(cutoff,utc=True)
    df=arsiv[arsiv['date']<end].sort_values('date').tail(2500).copy()
    names=sorted(set(df.home)|set(df.away)); idx={t:i for i,t in enumerate(names)}
    if len(df)<80 or home not in idx or away not in idx or len(names)>180: return None
    if min(sum((df.home==t)|(df.away==t)) for t in [home,away])<5: return None
    h=df.home.map(idx).to_numpy(); a=df.away.map(idx).to_numpy(); hg=df.hg.to_numpy(int); ag=df.ag.to_numpy(int); n=len(names)
    weight=np.exp(-np.log(2)*(end-df.date).dt.total_seconds().to_numpy()/86400/180)
    def unpack(z):
        return z[0],z[1],z[2],z[3:3+n],z[3+n:]
    def obj(z):
        base,adv,rho,attack,defense=unpack(z)
        lh=np.exp(np.clip(base+adv+attack[h]+defense[a],-3,3)); la=np.exp(np.clip(base+attack[a]+defense[h],-3,3))
        tau=np.ones(len(h)); m=(hg==0)&(ag==0);tau[m]=1-lh[m]*la[m]*rho
        m=(hg==0)&(ag==1);tau[m]=1+lh[m]*rho
        m=(hg==1)&(ag==0);tau[m]=1+la[m]*rho
        m=(hg==1)&(ag==1);tau[m]=1-rho
        if np.any(tau<=0): return 1e8+1e6*np.sum(np.minimum(tau,0)**2)
        ll=hg*np.log(lh)-lh+ag*np.log(la)-la+np.log(tau)
        return -float(weight@ll)+3*(np.sum(attack**2)+np.sum(defense**2))
    z=np.zeros(3+2*n); z[0]=.2;z[1]=.2
    res=minimize(obj,z,method='L-BFGS-B',bounds=[(-1,1),(-.3,.7),(-.15,.15)]+[(-1.4,1.4)]*(2*n),options={'maxiter':100})
    if not res.success or not np.isfinite(res.fun): return None
    base,adv,rho,at,de=unpack(res.x); i,j=idx[home],idx[away]
    lh=np.exp(np.clip(base+adv+at[i]+de[j],-3,3));la=np.exp(np.clip(base+at[j]+de[i],-3,3))
    elo={t:1500. for t in names}
    for hh,aa,gg,ga in zip(df.home,df.away,hg,ag):
        e=1/(1+10**(-(elo[hh]+65-elo[aa])/400));s=1 if gg>ga else .5 if gg==ga else 0
        delta=20*(s-e);elo[hh]+=delta;elo[aa]-=delta
    # Küçük ve sınırlı Elo düzeltmesi; arşivde ayrıca kalibre edilmelidir.
    shift=np.clip((elo[home]-elo[away])/1600,-.15,.15);lh*=np.exp(shift);la*=np.exp(-shift)
    x=np.arange(16);mat=np.outer(poisson.pmf(x,lh),poisson.pmf(x,la))
    for ii,jj,tau in [(0,0,1-lh*la*rho),(0,1,1+lh*rho),(1,0,1+la*rho),(1,1,1-rho)]:
        if tau<=0: return None
        mat[ii,jj]*=tau
    mat/=mat.sum()
    return np.array([np.tril(mat,-1).sum(),np.trace(mat),np.triu(mat,1).sum()])*100


def _arsiv_oku(file):
    df=pd.read_csv(file); required={'date','home','away','hg','ag'}
    if not required<=set(df): raise ValueError('Gerekli alanlar: date,home,away,hg,ag')
    df=df[list(required)].copy();df.date=pd.to_datetime(df.date,utc=True,errors='raise')
    for c in ['hg','ag']:
        df[c]=pd.to_numeric(df[c],errors='raise')
        if not np.isfinite(df[c]).all() or (df[c]<0).any() or (df[c]%1!=0).any(): raise ValueError('Gol değerleri geçersiz.')
    if df[['home','away']].isna().any().any(): raise ValueError('Takım adı boş.')
    df.home=df.home.astype(str).str.strip();df.away=df.away.astype(str).str.strip()
    return df.drop_duplicates(['date','home','away']).sort_values('date')


def halk_egilimi_simule_et(p1, px_val, p2, mac_adi=""):
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
    hatalar=[]
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
    except Exception as exc:
        hatalar.append(str(exc))

    try:
        res_odds = api_istegi_at(f"https://v3.football.api-sports.io/odds?fixture={f_id}", api_key, timeout=6)
        if res_odds.get("response") and res_odds["response"][0].get("bookmakers"):
            for buro in res_odds["response"][0]["bookmakers"]:
                for bahis in buro.get("bets", []):
                    if bahis.get("id") == 1 or bahis.get("name") == "Match Winner":
                        degerler = {v["value"]: float(v["odd"]) for v in bahis.get("values", []) if float(v.get("odd", 0)) > 1.0}
                        if "Home" in degerler and "Draw" in degerler and "Away" in degerler:
                            p1_c, px_c, p2_c = marj_arindir(
                                degerler["Home"], degerler["Draw"], degerler["Away"], lig_id=lig_id
                            )
                            odds_list_1.append(p1_c)
                            odds_list_x.append(px_c)
                            odds_list_2.append(p2_c)
                        break
                if len(odds_list_1) >= 10:
                    break
    except Exception as exc:
        hatalar.append(str(exc))

    market=np.median(np.array([odds_list_1,odds_list_x,odds_list_2]),axis=1) if odds_list_1 else None
    spread=float(max(np.std(x) for x in [odds_list_1,odds_list_x,odds_list_2])) if odds_list_1 else 0.
    api=np.array([ai_1,ai_x,ai_2]) if pred_geldi else None
    return market,api,spread,len(odds_list_1),hatalar


def hibrit_tahminleri_al(secilen_maclar, api_key):
    sonuclar = []
    history=None
    if arsiv_upload is not None:
        try: history=_arsiv_oku(arsiv_upload)
        except Exception as exc: st.warning(f"Arşiv kullanılmadı: {exc}")
    progress = st.progress(0, text="Kaynaklar ve model tahminleri hesaplanıyor...")
    for i, mac in enumerate(secilen_maclar):
        f_id = mac["id"]
        lig_id = mac.get("lig_id", 203)
        market,api,piyasa_std,bureau,hatalar = tek_mac_analiz_cek(f_id, api_key, lig_id=lig_id)
        model=None
        if history is not None:
            try:
                # Bugün başlamadan önceki veri; ileri tarihli fikstür için de bugünü geçme.
                cutoff=min(pd.to_datetime(mac['tarih'],utc=True),pd.Timestamp.now(tz='UTC').normalize())
                model=_dc_elo_tahmin(history,mac['ev'],mac['dep'],cutoff)
            except Exception as exc: hatalar.append(f"Arşiv modeli: {exc}")
        p,kaynak=_model_birlestir(market,api,model,bureau,piyasa_std)
        g1,gx,g2=olasilik_yumusat(*p)
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
            "piyasa_std": piyasa_std,
            "kaynak":kaynak,"buro_sayisi":bureau,"veri_uyarilari":hatalar,
            "snapshot_utc":datetime.utcnow().isoformat()+"Z"
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
        r"\b(fk|sk|as|fc|ac|sc|cf|cd|ud|rc|rcd|sv|vfb|vfl|tsg|1899|1907|spor|belediyespor|club|caykur|atakas|rams|bellona|iklimlendirme|corendon)\b",
        " ",
        s
    )
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return " ".join(s.split())


def bulten_metni_eslestir(yapistirilan_metin, havuz_maclari):
    satirlar = [s.strip() for s in yapistirilan_metin.splitlines() if len(s.strip()) > 2]
    eslesen_maclar = []
    eslesmeyen_satirlar = []
    kullanilan_idler = set()

    for idx_s, satir in enumerate(satirlar):
        temiz_satir = re.sub(r"^\d+[\.\-\)\s]+", "", satir).strip()
        parcalar = re.split(r"\s+[-–—]\s+|\s+[vV][sS]?\.?\s+", temiz_satir, maxsplit=1)
        metin_adayi = metin_temizle(temiz_satir)
        if len(metin_adayi) < 3:
            continue

        ev_aday = metin_temizle(parcalar[0]) if len(parcalar) == 2 else ""
        dep_aday = metin_temizle(parcalar[1]) if len(parcalar) == 2 else ""

        en_iyi_skor = 0.0
        ikinci_skor = 0.0
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
                ikinci_skor = en_iyi_skor
                en_iyi_skor = toplam_skor
                en_iyi_mac = m
            elif toplam_skor > ikinci_skor:
                ikinci_skor = toplam_skor

        if en_iyi_mac and en_iyi_skor >= 0.85 and en_iyi_skor-ikinci_skor >= 0.10:
            eslesen_maclar.append(en_iyi_mac)
            kullanilan_idler.add(en_iyi_mac["id"])
            if len(eslesen_maclar) == 15:
                break
        else:
            eslesmeyen_satirlar.append(f"Satır {idx_s + 1}: {satir}")

    return eslesen_maclar, eslesmeyen_satirlar


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
                    dakika = md["fixture"]["status"].get("elapsed")
                    ft_skor = md.get("score", {}).get("fulltime", {})

                    if durum in ["FT", "AET", "PEN"]:
                        if ft_skor.get("home") is not None and ft_skor.get("away") is not None:
                            eg, dg = ft_skor["home"], ft_skor["away"]
                        elif durum == "FT":
                            eg, dg = md["goals"]["home"], md["goals"]["away"]
                        else:
                            eg,dg=None,None
                        if eg is not None and dg is not None:
                            ek_bilgi = " (90' MS)" if durum in ["AET", "PEN"] else " (✅ MS)"
                            skor_metinleri[idx] = f"{eg} - {dg}{ek_bilgi}"
                            yeni_sonuclar[idx] = "1" if eg > dg else ("X" if eg == dg else "2")
                    elif durum in ["1H", "HT", "2H", "ET", "BT", "LIVE"] and md["goals"]["home"] is not None:
                        eg, dg = md["goals"]["home"], md["goals"]["away"]
                        dk_str = f" {dakika}'" if dakika else ""
                        skor_metinleri[idx] = f"{eg} - {dg} (🔴 {durum}{dk_str})"
                        yeni_sonuclar[idx] = "⏳ Bekliyor"
                    elif durum in ["PST", "CANC", "ABD", "SUSP", "INT"]:
                        skor_metinleri[idx] = f"⚠️ Ertelendi/Kura ({durum})"
                        yeni_sonuclar[idx] = "🎲 Kura (1/X/2)"
    except Exception as exc:
        st.warning(f"Skor güncellenmedi: {exc}")
        return st.session_state.canli_sonuclar,st.session_state.canli_skor_metni
    return yeni_sonuclar, skor_metinleri


# ==============================================================================
# v15.1 ULTRA HIZLI ŞABLON KURUCU, TEK GEÇİŞLİ ORTOGONAL & 2-OPT MOTORU
# ==============================================================================
def akilli_cifte_sec(v):
    return sorted(['1','X','2'],key=lambda k:v[k],reverse=True)[:2]


def butceye_gore_sablon_optimize_et(veriler, hedef_kolon, garanti_derecesi, mutlak_mod=True, hibrit_mod=False, tuzak_aktif=True):
    # Muhafazakâr ham şablon DP: her ham kolon bütçeye sığar. Daraltma potansiyeli ayrıca raporlanır.
    limit=max(1,min(160000,int(hedef_kolon))) # sıfır bütçede üretim motoru boş sonuç döndürür
    dp={1:(0.,[])}
    for v in veriler:
        probs=sorted([v[k]/100 for k in ('1','X','2')],reverse=True)
        new={}
        for n,(score,path) in dp.items():
            for k in (1,2,3):
                m=n*k
                if m>limit: continue
                val=score+math.log(max(1e-12,sum(probs[:k])))
                if m not in new or val>new[m][0]:new[m]=(val,path+[k])
        dp=new
    return max(dp.values(),key=lambda x:x[0])[1]


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

    aralik_1 = (max(banko_1, int(round(exp_1)) - 3), min(acik_1, int(round(exp_1)) + 3))
    aralik_x = (max(banko_x, max(0, int(round(exp_x)) - 3)), min(acik_x, int(round(exp_x)) + 3))
    aralik_2 = (max(banko_2, int(round(exp_2)) - 3), min(acik_2, int(round(exp_2)) + 3))

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
        fav_aralik = (max(zorunlu_fav, int(round(exp_fav)) - 2), min(acik_fav, int(round(exp_fav)) + 3))
        plase_aralik = (max(zorunlu_plase, int(round(exp_plase)) - 3), min(acik_plase, int(round(exp_plase)) + 2))
        surpriz_aralik = (zorunlu_surp, min(acik_surp, max(zorunlu_surp + 2, int(math.ceil(exp_surp)) + 2)))
        z_zarf = (-1.65, 2.50)
    elif "İkramiye" in strateji:
        fav_aralik = (max(zorunlu_fav, int(round(exp_fav)) - 4), min(acik_fav, max(zorunlu_fav + 2, int(round(exp_fav)) + 2)))
        plase_aralik = (max(zorunlu_plase, int(round(exp_plase)) - 2), min(acik_plase, int(round(exp_plase)) + 3))
        surpriz_aralik = (max(zorunlu_surp, int(round(exp_surp)) - 2), min(acik_surp, max(zorunlu_surp + 3, int(math.ceil(exp_surp)) + 3)))
        z_zarf = (-2.35, 1.85)
    else:
        fav_aralik = (max(zorunlu_fav, int(round(exp_fav)) - 3), min(acik_fav, int(round(exp_fav)) + 3))
        plase_aralik = (max(zorunlu_plase, int(round(exp_plase)) - 3), min(acik_plase, int(round(exp_plase)) + 3))
        surpriz_aralik = (zorunlu_surp, min(acik_surp, max(zorunlu_surp + 2, int(math.ceil(exp_surp)) + 2)))
        z_zarf = (-1.95, 2.25)

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
        "ardisik_1": 15,
        "ardisik_x": 15,
        "ardisik_2": 15,
        "banko_siniri": ai_banko,
        "cifte_siniri": ai_cifte,
        "zorluk_skoru": hz
    }


def teshis_etiketi_hesapla(en_b_oran, tuzak_farki, piyasa_std):
    kirilgan_tuzak_mi = (42 <= en_b_oran <= 57) and (tuzak_farki >= 9)
    kararsiz_mi = piyasa_std >= 2.2
    if en_b_oran >= 56 and not kararsiz_mi:
        return "🔒 Yüksek model olasılığı"
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


def analitik_shannon_parametreleri(sablon, mac_verileri):
    toplam_mu = 0.0
    toplam_var = 0.0
    norm_log_mat = np.zeros((15, 3), dtype=np.float32)
    harita = {"1": 0, "X": 1, "2": 2}

    for m_i, (v, s) in enumerate(zip(mac_verileri, sablon)):
        if len(s) <= 1:
            sec_kod = harita[s[0]]
            norm_log_mat[m_i, sec_kod] = 0.0
            continue
        p_ham = np.array([max(1.0, float(v[k])) for k in s], dtype=float)
        p_norm = p_ham / np.sum(p_ham)
        log_p = np.log(np.maximum(p_norm, 1e-4))
        for idx_k, k in enumerate(s):
            norm_log_mat[m_i, harita[k]] = float(log_p[idx_k])

        beklenen_log = float(np.sum(p_norm * log_p))
        beklenen_kare = float(np.sum(p_norm * (log_p ** 2)))
        toplam_mu += beklenen_log
        toplam_var += max(0.0, beklenen_kare - (beklenen_log ** 2))

    return toplam_mu, math.sqrt(max(1e-6, toplam_var)), norm_log_mat


def vektorel_filtrele(
    sablon, mac_verileri, limitler,
    g1_indeksleri, g1_aralik,
    g2_indeksleri, g2_aralik,
    ev_agirligi=0.20,
    log_zarf_aktif=True,
    kademe_aktif=True,
    entropi_aktif=False,
    homojen_aktif=False,
    kati_filtre=False
):
    harita = {"1": 0, "X": 1, "2": 2}
    ters = np.array(["1", "X", "2"])
    grids = np.meshgrid(*[[harita[s] for s in m] for m in sablon], indexing="ij")
    ham_matris = np.stack(grids, axis=-1).reshape(-1, 15).astype(np.int8)
    matris = ham_matris
    esnetilenler = []

    min_kabul_edilebilir = 1 if kati_filtre else max(1, min(8, len(ham_matris) // 20))

    oran_mat = np.array([[v["1"], v["X"], v["2"]] for v in mac_verileri], dtype=np.float32)
    halk_mat = np.array([[v["h1"], v["hX"], v["h2"]] for v in mac_verileri], dtype=np.float32)

    sira_mat = np.argsort(-oran_mat, axis=1)
    kademe_haritasi = np.zeros((15, 3), dtype=np.int8)
    for m_i in range(15):
        kademe_haritasi[m_i, sira_mat[m_i, 0]] = 0
        kademe_haritasi[m_i, sira_mat[m_i, 1]] = 1
        kademe_haritasi[m_i, sira_mat[m_i, 2]] = 2

    def filtre_uygula(mevcut_mat, maske, etiket):
        kalan = int(np.sum(maske))
        if kati_filtre:
            return mevcut_mat[maske]
        if kalan >= min_kabul_edilebilir or (kalan > 0 and len(mevcut_mat) < min_kabul_edilebilir):
            return mevcut_mat[maske]
        esnetilenler.append(etiket)
        return mevcut_mat

    c1 = np.sum(matris == 0, axis=1)
    cx = np.sum(matris == 1, axis=1)
    c2 = np.sum(matris == 2, axis=1)
    maske_1x2 = (
        (c1 >= limitler["1"][0]) & (c1 <= limitler["1"][1]) &
        (cx >= limitler["X"][0]) & (cx <= limitler["X"][1]) &
        (c2 >= limitler["2"][0]) & (c2 <= limitler["2"][1])
    )
    matris = filtre_uygula(matris, maske_1x2, "1-X-2 Adet Sınırı")

    if len(g1_indeksleri) > 0 and len(matris) > 0:
        g1_idx = np.array(g1_indeksleri, dtype=int)
        g1_kademeler = kademe_haritasi[g1_idx[None, :], matris[:, g1_idx]]
        g1_hatalar = np.sum(g1_kademeler > 0, axis=1)
        m_g1 = (g1_hatalar >= g1_aralik[0]) & (g1_hatalar <= g1_aralik[1])
        matris = filtre_uygula(matris, m_g1, "G1 Favori Güvencesi")

    if len(g2_indeksleri) > 0 and len(matris) > 0:
        g2_idx = np.array(g2_indeksleri, dtype=int)
        g2_kademeler = kademe_haritasi[g2_idx[None, :], matris[:, g2_idx]]
        g2_surprizler = np.sum(g2_kademeler > 0, axis=1)
        m_g2 = (g2_surprizler >= g2_aralik[0]) & (g2_surprizler <= g2_aralik[1])
        matris = filtre_uygula(matris, m_g2, "G2 Plase/Sürpriz Filtresi")

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
        matris = filtre_uygula(matris, maske_kademe, "Favori/Plase/Sürpriz Bütçesi")

    if log_zarf_aktif and len(matris) > 0:
        teo_mu, teo_sigma, norm_log_mat = analitik_shannon_parametreleri(sablon, mac_verileri)
        if teo_sigma > 1e-4:
            log_l = np.sum(norm_log_mat[np.arange(15), matris], axis=1)
            z_skor = (log_l - teo_mu) / teo_sigma
            z_alt, z_ust = limitler.get("z_zarf", (-1.95, 2.25))
            maske_log = (z_skor >= z_alt) & (z_skor <= z_ust)
            matris = filtre_uygula(matris, maske_log, "Shannon Log-Olasılık Zarfı")

    for deger, anahtar, etiket in [(0, "ardisik_1", "Ardışık 1"), (1, "ardisik_x", "Ardışık X"), (2, "ardisik_2", "Ardışık 2")]:
        max_ard = int(limitler[anahtar])
        if 1 <= max_ard < 15 and len(matris) > 0:
            pencereler = sliding_window_view(matris == deger, window_shape=max_ard + 1, axis=1)
            ardisik_ihlal = np.any(np.all(pencereler, axis=2), axis=1)
            matris = filtre_uygula(matris, ~ardisik_ihlal, etiket)

    if homojen_aktif and len(matris) > 0:
        sec_kademe_h = kademe_haritasi[np.arange(15), matris]
        ilk_yari_surpriz = np.sum(sec_kademe_h[:, :7] == 2, axis=1)
        son_yari_surpriz = np.sum(sec_kademe_h[:, 7:] == 2, axis=1)
        homojen_maske = (ilk_yari_surpriz <= 3) & (son_yari_surpriz <= 3)
        matris = filtre_uygula(matris, homojen_maske, "Alt/Üst Homojenlik")

    if entropi_aktif and len(matris) > 0:
        gecis_sayisi = np.sum(matris[:, 1:] != matris[:, :-1], axis=1)
        periyot_3 = np.sum(matris[:, 3:] == matris[:, :-3], axis=1)
        entropi_maske = (gecis_sayisi >= 4) & (gecis_sayisi <= 14) & (periyot_3 <= 10)
        matris = filtre_uygula(matris, entropi_maske, "Simetrik Dizilim (Entropi)")

    hibrit_maske = np.ones(len(ham_matris), dtype=bool)
    ham_kademeler = kademe_haritasi[np.arange(15), ham_matris]
    toplam_agir_surpriz = np.sum(ham_kademeler == 2, axis=1)

    if len(g2_indeksleri) >= 1:
        g2_idx_h = np.array(g2_indeksleri, dtype=int)
        g2_surp_h = np.sum(ham_kademeler[:, g2_idx_h] > 0, axis=1)
        g2_agir_h = np.sum(ham_kademeler[:, g2_idx_h] == 2, axis=1)
        hibrit_maske &= (
            (g2_surp_h >= g2_aralik[0]) &
            (g2_surp_h <= g2_aralik[1]) &
            (g2_agir_h <= max(1, int(math.ceil(g2_aralik[1] * 0.65))))
        )
    if not kati_filtre and int(np.sum(hibrit_maske)) < 4:
        esnetilenler.append("Hibrit G2 (çok dar)")
        hibrit_matris = ham_matris
    else:
        hibrit_matris = ham_matris[hibrit_maske]

    secilen_oranlar = oran_mat[np.arange(15), matris]
    secilen_halk = halk_mat[np.arange(15), matris]
    puanlar = np.sum(secilen_oranlar, axis=1)

    log_gercek = np.sum(np.log(np.maximum(secilen_oranlar, 1.0) / 100.0), axis=1)
    log_halk = np.sum(np.log(np.maximum(secilen_halk, 1.0) / 100.0), axis=1)
    kompozit_skor = log_gercek - (ev_agirligi * 0.24 * log_halk)

    ham_oranlar = oran_mat[np.arange(15), ham_matris]
    ham_halk = halk_mat[np.arange(15), ham_matris]
    ham_puanlar = np.sum(ham_oranlar, axis=1)
    ham_log_gercek = np.sum(np.log(np.maximum(ham_oranlar, 1.0) / 100.0), axis=1)
    ham_log_halk = np.sum(np.log(np.maximum(ham_halk, 1.0) / 100.0), axis=1)
    ham_kompozit = ham_log_gercek - (ev_agirligi * 0.24 * ham_log_halk)
    ham_idx = np.argsort(ham_kompozit)[::-1]

    hib_oranlar = oran_mat[np.arange(15), hibrit_matris]
    hib_halk = halk_mat[np.arange(15), hibrit_matris]
    hib_puanlar = np.sum(hib_oranlar, axis=1)
    hib_log_gercek = np.sum(np.log(np.maximum(hib_oranlar, 1.0) / 100.0), axis=1)
    hib_log_halk = np.sum(np.log(np.maximum(hib_halk, 1.0) / 100.0), axis=1)
    hib_kompozit = hib_log_gercek - (ev_agirligi * 0.24 * hib_log_halk)
    hib_idx = np.argsort(hib_kompozit)[::-1]

    idx = np.argsort(kompozit_skor)[::-1]
    return (
        ters[matris[idx]], puanlar[idx], kompozit_skor[idx], esnetilenler,
        ters[ham_matris[ham_idx]], ham_puanlar[ham_idx], ham_kompozit[ham_idx],
        ters[hibrit_matris[hib_idx]], hib_puanlar[hib_idx], hib_kompozit[hib_idx]
    )


def _kodla(a):
    a = np.asarray(a)
    if a.ndim != 2 or a.shape[1] != 15 or not np.all(np.isin(a,['1','X','2'])):
        raise ValueError('15 sütunlu 1/X/2 dizisi gerekli.')
    return np.where(a=='X',1,np.where(a=='2',2,0)).astype(np.int8)


def _en_yakin_isabet(secilen, evren):
    a,b = _kodla(secilen),_kodla(evren)
    if not len(a): return np.full(len(b),-1,dtype=np.int8)
    if not len(b): return np.empty(0,dtype=np.int8)
    if len(a)*len(b) <= 2_000_000:
        sonuc=[]
        for i in range(0,len(b),256):
            x=b[i:i+256]; best=np.zeros(len(x),dtype=np.int8)
            for j in range(0,len(a),512):
                best=np.maximum(best,(x[:,None,:]==a[None,j:j+512,:]).sum(axis=2).max(axis=1))
            sonuc.extend(best)
        return np.asarray(sonuc,dtype=np.int8)
    # Hamming uzaklık dönüşümü: bütün 3^15 durum, 14.35 MB uint8.
    # Sabit aday sütunlarını çıkarıp hedefe bu sütunların hatasını sonradan ekle.
    deg=np.any(a!=a[0],axis=0); m=int(deg.sum())
    sabit_hata=(b[:,~deg]!=a[0,~deg]).sum(axis=1)
    if m==0: return (15-sabit_hata).astype(np.int8)
    d=np.full((3,)*m,16,dtype=np.uint8)
    d[tuple(a[:,deg].T)]=0
    for ax in range(m):
        z=np.moveaxis(d,ax,0)
        min_z=z.min(axis=0)+1
        np.minimum(z,min_z[None,...],out=z)
    return (15-sabit_hata-d[tuple(b[:,deg].T)]).astype(np.int8)


def deterministik_garanti_denetle(secilen_kolonlar, hedef_evren):
    if not len(hedef_evren) or not len(secilen_kolonlar):
        return dict.fromkeys(['tam_15','en_az_14','en_az_13','en_az_12'],0.0)
    h=_en_yakin_isabet(secilen_kolonlar,hedef_evren)
    return {k:float(100*np.mean(h>=t)) for k,t in [('tam_15',15),('en_az_14',14),('en_az_13',13),('en_az_12',12)]}


def _kutle(kolonlar, veriler):
    kod=_kodla(kolonlar)
    p=np.array([[v[k] for k in ('1','X','2')] for v in veriler],dtype=float)
    p=np.maximum(p,1e-12); p/=p.sum(axis=1,keepdims=True)
    return np.prod(p[np.arange(15),kod],axis=1)


def _kure_siniri(code, r):
    # Her koordinat için gözlenen alfabe. Adaylar hedef evrenin içindedir.
    coeff=[1]+[0]*r
    for col in code.T:
        t=len(np.unique(col))-1
        for j in range(r,0,-1): coeff[j]+=t*coeff[j-1]
    return sum(coeff)


def _komsuluk_grafigi(code,r,limit=8_000_000):
    """Hamming komşuluklarını yoğun N x N matris olmadan oluşturur."""
    from scipy import sparse
    from itertools import combinations, product
    n=len(code); dims=[i for i in range(15) if len(np.unique(code[:,i]))>1]
    ball=_kure_siniri(code,r)
    if n*ball>limit: return None
    # Kodları koordinat başına 0..q-1'e sıkıştır; karışık taban.
    digits=np.zeros((n,len(dims)),np.int64); qs=[]
    for j,i in enumerate(dims):
        vals=np.unique(code[:,i]); qs.append(len(vals)); digits[:,j]=np.searchsorted(vals,code[:,i])
    radix=np.cumprod([1]+qs[:-1],dtype=np.int64) if dims else np.array([],np.int64)
    keys=digits@radix; order=np.argsort(keys); sortedkeys=keys[order]
    idx=np.arange(n,dtype=np.int32); rows=[idx]; cols=[idx]
    for size in range(1,min(r,len(dims))+1):
        for chosen in combinations(range(len(dims)),size):
            for shifts in product(*(range(1,qs[j]) for j in chosen)):
                key=keys.copy()
                for j,shift in zip(chosen,shifts):
                    key+=(((digits[:,j]+shift)%qs[j])-digits[:,j])*radix[j]
                pos=np.searchsorted(sortedkeys,key); valid=pos<n
                valid &= sortedkeys[np.minimum(pos,n-1)]==key
                if valid.any(): rows.append(idx[valid]);cols.append(order[pos[valid]].astype(np.int32))
    rr=np.concatenate(rows);cc=np.concatenate(cols)
    graph=sparse.csr_matrix((np.ones(len(rr),dtype=np.uint8),(rr,cc)),shape=(n,n))
    return graph


def _eski_kapsama_motoru(kolonlar,puanlar,kompozit_skor,hedef,
    max_k=None,akilli_merkez=True,min_fark=1,hedef_kapsama=100.0,
    tam_evren_kolonlar=None,tam_evren_puanlar=None,tam_evren_kompozit=None,
    sablon=None,ortogonal_aktif=True,veriler=None):
    from itertools import combinations
    import heapq
    if tam_evren_kolonlar is not None:
        kolonlar,puanlar,kompozit_skor=tam_evren_kolonlar,tam_evren_puanlar,tam_evren_kompozit
    a=np.asarray(kolonlar).reshape(-1,15);p=np.asarray(puanlar);s=np.asarray(kompozit_skor)
    n=len(a); hedef=int(hedef);r=15-hedef;k=n if max_k is None else min(n,max(0,int(max_k)))
    target=float(hedef_kapsama)/100; min_fark=1 if r==0 else int(min_fark)
    if not 0<=r<=3 or not 0<target<=1:raise ValueError('Geçersiz kapsama hedefi')
    meta=dict(durum='BOŞ',alt_sinir=None,optimal=False,kapsama_adet=0.,kapsama_kutle=0.,hedef_tam=False,yontem='',sinir_evrende=n,bütçe_limiti=max_k)
    _eski_kapsama_motoru.meta=meta
    if not n:return a[:0],p[:0],0.,0,0
    code=_kodla(a);order=np.argsort(-s,kind='stable');rank=np.empty(n,int);rank[order]=np.arange(n)
    w=_kutle(a,veriler) if veriler is not None else np.ones(n);w=w/w.sum()
    alt=math.ceil(n/_kure_siniri(code,r)) if target==1 else None
    meta['alt_sinir']=alt
    if not k: meta['durum']='SIFIR BÜTÇE'; return a[:0],p[:0],0.,0,0
    sel=[];budanan=0;graph=None
    if r==0:
        o=np.argsort(-w,kind='stable'); need=n if target==1 else int(np.searchsorted(np.cumsum(w[o]),target-1e-12)+1)
        sel=o[:min(k,need)].tolist();meta.update(yontem='Tam eşleşme / minimum',alt_sinir=need,optimal=len(sel)==need)
    else:
        try: graph=_komsuluk_grafigi(code,r)
        except ImportError: graph=None
        if graph is not None:
            degree=np.diff(graph.indptr)
            if target==1:alt=math.ceil(n/int(degree.max()));meta['alt_sinir']=alt
            meta['yontem']='Seyrek Hamming + dinamik greedy + ters budama'
            weights=np.ones(n) if target==1 else w
            goal=float(n) if target==1 else target
            def nbr(j):return graph.indices[graph.indptr[j]:graph.indptr[j+1]]
            # Greedy: güncel marjinal kazanç; tembel heap, gerçek kazanç doğrulanır.
            initial=graph@weights;heap=[(-float(initial[j]),int(rank[j]),j) for j in range(n)];heapq.heapify(heap)
            uncovered=np.ones(n,bool);covered=0.;eligible=np.ones(n,bool)
            while heap and len(sel)<k and covered<goal-1e-10:
                old,rr,j=heapq.heappop(heap)
                if not eligible[j]:continue
                ids=nbr(j);gain=float(weights[ids[uncovered[ids]]].sum())
                if gain<=0:continue
                if gain < -old-1e-12:heapq.heappush(heap,(-gain,rr,j));continue
                sel.append(j);uncovered[ids]=False;covered+=gain;eligible[j]=False
                if min_fark>1:eligible &= (code!=code[j]).sum(axis=1)>=min_fark
            counts=np.zeros(n,np.int32)
            for j in sel:counts[nbr(j)]+=1
            if akilli_merkez:
                keep=[]
                for j in reversed(sel):
                    ids=nbr(j);lost=ids[counts[ids]==1];loss=float(weights[lost].sum())
                    if covered-loss>=goal-1e-10:
                        counts[ids]-=1;covered-=loss;budanan+=1
                    else:keep.append(j)
                sel=list(reversed(keep))
            if target==1 and min_fark==1 and akilli_merkez and n<=900 and len(sel)!=alt:
                try:
                    from scipy.optimize import milp,Bounds,LinearConstraint
                    from scipy.sparse import vstack,csr_matrix
                    upper=min(k,len(sel)-1) if np.all(counts>0) else k
                    if upper>=alt:
                        mat=vstack([graph.astype(float),csr_matrix(np.ones((1,n)))],format='csr')
                        res=milp(np.ones(n),integrality=np.ones(n),bounds=Bounds(0,1),constraints=LinearConstraint(mat,np.r_[np.ones(n),0],np.r_[np.full(n,np.inf),upper]),options={'time_limit':15.,'mip_rel_gap':0.})
                        if res.x is not None:
                            trial=np.flatnonzero(res.x>.5)
                            if len(trial)<=upper and np.all(np.asarray(graph[:,trial].sum(axis=1)).ravel()>0):
                                sel=trial.tolist();meta.update(yontem='MILP / HiGHS',optimal=res.status==0)
                        elif res.status==2 and np.all(counts>0) and upper==len(sel)-1:
                            meta.update(yontem='Greedy + MILP daha küçük çözüm yok',optimal=True)
                        bound=getattr(res,'mip_dual_bound',None)
                        if bound is not None and np.isfinite(bound):meta['alt_sinir']=max(alt,int(math.ceil(bound-1e-7)))
                except (ImportError,ValueError,RuntimeError):pass
        else:
            # Büyük evren: garantisi bağımsız doğrulanan bölümleme; kaynak sınırı.
            varying=np.flatnonzero(np.any(code!=code[0],axis=0));free=min(r,len(varying));radix=3**np.arange(15,dtype=np.int64);allkey=code@radix
            best=None;best_n=n+1;opts=list(combinations(varying.tolist(),free))
            if not ortogonal_aktif:opts=opts[:1]
            if len(opts)>24:opts=[opts[i] for i in np.linspace(0,len(opts)-1,24,dtype=int)]
            for dims in opts:
                keys=allkey-(code[:,dims]@radix[list(dims)] if dims else 0)
                _,inv=np.unique(keys,return_inverse=True);inv=inv.ravel();cnt=int(inv.max())+1
                if cnt<best_n:best_n=cnt;best=inv
            inv=best;masses=np.bincount(inv,weights=w,minlength=best_n);rep=np.full(best_n,n,int);np.minimum.at(rep,inv[order],np.arange(n));reps=order[rep]
            total=0.;meta['yontem']='Büyük evren: Hamming bölümleme (yaklaşık)'
            for g in np.argsort(-masses,kind='stable'):
                if len(sel)>=k or (target<1 and total>=target-1e-12):break
                j=int(reps[g])
                if min_fark>1 and (len(sel)>=2000 or (sel and np.any((code[sel]!=code[j]).sum(axis=1)<min_fark))):continue
                sel.append(j);total+=masses[g]
    out=a[sel];hits=_en_yakin_isabet(out,a);mask=hits>=hedef;adet=float(mask.mean()*100);mass=float(w[mask].sum()*100)
    ok=bool(mask.all()) if target==1 else mass>=hedef_kapsama-1e-8
    if ok and target==1 and meta['alt_sinir']==len(sel):meta['optimal']=True
    meta.update(durum='HEDEF DOĞRULANDI' if ok else 'HEDEF SAĞLANAMADI',hedef_tam=ok,kapsama_adet=adet,kapsama_kutle=mass,optimal=bool(meta['optimal'] and ok))
    return out,p[sel],adet if target==1 else mass,budanan,0



class _OrtukKomsuluk143:
    """Karışık taban Hamming komşulukları, bloklar halinde; N×N matris yok."""
    def __init__(self, code, r):
        from itertools import combinations, product
        self.n=len(code); self.code=code; self.r=r
        self.dims=[i for i in range(15) if len(np.unique(code[:,i]))>1]
        self.vals=[np.unique(code[:,i]) for i in self.dims]
        self.q=[len(v) for v in self.vals]; self.radix=np.cumprod([1]+self.q[:-1],dtype=np.int64) if self.q else np.empty(0,np.int64)
        self.digits=np.column_stack([np.searchsorted(v,code[:,i]) for i,v in zip(self.dims,self.vals)]).astype(np.int32) if self.q else np.empty((self.n,0),np.int32)
        self.keys=(self.digits@self.radix).astype(np.int32)
        self.size=math.prod(self.q); self.ball=_kure_siniri(code,r)
        if self.size>3_000_000 or self.n*self.ball>125_000_000: raise OverflowError('Kaynak sınırı')
        self.lookup=np.full(self.size,-1,np.int32); self.lookup[self.keys]=np.arange(self.n,dtype=np.int32)
        if len(np.unique(self.keys))!=self.n: raise ValueError('Tekrarlı evren')
        patterns=[np.zeros(len(self.q),np.int8)]
        for k in range(1,min(r,len(self.q))+1):
            for chosen in combinations(range(len(self.q)),k):
                for shifts in product(*(range(1,self.q[j]) for j in chosen)):
                    a=np.zeros(len(self.q),np.int8); a[list(chosen)]=shifts;patterns.append(a)
        patterns=np.array(patterns); self.delta=[]
        for j,q in enumerate(self.q):
            d=np.arange(q)[:,None];self.delta.append(((((d+patterns[:,j])%q)-d)*self.radix[j]).astype(np.int32))
        self.full=self.n==self.size
        self.block=max(1,min(256,262144//max(1,self.ball)))
    def neighbors(self, ids):
        ids=np.asarray(ids,dtype=np.int32).reshape(-1)
        keys=np.broadcast_to(self.keys[ids,None],(len(ids),self.ball)).copy()
        for j,d in enumerate(self.delta): keys+=d[self.digits[ids,j]]
        return self.lookup[keys]
    def initial(self, weights):
        if self.full and np.all(weights==weights[0]): return np.full(self.n,self.ball*weights[0],float),self.ball
        out=np.empty(self.n,float);degree=0
        extended=np.r_[weights,0.]
        for i in range(0,self.n,self.block):
            ids=np.arange(i,min(i+self.block,self.n)); nb=self.neighbors(ids)
            out[ids]=extended[nb].sum(axis=1);degree=max(degree,int((nb>=0).sum(axis=1).max()))
        return out,degree
    def update(self,gains, ids, weights):
        for i in range(0,len(ids),self.block):
            sub=ids[i:i+self.block]; nb=self.neighbors(sub); valid=nb>=0
            if np.all(weights[sub]==1): dec=np.bincount(nb[valid],minlength=self.n)
            else: dec=np.bincount(nb[valid],weights=np.broadcast_to(weights[sub,None],nb.shape)[valid],minlength=self.n)
            gains-=dec
    def prune(self, selected, weights, goal):
        counts=np.zeros(self.n,np.int32)
        for j in selected:
            nb=self.neighbors([j]).ravel(); nb=nb[nb>=0]; counts[nb]+=1
        covered=float(weights[counts>0].sum()); keep=[]
        if covered<goal-1e-10: return list(selected),covered
        for j in reversed(selected):
            nb=self.neighbors([j]).ravel(); nb=nb[nb>=0]; loss=float(weights[nb[counts[nb]==1]].sum())
            if covered-loss>=goal-1e-10: counts[nb]-=1; covered-=loss
            else: keep.append(int(j))
        return list(reversed(keep)),covered
    def two_to_one(self, selected, priority, rounds=3):
        from itertools import combinations
        sel=list(selected); swapped=0
        if len(sel)<2 or len(sel)>6000:return sel,swapped
        counts=np.zeros(self.n,np.int32); rank=np.empty(self.n,np.int32);rank[priority]=np.arange(self.n)
        for j in sel:
            nb=self.neighbors([j]).ravel();nb=nb[nb>=0];counts[nb]+=1
        if not np.all(counts>0):return sel,swapped
        for _ in range(rounds):
            lists=[]; burdens=[]
            for j in sel:
                nb=self.neighbors([j]).ravel();nb=nb[nb>=0];lists.append(nb);burdens.append(int((counts[nb]==1).sum()))
            choices=np.argsort(burdens)[:min(18,len(sel))];changed=False; used=set(sel)
            for i,j in combinations(choices,2):
                x,y=lists[i],lists[j]
                unique=np.r_[x[counts[x]==1],y[counts[y]==1]]
                shared=np.intersect1d(x[counts[x]==2],y[counts[y]==2],assume_unique=True)
                gap=np.r_[unique,shared]
                if not len(gap) or len(gap)>self.ball:continue
                opts=self.neighbors([gap[0]]).ravel();opts=opts[opts>=0]
                if not len(opts):continue
                for gen in gap[1:]:
                    opts=opts[(self.code[opts]!=self.code[gen]).sum(axis=1)<=self.r]
                    if not len(opts):break
                opts=[int(a) for a in opts if int(a) not in used]
                if opts:
                    k=min(opts,key=lambda a:rank[a]);counts[x]-=1;counts[y]-=1;nb=self.neighbors([k]).ravel();counts[nb[nb>=0]]+=1
                    if not np.all(counts>0):raise RuntimeError('Yerel örtü doğrulaması başarısız')
                    for idx in sorted((i,j),reverse=True):sel.pop(int(idx))
                    sel.append(k);swapped+=1;changed=True;break
            if not changed:break
        return sel,swapped
    def greedy(self, weights, initial, goal, cap, priority, min_fark, seed=None):
        gains=initial.copy(); eligible=np.ones(self.n,bool); uncovered=np.ones(self.n,bool); sel=[]; total=0.
        rank=np.empty(self.n,np.int32);rank[priority]=np.arange(self.n)
        def add(j):
            nonlocal total
            sel.append(int(j)); eligible[j]=False
            nb=self.neighbors([j]).ravel(); nb=nb[nb>=0]; ids=nb[uncovered[nb]]; uncovered[ids]=False
            total+=float(weights[ids].sum()); self.update(gains,ids,weights)
            if min_fark>1: eligible[:] &= (self.code!=self.code[j]).sum(axis=1)>=min_fark
        for j in ([] if seed is None else seed):
            if len(sel)>=cap or total>=goal-1e-10: break
            if eligible[j]:add(j)
        while len(sel)<cap and total<goal-1e-10:
            g=np.where(eligible,gains,-np.inf); best=float(g.max())
            if best<=1e-12:break
            ties=np.flatnonzero(g>=best-1e-11);j=int(ties[np.argmin(rank[ties])]);add(j)
        return sel,total


def _karma_koset_adayi(engine, limit, tries=400, seconds=12.):
    """Tam çarpım uzayında GF(2)/GF(3) doğrusal bölüm örtüsü."""
    import time
    from itertools import combinations, product
    if not engine.full or not 1<=engine.r<=3 or engine.n>60000:return None,0
    n=engine.n; qs=np.array(engine.q); b=np.flatnonzero(qs==2); t=np.flatnonzero(qs==3)
    rng=np.random.default_rng(143+engine.r); started=time.monotonic(); best=None; tried=0
    shapes=[]
    for i in range(len(b)+1):
        for j in range(len(t)+1):
            m=2**i*3**j; k=n//m
            if 12<=m<=2592 and k*math.ceil(m/min(m,engine.ball))<limit:shapes.append((i,j,m,k))
    shapes.sort(key=lambda x:(x[3]*math.ceil(x[2]/min(x[2],engine.ball)), -x[2]))
    if not shapes:return None,0
    def matrix(d,l,p):
        if d==0:return np.empty((l,0),np.int32)
        z=rng.integers(0,p,size=(l,d),dtype=np.int32);z[:d]=np.eye(d,dtype=np.int32)
        return z[rng.permutation(l)]
    for attempt in range(tries):
        if time.monotonic()-started>seconds:break
        i,j,m,k=shapes[attempt%len(shapes)]
        if k>=limit:continue
        q=np.array([2]*i+[3]*j,np.int32);rad=np.cumprod(np.r_[1,q[:-1]],dtype=np.int32)
        h=np.zeros((len(qs),len(q)),np.int32);h[b,:i]=matrix(i,len(b),2);h[t,i:]=matrix(j,len(t),3)
        pat=[np.zeros(len(q),np.int32)]
        for z in range(1,min(engine.r,len(qs))+1):
            for ix in combinations(range(len(qs)),z):
                for v in product(*(range(1,qs[a]) for a in ix)):
                    pat.append((np.array(v,dtype=np.int32)@h[list(ix)])%q)
        shifts=np.unique(np.asarray(pat)@rad);ball=len(shifts);tried+=1
        if k*math.ceil(m/ball)>=limit:continue
        digits=(np.arange(m,dtype=np.int32)[:,None]//rad)%q
        ids=np.arange(m,dtype=np.int32);adj=np.zeros((m,m),bool)
        for g in shifts:adj[ids,((digits+digits[g])%q)@rad]=True
        for rep in range(5):
            uncovered=np.ones(m,bool);gains=np.full(m,ball,np.int32);sel=[]
            for step in range((limit-1)//k):
                if not uncovered.any():break
                mx=gains.max();ties=np.flatnonzero(gains==mx)
                if mx<=0:break
                a=0 if step==0 else int(rng.choice(ties));sel.append(a)
                new=adj[a]&uncovered;uncovered[new]=False
                gains-=adj[:,new].sum(axis=1,dtype=np.int32)
            if uncovered.any():continue
            counts=adj[sel].sum(axis=0,dtype=np.int32);keep=[]
            for a in reversed(sel):
                if np.all(counts[adj[a]]>1):counts[adj[a]]-=1
                else:keep.append(a)
            if len(keep)*k>=limit:continue
            syn=((engine.digits@h)%q)@rad;trial=np.flatnonzero(np.isin(syn,keep)).tolist()
            if len(trial)!=len(keep)*k:continue
            best=trial;limit=len(best)
    return best,tried


def _genis_komsuluk_adayi(engine, selected, priority, rounds=120, seconds=5.):
    """Sınırlı destroy/repair LNS; sadece daha küçük doğrulanabilir örtü döner."""
    import time
    if not engine.full or len(selected)<3 or len(selected)>1200 or engine.n>60000:return list(selected),0
    rng=np.random.default_rng(145+engine.r);started=time.monotonic();n=engine.n
    rank=np.empty(n,np.int32);rank[priority]=np.arange(n)
    cache={}
    def nb(j):
        j=int(j)
        if j not in cache:
            a=engine.neighbors([j]).ravel();cache[j]=a[a>=0]
        return cache[j]
    def counts_for(sel):
        c=np.zeros(n,np.int16)
        for j in sel:c[nb(j)]+=1
        return c
    best=list(selected);cur=list(selected);accepted=0
    for step in range(rounds):
        if time.monotonic()-started>=seconds:break
        if step%20==0:cur=list(best)
        c=counts_for(cur);burden=np.array([(c[nb(j)]==1).sum() for j in cur]);order=np.argsort(burden)
        drop=min(len(cur)-1,int(rng.integers(2, min(9,len(cur))+1)))
        pool=order[:min(len(cur),max(drop,drop*5))] if step%3 else np.arange(len(cur))
        ix=set(rng.choice(pool,size=drop,replace=False).tolist());trial=[j for i,j in enumerate(cur) if i not in ix]
        for i in ix:c[nb(cur[i])]-=1
        used=set(trial);cap=len(best) if step%4 else len(best)-1
        while len(trial)<cap:
            gap=np.flatnonzero(c==0)
            if not len(gap):break
            gain=np.zeros(n,np.int32)
            for i in range(0,len(gap),engine.block):
                near=engine.neighbors(gap[i:i+engine.block]);gain+=np.bincount(near[near>=0],minlength=n).astype(np.int32)
            if used:gain[list(used)]=0
            mx=int(gain.max())
            if mx<=0:break
            choices=np.flatnonzero(gain>=mx)
            j=int(rng.choice(choices)) if step%2 else int(choices[np.argmin(rank[choices])]);trial.append(j);used.add(j);c[nb(j)]+=1
        if not np.all(c>0):continue
        # Prune redundant centers.
        for j in list(reversed(trial)):
            a=nb(j)
            if np.all(c[a]>1):c[a]-=1;trial.remove(j)
        if len(trial)<len(best):best=list(trial);accepted+=1
        if len(trial)<=len(best):cur=list(trial)
        if len(cache)*engine.ball>4_000_000:cache.clear()
    return best,accepted


def gelismis_garanti_ve_budama_uygula(kolonlar,puanlar,kompozit_skor,hedef,
    max_k=None,akilli_merkez=True,min_fark=1,hedef_kapsama=100.0,
    tam_evren_kolonlar=None,tam_evren_puanlar=None,tam_evren_kompozit=None,
    sablon=None,ortogonal_aktif=True,veriler=None,baslangic=None,arama_derinligi="Dengeli"):
    a=np.asarray(tam_evren_kolonlar if tam_evren_kolonlar is not None else kolonlar).reshape(-1,15)
    p=np.asarray(tam_evren_puanlar if tam_evren_kolonlar is not None else puanlar)
    s=np.asarray(tam_evren_kompozit if tam_evren_kolonlar is not None else kompozit_skor)
    n=len(a);r=15-int(hedef);target=float(hedef_kapsama)/100;cap=n if max_k is None else min(n,max(0,int(max_k)))
    if not 0<=r<=3 or not 0<target<=1:raise ValueError('Geçersiz hedef')
    def fallback():
        out=_eski_kapsama_motoru(a,p,s,hedef,max_k,akilli_merkez,min_fark,hedef_kapsama,sablon=sablon,ortogonal_aktif=ortogonal_aktif,veriler=veriler)
        gelismis_garanti_ve_budama_uygula.meta=dict(_eski_kapsama_motoru.meta)
        return out
    if n<=900 or r==0 or not cap: return fallback()
    code=_kodla(a)
    try: engine=_OrtukKomsuluk143(code,r)
    except (OverflowError,MemoryError): return fallback()
    w=_kutle(a,veriler) if veriler is not None else np.ones(n);w=w/w.sum()
    weights=np.ones(n) if target==1 else w; goal=float(n) if target==1 else target
    initial,degree=engine.initial(weights);alt=math.ceil(n/degree) if target==1 else None
    order=np.argsort(-s,kind='stable');rng=np.random.default_rng(142)
    seed=None
    if baslangic is not None and len(baslangic):
        lookup={tuple(c):j for j,c in enumerate(a)};seed=[lookup[tuple(c)] for c in baslangic if tuple(c) in lookup]
    best=None;best_value=-1.;attempts=0;budanan=0
    candidates=[(order,None)]
    if seed and len(seed)<min(cap, max(100, 8*math.ceil(n/degree))): candidates.append((order,seed))
    if akilli_merkez and n<=60000 and n*engine.ball<=65_000_000: candidates.append((rng.permutation(n),None))
    for priority,start in candidates:
        if best is not None and alt==len(best) and best_value>=goal-1e-10:break
        trial,total=engine.greedy(weights,initial,goal,cap,priority,min_fark,start);attempts+=1
        before=len(trial)
        if akilli_merkez:trial,total=engine.prune(trial,weights,goal)
        if best is None or (total>=goal-1e-10 and best_value<goal-1e-10) or (total>=goal-1e-10 and best_value>=goal-1e-10 and len(trial)<len(best)) or (best_value<goal-1e-10 and total>best_value+1e-10):
            best=trial;best_value=total;budanan=before-len(trial)
    swaps=0
    if akilli_merkez and min_fark==1 and target==1 and best_value>=goal-1e-10 and n<=60000:
        best,swaps=engine.two_to_one(best,order)
    karma_deneme=lns_kazanc=0
    karma_kolon=None
    yontem='Örtük Hamming + marjinal kazanç + çoklu başlangıç / budama / 2→1'
    # Üst sınırı yalnız geçerli ve daha kısa örtüyle güncelle. Tam evrende GF(2)/GF(3).
    if akilli_merkez and ortogonal_aktif and target==1 and min_fark==1 and engine.full and best_value>=goal-1e-10 and len(best)>alt and n<=60000:
        derin=arama_derinligi=='Derin'
        tries=(800 if derin else 400) if r==3 else (160 if derin else 60)
        seconds=(22. if derin else 12.) if r==3 else (8. if derin else 3.)
        try:
            trial,karma_deneme=_karma_koset_adayi(engine,max(alt+1,len(best)-1),tries=tries,seconds=seconds)
            if trial is not None and len(trial)<len(best) and len(trial)<=cap and np.all(_en_yakin_isabet(a[trial],a)>=hedef):
                best=trial;karma_kolon=len(best);yontem+=' + GF(2)/GF(3) karma koset'
            trial,lns_kazanc=_genis_komsuluk_adayi(engine,best,order,rounds=400 if derin else 120,seconds=12. if derin else 5.)
            if len(trial)<len(best) and len(trial)<=cap and np.all(_en_yakin_isabet(a[trial],a)>=hedef):
                best=trial;yontem+=' + geniş komşuluk araması'
            else:lns_kazanc=0
        except (MemoryError,OverflowError):
            yontem+=' (kaynak sınırı; son geçerli çözüm korundu)'
    out=a[best];hits=_en_yakin_isabet(out,a);mask=hits>=hedef
    adet=float(mask.mean()*100);mass=float(w[mask].sum()*100);ok=bool(mask.all()) if target==1 else mass>=hedef_kapsama-1e-8
    meta=dict(durum='HEDEF DOĞRULANDI' if ok else 'HEDEF SAĞLANAMADI',alt_sinir=alt,optimal=bool(ok and target==1 and len(best)==alt),kapsama_adet=adet,kapsama_kutle=mass,hedef_tam=ok,yontem=yontem,sinir_evrende=n,bütçe_limiti=max_k,deneme=attempts,kure_boyutu=engine.ball,karma_deneme=karma_deneme,karma_kolon=karma_kolon,lns_iyilesme=lns_kazanc,arama_profili=arama_derinligi)
    gelismis_garanti_ve_budama_uygula.meta=meta
    return out,p[best],adet if target==1 else mass,budanan,swaps

def monte_carlo_simule_et(kuponlar,veriler,sablon):
    if not len(kuponlar): return dict(sablon_14_arti=0.,sablon_15=0.,genel_12_arti=0.,ikramiye_endeksi=0.,sablon_kutlesi=0.)
    rng=np.random.default_rng(42); n=4000; labels=np.array(['1','X','2']); geral=[]; cond=[]; mass=1.
    for v,s in zip(veriler,sablon):
        p=np.array([v[k] for k in labels],float); p/=p.sum(); q=np.where(np.isin(labels,s),p,0); mass*=q.sum(); q/=q.sum()
        geral.append(rng.choice(labels,n,p=p)); cond.append(rng.choice(labels,n,p=q))
    both=np.vstack([np.array(geral).T,np.array(cond).T]); h=_en_yakin_isabet(kuponlar,both); g,c=h[:n],h[n:]
    return dict(sablon_15=float(100*np.mean(c==15)),sablon_14_arti=float(100*np.mean(c>=14)),genel_12_arti=float(100*np.mean(g>=12)),ikramiye_endeksi=0.,sablon_kutlesi=float(100*mass))


def tarayici_isaretleme_kodu(kolonlar, maclar, paket_imza):
    """Kullanıcı tetiklemeli, yalnız tanınan seçim kutuları. Ödeme/submit yok."""
    rows=np.asarray(kolonlar)
    if not 1<=len(rows)<=4 or len(maclar)!=15:raise ValueError('1–4 kolon ve 15 maç gerekli')
    _kodla(rows)
    pairs=[]
    for name in maclar:
        parts=re.split(r'\s+[-–—]\s+',str(name),maxsplit=1)
        if len(parts)!=2 or not all(x.strip() for x in parts):raise ValueError('Maç adı ev - deplasman biçiminde olmalı')
        pairs.append(parts)
    payload=json.dumps({'pairs':pairs,'cols':rows.tolist(),'id':paket_imza},ensure_ascii=True)
    template=r'''(()=>{
const P=__PAYLOAD__;
if(location.protocol!=="https:" || !(["iddaa.com","www.iddaa.com"].includes(location.hostname)) || !location.pathname.startsWith("/spor-toto")){alert("Yalnızca iddaa.com Spor Toto sayfasında çalışır.");return;}
const id="st142-preview";
if(document.getElementById(id)){alert("Asistan zaten açık.");return;}
const normalize=s=>String(s).toLocaleLowerCase("tr-TR").normalize("NFKD").replace(/[\u0300-\u036f]/g,"").replace(/ı/g,"i").replace(/[^a-z0-9]+/g," ").trim();
const visible=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!=="hidden"&&s.display!=="none";};
const selector='input[type="checkbox"],[role="checkbox"][aria-checked="true"],[role="checkbox"][aria-checked="false"]';
const valid=e=>visible(e)&&!e.disabled&&e.getAttribute("aria-disabled")!=="true"&&!e.closest("a")&&(e.tagName!=="BUTTON"||e.getAttribute("type")==="button")&&(e.tagName==="INPUT"?e.type==="checkbox":["DIV","SPAN","BUTTON","LABEL"].includes(e.tagName));
const all=(root)=>Array.from(root.querySelectorAll(selector)).filter(valid).filter(e=>!e.querySelector(selector));
const state=e=>e.tagName==="INPUT"?e.checked:e.getAttribute("aria-checked")==="true";
const storage="st142-prepared-"+P.id;
const words=(hay,needle)=>(' '+hay+' ').includes(' '+needle+' ');
function locate(){
 const controls=all(document),used=new Set(),result=[];
 for(const pair of P.pairs){
  const [a,b]=pair.map(normalize);if(!a||!b||a===b)throw Error("Takım adları belirsiz");
  const candidates=new Set();
  for(const c of controls){let node=c.parentElement;for(let j=0;node&&j<9;j++,node=node.parentElement){
   const list=all(node);if(list.length>12) break;
   if(list.length!==12)continue;
   const t=normalize(node.innerText||node.textContent||"");if(words(t,a)&&words(t,b)){candidates.add(node);break;}
  }}
  const nodes=[...candidates].filter(n=>![...candidates].some(m=>m!==n&&n.contains(m)));
  if(nodes.length!==1)throw Error(pair.join(" - ")+": tekil 12 kutulu satır doğrulanamadı. Manuel aktarım kullanın.");
  const row=nodes[0];const list=all(row).sort((a,b)=>a.getBoundingClientRect().left-b.getBoundingClientRect().left);
  const rect=list.map(e=>e.getBoundingClientRect());
  if(rect.some((r,i)=>i>0&&r.left-rect[i-1].left<5)||Math.max(...rect.map(r=>r.top))-Math.min(...rect.map(r=>r.top))>15||list.some(e=>used.has(e)))throw Error("Kutular yatay olarak tekil değil");
  list.forEach(e=>used.add(e));result.push({row,list,pair});
 }
 if(result.length!==15||result.some((x,i)=>i>0&&x.row.getBoundingClientRect().top<=result[i-1].row.getBoundingClientRect().top))throw Error("Maç sırası uyuşmuyor");
 return result;
}
const panel=document.createElement("div");panel.id=id;panel.style.cssText="position:fixed;right:16px;top:16px;z-index:2147483647;background:#fff;color:#17212b;border:2px solid #315b8a;border-radius:10px;padding:16px;width:360px;max-height:85vh;overflow:auto;font:14px Arial;box-shadow:0 5px 20px #0005";
const title=document.createElement("strong");title.textContent="v15.1 – seçim önizleme / "+P.id;panel.append(title);
const msg=document.createElement("p");msg.textContent="Sadece seçim kutularını işaretler. Ödeme veya kupon onayı yapmaz.";panel.append(msg);
const preview=document.createElement("pre");preview.style.cssText="white-space:pre-wrap;font:12px monospace";preview.textContent=P.pairs.map((p,i)=>(i+1)+'. '+p.join(' - ')+' | '+P.cols.map(col=>col[i]).join(' ')).join('\n');panel.append(preview);
const check=document.createElement("input");check.type="checkbox";const label=document.createElement("label");label.append(check,document.createTextNode(" Maç sırasını ve soldan sağa A/B/C/D, her grupta 1/X/2 sırasını doğruladım."));panel.append(label);
const run=document.createElement("button");run.type="button";run.textContent="Bu grubu işaretle";run.style.cssText="display:block;margin:10px 0;padding:8px";panel.append(run);
const close=document.createElement("button");close.type="button";close.textContent="Kapat";close.onclick=()=>panel.remove();panel.append(close);document.body.append(panel);
run.onclick=async()=>{
 if(!check.checked){msg.textContent="Önce sıra doğrulamasını işaretleyin.";return;}
 run.disabled=true;close.disabled=true;
 try{
  if(localStorage.getItem(storage)){throw Error("Bu paket tarayıcıda daha önce hazırlanmış olarak kayıtlı. Siteyi ve manuel kayıtları kontrol edin.");}
  const rows=locate();const desired=rows.map((r,i)=>Array.from({length:12},(_,j)=>{const k=Math.floor(j/3),v=P.cols[k]?.[i];return v!==undefined&&["1","X","2"][j%3]===v;}));
  if(rows.some(r=>r.list.some(state)))throw Error("Sayfada önceden işaretli kutular var; manuel kontrol edin. Asistan bunları silmez.");
  if(!confirm("15 maç ve "+P.cols.length+" kolon için yalnızca seçim kutuları işaretlensin mi? Ödeme yapılmayacaktır.")){run.disabled=false;close.disabled=false;return;}
  localStorage.setItem(storage,"started");
  for(let i=0;i<15;i++)for(let j=0;j<12;j++)if(desired[i][j]){
   const el=rows[i].list[j];if(!el.isConnected||!valid(el)||state(el))throw Error("Sayfa değişti; elle kontrol gerekli");
   el.click();await new Promise(resolve=>setTimeout(resolve,120));
   if(!el.isConnected||!state(el))throw Error("İşaretleme doğrulanamadı; devam edilmedi");
  }
  const finalRows=locate();if(finalRows.some((r,i)=>r.list.some((e,j)=>state(e)!==desired[i][j])))throw Error("Son kontrol başarısız; elle kontrol edin");
  localStorage.setItem(storage,"prepared");msg.textContent="İşaretler doğrulandı. Ödeme/kupon onayı manuel; kayıt ödeme kanıtı değildir.";
 }catch(e){msg.textContent="DURDU: "+e.message+". Otomatik tekrar yok; elle kontrol edin.";}
 finally{close.disabled=false;}
};
})();'''
    return template.replace('__PAYLOAD__',payload)


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
                if len(parcalar) == 15:
                    k.append(parcalar)
        return np.array(k) if k else None
    except Exception:
        return None



# ==============================================================================
# v15.1 — SMART COUPON TRANSFER CENTER: çevrimdışı paket ve denetim
# ==============================================================================
AKTARIM_PLATFORMLARI = ("İddaa.com", "Nesine", "Bilyoner", "Misli", "Birebin", "Oley", "Diğer / manuel")

def aktarim_plan15(kolonlar, ozet, guncel_imza, uretim_modu, fiyat, butce):
    """Yalnız güncel, geçerli, bütçe kontrollü ve benzersiz kolonları kabul eder."""
    if not isinstance(ozet, dict) or not guncel_imza or ozet.get('imza') != guncel_imza:
        raise ValueError('Güncel üretim bulunamadı; önce kapsama hesaplayın.')
    if uretim_modu != 'Bütçe kontrollü' or ozet.get('uretim_modu') != uretim_modu:
        raise ValueError('Analiz modu yalnızca inceleme içindir. Aktarım merkezi bütçe kontrollü üretimi kabul eder.')
    a = np.asarray(kolonlar)
    if a.ndim != 2 or a.shape[1] != 15 or not len(a) or not np.isin(a,['1','X','2']).all():
        raise ValueError('Geçerli 15 maçlık kolon bulunamadı.')
    rows = [''.join(row) for row in a.tolist()]
    if len(set(rows)) != len(rows): raise ValueError('Mükerrer kolon bulundu; yeniden hesaplayın.')
    matches = ozet.get('s_veriler') or []
    ids = [str(m.get('id','')) for m in matches]
    names = [str(m.get('mac','')).strip() for m in matches]
    if len(ids)!=15 or len(set(ids))!=15 or not all(ids) or not all(names):
        raise ValueError('Bültenin 15 benzersiz maç kimliği doğrulanamadı.')
    if ids != [str(x) for x in ozet.get('mac_ids',[])]: raise ValueError('Bülten sırası değişmiş.')
    try:
        price=Decimal(str(fiyat)); cap=Decimal(str(butce)); oldprice=Decimal(str(ozet.get('kolon_fiyati')))
        if not price.is_finite() or not cap.is_finite() or price<=0 or cap<=0 or oldprice!=price or price*len(rows)>cap:
            raise ValueError('Fiyat veya bütçe sınırı geçersiz; tekrar hesaplayın.')
    except InvalidOperation as exc: raise ValueError('Fiyat veya bütçe okunamadı.') from exc
    content=json.dumps({'ids':ids,'names':names,'rows':rows},ensure_ascii=False,separators=(',',':'))
    fingerprint=hashlib.sha256(content.encode('utf-8')).hexdigest()
    packets=(len(rows)+3)//4
    return {'id':fingerprint,'rows':rows,'ids':ids,'names':names,'packets':packets,
            'price':str(price),'cost':str(price*len(rows)),'budget':str(cap)}

def aktarim_kayit15(plan, platform, values):
    if platform not in AKTARIM_PLATFORMLARI: raise ValueError('Bilinmeyen platform etiketi.')
    if not isinstance(values,list) or any(type(x) is not int or x<1 or x>plan['packets'] for x in values):
        raise ValueError('Paket kontrol kaydı geçersiz.')
    return {'schema':'15.0-manual-review','plan_id':plan['id'],'platform':platform,'checked':sorted(set(values))}

def aktarim_ilerleme15(plan, checked):
    ids=set(checked)
    done=sum(min(4,len(plan['rows'])-4*(i-1)) for i in ids)
    return done,len(plan['rows'])-done

def aktarim_arsiv15(plan, platform):
    """Genel amaçlı çevrimdışı arşiv; platform import protokolü değildir."""
    if platform not in AKTARIM_PLATFORMLARI: raise ValueError('Bilinmeyen platform.')
    out=io.StringIO(newline=''); w=csv.writer(out)
    w.writerow(['Paket','Kolon']+[str(i) for i in range(1,16)])
    for i,row in enumerate(plan['rows']): w.writerow([i//4+1,i+1,*row])
    manifest={k:plan[k] for k in ('id','ids','names','packets','price','cost','budget')}
    manifest.update(platform=platform,columns=len(plan['rows']),format='generic-offline-v15',status='not-submitted')
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('kolonlar.csv',out.getvalue().encode('utf-8-sig'))
        z.writestr('kolonlar.txt','\n'.join(plan['rows'])+'\n')
        z.writestr('bulten_ve_maliyet.json',json.dumps(manifest,ensure_ascii=False,indent=2))
        z.writestr('OKU.txt','Çevrimdışı kontrol arşivi. Resmî site aktarım formatı değildir. İşlem yapılmadı. Maç sırası, fiyat ve seçimleri kendiniz kontrol edin.')
    return stream.getvalue()

# v15.1 — bağımsız toplu ön kontrol; sağlayıcıya bağlanmaz.
def toplu_denetim151(plan, ozet):
    """Yerel veriyi denetler. Hiçbir hesap, bakiye, bilet veya gönderim doğrulamaz."""
    ids, names, rows = plan['ids'], plan['names'], plan['rows']
    if len(ids) != 15 or len(set(ids)) != 15 or len(names) != 15 or not all(names):
        raise ValueError('15 maç kimliği veya sırası geçersiz.')
    if not rows or len(set(rows)) != len(rows) or any(len(r)!=15 or set(r)-set('1X2') for r in rows):
        raise ValueError('Geçersiz veya mükerrer kolon.')
    raw=json.dumps({'ids':ids,'names':names,'rows':rows},ensure_ascii=False,separators=(',',':'))
    if hashlib.sha256(raw.encode('utf-8')).hexdigest()!=plan['id']:
        raise ValueError('Kolon içeriği imzası uyuşmuyor.')
    try:
        price, cost, budget = (Decimal(plan[k]) for k in ('price','cost','budget'))
        if not all(x.is_finite() and x>0 for x in (price,cost,budget)) or price*len(rows)!=cost or cost>budget:
            raise ValueError('Bütçe veya tutar uyuşmazlığı.')
    except InvalidOperation as exc:
        raise ValueError('Geçersiz tutar.') from exc
    sablon=ozet.get('g_sablon')
    if not isinstance(sablon,(list,tuple)) or len(sablon)!=15 or any(not x or len(x)!=len(set(x)) or set(x)-set('1X2') for x in sablon):
        raise ValueError('Şablon geçersiz.')
    if any(any(c not in sablon[i] for i,c in enumerate(r)) for r in rows):
        raise ValueError('Şablon dışı kolon bulundu.')
    size=math.prod(map(len,sablon))
    if size>300_000 or size!=ozet.get('ham_adet'):
        raise ValueError('Şablon büyüklüğü kayıtla uyuşmuyor veya kaynak sınırını aşıyor.')
    a=np.asarray([list(r) for r in rows],dtype='<U1')
    # Kartesyen evreni bağımsız olarak yeniden oluştur.
    b=np.asarray(list(itertools.product(*sablon)),dtype='<U1')
    audit=deterministik_garanti_denetle(a,b)
    old=ozet.get('denetim_ham',{})
    if any(not isinstance(old.get(k),(int,float,np.integer,np.floating)) or not math.isfinite(float(old[k])) or abs(float(old[k])-v)>1e-7 for k,v in audit.items()):
        raise ValueError('Yeniden hesaplanan ham kapsama ile önceki rapor uyuşmuyor.')
    target=ozet.get('garanti_derecesi')
    if target not in (12,13,14,15): raise ValueError('Hedef isabet derecesi geçersiz.')
    target_key={12:'en_az_12',13:'en_az_13',14:'en_az_14',15:'tam_15'}[target]
    packets=[{'paket':i//4+1,'kolon_sayisi':len(rows[i:i+4]),'sha256':hashlib.sha256(('\n'.join(rows[i:i+4])).encode()).hexdigest()} for i in range(0,len(rows),4)]
    return {'schema':'15.1-local-preflight','plan_id':plan['id'],'kolon_sayisi':len(rows),'paket_sayisi':len(packets),'maliyet_tl':str(cost),'butce_tl':str(budget),'ham_evren':size,'hedef':target,'ham_kapsama':audit,'ham_tam_kapsama':audit[target_key]==100.0,'paketler':packets,'durum':'LOCAL_VALIDATED','saglayici_durumu':'NOT_CONNECTED','gonderilen_kolon':0,'odeme_yapildi':False,'uyari':'Yerel denetim tamamlandı. Bilet, bakiye, hesap veya gerçek bahis işlemi doğrulanmadı.'}


def denetim_imza151(plan, ozet):
    payload={'id':plan['id'],'price':plan['price'],'budget':plan['budget'],'imza':ozet.get('imza'),'sablon':ozet.get('g_sablon'),'ham':ozet.get('denetim_ham'),'target':ozet.get('garanti_derecesi')}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()

# ANA SEKMELER
# ==============================================================================
tab_uretim, tab_takip, tab_otomasyon = st.tabs([
    "🎛️ 1. Bülten ve Senaryo Analizi",
    "📡 2. Canlı Sonuç ve Kapsama Takibi",
    "📋 3. Akıllı Aktarım ve Rapor Merkezi"
])

# ------------------------------------------------------------------------------
# SEKME 1: PROFESYONEL MAÇ KONTROL PANELİ VE SENDİKA MOTORU
# ------------------------------------------------------------------------------
guncel_uretim_imzasi = None
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
                    st.session_state.canli_sonuclar=["⏳ Bekliyor"]*15
                    st.session_state.canli_skor_metni=["-"]*15
                    st.session_state.secilen_mac_idleri=[]
                    st.session_state.mac_listesi = []
                    st.session_state.secilen_15_mac = []
                    st.session_state.eslesmeyen_satirlar = []
                    st.session_state.analiz_verisi = None
                    st.session_state.tablo_baz_df = None
                    st.session_state.tablo_df = None
                    st.session_state.uretilen_kuponlar = None
                    st.session_state.son_uretim_ozeti = None
                    st.session_state.son_param_imzasi = None
                    st.session_state.son_sol_menu_imzasi = None
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
                    sira_onayi=st.checkbox("15 maçın resmî bülten sırasını kontrol ettim",key="bulten_onay14")
                    b_col1, b_col2 = st.columns([2, 1.2])
                    with b_col1:
                        if s_sayi == 15:
                            st.success("✅ **15 / 15 Maç Hazır!** Analizi başlatabilirsiniz.")
                        else:
                            st.info(f"📌 Şu an **{s_sayi} / 15** maç seçili.")
                    with b_col2:
                        if st.button("🚀 Analizi Başlat", type="primary", disabled=(s_sayi != 15 or not sira_onayi or not api_key), use_container_width=True):
                            st.session_state.canli_sonuclar = ["⏳ Bekliyor"]*15
                            st.session_state.canli_skor_metni = ["-"]*15
                            st.session_state.secilen_mac_idleri = [m["id"] for m in st.session_state.secilen_15_mac]
                            st.session_state.analiz_verisi = hibrit_tahminleri_al(st.session_state.secilen_15_mac, api_key)
                            st.session_state.tablo_baz_df = None
                            st.session_state.tablo_df = None
                            st.session_state.tablo_versiyon += 1
                            st.session_state.uretilen_kuponlar = None
                            st.session_state.son_uretim_ozeti = None
                            st.session_state.son_param_imzasi = None
                            st.session_state.son_sol_menu_imzasi = None
                            st.session_state.yatirilan_paketler = []
                            st.rerun()

        # ======================================================================
        # ADIM 2: PROFESYONEL SENDİKA KONTROL PANELİ (v15.1 ULTRA HIZLI MOTOR)
        # ======================================================================
        if st.session_state.analiz_verisi:
            veriler = st.session_state.analiz_verisi
            with st.expander("Kaynak kalitesi ve veri uyarıları",expanded=False):
                st.dataframe(pd.DataFrame([{k:v.get(k) for k in ('mac','kaynak','buro_sayisi','snapshot_utc','veri_uyarilari')} for v in veriler]))
            if any(v.get('kaynak','').startswith('VERİ YOK') for v in veriler): st.warning('Bazı maçlarda veri yok; varsayımsal olasılıklar kullanılıyor. İsabet iddiası yapılamaz.')
            on_limitler = tam_otonom_analiz(veriler, strateji_modu)

            if st.session_state.tablo_baz_df is None:
                oto_durum = butceye_gore_sablon_optimize_et(
                    veriler, hedef_kolon_sayisi, garanti_derecesi,
                    mutlak_mod=mutlak_sablon_garantisi, hibrit_mod=hibrit_ekonomi_modu, tuzak_aktif=tuzak_koruma
                )
                ilk_df = tablo_verisi_olustur(
                    veriler, on_limitler, tuzak_koruma, mod="butce_oto", ozel_durumlar=oto_durum
                )
                st.session_state.tablo_baz_df = ilk_df.copy()
                st.session_state.tablo_df = ilk_df.copy()

            st.markdown("#### 🎛️ Profesyonel Şablon & Akıllı Bütçe Optimizasyon Masası")
            tb0, tb1, tb2, tb3, tb4 = st.columns([1.6, 1.15, 1.15, 1.15, 0.85])
            with tb0:
                if st.button(f"🎯 Bütçeme Göre Otomatik Kur ({hedef_butce_tl:,.0f} TL)", type="primary", use_container_width=True):
                    oto_durum = butceye_gore_sablon_optimize_et(
                        veriler, hedef_kolon_sayisi, garanti_derecesi,
                        mutlak_mod=mutlak_sablon_garantisi, hibrit_mod=hibrit_ekonomi_modu, tuzak_aktif=tuzak_koruma
                    )
                    yeni_df = tablo_verisi_olustur(
                        veriler, on_limitler, tuzak_koruma, mod="butce_oto", ozel_durumlar=oto_durum
                    )
                    st.session_state.tablo_baz_df = yeni_df.copy()
                    st.session_state.tablo_df = yeni_df.copy()
                    st.session_state.tablo_versiyon += 1
                    st.session_state.son_param_imzasi = None
                    st.rerun()
            with tb1:
                if st.button("🌱 Ekonomik (5B-6Ç-4K)", use_container_width=True):
                    yeni_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="super_eko_5b_6c_4k")
                    st.session_state.tablo_baz_df = yeni_df.copy()
                    st.session_state.tablo_df = yeni_df.copy()
                    st.session_state.tablo_versiyon += 1
                    st.session_state.son_param_imzasi = None
                    st.rerun()
            with tb2:
                if st.button("🤖 AI Dengeli (4B-7Ç-4K)", use_container_width=True):
                    yeni_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="ai")
                    st.session_state.tablo_baz_df = yeni_df.copy()
                    st.session_state.tablo_df = yeni_df.copy()
                    st.session_state.tablo_versiyon += 1
                    st.session_state.son_param_imzasi = None
                    st.rerun()
            with tb3:
                if st.button("💎 Sendika (3B-6Ç-6K)", use_container_width=True):
                    yeni_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="sendika_3b_6c_6k")
                    st.session_state.tablo_baz_df = yeni_df.copy()
                    st.session_state.tablo_df = yeni_df.copy()
                    st.session_state.tablo_versiyon += 1
                    st.session_state.son_param_imzasi = None
                    st.rerun()
            with tb4:
                if st.button("🔒 15 Banko", use_container_width=True):
                    yeni_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="15_banko")
                    st.session_state.tablo_baz_df = yeni_df.copy()
                    st.session_state.tablo_df = yeni_df.copy()
                    st.session_state.tablo_versiyon += 1
                    st.session_state.son_param_imzasi = None
                    st.rerun()

            df_edit = st.data_editor(
                st.session_state.tablo_baz_df,
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
            yeni_ids = [int(x) for x in sirali["ID"].tolist()]
            if yeni_ids != st.session_state.secilen_mac_idleri:
                st.session_state.canli_sonuclar=["⏳ Bekliyor"]*15
                st.session_state.canli_skor_metni=["-"]*15
            st.session_state.secilen_mac_idleri = yeni_ids
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

                kaynak_m = id_analiz_haritasi.get(int(r["ID"]), {})
                orijinal_halk_fav = kaynak_m.get("halk_favori", max(h1, hx, h2))
                kullanici_halk_fav = int(r["Halk (%)"])

                if abs(kullanici_halk_fav - orijinal_halk_fav) >= 2:
                    if y1 >= yx and y1 >= y2:
                        h1, hx, h2 = olasilik_yumusat(kullanici_halk_fav, (100 - kullanici_halk_fav) * (hx / max(1, hx + h2)), (100 - kullanici_halk_fav) * (h2 / max(1, hx + h2)))
                    elif y2 >= y1 and y2 >= yx:
                        h1, hx, h2 = olasilik_yumusat((100 - kullanici_halk_fav) * (h1 / max(1, h1 + hx)), (100 - kullanici_halk_fav) * (hx / max(1, h1 + hx)), kullanici_halk_fav)
                    else:
                        h1, hx, h2 = olasilik_yumusat((100 - kullanici_halk_fav) * (h1 / max(1, h1 + h2)), kullanici_halk_fav, (100 - kullanici_halk_fav) * (h2 / max(1, h1 + h2)))

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
                    g1_aralik = (0, max(1, int(math.ceil(g1_say * 0.65)))) if g1_say > 0 else (0, 15)
                    g2_aralik = (0, max(2, int(math.ceil(g2_say * 0.80)))) if g2_say > 0 else (0, 15)
                else:
                    g1_aralik, g2_aralik = g1_manuel, g2_manuel
            else:
                g1_aralik, g2_aralik = (0, 15), (0, 15)

            ham_kolon_sayisi = math.prod(len(s) for s in g_sablon)

            tahmini_net_kolon = ham_kolon_sayisi

            sol_menu_imza_ham = json.dumps({
                "garanti": garanti_derecesi,
                "mutlak_sablon": mutlak_sablon_garantisi,
                "hibrit_mod": hibrit_ekonomi_modu,
                "ortogonal": ortogonal_anahtar_aktif,
                "kati_filtre": kati_filtre_kilidi,
                "kapsama": hedef_kapsama_orani,
                "max_k": max_kolon_limiti,
                "uretim_modu": uretim_modu, "kolon_fiyati": kolon_fiyati,
                "ev": ev_katsayisi,
                "strateji": strateji_modu,
                "hamming": benzerlik_elemesi,
                "akilli_merkez": akilli_merkez, "arama_derinligi": arama_derinligi,
                "log_zarf": log_zarf_aktif,
                "kademe": kademe_filtre_aktif,
                "homojen": homojen_bulten,
                "entropi": entropi_filtresi,
                "ai_filtre": ai_filtre_modu,
                "manuel_filtreler": None if ai_filtre_modu else {
                    "r1": range_1, "rx": range_x, "r2": range_2,
                    "rf": range_fav, "rp": range_plase, "rs": range_surpriz,
                    "a1": max_ardisik_1, "ax": max_ardisik_x, "a2": max_ardisik_2,
                    "bs": banko_siniri, "cs": cifte_sans_siniri
                },
                "grup_guvence": grup_guvence_aktif,
                "g1_aralik": g1_aralik,
                "g2_aralik": g2_aralik
            }, sort_keys=True)
            sol_menu_imzasi = hashlib.md5(sol_menu_imza_ham.encode("utf-8")).hexdigest()
            sol_menu_degisti = (st.session_state.get("son_sol_menu_imzasi") != sol_menu_imzasi)

            imza_ham = json.dumps({
                "sablon": g_sablon,
                "mac_ids":[v["id"] for v in s_veriler],
                "oranlar": [(v["1"], v["X"], v["2"], v["h1"], v["hX"], v["h2"]) for v in s_veriler],
                "g1_idx": g1_indeksleri,
                "g2_idx": g2_indeksleri,
                "sol_menu_imzasi": sol_menu_imzasi
            }, sort_keys=True)
            param_imzasi = hashlib.md5(imza_ham.encode("utf-8")).hexdigest()
            degisiklik_bekliyor = (st.session_state.get("son_param_imzasi") != param_imzasi)
            if not bos_mac_var and not sira_hatasi_var and ham_kolon_sayisi <= 300_000:
                guncel_uretim_imzasi = param_imzasi

            col_ozet, col_buton = st.columns([2.2, 1.2])
            with col_ozet:
                durum_etiketi = (
                    "🟠 **Şablon/Ayar Değişti ('⚡ KAPSAMA HESAPLA' Butonuna Basın)**"
                    if degisiklik_bekliyor else "🟢 **Kuponlar Güncel & Senkronize**"
                )
                evren_etiketi = "🛡️ %100 Kesin Şablon" if mutlak_sablon_garantisi else ("🧬 Akıllı Hibrit Ekonomi" if hibrit_ekonomi_modu else "📐 Filtreli Evren")
                st.info(
                    f"{durum_etiketi} | **Mod:** {evren_etiketi} | **Şablon:** **{banko_say}** Banko, **{cifte_say}** Çifte, **{kapali_say}** Kapalı | "
                    f"**🌟 G1:** {len(g1_indeksleri)} Maç ({g1_aralik[0]}-{g1_aralik[1]}) | "
                    f"**🔥 G2:** {len(g2_indeksleri)} Maç ({g2_aralik[0]}-{g2_aralik[1]})\n\n"
                    f"🧮 **Ham Şablon:** `{ham_kolon_sayisi:,} Kolon ({ham_kolon_sayisi * kolon_fiyati:,.0f} TL)`  ➔  "
                    f"{limit_metni}; gerçekleşen kapsama hesap sonrasında gösterilir."
                )
            with col_buton:
                st.write("")
                uretim_tetikle = st.button(
                    "⚡ KAPSAMA HESAPLA",
                    type="primary",
                    use_container_width=True,
                    disabled=(bos_mac_var or sira_hatasi_var or ham_kolon_sayisi > 300_000)
                )

            if sira_hatasi_var:
                st.error("⚠️ **Bülten Sıra Hatası:** 'No' sütunundaki maç sıra numaraları 1'den 15'e kadar benzersiz olmalıdır!")
            elif bos_mac_var:
                st.error("⚠️ Her maçta en az 1 tercih (1, X veya 2) işaretli olmalıdır.")
            elif ham_kolon_sayisi > 300_000:
                st.warning(
                    "⚠️ **CPU Koruması:** Şablonunuz 300.000 kolonu aşıyor. "
                    "Lütfen yukarıdaki **'🎯 Bütçeme Göre Otomatik Kur'** veya **'🌱 Ekonomik'** butonuna basın."
                )

            # DÜZELTME 3 & 4 (v15.1):
            # - Otomatik anlık senkronizasyon yalnızca <= 4.000 kolonda devreye girer (büyük şablonlarda arayüzü kilitlemez).
            # - uretilen_kuponlar ASLA None yapılarak silinmez! Böylece 2. ve 3. sekmeler her zaman kesintisiz çalışır.
            # - tablo_baz_df sol menü değişimlerinde yeniden atanmaz; tablo zıplaması önlenir.
            otomatik_hizli_yenile = (
                aninda_otomatik_hesapla
                and (degisiklik_bekliyor or sol_menu_degisti)
                and not bos_mac_var
                and not sira_hatasi_var
                and ham_kolon_sayisi <= 4000
            )
            ilk_acilis_uretim = (
                st.session_state.uretilen_kuponlar is None
                and not bos_mac_var
                and not sira_hatasi_var
                and ham_kolon_sayisi <= 4000
            )

            if degisiklik_bekliyor or bos_mac_var or sira_hatasi_var or ham_kolon_sayisi > 300_000 or max_kolon_limiti == 0:
                st.session_state.uretilen_kuponlar = None
                st.session_state.son_uretim_ozeti = None
            if max_kolon_limiti == 0:
                st.info("Sıfır bütçe: aktif kolon yok.")
            if max_kolon_limiti != 0 and not bos_mac_var and not sira_hatasi_var and ham_kolon_sayisi<=300_000 and (uretim_tetikle or otomatik_hizli_yenile or (ilk_acilis_uretim and not st.session_state.get('son_param_imzasi'))):
                with st.spinner("⚡ Garantili kuponlar ve deterministik denetim hesaplanıyor..."):
                    if ai_filtre_modu:
                        limitler = tam_otonom_analiz(s_veriler, strateji_modu, aktif_sablon=g_sablon)
                    else:
                        limitler = {
                            "1": range_1, "X": range_x, "2": range_2,
                            "fav": range_fav, "plase": range_plase, "surpriz": range_surpriz,
                            "z_zarf": (-1.95, 2.25),
                            "ardisik_1": max_ardisik_1, "ardisik_x": max_ardisik_x, "ardisik_2": max_ardisik_2,
                            "banko_siniri": banko_siniri, "cifte_siniri": cifte_sans_siniri
                        }

                    (
                        mat, puanlar, kompozit_skor, esnetilenler,
                        ham_evren, ham_puanlar, ham_kompozit,
                        hibrit_evren, hibrit_puanlar, hibrit_kompozit
                    ) = vektorel_filtrele(
                        g_sablon, s_veriler, limitler,
                        g1_indeksleri=g1_indeksleri if grup_guvence_aktif else [],
                        g1_aralik=g1_aralik,
                        g2_indeksleri=g2_indeksleri if grup_guvence_aktif else [],
                        g2_aralik=g2_aralik,
                        ev_agirligi=ev_katsayisi,
                        log_zarf_aktif=log_zarf_aktif,
                        kademe_aktif=kademe_filtre_aktif,
                        entropi_aktif=entropi_filtresi,
                        homojen_aktif=homojen_bulten,
                        kati_filtre=kati_filtre_kilidi
                    )

                    if mutlak_sablon_garantisi:
                        hedef_tam_kolonlar, hedef_tam_puanlar, hedef_tam_komp = ham_evren, ham_puanlar, ham_kompozit
                        denetlenecek_hedef_evren = ham_evren
                    elif hibrit_ekonomi_modu:
                        hedef_tam_kolonlar, hedef_tam_puanlar, hedef_tam_komp = hibrit_evren, hibrit_puanlar, hibrit_kompozit
                        denetlenecek_hedef_evren = hibrit_evren
                    else:
                        hedef_tam_kolonlar, hedef_tam_puanlar, hedef_tam_komp = None, None, None
                        denetlenecek_hedef_evren = mat

                    if len(denetlenecek_hedef_evren) > 0:
                        garanti, g_puan, kapsama, budanan_adet, swap_adet = gelismis_garanti_ve_budama_uygula(
                            mat, puanlar, kompozit_skor, garanti_derecesi,
                            max_k=max_kolon_limiti,
                            akilli_merkez=akilli_merkez,
                            min_fark=benzerlik_elemesi,
                            hedef_kapsama=hedef_kapsama_orani,
                            tam_evren_kolonlar=hedef_tam_kolonlar,
                            tam_evren_puanlar=hedef_tam_puanlar,
                            tam_evren_kompozit=hedef_tam_komp,
                            sablon=g_sablon,
                            ortogonal_aktif=ortogonal_anahtar_aktif,veriler=s_veriler,arama_derinligi=arama_derinligi
                        )
                        aktif_meta = dict(gelismis_garanti_ve_budama_uygula.meta)
                        karsilastirma = []
                        if uretim_modu.startswith("12–15"):
                            onceki = None
                            rows143 = []
                            for d in (15,14,13,12):
                                if d == garanti_derecesi and hedef_kapsama_orani == 100 and benzerlik_elemesi == 1:
                                    sonuc, m = garanti, dict(aktif_meta)
                                else:
                                    sonuc, _, _, _, _ = gelismis_garanti_ve_budama_uygula(mat,puanlar,kompozit_skor,d,max_k=None,akilli_merkez=akilli_merkez,min_fark=1,hedef_kapsama=100.,tam_evren_kolonlar=hedef_tam_kolonlar,tam_evren_puanlar=hedef_tam_puanlar,tam_evren_kompozit=hedef_tam_komp,sablon=g_sablon,veriler=s_veriler,baslangic=onceki if d < 14 else None,ortogonal_aktif=ortogonal_anahtar_aktif,arama_derinligi=arama_derinligi)
                                    m = dict(gelismis_garanti_ve_budama_uygula.meta)
                                # Daha güçlü hedefin örtüsü daha zayıf hedef için geçerli adaydır.
                                if onceki is not None and (not m['hedef_tam'] or len(onceki)<len(sonuc)):
                                    hits=_en_yakin_isabet(onceki,denetlenecek_hedef_evren)
                                    if np.all(hits>=d):
                                        sonuc=onceki.copy();m.update(hedef_tam=True,kapsama_adet=100.,kapsama_kutle=100.,optimal=(m.get('alt_sinir')==len(sonuc)),yontem='Üst garanti çözümünden doğrulanmış devralma',durum='HEDEF DOĞRULANDI')
                                if m['hedef_tam']: onceki=sonuc
                                if d==garanti_derecesi and hedef_kapsama_orani==100 and benzerlik_elemesi==1:
                                    garanti=sonuc;aktif_meta=dict(m);kapsama=float(m['kapsama_adet']);g_puan=np.sum(np.array([[v[k] for k in ('1','X','2')] for v in s_veriler])[np.arange(15),_kodla(garanti)],axis=1)
                                rows143.append({"Hedef":d,"Kolon":len(sonuc),"Alt sınır":m.get('alt_sinir'),"Kapsama (%)":round(m['kapsama_adet'],4),"Optimum ispatı":m['optimal'],"Maliyet (TL)":len(sonuc)*kolon_fiyati})
                            karsilastirma=list(reversed(rows143))
                        mc = monte_carlo_simule_et(garanti, s_veriler, g_sablon)
                        denetim_secili = deterministik_garanti_denetle(garanti, denetlenecek_hedef_evren)
                        denetim_ham = deterministik_garanti_denetle(garanti, ham_evren)
                        if len(garanti)==0: st.warning("Bütçe veya koşullar nedeniyle geçerli kolon üretilemedi.")
                        st.session_state.son_param_imzasi = param_imzasi
                        st.session_state.son_sol_menu_imzasi = sol_menu_imzasi
                        degisiklik_bekliyor = False
                        st.session_state.uretilen_kuponlar = garanti
                        st.session_state.son_uretim_ozeti = {
                            "optimizasyon":aktif_meta,
                            "karsilastirma":karsilastirma, "uretim_modu":uretim_modu, "kolon_fiyati":kolon_fiyati, "imza":param_imzasi,
                            "mac_ids":[v["id"] for v in s_veriler],
                            "filtreli_adet": len(denetlenecek_hedef_evren),
                            "saf_filtreli_adet": len(mat),
                            "ham_adet": ham_kolon_sayisi,
                            "garanti_derecesi": garanti_derecesi,
                            "mutlak_sablon": mutlak_sablon_garantisi,
                            "hibrit_mod": hibrit_ekonomi_modu,
                            "kapsama": kapsama,
                            "budanan_adet": budanan_adet,
                            "swap_adet": swap_adet,
                            "mc": mc,
                            "denetim": denetim_secili,
                            "denetim_ham": denetim_ham,
                            "s_veriler": s_veriler,
                            "g_sablon": g_sablon,
                            "esnetilenler": esnetilenler
                        }
                    else:
                        st.session_state.uretilen_kuponlar = None
                        st.session_state.son_uretim_ozeti = None
                        st.session_state.son_param_imzasi = param_imzasi
                        st.session_state.son_sol_menu_imzasi = sol_menu_imzasi
                        st.warning("⚠️ Filtreler tüm kombinasyonları eledi; yeni çıktı yok.")

            if st.session_state.uretilen_kuponlar is not None and len(st.session_state.uretilen_kuponlar)>0 and st.session_state.son_uretim_ozeti is not None:
                garanti = st.session_state.uretilen_kuponlar
                ozet = st.session_state.son_uretim_ozeti
                mc = ozet["mc"]
                if ozet.get("karsilastirma"): st.dataframe(pd.DataFrame(ozet["karsilastirma"]),hide_index=True,use_container_width=True)
                meta=ozet.get('optimizasyon',{})
                if degisiklik_bekliyor or (max_kolon_limiti is not None and len(garanti)>max_kolon_limiti):
                    st.warning('Önceki üretim gösteriliyor; ayarlar/bütçe değişti. Yeniden hesaplayın.')
                if not meta.get('hedef_tam',False): st.warning('İstenen kapsama hedefi doğrulanmadı veya eski rapor. Kesin garanti yok.')
                elif not degisiklik_bekliyor: st.success('Tanımlı evrende seçilen kapsama hedefi doğrulandı (gerçek sonuç garantisi değildir).')
                if meta.get('alt_sinir') and meta.get('hedef_tam') and ozet.get('kapsama')==100.0:
                    st.caption(f"Alt sınır / çözüm: {meta['alt_sinir']} / {len(garanti)}; çözüm maliyetine göre ispatlanmamış fark üst sınırı: %{100*(len(garanti)-meta['alt_sinir'])/max(1,len(garanti)):.2f}")
                st.write(f"Yöntem: {meta.get('yontem','eski sürüm')} | Optimalite ispatı: {'var' if meta.get('optimal') else 'yok'} | Alt sınır: {meta.get('alt_sinir')} | Adet kapsama: %{meta.get('kapsama_adet',0):.2f} | Koşullu kütle: %{meta.get('kapsama_kutle',0):.2f}")
                if meta.get('alt_sinir') and max_kolon_limiti is not None and max_kolon_limiti < meta['alt_sinir'] and hedef_kapsama_orani == 100:
                    st.warning(f"Bütçe sınırı ({max_kolon_limiti:,}) teorik alt sınırdan ({meta['alt_sinir']:,}) düşük: bu şablonda yüzde 100 kapsama matematiksel olarak mümkün değil.")
                st.caption(f"Modelin şablon olasılığı (bağımsızlık varsayımı): %{mc.get('sablon_kutlesi',0):.4f}")
                denetim = ozet.get("denetim", {"tam_15": 0.0, "en_az_14": 0.0, "en_az_13": 0.0, "en_az_12": 0.0})
                denetim_ham = ozet.get("denetim_ham", denetim)
                ham_k = max(1, ozet["ham_adet"])
                tasarruf_orani = (1.0 - (len(garanti) / ham_k)) * 100

                if ozet.get("esnetilenler"):
                    st.caption(f"ℹ️ **Otonom Koruma:** Daralmaya karşı şu filtreler otomatik esnetildi: `{', '.join(ozet['esnetilenler'])}`")
                if ozet.get("budanan_adet", 0) > 0 or ozet.get("swap_adet", 0) > 0:
                    st.caption(
                        f"✂️ **v15.1 Ekonomik Sıkıştırma Kazancı:** Ters budama ile **{ozet.get('budanan_adet', 0)}** kolon, "
                        f"Ek yerel sıkıştırma ile **{ozet.get('swap_adet', 0)}** ekstra kolon "
                        f"hedef kapsama korunarak tasarruf edildi!"
                    )

                hedef_anahtar = {15: "tam_15", 14: "en_az_14", 13: "en_az_13", 12: "en_az_12"}[ozet["garanti_derecesi"]]
                if denetim_ham.get(hedef_anahtar, 0.0) < 100.0:
                    mod_adi = "Kesin Şablon" if ozet.get("mutlak_sablon") else ("Hibrit" if ozet.get("hibrit_mod") else "Filtreli Evren")
                    st.warning(
                        f"💡 **Önemli Garanti Bilgilendirmesi:** Şu an **'{mod_adi}'** modundasınız. "
                        f"Üretilen {len(garanti):,} kolon seçili hedef evrendeki {ozet['filtreli_adet']:,} senaryonun **%{denetim[hedef_anahtar]:.1f}**'ini örter; "
                        f"ancak aşırı sürpriz uç senaryolar dahil tüm ham şablonun ({ozet['ham_adet']:,} kolon) **%{denetim_ham[hedef_anahtar]:.1f}**'ini örter. "
                        f"Ham evrende tam kapsama doğrulanmamıştır; bütçe ve filtre koşullarını kontrol edin."
                    )

                m1, m2, m3, m4, m5, m6 = st.columns([1, 1.1, 1.1, 1.1, 1.1, 1.1])
                m1.metric("Ham -> Hedef Evren", f"{ozet['filtreli_adet']:,}", f"-%{100 - (ozet['filtreli_adet']*100/ham_k):.0f} Ön Eleme")
                m2.metric(f"🎯 {ozet['garanti_derecesi']}G Net Kolon", f"{len(garanti):,} Kolon", f"%{tasarruf_orani:.1f} Toplam Tasarruf")
                m3.metric("Kolon maliyeti (varsayılan fiyat)", f"{len(garanti) * kolon_fiyati:,.0f} TL", f"Kapsama: %{ozet.get('kapsama', 100):.1f}")
                m4.metric("🥇 Şablon İçi 14+ Gücü", f"%{mc['sablon_14_arti']:.1f}", f"Tam 15: %{mc['sablon_15']:.1f}")
                m5.metric("Simülasyon: 12+", f"%{mc['genel_12_arti']:.1f}", "Tahmin; gerçekleşmiş başarı değil")
                with m6:
                    st.write("")
                    st.download_button(
                        "📥 Senaryo kolonlarını indir (.TXT)",
                        "\n".join([" ".join(k) for k in garanti]),
                        f"spor_toto_v15_1_{ozet['garanti_derecesi']}G_{len(garanti)}kolon.txt",
                        mime="text/plain",
                        disabled=degisiklik_bekliyor or (max_kolon_limiti is not None and len(garanti)>max_kolon_limiti),
                        type="primary",
                        use_container_width=True
                    )

                st.caption(
                    f"🔬 **Deterministik Senaryo Kapsama Denetimi:** "
                    f"**Ham Şablon Evreni ({ozet['ham_adet']:,} senaryo):** "
                    f"Tam 15: **%{denetim_ham['tam_15']:.1f}** | En Az 14: **%{denetim_ham['en_az_14']:.1f}** | "
                    f"En Az 13: **%{denetim_ham['en_az_13']:.1f}** | En Az 12: **%{denetim_ham['en_az_12']:.1f}**  —  "
                    f"**Seçili Hedef Evren ({ozet['filtreli_adet']:,} senaryo):** "
                    f"Tam 15: **%{denetim['tam_15']:.1f}** | En Az 14: **%{denetim['en_az_14']:.1f}** | En Az 13: **%{denetim['en_az_13']:.1f}**"
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
            if (st.session_state.son_uretim_ozeti or {}).get('mac_ids') != st.session_state.secilen_mac_idleri:
                aktif_k=None
                st.warning('Üretim bülteni sırasıyla takip sırası uyuşmuyor; yeniden üretin.')

        if api_key and len(st.session_state.secilen_mac_idleri) == 15:
            if st.button("🔄 Canlı Skorları API'den Çek (90-Dk Resmi Kural Korumalı)", type="primary", use_container_width=True):
                st.session_state.canli_sonuclar, st.session_state.canli_skor_metni = canli_skorlari_cek(
                    st.session_state.secilen_mac_idleri, api_key
                )
                st.session_state["skor_revision14"]=st.session_state.get("skor_revision14",0)+1
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
                "Sonuç": st.column_config.SelectboxColumn(
                    "Sonuç",
                    options=["⏳ Bekliyor", "1", "X", "2", "🎲 Kura (1/X/2)"],
                    required=True
                )
            },
            key="sonuc14_"+hashlib.sha256(str((st.session_state.secilen_mac_idleri,st.session_state.get("skor_revision14",0))).encode()).hexdigest()[:12],
            disabled=["No", "Maç", "Skor"],
            hide_index=True,
            use_container_width=True,
            height=560
        )
        st.session_state.canli_sonuclar = sonuc_df["Sonuç"].tolist()

    with col_t2:
        if aktif_k is not None and len(aktif_k) > 0:
            if "Oturumdaki" in kaynak and st.session_state.son_uretim_ozeti is not None:
                ozet_bilgi = st.session_state.son_uretim_ozeti
                evren_turu = "🛡️ %100 Kesin Şablon" if ozet_bilgi.get("mutlak_sablon") else ("🧬 Akıllı Hibrit Ekonomi" if ozet_bilgi.get("hibrit_mod") else "📐 Filtreli Evren")
                st.caption(
                    f"📌 **Aktif Takip Edilen Kupon Seti:** `{len(aktif_k):,} Kolon` | "
                    f"**Hedef:** `{ozet_bilgi['garanti_derecesi']} Garanti` | "
                    f"**Evren:** `{evren_turu}` | **Ham Şablon:** `{ozet_bilgi['ham_adet']:,} Kolon`"
                )

            res = np.array(sonuc_df["Sonuç"].tolist())
            kesin_mask = np.isin(res, ["1", "X", "2"])
            kura_mask = (res == "🎲 Kura (1/X/2)")
            oynanan = int(np.sum(kesin_mask))

            if oynanan > 0:
                dogru_kesin = np.sum(aktif_k[:, kesin_mask] == res[kesin_mask], axis=1) if np.any(kesin_mask) else np.zeros(len(aktif_k), dtype=int)
                dogru = dogru_kesin
                hata = oynanan - dogru
                maks_h = 15 - hata

                if "Oturumdaki" in kaynak and st.session_state.son_uretim_ozeti is not None:
                    aktif_sablon_list = st.session_state.son_uretim_ozeti.get("g_sablon", [])
                    sablon_disi_maclar = []
                    for m_idx in np.where(kesin_mask)[0]:
                        if m_idx < len(aktif_sablon_list) and res[m_idx] not in aktif_sablon_list[m_idx]:
                            sablon_disi_maclar.append(f"{m_idx + 1}. Maç ({m_isim[m_idx]}: Geldi '{res[m_idx]}', Şablon '{'-'.join(aktif_sablon_list[m_idx])}')")
                    if sablon_disi_maclar:
                        st.warning(
                            f"⚠️ **Şablon Dışı Sonuç Tespiti ({len(sablon_disi_maclar)} Maç):** "
                            f"1. Sekmedeki tablonuzda işaretlenmemiş sonuç gerçekleşti: `{'; '.join(sablon_disi_maclar)}`. "
                            f"Bu nedenle kuponlar en fazla **{15 - len(sablon_disi_maclar)}** derecesine ulaşabilir."
                        )

                st.markdown(f"### 🏆 Canlı İkramiye Potası ({oynanan} / 15 Maç Tamamlandı)")
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("🥇 15'e Giden", f"{int(np.sum(maks_h == 15)):,}")
                k2.metric("🥈 14'e Giden", f"{int(np.sum(maks_h == 14)):,}")
                k3.metric("🥉 13'e Giden", f"{int(np.sum(maks_h == 13)):,}")
                k4.metric("🎯 12'ye Giden", f"{int(np.sum(maks_h == 12)):,}")

                en_yuksek_derece = int(np.max(maks_h))
                hedef_kuponlar = aktif_k[maks_h == en_yuksek_derece]
                bekleyen_indeksler = np.where(~kesin_mask)[0]

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
                                "Açık sonuç": ", ".join(acik_risk) if acik_risk else "Yok"
                            })
                        st.dataframe(pd.DataFrame(hedge_satirlar), hide_index=True, use_container_width=True)

                        st.caption("Bu tablo yalnızca açık sonuçları gösterir; ikramiye, net kâr veya finansal koruma garantisi değildir.")

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
                st.info("👈 Sol tablodan maç sonuçlarını seçtiğiniz anda canlı kapsama analizi hesaplanır.")
        else:
            st.info("👈 Takip başlatmak için önce 1. Sekmeden kupon üretin veya kupon dosyası yükleyin.")

# ------------------------------------------------------------------------------
# SEKME 3: AKILLI ÇEVRİMDIŞI AKTARIM VE RAPOR MERKEZİ (v15.1)
# ------------------------------------------------------------------------------
with tab_otomasyon:
    st.subheader("📋 Güvenli Kupon Denetim Merkezi v15.1")
    st.caption("Tek ekranda bütün kolonların yerel doğrulaması. Resmî hesap bağlantısı, otomatik bahis gönderimi ve ödeme bu sürümde yoktur.")
    o = st.session_state.son_uretim_ozeti or {}
    k = st.session_state.uretilen_kuponlar
    try:
        plan = aktarim_plan15(k,o,guncel_uretim_imzasi,uretim_modu,kolon_fiyati,hedef_butce_tl)
    except ValueError as exc:
        st.info(str(exc)); plan=None
    if plan:
        st.markdown("### 1. Platformu seçin")
        platform=st.radio('Platform etiketi',AKTARIM_PLATFORMLARI,horizontal=True,key='platform15')
        st.info('Seçim yalnızca dosya ve kontrol kaydına etiket ekler. Bu platformla hesap veya resmî API bağlantısı kurulmaz.')
        ledger=st.session_state.setdefault('aktarim_kontrol15',{})
        key=plan['id']+':'+platform
        try: record=aktarim_kayit15(plan,platform,ledger.get(key,[]))
        except ValueError: record=aktarim_kayit15(plan,platform,[])
        checked=record['checked']
        other=[p for p in AKTARIM_PLATFORMLARI if p!=platform and ledger.get(plan['id']+':'+p)]
        if other: st.warning('Aynı kolonlar başka platform etiketi altında kontrol edilmiş: '+', '.join(other)+'. Çift işlem riskine dikkat edin.')
        done,left=aktarim_ilerleme15(plan,checked)
        c=st.columns(4)
        c[0].metric('Toplam kolon',len(plan['rows']))
        c[1].metric('Hesaplanan toplam',f"{Decimal(plan['cost']):,.2f} TL")
        c[2].metric('Kontrol edilen',done)
        c[3].metric('Bekleyen kontrol',left)
        st.progress(done/len(plan['rows']))
        st.caption(f"{len(checked)}/{plan['packets']} paket kontrol kaydı | Üst bütçe {Decimal(plan['budget']):,.2f} TL | Bu sayaç yatırılan kupon veya ödeme kanıtı değildir.")
        if not o.get('optimizasyon',{}).get('hedef_tam'):
            st.warning('Seçili tam kapsama hedefi doğrulanmamış olabilir. Denetim raporunu inceleyin.')
        st.markdown('### 2. Bütün kolonları otomatik denetleyin')
        st.info('Hesap bağlantısı: YOK — Yetkili işlem API’si doğrulanmadı. Kullanıcı adı veya parola istenmez; gerçek kupon gönderimi ve ödeme yapılmaz.')
        audit_key=denetim_imza151(plan,o)
        if st.button('🔎 TÜM KOLONLARI KONTROL ET',type='primary',use_container_width=True,key='preflight151:'+key):
            st.session_state.pop('preflight151',None)
            try:
                with st.spinner('Bülten, kolonlar, maliyet ve ham evren kapsaması yeniden doğrulanıyor...'):
                    report=toplu_denetim151(plan,o)
                st.session_state['preflight151']=(audit_key,report)
            except (ValueError,TypeError,KeyError,OverflowError) as exc:
                st.error('Denetim durduruldu: '+str(exc))
        saved_audit=st.session_state.get('preflight151')
        if saved_audit and saved_audit[0]==audit_key:
            report=saved_audit[1]
            st.success(f"{report['kolon_sayisi']} kolon yerel denetimden geçti. Bu bilgi yatırılmış kupon sayısı değildir.")
            q=st.columns(3)
            q[0].metric('Yerel doğrulanan',report['kolon_sayisi'])
            q[1].metric('Bu uygulamanın gönderdiği',0)
            q[2].metric('Paket',report['paket_sayisi'])
            st.progress(1.0)
            if not report['ham_tam_kapsama']:
                st.warning('Ham şablonda seçilen hedef için %100 kapsama yoktur. Filtreli evren garantisi ile karıştırmayın.')
            st.write('Ham evren yeniden denetimi (%)',report['ham_kapsama'])
            st.download_button('📥 Toplu yerel denetim raporu (.JSON)',json.dumps(report,ensure_ascii=False,indent=2),f"denetim151_{plan['id'][:12]}.json",mime='application/json')
        else:
            st.caption('Güncel toplu denetim henüz tamamlanmadı.')
        st.markdown('### 3. Çevrimdışı paket ve arşiv (isteğe bağlı)')
        with st.expander('15 maçın bülten sırası',expanded=False):
            st.dataframe(pd.DataFrame({'No':range(1,16),'Maç':plan['names'],'Maç ID':plan['ids']}),hide_index=True,use_container_width=True)
        export_key='arsiv15:'+key+':'+plan['price']+':'+plan['budget']
        if st.button('📦 Tüm kolonlar için kontrol arşivi hazırla',type='primary',use_container_width=True):
            st.session_state['arsiv15_hazir']=(export_key,aktarim_arsiv15(plan,platform))
        cached=st.session_state.get('arsiv15_hazir')
        if cached and cached[0]==export_key:
            st.download_button('📥 TXT + CSV + bülten bilgileri (.ZIP)',cached[1],f"toto15_{plan['id'][:12]}.zip",mime='application/zip',use_container_width=True)
        st.caption('Genel amaçlı arşivdir; bahis sitelerinin doğrudan içe aktarabileceği doğrulanmış bir format değildir.')
        first=next((i for i in range(1,plan['packets']+1) if i not in checked),plan['packets'])
        nav='paket15:'+key
        if nav not in st.session_state: st.session_state[nav]=first
        navcols=st.columns(3)
        if navcols[0].button('← Önceki',key='prev15:'+key,disabled=st.session_state[nav]<=1): st.session_state[nav]-=1
        if navcols[1].button('İlk bekleyen paket',key='resume15:'+key): st.session_state[nav]=first
        if navcols[2].button('Sonraki →',key='next15:'+key,disabled=st.session_state[nav]>=plan['packets']): st.session_state[nav]+=1
        paket=int(st.number_input('Paket numarası (en fazla 4 kolon)',min_value=1,max_value=plan['packets'],step=1,key=nav))
        bas=(paket-1)*4; parca=plan['rows'][bas:bas+4]
        d={'No':range(1,16),'Maç':plan['names']}
        for i,col in enumerate(parca): d[chr(65+i)]=list(col)
        st.dataframe(pd.DataFrame(d),hide_index=True,use_container_width=True)
        st.caption(f"Paket {paket}/{plan['packets']} | Kolon {bas+1}–{bas+len(parca)} | {Decimal(plan['price'])*len(parca):,.2f} TL (tahmini)")
        st.download_button('Bu paketi indir (.TXT)','\n'.join(parca)+'\n',f"paket_{paket}_{plan['id'][:12]}.txt",mime='text/plain')
        if platform=='İddaa.com':
            with st.expander('Eski deneysel seçim önizleme asistanı (isteğe bağlı)',expanded=False):
                st.caption('v14.3 işaretleme önizlemesi korunmuştur; canlı siteyle uyumluluğu doğrulanmamıştır. Ödeme/gönderim yapmaz. Hata varsa manuel kontrol edin.')
                try:
                    pid=hashlib.sha256((plan['id']+':'+str(paket)).encode()).hexdigest()[:16]
                    js=tarayici_isaretleme_kodu(np.array([list(r) for r in parca]),plan['names'],pid)
                    st.code('javascript:'+urllib.parse.quote(js,safe="!~*'();:@&=+$,/?[]"),language='text')
                    st.caption('İsteğe bağlı: favori URL alanına eklenebilir; bu yalnız seçili paketin deneysel önizlemesidir.')
                    if st.checkbox('JavaScript kaynağını göster',key='js15:'+pid): st.code(js,language='javascript')
                except ValueError as exc: st.warning(str(exc))
        st.markdown('### 4. Manuel kontrol kaydı')
        st.caption('İşaret yalnızca manuel kontrolü kaydeder. Hiçbir hesap veya bahis işlemi başlatmaz.')
        a,b=st.columns(2)
        if a.button('✅ Bu paketi kontrol ettim',disabled=paket in checked,key='check15:'+key):
            ledger[key]=sorted(set(checked+[paket])); st.rerun()
        if b.button('Kontrol işaretini kaldır',disabled=paket not in checked,key='undo15:'+key):
            ledger[key]=[p for p in checked if p!=paket]; st.rerun()
        st.download_button('💾 Kontrol kaydını sakla (JSON)',json.dumps(record,ensure_ascii=False,indent=2),f"kontrol_{plan['id'][:12]}.json",mime='application/json')
        with st.expander('Kayıtlı kontrol ilerlemesini geri yükle'):
            saved=st.file_uploader('Kontrol JSON dosyası',type=['json'],key='restore15:'+key)
            if saved is not None and st.button('Kaydı doğrula ve geri yükle',key='restorebtn15:'+key):
                try:
                    if len(saved.getvalue())>1_000_000: raise ValueError('Dosya çok büyük.')
                    x=json.loads(saved.getvalue())
                    if x.get('schema')!='15.0-manual-review' or x.get('plan_id')!=plan['id'] or x.get('platform')!=platform:
                        raise ValueError('Kayıt bu bülten, kolon dizisi veya platforma ait değil.')
                    restored=aktarim_kayit15(plan,platform,x.get('checked'))
                    ledger[key]=sorted(set(checked+restored['checked'])); st.rerun()
                except (ValueError,TypeError,AttributeError) as exc: st.error(str(exc))
    st.divider()
    if st.session_state.son_uretim_ozeti:
        o=st.session_state.son_uretim_ozeti
        st.json(o.get('optimizasyon',{}))
        st.download_button('Denetim raporu (JSON)',json.dumps(o,ensure_ascii=False,indent=2,default=str),'spor_toto_v15_1_denetime.json',mime='application/json')
    st.divider()
    st.subheader("Geçmiş tahmin kayıtları — kalibrasyon testi")
    st.caption("CSV: fixture_id, kickoff, snapshot, p1, px, p2, result. Tarihler ISO 8601 ve saat dilimi içermeli. Olasılık 0–1. Her maç için maçtan önceki son tek snapshot kullanılır. Bu bölüm kendi kendine geçmiş tahmin üretmez.")
    f=st.file_uploader('Tahmin arşivi CSV',type=['csv'],key='backtest14')
    if f is not None:
        try:
            d=pd.read_csv(f); req=['fixture_id','kickoff','snapshot','p1','px','p2','result']
            if not set(req)<=set(d): raise ValueError('Eksik CSV sütunu')
            for c in ['kickoff','snapshot']: d[c]=pd.to_datetime(d[c],utc=True,errors='raise')
            invalid=int((d.snapshot>=d.kickoff).sum());d=d[d.snapshot<d.kickoff].sort_values('snapshot').drop_duplicates('fixture_id',keep='last')
            d['result']=d['result'].astype(str).str.upper();p=d[['p1','px','p2']].to_numpy(float)
            if not len(d) or not np.isfinite(p).all() or np.any(p<0) or np.any(abs(p.sum(axis=1)-1)>1e-4) or not d.result.isin(['1','X','2']).all():raise ValueError('Geçerli maç/olasılık/sonuç kaydı yok veya değerler geçersiz.')
            y=np.array([{'1':0,'X':1,'2':2}[v] for v in d.result]);oh=np.eye(3)[y]
            losses=-np.log(np.maximum(p[np.arange(len(p)),y],1e-15));bs=((p-oh)**2).sum(axis=1)
            pred=p.argmax(axis=1);acc=(pred==y)
            cols=st.columns(3);cols[0].metric('Maç',len(d));cols[1].metric('Log Loss',f'{losses.mean():.4f}');cols[2].metric('Brier (3 sınıf toplamı)',f'{bs.mean():.4f}')
            st.write(f'En yüksek olasılık isabeti: %{100*acc.mean():.1f} | Maç sonrası kayıt elendi: {invalid}')
            cal=pd.DataFrame({'p':p.ravel(),'actual':oh.ravel()});cal['band']=pd.cut(cal.p,np.linspace(0,1,11),include_lowest=True)
            st.dataframe(cal.groupby('band',observed=True).agg(n=('p','size'),forecast=('p','mean'),actual=('actual','mean')).reset_index().assign(band=lambda x:x.band.astype(str)))
            st.caption('Kaynağın gerçekten maç öncesinde kaydedildiği kullanıcı tarafından doğrulanmalıdır. Bu sonuçlar tek başına sistem üstünlüğünü kanıtlamaz.')
        except Exception as exc: st.error(f'Backtest dosyası işlenemedi: {exc}')
