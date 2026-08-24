# ==============================
# FOOTBALL ORACLE v20.0 TITAN (STREAMLIT WEB EDITION)
# GOL FARKI ELO + KORNER (NEGATİF BİNOM) + ŞUT (NORMAL DAĞILIM)
# ==============================

import streamlit as st
import requests
import numpy as np
from scipy.stats import poisson, nbinom, norm
import time
import datetime
import pandas as pd
import re
from io import BytesIO

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Football Oracle v20.0", page_icon="🛡️", layout="wide")

# --- AYARLAR ---
BASE_URL = "https://v3.football.api-sports.io"
TARGET_BOOKIES = [1, 8, 11, 17]
HFA_ELO_BONUS = 75 

BANNED_KEYWORDS = [
    "u23", "u22", "u21", "u20", "u19", "u18", "u17", "development", "gelişim", 
    "youth", "primavera", "juvenil", "academy", "premier league 2", "pdl", 
    "professional development", "women", "femenina", "kadınlar", "feminine", 
    "frauen", "dam", "w-league", "amateur", "amatör", "amateurs", "regional", 
    "oberliga", "county", "state league", "npsl", "bölgesel", "non-league",
    "reserve", "reserves", "rezerv", "friendly", "friendlies", "hazırlık", 
    "club friendlies", "esoccer", "e-soccer", "esports", "university", "college", "ncaa"
]

# --- MATEMATİK VE İSTATİSTİK MODÜLLERİ ---
def get_dynamic_params(avg_goals):
    if avg_goals >= 2.8: return -0.10, 24
    elif avg_goals <= 2.3: return -0.18, 16
    else: return -0.14, 20

def apply_dixon_coles(matrix, lh, la, rho):
    dc_matrix = matrix.copy()
    dc_matrix[0, 0] = max(0, matrix[0, 0] * (1 - lh * la * rho))
    dc_matrix[1, 0] = max(0, matrix[1, 0] * (1 + lh * rho))
    dc_matrix[0, 1] = max(0, matrix[0, 1] * (1 + la * rho))
    dc_matrix[1, 1] = max(0, matrix[1, 1] * (1 - rho))
    return dc_matrix / np.sum(dc_matrix)

def apply_elo_mean_reversion(current_elo, mean_elo=1500, reversion_rate=0.30):
    return (current_elo * (1 - reversion_rate)) + (mean_elo * reversion_rate)

def get_mov_multiplier(home_goals, away_goals):
    diff = abs(home_goals - away_goals)
    if diff <= 1: return 1.0
    elif diff == 2: return 1.5
    else: return (11.0 + diff) / 8.0

def get_fair_odds(prob): return (100 / prob) if prob > 1.0 else 99.99

def is_dynamic_value(fair_prob, book_odd):
    if fair_prob <= 0 or book_odd <= 1.0: return False, 0.0
    fair_odd = 100 / fair_prob
    edge = book_odd / fair_odd
    min_edge = 1.05 + (book_odd * 0.015)
    max_edge = 1.55 
    return (min_edge < edge <= max_edge), edge

def calculate_kelly(prob_percent, odds):
    if odds <= 1.0 or prob_percent <= 0: return 0.0
    p = prob_percent / 100.0
    q = 1.0 - p
    b = odds - 1.0
    kelly_fraction = (p * b - q) / b
    return max(0.0, (kelly_fraction * 100) / 4.0)

def get_risk_label(prob):
    if prob >= 65: return '<span style="background:#059669; color:white; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold;">🏦 BANKO</span>'
    elif prob >= 55: return '<span style="background:#10b981; color:white; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold;">🟢 GÜVENLİ</span>'
    elif prob >= 38: return '<span style="background:#f59e0b; color:white; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold;">🟡 DENGELİ</span>'
    else: return '<span style="background:#ef4444; color:white; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold;">🔴 SÜRPRİZ</span>'

def calculate_nbinom_prob(expected_value, over_line, variance_multiplier=1.25):
    if expected_value <= 0: return 0
    variance = expected_value * variance_multiplier
    p = expected_value / variance
    r = (expected_value ** 2) / (variance - expected_value)
    prob_under = nbinom.cdf(np.floor(over_line), r, p)
    return (1 - prob_under) * 100

def calculate_normal_prob(expected_value, over_line, std_dev=3.5):
    if expected_value <= 0: return 0
    prob_over = norm.sf(over_line, loc=expected_value, scale=std_dev)
    return prob_over * 100

