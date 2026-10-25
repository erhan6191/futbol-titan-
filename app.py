import streamlit as st
import requests
import itertools
import time
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Spor Toto Tam Otonom AI & Derin Analiz", page_icon="⚽", layout="wide")
st.title("🏆 Spor Toto AI & Gelişmiş Derin Öğrenme Motoru")

with st.sidebar:
    st.header("⚙️ Sistem Ayarları")
    api_key = st.text_input("API-Football Anahtarı:", type="password")
    
    st.subheader("🎯 Garanti Sistemi")
    garanti_secimi = st.selectbox("Hedeflenen Garanti:", 
                                ["15 Garanti (Tam Kombinasyon)", "14 Garanti (1 Hata Payı)", 
                                 "13 Garanti (2 Hata Payı)", "12 Garanti (3 Hata Payı)"])
    garanti_derecesi = int(garanti_secimi.split()[0])
    
    st.subheader("🧠 Yapay Zeka Yönetimi")
    ai_filtre_modu = st.toggle("🤖 Tam Otonom Mod (Tavsiye Edilen)", value=True, help="Tüm limitleri, ardışık engelleri ve blok filtrelerini haftanın zorluğuna göre AI kendi ayarlar.")
    
    if not ai_filtre_modu:
        st.markdown("**(Min - Max) Manuel Değerler:**")
        range_1 = st.slider("Ev Sahibi (1)", 0, 15, (4, 9))
        range_x = st.slider("Beraberlik (X)", 0, 15, (1, 5))
        range_2 = st.slider("Deplasman (2)", 0, 15, (2, 7))
        range_puan = st.slider("Puan (Sürpriz-Favori)", 300, 1200, (550, 900))
        max_ardisik_1 = st.slider("Üst Üste '1'", 2, 10, 5)
        max_ardisik_x = st.slider("Üst Üste 'X'", 2, 10, 3)
        max_ardisik_2 = st.slider("Üst Üste '2'", 2, 10, 4)
        banko_siniri = st.number_input("Banko Sınırı (%)", value=63)
        cifte_sans_siniri = st.number_input("Çifte Şans Sınırı (%)", value=42)
        
        st.subheader("🔗 Manuel Blok Filtresi")
        aktif_blok_filtresi = st.toggle("Blok Sonuç Sınırlandırma", value=True)
        max_blok_tekrar = st.slider("3'lü Blokta Aynı Sonuç Maksimum Tekrarı", 1, 3, 2)

def maclari_getir(api_key):
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "v3.football.api-sports.io"}
    ligler = [203, 39, 140, 135, 78, 61, 2, 3, 848, 204, 40, 88, 94, 144, 71]
    tum_maclar = []
    
    for lig in ligler:
        url = f"https://v3.football.api-sports.io/fixtures?league={lig}&next=10"
        try:
            res = requests.get(url, headers=headers).json()
            if res.get('response'):
                for item in res['response']:
                    f_id = item['fixture']['id']
                    ev = item['teams']['home']['name']
                    dep = item['teams']['away']['name']
                    ev_id = item['teams']['home']['id']
                    dep_id = item['teams']['away']['id']
                    tarih = item['fixture']['date'][:10]
                    tum_maclar.append({
                        "id": f_id, 
                        "label": f"{tarih} | {ev} - {dep}",
                        "home_id": ev_id,
                        "away_id": dep_id
                    })
        except:
            continue
    return tum_maclar

def gelismis_tahmin_ve_h2h_cek(mac, api_key):
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "v3.football.api-sports.io"}
    
    # 1. Temel Tahminleri Çek
    pred_url = f"https://v3.football.api-sports.io/predictions?fixture={mac['id']}"
    res = requests.get(pred_url, headers=headers).json()
    
    h_oran, x_oran, a_oran = 34, 33, 33 # Varsayılan
    if res.get('response'):
        t = res['response'][0]['predictions']['percent']
        h_oran = int(t['home'].replace('%', ''))
        x_oran = int(t['draw'].replace('%', ''))
        a_oran = int(t['away'].replace('%', ''))

    # 2. H2H (Aralarındaki Maçlar) Verisini Çek ve Oranları Optimize Et
    h2h_url = f"https://v3.football.api-sports.io/fixtures/headtohead?h2h={mac['home_id']}-{mac['away_id']}&last=5"
    try:
        h2h_res = requests.get(h2h_url, headers=headers).json()
        if h2h_res.get('response'):
            h2h_maclar = h2h_res['response']
            ev_galibiyet = 0
            dep_galibiyet = 0
            for h2h in h2h_maclar:
                ev_gol = h2h['goals']['home']
                dep_gol = h2h['goals']['away']
                if ev_gol is not None and dep_gol is not None:
                    # Ev sahibi takım ID'sine göre galibiyet kontrolü
                    if h2h['teams']['home']['id'] == mac['home_id']:
                        if ev_gol > dep_gol: ev_galibiyet += 1
                        elif dep_gol > ev_gol: dep_galibiyet += 1
                    else:
                        if dep_gol > ev_gol: ev_galibiyet += 1
                        elif ev_gol > dep_gol: dep_galibiyet += 1
            
            # H2H sonuçlarına göre oranlara küçük bir akıllı bonus ekleyelim
            if ev_galibiyet > dep_galibiyet:
                h_oran = min(90, h_oran + (ev_galibiyet * 3))
            elif dep_galibiyet > ev_galibiyet:
                a_oran = min(90, a_oran + (dep_galibiyet * 3))
    except:
            pass

    # Yüzdeleri 100'e sabitle
    toplam = h_oran + x_oran + a_oran
    if toplam > 0:
        h_oran = int((h_oran / toplam) * 100)
        x_oran = int((x_oran / toplam) * 100)
        a_oran = 100 - (h_oran + x_oran)

    return {
        "mac": mac['label'],
        "1": h_oran,
        "X": x_oran,
        "2": a_oran
    }

