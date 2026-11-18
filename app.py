import streamlit as st
import requests
import math
import json
import re
import hashlib
import unicodedata
import html
import urllib.parse
import io
import csv
import zipfile
import itertools
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import pandas as pd

st.set_page_config(
    page_title="Spor Toto AI Pro v19.0 — ULTIMATE FINAL (ANALIZ)",
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

# --- HTML KULLANIM KILAVUZU ---
KULLANIM_KILAVUZU_HTML = "<!doctype html><html lang='tr'><head><meta charset='utf-8'><title>Spor Toto AI Pro v19.0 Kolay Kullanım</title><style>body{max-width:760px;margin:48px auto;font:17px/1.65 system-ui,Arial;color:#243044;padding:0 20px}h1{color:#14375b}li{margin-bottom:10px}.note{padding:12px 16px;border-left:4px solid #2563eb;background:#f5f8ff}</style></head><body><h1>SPOR TOTO AI PRO v19.0 — Kolay Kullanım</h1><p>Motor ve hesaplama kuralları orijinal v19.0'dır. Sadece ekran düzeni sadeleştirilmiştir.</p><ol><li>Sol menüye API-Football anahtarınızı girin.</li><li>Sol menüde kolon birim fiyatını ve toplam bütçeyi kontrol edin. Diğer ayarlar başlangıçta gizli olup orijinal değerleriyle aktiftir.</li><li><b>1. Maçlar ve Kolonlar:</b> günleri seçin, maçları yükleyin, resmî bülten sırasına göre 15 maç ekleyin, sırayı onaylayın ve <b>Analizi Başlat</b> düğmesine basın.</li><li><b>Bütçeme Göre Otomatik Kur</b> ardından <b>KAPSAMA HESAPLA</b> düğmesine basın. İsteğe bağlı alternatif şablonlar katlanır paneldedir.</li><li>Birinci sekmenin başındaki <b>BÜLTEN ONAYI</b> bölümünü açıp 15 maç sırasını gözden geçirerek onayınızı kaydedin.</li><li><b>2. Dosyaları İndir:</b> A01–A10 kabul kontrolü uygun olduğunda tüm kolonların TXT/ZIP analiz dosyalarını indirin.</li><li><b>3. Sonuç Takibi:</b> maçların sonuçlarını ve kuponların durumunu inceleyin.</li><li>Teknik önizleme, geçmiş tahmin testi, Anti-Public ve bağımsız matematik denetimi için <b>Gelişmiş Araçlar</b> bölümünü açın.</li></ol><p class='note'><b>Önemli:</b> 12–15 kapsama hedefleri yalnız tanımlı koşullu şablon senaryolarına ilişkindir. Gerçek maç sonuçları veya kazanç garanti edilmez. Canlı kupon yatırma, ödeme, resmî kapanış ve makbuz doğrulaması yoktur.</p></body></html>"

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
    "paket_konfig_v161": None,
    "sema_versiyonu": "19.0",
    "v171_api_proof": None,
    "v17_receipts": {},
    "v17_official_user_csv": None,
    "v17_official_hash": None
}
for anahtar, deger in varsayilan_state.items():
    if anahtar not in st.session_state:
        st.session_state[anahtar] = deger

if st.session_state.get("sema_versiyonu") != "19.0":
    st.session_state.uretilen_kuponlar = None
    st.session_state.son_uretim_ozeti = None
    st.session_state.son_param_imzasi = None
    st.session_state.son_sol_menu_imzasi = None
    st.session_state.yatirilan_paketler = []
    st.session_state.paket_konfig_v161 = None
    # Eski sürüm tahminleri yeni güvenlik rejimine veri kaynağı olarak aktarılmaz.
    st.session_state.analiz_verisi = None
    st.session_state.tablo_df = None
    st.session_state.tablo_baz_df = None
    st.session_state.v17_receipts = {}
    st.session_state.v17_official_user_csv = None
    st.session_state.v17_official_hash = None
    st.session_state.v171_api_proof = None
    st.session_state.sema_versiyonu = "19.0"

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
    st.markdown("## 🏆 Spor Toto AI v19.0")
    st.caption("KOLAY KULLANIM ARAYÜZÜ — motor v19.0 ile aynı")
    st.caption("Denetimli analiz • Canlı otomatik oynama kapalı")
    st.caption("Analiz amaçlıdır; gerçek maç isabeti veya kazanç garantisi yoktur.")

    st.download_button(
        label="📄 Kullanım Kılavuzunu İndir (HTML)",
        data=KULLANIM_KILAVUZU_HTML.encode("utf-8"),
        file_name="Spor_Toto_AI_v19_0_Kullanim_Kilavuzu.html",
        mime="text/html",
        use_container_width=True
    )

    st.markdown("### 1) API anahtarınızı girin")
    api_key = st.text_input("🔑 API-Football Anahtarı:", type="password")
    if api_key:
        st.caption(f"📊 Kalan Günlük API Kotası: **{st.session_state.kalan_kota}**")

    st.markdown("---")
    st.markdown("### 2) Bütçenizi belirleyin")
    st.caption("Diğer bütün teknik ayarlar orijinal varsayılanlarıyla çalışır. İhtiyaç olursa aşağıdan açabilirsiniz.")
    uretim_modu = st.radio("Üretim modu", ["Bütçe kontrollü", "Matematiksel minimum (analiz)", "12–15 karşılaştırma (analiz)"], index=0,
        help="Minimum ve karşılaştırma yalnızca maliyet/kapsama analizi yapar; bütçe sınırı yoktur. Optimum yalnızca ispat varsa gösterilir.")
    kolon_fiyati = st.number_input("Kolon Birim Fiyatı (TL):", min_value=1.0, value=10.0, step=1.0)
    hedef_butce_tl = st.number_input("Üst bütçe / şablon kurma referansı (TL):", min_value=0.0,max_value=500000.0,value=2500.0,step=50.0)
    hedef_kolon_sayisi = int(hedef_butce_tl // kolon_fiyati)
    butce_kilidi_aktif = uretim_modu == "Bütçe kontrollü"
    max_kolon_limiti = hedef_kolon_sayisi if butce_kilidi_aktif else None
    limit_metni = f"En fazla {max_kolon_limiti:,} kolon" if max_kolon_limiti is not None else "Bütçesiz analiz (oynama talimatı değildir)"
    st.caption("Bütçe sınırı: " + limit_metni)

    with st.expander("⚙️ GELİŞMİŞ AYARLAR — isteğe bağlı", expanded=False):
        st.markdown("---")
        st.markdown("### 🎯 1. Senaryo Kapsama & Ekonomik Daraltma Motoru")
        garanti_secimi = st.selectbox(
            "Senaryo içi isabet / kapsama hedefi:",
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
            "🔒 Senaryo Kapsama Evreni:",
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
            st.caption("🛡️ **15/15 Şablon Kapsama Koruması:** Kesin Şablon modunda kapsama oranı otomatik olarak **%100 Tam Kapsama**'ya kilitlenmiştir.")
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

        arsiv_upload = st.file_uploader("İsteğe bağlı geçmiş maç arşivi (CSV)", type=["csv"], key="history14", help="date,home,away,hg,ag; yalnız tamamlanmış maçlar, takım adları API ile aynı olmalıdır. Her lig için ayrı model önerilir.")
        st.caption("Kolon fiyatı ve oynanma oranları otomatik doğrulanmaz. Arşiv yoksa piyasa/API; arşiv varsa DC/Elo deneysel model. Ağırlıklar kalibre edilmemiştir. Geçmiş tahmin testleri Gelişmiş Araçlar bölümündedir.")

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
                "🛡️ Favori Ağırlıklı (model senaryosu)",
                "🔍 Belirsizlik incelemesi (sıkı banko eşiği)"
            ]
        )

        # Halk tercihi, parasal EV veya gerçek maç olasılığı değildir.
        ev_katsayisi = 0.0  # v16 eski vekil (model == halk) puanlama devre dışı.
        st.caption("v17.3: Halk oranları, model olasılığından AYRIDIR. Tam ve zamanında CSV yoksa etkisi sıfırdır.")
        v173_opt_in = st.checkbox("🔍 Anti-Public deneysel puanlamayı etkinleştir (yalnız doğrulanmış biçimli halk CSV)",value=False,key='v173_enable',
            help="Halk tercihi kullanıcının sağladığı kaynak açıklamasıdır; kaynağın otantikliği doğrulanmaz. Gerçek kazanç veya tahmin gücü garantisi yoktur.")
        v173_weight = st.slider('Kalabalıktan ayrışma puanı ağırlığı (deneysel)',0.00,0.25,0.08,0.01,key='v173_weight',
            help='0 = yalnız model skoru. Yalnız tam 15 maçlık güncel kullanıcı CSV dosyasıyla aktiftir. Kalibre edilmemiştir.')
        risk_banko_p = st.slider("Banko inceleme eşiği (%)", 40, 90, 65, key="banko16_p")
        risk_gap = st.slider("Halk-model farkı uyarısı (puan)", 5, 30, 15, key="banko16_gap")
        risk_spread = st.slider("Piyasa sapması uyarısı (puan)", 1.0, 10.0, 2.5, 0.5, key="banko16_spread")

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
        st.markdown("### 🔬 3. Matematiksel Optimizasyon ve Yapısal Filtreler")
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
            value=True,
            help="Açık olduğunda, çok dar filtreler girdiğinizde sistem filtreyi sessizce devre dışı bırakıp kupon sayısını şişirmez; seçtiğiniz şartlara sadık kalır."
        )
        homojen_bulten = st.toggle("⚖️ Alt/Üst Bülten Homojenlik Filtresi", value=False)
        entropi_filtresi = st.toggle("🌀 Yapay/Simetrik Dizilim Elemesi", value=False)
        tuzak_koruma = st.toggle("🚨 Kırılgan Halk Tuzaklarını & Kararsızları Çifteye Al", value=True)

        if garanti_derecesi == 15:
            benzerlik_elemesi = 1
            st.caption("🔒 15 hedefinde Hamming alt sınırı 1; gerçek sonuç için garanti değildir.")
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


    with st.expander("💾 Oturumu kaydet / geri yükle", expanded=False):
        st.markdown("---")
        st.markdown("### 💾 4. Haftalık Bülten Yedeği")
        if st.session_state.analiz_verisi is not None:
            yedek_paket = {
                "versiyon": "17.3",
                "secilen_15_mac": st.session_state.secilen_15_mac,
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
                file_name=f"spor_toto_v17_3_oturum_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True
            )

        if st.session_state.get('v172_restore_notice'):
            st.warning(st.session_state.v172_restore_notice)
        yuklenen_oturum = st.file_uploader("📂 Kayıtlı Oturumu Yükle (.JSON):", type=["json"])
        if yuklenen_oturum is not None:
            if st.button("♻️ Oturumu Geri Yükle", use_container_width=True):
                try:
                    veri_json = json.loads(yuklenen_oturum.getvalue().decode("utf-8"))
                    ids=veri_json.get('secilen_mac_idleri',[]); av=veri_json.get('analiz_verisi') or []
                    if len(ids)!=15 or len(set(ids))!=15 or len(av)!=15 or set(ids)!={v['id'] for v in av}: raise ValueError('Bülten kimlikleri geçersiz.')
                    if veri_json.get('uretilen_kuponlar'):
                        arr=np.asarray(veri_json['uretilen_kuponlar'])
                        if arr.ndim!=2 or arr.shape[1]!=15 or not np.isin(arr,['1','X','2']).all(): raise ValueError('Geçersiz kolon kaydı')
                    st.session_state.uretilen_kuponlar=None
                    st.session_state.tablo_df=None;st.session_state.tablo_baz_df=None

                    st.session_state.secilen_mac_idleri = ids
                    # Eski JSON'larda secilen_15_mac bulunmuyordu: mac sirasini tahmin etmeyiz.
                    yeniden_secim=veri_json.get('secilen_15_mac')
                    if isinstance(yeniden_secim,list) and len(yeniden_secim)==15:
                        if [int(x['id']) for x in yeniden_secim]!=[int(x) for x in ids] or any(
                            not all(str(x.get(k,'')).strip() for k in ('ev','dep','tarih','saat')) for x in yeniden_secim):
                            raise ValueError('Yedek 15 mac ayrintilari eksik veya sirasi farkli.')
                        restored=[]
                        for m in yeniden_secim:
                            mm=dict(m)
                            mm['karsilasma']=f"{mm['ev']} - {mm['dep']}"
                            mm['label']=mm.get('label') or mm['karsilasma']
                            restored.append(mm)
                        st.session_state.secilen_15_mac=restored
                        st.session_state.mac_listesi=list(restored)
                        st.session_state.v172_restore_notice='15 maç sırası yedekten geri getirildi. Eski tahmin/kuponlar güncel sayılmaz.'
                    else:
                        in_session=st.session_state.get('secilen_15_mac',[])
                        if len(in_session)!=15 or [int(m['id']) for m in in_session]!=[int(x) for x in ids]:
                            st.session_state.secilen_15_mac=[]
                            st.session_state.mac_listesi=[]
                        st.session_state.v172_restore_notice='Eski JSON dosyasında 15 maçın tam seçimi bulunmuyor. Maçları resmî sırasıyla yeniden seçin.'
                    st.session_state.v171_api_proof=None
                    st.session_state.analiz_verisi = veri_json.get("analiz_verisi")
                    if veri_json.get("tablo_df"):
                        yuklenen_df = pd.DataFrame(veri_json["tablo_df"])
                        st.session_state.tablo_baz_df = yuklenen_df.copy()
                        st.session_state.tablo_df = yuklenen_df.copy()
                        st.session_state.tablo_versiyon += 1
                    if veri_json.get("uretilen_kuponlar"):
                        st.session_state.uretilen_kuponlar = None  # eski üretimi yeniden hesapla
                    st.session_state.son_uretim_ozeti = None # Önceki üretim yeni analize taşınamaz.
                    st.session_state.canli_sonuclar = veri_json.get("canli_sonuclar", ["⏳ Bekliyor"] * 15)
                    st.session_state.canli_skor_metni = veri_json.get("canli_skor_metni", ["-"] * 15)
                    st.session_state.yatirilan_paketler = veri_json.get("yatirilan_paketler", [])
                    st.session_state.son_param_imzasi = None
                    st.session_state.son_sol_menu_imzasi = None
                    st.toast("✅ Oturumun 15 maçı ve analiz bilgileri yüklendi; eski kuponlar yeniden üretilmeli!")
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


@st.cache_data(ttl=600, show_spinner=False)
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
            # API yanıtındaki TZ offsetini koruyarak Türkiye saatine dönüştür.
            api_tarihi = datetime.fromisoformat(item["fixture"]["date"].replace("Z", "+00:00"))
            if api_tarihi.tzinfo is None:
                api_tarihi = api_tarihi.replace(tzinfo=ZoneInfo("Europe/Istanbul"))
            saat = api_tarihi.astimezone(ZoneInfo("Europe/Istanbul")).strftime("%H:%M")
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
        # Hata durumunda boş sonucu 6 saat önbelleğe alma.
        raise RuntimeError(f"{tarih_str}: {exc}") from exc
    return gunun_maclari


def tarih_araligi_maclarini_getir(bas_tarih, bit_tarih, api_key, sadece_toto_ligleri=True):
    gun_sayisi = (bit_tarih - bas_tarih).days + 1
    if not 1 <= gun_sayisi <= 14:
        raise ValueError("Bülten taraması 1–14 gün aralığında olmalıdır (API kotası koruması).")
    tum_maclar, hatalar = [], []
    progress = st.progress(0, text="Bülten günleri taranıyor (Önbellek destekli)...")
    try:
        for i in range(gun_sayisi):
            g_str = (bas_tarih + timedelta(days=i)).strftime("%Y-%m-%d")
            try:
                tum_maclar.extend(gunluk_bulten_cek_cacheli(g_str, api_key, sadece_toto_ligleri))
            except (requests.RequestException, RuntimeError, ValueError) as exc:
                hatalar.append(str(exc))
            progress.progress((i + 1) / gun_sayisi)
    finally:
        progress.empty()
    if hatalar:
        st.warning(f"{len(hatalar)} günün verisi alınamadı. Eksik bülten olabilir: " + " | ".join(hatalar[:3]))
    # Aynı fikstür birden fazla kaynaktan/kayıttan gelirse ID bazında tekilleştir.
    tekil = {int(m["id"]): m for m in tum_maclar}
    sirali = list(tekil.values())
    sirali.sort(key=lambda x: (0 if x["lig_id"] in [203, 204] else 1, x["tarih"], x["saat"], x["id"]))
    return sirali


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


