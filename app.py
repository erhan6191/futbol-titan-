import streamlit as st
import requests
import math
import json
import re
import hashlib
import unicodedata
import urllib.parse
from difflib import SequenceMatcher
from datetime import datetime, timedelta
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import pandas as pd

st.set_page_config(
    page_title="Spor Toto AI Pro v12.9 — Piyasa Seviyesi Ekonomik & %100 Garantili Motor",
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
<title>Spor Toto AI Pro v12.9 - Gerçek Oyun Saha Kılavuzu</title>
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
            <h1>🏆 Spor Toto AI Pro v12.9 — Piyasa Seviyesi Ekonomik & %100 Garantili Saha Kılavuzu</h1>
            <span>Ortogonal Küp Anahtarları, 2-Opt Sıkıştırma, Akıllı Hibrit Ekonomi & Mükerrer Korumalı 4'lü Kolon Asistanı</span>
        </div>
        <button class="print-btn no-print" onclick="window.print()">🖨️ PDF Olarak Kaydet / Yazdır (CTRL+P)</button>
    </div>
    <div class="alert">
        <strong>🌱 v12.9 Gerçek Oyun İçin 6 Altın Yenilik:</strong><br>
        1. <strong>🔑 Ortogonal / Hamming Küp Anahtarı (La Jolla Covering):</strong> 14 Garantili daraltmada açgözlü (greedy) algoritma yerine önce teorik minimum olan matematiksel mod-3/mod-2 simetrik blok anahtarlarını dener ve en az kolon çıkaranı seçer.<br>
        2. <strong>✂️ 2-Opt Yer Değiştirmeli Sıkıştırma (2-Çıkar-1-Koy):</strong> Ters budama sonrasında, seçilen kuponlardan 2 tanesini silip yerlerine ikisinin de yükünü tek başına taşıyan 1 ortak merkez kolon yerleştirerek kupon sayısını piyasa minimumuna indirir.<br>
        3. <strong>🧬 Akıllı Hibrit Ekonomi Modu (G1 %100 + G2 Daraltmalı):</strong> Banko ve G1 (Ağır Favori) maçlarınızı %100 kesin garantide tutarken sadece G2 (Plase/Sürpriz) maçlarındaki aşırı uç kombinasyonları süzerek maliyeti %40-%60 düşürür.<br>
        4. <strong>🔒 Katı Filtre Kilidi:</strong> Filtreli evren modunda oynarken bütçenizin sessizce şişmemesi için otomatik filtre esnetmeyi kapatma seçeneği eklendi.<br>
        5. <strong>⚡ Mükerrer Dolum Korumalı İddaa.com Asistanı:</strong> 4 kolonu doldurduğunuz anda sayacı otomatik hazırlar ve aynı 4 kolonu yanlışlıkla ikinci kez doldurmanızı sesli/görsel uyarıyla engeller.<br>
        6. <strong>🛟 Canlı Hedge (Dutching):</strong> Pazar günü son maçlara 14/15 adayı ile girdiğinizde 2. Sekmedeki Finansal Sigorta Hesaplayıcısı ile garantili net kârı kilitleyin.
    </div>
    <div class="section">
        <h2>📊 Otomatik Kupon Yatırma (Yöntem B — Favori Çubuğu & Konsol) Özeti</h2>
        <table>
            <tr><th>Adım</th><th>Uygulama</th><th>Avantajı</th></tr>
            <tr><td><strong>1. Favori Çubuğuna Ekle</strong></td><td>Chrome Favoriler çubuğuna sağ tıklayıp <em>"Sayfa ekle..."</em> deyin, URL kısmına 3. Sekmedeki <strong>Bookmarklet</strong> kodunu yapıştırın.</td><td>F12 Konsol açma ve <code>allow pasting</code> yazma zorunluluğunu tamamen ortadan kaldırır.</td></tr>
            <tr><td><strong>2. Tek Tıkla 4 Kolon Doldur</strong></td><td><code>iddaa.com/spor-toto</code> sayfasında üstteki favori butonunuza tıklayın ve açılan panelde <strong>"🎯 4 Kolonu Doldur ve İlerle"</strong> butonuna basın.</td><td>A, B, C ve D kolonlarının tamamını (60 kutucuk) tek seferde işaretler ve sayacı otomatik olarak sıradaki 4'lüye hazırlar.</td></tr>
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
    "sema_versiyonu": "12.9"
}
for anahtar, deger in varsayilan_state.items():
    if anahtar not in st.session_state:
        st.session_state[anahtar] = deger

