# ==============================
# FOOTBALL ORACLE v20.0 TITAN (MoV + PROP BETTING EDITION)
# GOL FARKI ELO + KORNER (NEGATİF BİNOM) + ŞUT (NORMAL DAĞILIM) + LİG FİLTRESİ
# ==============================

import requests
import numpy as np
from scipy.stats import poisson, nbinom, norm
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import time
import datetime
import pandas as pd
import re

# --- AYARLAR VE HAFIZA ---
CACHE_TTL = 3600 * 6
HFA_ELO_BONUS = 75
BASE_URL = "https://v3.football.api-sports.io"
TARGET_BOOKIES = [1, 8, 11, 17]

if 'api_cache_global' not in globals(): api_cache_global = {}
if 'league_stats_cache' not in globals(): league_stats_cache = {}

req_session = requests.Session()

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

# --- PROP BAHİSLERİ İÇİN MATEMATİK MODELLERİ ---

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
    base_corners = 9.5
    base_shots_on = 8.5
    
    h_dom = (h_att / max(0.1, a_def))
    a_dom = (a_att / max(0.1, h_def))
    
    total_corners_exp = (base_corners * 0.55 * h_dom) + (base_corners * 0.45 * a_dom)
    total_shots_exp = (base_shots_on * 0.55 * h_dom) + (base_shots_on * 0.45 * a_dom)
    
    prob_cor_9_5 = calculate_nbinom_prob(total_corners_exp, 9.5, variance_multiplier=1.2)
    prob_sho_8_5 = calculate_normal_prob(total_shots_exp, 8.5, std_dev=2.2)
    
    return prob_cor_9_5, prob_sho_8_5

# --- VERİ ÇEKME MODÜLLERİ ---

def fetch_fixtures(api_key, target_date):
    req_session.headers.update({"x-apisports-key": api_key})
    date_cache_key = f"fixtures_v20_{target_date}"
    now = time.time()
    
    if date_cache_key in api_cache_global and now - api_cache_global[date_cache_key]["time"] < CACHE_TTL:
        return api_cache_global[date_cache_key]["data"]
    
    try:
        resp = req_session.get(f"{BASE_URL}/fixtures?date={target_date}").json()
        if "response" not in resp: return []
        target_matches = [m for m in resp.get("response", []) if m["fixture"]["status"]["short"] == "NS" and not any(b in f"{m['league']['country']} {m['league']['name']}".lower() for b in BANNED_KEYWORDS)]
        api_cache_global[date_cache_key] = {"time": now, "data": target_matches}
        return target_matches
    except: return []

def calculate_league_stats(l_id, season):
    l_cache_key = f"stats_v20_coldstart_{l_id}_{season}"
    now = time.time()
    if l_cache_key in league_stats_cache and now - league_stats_cache[l_cache_key]["time"] < CACHE_TTL:
        return league_stats_cache[l_cache_key]

    stats, avg_h, avg_a, league_rho, league_k = {}, 1.4, 1.2, -0.14, 20
    try:
        fin_prev = req_session.get(f"{BASE_URL}/fixtures?league={l_id}&season={season-1}&status=FT").json().get("response", [])
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
            
        stand_resp = req_session.get(f"{BASE_URL}/standings?league={l_id}&season={season}").json()
        fin = req_session.get(f"{BASE_URL}/fixtures?league={l_id}&season={season}&status=FT").json().get("response", [])
        
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
        
        result_data = {"stats": stats, "avg_h": avg_h, "avg_a": avg_a, "rho": league_rho, "k": league_k, "time": now}
        league_stats_cache[l_cache_key] = result_data
        return result_data
    except Exception as e:
        return {"stats": {}, "avg_h": 1.4, "avg_a": 1.2, "rho": -0.14, "k": 20, "time": now}

def get_market_max_odds(fixture_id):
    odds = {"1": [], "X": [], "2": [], "o25": []}
    max_odds = {"1": 0.0, "X": 0.0, "2": 0.0, "o25": 0.0}
    try:
        resp_data = req_session.get(f"{BASE_URL}/odds?fixture={fixture_id}").json().get("response", [])
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