def get_prop_projections(h_att, h_def, a_att, a_def):
    base_corners, base_shots_on = 9.5, 8.5
    h_dom = (h_att / max(0.1, a_def))
    a_dom = (a_att / max(0.1, h_def))
    total_corners_exp = (base_corners * 0.55 * h_dom) + (base_corners * 0.45 * a_dom)
    total_shots_exp = (base_shots_on * 0.55 * h_dom) + (base_shots_on * 0.45 * a_dom)
    
    prob_cor_9_5 = calculate_nbinom_prob(total_corners_exp, 9.5, variance_multiplier=1.2)
    prob_sho_8_5 = calculate_normal_prob(total_shots_exp, 8.5, std_dev=2.2)
    return prob_cor_9_5, prob_sho_8_5

# --- VERİ ÇEKME MODÜLLERİ (STREAMLIT CACHE İLE API KORUMASI) ---
@st.cache_data(ttl=3600)
def fetch_fixtures(api_key, target_date):
    headers = {"x-apisports-key": api_key}
    try:
        resp = requests.get(f"{BASE_URL}/fixtures?date={target_date}", headers=headers).json()
        if "response" not in resp: return []
        target_matches = [m for m in resp.get("response", []) if m["fixture"]["status"]["short"] == "NS" and not any(b in f"{m['league']['country']} {m['league']['name']}".lower() for b in BANNED_KEYWORDS)]
        return target_matches
    except: return []

@st.cache_data(ttl=21600)
def calculate_league_stats(api_key, l_id, season):
    headers = {"x-apisports-key": api_key}
    stats, avg_h, avg_a, league_rho, league_k = {}, 1.4, 1.2, -0.14, 20
    try:
        fin_prev = requests.get(f"{BASE_URL}/fixtures?league={l_id}&season={season-1}&status=FT", headers=headers).json().get("response", [])
        elo_db = {}
        
        if fin_prev:
            for f in fin_prev:
                h, a = f["teams"]["home"]["name"], f["teams"]["away"]["name"]
                hg, ag = f["goals"]["home"], f["goals"]["away"]
                if hg is None or ag is None: continue
                elo_db.setdefault(h, 1500); elo_db.setdefault(a, 1500)
                rh, ra = 10**((elo_db[h] + HFA_ELO_BONUS) / 400), 10**(elo_db[a] / 400)
                sh, sa = (1, 0) if hg > ag else (0, 1) if ag > hg else (0.5, 0.5)
                mov = get_mov_multiplier(hg, ag)
                elo_db[h] += league_k * mov * (sh - rh/(rh+ra))
                elo_db[a] += league_k * mov * (sa - ra/(rh+ra))
        
        for team in elo_db:
            elo_db[team] = apply_elo_mean_reversion(elo_db[team], mean_elo=1500, reversion_rate=0.30)
            
        stand_resp = requests.get(f"{BASE_URL}/standings?league={l_id}&season={season}", headers=headers).json()
        fin = requests.get(f"{BASE_URL}/fixtures?league={l_id}&season={season}&status=FT", headers=headers).json().get("response", [])
        
        all_matches_for_avg = fin if len(fin) > 30 else (fin_prev + fin)
        if all_matches_for_avg:
            h_goals = [f["goals"]["home"] for f in all_matches_for_avg if f["goals"]["home"] is not None]
            a_goals = [f["goals"]["away"] for f in all_matches_for_avg if f["goals"]["away"] is not None]
            avg_h = np.mean(h_goals) if h_goals else 1.4
            avg_a = np.mean(a_goals) if a_goals else 1.2
            league_rho, league_k = get_dynamic_params(avg_h + avg_a)

        for f in fin:
            h, a = f["teams"]["home"]["name"], f["teams"]["away"]["name"]
            hg, ag = f["goals"]["home"], f["goals"]["away"]
            if hg is None or ag is None: continue
            elo_db.setdefault(h, 1400); elo_db.setdefault(a, 1400)
            rh, ra = 10**((elo_db[h] + HFA_ELO_BONUS) / 400), 10**(elo_db[a] / 400)
            sh, sa = (1, 0) if hg > ag else (0, 1) if ag > hg else (0.5, 0.5)
            mov = get_mov_multiplier(hg, ag)
            elo_db[h] += league_k * mov * (sh - rh/(rh+ra))
            elo_db[a] += league_k * mov * (sa - ra/(rh+ra))
            
        if stand_resp.get("response") and len(stand_resp["response"]) > 0:
            for t in stand_resp["response"][0]["league"]["standings"][0]:
                nm = t["team"]["name"]
                stats[nm] = {
                    "att_h": ((t["home"]["goals"]["for"] + 5*avg_h) / (t["home"]["played"] + 5)) / avg_h if t["home"]["played"] > 0 else 1.0,
                    "def_a": ((t["away"]["goals"]["against"] + 5*avg_h) / (t["away"]["played"] + 5)) / avg_h if t["away"]["played"] > 0 else 1.0,
                    "att_a": ((t["away"]["goals"]["for"] + 5*avg_a) / (t["away"]["played"] + 5)) / avg_a if t["away"]["played"] > 0 else 1.0,
                    "def_h": ((t["home"]["goals"]["against"] + 5*avg_a) / (t["home"]["played"] + 5)) / avg_a if t["home"]["played"] > 0 else 1.0,
                    "elo": elo_db.get(nm, 1400)
                }
        
        return {"stats": stats, "avg_h": avg_h, "avg_a": avg_a, "rho": league_rho, "k": league_k}
    except: 
        return {"stats": {}, "avg_h": 1.4, "avg_a": 1.2, "rho": -0.14, "k": 20}

