import streamlit as st
import requests
import math
import time
import json
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Spor Toto AI Pro v5.1 (Kompakt)", page_icon="🏆", layout="wide")

# --- EKRANI KOMPAKT YAPAN ÖZEL CSS ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🏆 Spor Toto AI v5.1 — Kompakt Ekran & Hibrit Motor")

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
    st.header("⚙️ Ayarlar")
    api_key = st.text_input("API-Football Anahtarı:", type="password")
    kolon_fiyati = st.number_input("Kolon Fiyatı (TL):", min_value=1.0, value=10.0, step=1.0)
    
    st.subheader("🎯 Garanti & Bütçe")
    garanti_secimi = st.selectbox(
        "Garanti:", 
        ["15 Garanti (Tam Kombinasyon)", "14 Garanti (1 Hata Payı)", 
         "13 Garanti (2 Hata Payı)", "12 Garanti (3 Hata Payı)"],
        index=1
    )
    garanti_derecesi = int(garanti_secimi.split()[0])
    
    butce_aktif = st.toggle("💰 Maks Kolon Sınırı", value=False)
    if butce_aktif:
        max_kolon_limiti = st.number_input("Maks Kolon:", min_value=1, max_value=50000, value=100, step=10)
    else:
        max_kolon_limiti = None

    st.subheader("🧠 Yapay Zeka")
    strateji_modu = st.radio(
        "Strateji:",
        ["⚖️ Dengeli", "🛡️ Favori Korumalı", "💎 İkramiye Avcısı"]
    )
    tuzak_koruma = st.toggle("🚨 Tuzak Koruması", value=True)
    ai_filtre_modu = st.toggle("🤖 Otonom Filtre", value=True)