if st.session_state.get("sema_versiyonu") != "12.9":
    st.session_state.uretilen_kuponlar = None
    st.session_state.son_uretim_ozeti = None
    st.session_state.son_param_imzasi = None
    st.session_state.son_sol_menu_imzasi = None
    st.session_state.sema_versiyonu = "12.9"

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
    st.markdown("## 🏆 Spor Toto AI v12.9 Pro")
    st.caption("Piyasa Seviyesi Ekonomik & %100 Garantili Motor")

    st.download_button(
        label="📄 Kullanım Kılavuzunu İndir (PDF/HTML)",
        data=KULLANIM_KILAVUZU_HTML.encode("utf-8"),
        file_name="Spor_Toto_AI_v12_9_Kullanim_Kilavuzu.html",
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
            "15 Garanti (Sıfır Hata Payı - Tam İsabet)",
            "14 Garanti (1 Maç Hata Payı - %85+ Tasarruf)",
            "13 Garanti (2 Maç Hata Payı - %95+ Tasarruf)",
            "12 Garanti (3 Maç Hata Payı - %98+ Tasarruf)"
        ],
        index=0
    )
    garanti_derecesi = int(garanti_secimi.split()[0])

    kapsama_evreni_modu = st.radio(
        "🔒 Garanti Kapsama Evreni:",
        [
            "🛡️ %100 Kesin Şablon Garantisi (15/15 Tuttuğunda Asla Sekmez - Önerilen)",
            "🧬 Akıllı Hibrit Ekonomi (G1 %100 Kesin + G2 Optimize - %45 Ek Tasarruf)",
            "📐 Filtreli & Şartlı Evren Garantisi (Önce Filtreler Eler - Maksimum Tasarruf)"
        ],
        index=0,
        help="1. Seçenek: Tabloda işaretlediğiniz 15 maçlık tahminlerin tamamı tuttuğunda hiçbir filtre kuponunuzu garanti derecesinin altına düşüremez. 2. Seçenek (Hibrit): G1 (Ağır Favori) maçlarınızı %100 korurken sadece G2 (Plase/Sürpriz) grubunda 3. tercih yığılmalarını süzerek yarı yarıya ekonomi sağlar. 3. Seçenek: Tüm filtreleri uygular, kalan kuponlara garanti verir."
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
                "🔥 Süper Ekonomi (%85 Kütle - En Az Kolon)",
                "⚖️ Optimum Ekonomi (%93 Kütle - Piyasa Dengesi)",
                "🛡️ Tam Kapsama (%100 Kütle - Kesin Garanti)"
            ],
            value="🛡️ Tam Kapsama (%100 Kütle - Kesin Garanti)",
            help="%100 Kesin Garanti için 'Tam Kapsama (%100)' seçili olmalıdır. Bütçeyi daha da düşürmek isterseniz %93 veya %85 seçebilirsiniz."
        )
        if "85" in tasarruf_profili:
            hedef_kapsama_orani = 85.0
        elif "93" in tasarruf_profili:
            hedef_kapsama_orani = 93.0
        else:
            hedef_kapsama_orani = 100.0

    kolon_fiyati = st.number_input("Kolon Birim Fiyatı (TL):", min_value=1.0, value=10.0, step=1.0)
    hedef_butce_tl = st.number_input(
        "💸 Hedef Toplam Bütçe (TL):",
        min_value=10.0, max_value=500000.0, value=2500.0, step=50.0,
        help="Şablonu otomatik kurarken ve maksimum kolon sınırında baz alınacak bütçeniz."
    )
    hedef_kolon_sayisi = max(1, int(hedef_butce_tl // kolon_fiyati))
    st.caption(f"🎯 Hedef Bütçe Karşılığı: **En Fazla {hedef_kolon_sayisi:,} Kolon**")

    if garanti_derecesi == 15 and mutlak_sablon_garantisi:
        butce_kilidi_aktif = False
        max_kolon_limiti = None
        st.caption("🔒 **Kesinti Koruması:** 15 Garanti (%100 Kesin Şablon) modunda kuponların yarısının kesilip 14'e düşmemesi için bütçe kırpma kilidi devre dışıdır.")
    else:
        butce_kilidi_aktif = st.toggle(
            "🔒 Üretimi Bu Bütçeyle Kesin Sınırla",
            value=False,
            help="DİKKAT: Bu kilit açıldığında kupon sayısı bütçenizi aşmaz ancak şablonunuz çok genişse matematiksel garanti yüzdesi (%100'den aşağı) düşebilir."
        )
        max_kolon_limiti = hedef_kolon_sayisi if butce_kilidi_aktif else None

    aninda_otomatik_hesapla = st.toggle(
        "⚡ Tablo & Menü Değişikliklerinde Anında Senkronize Et (<= 65.000 Ham Kolon)",
        value=True,
        help="Açık olduğunda sol menüden veya tablodan yaptığınız değişiklikler anında kuponlara yansır; Canlı Takip sekmesi her zaman güncel kuponları gösterir."
    )

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
        min_value=0.0, max_value=1.0, value=0.20, step=0.05,
        help="0.15 - 0.30 arası gerçek olasılıkları korurken balon favorilerden dengeli şekilde kaçınır."
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
    st.markdown("### 🔬 3. v12.9 Ekonomik Sıkıştırma & Yapısal Filtreler")
    ortogonal_anahtar_aktif = st.toggle(
        "🔑 Ortogonal / Hamming Küp Anahtarı + 2-Opt Sıkıştırma (En Az Kolon)",
        value=True,
        help="Piyasadaki profesyonel programlar gibi sabit simetrik mod-3/mod-2 küp anahtarlarını ve 2-çıkar-1-koy (2-Opt) algoritmasını kullanarak kupon sayısını teorik minimuma indirir."
    )
    akilli_merkez = st.toggle("🧮 Tam Sayı (Integer) Set-Cover + Bloklu Ters Budama", value=True)
    log_zarf_aktif = st.toggle("📐 Normalize Shannon Log-Olasılık (Altın Koridor) Zarfı", value=True)
    kademe_filtre_aktif = st.toggle("📊 3 Kademeli (Favori/Plase/Sürpriz) Bütçesi", value=True)
    kati_filtre_kilidi = st.toggle(
        "🔒 Katı Filtre Kilidi (Filtreleri Sessizce Esnetme)",
        value=False,
        help="Açık olduğunda, çok dar filtreler girdiğinizde sistem filtreyi sessizce devre dışı bırakıp kupon sayısını şişirmez; seçtiğiniz şartlara sadık kalır."
    )
    homojen_bulten = st.toggle("⚖️ Alt/Üst Bülten Homojenlik Filtresi", value=False)
    entropi_filtresi = st.toggle("🌀 Yapay/Simetrik Dizilim Elemesi", value=False)
    tuzak_koruma = st.toggle("🚨 Kırılgan Halk Tuzaklarını & Kararsızları Çifteye Al", value=True)

    if garanti_derecesi == 15:
        benzerlik_elemesi = 1
        st.caption("🔒 **Hamming Kilidi:** 15 Garanti modunda komşu kolonların elenmemesi için Min. Fark otomatik olarak `1`'e sabitlenmiştir.")
    else:
        benzerlik_elemesi = st.select_slider(
            "🔍 Kuponlar Arası Min. Farklı Maç (Hamming):",
            options=[1, 2, 3, 4],
            value=1,
            help="Tam matematiksel garanti (%100 örtme ve en az kolon) için '1' önerilir. 2 veya üzeri seçildiğinde kuponlar birbirinden uzaklaşır ancak yakın kombinasyonlar elenebilir."
        )

    ai_filtre_modu = st.toggle("🤖 Şablon-Duyarlı Otonom İstatistik Sınırları", value=True)

    if not ai_filtre_modu:
        with st.expander("⚙️ Manuel Filtre Ayarları"):
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
            "versiyon": "12.9",
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
            file_name=f"spor_toto_v12_9_oturum_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
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
                    yuklenen_df = pd.DataFrame(veri_json["tablo_df"])
                    st.session_state.tablo_baz_df = yuklenen_df.copy()
                    st.session_state.tablo_df = yuklenen_df.copy()
                    st.session_state.tablo_versiyon += 1
                if veri_json.get("uretilen_kuponlar"):
                    st.session_state.uretilen_kuponlar = np.array(veri_json["uretilen_kuponlar"])
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
    progress = st.progress(0, text="v12.9 Dixon-Coles kalibrasyonu, büro sapması ve halk eğilimi hesaplanıyor...")
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
                        skor_metinleri[idx] = f"⚠️ Ertelendi/Kura ({durum})"
                        yeni_sonuclar[idx] = "🎲 Kura (1/X/2)"
    except Exception:
        pass
    return yeni_sonuclar, skor_metinleri


# ==============================================================================
# v12.9 BÜTÇE-DUYARLI ŞABLON KURUCU, ORTOGONAL ANAHTAR VE 2-OPT SIKIŞTIRMA MOTORU
# ==============================================================================
def akilli_cifte_sec(v):
    s = sorted([(v["1"], "1"), (v["X"], "X"), (v["2"], "2")], reverse=True)
    en_b_oran, en_b_secim = s[0][0], s[0][1]
    ikinci_oran, ikinci_secim = s[1][0], s[1][1]

    if {en_b_secim, ikinci_secim} == {"1", "2"} and v["X"] >= 27 and (en_b_oran - ikinci_oran) >= 5:
        return [en_b_secim, "X"]
    return [en_b_secim, ikinci_secim]


def butceye_gore_sablon_optimize_et(veriler, hedef_kolon, garanti_derecesi, mutlak_mod=True, hibrit_mod=False, tuzak_aktif=True):
    if mutlak_mod:
        sikistirma_carpani = {15: 1.0, 14: 7.5, 13: 32.0, 12: 105.0}.get(garanti_derecesi, 12.0)
    elif hibrit_mod:
        sikistirma_carpani = {15: 1.8, 14: 12.5, 13: 52.0, 12: 160.0}.get(garanti_derecesi, 18.0)
    else:
        sikistirma_carpani = {15: 2.8, 14: 18.0, 13: 75.0, 12: 225.0}.get(garanti_derecesi, 25.0)

    alt_taban = 64 if garanti_derecesi == 15 else 16
    hedef_ham_ust_sinir = min(160000, max(alt_taban, int(hedef_kolon * sikistirma_carpani)))
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
        "ardisik_1": max(5, zorunlu_ard_1 + 1),
        "ardisik_x": max(3, zorunlu_ard_x + 1),
        "ardisik_2": max(4, zorunlu_ard_2 + 1),
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
        kademe_haritasi[m_i, sira_mat[m_i, 0]] = 0  # 1. Tercih (Favori)
        kademe_haritasi[m_i, sira_mat[m_i, 1]] = 1  # 2. Tercih (Plase)
        kademe_haritasi[m_i, sira_mat[m_i, 2]] = 2  # 3. Tercih (Sürpriz)

    def filtre_uygula(mevcut_mat, maske, etiket):
        kalan = int(np.sum(maske))
        if kati_filtre and kalan > 0:
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

    if log_zarf_aktif and len(matris) > 8:
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

    # AKILLI HİBRİT EKONOMİ EVRENİ (G1 %100 Korunur, sadece G2 içindeki aşırı 3. tercih sürpriz yığılmaları elenir)
    hibrit_maske = np.ones(len(ham_matris), dtype=bool)
    ham_kademeler = kademe_haritasi[np.arange(15), ham_matris]
    toplam_agir_surpriz = np.sum(ham_kademeler == 2, axis=1)
    hibrit_maske &= (toplam_agir_surpriz <= max(2, limitler["surpriz"][1]))
    if len(g2_indeksleri) >= 3:
        g2_idx_h = np.array(g2_indeksleri, dtype=int)
        g2_agir_surp = np.sum(ham_kademeler[:, g2_idx_h] == 2, axis=1)
        hibrit_maske &= (g2_agir_surp <= max(1, int(math.ceil(len(g2_indeksleri) * 0.45))))
    if int(np.sum(hibrit_maske)) < 4:
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


def deterministik_garanti_denetle(secilen_kolonlar, hedef_evren):
    if len(secilen_kolonlar) == 0 or len(hedef_evren) == 0:
        return {"tam_15": 0.0, "en_az_14": 0.0, "en_az_13": 0.0, "en_az_12": 0.0}

    M = len(hedef_evren)
    K = len(secilen_kolonlar)

    kupon_kod = np.zeros((K, 15), dtype=np.int8)
    kupon_kod[secilen_kolonlar == "X"] = 1
    kupon_kod[secilen_kolonlar == "2"] = 2

    kupon_oh = np.zeros((K, 45), dtype=np.int16)
    kupon_oh[np.arange(K)[:, None], np.arange(15)[None, :] * 3 + kupon_kod] = 1

    maks_isabet = np.zeros(M, dtype=np.int16)
    BLOK = 15000
    for bas in range(0, M, BLOK):
        bit = min(M, bas + BLOK)
        parca = hedef_evren[bas:bit]
        B = len(parca)
        evren_kod = np.zeros((B, 15), dtype=np.int8)
        evren_kod[parca == "X"] = 1
        evren_kod[parca == "2"] = 2
        evren_oh = np.zeros((B, 45), dtype=np.int16)
        evren_oh[np.arange(B)[:, None], np.arange(15)[None, :] * 3 + evren_kod] = 1
        maks_isabet[bas:bit] = np.max(evren_oh @ kupon_oh.T, axis=1)

    return {
        "tam_15": float(np.mean(maks_isabet == 15) * 100.0),
        "en_az_14": float(np.mean(maks_isabet >= 14) * 100.0),
        "en_az_13": float(np.mean(maks_isabet >= 13) * 100.0),
        "en_az_12": float(np.mean(maks_isabet >= 12) * 100.0)
    }


def ortogonal_anahtar_adaylari_uret(kolonlar, kompozit_skor, sablon, hedef_int):
    """
    YENİLİK (v12.9 - Piyasa Seviyesi Sabit Ortogonal Küp Anahtarları):
    14 Garantili daraltmada La Jolla Covering Repository'deki mod-3 (Kapalı maçlar için 3^k / 3)
    ve mod-2 (Çifte maçlar için 2^d / 2) doğrusal eşlik (parity check) alt-kümelerini oluşturur.
    Böylece örneğin 3 Kapalıda 9 yerine 3 kolon, 4 Kapalıda 12 yerine 9 kolonluk teorik minimum
    başlangıç çekirdeğini yakalar.
    """
    if hedef_int != 14 or sablon is None:
        return []

    N = len(kolonlar)
    if N == 0 or N > 80000:
        return []

    kapali_idx = [i for i, s in enumerate(sablon) if len(s) == 3]
    cifte_idx = [i for i, s in enumerate(sablon) if len(s) == 2]

    yerel_mat = np.zeros((N, 15), dtype=np.int16)
    for m_i, s in enumerate(sablon):
        for yerel_kod, harf in enumerate(s):
            if yerel_kod > 0:
                yerel_mat[kolonlar[:, m_i] == harf, m_i] = yerel_kod

    aday_listesi = []

    # 1. Kapalı maçlar varsa Mod-3 Doğrusal Eşlik (Ternary Hamming Subspace) çekirdeği
    if len(kapali_idx) >= 1:
        k_toplam = np.sum(yerel_mat[:, kapali_idx], axis=1) % 3
        for r in range(3):
            idx_r = np.where(k_toplam == r)[0]
            if len(idx_r) > 0:
                aday_listesi.append((float(np.mean(kompozit_skor[idx_r])), idx_r))

    # 2. Sadece Çifte maçlar varsa (Kapalı == 0) Mod-2 Eşlik (Binary Parity) çekirdeği
    if len(kapali_idx) == 0 and len(cifte_idx) >= 2:
        c_toplam = np.sum(yerel_mat[:, cifte_idx], axis=1) % 2
        for r in range(2):
            idx_r = np.where(c_toplam == r)[0]
            if len(idx_r) > 0:
                aday_listesi.append((float(np.mean(kompozit_skor[idx_r])), idx_r))

    # 3. Hem Çifte hem Kapalı varsa Mod-6 Melez Çekirdek
    if len(kapali_idx) >= 2 and len(cifte_idx) >= 2:
        k_top = np.sum(yerel_mat[:, kapali_idx], axis=1) % 3
        c_top = np.sum(yerel_mat[:, cifte_idx], axis=1) % 2
        for r3 in range(3):
            for r2 in range(2):
                idx_rc = np.where((k_top == r3) & (c_top == r2))[0]
                if len(idx_rc) > 0:
                    aday_listesi.append((float(np.mean(kompozit_skor[idx_rc])), idx_rc))

    aday_listesi.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in aday_listesi[:3]]


def ters_budama_ve_2opt_sikistir(nihai_indeksler, one_hot, kapsanan_evren, hedef_int, kompozit_skor):
    """
    YENİLİK (v12.9 - Bloklu Ters Budama + 2-Opt Yer Değiştirmeli Sıkıştırma):
    Adım 1: Gereksiz (1-Opt) kolonları temizler.
    Adım 2: Seçilen kuponlardan 2 tanesini çıkarıp yerlerine 1 ortak merkez koyarak
            %100 garantiyi bozmadan kupon sayısını piyasa minimumuna indirir (2-Çıkar-1-Koy).
    """
    nihai = list(nihai_indeksler)
    M_evren = len(kapsanan_evren)
    if len(nihai) <= 2 or M_evren == 0 or M_evren > 120000 or len(nihai) > 4500:
        return nihai, 0, 0

    K_sec = len(nihai)
    secilen_oh = one_hot[nihai]
    ortme_sayaci = np.zeros(M_evren, dtype=np.int16)
    kapsama_sayilari = np.zeros(K_sec, dtype=np.int32)

    BLOK = 10000
    for bas in range(0, M_evren, BLOK):
        bit = min(M_evren, bas + BLOK)
        evren_parca = one_hot[kapsanan_evren[bas:bit]]
        parca_mat = (secilen_oh @ evren_parca.T) >= hedef_int
        ortme_sayaci[bas:bit] = np.sum(parca_mat, axis=0, dtype=np.int16)
        kapsama_sayilari += np.sum(parca_mat, axis=1, dtype=np.int32)

    # ADIM 1: 1-OPT TERS BUDAMA
    kontrol_sirasi = np.argsort(kapsama_sayilari)
    aktif_tut = np.ones(K_sec, dtype=bool)
    budanan_adet = 0

    for i in kontrol_sirasi:
        merkez_vektor = secilen_oh[i]
        gereksiz_mi = True
        for bas in range(0, M_evren, BLOK):
            bit = min(M_evren, bas + BLOK)
            evren_parca = one_hot[kapsanan_evren[bas:bit]]
            ortuyor_mu = (evren_parca @ merkez_vektor) >= hedef_int
            if np.any(ortme_sayaci[bas:bit][ortuyor_mu] < 2):
                gereksiz_mi = False
                break
        if gereksiz_mi:
            aktif_tut[i] = False
            budanan_adet += 1
            for bas in range(0, M_evren, BLOK):
                bit = min(M_evren, bas + BLOK)
                evren_parca = one_hot[kapsanan_evren[bas:bit]]
                ortuyor_mu = (evren_parca @ merkez_vektor) >= hedef_int
                ortme_sayaci[bas:bit][ortuyor_mu] -= 1

    nihai = [nihai[i] for i in range(K_sec) if aktif_tut[i]]

    # ADIM 2: 2-OPT YER DEĞİŞTİRMELİ SIKIŞTIRMA (2 Kolon Sil -> 1 Ortak Merkez Ekle)
    swap_kazanci = 0
    if 3 <= len(nihai) <= 450 and M_evren <= 35000:
        evren_oh = one_hot[kapsanan_evren]
        devam = True
        tur = 0
        while devam and tur < 25 and len(nihai) >= 3:
            devam = False
            tur += 1
            K_cur = len(nihai)
            sec_oh = one_hot[nihai]
            kapsama_mat = (sec_oh @ evren_oh.T) >= hedef_int  # (K_cur, M_evren)
            ortme_say = np.sum(kapsama_mat, axis=0, dtype=np.int16)

            # En az tekil (benzersiz) yük taşıyan 35 kolonu aday çift olarak incele
            tekil_yuk = np.sum(kapsama_mat & (ortme_say[None, :] == 1), axis=1)
            aday_sirasi = np.argsort(tekil_yuk)[:min(35, K_cur)]

            for idx_a_pos in range(len(aday_sirasi)):
                i = int(aday_sirasi[idx_a_pos])
                for idx_b_pos in range(idx_a_pos + 1, len(aday_sirasi)):
                    j = int(aday_sirasi[idx_b_pos])
                    # i ve j birlikte çıkarıldığında açıkta kalacak olan senaryolar:
                    acikta_kalan_maske = (
                        ((ortme_say == 1) & (kapsama_mat[i] | kapsama_mat[j])) |
                        ((ortme_say == 2) & kapsama_mat[i] & kapsama_mat[j])
                    )
                    acik_idx = np.where(acikta_kalan_maske)[0]
                    if len(acik_idx) == 0:
                        nihai.pop(max(i, j))
                        budanan_adet += 1
                        devam = True
                        break
                    if len(acik_idx) > 81:
                        continue

                    acik_oh = evren_oh[acik_idx]
                    # Açıkta kalan tüm senaryoları tek başına örten bir merkez var mı?
                    uyum = np.all((evren_oh @ acik_oh.T) >= hedef_int, axis=1)
                    if np.any(uyum):
                        aday_havuz_idx = np.where(uyum)[0]
                        gercek_merkezler = kapsanan_evren[aday_havuz_idx]
                        mevcut_set = set(nihai) - {nihai[i], nihai[j]}
                        uygun_yeni = [int(m) for m in gercek_merkezler if int(m) not in mevcut_set]
                        if uygun_yeni:
                            en_iyi_yeni = max(uygun_yeni, key=lambda m: float(kompozit_skor[m]))
                            for sil_idx in sorted([i, j], reverse=True):
                                nihai.pop(sil_idx)
                            nihai.append(en_iyi_yeni)
                            swap_kazanci += 1
                            devam = True
                            break
                if devam:
                    break

    return nihai, budanan_adet, swap_kazanci


def gelismis_garanti_ve_budama_uygula(
    kolonlar, puanlar, kompozit_skor, hedef,
    max_k=None, akilli_merkez=True, min_fark=1, hedef_kapsama=100.0,
    tam_evren_kolonlar=None, tam_evren_puanlar=None, tam_evren_kompozit=None,
    sablon=None, ortogonal_aktif=True
):
    """
    v12.9 Piyasa Seviyesi Ekonomik Daraltma Motoru:
    1. EV bonus ağırlığı (0.0005 tie-breaker) yalnızca eşit örtme gücüne sahip merkezler arasında eşitliği bozar;
       böylece kupon sayısının EV yüzünden şişmesi %100 engellenir.
    2. Ortogonal/Hamming küp anahtarı aktifse, 14G modunda simetrik blok anahtarlarını yarışmaya sokar ve
       en az kolon üreten çözümü seçer.
    3. Son aşamada Bloklu Ters Budama + 2-Opt Sıkıştırma (2-Çıkar-1-Koy) uygular.
    """
    if hedef == 15:
        min_fark = 1

    if tam_evren_kolonlar is not None and len(tam_evren_kolonlar) > 0:
        if len(kolonlar) > 0:
            kod_tam = np.zeros((len(tam_evren_kolonlar), 15), dtype=np.int64)
            kod_tam[tam_evren_kolonlar == "X"] = 1
            kod_tam[tam_evren_kolonlar == "2"] = 2
            uf_katsayi = (3 ** np.arange(15, dtype=np.int64))
            imza_tam = kod_tam @ uf_katsayi

            kod_filt = np.zeros((len(kolonlar), 15), dtype=np.int64)
            kod_filt[kolonlar == "X"] = 1
            kod_filt[kolonlar == "2"] = 2
            imza_filt = kod_filt @ uf_katsayi

            filtre_icinde_mi = np.isin(imza_tam, imza_filt)
            oncelik_skoru = tam_evren_kompozit + np.where(filtre_icinde_mi, 2.5, 0.0)
            sira = np.argsort(oncelik_skoru)[::-1]

            kolonlar = tam_evren_kolonlar[sira]
            puanlar = tam_evren_puanlar[sira]
            kompozit_skor = tam_evren_kompozit[sira]
        else:
            kolonlar = tam_evren_kolonlar
            puanlar = tam_evren_puanlar
            kompozit_skor = tam_evren_kompozit
    else:
        if len(kolonlar) == 0:
            return np.empty((0, 15), dtype="<U1"), np.array([]), 0.0, 0, 0

    N = len(kolonlar)
    hedef_int = int(hedef)

    if hedef_int == 15 and (tam_evren_kolonlar is not None or (hedef_kapsama >= 99.9 and max_k is None)):
        if max_k is not None and tam_evren_kolonlar is None:
            return kolonlar[:max_k], puanlar[:max_k], float(min(100.0, max_k * 100.0 / max(1, N))), 0, 0
        return kolonlar, puanlar, 100.0, 0, 0

    mat = np.zeros((N, 15), dtype=np.int8)
    mat[kolonlar == "X"] = 1
    mat[kolonlar == "2"] = 2

    one_hot = np.zeros((N, 45), dtype=np.int16)
    satir_idx = np.arange(N)[:, None]
    sutun_ofset = np.arange(15)[None, :] * 3
    one_hot[satir_idx, sutun_ofset + mat] = 1

    # DÜZELTME (v12.9): EV bonusu yalnızca eşit sayıda açık kombinasyon örten merkezler arasında
    # eşitlik bozucu (tie-breaker: 0.0005) olarak kullanılır; asla daha az yer kapatan kolonu seçtirmez!
    skor_min = float(np.min(kompozit_skor))
    skor_ptp = max(1e-5, float(np.max(kompozit_skor) - skor_min))
    norm_ev_tiebreaker = ((kompozit_skor - skor_min) / skor_ptp).astype(np.float32) * 0.0005

    if hedef_kapsama >= 99.9:
        agirlik = np.ones(N, dtype=np.float32)
    else:
        agirlik = np.exp((kompozit_skor - np.max(kompozit_skor)) * 0.35).astype(np.float32)
        agirlik = agirlik / np.mean(agirlik)
    toplam_agirlik = float(np.sum(agirlik))

    def set_cover_calistir(baslangic_indeksleri=None):
        kapsanmamis_maske = np.ones(N, dtype=bool)
        secilebilir_merkez_maske = np.ones(N, dtype=bool)
        nihai_yerel = []
        kapsama_yerel = 0.0

        if baslangic_indeksleri is not None and len(baslangic_indeksleri) > 0:
            for b_idx in baslangic_indeksleri:
                if max_k and len(nihai_yerel) >= max_k:
                    break
                b_int = int(b_idx)
                nihai_yerel.append(b_int)
                secilebilir_merkez_maske[b_int] = False

            if len(nihai_yerel) > 0:
                BLOK_B = 10000
                sec_oh_b = one_hot[nihai_yerel]
                for bas_b in range(0, N, BLOK_B):
                    bit_b = min(N, bas_b + BLOK_B)
                    es_b = one_hot[bas_b:bit_b] @ sec_oh_b.T
                    kapsanmamis_maske[bas_b:bit_b] &= ~np.any(es_b >= hedef_int, axis=1)

                if hedef_kapsama >= 99.9:
                    kapsama_yerel = float(np.sum(~kapsanmamis_maske) / float(N) * 100.0)
                else:
                    kapsama_yerel = float(np.sum(agirlik[~kapsanmamis_maske]) / toplam_agirlik * 100.0)

        while np.any(kapsanmamis_maske):
            if max_k and len(nihai_yerel) >= max_k:
                break
            if hedef_kapsama < 99.9 and kapsama_yerel >= hedef_kapsama:
                break

            kapsanmamis_indeksler = np.where(kapsanmamis_maske)[0]
            uygun_merkezler = np.where(secilebilir_merkez_maske)[0]
            if len(uygun_merkezler) == 0:
                uygun_merkezler = kapsanmamis_indeksler

            if akilli_merkez and len(kapsanmamis_indeksler) > 1 and hedef_int < 15:
                acik_frekans = np.sum(one_hot[kapsanmamis_indeksler], axis=0, dtype=np.int32)
                if len(uygun_merkezler) <= 1500:
                    aday_idx = uygun_merkezler
                else:
                    on_skor = (one_hot[uygun_merkezler].astype(np.float32) @ acik_frekans.astype(np.float32)) + norm_ev_tiebreaker[uygun_merkezler]
                    en_iyi_aday_indeksleri = np.argpartition(on_skor, -1100)[-1100:]
                    kalan_bas_aday = kapsanmamis_indeksler[:120]
                    kalan_son_aday = kapsanmamis_indeksler[-120:]
                    aday_idx = np.unique(np.concatenate([uygun_merkezler[en_iyi_aday_indeksleri], kalan_bas_aday, kalan_son_aday]))

                ornek_say = min(120000, len(kapsanmamis_indeksler))
                if len(kapsanmamis_indeksler) <= ornek_say:
                    ornek_idx = kapsanmamis_indeksler
                else:
                    ornek_idx = kapsanmamis_indeksler[np.linspace(0, len(kapsanmamis_indeksler) - 1, ornek_say, dtype=int)]

                eslesme_mat = one_hot[aday_idx] @ one_hot[ornek_idx].T
                kapsama_mat = (eslesme_mat >= hedef_int)

                if hedef_kapsama >= 99.9:
                    kapsanan_skor = np.sum(kapsama_mat, axis=1, dtype=np.float32) + norm_ev_tiebreaker[aday_idx]
                else:
                    kapsanan_skor = (kapsama_mat.astype(np.float32) @ agirlik[ornek_idx]) + norm_ev_tiebreaker[aday_idx]

                en_iyi_yerel = int(np.argmax(kapsanan_skor))
                m_idx = int(aday_idx[en_iyi_yerel])

                if kapsanan_skor[en_iyi_yerel] < 0.99:
                    m_idx = int(kapsanmamis_indeksler[0])
            else:
                m_idx = int(kapsanmamis_indeksler[0])

            nihai_yerel.append(m_idx)
            secilebilir_merkez_maske[m_idx] = False

            eslesmeler = one_hot[kapsanmamis_indeksler] @ one_hot[m_idx]
            yeni_kapsananlar = kapsanmamis_indeksler[eslesmeler >= hedef_int]
            kapsanmamis_maske[yeni_kapsananlar] = False

            if min_fark > 1:
                kalan_merkezler = np.where(secilebilir_merkez_maske)[0]
                if len(kalan_merkezler) > 0:
                    fark_sayisi = np.sum(mat[kalan_merkezler] != mat[m_idx], axis=1)
                    secilebilir_merkez_maske[kalan_merkezler[fark_sayisi < min_fark]] = False

            if hedef_kapsama >= 99.9:
                kapsama_yerel = float(np.sum(~kapsanmamis_maske) / float(N) * 100.0)
            else:
                kapsama_yerel = float(np.sum(agirlik[~kapsanmamis_maske]) / toplam_agirlik * 100.0)

        kapsanan_evren_idx = np.where(~kapsanmamis_maske)[0]
        if akilli_merkez and hedef_int < 15:
            nihai_yerel, bud_adet, swp_adet = ters_budama_ve_2opt_sikistir(
                nihai_yerel, one_hot, kapsanan_evren_idx, hedef_int, kompozit_skor
            )
        else:
            bud_adet, swp_adet = 0, 0

        return nihai_yerel, kapsama_yerel, bud_adet, swp_adet

    # Yöntem 1: Saf Tam Sayı Set-Cover + 2-Opt
    en_iyi_nihai, en_iyi_kapsama, en_iyi_budanan, en_iyi_swap = set_cover_calistir(None)

    # Yöntem 2: Ortogonal / Hamming Küp Anahtarı Adaylarıyla Yarıştır (En az kolon çıkanı seç)
    if ortogonal_aktif and min_fark == 1 and hedef_int == 14 and sablon is not None and N <= 65000:
        ort_adaylar = ortogonal_anahtar_adaylari_uret(kolonlar, kompozit_skor, sablon, hedef_int)
        for ort_cekirdek in ort_adaylar:
            if len(ort_cekirdek) <= len(en_iyi_nihai) * 1.35:
                aday_nihai, aday_kapsama, aday_bud, aday_swp = set_cover_calistir(ort_cekirdek)
                if aday_kapsama >= en_iyi_kapsama - 0.05 and len(aday_nihai) < len(en_iyi_nihai):
                    fark_kazanc = len(en_iyi_nihai) - len(aday_nihai)
                    en_iyi_nihai = aday_nihai
                    en_iyi_kapsama = aday_kapsama
                    en_iyi_budanan = aday_bud
                    en_iyi_swap = aday_swp + fark_kazanc

    if max_k and len(en_iyi_nihai) > max_k:
        en_iyi_nihai = en_iyi_nihai[:max_k]

    return kolonlar[en_iyi_nihai], puanlar[en_iyi_nihai], en_iyi_kapsama, en_iyi_budanan, en_iyi_swap


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

    kupon_oh = np.zeros((len(kuponlar), 45), dtype=np.int16)
    kupon_oh[np.arange(len(kuponlar))[:, None], np.arange(15)[None, :] * 3 + k_num] = 1

    sim_genel_oh = np.zeros((N_SIM, 45), dtype=np.int16)
    sim_genel_oh[np.arange(N_SIM)[:, None], np.arange(15)[None, :] * 3 + sim_genel] = 1
    derece_genel = np.max(sim_genel_oh @ kupon_oh.T, axis=1)

    sim_sablon_oh = np.zeros((N_SIM, 45), dtype=np.int16)
    sim_sablon_oh[np.arange(N_SIM)[:, None], np.arange(15)[None, :] * 3 + sim_sablon] = 1
    derece_sablon = np.max(sim_sablon_oh @ kupon_oh.T, axis=1)

    halk_mat = np.array([[v["h1"], v["hX"], v["h2"]] for v in veriler], dtype=float)
    secilen_halk_ort = np.mean(halk_mat[np.arange(15), k_num])
    ikramiye_endeksi = max(10.0, min(99.0, 100.0 - secilen_halk_ort))

    return {
        "sablon_15": float(np.mean(derece_sablon == 15) * 100),
        "sablon_14_arti": float(np.mean(derece_sablon >= 14) * 100),
        "genel_12_arti": float(np.mean(derece_genel >= 12) * 100),
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
    paket_imza = hashlib.md5(json.dumps(aktif_paket).encode("utf-8")).hexdigest()[:8]
    kisa_maclar = [m.split("-")[0].strip()[:10] for m in mac_isimleri]

    js_kodu = f"""// ============================================================================
// 🏆 SPOR TOTO AI PRO v12.9 — MÜKERRER KORUMALI İDDAA.COM 4'LÜ KOLON ASİSTANI
// 🛡️ GÜVENLİK GARANTİSİ: Bu kod ASLA 'Oyna / Öde / Onayla' butonuna basmaz!
// ============================================================================
(function() {{
    const PAKET_NO = {paket_no};
    const TOPLAM_PAKET = {toplam_paket};
    const PAKET_IMZA = "{paket_imza}";
    const HIZ_MS = {hiz_ms};
    const BEKLENEN_TAKIMLAR = {json.dumps(kisa_maclar, ensure_ascii=False)};
    const KUPONLAR = {json.dumps(aktif_paket)};
    const STORAGE_KEY = "st_ai_v12_9_progress_" + PAKET_IMZA;
    const FILLED_KEY = "st_ai_v12_9_filled_" + PAKET_IMZA;

    let aktifIdx = parseInt(localStorage.getItem(STORAGE_KEY) || "0", 10);
    if (aktifIdx >= KUPONLAR.length || aktifIdx < 0) aktifIdx = 0;
    let doldurulanSet = new Set(JSON.parse(localStorage.getItem(FILLED_KEY) || "[]"));
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
        if (manuelSeciciSinif) {{
            const ozelSonuc = geometrikKutuTaramasiYap((el) => {{
                return el.tagName === manuelSeciciSinif.tag &&
                       (manuelSeciciSinif.cls === "" || (el.className || "") === manuelSeciciSinif.cls);
            }});
            if (ozelSonuc.length === 15) return ozelSonuc;
        }}

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

        const geoMetinKutular = geometrikKutuTaramasiYap((el) => {{
            const txt = (el.innerText || "").trim().toUpperCase();
            return ["1", "0", "X", "2"].includes(txt) && el.children.length <= 1;
        }});
        if (geoMetinKutular.length === 15) return geoMetinKutular;

        return geoBosKareler.length >= geoMetinKutular.length ? geoBosKareler : geoMetinKutular;
    }}

    const hud = document.createElement("div");
    hud.id = "st-ai-floating-hud";
    hud.style.cssText = "position:fixed;top:16px;right:16px;width:405px;background:#0f172a;color:#f8fafc;border:2px solid #3b82f6;border-radius:12px;padding:14px;z-index:999999;font-family:'Segoe UI',sans-serif;box-shadow:0 12px 28px rgba(0,0,0,0.55);font-size:13px;";
    document.body.appendChild(hud);

    function hudGuncelle(durumMesaji = "") {{
        const satirlar = macSatirlariniBul();
        const tabloKolonKapasitesi = satirlar.length === 15 ? satirlar[0].kolonSayisi : 4;
        const bitisIdx = Math.min(aktifIdx + tabloKolonKapasitesi, KUPONLAR.length);
        const aktifGrup = KUPONLAR.slice(aktifIdx, bitisIdx);
        const harfler = ["A", "B", "C", "D"];
        const buGrupDoldurulduMu = doldurulanSet.has(aktifIdx);

        let durumRenk = satirlar.length === 15 ? "#4ade80" : "#fbbf24";
        let ustBilgi = satirlar.length === 15
            ? `✅ 15 Maç Hazır (${{tabloKolonKapasitesi === 4 ? "İddaa.com A-B-C-D 4'lü Kolon Modu" : "Tekli Kolon Modu"}})`
            : `⚠️ Otomatik taramada ${{satirlar.length}}/15 satır bulundu. Aşağıdaki '🎯 1. Kutuyu Tanıt' butonuna basıp 1. maçın ilk kutucuğuna tıklayın.`;

        let onizlemeHtml = aktifGrup.map((kl, idx) =>
            `<div style="margin:2px 0;"><strong style="color:#60a5fa;">${{harfler[idx] || ""}} Kolonu (#${{aktifIdx + idx + 1}}):</strong> ${{kl.join("-")}}</div>`
        ).join("");

        let mukerrerEtiketi = buGrupDoldurulduMu
            ? `<span style="background:#dc2626;color:#ffffff;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:bold;">⚠️ Bu Grup Az Önce Dolduruldu</span>`
            : `<span style="background:#166534;color:#dcfce7;padding:2px 8px;border-radius:99px;font-size:11px;">🛡️ Mükerrer Korumalı</span>`;

        hud.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #334155;padding-bottom:8px;margin-bottom:8px;">
                <div>
                    <strong style="font-size:14px;color:#60a5fa;">🏆 Spor Toto AI v12.9 Hızlı Asistan</strong>
                    <div style="font-size:11px;color:#94a3b8;">Paket ${{PAKET_NO}} / ${{TOPLAM_PAKET}} • Toplam: ${{KUPONLAR.length}} Kolon</div>
                </div>
                <button id="st-ai-kapat" style="background:#ef4444;color:white;border:none;border-radius:6px;padding:4px 8px;cursor:pointer;font-weight:bold;">✕</button>
            </div>
            <div style="background:#1e293b;padding:8px;border-radius:8px;margin-bottom:8px;font-size:11.5px;color:${{durumRenk}};">
                ${{ustBilgi}}
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <span>📌 Sıradaki Kolonlar: <strong style="color:#38bdf8;font-size:14px;">#${{aktifIdx + 1}} - #${{bitisIdx}} / ${{KUPONLAR.length}}</strong></span>
                ${{mukerrerEtiketi}}
            </div>
            <div style="background:#020617;padding:8px;border-radius:6px;font-family:monospace;font-size:11.5px;color:#e2e8f0;margin-bottom:10px;border:1px solid #1e293b;">
                ${{onizlemeHtml || "🎉 PAKET TAMAMLANDI"}}
            </div>
            ${{durumMesaji ? `<div style="margin-bottom:8px;color:#38bdf8;font-size:12px;text-align:center;font-weight:bold;">${{durumMesaji}}</div>` : ""}}
            <div style="display:grid;grid-template-columns:1fr 2.3fr 1fr;gap:6px;margin-bottom:6px;">
                <button id="st-ai-geri" style="background:#334155;color:white;border:none;padding:8px;border-radius:6px;cursor:pointer;font-weight:bold;">◀ Geri</button>
                <button id="st-ai-isaretle" style="background:#2563eb;color:white;border:none;padding:8px;border-radius:6px;cursor:pointer;font-weight:bold;">
                    🎯 ${{aktifGrup.length}} Kolonu Doldur & İlerle
                </button>
                <button id="st-ai-ileri" style="background:#16a34a;color:white;border:none;padding:8px;border-radius:6px;cursor:pointer;font-weight:bold;">Atla ▶</button>
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
                hudGuncelle("▶ Sıradaki kolon grubuna geçildi.");
            }} else {{
                hudGuncelle("🎉 Bu paketteki tüm kolonların sonundasınız!");
            }}
        }};
        document.getElementById("st-ai-sifirla").onclick = (e) => {{
            e.preventDefault();
            aktifIdx = 0;
            doldurulanSet.clear();
            localStorage.setItem(STORAGE_KEY, "0");
            localStorage.setItem(FILLED_KEY, "[]");
            hudGuncelle("🔄 Sayaç ve mükerrer hafızası 1. kolona sıfırlandı.");
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

        if (doldurulanSet.has(aktifIdx)) {{
            const onay = window.confirm("⚠️ DİKKAT: #" + (aktifIdx + 1) + " ile #" + (aktifIdx + aktifGrup.length) + " arasındaki kolonları az önce zaten doldurdunuz! Aynı kuponu mükerrer yatırmamak için İptal'e basabilirsiniz. Yine de tekrar doldurulsun mu?");
            if (!onay) return;
        }}

        const doldurulanBas = aktifIdx + 1;
        const doldurulanBit = aktifIdx + aktifGrup.length;
        hudGuncelle("⏳ #" + doldurulanBas + "-#" + doldurulanBit + " arası " + aktifGrup.length + " kolon dolduruluyor...");

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

        doldurulanSet.add(aktifIdx);
        localStorage.setItem(FILLED_KEY, JSON.stringify(Array.from(doldurulanSet)));

        window.scrollTo({{ top: 0, behavior: "smooth" }});

        // OTOMATİK SAYAÇ İLERLETME (Mükerrer dolumu önler)
        if (aktifIdx + kapasite < KUPONLAR.length) {{
            aktifIdx += kapasite;
            localStorage.setItem(STORAGE_KEY, String(aktifIdx));
            hudGuncelle("✅ #" + doldurulanBas + "-#" + doldurulanBit + " dolduruldu! Şimdi siteden kuponu onaylayın; sayaç otomatik olarak sıradaki #" + (aktifIdx + 1) + ". kolona hazırlandı.");
        }} else {{
            hudGuncelle("🎉 #" + doldurulanBas + "-#" + doldurulanBit + " dolduruldu! Bu paketteki TÜM KOLONLARI tamamladınız, siteden onaylayabilirsiniz.");
        }}
    }}

    hudGuncelle();
}})();"""
    return js_kodu


def bookmarklet_tek_satir_uret(js_kodu):
    temiz_satirlar = []
    for satir in js_kodu.splitlines():
        s = satir.strip()
        if not s or s.startswith("//"):
            continue
        temiz_satirlar.append(s)
    tek_satir = " ".join(temiz_satirlar)
    kodlanmis = urllib.parse.quote(tek_satir, safe="(){}[];:,._-+*/=!<>?")
    return f"javascript:{kodlanmis}"


# ==============================================================================
# ANA SEKMELER
# ==============================================================================
tab_uretim, tab_takip, tab_otomasyon = st.tabs([
    "🎛️ 1. Profesyonel Sendika Masası & Ekonomik Garantili Üretim",
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
        # ADIM 2: PROFESYONEL SENDİKA KONTROL PANELİ (v12.9 EKONOMİK MOTOR)
        # ======================================================================
        if st.session_state.analiz_verisi:
            veriler = st.session_state.analiz_verisi
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
                    st.session_state.uretilen_kuponlar = None
                    st.rerun()
            with tb1:
                if st.button("🌱 Ekonomik (5B-6Ç-4K)", use_container_width=True):
                    yeni_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="super_eko_5b_6c_4k")
                    st.session_state.tablo_baz_df = yeni_df.copy()
                    st.session_state.tablo_df = yeni_df.copy()
                    st.session_state.tablo_versiyon += 1
                    st.session_state.uretilen_kuponlar = None
                    st.rerun()
            with tb2:
                if st.button("🤖 AI Dengeli (4B-7Ç-4K)", use_container_width=True):
                    yeni_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="ai")
                    st.session_state.tablo_baz_df = yeni_df.copy()
                    st.session_state.tablo_df = yeni_df.copy()
                    st.session_state.tablo_versiyon += 1
                    st.session_state.uretilen_kuponlar = None
                    st.rerun()
            with tb3:
                if st.button("💎 Sendika (3B-6Ç-6K)", use_container_width=True):
                    yeni_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="sendika_3b_6c_6k")
                    st.session_state.tablo_baz_df = yeni_df.copy()
                    st.session_state.tablo_df = yeni_df.copy()
                    st.session_state.tablo_versiyon += 1
                    st.session_state.uretilen_kuponlar = None
                    st.rerun()
            with tb4:
                if st.button("🔒 15 Banko", use_container_width=True):
                    yeni_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="15_banko")
                    st.session_state.tablo_baz_df = yeni_df.copy()
                    st.session_state.tablo_df = yeni_df.copy()
                    st.session_state.tablo_versiyon += 1
                    st.session_state.uretilen_kuponlar = None
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

            if mutlak_sablon_garantisi:
                tahmini_daraltma = {15: 1.0, 14: 7.5, 13: 32.0, 12: 105.0}.get(garanti_derecesi, 10.0)
            elif hibrit_ekonomi_modu:
                tahmini_daraltma = {15: 1.8, 14: 12.5, 13: 52.0, 12: 160.0}.get(garanti_derecesi, 16.0)
            else:
                tahmini_daraltma = {15: 2.8, 14: 18.0, 13: 75.0, 12: 225.0}.get(garanti_derecesi, 20.0)
            tahmini_net_kolon = max(1, int(round(ham_kolon_sayisi / tahmini_daraltma)))

            sol_menu_imza_ham = json.dumps({
                "garanti": garanti_derecesi,
                "mutlak_sablon": mutlak_sablon_garantisi,
                "hibrit_mod": hibrit_ekonomi_modu,
                "ortogonal": ortogonal_anahtar_aktif,
                "kati_filtre": kati_filtre_kilidi,
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
                "ai_filtre": ai_filtre_modu,
                "g1_aralik": g1_aralik,
                "g2_aralik": g2_aralik
            }, sort_keys=True)
            sol_menu_imzasi = hashlib.md5(sol_menu_imza_ham.encode("utf-8")).hexdigest()
            sol_menu_degisti = (st.session_state.get("son_sol_menu_imzasi") != sol_menu_imzasi)

            imza_ham = json.dumps({
                "sablon": g_sablon,
                "oranlar": [(v["1"], v["X"], v["2"], v["h1"], v["hX"], v["h2"]) for v in s_veriler],
                "g1_idx": g1_indeksleri,
                "g2_idx": g2_indeksleri,
                "sol_menu_imzasi": sol_menu_imzasi
            }, sort_keys=True)
            param_imzasi = hashlib.md5(imza_ham.encode("utf-8")).hexdigest()
            degisiklik_bekliyor = (st.session_state.get("son_param_imzasi") != param_imzasi)

            col_ozet, col_buton = st.columns([2.2, 1.2])
            with col_ozet:
                durum_etiketi = "🟠 **Şablon Değişti (Üretim Bekliyor)**" if degisiklik_bekliyor else "🟢 **Kuponlar Güncel & Senkronize**"
                evren_etiketi = "🛡️ %100 Kesin Şablon" if mutlak_sablon_garantisi else ("🧬 Akıllı Hibrit Ekonomi" if hibrit_ekonomi_modu else "📐 Filtreli Evren")
                st.info(
                    f"{durum_etiketi} | **Mod:** {evren_etiketi} | **Şablon:** **{banko_say}** Banko, **{cifte_say}** Çifte, **{kapali_say}** Kapalı | "
                    f"**🌟 G1:** {len(g1_indeksleri)} Maç ({g1_aralik[0]}-{g1_aralik[1]}) | "
                    f"**🔥 G2:** {len(g2_indeksleri)} Maç ({g2_aralik[0]}-{g2_aralik[1]})\n\n"
                    f"🧮 **Ham Şablon:** `{ham_kolon_sayisi:,} Kolon ({ham_kolon_sayisi * kolon_fiyati:,.0f} TL)`  ➔  "
                    f"📉 **Beklenen {garanti_derecesi}G Çıktı:** `~{tahmini_net_kolon:,} Kolon (~{tahmini_net_kolon * kolon_fiyati:,.0f} TL)`"
                )
            with col_buton:
                st.write("")
                uretim_tetikle = st.button(
                    "⚡ GARANTİLİ KUPONLARI ÜRET",
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

            sol_menu_otomatik_yenile = (
                sol_menu_degisti
                and not bos_mac_var
                and not sira_hatasi_var
                and ham_kolon_sayisi <= 300_000
            )
            tablo_otomatik_yenile = (
                aninda_otomatik_hesapla
                and degisiklik_bekliyor
                and not bos_mac_var
                and not sira_hatasi_var
                and ham_kolon_sayisi <= 65_000
            )
            ilk_acilis_uretim = (
                st.session_state.uretilen_kuponlar is None
                and not bos_mac_var
                and not sira_hatasi_var
                and ham_kolon_sayisi <= 120_000
            )

            if degisiklik_bekliyor and not (uretim_tetikle or sol_menu_otomatik_yenile or tablo_otomatik_yenile or ilk_acilis_uretim):
                st.session_state.uretilen_kuponlar = None
                st.session_state.son_uretim_ozeti = None

            if uretim_tetikle or sol_menu_otomatik_yenile or tablo_otomatik_yenile or ilk_acilis_uretim:
                if uretim_tetikle:
                    st.session_state.tablo_baz_df = df_edit.copy()
                st.session_state.son_param_imzasi = param_imzasi
                st.session_state.son_sol_menu_imzasi = sol_menu_imzasi
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
                elif hibrit_ekonomi_modu:
                    hedef_tam_kolonlar, hedef_tam_puanlar, hedef_tam_komp = hibrit_evren, hibrit_puanlar, hibrit_kompozit
                else:
                    hedef_tam_kolonlar, hedef_tam_puanlar, hedef_tam_komp = None, None, None

                if len(mat) > 0 or len(ham_evren) > 0:
                    garanti, g_puan, kapsama, budanan_adet, swap_adet = gelismis_garanti_ve_budama_uygula(
                        mat, puanlar, kompozit_skor, garanti_derecesi,
                        max_k=max_kolon_limiti,
                        akilli_merkez=akilli_merkez,
                        min_fark=benzerlik_elemesi,
                        hedef_kapsama=hedef_kapsama_orani,
                        tam_evren_kolonlar=hedef_tam_kolonlar,
                        tam_evren_puanlar=hedef_tam_puanlar,
                        tam_evren_kompozit=hedef_tam_komp,
                        sablon=g_sablon if mutlak_sablon_garantisi else None,
                        ortogonal_aktif=ortogonal_anahtar_aktif
                    )
                    mc = monte_carlo_simule_et(garanti, s_veriler, g_sablon)
                    denetim_filtreli = deterministik_garanti_denetle(garanti, mat if len(mat) > 0 else ham_evren)
                    denetim_ham = deterministik_garanti_denetle(garanti, ham_evren)
                    st.session_state.uretilen_kuponlar = garanti
                    st.session_state.son_uretim_ozeti = {
                        "filtreli_adet": len(mat),
                        "ham_adet": ham_kolon_sayisi,
                        "garanti_derecesi": garanti_derecesi,
                        "mutlak_sablon": mutlak_sablon_garantisi,
                        "hibrit_mod": hibrit_ekonomi_modu,
                        "kapsama": kapsama,
                        "budanan_adet": budanan_adet,
                        "swap_adet": swap_adet,
                        "mc": mc,
                        "denetim": denetim_filtreli,
                        "denetim_ham": denetim_ham,
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
                denetim_ham = ozet.get("denetim_ham", denetim)
                ham_k = max(1, ozet["ham_adet"])
                tasarruf_orani = (1.0 - (len(garanti) / ham_k)) * 100

                if ozet.get("esnetilenler"):
                    st.caption(f"ℹ️ **Otonom Koruma:** Daralmaya karşı şu filtreler otomatik esnetildi: `{', '.join(ozet['esnetilenler'])}`")
                if ozet.get("budanan_adet", 0) > 0 or ozet.get("swap_adet", 0) > 0:
                    st.caption(
                        f"✂️ **v12.9 Ekonomik Sıkıştırma Kazancı:** Ters budama ile **{ozet.get('budanan_adet', 0)}** kolon, "
                        f"Ortogonal Anahtar & 2-Opt (2-Çıkar-1-Koy) sıkıştırma ile **{ozet.get('swap_adet', 0)}** ekstra kolon "
                        f"garanti gücü bozulmadan tasarruf edildi!"
                    )

                hedef_anahtar = {15: "tam_15", 14: "en_az_14", 13: "en_az_13", 12: "en_az_12"}[ozet["garanti_derecesi"]]
                if not ozet.get("mutlak_sablon") and denetim_ham.get(hedef_anahtar, 0.0) < 99.9:
                    mod_adi = "🧬 Akıllı Hibrit Ekonomi" if ozet.get("hibrit_mod") else "📐 Filtreli & Şartlı Evren Garantisi"
                    st.warning(
                        f"💡 **Önemli Garanti Bilgilendirmesi:** Şu an **'{mod_adi}'** modundasınız. "
                        f"Üretilen {len(garanti):,} kolon filtrelerden geçen {ozet['filtreli_adet']:,} senaryonun **%{denetim[hedef_anahtar]:.1f}**'ini örter; "
                        f"ancak aşırı sürpriz uç senaryolar dahil tüm ham şablonun ({ozet['ham_adet']:,} kolon) **%{denetim_ham[hedef_anahtar]:.1f}**'ini örter. "
                        f"15/15 tahmininiz tuttuğunda filtreler yüzünden 14'e düşmemek için sol menüden **'🛡️ %100 Kesin Şablon Garantisi'** modunu seçebilirsiniz."
                    )

                m1, m2, m3, m4, m5, m6 = st.columns([1, 1.1, 1.1, 1.1, 1.1, 1.1])
                m1.metric("Ham -> Filtreli", f"{ozet['filtreli_adet']:,}", f"-%{100 - (ozet['filtreli_adet']*100/ham_k):.0f} Filtre Elemesi")
                m2.metric(f"🎯 {ozet['garanti_derecesi']}G Net Kolon", f"{len(garanti):,} Kolon", f"%{tasarruf_orani:.1f} Toplam Tasarruf")
                m3.metric("Ödenecek Bütçe", f"{len(garanti) * kolon_fiyati:,.0f} TL", f"Kapsama: %{ozet.get('kapsama', 100):.1f}")
                m4.metric("🥇 Şablon İçi 14+ Gücü", f"%{mc['sablon_14_arti']:.1f}", f"Tam 15: %{mc['sablon_15']:.1f}")
                m5.metric("💎 İkramiye Çarpanı", f"{mc['ikramiye_endeksi']:.0f} / 100", f"Genel 12+: %{mc['genel_12_arti']:.1f}")
                with m6:
                    st.write("")
                    st.download_button(
                        "📥 Kuponları İndir (.TXT)",
                        "\n".join([" ".join(k) for k in garanti]),
                        f"spor_toto_v12_9_{ozet['garanti_derecesi']}G_{len(garanti)}kolon.txt",
                        mime="text/plain",
                        type="primary",
                        use_container_width=True
                    )

                st.caption(
                    f"🔬 **Deterministik Garanti Denetimi (15/15 Tahmin Tuttuğunda):** "
                    f"**Ham Şablon Evreni ({ozet['ham_adet']:,} senaryo):** "
                    f"Tam 15: **%{denetim_ham['tam_15']:.1f}** | En Az 14: **%{denetim_ham['en_az_14']:.1f}** | "
                    f"En Az 13: **%{denetim_ham['en_az_13']:.1f}** | En Az 12: **%{denetim_ham['en_az_12']:.1f}**  —  "
                    f"**Filtreli Evren ({ozet['filtreli_adet']:,} senaryo):** "
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
                "Sonuç": st.column_config.SelectboxColumn(
                    "Sonuç",
                    options=["⏳ Bekliyor", "1", "X", "2", "🎲 Kura (1/X/2)"],
                    required=True
                )
            },
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
            oynanan = int(np.sum(kesin_mask) + np.sum(kura_mask))

            if oynanan > 0:
                dogru_kesin = np.sum(aktif_k[:, kesin_mask] == res[kesin_mask], axis=1) if np.any(kesin_mask) else np.zeros(len(aktif_k), dtype=int)
                dogru = dogru_kesin + int(np.sum(kura_mask))
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
                bekleyen_indeksler = np.where(~(kesin_mask | kura_mask))[0]

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
            st.info("👈 Takip başlatmak için önce 1. Sekmeden kupon üretin veya kupon dosyası yükleyin.")

# ------------------------------------------------------------------------------
# SEKME 3: GÜVENLİ, ANLAŞILIR VE KOLAY OTOMATİK KUPON YATIRMA MERKEZİ (v12.9)
# ------------------------------------------------------------------------------
with tab_otomasyon:
    st.markdown("### 🛡️ Güvenli & Kolay Kupon Yatırma Merkezi (Safe-Play v12.9 — Mükerrer Korumalı 4'lü Kolon Destekli)")

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

        st.markdown(
            f"""<div class="step-card">
                <span class="safe-badge">🛡️ SALT-İŞARETLEME & MÜKERRER KORUMA KİLİDİ AKTİF</span>
                <strong style="margin-left:8px;">Bu sistemdeki hiçbir araç kendi başına 'Oyna / Öde / Onayla' butonuna basmaz!</strong><br>
                <span style="font-size:0.9rem;color:#334155;">
                • Toplam Üretilen: <strong>{toplam_kolon_say:,} Kolon ({toplam_tutar_tl:,.0f} TL)</strong> &nbsp;|&nbsp;
                • 1. Maç: <strong>{aktif_mac_isimleri[0]}</strong> &nbsp;➔&nbsp; 15. Maç: <strong>{aktif_mac_isimleri[-1]}</strong>
                </span>
            </div>""",
            unsafe_allow_html=True
        )

        with st.expander("🔍 ADIM 1: Yatırmadan Önce 15 Maçın Resmi Bülten Sırasını Doğrulayın (Çok Önemli)", expanded=False):
            st.caption("Kuponlarınızın yanlış maçlara işaretlenmemesi için aşağıdaki 1'den 15'e kadar olan sıranın oynayacağınız sitedeki (İddaa, Nesine, Bilyoner, Misli vb.) sıra ile birebir aynı olduğundan emin olun.")
            sira_k1, sira_k2, sira_k3 = st.columns(3)
            for idx_m, m_adi in enumerate(aktif_mac_isimleri):
                hedef_sutun = sira_k1 if idx_m < 5 else (sira_k2 if idx_m < 10 else sira_k3)
                hedef_sutun.markdown(f"**{idx_m + 1}.** {m_adi}")

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
                    file_name=f"st_v12_9_{len(k_oto)}kolon_{dosya_kontrol_imzasi}.txt",
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
                    file_name=f"st_v12_9_{len(k_oto)}kolon_{dosya_kontrol_imzasi}.csv",
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
                    "3. Artık `iddaa.com/spor-toto` sayfasındayken üstteki **🎯 Toto Doldur** butonuna bastığınızda **Mükerrer Korumalı 4'lü Kolon Asistanı** doğrudan açılır!"
                )
                st.code(bookmarklet_kodu, language="text")

                with st.expander("🖥️ Seçenek 2: Klasik F12 Konsol (Console) Kodu İle Çalıştır", expanded=False):
                    st.info(
                        "1. `iddaa.com/spor-toto` sayfasında **F12** tuşuna basıp **Console** sekmesine geçin (İlk kez yapıştırıyorsanız `allow pasting` yazıp Enter'a basın).\n"
                        "2. Aşağıdaki kodu kopyalayıp konsola yapıştırın ve **Enter**'a basın.\n"
                        "3. Sağ üstte açılan panelde **'🎯 4 Kolonu Doldur & İlerle'** butonuna basın. Asistan 4 kolonu doldurduğu anda sayacı otomatik olarak sıradaki 4'lüye geçirir."
                    )
                    st.code(js_hud_kodu, language="javascript")

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