@st.cache_data(ttl=3600)
def get_market_max_odds(api_key, fixture_id):
    headers = {"x-apisports-key": api_key}
    odds = {"1": [], "X": [], "2": [], "o25": []}
    max_odds = {"1": 0.0, "X": 0.0, "2": 0.0, "o25": 0.0}
    try:
        resp_data = requests.get(f"{BASE_URL}/odds?fixture={fixture_id}", headers=headers).json().get("response", [])
        if not resp_data: return max_odds
        for bk in resp_data[0].get("bookmakers", []):
            if bk["id"] in TARGET_BOOKIES:
                for bet in bk.get("bets", []):
                    if bet["name"] == "Match Winner":
                        for v in bet["values"]:
                            if v["value"] == "Home": odds["1"].append(float(v["odd"]))
                            elif v["value"] == "Draw": odds["X"].append(float(v["odd"]))
                            elif v["value"] == "Away": odds["2"].append(float(v["odd"]))
                    elif bet["name"] == "Goals Over/Under":
                        for v in bet["values"]: 
                            if v["value"] == "Over 2.5": odds["o25"].append(float(v["odd"]))
                            
        for key in max_odds.keys():
            if len(odds[key]) > 0: max_odds[key] = max(odds[key])
    except: pass
    return max_odds