@st.cache_data(ttl=900, show_spinner=False)
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
    # Bu fonksiyon cache icinde calistigi icin gercek FETCH zamani cache ile korunur.
    fetched_at = datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    return market,api,spread,len(odds_list_1),hatalar,fetched_at


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
        market,api,piyasa_std,bureau,hatalar,remote_fetched_at = tek_mac_analiz_cek(f_id, api_key, lig_id=lig_id)
        model=None
        if history is not None:
            try:
                cutoff=min(pd.to_datetime(mac['tarih'],utc=True),pd.Timestamp.now(tz='UTC').normalize())
                model=_dc_elo_tahmin(history,mac['ev'],mac['dep'],cutoff)
            except Exception as exc: hatalar.append(f"Arşiv modeli: {exc}")
        p,kaynak=_model_birlestir(market,api,model,bureau,piyasa_std)
        g1,gx,g2=olasilik_yumusat(*p)
        h1, hx, h2 = g1, gx, g2
        sonuclar.append({
            "bulten_no": i + 1,
            "id": f_id,
            "mac": mac["karsilasma"],
            "lig": mac.get("lig", "-"),
            "tarih": mac.get("tarih", "-"),
            "saat": mac.get("saat", "-"),
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
            "source_fetched_at":remote_fetched_at,
            "source_provenance":"API_REQUEST_AT" if (market is not None or api is not None) else "NO_API_PREDICTION",
            "snapshot_utc":datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
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


def mac_secimi_senkronize_v161():
    """Havuz güncellendiğinde mevcut 15'li listede yalnızca geçerli tekil ID'ler kalsın."""
    lookup = {int(m["id"]): m for m in st.session_state.mac_listesi}
    kullanilan = set()
    temiz = []
    for eski in st.session_state.secilen_15_mac:
        mid = int(eski["id"])
        if mid in lookup and mid not in kullanilan and len(temiz) < 15:
            temiz.append(lookup[mid]); kullanilan.add(mid)
    st.session_state.secilen_15_mac = temiz


def mac_ekle_v161(fixture_id):
    mac_secimi_senkronize_v161()
    fid = int(fixture_id)
    ids = {int(m["id"]) for m in st.session_state.secilen_15_mac}
    if fid in ids or len(ids) >= 15:
        return False
    lookup = {int(m["id"]): m for m in st.session_state.mac_listesi}
    if fid not in lookup:
        return False
    st.session_state.secilen_15_mac.append(lookup[fid])
    st.session_state["bulten_onay14"] = False
    return True


def mac_cikar_v161(fixture_id):
    fid = int(fixture_id)
    st.session_state.secilen_15_mac = [m for m in st.session_state.secilen_15_mac if int(m["id"]) != fid]
    st.session_state["bulten_onay14"] = False


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
                        skor_metinleri[idx] = f"⚠️ Özel durum ({durum}) — resmî Spor Toto hükmünü kontrol edin"
                        # Fikstür API statüsü, Spor Toto'nun resmî kura/sonuç kararı değildir.
                        yeni_sonuclar[idx] = "⏳ Bekliyor"
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
    elif "Belirsizlik" in strateji:
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
    elif "Belirsizlik" in strateji:
        fav_aralik = (max(zorunlu_fav, int(round(exp_fav)) - 4), min(acik_fav, max(zorunlu_fav + 2, int(round(exp_fav)) + 2)))
        plase_aralik = (max(zorunlu_plase, int(round(exp_plase)) - 2), min(acik_plase, int(round(exp_plase)) + 3))
        surpriz_aralik = (max(zorunlu_surp, int(round(exp_surp)) - 2), min(acik_surp, max(zorunlu_surp + 3, int(math.ceil(exp_surp)) + 3)))
        z_zarf = (-2.35, 1.85)
    else:
        fav_aralik = (max(zorunlu_fav, int(round(exp_fav)) - 3), min(acik_fav, int(round(exp_fav)) + 3))
        plase_aralik = (max(zorunlu_plase, int(round(exp_plase)) - 3), min(acik_plase, int(round(exp_plase)) + 3))
        surpriz_aralik = (zorunlu_surp, min(acik_surp, max(zorunlu_surp + 2, int(math.ceil(exp_surp)) + 2)))
        z_zarf = (-1.95, 2.25)

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


def halk_verisi_oku16(file, expected_ids):
    """User supplied marginal percentages. No inference of provenance."""
    d = pd.read_csv(file, dtype={"fixture_id":"string"})
    required = {"fixture_id", "h1", "hx", "h2", "source", "snapshot"}
    if not required <= set(d.columns):
        raise ValueError("Gerekli sütunlar: fixture_id,h1,hx,h2,source,snapshot")
    if d.fixture_id.isna().any() or d.fixture_id.duplicated().any():
        raise ValueError("Boş veya mükerrer maç ID'si.")
    if any(not str(x).isdigit() for x in d.fixture_id):
        raise ValueError("Maç ID sayısal olmalı.")
    ids = [int(x) for x in d.fixture_id]
    if len(ids)!=len(set(ids)) or not set(ids) <= set(map(int, expected_ids)):
        raise ValueError("Dosya bu bültene ait olmayan veya tekrarlı maç içeriyor.")
    q = d[["h1","hx","h2"]].apply(pd.to_numeric, errors="raise").to_numpy(float)
    if not np.isfinite(q).all() or (q<0).any() or (q>100).any() or (abs(q.sum(axis=1)-100)>0.2).any():
        raise ValueError("Halk oranları 0–100 olmalı ve her satır yaklaşık 100 etmelidir.")
    if d.source.isna().any() or d.source.astype(str).str.strip().eq("").any():
        raise ValueError("Kaynak bilgisi boş olamaz.")
    if not d.snapshot.astype(str).str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$",regex=True).all():
        raise ValueError("Snapshot ISO 8601 saat dilimi içermeli.")
    times=pd.to_datetime(d.snapshot,utc=True,errors="raise")
    if (times>pd.Timestamp.now(tz="UTC")).any():
        raise ValueError("Gelecek tarihli snapshot olamaz.")
    return {i:{"q":(row/row.sum()).tolist(),"source":str(src),"snapshot":str(t)} for i,row,src,t in zip(ids,q,d.source,times)}


def banko_risk16(v, selected, public=None, p_threshold=65, gap_threshold=15, spread_threshold=2.5):
    keys=("1","X","2")
    p=np.asarray([v[k] for k in keys],float)
    if not np.isfinite(p).all() or (p<0).any() or p.sum()<=0:
        raise ValueError("Geçersiz model olasılığı")
    p=p/p.sum(); order=np.argsort(-p,kind="stable"); fav=int(order[0]); second=int(order[1])
    entropy=float(-np.sum(p*np.log(np.maximum(p,1e-15)))/np.log(3))
    ix=keys.index(selected[0]) if len(selected)==1 else fav
    source=str(v.get("kaynak", "")); missing=not source or "VERİ YOK" in source
    spread=float(v.get("piyasa_std",0) or 0); bureau=int(v.get("buro_sayisi",0) or 0)
    data_limited=missing or bureau<2
    q=np.asarray(public["q"],float) if public is not None else None
    gap=None if q is None else float((q[ix]-p[ix])*100)
    reasons=[]
    if data_limited: reasons.append("Sınırlı kaynak")
    if spread>=spread_threshold: reasons.append("Piyasa sapması")
    if p[ix]*100<p_threshold: reasons.append("Olasılık eşiği altında")
    if gap is not None and gap>=gap_threshold: reasons.append("Halk-model farkı yüksek")
    if ix!=fav: reasons.append("Model favorisi dışında")
    if entropy>=.9: reasons.append("Yüksek belirsizlik")
    return {"favori":keys[fav],"incelenen":keys[ix],"p":float(p[ix]),"entropy":entropy,
            "margin":float((p[fav]-p[second])*100),"gap":gap,"reasons":reasons,
            "halk":None if q is None else float(q[ix]),"covered":float(sum(p[keys.index(k)] for k in selected)),
            "p_all":p}


def banko_hata_dagilimi16(probabilities):
    # Independent Bernoulli error count, descriptive scenario analysis only.
    out=np.array([1.0])
    for p in probabilities:
        if not np.isfinite(p) or not 0<=p<=1: raise ValueError("Geçersiz olasılık")
        out=np.convolve(out,[p,1-p])
    return out


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

        kirilgan_tuzak_mi = False  # halk oranı arşivi şablonu otomatik değiştirmez
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
            if en_b_oran >= max(limitler["banko_siniri"], risk_banko_p) and not banko_risk16(v, [en_b_secim], p_threshold=risk_banko_p, gap_threshold=risk_gap, spread_threshold=risk_spread)["reasons"]:
                secim = [en_b_secim]
                g1, g2 = False, False
            elif (en_b_oran >= limitler["cifte_siniri"] or sira_idx < 11) and not (tuzak_aktif and kirilgan_tuzak_mi and sira_idx >= 11):
                secim = cifte_secim
                g1 = True if en_b_oran >= 45 else False
                g2 = True if en_b_oran < 45 else False
            else:
                secim = ["1", "X", "2"]
                g1, g2 = False, True

        # v17: 15 banko, ekonomik ve sendika dâhil BÜTÜN hazır şablonlarda veto.
        if len(secim)==1:
            risk=banko_risk16(v,secim,p_threshold=risk_banko_p,gap_threshold=risk_gap,spread_threshold=risk_spread)
            if risk['reasons']:
                secim=akilli_cifte_sec(v)  # riskli banko iki işaretle korunur; kaynak yoksa analiz uyarısı vardır.
                g1, g2 = True, False
        teshis = "; ".join(banko_risk16(v,[en_b_secim],p_threshold=risk_banko_p,gap_threshold=risk_gap,spread_threshold=risk_spread)["reasons"]) or "Eşik uyarısı yok"

        satirlar.append({
            "Sıra": v["bulten_no"],
            "ID": v["id"],
            "Lig": v.get("lig", "-"),
            "Karşılaşma": v["mac"],
            "1 (%)": v["1"],
            "X (%)": v["X"],
            "2 (%)": v["2"],
            "Halk (%)": None,
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
    kati_filtre=False,
    public_prob=None,
    crowd_strength=0.0
):
    harita = {"1": 0, "X": 1, "2": 2}
    ters = np.array(["1", "X", "2"])
    grids = np.meshgrid(*[[harita[s] for s in m] for m in sablon], indexing="ij")
    ham_matris = np.stack(grids, axis=-1).reshape(-1, 15).astype(np.int8)
    matris = ham_matris
    esnetilenler = []

    min_kabul_edilebilir = 1 if kati_filtre else max(1, min(8, len(ham_matris) // 20))

    oran_mat = np.array([[v["1"], v["X"], v["2"]] for v in mac_verileri], dtype=np.float32)
    # Model olasiliklarini halk tercihi sanmak yasak: bos veri = yalniz model skoru.

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
    puanlar = np.sum(secilen_oranlar, axis=1)
    kompozit_skor = v173_skor_olustur(matris, oran_mat, public_prob, crowd_strength)

    ham_oranlar = oran_mat[np.arange(15), ham_matris]
    ham_puanlar = np.sum(ham_oranlar, axis=1)
    ham_kompozit = v173_skor_olustur(ham_matris, oran_mat, public_prob, crowd_strength)
    ham_idx = np.argsort(ham_kompozit,kind='stable')[::-1]

    hib_oranlar = oran_mat[np.arange(15), hibrit_matris]
    hib_puanlar = np.sum(hib_oranlar, axis=1)
    hib_kompozit = v173_skor_olustur(hibrit_matris, oran_mat, public_prob, crowd_strength)
    hib_idx = np.argsort(hib_kompozit,kind='stable')[::-1]

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
# B SİSTEMİNDEN ENTEGRE EDİLEN OTOMATİK KUPON YATIRMA MERKEZİ FONKSİYONLARI
# ==============================================================================
def guvenli_tarayici_asistani_uret(*args, **kwargs):
    """v17 fail-closed: arbitrary third-party DOM automation is not trusted."""
    raise RuntimeError("Otomatik işaretleme kapalı: resmî bülten/site DOM doğrulaması yok.")


def tum_kolonlar_txt153(kolonlar, ozet, guncel_imza, mac_ids, max_k=None, ayirici=""):
    """Güncel oturumun bütün nihai kolonlarını, sıra değiştirmeden metne çevirir."""
    if not isinstance(ozet, dict) or not guncel_imza or ozet.get("imza") != guncel_imza:
        raise ValueError("Güncel üretim yok. Önce 1. sekmede KAPSAMA HESAPLA düğmesine basın.")
    ids = [str(x) for x in ozet.get("mac_ids", [])]
    if len(ids) != 15 or len(set(ids)) != 15 or ids != [str(x) for x in mac_ids]:
        raise ValueError("15 maçın bülten sırası uyuşmuyor. Yeniden hesaplayın.")
    a = np.asarray(kolonlar)
    if a.ndim != 2 or a.shape[1] != 15 or a.shape[0] == 0:
        raise ValueError("İndirilebilecek 15 maçlık kolon bulunamadı.")
    if max_k is not None and len(a) > max_k:
        raise ValueError("Güncel bütçe sınırı aşıldı. Yeniden hesaplayın.")
    if not np.isin(a, ("1", "X", "2")).all():
        raise ValueError("Geçersiz kolon işareti bulundu. Yeniden hesaplayın.")
    if ayirici not in ("", " "):
        raise ValueError("Geçersiz TXT biçimi.")
    rows = [ayirici.join(row) for row in a.tolist()]
    if len(set(rows)) != len(rows):
        raise ValueError("Mükerrer kolon bulundu. Hiçbir kolonu sessizce silmeden işlem durduruldu.")
    return ("\n".join(rows) + "\n").encode("utf-8"), len(rows)


# ==============================================================================
# V17: BAĞIMSIZ DOĞRULANABİLİR ŞABLON, VERİ, BÜTÇE VE DOSYA DENETİMİ
# ==============================================================================
V17_SAAT = ZoneInfo("Europe/Istanbul")
V17_SONUC = ("1", "X", "2")


def v17_utc(tarih):
    t = pd.Timestamp(tarih)
    if pd.isna(t) or t.tzinfo is None:
        raise ValueError("ISO 8601 tarih/saat dilimi (örn. +03:00 veya Z) gerekli.")
    return t.tz_convert("UTC")


def v17_resmi_bulten_denetle(csv_bayt, secilenler, simdi=None):
    """Yalnız KULLANICI CSV'sinin API seçimiyle tutarlılığını ölçer; kaynağı doğrulayamaz."""
    df = pd.read_csv(io.BytesIO(csv_bayt), dtype={"fixture_id": "string", "bulletin_id":"string"})
    required = {"bulletin_id", "order", "fixture_id", "home", "away", "starts_at", "closes_at", "source_url", "obtained_at"}
    if not required <= set(df.columns):
        raise ValueError("Eksik CSV sütunu: " + ", ".join(sorted(required-set(df.columns))))
    if len(df) != 15 or len(secilenler) != 15:
        raise ValueError("CSV ve seçilen bülten tam 15 satır olmalıdır.")
    if df[list(required)].isna().any().any():
        raise ValueError("CSV'de boş alan var.")
    if len(set(df.bulletin_id.astype(str).str.strip())) != 1:
        raise ValueError("Bülten kodları tutarsız.")
    order = pd.to_numeric(df['order'], errors='raise')
    if order.tolist() != list(range(1,16)):
        raise ValueError("CSV satırları 1..15 sırasıyla yazılmalıdır.")
    if not df.fixture_id.str.fullmatch(r"[0-9]+").all():
        raise ValueError("fixture_id sayısal olmalıdır.")
    ids=[int(x) for x in df.fixture_id.tolist()]
    if len(set(ids)) != 15 or ids != [int(x['id']) for x in secilenler]:
        raise ValueError("CSV ile seçilen 15 maçın ID veya sırası farklı.")
    now = v17_utc(simdi) if simdi is not None else pd.Timestamp.now(tz='UTC')
    closes = [v17_utc(x) for x in df.closes_at]
    obtained = [v17_utc(x) for x in df.obtained_at]
    if len(set(closes))!=1: raise ValueError("Bülten kapanış saatleri farklı.")
    if any(t>now for t in obtained): raise ValueError("Gelecek tarihli alım zamanı olamaz.")
    if any((now-t)>pd.Timedelta(hours=24) for t in obtained):
        raise ValueError("Bülten dosyası alım zamanı 24 saatten eski; güncelleyiniz.")
    for i,(row,m) in enumerate(zip(df.to_dict('records'),secilenler),1):
        if metin_temizle(str(row['home'])) != metin_temizle(m['ev']) or metin_temizle(str(row['away'])) != metin_temizle(m['dep']):
            raise ValueError(f"Maç {i}: ev/deplasman takım adı uyuşmuyor.")
        # API selected list contains the local fixture date/time; compare minutes, do not infer timezone.
        kick=v17_utc(row['starts_at']).tz_convert(V17_SAAT).strftime('%Y-%m-%d %H:%M')
        expected=f"{m['tarih']} {m['saat']}"
        if kick != expected:
            raise ValueError(f"Maç {i}: başlama saati farklı: CSV {kick} / API {expected}")
        if closes[0] > v17_utc(row['starts_at']):
            raise ValueError(f"Maç {i}: bülten kapanışı maçtan sonra olamaz.")
        if not str(row['source_url']).strip().startswith(('https://','http://')):
            raise ValueError(f"Maç {i}: kaynak URL eksik/geçersiz.")
    return {"bulletin_id":str(df.bulletin_id.iloc[0]).strip(),
            "closes_at":closes[0].isoformat(),
            "closed":bool(now >= closes[0]),
            "rows":len(df),
            "file_sha256":hashlib.sha256(csv_bayt).hexdigest(),
            "source_url":str(df.source_url.iloc[0]),
            "verification":"USER_SUPPLIED_CONSISTENCY_ONLY"}


def v17_tahmin_kalitesi(veriler, simdi=None):
    """Kaynaksız, bozuk veya bir gün önce hesaplanmış tahmin canlı transfer için yasak."""
    issues=[]
    if not isinstance(veriler,list) or len(veriler)!=15:
        return ["Tam 15 maçlık tahmin yok."]
    if len({str(v.get('id')) for v in veriler})!=15:
        issues.append("Mükerrer maç kimliği.")
    now=v17_utc(simdi) if simdi is not None else pd.Timestamp.now(tz='UTC')
    for i,v in enumerate(veriler,1):
        src=str(v.get('kaynak',''))
        if not src or 'VERİ YOK' in src or 'varsayım' in src.lower():
            issues.append(f"{i}. maç: güvenilir tahmin kaynağı yok.")
        try:
            p=np.array([float(v[k]) for k in V17_SONUC],float)
            if not np.isfinite(p).all() or (p<=0).any() or abs(sum(p)-100)>0.5:
                issues.append(f"{i}. maç: 1/X/2 yüzde dağılımı geçersiz.")
            snap=v17_utc(v['snapshot_utc'])
            if snap>now or now-snap>pd.Timedelta(minutes=30):
                issues.append(f"{i}. maç: hesaplama snapshot'ı 30 dakika dışında.")
        except (KeyError,ValueError,TypeError):
            issues.append(f"{i}. maç: zaman/olasılık alanları eksik.")
    return issues


def v17_paket_uret(kolonlar, ozet, param_imza, mac_ids, maclar, birim_fiyat, butce, strict=True):
    """Tam 15 sütun, tekil, güncel, bütçe kontrollü çıktı + SHA256 manifest."""
    if not (Decimal(str(birim_fiyat))>0 and Decimal(str(butce))>=0):
        raise ValueError('Fiyat/bütçe geçersiz.')
    raw, count = tum_kolonlar_txt153(kolonlar, ozet, param_imza, mac_ids,
                                    max_k=int(Decimal(str(butce))//Decimal(str(birim_fiyat))), ayirici='')
    if len(maclar)!=15 or [str(x.get('id')) for x in maclar] != [str(x) for x in mac_ids]:
        raise ValueError('Paket maç sırası üretimle farklı.')
    if strict and (ozet.get('esnetilenler') or not ozet.get('optimizasyon',{}).get('hedef_tam',False)):
        raise ValueError('Filtre esnetilmiş veya hedef kapsama sağlanmamış: kritik dışa aktarım durduruldu.')
    cost=Decimal(count)*Decimal(str(birim_fiyat))
    if cost>Decimal(str(butce)):
        raise ValueError('Bütçe aşıldı.')
    rows=[{'order':i+1,'fixture_id':str(m['id']),'match':str(m['mac']), 'date':m.get('tarih'), 'time':m.get('saat')} for i,m in enumerate(maclar)]
    manifest={"version":"19.0 ULTIMATE FINAL ANALYSIS ONLY", "mode":"ANALYSIS_ONLY_NOT_A_BET",
              "bulletin_verification":"NOT_INDEPENDENTLY_VERIFIED",
              "columns":count,"rows_per_column":15,"cost_assumption_tl":str(cost),
              "unit_price_assumption_tl":str(birim_fiyat),"budget_tl":str(butce),
              "model_scope":"conditional scenario coverage, not real-result guarantee",
              "coverage_target_met":bool(ozet.get('optimizasyon',{}).get('hedef_tam',False)),
              "coverage_selected_universe_percent":ozet.get('optimizasyon',{}).get('kapsama_adet'),
              "coverage_raw_universe_percent":ozet.get('denetim_ham',{}).get({15:'tam_15',14:'en_az_14',13:'en_az_13',12:'en_az_12'}.get(ozet.get('garanti_derecesi',0),'')),
              "target_correct_matches":ozet.get('garanti_derecesi'),
              "parameter_hash":str(param_imza),"matches":rows,
              "crowd_proxy_weight":ozet.get('v173_crowd_weight',0.0),
              "crowd_csv_sha256":ozet.get('v173_public_sha256'),
              "crowd_proxy_not_payout_forecast":True,
              "txt_sha256":hashlib.sha256(raw).hexdigest()}
    # v18.1: Bağımsız denetim için orijinal ham şablon ve raporlanan dört değer pakete bağlanır.
    manifest['version']='19.0 ULTIMATE FINAL ANALYSIS ONLY'
    if ozet.get('g_sablon') is not None:
        original_template=v181_template_canonical(ozet['g_sablon'])
        original_size=math.prod(map(len,original_template))
        if int(ozet.get('ham_adet',-1))!=original_size:
            raise ValueError('Ham şablon sayısı manifest hazırlığında tutarsız.')
        manifest['raw_template']=original_template
        manifest['raw_template_sha256']=v181_template_hash(original_template)
        manifest['raw_universe_count']=original_size
        manifest['reported_raw_coverage']=ozet.get('denetim_ham')
        manifest['independent_audit_required']=True
    else:
        # Eski test/yardımcı paketlerinde şablon yoksa işlev geriye uyumlu kalır;
        # A10/B04 kabul kontrolleri ve bağımsız denetçi, tam şablonu OLMADAN PASS vermez.
        manifest['independent_audit_required']=False
    payload=json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2).encode('utf-8')
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('KOLONLAR_ANALIZ.txt',raw)
        z.writestr('BULTEN_MANIFEST.json',payload)
    return raw,payload,out.getvalue(),manifest


def v17_paket_kontrol(txt,manifest_bytes):
    m=json.loads(manifest_bytes)
    rows=txt.decode('utf-8-sig').splitlines()
    if len(rows)!=m['columns'] or any(len(s)!=15 or any(k not in '1X2' for k in s) for s in rows):
        raise ValueError('Paket kolon biçimi/sayısı bozuk.')
    if len(set(rows))!=len(rows):raise ValueError('Paket mükerrer kolon içeriyor.')
    if hashlib.sha256(txt).hexdigest()!=m['txt_sha256']:
        raise ValueError('TXT SHA-256 uyuşmuyor.')
    if len(m['matches'])!=15 or [x['order'] for x in m['matches']]!=list(range(1,16)):
        raise ValueError('Manifest maç sırası hatalı.')
    return True




# ==============================================================================
# v17.1: EŞLEŞTİRME, İZLENEBİLİR KAYNAK, API FİKSTÜR YENİDEN KONTROLÜ
# Resmî kaynağın kriptografik imzası/otantikliği BU İŞLEVLERLE kanıtlanmaz.
# ==============================================================================
def v171_mac_imzasi(maclar):
    if not isinstance(maclar, list) or len(maclar) != 15:
        raise ValueError('İmza için tam 15 maç gerekli.')
    items=[]
    for m in maclar:
        items.append([str(m['id']),str(m['ev']),str(m['dep']),str(m['tarih']),str(m['saat']),str(m.get('lig_id',''))])
    if len({x[0] for x in items})!=15: raise ValueError('Mükerrer ID.')
    payload=json.dumps(items,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def v171_takim_kimlik(ad):
    """Katı, isim koruyan karşılaştırma (spor, şehir ve isim kökleri atılmaz)."""
    t=unicodedata.normalize('NFKD',str(ad).translate(str.maketrans('çğıöşüÇĞİÖŞÜ','cgiosuCGIOSU'))).encode('ascii','ignore').decode('ascii').lower()
    t=re.sub(r'[^a-z0-9]+',' ',t).strip()
    t=re.sub(r'\b(?:a s|a s s|fk|fc|sk)\b',' ',t)
    return ' '.join(t.split())


def v171_liste_metin_denetle(metin,maclar):
    """Kullanıcının resmî sayfadan bağımsız kopyaladığı 1..15 satırını sırasıyla karşılaştırır."""
    if not isinstance(metin,str) or len(metin)>12000:
        raise ValueError('Liste metni boş veya aşırı uzun.')
    rows=[r.strip() for r in metin.splitlines() if r.strip()]
    if len(rows)!=15 or len(maclar)!=15:
        raise ValueError('Bağımsız maç listesi tam 15 satır olmalıdır.')
    names=[]
    for i,(line,m) in enumerate(zip(rows,maclar),1):
        a=re.match(r'^\s*(\d{1,2})\s*[.)\-:]\s*(.+)$',line)
        if not a or int(a.group(1))!=i:
            raise ValueError(f'Satır {i}: numaralar 1..15 sıralı olmalıdır.')
        match=re.split(r'\s+(?:-|–|—|vs\.?|VS\.?)\s+',a.group(2),maxsplit=1,flags=re.IGNORECASE)
        if len(match)!=2 or not match[0].strip() or not match[1].strip():
            raise ValueError(f'Satır {i}: Ev Takımı - Deplasman Takımı bekleniyor.')
        home,away=[x.strip() for x in match]
        if v171_takim_kimlik(home)!=v171_takim_kimlik(m['ev']) or v171_takim_kimlik(away)!=v171_takim_kimlik(m['dep']):
            raise ValueError(f'Satır {i}: takım isimleri veya ev/deplasman sırası uyuşmuyor ({home} - {away}).')
        names.append([home,away])
    return {'count':15,'match_signature':v171_mac_imzasi(maclar),
            'text_sha256':hashlib.sha256(metin.encode('utf-8')).hexdigest(),
            'status':'USER_PASTED_LIST_MATCHES_API_NOT_SOURCE_AUTHENTICATED'}


def v171_url_resmi_aday(url):
    """URL, yalnızca resmî web alanı biçiminde mi? İçeriği doğrulamaz."""
    x=urllib.parse.urlsplit(str(url).strip())
    return bool(x.scheme=='https' and x.hostname in ('sportoto.gov.tr','www.sportoto.gov.tr')
                and not x.username and not x.password and (x.port in (None,443)))


def v171_bulten_csv_denetle(csv_bytes,maclar,simdi=None):
    """Güvenilmez kullanıcı CSV'sinin 15/15 tutarlılık ve kaynak ADRESİ sınaması."""
    if not isinstance(csv_bytes,(bytes,bytearray)) or not 50<len(csv_bytes)<200_000:
        raise ValueError('CSV boyutu geçersiz.')
    checked=v17_resmi_bulten_denetle(csv_bytes,maclar,simdi=simdi)
    df=pd.read_csv(io.BytesIO(csv_bytes),dtype=str)
    urls=[str(v).strip() for v in df.source_url]
    if len(set(urls))!=1 or not v171_url_resmi_aday(urls[0]):
        raise ValueError('Kaynak URL her satırda aynı ve https://www.sportoto.gov.tr/... olmalı.')
    closes=v17_utc(checked['closes_at'])
    now=v17_utc(simdi) if simdi is not None else pd.Timestamp.now(tz='UTC')
    if closes-now<=pd.Timedelta(minutes=5):
        raise ValueError('Kapanışa 5 dakika veya daha az kaldı, güvenlik kilidi etkin.')
    obtained=[v17_utc(x) for x in df.obtained_at]
    if max(now-v for v in obtained)>pd.Timedelta(hours=2):
        raise ValueError('Bağımsız kaynak alım beyanı 2 saatten eski.')
    checked['match_signature']=v171_mac_imzasi(maclar)
    checked['verification']='USER_CSV_OFFICIAL_URL_CLAIM_ONLY_NOT_AUTHENTICATED'
    return checked


def v171_api_fikstur_tekrar_kontrol(api_response,maclar,simdi=None):
    """API'den tekrar alınan fikstürü yalnız güncel kaynak tutarlılığı için denetler."""
    now=v17_utc(simdi) if simdi is not None else pd.Timestamp.now(tz='UTC')
    entries=api_response.get('response') if isinstance(api_response,dict) else None
    if not isinstance(entries,list) or len(entries)!=15:
        raise ValueError('API güncel fikstür yanıtında tam 15 karşılaşma yok.')
    by_id={}
    for entry in entries:
        fid=int(entry['fixture']['id'])
        if fid in by_id: raise ValueError('API yinelenen ID döndü.')
        by_id[fid]=entry
    if set(by_id)!={int(m['id']) for m in maclar}:
        raise ValueError('API 15 maç kimliğinde farklılık var.')
    for i,m in enumerate(maclar,1):
        obj=by_id[int(m['id'])]
        name_home=obj['teams']['home']['name'];name_away=obj['teams']['away']['name']
        if v171_takim_kimlik(name_home)!=v171_takim_kimlik(m['ev']) or v171_takim_kimlik(name_away)!=v171_takim_kimlik(m['dep']):
            raise ValueError(f'API güncellemesi: {i}. maçta takım adı/ev sahibi değişmiş.')
        kickoff=v17_utc(obj['fixture']['date'])
        if kickoff.tz_convert(V17_SAAT).strftime('%Y-%m-%d %H:%M') != f"{m['tarih']} {m['saat']}":
            raise ValueError(f'API güncellemesi: {i}. maçta başlama saati değişmiş.')
        if kickoff<=now: raise ValueError(f'{i}. maç başlamış veya başlama zamanı geçmiş.')
        if obj['fixture']['status']['short']!='NS':
            raise ValueError(f'{i}. maç: API durumu NS değil; otomatik güvenilir kabul edilmez.')
        if m.get('lig_id') is not None and int(obj['league']['id'])!=int(m['lig_id']):
            raise ValueError(f'{i}. maçın lig kimliği değişmiş.')
    audit={'count':15,'match_signature':v171_mac_imzasi(maclar),
           'checked_at':now.isoformat(),
           'api_response_sha256':hashlib.sha256(json.dumps(entries,ensure_ascii=False,sort_keys=True,default=str).encode('utf-8')).hexdigest(),
           'status':'API_FIXTURE_MATCHES_SELECTION_NOT_OFFICIAL_BULLETIN'}
    return audit


def v171_bagimsiz_kontrol_kapisi(csv_bytes, liste_metin, maclar, api_kontrol, tahminler, simdi=None):
    """Ön-oyun analiz paketi kapısı. Gerçek oyun yetkisi ASLA vermez."""
    now=v17_utc(simdi) if simdi is not None else pd.Timestamp.now(tz='UTC')
    errors=[]; csvinfo=None; listinfo=None; signature=None
    try:
        signature=v171_mac_imzasi(maclar)
    except (KeyError,ValueError,TypeError) as e: errors.append(str(e))
    try:
        csvinfo=v171_bulten_csv_denetle(csv_bytes,maclar,simdi=now)
    except (KeyError,ValueError,TypeError,AttributeError) as e: errors.append('CSV: '+str(e))
    try:
        listinfo=v171_liste_metin_denetle(liste_metin,maclar)
    except (KeyError,ValueError,TypeError) as e: errors.append('Bağımsız liste: '+str(e))
    if not isinstance(api_kontrol,dict):errors.append('API tekrar kontrolü yok.')
    else:
        try:
            at=v17_utc(api_kontrol['checked_at'])
            if at>now or now-at>pd.Timedelta(minutes=10) or signature!=api_kontrol['match_signature'] or api_kontrol.get('count')!=15:
                errors.append('API tekrar kontrolü bayat, eksik veya farklı bültene ait.')
        except (KeyError,ValueError,TypeError):errors.append('API kontrol zaman bilgisi bozuk.')
    if not isinstance(tahminler,list) or len(tahminler)!=15:
        errors.append('Tam 15 analiz tahmini yok.')
    else:
        if [str(m.get('id')) for m in maclar]!=[str(v.get('id')) for v in tahminler]:
            errors.append('Tahmin maç sırası / kimliği uyuşmuyor.')
        errors.extend(v17_tahmin_kalitesi(tahminler,simdi=now))
    return {'ok':not errors, 'issues':errors, 'csv':csvinfo,'manual_list':listinfo,
            'api':api_kontrol if isinstance(api_kontrol,dict) else None,
            'match_signature':signature,'evaluated_at':now.isoformat(),
            'expected_export_rows':[{'order':i+1,'fixture_id':str(m['id']),
                'match':f"{m['ev']} - {m['dep']}",'date':m['tarih'],'time':m['saat']}
                for i,m in enumerate(maclar)] if signature else [],
            'status':'INDEPENDENT_INPUTS_CONSISTENT_NOT_OFFICIALLY_AUTHENTICATED' if not errors else 'BLOCKED'}


def v171_toto_0_txt(raw):
    """Spor Toto'nun resmî sonuç alfabesi 1/0/2'dir; iç sistem 1/X/2 kullanır."""
    rows=raw.decode('utf-8').splitlines()
    if not rows or any(len(r)!=15 or set(r)-set('1X2') for r in rows):
        raise ValueError('İç TXT biçimi geçersiz.')
    return ('\n'.join(r.replace('X','0') for r in rows)+'\n').encode('utf-8')


def v171_denetimli_analiz_zip(raw,manifest_bytes,kapisi):
    """İki alfabe + giriş kanıtları. Bu bir resmî işlem dosyası değildir."""
    if not isinstance(kapisi,dict) or not kapisi.get('ok'):
        raise ValueError('Denetimli paket için 15/15 kontrol kapısı geçilmeli.')
    v17_paket_kontrol(raw,manifest_bytes)
    manifest=json.loads(manifest_bytes)
    ids=[str(x['fixture_id']) for x in manifest['matches']]
    if len(ids)!=15: raise ValueError('Manifest maç listesi eksik.')
    if manifest['matches'] != kapisi.get('expected_export_rows'):
        raise ValueError('Üretilen kolon paketindeki maç adları/saatleri resmî liste kontrollerinden farklı.')
    if not all(isinstance(kapisi.get(k),dict) and kapisi[k].get('match_signature')==kapisi.get('match_signature')
               for k in ('csv','manual_list','api')):
        raise ValueError('Çapraz kontrol kanıtları aynı bültene ait değil.')
    evidence=kapisi.copy()
    evidence['note']='Girilen kaynak verilerinin tutarlılığı denetlendi; resmî kaynak otantikliği bağımsız kanıtlanmadı.'
    zero=v171_toto_0_txt(raw)
    evidence['txt_1X2_sha256']=hashlib.sha256(raw).hexdigest()
    evidence['txt_102_sha256']=hashlib.sha256(zero).hexdigest()
    bundle=io.BytesIO()
    with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED) as zipout:
        zipout.writestr('KOLONLAR_ANALIZ_1X2.txt',raw)
        zipout.writestr('KOLONLAR_SPORTOTO_102_INCELEME.txt',zero)
        zipout.writestr('BULTEN_MANIFEST.json',manifest_bytes)
        zipout.writestr('KONTROL_KANITLARI.json',json.dumps(evidence,ensure_ascii=False,indent=2,default=str).encode('utf-8'))
    return bundle.getvalue()




# =============================================================================
# v17.2: GERCEK API VERI ALIM SAATI + GECMIS TAHMIN BACKTEST / CHRONO SPLIT
# NOT: Kullanicinin sagladigi gecmis veriler bagimsiz olarak onaylanmaz.
# =============================================================================
V172_SOURCES = ('market', 'api', 'model', 'blend')
V172_REQUIRED = ('match_id','kickoff_utc','snapshot_utc','league','result')
V172_NUMERIC = tuple(f'{src}_{r}' for src in V172_SOURCES for r in ('1','x','2'))


def v172_source_quality(records, simdi=None):
    """Arayuzde yeniden hesaplanmis olmasi kaynak alimini yeni yapmaz."""
    now=v17_utc(simdi) if simdi is not None else pd.Timestamp.now(tz='UTC')
    out=[]
    if not isinstance(records,list) or len(records)!=15:
        return ['15 tahmin satiri gerekli.']
    for i,r in enumerate(records,1):
        try:
            fetched=v17_utc(r['source_fetched_at'])
            if fetched>now + pd.Timedelta(seconds=5) or now-fetched>pd.Timedelta(minutes=30):
                out.append(f'{i}. mac: API veri alim zamani 30 dakikadan eski/gelecekte.')
            if r.get('source_provenance')!='API_REQUEST_AT':
                out.append(f'{i}. mac: API tahmin/oran kaynagi dogrulanamadi.')
        except (KeyError,ValueError,TypeError):
            out.append(f'{i}. mac: gercek API alis zamani yok (eski oturum olabilir).')
    return out


def v172_history_parse(csv_bytes, now=None):
    """Tarihsel tahminler: baslamadan EN AZ 30 dk once kaydedilmis olmalidir.
    Yalnizca skorlardan geriye donuk model tahmini uretmez.
    """
    if not isinstance(csv_bytes,bytes) or not csv_bytes or len(csv_bytes)>16_000_000:
        raise ValueError('Gecmis tahmin CSV dosyasi yok veya 16 MB sinirini asiyor.')
    df=pd.read_csv(io.BytesIO(csv_bytes),dtype={'match_id':'string','league':'string','result':'string'},low_memory=False)
    if not set(V172_REQUIRED) <= set(df.columns):
        raise ValueError('Eksik CSV alanlari: '+', '.join(sorted(set(V172_REQUIRED)-set(df.columns))))
    if not 1<=len(df)<=50_000:
        raise ValueError('CSV 1 ile 50000 mac icermelidir.')
    if df[list(V172_REQUIRED)].isna().any().any():
        raise ValueError('Mac ID, lig, baslama, snapshot veya sonuc bos.')
    df['match_id']=df.match_id.str.strip()
    if (df.match_id.str.len()>60).any() or (df.match_id=='').any() or df.match_id.duplicated().any():
        raise ValueError('Tekrarlanan/bos/asiri uzun mac ID.')
    df['league']=df.league.str.strip()
    if (df.league=='').any() or (df.league.str.len()>90).any():
        raise ValueError('Lig etiketi gecersiz.')
    for c in ('kickoff_utc','snapshot_utc'):
        raw=df[c].astype(str).str.strip()
        # Offset kaybolmus sessiz UTC varsayimi yasak.
        if not raw.str.contains(r'(?:Z|[+-]\d{2}:?\d{2})$',regex=True).all():
            raise ValueError(c+' saat dilimi icermeli (Z veya +03:00).')
        try:df[c]=pd.to_datetime(raw,utc=True,errors='raise',format='ISO8601')
        except (ValueError,TypeError):df[c]=pd.to_datetime(raw,utc=True,errors='raise')
    t_now=v17_utc(now) if now is not None else pd.Timestamp.now(tz='UTC')
    if (df.kickoff_utc>=t_now).any():
        raise ValueError('Gecmiste bitmis mac olmalidir; henuz baslamamis maclar yasak.')
    if (df.snapshot_utc >= df.kickoff_utc-pd.Timedelta(minutes=30)).any():
        raise ValueError('Maç baslamadan en az 30 dakika oncesine ait tahmin kaydi gerekli.')
    if (df.kickoff_utc-df.snapshot_utc > pd.Timedelta(days=30)).any():
        raise ValueError('Tahmin kaydi mactan 30 gun oncesine ait olamaz.')
    df['result']=df.result.str.strip().str.upper().replace({'0':'X'})
    if not df.result.isin(('1','X','2')).all():
        raise ValueError('90 dakika normal sure mac sonucu 1/X/2 olmali (0 -> X).')
    active=[]
    for src in V172_SOURCES:
        cols=[f'{src}_{r}' for r in ('1','x','2')]
        exists=[c in df.columns for c in cols]
        if any(exists) and not all(exists):
            raise ValueError(f'{src} eksik 1/X/2 sutunu.')
        if not all(exists):continue
        vals=df[cols].apply(pd.to_numeric,errors='coerce').to_numpy(float)
        valid=np.isfinite(vals).all(axis=1)
        absent=df[cols].isna().all(axis=1).to_numpy()
        if ((~valid)&(~absent)).any():
            raise ValueError(f'{src}: kismi, metin veya sonsuz olasilik satiri var.')
        if valid.any():
            p=vals[valid]
            if ((p<0)|(p>100)).any() or (abs(p.sum(axis=1)-100)>1.0).any():
                raise ValueError(f'{src}: olasiliklar 0-100 arasi ve toplami yaklasik 100 olmali.')
            active.append(src)
        for c in cols: df[c]=pd.to_numeric(df[c],errors='coerce')
    if not active:raise ValueError('En az bir kaynaga ait baslangic oncesi 1/X/2 tahminleri gerekli.')
    df=df.sort_values(['kickoff_utc','match_id'],kind='stable').reset_index(drop=True)
    return df,active


def v172_prob_and_label(df, src):
    cols=[f'{src}_{x}' for x in ('1','x','2')]
    p=df[cols].to_numpy(float)/100.
    mask=np.isfinite(p).all(axis=1)
    # 99.7 gibi kucuk yuzde yuvarlama farklarini normalleştir.
    p=p[mask]; p=p/np.sum(p,axis=1,keepdims=True)
    yy=df.loc[mask,'result'].map({'1':0,'X':1,'2':2}).to_numpy(int)
    return mask,p,yy


def v172_metrics(probs,y):
    p=np.asarray(probs,dtype=float);y=np.asarray(y,dtype=int)
    if p.ndim!=2 or p.shape[1]!=3 or len(y)!=len(p) or len(p)==0:
        raise ValueError('3 sinifli pozitif sayida tahmin gerekli.')
    if not np.isfinite(p).all() or (p<0).any() or (p.sum(axis=1)<=0).any():
        raise ValueError('Sayisal olasilik gecersiz.')
    p=p/p.sum(axis=1,keepdims=True)
    if not np.isin(y,[0,1,2]).all():raise ValueError('Sonuc 0,1,2 siniflarinda olmali.')
    onehot=np.eye(3)[y]
    brier=np.mean(np.sum((p-onehot)**2,axis=1))
    ll=np.mean(-np.log(np.clip(p[np.arange(len(y)),y],1e-12,1)))
    prediction=np.argmax(p,axis=1)
    confidence=np.max(p,axis=1)
    # Multiclass ECE: top confidence binning; sample size yetmezse yorum icin az.
    ece=0.
    for j in range(10):
        inbin=(confidence>=j/10)&((confidence<(j+1)/10) if j<9 else (confidence<=1.0))
        if inbin.any():ece+=inbin.mean()*abs((prediction[inbin]==y[inbin]).mean()-confidence[inbin].mean())
    return {'n':int(len(y)),'brier':float(brier),'log_loss':float(ll),
            'top1_accuracy':float(np.mean(prediction==y)),'ece_top1':float(ece)}


def v172_temperature(probs, t):
    p=np.asarray(probs,float)
    if t<=0:raise ValueError('Temperature pozitif olmali.')
    logits=np.log(np.clip(p,1e-12,1.))/float(t)
    logits-=np.max(logits,axis=1,keepdims=True)
    e=np.exp(logits)
    return e/e.sum(axis=1,keepdims=True)


def v172_temporal_calibration(df,src):
    """Takvim gunu kesmesi + embargo; test sonucuyla sicaklik ogrenilmez."""
    from scipy.optimize import minimize_scalar
    mask,p,y=v172_prob_and_label(df,src)
    data=df.loc[mask].reset_index(drop=True)
    result={'source':src,'total_n':int(len(data)),'status':'INSUFFICIENT_DATA','train_n':0,'holdout_n':0}
    if len(data)<120:return result
    dates=data.kickoff_utc.dt.floor('D')
    days=np.sort(dates.unique())
    if len(days)<20:return result
    # Her gun tamamen ya train ya test; test baslangicindan once 24h embargo.
    cutday=days[int(len(days)*0.70)]
    cut=pd.Timestamp(cutday)
    tr=(data.kickoff_utc < cut-pd.Timedelta(days=1)).to_numpy()
    te=(data.kickoff_utc >= cut).to_numpy()
    result['train_n']=int(tr.sum());result['holdout_n']=int(te.sum())
    if tr.sum()<80 or te.sum()<30:return result
    def objective(t):
        pc=v172_temperature(p[tr],t)
        return float(-np.mean(np.log(np.clip(pc[np.arange(tr.sum()),y[tr]],1e-12,1))))
    fit=minimize_scalar(objective,bounds=(.5,4),method='bounded',options={'xatol':1e-3})
    if not fit.success or not np.isfinite(fit.x):return result
    val_raw=v172_metrics(p[te],y[te]); val_cal=v172_metrics(v172_temperature(p[te],fit.x),y[te])
    freq=(np.bincount(y[tr],minlength=3)+1)/(int(tr.sum())+3)
    val_base=v172_metrics(np.tile(freq,(int(te.sum()),1)),y[te])
    result.update(status='OUT_OF_TIME_TEST',temperature=float(fit.x),
                  holdout_start=cut.isoformat(),train_end=(cut-pd.Timedelta(days=1)).isoformat(),
                  raw=val_raw,calibrated=val_cal,baseline=val_base,
                  calibrated_better_log_loss=bool(val_cal['log_loss']<val_raw['log_loss']))
    return result


def v172_backtest_report(df,sources):
    rows=[];temp=[]; league=[]
    for src in sources:
        mask,p,y=v172_prob_and_label(df,src)
        met=v172_metrics(p,y)
        rows.append({'Kaynak':src,'Mac':met['n'],'Brier':round(met['brier'],5),
                     'LogLoss':round(met['log_loss'],5),'1X2_Isabet_%':round(100*met['top1_accuracy'],2),
                     'ECE_%':round(100*met['ece_top1'],2),'Not':'Retrospektif; bagimsiz onay yok'})
        temp.append(v172_temporal_calibration(df,src))
        srcdf=df.loc[mask].copy()
        for lig, grp in srcdf.groupby('league',sort=True):
            if len(grp)<10:continue
            _,pl,yl=v172_prob_and_label(grp,src)
            r=v172_metrics(pl,yl)
            league.append({'Kaynak':src,'Lig':str(lig),'Mac':r['n'],
                           'Brier':round(r['brier'],5),'LogLoss':round(r['log_loss'],5),
                           'Uyari':'Az ornek (<30)' if r['n']<30 else 'Betimleyici'})
    common=np.ones(len(df),bool)
    for src in sources:
        common &= np.isfinite(df[[f'{src}_{r}' for r in ('1','x','2')]].to_numpy(float)).all(axis=1)
    paired=[]
    if common.sum()>=30:
        for src in sources:
            _,p,y=v172_prob_and_label(df.loc[common],src)
            m=v172_metrics(p,y)
            paired.append({'Kaynak':src,'Ayni_mac_adedi':m['n'],'Brier':round(m['brier'],5),
                           'LogLoss':round(m['log_loss'],5),'1X2_Isabet_%':round(100*m['top1_accuracy'],2)})
    return rows,temp,league,paired


# ============================================================================
# v17.3 Anti-Public PRO: user-supplied FULL verified-form 15-match CSV only.
# "verified-form" != external authenticity; no payout/EV or win guarantees.
# ============================================================================
def v173_halk_dogrula(raw, fixture_ids, kickoff_times=None, now=None, max_age_hours=72):
    """Parse fully aligned public marginal percentages; fail closed for scoring.

    CSV columns: fixture_id,h1,hx,h2,source,snapshot. `source` must be an
    HTTPS URL, but its contents and ownership are NOT verified here.
    """
    from urllib.parse import urlparse
    ids=[int(x) for x in fixture_ids]
    if len(ids)!=15 or len(set(ids))!=15:
        raise ValueError('Anti-Public: 15 farkli mac kimligi gerekli.')
    if not isinstance(raw,(bytes,bytearray)) or not raw or len(raw)>1_000_000:
        raise ValueError('Anti-Public CSV bos ya da 1 MB uzerinde.')
    df=pd.read_csv(io.BytesIO(raw),dtype={'fixture_id':'string','source':'string','snapshot':'string'})
    needed={'fixture_id','h1','hx','h2','source','snapshot'}
    if not needed.issubset(df.columns) or len(df)!=15:
        raise ValueError('Anti-Public tam 15 satir ve fixture_id,h1,hx,h2,source,snapshot sutunlari ister.')
    if df.fixture_id.isna().any() or not df.fixture_id.str.fullmatch(r'[0-9]+').fillna(False).all():
        raise ValueError('Anti-Public: mac ID hatali.')
    found=[int(x) for x in df.fixture_id]
    if len(set(found))!=15 or set(found)!=set(ids):
        raise ValueError('Anti-Public: eksik, fazla veya mukerrer mac kimligi.')
    q=df[['h1','hx','h2']].apply(pd.to_numeric,errors='raise').to_numpy(float)
    if not np.isfinite(q).all() or np.any(q<0) or np.any(q>100) or np.any(abs(q.sum(axis=1)-100)>0.20):
        raise ValueError('Anti-Public: oranlar 0..100 araliginda ve yaklasik 100 toplami olmalidir.')
    if df.source.isna().any():raise ValueError('Anti-Public: kaynak adresi bos.')
    for v in df.source.astype(str):
        u=urlparse(v.strip())
        if u.scheme.lower()!='https' or not u.hostname or '.' not in u.hostname or u.username or u.password or len(v)>1000:
            raise ValueError('Anti-Public: source alani HTTPS URL olmalidir (otantiklik kaniti degildir).')
    if df.snapshot.isna().any() or not df.snapshot.astype(str).str.contains(r'(?:Z|[+-]\d{2}:?\d{2})$',regex=True).all():
        raise ValueError('Anti-Public: saat dilimli snapshot gerekli.')
    ts=pd.to_datetime(df.snapshot,utc=True,errors='raise')
    now_ts=pd.Timestamp.now(tz='UTC') if now is None else pd.Timestamp(now)
    if now_ts.tzinfo is None:raise ValueError('Anti-Public: simdi zaman dilimli olmali.')
    now_ts=now_ts.tz_convert('UTC')
    age=(now_ts-ts).dt.total_seconds()/3600
    if (age<0).any() or (age>max_age_hours).any():
        raise ValueError(f'Anti-Public: gelecek veya {max_age_hours} saatten eski snapshot var.')
    kick_dict={}
    if kickoff_times is not None:
        if len(kickoff_times)!=15:raise ValueError('Anti-Public: 15 baslama zamani gerekli.')
        for mid,kick in zip(ids,kickoff_times):
            k=pd.Timestamp(kick)
            if k.tzinfo is None:raise ValueError('Anti-Public: baslama zamani dilimsiz.')
            kick_dict[mid]=k.tz_convert('UTC')
    pub={}
    for i,(mid,row) in enumerate(zip(found,q)):
        if kick_dict and ts.iloc[i]>=kick_dict[mid]:
            raise ValueError('Anti-Public: mac basladiktan sonra toplanmis halk oranlari reddedildi.')
        pub[mid]={'q':(row/row.sum()).tolist(),'source':str(df.source.iloc[i]).strip(),
                  'snapshot':ts.iloc[i].isoformat()}
    return {'ok':True,'data':pub,'sha256':hashlib.sha256(raw).hexdigest(),
            'max_age_hours':float(age.max()),'source_count':len({v['source'] for v in pub.values()}),
            'provenance':'USER_SUPPLIED_UNVERIFIED','match_ids':ids}


def v173_skor_olustur(code, model, crowd=None, crowd_strength=0.0):
    """Bounded log-score ranking ONLY; not payout prediction or calibration."""
    code=np.asarray(code)
    p=np.asarray(model,dtype=float)
    strength=float(crowd_strength)
    if code.ndim!=2 or code.shape[1]!=15 or p.shape!=(15,3) or not np.isin(code,[0,1,2]).all():
        raise ValueError('Anti-Public: matris boyutlari hatali.')
    if not np.isfinite(p).all() or np.any(p<=0) or np.any(abs(p.sum(axis=1)-100)>1.5):
        raise ValueError('Anti-Public: model yuzdeleri gecersiz.')
    if not np.isfinite(strength) or not 0<=strength<=0.25:
        raise ValueError('Anti-Public: agirlik 0..0.25 araliginda olmali.')
    score=np.sum(np.log(np.maximum(p[np.arange(15),code],1)/100),axis=1)
    if strength==0 or crowd is None:
        if strength>0 and crowd is None:
            raise ValueError('Anti-Public: halk CSV olmadan pozitif agirlik uygulanamaz.')
        return score
    q=np.asarray(crowd,float)
    if q.shape!=(15,3) or not np.isfinite(q).all() or (q<0).any() or (q>1).any() or not np.allclose(q.sum(axis=1),1,atol=.002):
        raise ValueError('Anti-Public: halk matrisi 15x3 normalize olasalik olmali.')
    crowd_log=np.log(np.clip(q[np.arange(15),code],.01,1)).sum(axis=1)
    return score-strength*crowd_log


def v173_portfoy_raporu(kolonlar,veriler,public=None,strength=0.0,max_rows=60):
    """Produces stable diagnostic rankings without changing coupon membership."""
    a=np.asarray(kolonlar)
    if a.ndim!=2 or a.shape[1]!=15 or not np.isin(a,['1','X','2']).all():
        raise ValueError('Anti-Public: 15 kolon isareti gerekli.')
    if not len(a) or len(a)>300000:raise ValueError('Anti-Public: kolon adedi 1..300000 olmali.')
    if len(veriler)!=15:raise ValueError('Anti-Public: 15 tahmin gerekli.')
    code=np.where(a=='X',1,np.where(a=='2',2,0)).astype(np.int8)
    model=np.array([[v[k] for k in ('1','X','2')] for v in veriler],float)
    q=None
    if public is not None:
        q=np.array([public[int(v['id'])]['q'] for v in veriler],float)
    score=v173_skor_olustur(code,model,q,strength)
    pure=v173_skor_olustur(code,model,None,0)
    ranks=np.argsort(-score,kind='stable')[:max_rows]
    unique=int(len(np.unique(code,axis=0)))
    # deterministic evenly spaced sample: O(200^2 * 15), never n*n at 300k.
    ix=np.unique(np.linspace(0,len(a)-1,min(200,len(a)),dtype=int))
    sampled=code[ix]
    if len(sampled)>1:
        distances=np.sum(sampled[:,None,:]!=sampled[None,:,:],axis=2)
        pairs=distances[np.triu_indices(len(sampled),1)]
        distance_min=int(pairs.min()); distance_avg=float(pairs.mean())
    else: distance_min=None;distance_avg=None
    rows=[]
    for ind in ranks:
        r={'rank':len(rows)+1,'original_no':int(ind+1),'column':''.join(a[ind]),
           'model_log_score':round(float(pure[ind]),6),
           'crowd_proxy_score':round(float(score[ind]),6)}
        if q is not None:
            r['crowd_log_proxy']=round(float(np.log(np.clip(q[np.arange(15),code[ind]],.01,1)).sum()),6)
        rows.append(r)
    return {'count':len(a),'unique':unique,'duplicates':len(a)-unique,
            'sample_size':len(sampled),'min_pairwise_hamming_sample':distance_min,
            'mean_pairwise_hamming_sample':distance_avg,
            'crowd_complete':public is not None,'weight':float(strength),
            'top_rows':rows,'method':'MODEL_LOG_MINUS_LAMBDA_CROWD_LOG_NOT_EV',
            'warning':'Halk marjinalleri kupon ortak-dagilimini, ikramiye paylasimini veya kar olasiligini olcmez.'}


# ==============================================================================
# v18.0 KABUL MERKEZİ — SADECE ANALİZ ÇIKTISI
# Bu fonksiyonlar resmî Spor Toto sayfasının kimliğini, ödeme ve makbuzu
# ONAYLAMAZ. SHA-256 dosya bozulmasını tespit eder, kaynak otantikliği sağlamaz.
# ==============================================================================
V18_DOSYALAR = (
    'KOLONLAR_ANALIZ_1X2.txt',
    'KOLONLAR_SPORTOTO_102_INCELEME.txt',
    'BULTEN_MANIFEST.json',
    'KABUL_RAPORU.json',
)



# ===== v18.1 / EXACT INDEPENDENT MATH AUDITOR (NO PREDICTION ENGINE) =====
V181_KEYS = ('tam_15', 'en_az_14', 'en_az_13', 'en_az_12')


def v181_template_canonical(template):
    if not isinstance(template, list) or len(template) != 15:
        raise ValueError('Tam 15 satırlı ham şablon gereklidir.')
    normalized = []
    for n, row in enumerate(template, 1):
        if not isinstance(row, (list, tuple)) or not 1 <= len(row) <= 3:
            raise ValueError(f'{n}. ham şablon satırı geçersiz.')
        if any(not isinstance(x, str) or x not in ('1', 'X', '2') for x in row) or len(row) != len(set(row)):
            raise ValueError(f'{n}. şablonda geçersiz veya mükerrer işaret.')
        # Kanonik sıralama: farklı serileştirme sıralarından kaynaklanan imza karışıklığını önler.
        normalized.append([x for x in ('1', 'X', '2') if x in row])
    if math.prod(map(len, normalized)) > 300000:
        raise ValueError('Ham evren 300.000 sınırının üzerinde. Kör/eksik hesap yapılmaz.')
    return normalized


def v181_template_hash(template):
    normalized = v181_template_canonical(template)
    return hashlib.sha256(json.dumps(normalized, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest()


def v181_parse_txt(raw):
    if not isinstance(raw, (bytes, bytearray)) or not 0 < len(raw) < 8_000_000:
        raise ValueError('Kolon TXT eksik veya güvenli boyut sınırı dışında.')
    try:
        lines = raw.decode('utf-8-sig').splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError('TXT UTF-8 olmalıdır.') from exc
    if not 0 < len(lines) <= 300000:
        raise ValueError('Geçersiz kolon sayısı.')
    if any(len(s) != 15 or any(c not in '1X2' for c in s) for s in lines):
        raise ValueError('Tüm kolonlar 15 karakterli 1/X/2 olmalıdır.')
    if len(set(lines)) != len(lines):
        raise ValueError('Mükerrer kolon bulunuyor.')
    return lines


def v181_exact_audit(raw, template, expected=None, max_universe=300000):
    """Sıfır örnekleme ile ürün evrenindeki HER olasılığı sayar.
    min-plus Hamming uzaklık dönüşümü; 15 eksenin hepsinde geçiş tamdır.
    """
    t = v181_template_canonical(template)
    n = math.prod(map(len, t))
    if n > max_universe:
        raise ValueError('Bu çalıştırmadaki evren kaynak limiti aşıldı; kapsam iddiası yok.')
    lines = v181_parse_txt(raw)
    dims = tuple(len(row) for row in t)
    lookups = [{symbol: idx for idx, symbol in enumerate(row)} for row in t]
    coords = [[] for _ in range(15)]
    for k, line in enumerate(lines, 1):
        for axis, ch in enumerate(line):
            if ch not in lookups[axis]:
                raise ValueError(f'{k}. kolon {axis + 1}. maçta ham şablon dışında.')
            coords[axis].append(lookups[axis][ch])
    distances = np.full(dims, 16, dtype=np.uint8)
    distances[tuple(np.asarray(c, dtype=np.intp) for c in coords)] = 0
    # Min-plus Hamming transform: bir eksen için d'(s)=min(d(s), 1+min_{u} d(u)).
    # Her eksende geçildiğinde kalan eksenlerden bağımsız en yakın kupon uzaklığı elde edilir.
    for axis in range(15):
        if dims[axis] == 1:
            continue
        minima = distances.min(axis=axis, keepdims=True)
        np.minimum(distances, minima + np.uint8(1), out=distances)
    closest = np.subtract(np.uint8(15), distances.reshape(-1))
    histogram = np.bincount(closest, minlength=16)
    if int(histogram.sum()) != n:
        raise AssertionError('Dahili toplam sayım hatası.')
    counts = {key: int(histogram[cutoff:].sum()) for cutoff, key in [(15, V181_KEYS[0]), (14, V181_KEYS[1]), (13, V181_KEYS[2]), (12, V181_KEYS[3])]}
    percents = {key: 100.0 * count / n for key, count in counts.items()}
    mismatches = []
    if expected is not None:
        if not isinstance(expected, dict):
            raise ValueError('Bildirilen kapsama özeti JSON nesnesi olmalıdır.')
        for key in V181_KEYS:
            if key not in expected:
                raise ValueError(f'Bildirilen ham kapsamada {key} alanı eksik.')
            try:
                claim = float(expected[key])
            except (TypeError, ValueError) as exc:
                raise ValueError(f'{key} yüzdesi sayı değil.') from exc
            if not math.isfinite(claim) or abs(claim - percents[key]) > 1e-6:
                mismatches.append({'metric': key, 'reported_percent': expected[key], 'exact_percent': percents[key]})
    # En zayıf en iyi isabetli senaryo bir karşı-örnektir (tüm eşiği geçmeyebilir).
    worst_flat = int(np.argmin(closest))
    worst_coords = np.unravel_index(worst_flat, dims)
    witness = ''.join(t[i][int(worst_coords[i])] for i in range(15))
    return {
        'audit_version': '19.0 INDEPENDENT EXACT FULL-UNIVERSE',
        'algorithm': 'EXACT_MIXED_RADIX_HAMMING_MIN_PLUS_FULL_ENUMERATION',
        'scope': 'RAW_TEMPLATE_CARTESIAN_UNIVERSE_ONLY',
        'input_txt_sha256': hashlib.sha256(raw).hexdigest(),
        'template_sha256': v181_template_hash(t),
        'template': t,
        'scenario_count': n,
        'unique_columns': len(lines),
        'closest_hit_histogram_0_to_15': [int(x) for x in histogram],
        'exact_count': counts,
        'exact_percent': percents,
        'minimum_best_hits': int(closest.min()),
        'worst_case_example': witness,
        'reported_coverage_agrees': not mismatches if expected is not None else None,
        'mismatches': mismatches,
        'official_bulletin_verified': False,
        'prediction_accuracy_verified': False,
        'payment_verified': False,
        'real_money_approved': False,
        'warning': 'Kapsama yalnız verilen ham şablon senaryolarında. Tahmin, ikramiye veya gerçek maç garantisi değildir.'
    }


def v181_audit_archive(zip_bytes, external_template=None):
    """v18.x analiz ZIP'i açar; yeni imzalı şablon veya dışarıdan açık şablon gerekir."""
    if not isinstance(zip_bytes, (bytes, bytearray)) or not 100 < len(zip_bytes) <= 16_000_000:
        raise ValueError('ZIP boyutu geçersiz.')
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            members = z.infolist()
            names = [m.filename for m in members]
            required = {'KOLONLAR_ANALIZ_1X2.txt','BULTEN_MANIFEST.json','KABUL_RAPORU.json','DOSYA_BUTUNLUK.json','KOLONLAR_SPORTOTO_102_INCELEME.txt'}
            if set(names) != required or len(names) != 5 or len(names) != len(set(names)):
                raise ValueError('ZIP içindeki dosya listesi beklenen biçimde değil.')
            if any(m.is_dir() or m.file_size > 8_000_000 for m in members) or sum(m.file_size for m in members) > 17_000_000:
                raise ValueError('Şişirilmiş ZIP içerikleri reddedildi.')
            data = {name: z.read(name) for name in names}
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise ValueError('ZIP okunamadı.') from exc
    try:
        integrity = json.loads(data['DOSYA_BUTUNLUK.json'])
        manifest = json.loads(data['BULTEN_MANIFEST.json'])
        acceptance = json.loads(data['KABUL_RAPORU.json'])
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('ZIP içindeki JSON bozuk.') from exc
    if integrity.get('format') != 'SHA256_FILE_INTEGRITY_NOT_ORIGIN_AUTHENTICATION' or set(integrity.get('sha256', {})) != (required - {'DOSYA_BUTUNLUK.json'}):
        raise ValueError('Dosya bütünlük şeması geçersiz.')
    for name in required - {'DOSYA_BUTUNLUK.json'}:
        if hashlib.sha256(data[name]).hexdigest() != integrity['sha256'][name]:
            raise ValueError(f'{name} SHA-256 uyuşmuyor.')
    raw = data['KOLONLAR_ANALIZ_1X2.txt']
    lines = v181_parse_txt(raw)
    if hashlib.sha256(raw).hexdigest() != manifest.get('txt_sha256') or len(lines) != manifest.get('columns'):
        raise ValueError('Kolon dosyası manifestle uyuşmuyor.')
    if acceptance.get('manifest_sha256') != hashlib.sha256(data['BULTEN_MANIFEST.json']).hexdigest() or acceptance.get('txt_sha256') != hashlib.sha256(raw).hexdigest():
        raise ValueError('Kabul raporu başka pakete ait.')
    if acceptance.get('analysis_package_eligible') is not True or acceptance.get('real_money_approved') is not False:
        raise ValueError('ZIP analiz kabul raporu uygun değil.')
    if data['KOLONLAR_SPORTOTO_102_INCELEME.txt'] != raw.replace(b'X',b'0'):
        raise ValueError('102 dönüştürme dosyası eşleşmiyor.')
    t = manifest.get('raw_template')
    if t is None:
        if external_template is None:
            raise ValueError('Bu eski ZIP orijinal ham şablonu taşımıyor. 15 satırlı g_sablon JSON ayrıca gerekir; yalnız 1.849 kolondan şablon çıkarılamaz.')
        t = external_template
        provenance = 'EXTERNAL_TEMPLATE_NOT_BOUND_TO_OLD_MANIFEST'
    else:
        if external_template is not None and v181_template_hash(external_template) != v181_template_hash(t):
            raise ValueError('Harici şablonla manifest şablonu uyuşmuyor.')
        if manifest.get('raw_template_sha256') != v181_template_hash(t):
            raise ValueError('Manifest şablon imzası uyuşmuyor.')
        if manifest.get('raw_universe_count') != math.prod(len(x) for x in t):
            raise ValueError('Manifest evren büyüklüğü hatalı.')
        provenance = 'EMBEDDED_TEMPLATE_MANIFEST_BOUND'
    expected = manifest.get('reported_raw_coverage') if provenance == 'EMBEDDED_TEMPLATE_MANIFEST_BOUND' else None
    audit = v181_exact_audit(raw, t, expected=expected)
    target = manifest.get('target_correct_matches')
    metric = {15:V181_KEYS[0],14:V181_KEYS[1],13:V181_KEYS[2],12:V181_KEYS[3]}.get(target)
    if metric is None:
        raise ValueError('Hedef isabet geçersiz.')
    if manifest.get('coverage_raw_universe_percent') is not None and abs(float(manifest['coverage_raw_universe_percent']) - audit['exact_percent'][metric]) > 1e-6:
        raise ValueError('Manifest ham kapsam yüzdesi ile tam yeniden sayım farklı.')
    if audit['mismatches']:
        raise ValueError('Ham senaryo kapsam iddiaları bağımsız tam hesapla eşleşmiyor.')
    audit['template_provenance'] = provenance
    audit['bulletin_signature'] = acceptance.get('bulletin_signature')
    audit['analysis_zip_sha256'] = hashlib.sha256(zip_bytes).hexdigest()
    return audit



def v18_sablon_kontrol(raw, ozet, limit=300000):
    """v18.1: tüm ham evrende bağımsız 12/13/14/15 tam sayımı."""
    if not isinstance(ozet, dict):
        raise ValueError('Ham şablon özeti gerekli.')
    template = ozet.get('g_sablon')
    if not isinstance(ozet.get('denetim_ham'), dict):
        raise ValueError('Karşılaştırılacak eski ham kapsama yüzdeleri eksik.')
    audit = v181_exact_audit(raw, template, expected=ozet['denetim_ham'], max_universe=limit)
    if int(ozet.get('ham_adet', -1)) != audit['scenario_count']:
        raise ValueError('Ham evren büyüklüğü özetle farklı.')
    if audit['mismatches']:
        raise ValueError('Bağımsız tam sayım: önceki ham kapsama değerleriyle uyuşmazlık.')
    return {'mode':'EXACT_RAW_UNIVERSE_RECOMPUTED',
            'universe_count':audit['scenario_count'],
            'raw_coverage_percent':audit['exact_percent'],
            'closest_hit_histogram_0_to_15':audit['closest_hit_histogram_0_to_15'],
            'input_txt_sha256':audit['input_txt_sha256'],
            'template_sha256':audit['template_sha256']}

# =============================================================================
# v18.0.2 — İSTEĞE BAĞLI KULLANICI ONAYLI BÜLTEN KAPISI (ANALİZ AMAÇLI)
# CSV, bağımsız metin veya tekrar API sorgusu bu modda GEREKMEZ.
# Beyan resmî doğrulama, canlı oyun yetkisi veya resmî kapanış bilgisi değildir.
# =============================================================================
V1802_BEYAN = 'USER_CHECKED_15_MATCHES_AND_ORDER_NOT_OFFICIALLY_VERIFIED'


def v1802_onay_kapisi(maclar, tahminler, beyan, simdi=None):
    now=v17_utc(simdi) if simdi is not None else pd.Timestamp.now(tz='UTC')
    errors=[]
    signature=None
    try:
        signature=v171_mac_imzasi(maclar)
    except (ValueError,TypeError,KeyError,AttributeError) as exc:
        errors.append('15 maç kimliği/sırası geçersiz: '+str(exc))
    if not isinstance(beyan,dict) or beyan.get('declaration')!=V1802_BEYAN:
        errors.append('Kullanıcının açık onay kaydı eksik.')
    else:
        if not signature or beyan.get('match_signature')!=signature:
            errors.append('Kullanıcı onayı bu bültenin sırası/kimliğiyle eşleşmiyor.')
        try:
            approved=v17_utc(beyan['attested_at'])
            if approved>now+pd.Timedelta(minutes=1) or now-approved>pd.Timedelta(hours=24):
                errors.append('Kullanıcı onayı 24 saatten eski veya gelecekte.')
        except (KeyError,TypeError,ValueError,AttributeError):
            errors.append('Kullanıcı onayı zaman damgası eksik/hatalı.')
    if not isinstance(tahminler,list) or len(tahminler)!=15:
        errors.append('Tam 15 tahmin kaydı yok.')
    elif isinstance(maclar,list) and len(maclar)==15:
        if [str(m.get('id')) for m in maclar]!=[str(v.get('id')) for v in tahminler]:
            errors.append('Tahmin ID/sırası bültenle eşleşmiyor.')
        errors.extend(v17_tahmin_kalitesi(tahminler,simdi=now))
        errors.extend(v172_source_quality(tahminler,simdi=now))
    expected=[{'order':i+1,'fixture_id':str(m['id']),
               'match':f"{m['ev']} - {m['dep']}",'date':m['tarih'],'time':m['saat']}
              for i,m in enumerate(maclar)] if signature else []
    return {'ok':not errors,'mode':'USER_ATTESTED','status':'USER_ATTESTED_NOT_OFFICIAL_VERIFIED' if not errors else 'BLOCKED',
            'issues':errors,'match_signature':signature,'evaluated_at':now.isoformat(),
            'manual_attestation':dict(beyan) if isinstance(beyan,dict) else None,
            'csv':None,'manual_list':None,'api':None,'expected_export_rows':expected,
            'official_source_verified':False,'official_closing_verified':False}


def v18_kabul_raporu(raw, manifest_bytes, kapi, maclar, tahminler, param_imza,
                     kolon_fiyati, butce, simdi=None, ozet=None):
    """Bütün sonuçlar deterministik ve fail-closed. Canlı oynama yetkisi ASLA üretmez."""
    now = v17_utc(simdi) if simdi is not None else pd.Timestamp.now(tz='UTC')
    checks=[]
    def kaydet(code, title, passed, detail, blocking=True):
        checks.append({'code':code, 'title':title,
                       'status':'PASS' if passed else ('FAIL' if blocking else 'NOT_VERIFIED'),
                       'blocking_for_analysis':bool(blocking), 'detail':str(detail)[:600]})

    signature=None
    try:
        signature=v171_mac_imzasi(maclar)
        kaydet('A01','15 benzersiz maçın kimliği ve sırası',True,'15 benzersiz ID, sıra 1–15.')
    except (ValueError,TypeError,KeyError) as exc:
        kaydet('A01','15 benzersiz maçın kimliği ve sırası',False,exc)

    # Açıkça seçilen kullanıcı onayı modunda dış CSV/metin/API üçlü kapısı YOKTUR.
    # Bu iki kontrolü PASS diye sunmuyoruz; USER_ACCEPTED ayrı durumdur.
    manual_mode=isinstance(kapi,dict) and kapi.get('mode')=='USER_ATTESTED'
    if manual_mode:
        manual_issues=[]
        att=kapi.get('manual_attestation')
        if not isinstance(att,dict) or att.get('declaration')!=V1802_BEYAN:
            manual_issues.append('Kullanıcının açık onay kaydı yok.')
        elif not signature or att.get('match_signature')!=signature:
            manual_issues.append('Kullanıcı onayı farklı maç sırasına ait.')
        else:
            try:
                approved=v17_utc(att['attested_at'])
                if approved>now+pd.Timedelta(minutes=1) or now-approved>pd.Timedelta(hours=24):
                    manual_issues.append('Kullanıcı onayı 24 saatten eski veya gelecekte.')
            except (KeyError,ValueError,TypeError,AttributeError):
                manual_issues.append('Kullanıcı onay zamanı hatalı.')
        if not kapi.get('ok') or kapi.get('status')!='USER_ATTESTED_NOT_OFFICIAL_VERIFIED':
            manual_issues.append('Kullanıcı beyanı kontrol kapısı başarısız.')
        if signature!=kapi.get('match_signature'):
            manual_issues.append('Maç imzası farklı.')
        issues=kapi.get('issues')
        if issues is None or not isinstance(issues,list):
            manual_issues.append('Kullanıcı beyanı kontrol listesi bozuk.')
        elif issues:
            manual_issues.extend(str(i) for i in issues[:5])
        try:
            evaluated=v17_utc(kapi['evaluated_at'])
            if evaluated>now+pd.Timedelta(minutes=1) or now-evaluated>pd.Timedelta(minutes=10):
                manual_issues.append('Kullanıcı beyanı mevcut kabul hesabına ait değil.')
        except (KeyError,TypeError,ValueError,AttributeError):
            manual_issues.append('Beyan değerlendirme saati bulunamadı.')
        if manual_issues:
            kaydet('A02','Kullanıcının 15 maç listesi ve sıra onayı',False,'; '.join(dict.fromkeys(manual_issues)))
        else:
            checks.append({'code':'A02','title':'Kullanıcı 15 maç sırasını kabul etti (bağımsız doğrulama yok)',
                'status':'USER_ACCEPTED','blocking_for_analysis':True,
                'detail':'CSV/metin/API karşılaştırması kullanıcı isteğiyle kaldırıldı; resmî 15 maç listesi bağımsız doğrulanmadı.'})
    else:
        # Üçlü kontrol modu: yanlış/eksik girdileri otomatik onaylama.
        # A02 her durumda zorunludur; eksik kanıt varsa ASLA varsayılan PASS verme.
        a02_issues=[]
        if not isinstance(kapi,dict):
            a02_issues.append('Bülten karşılaştırma kaydı yok. 1. sekmedeki üçlü kontrolü tamamlayın.')
        else:
            if not signature or kapi.get('match_signature')!=signature:
                a02_issues.append('Maç kimliği/sırası mevcut bültenle aynı değil.')
            for label,key in [('CSV','csv'),('Bağımsız maç listesi','manual_list'),('API tekrar sorgusu','api')]:
                part=kapi.get(key)
                if not isinstance(part,dict):
                    a02_issues.append(f'{label} doğrulama kaydı eksik veya başarısız.')
                elif signature and part.get('match_signature')!=signature:
                    a02_issues.append(f'{label} farklı maç sırasına/bültene ait.')
            if not kapi.get('ok'):
                a02_issues.append('Üçlü kontrol kapısı başarısız (ok=False); işlem engeli korunuyor.')
            issues=kapi.get('issues')
            if isinstance(issues,list) and issues:
                a02_issues.extend(str(x) for x in issues[:8])
            elif issues is not None and not isinstance(issues,list):
                a02_issues.append('Üçlü kontrol hata listesi geçersiz biçimde.')
            if kapi.get('status')!='INDEPENDENT_INPUTS_CONSISTENT_NOT_OFFICIALLY_AUTHENTICATED':
                a02_issues.append('Üçlü karşılaştırmanın onay durumu geçerli değil.')
            try:
                tt=v17_utc(kapi['evaluated_at'])
                if tt>now:
                    a02_issues.append('Bülten karşılaştırma tarihi gelecekte.')
                elif now-tt>pd.Timedelta(minutes=10):
                    a02_issues.append('Bülten karşılaştırması 10 dakikadan eski; API kontrolünü yenileyin.')
            except (KeyError,TypeError,ValueError,AttributeError):
                a02_issues.append('Bülten karşılaştırma zamanı eksik/hatalı.')
        kaydet('A02','Bülten CSV/metin/API ön-kontrol kapısı',not a02_issues,
               '; '.join(dict.fromkeys(a02_issues)) if a02_issues else
               'CSV, bağımsız liste ve taze API tekrar sorgusu aynı 15 maçla uyumlu; resmî kaynak otantikliği değildir.')

    try:
        if not isinstance(maclar,list) or len(maclar)!=15:
            raise ValueError('15 maç gereklidir.')
        kickoff=[v17_utc(f"{m['tarih']}T{m['saat']}:00+03:00") for m in maclar]
        if min(kickoff)-now<=pd.Timedelta(minutes=5):
            raise ValueError('En erken maç başlamış veya 5 dakikalık emniyet sınırında.')
        if manual_mode:
            if any(c['code']=='A02' and c['status']=='FAIL' for c in checks):
                raise ValueError('Kullanıcı onayı geçersiz; A02 kontrolünü tamamlayın.')
            # Maçların kayıtlı başlama zamanları sınanır, fakat resmî kapanış bilinmiyor.
            checks.append({'code':'A03','title':'Başlama saatleri kontrolü; resmî kapanış bilinmiyor',
                'status':'USER_ACCEPTED','blocking_for_analysis':True,
                'detail':'Seçili 15 maçın kayıtlı başlangıç zamanı gelecekte. Resmî bülten kapanışı doğrulanmadı.'})
        else:
            csv_proof=kapi.get('csv') if isinstance(kapi,dict) else None
            if not isinstance(csv_proof,dict):
                raise ValueError('CSV kapanış bilgisi doğrulanmadı; önce A02 bülten kontrolünü tamamlayın.')
            close_value=csv_proof.get('closes_at')
            if not close_value:
                raise ValueError('CSV closes_at alanı eksik; önce A02 bülten kontrolünü tamamlayın.')
            close=v17_utc(close_value)
            if close-now<=pd.Timedelta(minutes=5):
                raise ValueError('Kullanıcı beyanındaki bülten kapanışına 5 dakika veya daha az kaldı.')
            if close>min(kickoff):
                raise ValueError('Kapanış en erken maç saatini geçiyor.')
            kaydet('A03','Başlama ve kapanış emniyet sınırı',True,'Tüm maçlar başlamamış, beyan edilen kapanış öncesi.')
    except (KeyError,ValueError,TypeError,AttributeError,OverflowError) as exc:
        kaydet('A03','Başlama ve kapanış emniyet sınırı',False,exc)

    try:
        issues=v17_tahmin_kalitesi(tahminler,simdi=now)+v172_source_quality(tahminler,simdi=now)
        if isinstance(tahminler,list) and isinstance(maclar,list):
            if [str(x.get('id')) for x in tahminler]!=[str(x.get('id')) for x in maclar]:
                issues.append('Tahmin ve bülten maç ID sırası uyuşmuyor.')
        kaydet('A04','15 maç tahmin kaynağı ve gerçek API alım zamanı',not issues,
               '; '.join(issues[:6]) if issues else 'Güncel API alım ve hesaplama zamanı mevcut.')
    except (KeyError,ValueError,TypeError,AttributeError) as exc:
        kaydet('A04','15 maç tahmin kaynağı ve gerçek API alım zamanı',False,exc)

    try:
        if not isinstance(raw,(bytes,bytearray)) or not isinstance(manifest_bytes,(bytes,bytearray)):
            raise ValueError('TXT/manifest yok.')
        if not (0<len(raw)<=8_000_000 and 0<len(manifest_bytes)<=200_000):
            raise ValueError('TXT veya manifest boyutu sınır dışında.')
        v17_paket_kontrol(raw,manifest_bytes)
        manifest=json.loads(manifest_bytes)
        expected=[{'order':i+1,'fixture_id':str(m['id']),
                   'match':f"{m['ev']} - {m['dep']}",'date':m['tarih'],'time':m['saat']}
                  for i,m in enumerate(maclar)]
        if manifest['matches']!=expected:
            raise ValueError('Manifest maç adları, saatleri veya sırası seçili bültenle uyuşmuyor.')
        if manifest['parameter_hash']!=str(param_imza) or not param_imza:
            raise ValueError('Üretim parametre imzası uyuşmuyor veya yok.')
        if manifest.get('mode')!='ANALYSIS_ONLY_NOT_A_BET':
            raise ValueError('Manifest güvenli analiz modunda değil.')
        kaydet('A05','TXT/manifest/SHA-256, maç sırası ve parametre bağlama',True,
               f"{manifest['columns']} benzersiz kolon; TXT SHA-256 ve sıra tutarlı.")
    except (ValueError,TypeError,KeyError,UnicodeError,OverflowError) as exc:
        manifest=None
        kaydet('A05','TXT/manifest/SHA-256, maç sırası ve parametre bağlama',False,exc)

    try:
        if not isinstance(manifest,dict): raise ValueError('Geçerli manifest yok.')
        unit=Decimal(str(kolon_fiyati)); budget=Decimal(str(butce))
        if not unit.is_finite() or not budget.is_finite() or unit<=0 or budget<0:
            raise ValueError('Fiyat veya bütçe geçersiz.')
        if Decimal(str(manifest['unit_price_assumption_tl']))!=unit or Decimal(str(manifest['budget_tl']))!=budget:
            raise ValueError('Manifest ile güncel bütçe/fiyat ayarları farklı.')
        cost=unit*int(manifest['columns'])
        if cost>budget or Decimal(str(manifest['cost_assumption_tl']))!=cost:
            raise ValueError('Bütçe sınırı aşıldı veya hesaplanan tutar tutarsız.')
        kaydet('A06','Tam TL maliyet ve bütçe kilidi',True,f'{cost} / {budget} TL (kullanıcı fiyat varsayımı).')
    except (ValueError,TypeError,KeyError,InvalidOperation,OverflowError) as exc:
        kaydet('A06','Tam TL maliyet ve bütçe kilidi',False,exc)

    try:
        if not isinstance(manifest,dict) or not isinstance(ozet,dict):
            raise ValueError('Kapsama özeti ve manifest gerekli.')
        if ozet.get('imza')!=param_imza or not ozet.get('optimizasyon',{}).get('hedef_tam',False):
            raise ValueError('Kapsama hedefi doğrulanmadı veya eski parametreler.')
        if ozet.get('esnetilenler'):
            raise ValueError('Katı filtre esnetilmiş.')
        if not manifest.get('coverage_target_met'):
            raise ValueError('Manifest kapsama hedefi başarısız.')
        key={15:'tam_15',14:'en_az_14',13:'en_az_13',12:'en_az_12'}.get(ozet.get('garanti_derecesi'))
        if key is None: raise ValueError('Geçersiz kapsama hedefi.')
        listed=ozet.get('denetim',{}).get(key)
        if listed is None or abs(float(listed)-float(ozet['optimizasyon']['kapsama_adet']))>1.1:
            raise ValueError('Seçilen senaryo evreni için kapsama raporu tutarsız.')
        if not (0<=float(listed)<=100): raise ValueError('Kapsama yüzdesi aralık dışında.')
        kaydet('A07','Şartlı evren kapsaması ve katı filtre',True,
               f'Seçilen evren %{float(listed):.2f} kapsama; gerçek sonuç garantisi değildir.')
    except (TypeError,KeyError,ValueError,OverflowError) as exc:
        kaydet('A07','Şartlı evren kapsaması ve katı filtre',False,exc)

    try:
        if not isinstance(manifest,dict) or not isinstance(ozet,dict):raise ValueError('Halk optimizasyon özeti/manifest yok.')
        w=float(ozet.get('v173_crowd_weight',0))
        if not (0<=w<=0.25) or w!=float(manifest.get('crowd_proxy_weight',0)):
            raise ValueError('Halk ağırlığı uyuşmuyor.')
        if ozet.get('v173_public_sha256')!=manifest.get('crowd_csv_sha256'):
            raise ValueError('Halk CSV özeti uyuşmuyor.')
        if w>0 and not re.fullmatch('[0-9a-f]{64}',str(manifest.get('crowd_csv_sha256',''))):
            raise ValueError('Halk CSV SHA-256 eksik.')
        kaydet('A08','Anti-Public izlenebilirliği',True,'İsteğe bağlı halk verisi/parametreler manifestle tutarlı.')
    except (TypeError,ValueError,KeyError) as exc:
        kaydet('A08','Anti-Public izlenebilirliği',False,exc)

    try:
        zero=v171_toto_0_txt(raw)
        if zero.replace(b'0',b'X')!=raw or len(zero)!=len(raw):
            raise ValueError('X/0 dönüşümü birebir geri çevrilemiyor.')
        kaydet('A09','1X2 ile 102 kolonlarının birebir dönüşümü',True,'Sıra ve kolon sayısı değiştirilmedi.')
    except (ValueError,TypeError,UnicodeError,AttributeError) as exc:
        kaydet('A09','1X2 ile 102 kolonlarının birebir dönüşümü',False,exc)

    try:
        template_audit=v18_sablon_kontrol(raw,ozet)
        kaydet('A10','Şablon üyeliği ve ham kapsama iç tutarlılığı',True,
               f"{template_audit['universe_count']} ham senaryo; {template_audit['mode']}.")
    except (ValueError,TypeError,KeyError,UnicodeError,OverflowError,AttributeError) as exc:
        template_audit=None
        kaydet('A10','Şablon üyeliği ve ham kapsama iç tutarlılığı',False,exc)

    # Aşağıdaki maddeler için bu programda bağımsız kaynak/işlem doğrulaması YOK.
    kaydet('B01','Resmî Spor Toto web içeriğinin bağımsız otantikliği',False,
           'Kullanıcı onaylı modda resmî kaynağın kimliği ve kapanışı kontrol edilmedi.' if manual_mode else 'Kullanıcıdan gelen URL, metin ve CSV resmî sayfa olduğunun kanıtı değildir.',blocking=False)
    kaydet('B02','Gerçek geçmişte kalibre edilmiş üstün tahmin başarısı',False,
           'Geniş, kaynak doğrulanmış pre-match tarihsel test ve bağımsız holdout bulunmuyor.',blocking=False)
    kaydet('B03','Bahis sitesi ekran işaretleri, fiyat ve ödeme makbuzu teyidi',False,
           'Canlı site DOM/ödeme entegrasyonu kapalı; E2E test yapılmadı.',blocking=False)
    if template_audit and template_audit.get('mode')=='EXACT_RAW_UNIVERSE_RECOMPUTED':
        kaydet('B04','Büyük ham evrenin bağımsız tam yeniden sayımı',True,
               f"{template_audit['universe_count']} ham senaryonun 12/13/14/15 tam sayımı yapıldı.",blocking=False)
    else:
        kaydet('B04','Büyük ham evrenin bağımsız tam yeniden sayımı',False,
               'Tam bağımsız sayım yok veya kontrol başarısız.',blocking=False)
    errors=[x['code']+': '+x['detail'] for x in checks if x['status']=='FAIL']
    eligible=not errors
    result={'version':'19.0 ULTIMATE FINAL ANALYSIS ONLY','scope':'ANALYSIS_ONLY',
            'checked_at_utc':now.isoformat(), 'bulletin_signature':signature,
            'manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest() if isinstance(manifest_bytes,(bytes,bytearray)) else None,
            'txt_sha256':hashlib.sha256(raw).hexdigest() if isinstance(raw,(bytes,bytearray)) else None,
            'parameter_signature':str(param_imza) if param_imza else None,
            'analysis_package_eligible':eligible,'real_money_approved':False,
            'result':'ANALYSIS_PACKAGE_ELIGIBLE_NOT_LIVE_APPROVED' if eligible else 'BLOCKED',
            'bulletin_verification_mode':'USER_ATTESTED_UNVERIFIED' if manual_mode else 'TRIPLE_INPUT_UNAUTHENTICATED',
            'official_list_verified':False,
            'official_closing_verified':False,
            'manual_attestation':kapi.get('manual_attestation') if manual_mode else None,
            'failures':errors,'checks':checks,
            'warning':'SHA-256 bütünlük kanıtıdır, resmî kaynak otantikliği veya ödeme teyidi değildir.'}
    return result


def v18_kabul_zip(raw, manifest_bytes, report):
    """Yalnız rapor PASS ise izlenebilir ANALİZ paketi oluşturur."""
    if not isinstance(report,dict) or not report.get('analysis_package_eligible') or report.get('real_money_approved') is not False:
        raise ValueError('Analiz kabul kapısı geçilmedi veya canlı kullanım iddiası var.')
    v17_paket_kontrol(raw,manifest_bytes)
    m=json.loads(manifest_bytes)
    if report.get('txt_sha256')!=hashlib.sha256(raw).hexdigest() or report.get('manifest_sha256')!=hashlib.sha256(manifest_bytes).hexdigest():
        raise ValueError('Kabul raporundaki imzalar güncel dosyalarla uyuşmuyor.')
    if report.get('parameter_signature')!=m.get('parameter_hash') or not report.get('bulletin_signature'):
        raise ValueError('Kabul parametre ve bülten imzası eksik.')
    zero=v171_toto_0_txt(raw)
    data={'KOLONLAR_ANALIZ_1X2.txt':bytes(raw),
          'KOLONLAR_SPORTOTO_102_INCELEME.txt':zero,
          'BULTEN_MANIFEST.json':bytes(manifest_bytes),
          'KABUL_RAPORU.json':json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True).encode('utf-8')}
    checks={'format':'SHA256_FILE_INTEGRITY_NOT_ORIGIN_AUTHENTICATION','sha256':{k:hashlib.sha256(v).hexdigest() for k,v in data.items()}}
    data['DOSYA_BUTUNLUK.json']=json.dumps(checks,ensure_ascii=False,indent=2,sort_keys=True).encode('utf-8')
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,payload in data.items():z.writestr(name,payload)
    return out.getvalue()


def v18_zip_kontrol(zip_bytes):
    """Disk üstündeki ZIP'in kapalı şemalı dosya bütünlüğü kontrolü; resmî belge değil."""
    if not isinstance(zip_bytes,(bytes,bytearray)) or len(zip_bytes)<300 or len(zip_bytes)>16_000_000:
        raise ValueError('ZIP boyutu geçersiz.')
    expected=set(V18_DOSYALAR)|{'DOSYA_BUTUNLUK.json'}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        members=z.infolist()
        if len(members)!=5 or [x.filename for x in members]!=list(V18_DOSYALAR)+['DOSYA_BUTUNLUK.json']:
            raise ValueError('Dosya listesi/sırası, tekrarlar veya harici dosyalar geçersiz.')
        if any(x.is_dir() or x.file_size>8_000_000 for x in members) or sum(x.file_size for x in members)>17_000_000:
            raise ValueError('Açılmış dosya boyutu güvenli sınır dışında.')
        data={x.filename:z.read(x.filename) for x in members}
    check=json.loads(data['DOSYA_BUTUNLUK.json'])
    if not isinstance(check,dict):raise ValueError('Bütünlük JSON nesnesi gerekli.')
    if check.get('format')!='SHA256_FILE_INTEGRITY_NOT_ORIGIN_AUTHENTICATION' or set(check.get('sha256',{}))!=set(V18_DOSYALAR):
        raise ValueError('Bütünlük şeması geçersiz.')
    if any(hashlib.sha256(data[name]).hexdigest()!=check['sha256'][name] for name in V18_DOSYALAR):
        raise ValueError('ZIP dosya içerikleri SHA-256 kontrolünden geçmedi.')
    txt=data['KOLONLAR_ANALIZ_1X2.txt']; manifest_bytes=data['BULTEN_MANIFEST.json']
    v17_paket_kontrol(txt,manifest_bytes)
    if v171_toto_0_txt(txt)!=data['KOLONLAR_SPORTOTO_102_INCELEME.txt']:
        raise ValueError('102 dosyası 1X2 dosyasıyla eşleşmiyor.')
    report=json.loads(data['KABUL_RAPORU.json']); m=json.loads(manifest_bytes)
    if not isinstance(report,dict) or report.get('result')!='ANALYSIS_PACKAGE_ELIGIBLE_NOT_LIVE_APPROVED' or report.get('real_money_approved') is not False:
        raise ValueError('Raporda desteklenmeyen kullanım iddiası var.')
    if not isinstance(report.get('checks'),list) or any(not isinstance(v,dict) for v in report['checks']):
        raise ValueError('Kabul raporu kontrol listesi geçersiz.')
    if not report.get('analysis_package_eligible') or any(v.get('status')=='FAIL' for v in report['checks']):
        raise ValueError('Kabul raporu analiz için başarısız.')
    cmap={v.get('code'):v.get('status') for v in report['checks']}
    if report.get('bulletin_verification_mode')=='USER_ATTESTED_UNVERIFIED':
        att=report.get('manual_attestation')
        if not isinstance(att,dict) or att.get('declaration')!=V1802_BEYAN or att.get('match_signature')!=report.get('bulletin_signature'):
            raise ValueError('Analiz ZIP kullanıcı beyanı eksik veya bülten imzası farklı.')
        if cmap.get('A02')!='USER_ACCEPTED' or cmap.get('A03')!='USER_ACCEPTED' or report.get('official_list_verified') is not False or report.get('official_closing_verified') is not False:
            raise ValueError('Kullanıcı beyanı modunda resmî doğrulama iddia edilemez.')
    elif report.get('bulletin_verification_mode') not in (None,'TRIPLE_INPUT_UNAUTHENTICATED'):
        raise ValueError('Bilinmeyen bülten doğrulama modu.')
    if report.get('manifest_sha256')!=hashlib.sha256(manifest_bytes).hexdigest() or report.get('txt_sha256')!=hashlib.sha256(txt).hexdigest():
        raise ValueError('Kabul raporu TXT veya manifestle uyuşmuyor.')
    if report.get('parameter_signature')!=m.get('parameter_hash'):
        raise ValueError('Parametre imzaları tutarsız.')
    if m.get('independent_audit_required'):
        audit181=v181_audit_archive(zip_bytes)
        if audit181.get('mismatches'):
            raise ValueError('Tam matematiksel sayım paket iddiasıyla eşleşmiyor.')
    return {'status':'OFFLINE_INTEGRITY_OK_NOT_OFFICIAL_AUTHENTICATED','columns':m['columns'],
            'txt_sha256':m['txt_sha256'],'matches':len(m['matches']),
            'analyzed_at':report.get('checked_at_utc')}

st.markdown("### 🏆 Spor Toto AI Pro — Kolay Kullanım")
_secili = len(st.session_state.secilen_15_mac)
_analiz_var = st.session_state.analiz_verisi is not None
_kolon_var = st.session_state.uretilen_kuponlar is not None and len(st.session_state.uretilen_kuponlar) > 0
st.caption(f"Durum: {_secili}/15 maç seçildi  •  Analiz: {'Hazır' if _analiz_var else 'Bekliyor'}  •  Kolonlar: {'Hazır' if _kolon_var else 'Henüz yok'}")
st.info("**Kısa yol:** 15 maç seç → **Analizi Başlat** → **Bütçeme Göre Otomatik Kur** → **KAPSAMA HESAPLA** → üstteki bülten onayını tamamla → **2. Dosyaları İndir**. Sonuçlar için 3. sekmeyi açın.")

# Günlük işler 3 sekmede. Diğer 5 özgün bölüm silinmedi; yalnız ileri araçlara taşındı.
tab_uretim, tab_acceptance, tab_takip = st.tabs([
    "⚽ 1. Maçlar ve Kolonlar",
    "📥 2. Dosyaları İndir",
    "📡 3. Sonuç Takibi"
])
with st.expander("🔬 GELİŞMİŞ ARAÇLAR — teknik inceleme, önizleme ve testler", expanded=False):
    tab_txt153, tab_otomasyon, tab_backtest, tab_antipublic, tab_math181 = st.tabs([
        "📋 TXT Önizleme",
        "🛡️ İşlem Kayıtları",
        "🧪 Geçmiş Tahmin Testleri",
        "🧠 Anti-Public",
        "🧮 Bağımsız Matematik Denetimi"
    ])

# ------------------------------------------------------------------------------
# SEKME 1: PROFESYONEL MAÇ KONTROL PANELİ VE SENDİKA MOTORU
# ------------------------------------------------------------------------------
guncel_uretim_imzasi = None
public173_ctx=None
v173_active_weight=0.0
with tab_uretim:
    with st.expander('✅ BÜLTEN ONAYI — 15 maç seçtikten sonra tamamlayın',expanded=(len(st.session_state.secilen_15_mac)==15)):
        st.warning('Bu uygulama resmî bülteni, resmî kapanışı veya ödeme işlemini bağımsız doğrulayamaz. Otomatik oynama ve ödeme kapalıdır.')
        v1802_mode=st.radio('Bülten kabul yöntemi',
            ['Benim liste onayım (CSV/metin/API zorunlu değil)', 'Eski üçlü karşılaştırma (CSV + metin + API)'],
            index=0,key='v1802_mode_selector',horizontal=False)
        if v1802_mode.startswith('Benim'):
            st.info('Kullanıcı beyanı yalnız analiz dosyalarını açar; resmî liste ve kapanış DOĞRULANMIŞ sayılmaz.')
            matchlist17=st.session_state.secilen_15_mac
            if len(matchlist17)==15:
                st.dataframe(pd.DataFrame([{'Sıra':i+1,'Maç':f"{m['ev']} - {m['dep']}",
                    'Tarih':m['tarih'],'Saat':m['saat']} for i,m in enumerate(matchlist17)]),
                    hide_index=True,use_container_width=True,height=300)
                v1802_checked=st.checkbox('15 maçın tamamını ve sırasını ben kontrol ettim. Resmî doğrulama ve kapanış teyidi yapılmadığını kabul ediyorum.',
                    value=False,key='v1802_ack_checkbox')
                if st.button('✅ Bu bülten için onayımı kaydet',key='v1802_ack_button'):
                    if not v1802_checked:
                        st.error('Onay kutusu işaretlenmeden beyan kaydedilemez.')
                    else:
                        st.session_state['v1802_attestation']={
                            'declaration':V1802_BEYAN,
                            'match_signature':v171_mac_imzasi(matchlist17),
                            'attested_at':pd.Timestamp.now(tz='UTC').isoformat(),
                            'scope':'ANALYSIS_ONLY','official_verified':False}
                        st.success('Beyan kaydedildi; yalnız analiz dosyaları için geçerlidir.')
                v171_current_gate=v1802_onay_kapisi(
                    matchlist17,st.session_state.analiz_verisi,
                    st.session_state.get('v1802_attestation'))
                if v171_current_gate['ok']:
                    st.success('Kullanıcı onayı geçerli. CSV/metin/ek API sorgusu gerekmiyor. Resmî kapanış hâlâ bilinmiyor.')
                else:
                    st.warning('Analiz kabulü için: '+ '; '.join(v171_current_gate['issues'][:3]))
            else:
                v171_current_gate={'ok':False,'mode':'USER_ATTESTED','issues':['15 maç seçilmedi.']}
        else:
            st.warning('Güvenlik sınırı: Bu kontrollerin HİÇBİRİ resmî web sitesi adına işlem, makbuz onayı veya bağımsız kaynak otantikliği sağlamaz. Otomatik oynama kapalıdır.')
            st.markdown('[Spor Toto Teşkilatının resmî haftalık maç listesi](https://www.sportoto.gov.tr/spor-toto-listeler) — önce bu sayfadan 15 maçı ve resmî kapanışı kontrol edin.')
            st.caption('Resmî listeden elle kopyalanmış 15 satırı 1. Ev Sahibi - Deplasman şeklinde aşağıya yazın. Bu giriş, CSV/API kayıtlarından bağımsız olarak maç sırasını sınamak içindir.')
            matchlist17=st.session_state.secilen_15_mac
            v171_manual=st.text_area('Resmî sayfadan bağımsız alınan 15 maç listesi',key='v171_official_manual',height=135,
                                     placeholder='1. Galatasaray - Fenerbahçe\n2. Beşiktaş - Trabzonspor\n...')
            st.caption('CSV sütunları: bulletin_id,order,fixture_id,home,away,starts_at,closes_at,source_url,obtained_at. Tüm zamanlar +03:00 veya Z içermeli.')
            user_bulten17=st.file_uploader('Bülten karşılaştırma CSV',type=['csv'],key='v171_bulletin_uploader')
            if len(matchlist17)==15:
                rows17=[{'bulletin_id':'', 'order':i+1,'fixture_id':str(m['id']),
                         'home':m['ev'],'away':m['dep'],
                         'starts_at':f"{m['tarih']}T{m['saat']}:00+03:00",
                         'closes_at':'','source_url':'https://www.sportoto.gov.tr/spor-toto-listeler','obtained_at':''} for i,m in enumerate(matchlist17)]
                st.download_button('⬇️ Boş karşılaştırma CSV şablonu',
                    pd.DataFrame(rows17).to_csv(index=False).encode('utf-8-sig'),
                    file_name='SPOR_TOTO_V172_BULTEN_SABLONU.csv',mime='text/csv')
                st.caption('CSV API listesinden oluşturulur; bağımsız kanıt DEĞİLDİR. Kapanışı, tarihleri ve takım isimlerini resmî kaynaktan karşılaştırın.')
                if api_key and st.button('🔄 API-Football 15 maçı YENİDEN canlı kontrol et',key='v171_api_revalidate'):
                    try:
                        ids17='-'.join(str(m['id']) for m in matchlist17)
                        resp17=api_istegi_at(f'https://v3.football.api-sports.io/fixtures?ids={ids17}',api_key,timeout=12)
                        st.session_state.v171_api_proof=v171_api_fikstur_tekrar_kontrol(resp17,matchlist17)
                        st.success('API tekrar sorgusu: 15/15 isim, sıra, saat, statü aynı. Bu resmî Spor Toto bültenini doğrulamaz.')
                    except Exception as exc:
                        st.session_state.v171_api_proof=None
                        st.error('Fikstür kontrolü başarısız: '+str(exc))
            else:
                st.info('Bülten çapraz kontrolü için önce 15 maç seçin.')
            if len(matchlist17)==15:
                _now171=pd.Timestamp.now(tz='UTC')
                v171_current_gate=v171_bagimsiz_kontrol_kapisi(
                    user_bulten17.getvalue() if user_bulten17 else b'',v171_manual,matchlist17,
                    st.session_state.get('v171_api_proof'),st.session_state.analiz_verisi,simdi=_now171)
                v172_source_issues = v172_source_quality(st.session_state.analiz_verisi,simdi=_now171)
                if v172_source_issues:
                    v171_current_gate['issues'].extend(v172_source_issues)
                    v171_current_gate['ok']=False
                    v171_current_gate['status']='BLOCKED'
                if v171_current_gate['ok']:
                    st.success('✅ Kullanıcı CSV + bağımsız metin + güncel API + tahmin kayıtları birbiriyle tutarlı. RESMÎ KAYNAĞIN OTANTİKLİĞİ DOĞRULANMADI.')
                else:
                    st.warning(f"Denetimli analiz paketi kilitli: {len(v171_current_gate['issues'])} kontrol uyarısı.")
                    with st.expander('Kontrol ayrıntıları'):
                        for message in v171_current_gate['issues'][:25]:st.write('• '+message)
            else:
                v171_current_gate={'ok':False,'issues':['15 maç seçilmedi.']}
    if not api_key and st.session_state.analiz_verisi is None:
        st.info("👈 Başlamak için sol menüden **API-Football Anahtarınızı** girin veya kayıtlı **.JSON** oturumunuzu yükleyin.")
    else:
        acik_kal = st.session_state.analiz_verisi is None
        with st.expander("⚡ ADIM 1: Bülten Maçlarını Seçin veya Yapıştırın (Önbellek Korumalı)", expanded=acik_kal):
            bugun = datetime.now(ZoneInfo("Europe/Istanbul")).date()
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
                    elif isinstance(tarih_araligi, (tuple, list)) and len(tarih_araligi) == 2:
                        try:
                            yeniler = tarih_araligi_maclarini_getir(tarih_araligi[0], tarih_araligi[1], api_key, sadece_toto)
                        except ValueError as exc:
                            st.error(str(exc))
                        else:
                            st.session_state.mac_listesi = yeniler
                            mac_secimi_senkronize_v161()
                            st.session_state["bulten_onay14"] = False
                            # Yeni havuzdan seçim değiştiyse eski kuponların yanlış bültene aktarılmasını önle.
                            st.session_state.analiz_verisi = None
                            st.session_state.tablo_baz_df = None
                            st.session_state.tablo_df = None
                            st.session_state.uretilen_kuponlar = None
                            st.session_state.son_uretim_ozeti = None
                            st.session_state.son_param_imzasi = None
                            st.session_state.son_sol_menu_imzasi = None
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
                    st.session_state["bulten_onay14"] = False
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
                mac_secimi_senkronize_v161()
                col_sol, col_sag = st.columns([1.05, 2.25])
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
                            st.session_state["bulten_onay14"] = False
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
                    st.markdown("#### 🎯 Maçları Tek Tıkla Ekle")
                    st.caption("Bir karşılaşmanın yanındaki **➕ Ekle** düğmesine bir kez basın. Listeye hemen eklenir; seçimler bülten sırasıyla saklanır.")
                    arama = st.text_input("🔎 Karşılaşma veya lig ara", key="mac_ara_v161", placeholder="Takım adı, maç veya lig yazın...")
                    arama_norm = metin_temizle(arama)
                    aramaya_uyan = [m for m in st.session_state.mac_listesi
                                    if not arama_norm or arama_norm in metin_temizle(m["label"])]
                    secili_idler = {int(m["id"]) for m in st.session_state.secilen_15_mac}
                    adaylar = [m for m in aramaya_uyan if int(m["id"]) not in secili_idler]
                    st.caption(f"Havuz: {len(st.session_state.mac_listesi)} maç | Arama sonucu: {len(adaylar)} eklenebilir | Seçili: {len(secili_idler)}/15")
                    if len(adaylar)>12:
                        st.caption("İlk 12 karşılaşma gösteriliyor. Diğerlerini bulmak için takım/lig adıyla arayın.")
                    with st.container(height=285, border=True):
                        if not adaylar:
                            st.info("Eklenecek maç bulunamadı veya tüm eşleşmeler seçildi.")
                        for m in adaylar[:12]:
                            mac_yazi, mac_buton = st.columns([5.5, 1.2], vertical_alignment="center")
                            mac_yazi.write(m["label"])
                            mac_buton.button("➕ Ekle", key=f"mac_ekle_v161_{m['id']}",
                                              disabled=(len(secili_idler)>=15),use_container_width=True,
                                              on_click=mac_ekle_v161,args=(m["id"],))
                    with st.expander(f"✅ Seçilen maçlar ve sıraları ({len(st.session_state.secilen_15_mac)}/15)", expanded=True):
                        if not st.session_state.secilen_15_mac:
                            st.caption("Henüz maç eklenmedi.")
                        else:
                            for sec_no, m in enumerate(st.session_state.secilen_15_mac, 1):
                                sec_yazi, sil_buton = st.columns([6,1],vertical_alignment="center")
                                sec_yazi.write(f"{sec_no}. {m['karsilasma']} ({m['tarih']} {m['saat']})")
                                if sil_buton.button("✕", key=f"mac_cikar_v161_{m['id']}",
                                                    help="Bu maçı listeden çıkar",use_container_width=True):
                                    mac_cikar_v161(m["id"])
                                    st.rerun()
                    s_sayi = len(st.session_state.secilen_15_mac)
                    sira_onayi=st.checkbox("15 maçın resmî bülten sırasını kontrol ettim",key="bulten_onay14")
                    b_col1, b_col2 = st.columns([2, 1.2])
                    with b_col1:
                        if s_sayi == 15:
                            st.info('15/15 maç seçildi. Resmî bülten doğrulaması ayrı bir işlemdir; analiz başlatılabilir.')
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
        # ADIM 2: PROFESYONEL SENDİKA KONTROL PANELİ (v16.1 MOTOR)
        # ======================================================================
        if st.session_state.analiz_verisi:
            veriler = st.session_state.analiz_verisi
            with st.expander("Kaynak kalitesi ve veri uyarıları",expanded=False):
                st.dataframe(pd.DataFrame([{k:v.get(k) for k in ('mac','kaynak','buro_sayisi','snapshot_utc','veri_uyarilari')} for v in veriler]))
            _q17=v17_tahmin_kalitesi(veriler) + v172_source_quality(veriler)
            if _q17:
                st.error(f"TAHMİN GÜNCELLİK/KAYNAK UYARISI: {len(_q17)} kontrol başarısız. "
                         "Bu uyarı eski oturum tahminleri veya eski API veri alımı nedeniyle olabilir; "
                         "analiz yapılabilir ama denetimli paket kapalıdır.")
                with st.expander('⚠️ Uyarı ayrıntıları ve çözümü',expanded=False):
                    for issue in _q17[:30]:st.write('• '+issue)
                    st.caption('Tahmin snapshot’ı hesaplama saati; API alım saati ayrı kaydedilir. Yenileme API kotası tüketebilir.')
                if st.button('🔄 15 MAÇIN TAHMİNLERİNİ API’DEN YENİDEN ÇEK VE HESAPLA',
                             key='v172_refresh_analysis',type='primary',use_container_width=True,
                             disabled=(not api_key or len(st.session_state.secilen_15_mac)!=15)):
                    try:
                        tek_mac_analiz_cek.clear()
                        recalculated=hibrit_tahminleri_al(st.session_state.secilen_15_mac,api_key)
                        problems=v17_tahmin_kalitesi(recalculated)+v172_source_quality(recalculated)
                        if problems:raise ValueError('Yenileme kaynaksız/eksik: '+' | '.join(problems[:4]))
                    except Exception as exc:
                        st.error(f'Tahmin yenilenemedi, eski kayıtlar değiştirilmedi: {exc}')
                    else:
                        st.session_state.analiz_verisi=recalculated
                        # Eski kuponlar ve düzenlenmiş tablo ASLA yeni olasılığa taşınmaz.
                        st.session_state.tablo_baz_df=None
                        st.session_state.tablo_df=None
                        st.session_state.tablo_versiyon+=1
                        st.session_state.uretilen_kuponlar=None
                        st.session_state.son_uretim_ozeti=None
                        st.session_state.son_param_imzasi=None
                        st.session_state.son_sol_menu_imzasi=None
                        st.session_state.v171_api_proof=None
                        st.session_state.v172_restore_notice=''
                        st.toast('Yeni API veri alımıyla 15 tahmin yenilendi. Eski şablon/kuponlar sıfırlandı; bülteni yeniden doğrulayın.')
                        st.rerun()
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

            st.markdown("#### 🎯 Kupon Şablonunu Oluştur")
            st.caption("Önerilen kolay yöntem: önce bütçenize göre otomatik şablon kurun, sonra aşağıdaki 'KAPSAMA HESAPLA' düğmesine basın.")
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
            with st.expander("⚙️ Diğer şablon yöntemleri (isteğe bağlı)", expanded=False):
                tb1, tb2, tb3, tb4 = st.columns(4)
                with tb1:
                    if st.button("🌱 Ekonomik (5B-6Ç-4K)", use_container_width=True):
                        yeni_df = tablo_verisi_olustur(veriler, on_limitler, tuzak_koruma, mod="super_eko_5b_6c_4k")
                        st.session_state.tablo_baz_df = yeni_df.copy()
                        st.session_state.tablo_df = yeni_df.copy()
                        st.session_state.tablo_versiyon += 1
                        st.session_state.son_param_imzasi = None
                        st.rerun()
                with tb2:
                    if st.button("🤖 AI Dinamik (sabit banko yok)", use_container_width=True):
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
                    if st.button("🔒 Banko stres testi (risk veto)", use_container_width=True):
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
                    "Halk (%)": None,
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
            olasilik_hata_satirlari=[]
            for _, _pr in sirali.iterrows():
                try:
                    _pv=np.asarray([float(_pr[c]) for c in ("1 (%)","X (%)","2 (%)")],float)
                    if not np.isfinite(_pv).all() or np.any(_pv < 1) or abs(_pv.sum()-100)>0.5:
                        olasilik_hata_satirlari.append(str(_pr["Sıra"]))
                except (ValueError,TypeError):
                    olasilik_hata_satirlari.append(str(_pr["Sıra"]))
            oran_hatasi_var=bool(olasilik_hata_satirlari)
            if oran_hatasi_var:
                st.error('Yüzde toplamı 100 olmayan maçlar: '+', '.join(olasilik_hata_satirlari)+' — değerleri düzeltmeden yeni kolon hesaplanamaz.')

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
                h1, hx, h2 = y1, yx, y2
                kaynak_m = id_analiz_haritasi.get(int(r["ID"]), {})
                piyasa_std_val = kaynak_m.get("piyasa_std", 0.0)
                tuzak_farki_val = 0.0

                g_sablon.append(sec if sec else ["1"])
                s_veriler.append({
                    "id": int(r["ID"]),
                    "mac": r["Karşılaşma"],
                    "tarih": kaynak_m.get("tarih"), "saat": kaynak_m.get("saat"),
                    "1": y1, "X": yx, "2": y2,
                    "h1": h1, "hX": hx, "h2": h2,
                    "tuzak_farki": tuzak_farki_val,
                    "piyasa_std": piyasa_std_val
                })

            with st.expander("🧠 Banko Riski & Halk Tercihi — Sayısal İnceleme", expanded=False):
                st.caption("Model olasılığı, halk tercihi ve matematiksel kapsama farklı kavramlardır. Bu ekran kazanç veya ikramiye tahmini yapmaz; mevcut şablonu değiştirmez.")
                public_file16=st.file_uploader("İsteğe bağlı halk tercihleri CSV (gerçek, maç bazlı)",type=["csv"],key="public16")
                st.download_button("Halk verisi boş CSV şablonu", "fixture_id,h1,hx,h2,source,snapshot\n"+"".join(f"{v['id']},,,,,\n" for v in s_veriler), "halk_verisi_sablon.csv",mime="text/csv",key="public_template16")
                public16={}
                if public_file16 is not None:
                    try: public16=halk_verisi_oku16(public_file16,[v['id'] for v in s_veriler])
                    except Exception as exc: st.error(f"Halk verisi kullanılmadı: {exc}")
                if public_file16 is not None:
                    try:
                        _kickoffs173=[]
                        _selected173={int(m['id']):m for m in st.session_state.secilen_15_mac}
                        for v in s_veriler:
                            _mm=_selected173[int(v['id'])]
                            _kickoffs173.append(pd.Timestamp(f"{_mm['tarih']}T{_mm['saat']}:00+03:00"))
                        public173_ctx=v173_halk_dogrula(public_file16.getvalue(),
                            [v['id'] for v in s_veriler],kickoff_times=_kickoffs173)
                    except Exception as exc:
                        public173_ctx={'ok':False,'issues':[str(exc)]}
                        st.warning('Anti-Public optimizasyonu devre dışı: '+str(exc))
                if v173_opt_in and public173_ctx is not None and public173_ctx.get('ok'):
                    v173_active_weight=v173_weight
                    st.success('15 maçlık halk CSV biçimsel denetimi geçti. Kaynak bağımsız doğrulanmadı; ağırlık deneyseldir.')
                elif v173_opt_in:
                    st.error('Anti-Public istendi ancak tam/güncel 15 maçlık CSV yok. Yeni kolon üretimi kilitlenecek.')
                if not public16: st.info("Gerçek halk tercihi verisi yok. Farklar hesaplanmadı; tahmini halk yüzdeleri gerçek veri olarak gösterilmez.")
                else: st.warning(f"{len(public16)}/15 maç için kullanıcının sağladığı oranlar var. Kaynak ve maç öncesi olma durumu bağımsız doğrulanmadı.")
                risk_rows16=[]; banko_probs16=[]; cover_probs16=[]; fav_probs16=[]
                for i,(v,selected) in enumerate(zip(s_veriler,g_sablon)):
                    src=id_analiz_haritasi.get(v['id'],{})
                    info=banko_risk16({**src,**v},selected,public16.get(v['id']),risk_banko_p,risk_gap,risk_spread)
                    if len(selected)==1: banko_probs16.append(info['p'])
                    cover_probs16.append(info['covered']);fav_probs16.append(float(max(info['p_all'])))
                    risk_rows16.append({"No":i+1,"Maç":v['mac'],"Seçimler":"/".join(selected),"İncelenen sonuç":info['incelenen'],"Model %":round(100*info['p'],1),"Halk %":None if info['halk'] is None else round(100*info['halk'],1),"Halk − model (puan)":None if info['gap'] is None else round(info['gap'],1),"Entropi":round(info['entropy'],3),"İlk iki farkı":round(info['margin'],1),"Şablon kapsamı %":round(100*info['covered'],1),"Kaynak":public16.get(v['id'],{}).get('source','—'),"Kayıt zamanı":public16.get(v['id'],{}).get('snapshot','—'),"İnceleme":"; ".join(info['reasons']) or "Eşik uyarısı yok"})
                st.dataframe(pd.DataFrame(risk_rows16),hide_index=True,use_container_width=True)
                bdist16=banko_hata_dagilimi16(banko_probs16)
                a16,b16,c16=st.columns(3)
                a16.metric("Seçili banko",len(banko_probs16)); b16.metric("En az bir banko hatası (model)",f"%{100*(1-bdist16[0]):.1f}" if banko_probs16 else "—")
                c16.metric("Tüm şablonun model kütlesi",f"%{100*np.prod(cover_probs16):.3f}" if not bos_mac_var else "—")
                fdist16=banko_hata_dagilimi16(fav_probs16)
                with st.expander("Banko/favori hata olasılıkları — sayısal tablo", expanded=False):
                    hata_uzunlugu = max(len(bdist16), len(fdist16))
                    hata_tablosu = pd.DataFrame({
                        "Hata sayısı": range(hata_uzunlugu),
                        "Banko hatası model %": [round(100*bdist16[i],2) if i<len(bdist16) else None for i in range(hata_uzunlugu)],
                        "Favori dışı sonuç model %": [round(100*fdist16[i],2) if i<len(fdist16) else None for i in range(hata_uzunlugu)]
                    })
                    st.dataframe(hata_tablosu,hide_index=True,use_container_width=True,height=300)
                st.caption("Tablo maçların bağımsız olduğu varsayımına dayanır; modeller kalibre edilmediyse yüzdeler gerçekleşme frekansı değildir. Halk oranı, beklenen kâr veya gerçek maç olasılığı garantisi değildir.")
                st.download_button("Risk incelemesini indir (CSV)",pd.DataFrame(risk_rows16).to_csv(index=False).encode('utf-8-sig'),"SPOR_TOTO_V17_RISK.csv",mime="text/csv",key="risk_export16")

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
                "v173_public_sha":(public173_ctx or {}).get('sha256'),
                "v173_opt_in":v173_opt_in,"v173_weight":v173_weight,
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
                "sol_menu_imzasi": sol_menu_imzasi,
                "v173_public_sha":(public173_ctx or {}).get('sha256'),
                "v173_active_weight":v173_active_weight
            }, sort_keys=True)
            param_imzasi = hashlib.md5(imza_ham.encode("utf-8")).hexdigest()
            degisiklik_bekliyor = (st.session_state.get("son_param_imzasi") != param_imzasi)
            if not bos_mac_var and not sira_hatasi_var and not oran_hatasi_var and ham_kolon_sayisi <= 300_000:
                guncel_uretim_imzasi = param_imzasi

            v173_blocked=bool(v173_opt_in and not (public173_ctx or {}).get('ok'))
            if v173_blocked:st.error('❌ Anti-Public modu etkin fakat geçerli 15 maç halk verisi yok: sistem yeni kolon üretmez.')
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
                    disabled=(bos_mac_var or sira_hatasi_var or oran_hatasi_var or v173_blocked or ham_kolon_sayisi > 300_000)
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

            otomatik_hizli_yenile = (
                aninda_otomatik_hesapla
                and (degisiklik_bekliyor or sol_menu_degisti)
                and not bos_mac_var
                and not sira_hatasi_var
                and not v173_blocked
                and ham_kolon_sayisi <= 4000
            )
            ilk_acilis_uretim = (
                st.session_state.uretilen_kuponlar is None
                and not bos_mac_var
                and not sira_hatasi_var
                and not v173_blocked
                and ham_kolon_sayisi <= 4000
            )

            if degisiklik_bekliyor or bos_mac_var or sira_hatasi_var or oran_hatasi_var or v173_blocked or ham_kolon_sayisi > 300_000 or max_kolon_limiti == 0:
                if degisiklik_bekliyor:
                    st.session_state.yatirilan_paketler = []
                    st.session_state.paket_konfig_v161 = None
                st.session_state.uretilen_kuponlar = None
                st.session_state.son_uretim_ozeti = None
            if max_kolon_limiti == 0:
                st.info("Sıfır bütçe: aktif kolon yok.")
            if max_kolon_limiti != 0 and not bos_mac_var and not sira_hatasi_var and not oran_hatasi_var and not v173_blocked and ham_kolon_sayisi<=300_000 and (uretim_tetikle or otomatik_hizli_yenile or (ilk_acilis_uretim and not st.session_state.get('son_param_imzasi'))):
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
                        kati_filtre=kati_filtre_kilidi,
                        public_prob=(np.array([public173_ctx['data'][v['id']]['q'] for v in s_veriler],float)
                                     if v173_active_weight>0 and public173_ctx and public173_ctx.get('ok') else None),
                        crowd_strength=v173_active_weight
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
                            "esnetilenler": esnetilenler,
                            "v173_public_sha256":(public173_ctx or {}).get('sha256') if v173_active_weight>0 else None,
                            "v173_crowd_weight":v173_active_weight,
                            "v173_note":"Crowd proxy is not payout, EV, or true joint popularity"
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
                elif not degisiklik_bekliyor: st.success('Tanımlı senaryo evreninde kapsama hedefi doğrulandı. Bu gerçek müsabaka sonucunu veya ikramiyeyi garanti etmez.')
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
                        f"✂️ **Ekonomik Sıkıştırma Kazancı:** Ters budama ile **{ozet.get('budanan_adet', 0)}** kolon, "
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
                m2.metric(f"🎯 {ozet['garanti_derecesi']} isabet hedefi", f"{len(garanti):,} Kolon", f"%{tasarruf_orani:.1f} Toplam Tasarruf")
                m3.metric("Kolon maliyeti (varsayılan fiyat)", f"{len(garanti) * kolon_fiyati:,.0f} TL", f"Kapsama: %{ozet.get('kapsama', 100):.1f}")
                m4.metric("🥇 Şablon İçi 14+ Gücü", f"%{mc['sablon_14_arti']:.1f}", f"Tam 15: %{mc['sablon_15']:.1f}")
                m5.metric("Simülasyon: 12+", f"%{mc['genel_12_arti']:.1f}", "Tahmin; gerçekleşmiş başarı değil")
                with m6:
                    st.write("")
                    st.info('TXT + imza denetimi için 2. Dosyaları İndir bölümünü kullanın.')

                st.caption(
                    f"🔬 **Deterministik Senaryo Kapsama Denetimi:** "
                    f"**Ham Şablon Evreni ({ozet['ham_adet']:,} senaryo):** "
                    f"Tam 15: **%{denetim_ham['tam_15']:.1f}** | En Az 14: **%{denetim_ham['en_az_14']:.1f}** | "
                    f"En Az 13: **%{denetim_ham['en_az_13']:.1f}** | En Az 12: **%{denetim_ham['en_az_12']:.1f}**  —  "
                    f"**Seçili Hedef Evren ({ozet['filtreli_adet']:,} senaryo):** "
                    f"Tam 15: **%{denetim['tam_15']:.1f}** | En Az 14: **%{denetim['en_az_14']:.1f}** | En Az 13: **%{denetim['en_az_13']:.1f}**"
                )

                with st.expander("Kuponların Maç Bazlı 1-X-2 Dağılımı — Sayısal Tablo", expanded=False):
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
        st.caption("⚠️ Erteleme/iptal, otomatik 'kura' değildir. Kura seçeneğini yalnızca resmî Spor Toto kararı doğrulandıktan sonra elle işaretleyin.")
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
                    with st.expander(f"Kalan {len(bekleyen_indeksler)} Maç: {en_yuksek_derece} Adayı İçin Açık Sonuç Analizi", expanded=False):
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
# SEKME 3: B SİSTEMİNDEN ENTEGRE EDİLEN GÜVENLİ & KOLAY OTOMATİK KUPON YATIRMA MERKEZİ
# ------------------------------------------------------------------------------
with tab_otomasyon:
    st.subheader('🛡️ v19.0 — Kupon İnceleme ve Kullanıcı İşlem Kayıtları')
    st.error('CANLI SİTE OTOMASYONU KAPALI. v16.1 bookmarklet / F12 tıklayıcı güvenli bulunmadığı için kaldırıldı. Bu ekran hiçbir sitede işaretleme, giriş, ödeme veya bahis gönderimi yapmaz.')
    st.caption('Kayıtlar yalnızca kullanıcı beyanıdır; gerçek satın alım ispatı değildir. Resmî makbuz doğrulaması yapılmaz.')
    output17=st.session_state.uretilen_kuponlar
    summary17=st.session_state.son_uretim_ozeti
    if output17 is None or len(output17)==0 or not isinstance(summary17,dict):
        st.info('Önce 1. sekmede analiz kuponlarını oluşturun.')
    else:
        try:
            paket_raw17,paket_m17,paket_zip17,paket_info17=v17_paket_uret(
                output17,summary17,guncel_uretim_imzasi,st.session_state.secilen_mac_idleri,
                summary17['s_veriler'],kolon_fiyati,hedef_butce_tl,strict=True)
            v17_paket_kontrol(paket_raw17,paket_m17)
        except Exception as exc:
            st.warning(f'Doğrulanmış analiz paketi oluşturulamıyor: {exc}')
        else:
            st.success(f"Analiz paketi: {paket_info17['columns']} tekil kolon, {len(paket_info17['matches'])} maç. SHA-256: {paket_info17['txt_sha256'][:20]}…")
            st.info('v19.0: Bu sekme yalnız önizleme ve kullanıcı beyanı kayıtları içindir. Tüm kolon indirmeleri 2. Dosyaları İndir bölümündeki kabul kontrollerinden sonradır.')
            st.dataframe(pd.DataFrame([{'Sıra':x['order'],'Maç':x['match'],'API ID':x['fixture_id']} for x in paket_info17['matches']]),hide_index=True,use_container_width=True)
            st.info('v19.0: Denetimli ZIP ve tek TXT dosyaları yalnızca 2. Dosyaları İndir bölümünden indirilir.')
            st.info('Yatırma kararı veriyorsanız resmî site/işlem detaylarıyla 15 satır, her kolon, tutar ve misli manuel teyit edilmelidir. Bu uygulama işlemin kabul edildiğini iddia etmez.')
            with st.expander('🧾 Elle kaydedilen işlem referansları (doğrulanmamış)',expanded=False):
                receipt17=st.text_input('Resmî makbuz / işlem referansı (kendi kaydınız)',key='v17_receipt_input')
                amount17=st.number_input('Makbuzda görünen tutar (TL)',min_value=0.,value=0.,step=1.,key='v17_receipt_amount')
                if st.button('Kullanıcı beyanı olarak kaydet',key='v17_save_receipt'):
                    if not receipt17.strip(): st.error('Referans boş olamaz.')
                    elif amount17<=0: st.error('Makbuz tutarı pozitif olmalı.')
                    elif receipt17.strip() in st.session_state.v17_receipts: st.error('Mükerrer işlem referansı!')
                    else:
                        st.session_state.v17_receipts[receipt17.strip()]={'amount_tl':amount17,'file_sha256':paket_info17['txt_sha256'],'status':'UNVERIFIED_USER_ENTRY'}
                        st.success('Kullanıcı beyanı kaydedildi. İşlem resmî kaynaktan doğrulanmadı.')
                if st.session_state.v17_receipts:
                    st.dataframe(pd.DataFrame([{'Referans':k,**v} for k,v in st.session_state.v17_receipts.items()]),hide_index=True)

# ------------------------------------------------------------------------------
# SEKME 4: TEK DOSYADA BÜTÜN GÜNCEL KOLONLAR (v15.3)
# ------------------------------------------------------------------------------
with tab_txt153:
    st.subheader('📥 Analiz kolonları — Tek TXT + doğrulama paketi')
    st.warning('Yalnızca analiz çıktısıdır. Resmî bülten, kapanış, olasılık kalibrasyonu, site DOM ve ödeme teyidi bağımsız doğrulanmadığından canlı bahis için onaylı değildir.')
    txt17_ozet=st.session_state.son_uretim_ozeti
    if v171_current_gate.get('ok'):
        st.info('Kabul yöntemi: '+('Kullanıcının açık beyanı (resmî doğrulama yok).' if v171_current_gate.get('mode')=='USER_ATTESTED' else 'CSV/metin/API çapraz kontrolü (otantiklik doğrulanmadı).'))
    else:
        st.warning('Seçilen bülten kabul yöntemi tamamlanmadı. ANALİZ çıktıları için onay/kanıtları kontrol edin.')
    try:
        raw17,manifest17,zip17,info17=v17_paket_uret(
            st.session_state.uretilen_kuponlar,txt17_ozet,guncel_uretim_imzasi,
            st.session_state.secilen_mac_idleri,txt17_ozet['s_veriler'] if txt17_ozet else [],
            kolon_fiyati,hedef_butce_tl,strict=True)
        v17_paket_kontrol(raw17,manifest17)
    except (ValueError,TypeError,KeyError,InvalidOperation) as exc:
        st.info('TXT üretimi durduruldu: '+str(exc))
    else:
        st.metric('Geçerli ve benzersiz kolon',f"{info17['columns']:,}")
        st.caption(f"Tahmini maliyet: {info17['cost_assumption_tl']} TL (birim fiyat kullanıcı varsayımı)")
        st.code('TXT SHA-256: '+info17['txt_sha256'])
        st.info('v19.0 güvenlik kuralı: Kolonların tek TXT veya ZIP indirmesi için 2. Dosyaları İndir bölümünde A01–A10 kabul raporunun başarılı olması gerekir. Bu sekme yalnız önizleme gösterir.')
        st.info('Tüm kolonların doğrulanmış 1X2/102 TXT ve ZIP çıktıları için 2. Dosyaları İndir sekmesini kullanın.')

        with st.expander('İlk 20 kolon',expanded=True):
            st.code('\n'.join(raw17.decode().splitlines()[:20]),language='text')
        with st.expander('15 maç sıra ve kimlik denetimi'):
            st.dataframe(pd.DataFrame(info17['matches']),hide_index=True,use_container_width=True)


# ------------------------------------------------------------------------------
# SEKME 5: v17.2 TARIHSEL TAHMIN DENETIMI -- yalnız gercek pre-match snapshot
# ------------------------------------------------------------------------------
with tab_backtest:
    st.subheader('🧪 v17.2 — Geçmiş Tahmin Başarısı & Kalibrasyon')
    st.warning('Gerçek sonuçlardan geriye dönük tahmin türetilmez. Yalnız maç başlamadan en az 30 dakika önce kaydedilmiş 1/X/2 olasılıkları değerlendirilir. CSV kullanıcı beyanıdır; sonuçlar ve snapshot kaynağı bağımsız doğrulanmaz.')
    st.caption('CSV zorunlu: match_id,kickoff_utc,snapshot_utc,league,result; kaynaklar için market_1,market_x,market_2 veya api_1,api_x,api_2 veya model_1,model_x,model_2 veya blend_1,blend_x,blend_2. Her kaynak yüzdeleri 100 etmeli. Sonuç normal süre 1/X/2 (0 kabul edilir). Saatler +03:00 veya Z içermeli.')
    tpl172='match_id,kickoff_utc,snapshot_utc,league,result,market_1,market_x,market_2,api_1,api_x,api_2,model_1,model_x,model_2,blend_1,blend_x,blend_2\n'
    st.download_button('⬇️ Boş tarihsel tahmin CSV şablonu',tpl172.encode('utf-8-sig'),
                       file_name='SPOR_TOTO_V172_BACKTEST_SABLONU.csv',mime='text/csv',key='v172_blank')
    # Güncel tahminleri maç başlamadan arşivleyin; 90dk sonuçlarını daha sonra doldurun.
    if st.session_state.analiz_verisi is not None:
        with st.expander('📥 Gelecek backtest için maç öncesi tahmin arşivi oluştur',expanded=False):
            try:
                ms=st.session_state.secilen_15_mac
                ps=st.session_state.analiz_verisi
                if len(ms)!=15 or len(ps)!=15 or [str(m['id']) for m in ms]!=[str(v['id']) for v in ps]:
                    raise ValueError('Tam 15 maç ve aynı sıradaki tahminler gerekli.')
                outrows=[]
                for m,v in zip(ms,ps):
                    kickoff=v17_utc(f"{m['tarih']}T{m['saat']}:00+03:00")
                    snap=v17_utc(v['source_fetched_at'])
                    if snap >= kickoff-pd.Timedelta(minutes=30) or kickoff-snap>pd.Timedelta(days=30):
                        raise ValueError(f"{m['karsilasma']}: geçerli maç öncesi API snapshot bulunmuyor.")
                    if v.get('source_provenance')!='API_REQUEST_AT':
                        raise ValueError(f"{m['karsilasma']}: API kaynaklı 1/X/2 bulunmuyor.")
                    outrows.append({'match_id':str(m['id']),'kickoff_utc':kickoff.isoformat(),
                        'snapshot_utc':snap.isoformat(),'league':str(m.get('lig','')),
                        'result':'','blend_1':v['1'],'blend_x':v['X'],'blend_2':v['2']})
                histcsv=pd.DataFrame(outrows).to_csv(index=False).encode('utf-8-sig')
                st.download_button('📥 Bu 15 maçın gerçek maç öncesi tahminlerini CSV indir',
                    histcsv,file_name='SPOR_TOTO_V172_ON_TAHMIN_15MAC.csv',mime='text/csv',key='v172_save_prematch')
                st.caption('Sonuç sütunu bilerek boş bırakılır. Maçlar bittikten sonra 90dk sonuçlarını resmî kayıtlara göre 1/X/2 girip bu arşivi Gelişmiş Araçlar > Geçmiş Tahmin Testleri bölümüne tekrar yükleyin. Blend, kalibre edilmemiş mevcut birleşik modeldir.')
            except (KeyError,TypeError,ValueError) as exc:
                st.info('Maç öncesi arşiv oluşturulamadı: '+str(exc))
    uploaded172=st.file_uploader('Geçmiş, maç öncesi tahmin kayıtları CSV',type=['csv'],key='v172_history_file')
    if uploaded172 is None:
        st.info('Henüz doğrulanabilir maç öncesi tahmin arşivi yüklenmedi; Brier/LogLoss veya model iyileştirme iddiası hesaplanmaz. Sonuç CSV’si tek başına yeterli değildir.')
    else:
        try:
            parsed172,sources172=v172_history_parse(uploaded172.getvalue())
            overview172,calib172,leagues172,paired172=v172_backtest_report(parsed172,sources172)
        except (ValueError,TypeError,KeyError,pd.errors.ParserError,OverflowError) as exc:
            st.error('Backtest başlatılmadı: '+str(exc))
        else:
            st.success(f'{len(parsed172)} benzersiz geçmiş maç, {len(sources172)} olasılık kaynağı okundu. Bu tarihsel verilerin doğruluğunu kullanıcı sağlamalıdır.')
            st.dataframe(pd.DataFrame(overview172),hide_index=True,use_container_width=True)
            st.caption('Brier ve LogLoss için düşük değer iyidir; ECE, en yüksek olasılıklı sınıfın kalibrasyon hatasıdır. Farklı maç kümelerinin skorları doğrudan sıralanmaz.')
            if paired172:
                st.markdown('#### Aynı maçlarda adil kaynak karşılaştırması')
                st.dataframe(pd.DataFrame(paired172),hide_index=True,use_container_width=True)
            else:st.info('Ortak en az 30 maç olmadığından kaynaklar arasında eşit örneklem karşılaştırması yok.')
            st.markdown('#### Kronolojik train/test ve sıcaklık kalibrasyonu (yalnız rapor)')
            tempview172=[]
            for c in calib172:
                row={'Kaynak':c['source'],'Durum':c['status'],'Toplam':c['total_n'],
                     'Train':c['train_n'],'Test':c['holdout_n']}
                if c['status']=='OUT_OF_TIME_TEST':
                    row.update({'Sicaklik':round(c['temperature'],3),
                                'Test_Orijinal_LogLoss':round(c['raw']['log_loss'],5),
                                'Test_Kalibre_LogLoss':round(c['calibrated']['log_loss'],5),
                                'Test_Baseline_LogLoss':round(c['baseline']['log_loss'],5)})
                tempview172.append(row)
            st.dataframe(pd.DataFrame(tempview172),hide_index=True,use_container_width=True)
            st.caption('Kronolojik ayırma ve en az 24 saat embargo uygulanır. Kalibrasyon en az 80 eğitim + 30 test maçı ve 20 farklı gün gerektirir. Sonuçlar otomatik olarak canlı tahminlere uygulanmaz.')
            if leagues172:
                with st.expander('Lig bazında sonuçlar (en az 10 maç)'):
                    st.dataframe(pd.DataFrame(leagues172),hide_index=True,use_container_width=True)
            report172={'version':'17.2 SAFE BETA','status':'HISTORICAL_USER_SUPPLIED_UNVERIFIED',
                'rows':len(parsed172),'sources':sources172,'metrics':overview172,
                'chronological_calibration':calib172,'leagues':leagues172,
                'paired':paired172,'input_sha256':hashlib.sha256(uploaded172.getvalue()).hexdigest(),
                'notes':['Backtest ile dogrulanan kaynak verisi kullaniciya aittir.',
                         'Bunlar gercek bahis karliligi veya gelecek mac basarisi garantisi degildir.',
                         'Kalibrasyon parametreleri canli tahmin motoruna uygulanmamistir.']}
            st.download_button('📄 Backtest raporunu JSON indir',
                json.dumps(report172,ensure_ascii=False,indent=2,default=str).encode('utf-8'),
                file_name='SPOR_TOTO_V172_BACKTEST_RAPORU.json',mime='application/json',key='v172_report_out')


# ------------------------------------------------------------------------------
# SEKME 6: v17.3 ANTI-PUBLIC PRO -- diagnoz + agirlik etkisi, grafik YOK
# ------------------------------------------------------------------------------
with tab_antipublic:
    st.subheader('🧠 v17.3 — Anti-Public & Portföy Çeşitliliği')
    st.warning('Halk tercihi veri seti size ait bir CSV kaydıdır. Kaynağın otantikliği, kayıt saatinin doğruluğu ve piyasa güncelliği bağımsız doğrulanmaz. '
               'Halk oranları tek-maç marjinalleridir; 15 maçlık ortak kupon dağılımı, ikramiye paylaşımı, net EV veya kazanç tahmini değildir.')
    st.caption('1. sekmede Banko Riski & Halk Tercihi bölümüne fixture_id,h1,hx,h2,source,snapshot dosyasını yükleyin. '
               'Tam 15 maç, HTTPS kaynak adresi, saat dilimli ve son 72 saatlik maç öncesi kayıt gereklidir. '
               'Deneysel ağırlığı sol menüden isteğe bağlı açabilirsiniz; varsayılan kapalıdır.')
    if public173_ctx is None:
        st.info('Tam halk CSV henüz yüklenmedi. Optimizasyon model ağırlıklı, Anti-Public etkisi sıfır.')
    elif not public173_ctx.get('ok'):
        st.error('Halk verisi doğrulaması başarısız: '+'; '.join(public173_ctx.get('issues',[])))
    else:
        st.success(f"15/15 kayıt biçimsel kontrolden geçti • Kullanıcı sağladı, otantiklik doğrulanmadı • En eski: {public173_ctx['max_age_hours']:.1f} saat")
        st.code('Kullanıcı halk CSV SHA-256: '+public173_ctx['sha256'])
        if not v173_opt_in:st.info('Deneysel optimizasyon kapalı; kamu verisi yalnız tanı amaçlı gösteriliyor.')
    if st.session_state.uretilen_kuponlar is None or st.session_state.son_uretim_ozeti is None:
        st.info('Portföy raporu için 1. sekmede 15 maçlık kupon setini hesaplayın.')
    elif guncel_uretim_imzasi is None or st.session_state.son_uretim_ozeti.get('imza')!=guncel_uretim_imzasi:
        st.warning('Şablon, halka açık veri veya ağırlık değişti: yeni kolonları hesaplamadan eski portföy raporu gösterilmiyor.')
    else:
        try:
            _sum173=st.session_state.son_uretim_ozeti
            _report173=v173_portfoy_raporu(st.session_state.uretilen_kuponlar,
                _sum173['s_veriler'],public173_ctx['data'] if public173_ctx and public173_ctx.get('ok') else None,
                _sum173.get('v173_crowd_weight',0))
            _sha173=_sum173.get('v173_public_sha256')
            if _sum173.get('v173_crowd_weight',0)>0 and _sha173!=(public173_ctx or {}).get('sha256'):
                raise ValueError('Halk veri SHA ile uretilen kuponlar uyusmuyor.')
            _k1,_k2,_k3=st.columns(3)
            _k1.metric('Kolon',str(_report173['count']))
            _k2.metric('Mükerrer kolon',str(_report173['duplicates']))
            _k3.metric('Örnek min. Hamming',str(_report173['min_pairwise_hamming_sample']))
            st.caption(f"Hamming mesafesi {int(_report173['sample_size'])} deterministik örnek kolon üzerinde hesaplanır; tam portföy ispatı değildir. "
                       f"Kullanılan halk ağırlığı: {_report173['weight']:.2f}. Bu sıralama kolonların içeriğini değiştirmez.")
            st.dataframe(pd.DataFrame(_report173['top_rows']),hide_index=True,use_container_width=True)
            st.download_button('📥 Anti-Public sıralama denetimini CSV indir',
                pd.DataFrame(_report173['top_rows']).to_csv(index=False).encode('utf-8-sig'),
                file_name='SPOR_TOTO_V173_ANTI_PUBLIC_INCELEME.csv',mime='text/csv')
            _audit173={k:v for k,v in _report173.items() if k!='top_rows'}
            _audit173.update({'model_version':'17.3 SAFE BETA','parameter_signature':guncel_uretim_imzasi,
                'public_csv_sha256':_sha173,'independent_authentication':False,
                'coverage_unchanged_by_report':True,'source':'user_supplied_csv'})
            st.download_button('📄 Anti-Public denetim özetini JSON indir',
                json.dumps(_audit173,ensure_ascii=False,indent=2).encode('utf-8'),
                file_name='SPOR_TOTO_V173_ANTI_PUBLIC_RAPOR.json',mime='application/json')
        except Exception as _exc173:
            st.error('Anti-Public portföy denetimi durduruldu: '+str(_exc173))


# ------------------------------------------------------------------------------
# SEKME 7: v18.0 ACCEPTANCE & RELIABILITY CENTER
# ------------------------------------------------------------------------------
with tab_acceptance:
    st.subheader('✅ v19.0 — Kabul ve Güvenilirlik Merkezi')
    st.error('GERÇEK PARAYLA OTOMATİK OYNAMA / ÖDEME YETKİSİ YOK. Bu sistem yalnızca analiz paketi ve doğrulama raporu üretir.')
    st.caption('Yazılım çekirdek testleri canlı bahis sitesi veya resmî veri otantikliği testi değildir. '
               'Tek başına CSV kaynağının URL bilgisi, resmî kaynağın gerçekten doğrulandığını kanıtlamaz.')
    v18_report=None
    if st.session_state.uretilen_kuponlar is None or not st.session_state.son_uretim_ozeti:
        st.warning('Önce 1. sekmeden güncel 15 maçın analizini ve kolonları oluşturun.')
    else:
        try:
            o18=st.session_state.son_uretim_ozeti
            raw18,manifest18,_,info18=v17_paket_uret(
                st.session_state.uretilen_kuponlar,o18,guncel_uretim_imzasi,
                st.session_state.secilen_mac_idleri,o18['s_veriler'],kolon_fiyati,hedef_butce_tl,strict=True)
        except (ValueError,TypeError,KeyError,OverflowError,InvalidOperation) as exc:
            st.error('Kabul testi için geçerli temel TXT paketi üretilemedi: '+str(exc))
        else:
            v18_report=v18_kabul_raporu(raw18,manifest18,v171_current_gate,
                st.session_state.secilen_15_mac,st.session_state.analiz_verisi,
                guncel_uretim_imzasi,kolon_fiyati,hedef_butce_tl,
                ozet=o18)
            st.dataframe(pd.DataFrame([{'Kod':r['code'],'Kontrol':r['title'],
                                       'Durum':r['status'],'Ayrıntı':r['detail']}
                                      for r in v18_report['checks']]),hide_index=True,use_container_width=True)
            st.caption('PASS: yerel kontrol başarılı. USER_ACCEPTED: kullanıcı beyanına dayalı, bağımsız doğrulanmamış. FAIL: analiz paketini engeller. '
                       'NOT_VERIFIED: canlı/onaylı oyun için gereken bağımsız doğrulama henüz yapılmamış.')
            a02a03=[r for r in v18_report['checks'] if r['code'] in ('A02','A03') and r['status']=='FAIL']
            if a02a03:
                st.error('🚫 Bülten kabul kilidi (A02/A03): Kullanıcı beyanı veya seçilen üçlü karşılaştırma tamamlanmadı.')
                for check in a02a03:
                    st.warning(f"{check['code']} — {check['detail']}")
                st.info('ÇÖZÜM: 1. sekmede Kullanıcı onayı seçiliyse 15 maçın sırasını kontrol edip kutuyu işaretleyin ve onayı kaydedin. '
                        'Üçlü karşılaştırma seçiliyse CSV, maç metni ve API tekrar kontrolü gereklidir. '
                        'Resmî kaynak doğrulaması her iki yolda da yapılmış sayılmaz.')
            st.download_button('📄 Kabul raporu JSON olarak indir',
                json.dumps(v18_report,ensure_ascii=False,indent=2).encode('utf-8'),
                file_name='SPOR_TOTO_V19_KABUL_RAPORU.json',mime='application/json',key='v18_report_download')
            if v18_report['analysis_package_eligible']:
                st.success('YEREL ANALİZ KABULÜ: Zorunlu yazılım kontrolleri geçti. Kullanıcı beyanı ile resmî doğrulama aynı şey değildir; canlı oyun onayı yoktur.')
                try:
                    audit18=v18_kabul_zip(raw18,manifest18,v18_report)
                    validate18=v18_zip_kontrol(audit18)
                    st.download_button('📦 v19.0 DENETİMLİ ANALİZ PAKETİ (ZIP)',audit18,
                        file_name=f"SPOR_TOTO_V190_ANALIZ_KABUL_{validate18['txt_sha256'][:12]}.zip",
                        mime='application/zip',type='primary',use_container_width=True,key='v19_archive_download')
                    # Tek TXT indirme, yalnız AYNI kabul kapısından geçen dosya ile yapılır.
                    st.download_button('📥 Tüm kolonları TEK TXT indir (1-X-2, ANALİZ)',raw18,
                        file_name=f"SPOR_TOTO_V190_ANALIZ_{info18['columns']}K_{validate18['txt_sha256'][:12]}.txt",
                        mime='text/plain',use_container_width=True,key='v19_approved_txt')
                    st.download_button('📥 Spor Toto 1-0-2 TXT indir (ANALİZ)',v171_toto_0_txt(raw18),
                        file_name=f"SPOR_TOTO_V190_102_ANALIZ_{info18['columns']}K_{validate18['txt_sha256'][:12]}.txt",
                        mime='text/plain',use_container_width=True,key='v19_approved_102')
                    st.code(f"TXT SHA-256: {validate18['txt_sha256']}")
                except (ValueError,TypeError,KeyError,zipfile.BadZipFile) as exc:
                    st.error('Denetimli ZIP üretimi veya kendi kendine testi başarısız: '+str(exc))
            else:
                st.error('KABUL ENGELİ: Zorunlu koşullar geçilmedi. 1. sekmeden veri ve kolonları yenileyin.')
    st.markdown('#### 📂 Daha önce indirilmiş v19/v18 analiz ZIP dosyasını kontrol et')
    incoming18=st.file_uploader('Yalnızca v18 denetimli analiz ZIP',type=['zip'],key='v18_audit_upload')
    if incoming18 is not None:
        try:
            result18=v18_zip_kontrol(incoming18.getvalue())
            st.success(f"Çevrimdışı dosya bütünlüğü doğru: {result18['columns']} kolon, 15 maç. Resmî veya ödeme otantikliği doğrulanmadı.")
            st.code('TXT SHA-256: '+result18['txt_sha256'])
        except (ValueError,TypeError,KeyError,UnicodeError,zipfile.BadZipFile,OverflowError) as exc:
            st.error('ZIP kabul edilmedi: '+str(exc))
    st.markdown('#### Bağımsız testte halen açık kalan alanlar')
    st.info('Resmî maç listesi içeriğinin otantikliği • Gerçek API anahtarında canlı veri gecikmesi '
            '• Streamlit tarayıcı uçtan uca testi • Geçmiş gerçek maç öncesi tahminlerle istatistiksel kalibrasyon '
            '• Bahis sitesi işaretleme, fiş, fiyat ve ödeme sonucu (entegrasyon kapalı).')


# ------------------------------------------------------------------------------
# SEKME 8: v18.1 — HAM EVRENİN TAM VE BAĞIMSIZ HESABI
# ------------------------------------------------------------------------------
with tab_math181:
    st.subheader('🧮 v19.0 — Bağımsız Matematiksel Denetim')
    st.info('Bu modül üretim motorunu çağırmaz. Ham şablondaki HER senaryo için en yakın kolonun 0–15 isabetini tam olarak hesaplar. Resmî bülten veya kâr garantisi değildir.')
    live_summary=st.session_state.get('son_uretim_ozeti')
    live_columns=st.session_state.get('uretilen_kuponlar')
    if live_summary is not None and live_columns is not None:
        try:
            ids=live_summary.get('mac_ids',[])
            if ids != st.session_state.get('secilen_mac_idleri'):
                raise ValueError('Oturumdaki maç sırası ile üretim maçı uyuşmuyor.')
            if not guncel_uretim_imzasi or live_summary.get('imza') != guncel_uretim_imzasi:
                raise ValueError('Üretim ayarları değişmiş; yeniden üretim gerekli.')
            exact_raw,_=tum_kolonlar_txt153(live_columns,live_summary,guncel_uretim_imzasi,ids)
            exact_report=v181_exact_audit(exact_raw,live_summary['g_sablon'],expected=live_summary.get('denetim_ham'))
            st.success(f"TAM MATEMATİK DENETİMİ: {exact_report['scenario_count']:,} senaryo, {exact_report['unique_columns']:,} tekil kolon.") if not exact_report['mismatches'] else st.error('Eski rapor yüzdeleri ile tam sayım uyuşmuyor; analiz paketini kullanmayın.')
            st.dataframe(pd.DataFrame([{'Hedef':k,'Karşılanan senaryo':exact_report['exact_count'][k],
                'Toplam':exact_report['scenario_count'],'Kapsama %':round(exact_report['exact_percent'][k],6)}
                for k in ('tam_15','en_az_14','en_az_13','en_az_12')]),hide_index=True,use_container_width=True)
            st.caption('En düşük en iyi isabet: '+str(exact_report['minimum_best_hits'])+' / 15. En zayıf senaryo örneği: '+exact_report['worst_case_example'])
            st.download_button('📄 Bağımsız tam matematik raporu (JSON)',json.dumps(exact_report,ensure_ascii=False,indent=2).encode('utf-8'),
                file_name='SPOR_TOTO_V181_BAGIMSIZ_MATEMATIK_RAPORU.json',mime='application/json',key='v181_session_report')
            st.download_button('📋 Orijinal 15 satırlık ham şablon (JSON)',json.dumps(exact_report['template'],ensure_ascii=False,indent=2).encode('utf-8'),
                file_name='SPOR_TOTO_V190_HAM_SABLON.json',mime='application/json',key='v181_template_export')
        except (ValueError,TypeError,KeyError,UnicodeError,OverflowError) as exc:
            st.error('Tam matematik denetimi başarısız: '+str(exc))
    else:
        st.warning('Oturumda kolon/ham şablon yok. Önce 1. sekmeden güncel kuponları üretin.')
    st.markdown('#### Dışa aktarılan analiz ZIP dosyasını tam sayım ile sınama')
    uploaded181=st.file_uploader('v19.0 veya eski v18.x denetimli analiz ZIP',type=['zip'],key='v181_audit_zip')
    old_template181=st.file_uploader('Yalnız eski ZIP için orijinal 15 satırlık ham şablon (JSON); yeni ZIP gerekmez',type=['json'],key='v181_template_json')
    if uploaded181 is not None:
        try:
            t181=json.loads(old_template181.getvalue().decode('utf-8-sig')) if old_template181 is not None else None
            out181=v181_audit_archive(uploaded181.getvalue(),external_template=t181)
            if out181['mismatches']:
                st.error('Ham kapsam tutarsızlığı bulundu; analiz doğrulanmadı.')
            else:
                st.success(f"Tam sayım: {out181['scenario_count']:,} senaryo; {out181['unique_columns']:,} kolon.")
                if out181['template_provenance']!='EMBEDDED_TEMPLATE_MANIFEST_BOUND':
                    st.warning('Bu eski ZIP için şablon haricen sağlandı: şablonun gerçekten orijinal olduğunu yalnız ZIP içinden doğrulayamıyoruz.')
                st.dataframe(pd.DataFrame([{'Hedef':k,'Kapsama %':round(out181['exact_percent'][k],6),'Senaryo':out181['exact_count'][k]}
                    for k in ('tam_15','en_az_14','en_az_13','en_az_12')]),hide_index=True,use_container_width=True)
            st.download_button('📄 Bu ZIP için bağımsız raporu indir',json.dumps(out181,ensure_ascii=False,indent=2).encode('utf-8'),
                file_name='SPOR_TOTO_V190_ZIP_DENETIM_RAPORU.json',mime='application/json',key='v181_zip_report')
        except (ValueError,TypeError,KeyError,UnicodeError,zipfile.BadZipFile,OverflowError) as exc:
            st.error('Denetim engellendi: '+str(exc))
    st.caption('Büyük evren tam sayımı 300.000 ham senaryoya kadar desteklenir. Kapsama yalnız şablon evrenindedir; bülten doğruluğunu, tahmin kalibrasyonunu veya ödeme sonucunu kanıtlamaz.')