def tahminleri_al(secilen_maclar, api_key):
    sonuclar = []
    progress = st.progress(0, text="Yapay Zeka H2H ve form analizlerini gerçekleştiriyor...")
    for i, mac in enumerate(secilen_maclar):
        veri = gelismis_tahmin_ve_h2h_cek(mac, api_key)
        sonuclar.append(veri)
        progress.progress((i + 1) / 15)
        time.sleep(0.3)
    progress.empty()
    return sonuclar

def tam_otonom_analiz(mac_verileri):
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

    hafta_zorlugu = np.mean(en_yuksek_ihtimaller)
    ai_banko = max(55, int(hafta_zorlugu + 7))
    ai_cifte = max(38, int(hafta_zorlugu - 10))
    ai_blok_tekrar = 3 if hafta_zorlugu > 65 else 2

    ai_limitler = {
        "1": (max(0, beklenen_1 - 3), min(15, beklenen_1 + 4)),
        "X": (max(0, beklenen_x - 1), min(15, beklenen_x + 5)),
        "2": (max(0, beklenen_2 - 2), min(15, beklenen_2 + 4)),
        "puan": (int(min_puan * 1.5), int(max_puan * 0.92)),
        "ardisik_1": max(3, (beklenen_1 // 2) + 2),
        "ardisik_x": max(2, (beklenen_x // 2) + 1),
        "ardisik_2": max(3, (beklenen_2 // 2) + 2),
        "banko_siniri": ai_banko,
        "cifte_siniri": ai_cifte,
        "aktif_blok_filtresi": True,
        "max_blok_tekrar": ai_blok_tekrar,
        "zorluk_skoru": hafta_zorlugu
    }
    return ai_limitler

def kolonlari_filtrele(sablon, mac_verileri, limitler):
    tum = list(itertools.product(*sablon))
    gecerli = []
    
    for kupon in tum:
        c1, cx, c2 = kupon.count('1'), kupon.count('X'), kupon.count('2')
        if not (limitler["1"][0] <= c1 <= limitler["1"][1]): continue
        if not (limitler["X"][0] <= cx <= limitler["X"][1]): continue
        if not (limitler["2"][0] <= c2 <= limitler["2"][1]): continue
        
        if max((len(list(g)) for k, g in itertools.groupby(kupon) if k == '1'), default=0) > limitler["ardisik_1"]: continue
        if max((len(list(g)) for k, g in itertools.groupby(kupon) if k == 'X'), default=0) > limitler["ardisik_x"]: continue
        if max((len(list(g)) for k, g in itertools.groupby(kupon) if k == '2'), default=0) > limitler["ardisik_2"]: continue
        
        if limitler.get("aktif_blok_filtresi", False):
            blok_ihlali = False
            for b in range(0, 15, 3):
                blok = kupon[b:b+3]
                if blok.count('1') > limitler["max_blok_tekrar"] or blok.count('X') > limitler["max_blok_tekrar"] or blok.count('2') > limitler["max_blok_tekrar"]:
                    blok_ihlali = True
                    break
            if blok_ihlali: continue

        puan = sum(mac_verileri[i][t] for i, t in enumerate(kupon))
        if not (limitler["puan"][0] <= puan <= limitler["puan"][1]): continue
        gecerli.append(kupon)
    return gecerli

def olasilik_hesapla(kolon, mac_verileri):
    skor = 1.0
    for i, tahmin in enumerate(kolon):
        skor *= (mac_verileri[i][tahmin] / 100.0)
    return skor

def garanti_sistemi_uygula(kolonlar, hedef, mac_verileri):
    if hedef == 15: return kolonlar
    fark = 15 - hedef
    
    with st.spinner('Olasılık Ağırlıklı Akıllı İndirgeme çalışıyor...'):
        kolon_skorlari = {tuple(k): olasilik_hesapla(k, mac_verileri) for k in kolonlar}
        sirali_kalan = sorted(kolonlar, key=lambda k: kolon_skorlari[tuple(k)], reverse=True)
        kalan_set = set(tuple(k) for k in kolonlar)
        
        nihai = []
        while kalan_set:
            merkez = None
            for aday in sirali_kalan:
                if tuple(aday) in kalan_set:
                    merkez = tuple(aday)
                    break
            if merkez is None:
                merkez = kalan_set.pop()
                
            nihai.append(list(merkez))
            kapsananlar = set([k for k in kalan_set if sum(1 for a, b in zip(merkez, k) if a != b) <= fark])
            kalan_set -= kapsananlar
            
    return nihai

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🌍 Global Maç Bülteni")
    if api_key:
        if "mac_listesi" not in st.session_state:
            with st.spinner("Ligler ve takımlar çekiliyor..."):
                st.session_state.mac_listesi = maclari_getir(api_key)
        
        opsiyonlar = {m['label']: m for m in st.session_state.mac_listesi}
        secilenler_label = st.multiselect("Bültenden Tam 15 Maç Seçin:", list(opsiyonlar.keys()), max_selections=15)
        
        if len(secilenler_label) == 15:
            if st.button("🚀 Analizi ve Derin Motoru Başlat", type="primary", use_container_width=True):
                secilenler_data = [opsiyonlar[lbl] for lbl in secilenler_label]
                with col2:
                    veriler = tahminleri_al(secilenler_data, api_key)
                    sablon = []
                    
                    if ai_filtre_modu:
                        limitler = tam_otonom_analiz(veriler)
                        st.info(f"🤖 **Derin Otonom Raporu:** Haftanın Zorluk Derecesi %{limitler['zorluk_skoru']:.1f}. Banko Sınırı %{limitler['banko_siniri']} ve 3'lü Blok Tekrar Limiti {limitler['max_blok_tekrar']} olarak optimize edildi.")
                    else:
                        limitler = {
                            "1": range_1, "X": range_x, "2": range_2, "puan": range_puan,
                            "ardisik_1": max_ardisik_1, "ardisik_x": max_ardisik_x, "ardisik_2": max_ardisik_2,
                            "banko_siniri": banko_siniri, "cifte_siniri": cifte_sans_siniri,
                            "aktif_blok_filtresi": aktif_blok_filtresi, "max_blok_tekrar": max_blok_tekrar
                        }
                    
                    for v in veriler:
                        sirali = sorted([(v["1"], "1"), (v["X"], "X"), (v["2"], "2")], reverse=True)
                        en = sirali[0][0]
                        if en >= limitler["banko_siniri"]: sablon.append([sirali[0][1]])
                        elif en >= limitler["cifte_siniri"]: sablon.append([sirali[0][1], sirali[1][1]])
                        else: sablon.append(["1", "X", "2"])
                    
                    filtrelenmis = kolonlari_filtrele(sablon, veriler, limitler)
                    
                    if not filtrelenmis:
                        st.error("Filtreler tüm kombinasyonları eledi. Haftanın maçları çok sürpriz barındırıyor olabilir.")
                    else:
                        garantili = garanti_sistemi_uygula(filtrelenmis, garanti_derecesi, veriler)
                        st.success("Derin Optimizasyon Başarıyla Tamamlandı!")
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Otonom Şablon", f"{len(list(itertools.product(*sablon)))}")
                        m2.metric("Filtre Sonrası", f"{len(filtrelenmis)}")
                        m3.metric(f"{garanti_derecesi} Garantili", f"{len(garantili)} Kolon", f"{len(garantili)*4} TL")
                        
                        st.download_button("Kuponları İndir (.txt)", "\n".join([" ".join(k) for k in garantili]), f"spor_toto_ai_{garanti_derecesi}.txt")
                        
                        st.markdown("### 📊 Yapay Zeka Risk ve Dağılım Raporu")
                        toplam_1 = sum(k.count('1') for k in garantili)
                        toplam_x = sum(k.count('X') for k in garantili)
                        toplam_2 = sum(k.count('2') for k in garantili)
                        
                        fig = px.pie(names=['Ev Sahibi (1)', 'Beraberlik (X)', 'Deplasman (2)'], 
                                     values=[toplam_1, toplam_x, toplam_2], 
                                     title="Nihai Kuponlardaki Genel İhtimal Dağılımı",
                                     color_discrete_sequence=px.colors.qualitative.Set2)
                        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("API Anahtarınızı sol menüden girdiğinizde ligler otomatik yüklenecektir.")