# --- ANA MOTOR (ORCHESTRATOR) ---

def oracle_titan_scan(b):
    with radar_out:
        clear_output()
        api_key = api_in_fd.value.strip()
        target_date = date_drop.value
        selected_league = league_drop.value
        only_value = value_cb.value
        only_safe = safe_cb.value
        only_banko = banko_cb.value
        only_over = over_cb.value
        
        if not api_key: print("❌ Önce API Key girmelisin!"); return
        print(f"🚀 TITAN v20.0 (PROP & MoV MOTORU) Tarama Başlatılıyor: {target_date}...")

        target_matches = fetch_fixtures(api_key, target_date)
        if not target_matches: return

        html = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            .ultimate-container { font-family: 'Inter', sans-serif; background: #f4f7f9; padding: 10px; border-radius: 15px; }
            .league-header { background: #1e1b4b; color: #e0e7ff; padding: 10px 15px; font-weight: 700; border-radius: 8px; margin: 20px 0 10px 0; border-left: 4px solid #6366f1;}
            .ultimate-table { width: 100%; border-collapse: separate; border-spacing: 0 5px; }
            .ultimate-table thead th { background: #e2e8f0; color: #334155; padding: 8px; font-size: 10px; text-transform: uppercase; }
            .match-row td { background: white; padding: 10px 8px; border-bottom: 1px solid #e2e8f0; font-size: 12px; text-align: center; }
            .value-cell { border: 2.5px solid #10b981 !important; background: #ecfdf5 !important; border-radius: 8px; font-weight: bold; }
            .score-pill { background: #4f46e5; color: white; padding: 3px 8px; border-radius: 999px; font-weight: 700; font-size: 11px; }
            .prop-cell { background: #fffbeb; color: #b45309; font-weight: 700; border: 1px solid #fde68a; border-radius: 6px; }
        </style>
        <div class="ultimate-container">
        """

        insight_list = []
        matches_rendered = 0
        grouped_matches = {}
        for m in target_matches: grouped_matches.setdefault(m["league"]["id"], []).append(m)

        for l_id, matches in grouped_matches.items():
            if selected_league != 'ALL' and str(l_id) != str(selected_league):
                continue
                
            league_name = f"{matches[0]['league']['country']} - {matches[0]['league']['name']}"
            season = matches[0]["league"]["season"]
            league_html = ""
            league_has_value = False
            
            l_data = calculate_league_stats(l_id, season)
            stats, avg_h, avg_a, league_rho = l_data["stats"], l_data["avg_h"], l_data["avg_a"], l_data["rho"]

            for m in matches:
                fid = m["fixture"]["id"]
                odds = get_market_max_odds(fid)
                if odds["1"] == 0 and odds["X"] == 0: continue

                h, a = m["teams"]["home"]["name"], m["teams"]["away"]["name"]
                h_s = stats.get(h, {"att_h": 1.0, "def_h": 1.0, "elo": 1400}); a_s = stats.get(a, {"att_a": 1.0, "def_a": 1.0, "elo": 1400})
                
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
                    return f'<td {c}><div style="font-weight:700;">%{prob:.1f}</div><span style="font-size:9px; color:#6366f1;">[{get_fair_odds(prob):.2f}]</span><br><b style="font-size:11px;">{book if book>0 else "-"}</b></td>'

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
                html += f'<div class="league-header">🌍 {league_name}</div>'
                html += '<table class="ultimate-table"><thead><tr><th>Saat</th><th style="text-align:left;">Eşleşme</th><th>MS 1</th><th>MS X</th><th>MS 2</th><th>2.5 ÜST</th><th>9.5 KORNER</th><th>8.5 İ. ŞUT</th><th>Skor</th></tr></thead><tbody>' + league_html + '</tbody></table>'

        html += "</div>"; clear_output()
        if matches_rendered == 0:
            print("🛑 Kriterlere uygun maç bulunamadı. (Filtreler çok sıkı olabilir veya seçtiğiniz ligde bugün maç yok.)")
        else:
            commentary = '<div style="background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%); color: white; padding: 20px; border-radius: 12px; margin-top: 20px;">'
            commentary += f'<h3 style="color:#34d399;">🛡️ TITAN v20.0 PRO RADARI ({len(insight_list)} Value Fırsatı)</h3><div class="report-scroll" style="max-height: 450px; overflow-y: auto;">'
            for it in sorted(insight_list, key=lambda x: x["margin"], reverse=True):
                kelly_badge = f'<span style="background:#10b981; color:white; padding:2px 6px; border-radius:4px; font-size:11px; margin-left:5px;">💰 Çeyrek Kelly: %{it["kelly"]:.1f}</span>' if it["kelly"] > 0 else ''
                commentary += f'''
                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(16,185,129,0.3); padding: 12px; border-radius: 8px; margin-bottom: 10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div><b style="color:#fcd34d;">{it['icon']} {it['team']}</b> {kelly_badge}</div>
                        <span style="background:#10b981; color:white; padding:2px 6px; border-radius:4px; font-size:12px; font-weight:bold;">%{it['margin']:.1f} VALUE</span>
                    </div>
                    <div style="font-size:13px; margin-top:8px;">Bahis: <b>{it['type']}</b> | Adil: <b style="color:#38bdf8;">{it['fair']:.2f}</b> | Piyasa: <b style="color:#f472b6;">{it['odd']:.2f}</b></div>
                    <div style="font-size:11px; color:#94a3b8; margin-top:6px; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 6px;">
                        🌍 <span style="color:#e2e8f0; font-weight:600;">{it['league']}</span><br>🕒 {it['time']} | ⚔️ {it['match']} | p_xG: {it['p_xg']:.2f} | {it['risk']}
                    </div>
                </div>'''
            display(HTML(html + commentary + '</div></div>'))
            
            # EXCEL EXPORT
            if len(insight_list) > 0:
                df = pd.DataFrame(insight_list)
                def clean_html(raw_html): return re.sub(re.compile('<.*?>'), '', raw_html).strip()
                df['risk'] = df['risk'].apply(clean_html)
                df = df[['time', 'league', 'match', 'type', 'fair', 'odd', 'margin', 'kelly', 'p_xg', 'risk']]
                df.columns = ['Saat', 'Lig', 'Eşleşme', 'Bahis', 'Adil Oran', 'Piyasa Max Oranı', 'Value (%)', 'Çeyrek Kelly (%)', 'p_xG', 'Risk']
                df['Adil Oran'] = df['Adil Oran'].round(2)
                df['Value (%)'] = df['Value (%)'].round(1)
                df['Çeyrek Kelly (%)'] = df['Çeyrek Kelly (%)'].round(1)
                df['p_xG'] = df['p_xG'].round(2)
                
                file_name = f"titan_v20_raporu_{target_date}.xlsx"
                df.to_excel(file_name, index=False)
                print(f"✅ Excel Dosyası Oluşturuldu: '{file_name}'")

# --- ARAYÜZ (UI) KURULUMU ---
date_options = [(("Bugün" if i == 0 else "Yarın" if i == 1 else (datetime.datetime.now() + datetime.timedelta(days=i)).strftime('%d.%m.%Y')) + f" ({(datetime.datetime.now() + datetime.timedelta(days=i)).strftime('%A')})", (datetime.datetime.now() + datetime.timedelta(days=i)).strftime('%Y-%m-%d')) for i in range(14)]

# KAPSAMLI LİG LİSTESİ
league_options = [
    ('🌍 Tüm Ligler', 'ALL'),
    ('🇬🇧 İngiltere Premier Lig', 39),
    ('🇹🇷 Türkiye Süper Lig', 203),
    ('🇪🇸 İspanya La Liga', 140),
    ('🇩🇪 Almanya Bundesliga', 78),
    ('🇮🇹 İtalya Serie A', 135),
    ('🇫🇷 Fransa Ligue 1', 61),
    ('🏆 Şampiyonlar Ligi', 2),
    ('🏆 Avrupa Ligi', 3),
    ('🏆 Konferans Ligi', 848),
    ('🇹🇷 Türkiye 1. Lig', 204),
    ('🇬🇧 İngiltere Championship', 40),
    ('🇪🇸 İspanya La Liga 2', 141),
    ('🇩🇪 Almanya 2. Bundesliga', 79),
    ('🇮🇹 İtalya Serie B', 136),
    ('🇳🇱 Hollanda Eredivisie', 88),
    ('🇵🇹 Portekiz Primeira Liga', 94),
    ('🇧🇪 Belçika Pro League', 144),
    ('🏴󠁧󠁢󠁳󠁣󠁴󠁿 İskoçya Premiership', 179),
    ('🇬🇷 Yunanistan Süper Lig', 197),
    ('🇨🇭 İsviçre Süper Lig', 207),
    ('🇩🇰 Danimarka Süper Lig', 119),
    ('🇸🇪 İsveç Allsvenskan', 113),
    ('🇳🇴 Norveç Eliteserien', 103),
    ('🇧🇷 Brezilya Serie A', 71),
    ('🇦🇷 Arjantin Liga Profesional', 128),
    ('🇺🇸 ABD MLS', 253),
    ('🇲🇽 Meksika Liga MX', 262)
]

api_in_fd = widgets.Password(description='🔑 API KEY:', layout={'width': '80%'})
date_drop = widgets.Dropdown(options=date_options, description='📅 TARİH:', layout={'width': '40%'})
league_drop = widgets.Dropdown(options=league_options, description='🏆 LİG:', layout={'width': '40%'})

value_cb = widgets.Checkbox(value=True, description='💎 Dinamik Value', layout={'width': 'auto'}, style={'description_width': 'initial'})
safe_cb = widgets.Checkbox(value=False, description='🟢 Güvenli (≥%55)', layout={'width': 'auto'}, style={'description_width': 'initial'})
banko_cb = widgets.Checkbox(value=False, description='🏦 Banko (≥%65)', layout={'width': 'auto'}, style={'description_width': 'initial'})
over_cb = widgets.Checkbox(value=False, description='⚽ Sadece Üst', layout={'width': 'auto'}, style={'description_width': 'initial'})

scan_btn = widgets.Button(description="🚀 TITAN v20.0 MOTORUNU ATEŞLE", button_style='primary', layout={'width': '80%', 'height': '50px', 'font_weight': 'bold'})
radar_out = widgets.Output()
scan_btn.on_click(oracle_titan_scan)

header_html = widgets.HTML('<div style="background:#0f172a; color:#f8fafc; padding:20px; text-align:center; border-radius:12px 12px 0 0; margin-bottom:15px; border-bottom: 3px solid #f59e0b;"><h1 style="margin:0; font-size:24px; color:#fbbf24;">🛡️ FOOTBALL ORACLE v20.0 TITAN (PROP EDITION)</h1><p style="margin:5px 0 0 0; opacity:0.8; font-size:12px;">Korner (Negatif Binom), İsabetli Şut (Normal Dağılım), MoV ve Lig Filtresi Devrede</p></div>')

api_row = widgets.HBox([api_in_fd], layout={'justify_content': 'center', 'margin': '10px 0'})
date_league_row = widgets.HBox([date_drop, league_drop], layout={'justify_content': 'center', 'margin': '10px 0', 'grid_gap': '20px'})
filters_html = widgets.HTML('<div style="text-align:center; font-weight:bold; color:#475569; margin-bottom:5px; margin-top:10px;">🔍 RADAR FİLTRELERİ</div>')
filters_box = widgets.HBox([value_cb, safe_cb, banko_cb, over_cb], layout={'justify_content': 'space-around', 'flex_flow': 'row wrap'})
filters_panel = widgets.VBox([filters_html, filters_box], layout={'margin': '10px 10%', 'padding': '15px', 'border': '1px solid #cbd5e1', 'border_radius': '10px', 'background_color': '#f8fafc'})
btn_row = widgets.HBox([scan_btn], layout={'justify_content': 'center', 'margin': '20px 0 10px 0'})

ui = widgets.VBox([
    header_html,
    api_row,
    date_league_row,
    filters_panel,
    btn_row,
    radar_out
], layout={'width': '100%', 'max_width': '950px', 'margin': 'auto', 'border': '1px solid #e2e8f0', 'border_radius': '15px', 'background': '#ffffff', 'padding': '10px'})

display(ui)