# ==============================================================================
# LİG HAVUZU VE MOTOR FONKSİYONLARI
# ==============================================================================
KATEGORIZE_LIGLER = {
    "🇹🇷 Türkiye": {"Trendyol Süper Lig": 203, "Trendyol 1. Lig": 204, "Türkiye Kupası": 205},
    "🇪🇺 Avrupa Büyükler": {"Premier League": 39, "La Liga": 140, "Serie A": 135, "Bundesliga": 78, "Ligue 1": 61},
    "⭐ Avrupa Kupaları": {"Şampiyonlar Ligi": 2, "Avrupa Ligi": 3, "Konferans Ligi": 848},
    "🌍 Diğer Avrupa": {"Eredivisie": 88, "Primeira Liga": 94, "Pro League": 144, "Super League": 103},
    "🌎 Diğer Kıtalar": {"Série A (Brezilya)": 71, "Liga Profesional (Arjentin)": 128, "MLS": 253}
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
                    tum_maclar.append({"id": f_id, "label": f"[{lig_adi}] {tarih} | {ev} - {dep}"})
        except Exception:
            continue
    return tum_maclar

def olasilik_yumusat(p1, px_val, p2):
    p1, px_val, p2 = max(5.0, float(p1)), max(5.0, float(px_val)), max(5.0, float(p2))
    toplam = p1 + px_val + p2
    return int(round(p1 * 100 / toplam)), int(round(px_val * 100 / toplam)), int(100 - round(p1 * 100 / toplam) - round(px_val * 100 / toplam))

def halk_egilimi_simule_et(p1, px_val, p2):
    w1, wx, w2 = (p1 ** 1.55), (px_val ** 1.15), (p2 ** 1.55)
    t = w1 + wx + w2
    return round(w1 * 100 / t), round(wx * 100 / t), 100 - round(w1 * 100 / t) - round(wx * 100 / t)

@st.cache_data(ttl=3600, show_spinner=False)
def hibrit_tahminleri_al(secilen_maclar, api_key):
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "v3.football.api-sports.io"}
    sonuclar = []
    progress = st.progress(0, text="Hibrit Motor çalışıyor...")
    for i, mac in enumerate(secilen_maclar):
        f_id = mac['id']
        ai_1, ai_x, ai_2 = 36.0, 33.0, 31.0
        odds_1, odds_x, odds_2 = None, None, None
        try:
            res_pred = requests.get(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", headers=headers, timeout=6).json()
            if res_pred.get('response') and res_pred['response'][0].get('predictions'):
                t = res_pred['response'][0]['predictions']['percent']
                ai_1, ai_x, ai_2 = float(t['home'].replace('%', '')), float(t['draw'].replace('%', '')), float(t['away'].replace('%', ''))
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
                        break
        except Exception:
            pass

        ham_1, ham_x, ham_2 = ((odds_1 * 0.65) + (ai_1 * 0.35)) if odds_1 else ai_1, ((odds_x * 0.65) + (ai_x * 0.35)) if odds_x else ai_x, ((odds_2 * 0.65) + (ai_2 * 0.35)) if odds_2 else ai_2
        g1, gx, g2 = olasilik_yumusat(ham_1, ham_x, ham_2)
        h1, hx, h2 = halk_egilimi_simule_et(g1, gx, g2)
        sonuclar.append({
            "bulten_no": i + 1, "id": f_id, "mac": mac['label'], "1": g1, "X": gx, "2": g2,
            "halk_favori": max(h1, hx, h2), "tuzak_farki": max(h1, hx, h2) - max(g1, gx, g2)
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
                    if md["fixture"]["status"]["short"] not in ["NS", "TBD", "PST", "CANC"] and md["goals"]["home"] is not None:
                        eg, dg = md["goals"]["home"], md["goals"]["away"]
                        skor_metinleri[idx] = f"{eg} - {dg}"
                        yeni_sonuclar[idx] = "1" if eg > dg else ("X" if eg == dg else "2")
    except Exception:
        pass
    return yeni_sonuclar, skor_metinleri

def tam_otonom_analiz(mac_verileri, strateji):
    min_puan, max_puan, en_yuksek = 0, 0, []
    for v in mac_verileri:
        s = sorted([v["1"], v["X"], v["2"]])
        min_puan, max_puan, en_yuksek = min_puan + s[0], max_puan + s[2], en_yuksek + [s[2]]
    hz = float(np.mean(en_yuksek))
    pf = max(15, max_puan - min_puan)
    return {
        "1": (0, 15), "X": (0, 15), "2": (0, 15),
        "puan": (int(min_puan + pf * 0.3), int(min_puan + pf * 0.95)),
        "surpriz": (0, 5), "ardisik_1": 6, "ardisik_x": 4, "ardisik_2": 5,
        "banko_siniri": max(52, int(hz + 5)), "cifte_siniri": max(36, int(hz - 8)),
        "aktif_blok_filtresi": True, "max_blok_tekrar": 2, "zorluk_skoru": hz
    }

def varsayilan_sablon_olustur(veriler, limitler, tuzak_aktif=True):
    sablon = []
    for v in veriler:
        s = sorted([(v["1"], "1"), (v["X"], "X"), (v["2"], "2")], reverse=True)
        if s[0][0] >= limitler["banko_siniri"]:
            sablon.append([s[0][1], s[1][1]] if (tuzak_aktif and v.get("tuzak_farki", 0) >= 12 and s[0][0] < 68) else [s[0][1]])
        elif s[0][0] >= limitler["cifte_siniri"]:
            sablon.append([s[0][1], s[1][1]])
        else:
            sablon.append(["1", "X", "2"])
    return sablon

def vektorel_filtrele(sablon, mac_verileri, limitler):
    harita = {'1': 0, 'X': 1, '2': 2}
    ters = np.array(['1', 'X', '2'])
    grids = np.meshgrid(*[[harita[s] for s in m] for m in sablon], indexing='ij')
    matris = np.stack(grids, axis=-1).reshape(-1, 15).astype(np.int8)
    oran_mat = np.array([[v["1"], v["X"], v["2"]] for v in mac_verileri], dtype=np.int16)
    puanlar = np.sum(oran_mat[np.arange(15), matris], axis=1)
    idx = np.argsort(puanlar)[::-1]
    return ters[matris[idx]], puanlar[idx]

def garanti_ve_butce_uygula(kolonlar, puanlar, hedef, max_k=None):
    if not len(kolonlar): return [], [], 0.0
    if hedef == 15:
        return (kolonlar[:max_k], puanlar[:max_k], (np.sum(puanlar[:max_k])/np.sum(puanlar))*100) if max_k else (kolonlar, puanlar, 100.0)
    
    fark, harita = 15 - hedef, {'1': 0, 'X': 1, '2': 2}
    mat = np.vectorize(harita.get)(kolonlar).astype(np.int8)
    mask, nihai = np.ones(len(kolonlar), dtype=bool), []
    while np.any(mask):
        if max_k and len(nihai) >= max_k: break
        m_idx = int(np.argmax(mask))
        nihai.append(m_idx)
        mask[np.where(mask)[0][np.sum(mat[np.where(mask)[0]] != mat[m_idx], axis=1) <= fark]] = False
    return kolonlar[nihai], puanlar[nihai], float(np.sum(puanlar[~mask]) / np.sum(puanlar) * 100)

def monte_carlo_simule_et(kuponlar, veriler):
    harita = {'1': 0, 'X': 1, '2': 2}
    k_num = np.vectorize(harita.get)(kuponlar).astype(np.int8)
    rng = np.random.default_rng(42)
    sim = np.zeros((2000, 15), dtype=np.int8)
    for idx, v in enumerate(veriler):
        o = np.array([v["1"], v["X"], v["2"]], dtype=float)
        sim[:, idx] = rng.choice([0, 1, 2], size=2000, p=o/o.sum())
    dereceler = np.max(np.sum(sim[:, None, :] == k_num[None, :, :], axis=2), axis=1)
    return {"15_oran": float(np.mean(dereceler == 15)*100), "12_arti_oran": float(np.mean(dereceler >= 12)*100), "ortalama": float(np.mean(dereceler))}

def kupon_dosyasi_coz(dosya):
    satirlar = dosya.getvalue().decode("utf-8-sig").strip().splitlines()
    k = [["X" if h=="0" else h.upper() for h in s.replace(","," ").split() if h.upper() in ["1","X","2","0"]] for s in satirlar]
    k_15 = [s[:15] for s in k if len(s) >= 15]
    return np.array(k_15) if k_15 else None


# ==============================================================================
# ANA SEKMELER
# ==============================================================================
tab_uretim, tab_takip, tab_otomasyon = st.tabs(["🚀 1. Hibrit Üretim", "📡 2. Canlı Takip", "🤖 3. Otomatik Yatırma"])

with tab_uretim:
    if api_key:
        kat = st.selectbox("Kategori:", list(KATEGORIZE_LIGLER.keys()), key="k1")
        ligler = st.multiselect("Ligler:", list(KATEGORIZE_LIGLER[kat].keys()), key="l1")
        
        if st.button("📥 Maçları Havuza Ekle", use_container_width=True):
            yeni = tum_liglerden_maclari_getir([KATEGORIZE_LIGLER[kat][l] for l in ligler], api_key)
            mevcut = {m["id"] for m in st.session_state.mac_listesi}
            for m in yeni:
                if m["id"] not in mevcut: 
                    st.session_state.mac_listesi.append(m)
            st.success(f"Havuzda toplam {len(st.session_state.mac_listesi)} maç var.")
            
        if st.session_state.mac_listesi:
            ops = {m['label']: m for m in st.session_state.mac_listesi}
            secilenler = st.multiselect("🎯 15 Maç Seçin:", list(ops.keys()), max_selections=15, key="m15")
            if len(secilenler) == 15 and st.button("🚀 Analizi Başlat", type="primary", use_container_width=True):
                st.session_state.secilen_mac_idleri = [ops[l]["id"] for l in secilenler]
                st.session_state.analiz_verisi = hibrit_tahminleri_al([ops[l] for l in secilenler], api_key)
    else:
        st.info("👈 Sol menüden API anahtarınızı girin.")

    if st.session_state.analiz_verisi:
        veriler = st.session_state.analiz_verisi
        limitler = tam_otonom_analiz(veriler, strateji_modu)
        sablon = varsayilan_sablon_olustur(veriler, limitler, tuzak_koruma)

        st.markdown("### 🛠️ Canlı Şablon ve Oran Editörü")
        df_edit = st.data_editor(
            pd.DataFrame([{
                "Sıra": v["bulten_no"], "Maç": v["mac"], "1%": v["1"], "X%": v["X"], "2%": v["2"],
                "Tuzak": "🚨 Evet" if v["tuzak_farki"] >= 12 else "✅ Normal",
                "1": "1" in s, "X": "X" in s, "2": "2" in s
            } for v, s in zip(veriler, sablon)]),
            disabled=["Maç", "1%", "X%", "2%", "Tuzak"], hide_index=True, use_container_width=True, height=350
        )

        sirali = df_edit.sort_values("Sıra").reset_index(drop=True)
        g_sablon, s_veriler = [], []
        for _, r in sirali.iterrows():
            sec = [k for k, b in [("1", r["1"]), ("X", r["X"]), ("2", r["2"])] if b]
            g_sablon.append(sec if sec else ["1"])
            s_veriler.append({"mac": r["Maç"], "1": int(r["1%"]), "X": int(r["X%"]), "2": int(r["2%"])})

        if math.prod(len(s) for s in g_sablon) <= 4_782_969:
            mat, puanlar = vektorel_filtrele(g_sablon, s_veriler, limitler)
            if len(mat) > 0:
                garanti, g_puan, kapsama = garanti_ve_butce_uygula(mat, puanlar, garanti_derecesi, max_kolon_limiti)
                st.session_state.uretilen_kuponlar = garanti
                mc = monte_carlo_simule_et(garanti, s_veriler)

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Filtreli Kolon", f"{len(mat):,}")
                c2.metric(f"{garanti_derecesi} Garantili", f"{len(garanti):,}")
                c3.metric("Bütçe", f"{len(garanti)*kolon_fiyati:,.0f} TL")
                c4.metric("15 Bilme Şansı", f"%{mc['15_oran']:.2f}")

                st.download_button("📥 Kuponları İndir (.TXT)", "\n".join([" ".join(k) for k in garanti]), f"spor_toto_{garanti_derecesi}.txt", use_container_width=True)

with tab_takip:
    st.markdown("### 📡 Canlı Takip Merkezi")
    col_t1, col_t2 = st.columns([1, 1.5])
    with col_t1:
        kaynak = st.radio("Kaynak:", ["📂 Dosya Yükle", "⚡ Oturumdakiler"], index=1 if st.session_state.uretilen_kuponlar is not None else 0)
        aktif_k = kupon_dosyasi_coz(st.file_uploader("Dosya:", type=["txt","csv"])) if "Dosya" in kaynak else st.session_state.uretilen_kuponlar
        
        if api_key and len(st.session_state.secilen_mac_idleri) == 15 and st.button("🔄 Skorları Çek"):
            st.session_state.canli_sonuclar, st.session_state.canli_skor_metni = canli_skorlari_cek(st.session_state.secilen_mac_idleri, api_key)

        m_isim = [v["mac"] for v in st.session_state.analiz_verisi] if st.session_state.analiz_verisi else [f"{i}. Maç" for i in range(1, 16)]
        sonuc_df = st.data_editor(
            pd.DataFrame({"No": list(range(1, 16)), "Maç": m_isim, "Skor": st.session_state.canli_skor_metni, "Sonuç": st.session_state.canli_sonuclar}),
            column_config={"Sonuç": st.column_config.SelectboxColumn("Sonuç", options=["⏳ Bekliyor", "1", "X", "2"], required=True)},
            disabled=["No", "Maç", "Skor"], hide_index=True, use_container_width=True, height=350
        )
    with col_t2:
        if aktif_k is not None and len(aktif_k) > 0:
            res = np.array(sonuc_df["Sonuç"].tolist())
            mask = np.isin(res, ["1", "X", "2"])
            if np.sum(mask) > 0:
                hata = np.sum(mask) - np.sum(aktif_k[:, mask] == res[mask], axis=1)
                maks_h = 15 - hata
                st.metric("🥇 15'e Giden", f"{int(np.sum(maks_h == 15)):,} Kupon")
                st.metric("🥈 14'e Giden", f"{int(np.sum(maks_h == 14)):,} Kupon")

with tab_otomasyon:
    st.markdown("### 🤖 Otomatik Yatırma")
    if st.session_state.uretilen_kuponlar is not None:
        k_oto = st.session_state.uretilen_kuponlar.tolist()
        boyut = st.number_input("Paket Boyutu:", 10, 500, 50)
        sec_p = st.selectbox("Paket Seç:", [f"Paket {i+1}" for i in range(math.ceil(len(k_oto)/boyut))])
        p_id = int(sec_p.split()[1]) - 1
        st.code(f"const kuponlar = {json.dumps(k_oto[p_id*boyut:(p_id+1)*boyut])};\nconsole.log('Hazır:', kuponlar.length);", language="javascript")
    else:
        st.info("Önce kupon üretin.")