# --- STREAMLIT ARAYÜZ (UI) ---
st.markdown('<div style="background:#0f172a; color:#f8fafc; padding:20px; text-align:center; border-radius:12px 12px 0 0; margin-bottom:15px; border-bottom: 3px solid #f59e0b;"><h1 style="margin:0; font-size:28px; color:#fbbf24;">🛡️ FOOTBALL ORACLE v20.0 TITAN (WEB EDITION)</h1><p style="margin:5px 0 0 0; opacity:0.8; font-size:14px;">Korner (Negatif Binom), İsabetli Şut (Normal Dağılım), MoV Devrede</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    api_key_input = st.text_input("🔑 API KEY:", type="password")
with col2:
    date_options = [(datetime.datetime.now() + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(14)]
    display_options = [(("Bugün" if i == 0 else "Yarın" if i == 1 else d) + f" ({(datetime.datetime.now() + datetime.timedelta(days=i)).strftime('%A')})") for i, d in enumerate(date_options)]
    selected_date_display = st.selectbox("📅 TARİH SEÇİNİZ:", display_options)
    target_date = date_options[display_options.index(selected_date_display)]

st.markdown("### 🔍 Radar Filtreleri")
f_col1, f_col2, f_col3, f_col4 = st.columns(4)
with f_col1: only_value = st.checkbox("💎 Dinamik Value", value=True)
with f_col2: only_safe = st.checkbox("🟢 Güvenli (≥%55)")
with f_col3: only_banko = st.checkbox("🏦 Banko (≥%65)")
with f_col4: only_over = st.checkbox("⚽ Sadece Üst")

if st.button("🚀 TITAN v20.0 MOTORUNU ATEŞLE", type="primary", use_container_width=True):
    if not api_key_input:
        st.error("❌ Lütfen önce API Key giriniz!")
    else:
        with st.spinner(f"📡 API'ye bağlanılıyor... Tarama başlatıldı: {target_date} (Bu işlem 1-3 dakika sürebilir, lütfen sekmeyi kapatmayın)"):
            target_matches = fetch_fixtures(api_key_input, target_date)
            
            if not target_matches:
                st.warning("Bu tarih için uygun/bekleyen maç bulunamadı.")
            else:
                html = """
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
                    .ultimate-table { width: 100%; border-collapse: separate; border-spacing: 0 5px; font-family: 'Inter', sans-serif;}
                    .ultimate-table thead th { background: #e2e8f0; color: #334155; padding: 8px; font-size: 11px; text-transform: uppercase; }
                    .match-row td { background: white; padding: 10px 8px; border-bottom: 1px solid #e2e8f0; font-size: 13px; text-align: center; color: black; }
                    .value-cell { border: 2.5px solid #10b981 !important; background: #ecfdf5 !important; border-radius: 8px; font-weight: bold; }
                    .score-pill { background: #4f46e5; color: white; padding: 3px 8px; border-radius: 999px; font-weight: 700; font-size: 12px; }
                    .prop-cell { background: #fffbeb; color: #b45309; font-weight: 700; border: 1px solid #fde68a; border-radius: 6px; }
                </style>
                """
                insight_list = []
                matches_rendered = 0
                grouped_matches = {}
                for m in target_matches: grouped_matches.setdefault(m["league"]["id"], []).append(m)

                for l_id, matches in grouped_matches.items():
                    league_name = f"{matches[0]['league']['country']} - {matches[0]['league']['name']}"
                    season = matches[0]["league"]["season"]
                    league_html = ""
                    league_has_value = False
                    
                    l_data = calculate_league_stats(api_key_input, l_id, season)
                    stats, avg_h, avg_a, league_rho = l_data["stats"], l_data["avg_h"], l_data["avg_a"], l_data["rho"]

                    for m in matches:
                        fid = m["fixture"]["id"]
                        odds = get_market_max_odds(api_key_input, fid) 
                        if odds["1"] == 0 and odds["X"] == 0: continue

                        h, a = m["teams"]["home"]["name"], m["teams"]["away"]["name"]
                        h_s = stats.get(h, {"att_h": 1.0, "def_h": 1.0, "elo": 1400})
                        a_s = stats.get(a, {"att_a": 1.0, "def_a": 1.0, "elo": 1400})
                        
                        lh = max(0.1, (0.65 * (h_s["att_h"] * a_s["def_a"] * avg_h)) + (0.35 * (avg_h * (1 + ((h_s["elo"] + HFA_ELO_BONUS) - a_s["elo"] + 70)/400))))
                        la = max(0.1, (0.65 * (a_s["att_a"] * h_s["def_h"] * avg_a)) + (0.35 * (avg_a * (1 - ((h_s["elo"] + HFA_ELO_BONUS) - a_s["elo"] + 70)/400))))
                        
                        mx = apply_dixon_coles(np.outer(poisson.pmf(np.arange(10), lh), poisson.pmf(np.arange(10), la)), lh, la, league_rho)
                        p1, pX, p2 = np.tril(mx, -1).sum()*100, np.trace(mx)*100, np.triu(mx, 1).sum()*100
                        o25 = mx[np.indices(mx.shape)[0] + np.indices(mx.shape)[1] >= 2.5].sum()*100
                        score = np.unravel_index(np.argmax(mx), mx.shape)
                        
                        p_cor_95, p_sho_85 = get_prop_projections(h_s["att_h"], h_s["def_h"], a_s["att_a"], a_s["def_a"])
                        
                        is_v1, edge_1 = is_dynamic_value(p1, odds["1"])
                        is_vX, edge_X = is_dynamic_value(pX, odds["X"])
                        is_v2, edge_2 = is_dynamic_value(p2, odds["2"])
                        is_vo, edge_o = is_dynamic_value(o25, odds["o25"])
                        
                        if only_value and not any([is_v1, is_vX, is_v2, is_vo]): continue
                        if only_safe and not any(p >= 55 for p in [p1, pX, p2, o25]): continue
                        if only_banko and not any(p >= 65 for p in [p1, pX, p2, o25]): continue

                        league_has_value = True; matches_rendered += 1
                        t_str = (datetime.datetime.fromtimestamp(m["fixture"]["timestamp"], datetime.timezone.utc) + datetime.timedelta(hours=3)).strftime('%d.%m %H:%M')
                        
                        def render_cell(prob, book, is_val):
                            if only_safe and prob < 55: is_val = False 
                            if only_banko and prob < 65: is_val = False 
                            c = "class='value-cell'" if is_val else ""
                            return f'<td {c}><div style="font-weight:700;">%{prob:.1f}</div><span style="font-size:10px; color:#6366f1;">[{get_fair_odds(prob):.2f}]</span><br><b style="font-size:12px;">{book if book>0 else "-"}</b></td>'

                        league_html += f"<tr class='match-row'><td style='color:#64748b; font-weight:700;'>{t_str[-5:]}</td>"
                        league_html += f"<td style='text-align:left; font-weight:700;'>{h}<br><span style='font-weight:400; font-size:10px;'>vs</span><br>{a}</td>"
                        league_html += render_cell(p1, odds["1"], is_v1) + render_cell(pX, odds["X"], is_vX) + render_cell(p2, odds["2"], is_v2) + render_cell(o25, odds["o25"], is_vo)
                        league_html += f"<td class='prop-cell'>%{p_cor_95:.1f}</td><td class='prop-cell'>%{p_sho_85:.1f}</td>"
                        league_html += f"<td><span class='score-pill'>{score[0]}-{score[1]}</span></td></tr>"

                        for p, o, is_v, edge, t, icon in [(p1, odds["1"], is_v1, edge_1, "MS 1", "🏠"), (pX, odds["X"], is_vX, edge_X, "MS X", "⚖️"), (p2, odds["2"], is_v2, edge_2, "MS 2", "🚀"), (o25, odds["o25"], is_vo, edge_o, "ÜST", "⚽")]:
                            if only_over and t != "ÜST": continue 
                            if is_v:
                                if only_safe and p < 55: continue 
                                if only_banko and p < 65: continue
                                insight_list.append({
                                    "icon": icon, "team": h if t=="MS 1" else a if t=="MS 2" else t, 
                                    "match": f"{h} - {a}", "odd": o, "fair": get_fair_odds(p), 
                                    "margin": (edge-1)*100, "league": league_name, "type": t, 
                                    "risk": get_risk_label(p), "p_xg": lh+la, "time": t_str, "kelly": calculate_kelly(p, o)
                                })

                    if league_has_value:
                        html += f'<div style="background: #1e1b4b; color: #e0e7ff; padding: 10px 15px; font-weight: 700; border-radius: 8px; margin: 20px 0 10px 0; border-left: 4px solid #6366f1;">🌍 {league_name}</div>'
                        html += '<table class="ultimate-table"><thead><tr><th>Saat</th><th style="text-align:left;">Eşleşme</th><th>MS 1</th><th>MS X</th><th>MS 2</th><th>2.5 ÜST</th><th>9.5 KORNER</th><th>8.5 İ. ŞUT</th><th>Skor</th></tr></thead><tbody>' + league_html + '</tbody></table>'

                if matches_rendered == 0:
                    st.warning("🛑 Kriterlere uygun maç bulunamadı. Filtreleri esnetip tekrar deneyin.")
                else:
                    st.markdown(html, unsafe_allow_html=True)
                    st.success(f"✅ Analiz Tamamlandı! {matches_rendered} maç listelendi.")
                    
                    if len(insight_list) > 0:
                        df = pd.DataFrame(insight_list)
                        def clean_html(raw_html): return re.sub(re.compile('<.*?>'), '', str(raw_html)).strip()
                        df['risk'] = df['risk'].apply(clean_html)
                        df = df[['time', 'league', 'match', 'type', 'fair', 'odd', 'margin', 'kelly', 'p_xg', 'risk']]
                        df.columns = ['Saat', 'Lig', 'Eşleşme', 'Bahis', 'Adil Oran', 'Piyasa Max Oranı', 'Value (%)', 'Çeyrek Kelly (%)', 'p_xG', 'Risk']
                        df['Adil Oran'] = df['Adil Oran'].round(2)
                        df['Value (%)'] = df['Value (%)'].round(1)
                        df['Çeyrek Kelly (%)'] = df['Çeyrek Kelly (%)'].round(1)
                        df['p_xG'] = df['p_xG'].round(2)
                        
                        st.markdown("### 📊 Detaylı Value Analiz Tablosu")
                        st.dataframe(df, use_container_width=True)
                        
                        # Excel İndirme Butonu
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False, sheet_name='Analiz')
                        st.download_button(
                            label="📥 Excel Olarak İndir",
                            data=output.getvalue(),
                            file_name=f"titan_v20_{target_date}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
