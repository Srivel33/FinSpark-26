import streamlit as st
import pandas as pd
import numpy as np
import time
import joblib
import json
import os
import plotly.graph_objects as go
from datetime import datetime

# ====================================================================
# PAGE CONFIGURATION
# ====================================================================
st.set_page_config(
    page_title="FinSpark Sentinel | SOC Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================================================================
# CUSTOM CSS (Premium Enterprise SOC Dark Theme)
# ====================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global Theme - Deep Dark Enterprise */
    :root {
        --bg-main: #0a0e17;
        --bg-panel: rgba(17, 24, 39, 0.75);
        --bg-card: rgba(31, 41, 55, 0.5);
        --border-subtle: rgba(255, 255, 255, 0.06);
        --border-glow: rgba(59, 130, 246, 0.35);
        --text-primary: #f3f4f6;
        --text-secondary: #9ca3af;
        --text-muted: #6b7280;
        --accent-blue: #3b82f6;
        --accent-cyan: #06b6d4;
        --risk-low: #10b981;
        --risk-med: #f59e0b;
        --risk-high: #f97316;
        --risk-crit: #ef4444;
    }
    
    .stApp {
        background-color: var(--bg-main);
        color: var(--text-primary);
        font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    /* Reduce Streamlit Whitespace */
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 95% !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* --- SCANNING BAR (persistent, no layout shift) --- */
    .scan-bar-wrap {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 10px;
        padding: 12px 20px;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        gap: 14px;
        overflow: hidden;
        position: relative;
    }
    .scan-bar-wrap::before {
        content: '';
        position: absolute;
        top: 0; left: -100%; width: 60%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(59,130,246,0.08), transparent);
        animation: scanSlide 2.5s linear infinite;
    }
    @keyframes scanSlide { 0% { left: -100%; } 100% { left: 200%; } }
    .scan-dot {
        width: 10px; height: 10px; border-radius: 50%;
        background: var(--accent-blue);
        box-shadow: 0 0 8px var(--accent-blue);
        animation: pulseDot 1.2s ease-in-out infinite;
        flex-shrink: 0;
    }
    @keyframes pulseDot { 0%,100% { transform: scale(0.8); opacity: 0.6; } 50% { transform: scale(1.2); opacity: 1; } }
    .scan-label { font-size: 0.88rem; color: var(--text-secondary); font-weight: 500; flex: 1; }
    .scan-pct { font-size: 1.15rem; font-weight: 800; color: var(--accent-blue); }
    .scan-progress-bg {
        flex: 1; height: 5px; border-radius: 3px;
        background: rgba(255,255,255,0.08);
        overflow: hidden;
    }
    .scan-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #3b82f6, #06b6d4);
        border-radius: 3px;
        transition: width 0.4s ease;
    }

    /* Enterprise SOC Panels */
    .soc-panel {
        background: var(--bg-panel);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 22px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        margin-bottom: 15px;
        transition: box-shadow 0.2s, border-color 0.2s;
        overflow: hidden;
    }
    .soc-panel:hover {
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
        border-color: var(--border-glow);
    }
    
    .soc-header {
        font-size: 0.8rem;
        font-weight: 700;
        color: var(--text-secondary);
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
        border-bottom: 1px solid var(--border-subtle);
        padding-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }

    /* KPI Cards */
    .soc-kpi {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 10px;
        padding: 15px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        transition: transform 0.2s, border-color 0.2s;
        position: relative;
        overflow: hidden;
    }
    .soc-kpi:hover { transform: translateY(-4px); border-color: var(--accent-cyan); }
    .kpi-title { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
    .kpi-value { font-size: 2.2rem; font-weight: 800; color: var(--text-primary); line-height: 1; }
    .kpi-glow { position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent, var(--accent-blue), transparent); }

    /* Custom Data Fields (Grouped) */
    .data-group { margin-bottom: 16px; }
    .data-group-title {
        font-size: 0.68rem; color: var(--accent-blue); text-transform: uppercase;
        letter-spacing: 2px; margin-bottom: 8px; font-weight: 700;
        display: flex; align-items: center; gap: 5px;
    }
    .data-group-title::after { content: ''; flex: 1; height: 1px; background: rgba(59,130,246,0.2); }
    .field-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
        font-size: 0.875rem;
    }
    .field-row:last-child { border-bottom: none; }
    .field-label { color: var(--text-muted); flex-shrink: 0; padding-right: 16px; min-width: 90px; }
    .field-value { color: var(--text-primary); font-weight: 600; text-align: right; }

    /* Correlation Engine Flow */
    .corr-container { display: flex; flex-direction: column; gap: 10px; }
    .corr-row {
        display: flex; align-items: center; background: rgba(0,0,0,0.2);
        border-radius: 8px; padding: 12px; border: 1px solid var(--border-subtle);
        position: relative;
    }
    .corr-col { flex: 1; font-size: 0.85rem; text-align: center; }
    .corr-icon { color: var(--accent-blue); font-weight: 900; font-size: 1rem; width: 30px; text-align: center; }
    .corr-result { width: 100px; text-align: center; font-weight: 800; font-size: 0.8rem; padding: 6px 0; border-radius: 6px; text-transform: uppercase; letter-spacing: 0.5px;}

    /* Top Header Status */
    .header-status { display: flex; gap: 15px; align-items: center; justify-content: flex-end; }
    .status-pill { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: var(--risk-low); padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; display: flex; align-items: center; gap: 5px; }
    .status-dot { width: 8px; height: 8px; background: var(--risk-low); border-radius: 50%; box-shadow: 0 0 8px var(--risk-low); animation: pulseGreen 2s infinite; }

    /* Animations */
    @keyframes pulseGreen { 0% { transform: scale(0.95); opacity: 0.8; } 50% { transform: scale(1.1); opacity: 1; } 100% { transform: scale(0.95); opacity: 0.8; } }
    @keyframes pulseRed { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }
    
    .danger-pulse { animation: pulseRed 2s infinite; border-color: var(--risk-crit) !important; }

    /* Badges */
    .badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
    .bg-green { background: rgba(16, 185, 129, 0.15); color: var(--risk-low); border: 1px solid rgba(16, 185, 129, 0.3); }
    .bg-yellow { background: rgba(245, 158, 11, 0.15); color: var(--risk-med); border: 1px solid rgba(245, 158, 11, 0.3); }
    .bg-red { background: rgba(239, 68, 68, 0.15); color: var(--risk-crit); border: 1px solid rgba(239, 68, 68, 0.3); }
    .bg-blue { background: rgba(59, 130, 246, 0.15); color: var(--accent-blue); border: 1px solid rgba(59, 130, 246, 0.3); }
    .bg-outline { border: 1px solid var(--border-subtle); color: var(--text-secondary); }

    /* Modern Enterprise Table */
    .table-container { width: 100%; overflow-y: auto; max-height: 400px; }
    .soc-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 0.85rem; }
    .soc-table th { position: sticky; top: 0; background: var(--bg-panel); backdrop-filter: blur(10px); z-index: 10; text-align: left; padding: 12px 15px; color: var(--text-muted); border-bottom: 2px solid var(--border-subtle); text-transform: uppercase; font-size: 0.75rem; font-weight: 700; letter-spacing: 1px; }
    .soc-table td { padding: 12px 15px; border-bottom: 1px solid rgba(255,255,255,0.02); color: var(--text-primary); }
    .soc-table tr:hover td { background: rgba(255,255,255,0.03); }

    /* Processing Timeline */
    .timeline-container { display: flex; align-items: center; justify-content: space-between; background: var(--bg-card); padding: 15px 30px; border-radius: 12px; border: 1px solid var(--border-subtle); margin-bottom: 20px; }
    .timeline-step { display: flex; flex-direction: column; align-items: center; gap: 8px; flex: 1; position: relative; z-index: 1; }
    .timeline-step::after { content: ''; position: absolute; top: 12px; left: 50%; width: 100%; height: 2px; background: var(--border-subtle); z-index: -1; }
    .timeline-step:last-child::after { display: none; }
    .step-icon { width: 26px; height: 26px; border-radius: 50%; background: var(--bg-main); border: 2px solid var(--text-muted); display: flex; align-items: center; justify-content: center; font-size: 0.7rem; color: transparent; transition: all 0.3s; }
    .step-text { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; }
    .step-active .step-icon { border-color: var(--accent-blue); background: rgba(59,130,246,0.2); color: var(--accent-blue); box-shadow: 0 0 10px var(--border-glow); }
    .step-active .step-text { color: var(--accent-blue); }
    .step-done .step-icon { border-color: var(--risk-low); background: var(--risk-low); color: #fff; }
    .step-done .step-text { color: var(--text-primary); }
    .step-done::after { background: var(--risk-low); }

</style>
""", unsafe_allow_html=True)

# ====================================================================
# SYSTEM CORE: CACHING & LOADING
# ====================================================================
@st.cache_resource
def load_ml_assets():
    model_path = "fraud_model.pkl"
    metrics_path = "training_metrics.json"
    
    if not os.path.exists(model_path):
        st.error(f"CRITICAL: {model_path} not found! Cannot initialize SOC.")
        st.stop()
        
    model = joblib.load(model_path)
    
    metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
            
    return model, metrics

@st.cache_data
def load_datasets():
    paths = {
        "cust": "dataset/customer_profile.csv",
        "txn": "dataset/transactions.csv",
        "sec": "dataset/security_logs.csv"
    }
    for k, v in paths.items():
        if not os.path.exists(v):
            st.error(f"CRITICAL: Dataset {v} missing!")
            st.stop()
            
    df_cust = pd.read_csv(paths["cust"])
    df_txn = pd.read_csv(paths["txn"])
    df_sec = pd.read_csv(paths["sec"])
    
    df_txn['transaction_time'] = pd.to_datetime(df_txn['transaction_time'])
    df_sec['login_time'] = pd.to_datetime(df_sec['login_time'])
    df_sec['logout_time'] = pd.to_datetime(df_sec['logout_time'])
    
    df_txn = df_txn.sort_values('transaction_time').reset_index(drop=True)
    return df_cust, df_txn, df_sec

# ====================================================================
# CORRELATION & FEATURE ENGINEERING ENGINE
# ====================================================================
class CorrelationEngine:
    @staticmethod
    def process(txn_row, df_sec, df_cust, past_txns):
        sec_row = df_sec[df_sec['transaction_id'] == txn_row['transaction_id']].iloc[0]
        cust_row = df_cust[df_cust['customer_id'] == txn_row['customer_id']].iloc[0]
        
        curr_time = txn_row['transaction_time']
        past_1h = sum(1 for t in past_txns if (curr_time - t).total_seconds() <= 3600)
        past_24h = sum(1 for t in past_txns if (curr_time - t).total_seconds() <= 86400)
        
        amount = float(txn_row['amount'])
        avg_txn = float(cust_row['average_transaction_amount'])
        time_gap = (curr_time - sec_row['login_time']).total_seconds() / 60.0
        
        loc_match = 1 if txn_row['transaction_location'] == sec_row['login_location'] else 0
        imp_travel = 1 if (sec_row['previous_login_city'] != sec_row['login_location'] and time_gap < 120) else 0
        new_dev = 1 if sec_row['device_id'] != cust_row['registered_device_id'] else 0
        trust_ip = 1 if sec_row['ip_address'] == cust_row['trusted_ip'] else 0
        
        # Build exact ML Input dict strictly matching training data
        ml_dict = {
            "amount": amount,
            "average_transaction_amount": avg_txn,
            "amount_ratio": amount / avg_txn if avg_txn > 0 else 0.0,
            "transaction_hour": curr_time.hour,
            "transaction_day": curr_time.weekday(),
            "location_match": loc_match,
            "location_changed": 1 if txn_row['transaction_location'] != cust_row['home_city'] else 0,
            "new_device": new_dev,
            "trusted_ip": trust_ip,
            "vpn_used": 1 if sec_row['vpn_used'] else 0,
            "failed_login_count": sec_row['failed_login_count'],
            "password_reset": 1 if sec_row['password_reset'] else 0,
            "otp_verified": 1 if sec_row['otp_verified'] else 0,
            "session_duration_minutes": sec_row['session_duration_minutes'],
            "ip_reputation_score": sec_row['ip_reputation_score'],
            "new_receiver": 1 if past_24h == 0 else 0,
            "receiver_trust_score": 50,
            "receiver_risk_score": 50,
            "merchant_category": txn_row['merchant_category'],
            "payment_method": txn_row['payment_method'],
            "high_risk_merchant": 1 if txn_row['merchant_category'] in ["Crypto", "Gaming", "Remittance"] else 0,
            "night_transaction": 1 if (curr_time.hour < 5 or curr_time.hour > 23) else 0,
            "impossible_travel": imp_travel,
            "time_gap_minutes": max(0, time_gap),
            "previous_transactions_last_1_hour": past_1h,
            "previous_transactions_last_24_hours": past_24h,
            "high_value_transaction": 1 if amount > (avg_txn * 4) else 0,
            "persona": cust_row['persona'],
            "home_city": cust_row['home_city'],
            "login_city": sec_row['login_location'],
            "transaction_city": txn_row['transaction_location']
        }
        
        # Build UI Correlation mapping
        mappings = [
            {"label": "Location", "txn_val": txn_row['transaction_location'], "sec_val": sec_row['login_location'], "match": loc_match == 1, "risk_val": 25},
            {"label": "Device", "txn_val": "Registered", "sec_val": "Current", "match": new_dev == 0, "risk_val": 20},
            {"label": "IP Integrity", "txn_val": "Known IP", "sec_val": "Session IP", "match": trust_ip == 1, "risk_val": 15},
            {"label": "VPN Usage", "txn_val": "Standard", "sec_val": "VPN Node", "match": not sec_row['vpn_used'], "risk_val": 15},
            {"label": "Password Reset", "txn_val": "Active", "sec_val": "Recent Reset", "match": not sec_row['password_reset'], "risk_val": 18},
            {"label": "Failed Login", "txn_val": "Normal", "sec_val": str(sec_row['failed_login_count']), "match": sec_row['failed_login_count'] < 3, "risk_val": 12},
            {"label": "Receiver", "txn_val": "Known", "sec_val": "Unknown", "match": past_24h > 0, "risk_val": 10},
            {"label": "Time", "txn_val": "Day", "sec_val": "Night", "match": not (curr_time.hour < 5 or curr_time.hour > 23), "risk_val": 8}
        ]
        
        # Build Triggers for AI Panel
        triggers = []
        if ml_dict['vpn_used']: triggers.append("VPN Used")
        if ml_dict['new_device']: triggers.append("New Device")
        if ml_dict['location_match'] == 0: triggers.append("Location Mismatch")
        if ml_dict['password_reset']: triggers.append("Password Reset")
        if ml_dict['failed_login_count'] >= 3: triggers.append(f"Failed Logins: {ml_dict['failed_login_count']}")
        if ml_dict['impossible_travel']: triggers.append("Impossible Travel")
        if ml_dict['high_risk_merchant']: triggers.append("High-Risk Merchant")
        if ml_dict['amount_ratio'] > 3: triggers.append("High Amount")
        if not triggers: triggers.append("Normal Profile")
        
        return pd.DataFrame([ml_dict]), mappings, triggers, sec_row, cust_row

# ====================================================================
# UI HELPERS
# ====================================================================
def render_risk_gauge(score):
    if score < 25: color = "#10b981"
    elif score < 60: color = "#f59e0b"
    elif score < 85: color = "#f97316"
    else: color = "#ef4444"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#374151"},
            'bar': {'color': color},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 25], 'color': 'rgba(16, 185, 129, 0.1)'},
                {'range': [25, 60], 'color': 'rgba(245, 158, 11, 0.1)'},
                {'range': [60, 85], 'color': 'rgba(249, 115, 22, 0.1)'},
                {'range': [85, 100], 'color': 'rgba(239, 68, 68, 0.1)'}
            ]
        },
        number={'font': {'color': color, 'size': 45, 'family': 'Inter'}, 'suffix': "%"}
    ))
    fig.update_layout(height=230, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", font={'color': "#f3f4f6"})
    return fig

def get_risk_badge(score):
    if score < 25: return "<span class='badge bg-green'>LOW</span>"
    if score < 60: return "<span class='badge bg-yellow'>MEDIUM</span>"
    if score < 85: return "<span class='badge bg-orange'>HIGH</span>"
    return "<span class='badge bg-red'>CRITICAL</span>"

def get_risk_level_text(score):
    if score < 25: return "LOW"
    if score < 60: return "MEDIUM"
    if score < 85: return "HIGH"
    return "CRITICAL"

# ====================================================================
# STATE MANAGEMENT
# ====================================================================
if 'run_state' not in st.session_state:
    st.session_state.run_state = "RUNNING"
if 'processed' not in st.session_state:
    st.session_state.processed = 0
if 'fraud_count' not in st.session_state:
    st.session_state.fraud_count = 0
if 'history' not in st.session_state:
    st.session_state.history = []
if 'customer_history' not in st.session_state:
    st.session_state.customer_history = {}

if 'stats' not in st.session_state:
    st.session_state.stats = {
        'sum_conf': 0.0, 'sum_risk': 0, 'start_time': datetime.now(), 'end_time': None,
        'highest_risk': {'score': -1}, 'lowest_risk': {'score': 101},
        'risk_dist': {'LOW':0, 'MEDIUM':0, 'HIGH':0, 'CRITICAL':0},
        'city_fraud': {}, 'merchant_fraud': {}, 'hour_txn': {}
    }

# ====================================================================
# PRE-LOAD & RENDER LOGIC
# ====================================================================

model, metrics = load_ml_assets()
df_cust, df_txn, df_sec = load_datasets()

# ---------------------------------------------------------
# VIEW 2 & 3: LIVE MONITORING & RESULTS
# ---------------------------------------------------------
if st.session_state.run_state in ["RUNNING", "FINISHED"]:
    
    # --- NEW ENTERPRISE HEADER ---
    elapsed = (datetime.now() - st.session_state.stats['start_time']).total_seconds()
    tx_speed = f"{(st.session_state.processed / max(1, elapsed)):.1f}" if st.session_state.processed > 0 else "0.0"
    st.markdown(f"""
        <div style='display:flex; justify-content:space-between; align-items:center; padding: 20px 30px; background: var(--bg-panel); border: 1px solid var(--border-subtle); margin-bottom: 25px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);'>
            <div style='display:flex; align-items:center; gap: 20px;'>
                <div style='font-size: 2.8rem;'>🛡️</div>
                <div>
                    <h2 style='margin:0; font-size: 1.8rem; font-weight: 800; background: linear-gradient(90deg, #3b82f6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>VeriFusion AI</h2>
                    <div style='color: var(--text-secondary); font-size: 0.85rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;'>Correlating Banking Transactions with Cybersecurity Intelligence</div>
                </div>
                <div style='display:flex; gap:10px; margin-left: 30px; border-left: 1px solid var(--border-subtle); padding-left: 30px;'>
                    <div class='status-pill'><div class='status-dot'></div>SYSTEM ONLINE</div>
                    <div class='status-pill'><div class='status-dot'></div>MODEL ACTIVE</div>
                    <div class='status-pill'><div class='status-dot'></div>DATA STREAM</div>
                </div>
            </div>
            <div style='display:flex; gap:30px; text-align: right;'>
                <div>
                    <div style='font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 4px; font-weight: 700; letter-spacing: 1px; text-transform:uppercase;'>Current Date</div>
                    <div style='color: var(--text-primary); font-weight: 600; font-size: 1.05rem;'>{datetime.now().strftime("%d %b %Y")}</div>
                </div>
                <div>
                    <div style='font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 4px; font-weight: 700; letter-spacing: 1px; text-transform:uppercase;'>Current Time</div>
                    <div style='color: var(--text-primary); font-weight: 600; font-size: 1.05rem;'>{datetime.now().strftime("%H:%M:%S")}</div>
                </div>
                <div>
                    <div style='font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 4px; font-weight: 700; letter-spacing: 1px; text-transform:uppercase;'>Processing Speed</div>
                    <div style='color: var(--accent-cyan); font-weight: 800; font-size: 1.05rem;'>{tx_speed} Tx/sec</div>
                </div>
            </div>
        </div>
    """.replace('\n', ''), unsafe_allow_html=True)
    
    # --- DYNAMIC PLACEHOLDERS ---
    kpi_ph = st.empty()
    timeline_ph = st.empty()
    anim_ph = st.empty()
    panels_ph = st.empty()
    history_ph = st.empty()
    analytics_ph = st.empty()
    finish_ph = st.empty()

    # ---------------------------------------------------------
    # RUNNING LOOP
    # ---------------------------------------------------------
    if st.session_state.run_state == "RUNNING":
        total_txns = len(df_txn)
        
        for idx, row in df_txn.iterrows():
            if st.session_state.run_state != "RUNNING": break
            if idx < st.session_state.processed: continue
            
            txn_id = row['transaction_id']
            cust_id = row['customer_id']
            
            if cust_id not in st.session_state.customer_history:
                st.session_state.customer_history[cust_id] = []
            past_txns = st.session_state.customer_history[cust_id]
            
            ml_input, mappings, triggers, sec_row, cust_row = CorrelationEngine.process(row, df_sec, df_cust, past_txns)
            
            prob = model.predict_proba(ml_input)[0][1]
            risk_score = int(prob * 100)
            confidence = int(max(prob, 1-prob) * 100)
            
            decision = "FRAUD" if risk_score >= 50 else "SAFE"
            action = "BLOCKED" if decision == "FRAUD" else "APPROVED"
            
            # --- SCAN ANIMATION (shown briefly while processing) ---
            pct_pre = max(1, int((st.session_state.processed / total_txns) * 100))
            elapsed_loop = (datetime.now() - st.session_state.stats['start_time']).total_seconds()
            curr_speed = st.session_state.processed / max(1, elapsed_loop)
            remaining_txns = total_txns - st.session_state.processed
            eta_secs = remaining_txns / max(0.1, curr_speed)
            eta_str = f"{int(eta_secs//60)} min {int(eta_secs%60)} sec"
            timeline_ph.markdown(f"""
<div class='scan-bar-wrap'>
    <div class='scan-dot'></div>
    <div class='scan-label' style='display:flex; justify-content:space-between; width:100%;'>
        <span>Processing <b>{st.session_state.processed} / {total_txns}</b> Transactions</span>
        <span>Remaining <b>{remaining_txns}</b></span>
        <span>Estimated Completion <b>{eta_str}</b></span>
    </div>
    <div class='scan-progress-bg' style='margin-left: 15px;'><div class='scan-progress-fill' style='width:{pct_pre}%;'></div></div>
    <div class='scan-pct'>{pct_pre}%</div>
</div>
""".replace('\n', ''), unsafe_allow_html=True)
            anim_ph.empty()
            time.sleep(0.75)
            
            # --- UPDATE STATS ---
            st.session_state.processed += 1
            if decision == "FRAUD": st.session_state.fraud_count += 1
            
            s = st.session_state.stats
            s['sum_conf'] += confidence
            s['sum_risk'] += risk_score
            
            if risk_score > s['highest_risk']['score']:
                s['highest_risk'] = {'score': risk_score, 'txn': txn_id, 'cust': cust_row['customer_name']}
            if risk_score < s['lowest_risk']['score']:
                s['lowest_risk'] = {'score': risk_score, 'txn': txn_id, 'cust': cust_row['customer_name']}
                
            if risk_score < 25: s['risk_dist']['LOW'] += 1
            elif risk_score < 60: s['risk_dist']['MEDIUM'] += 1
            elif risk_score < 85: s['risk_dist']['HIGH'] += 1
            else: s['risk_dist']['CRITICAL'] += 1
            
            st.session_state.customer_history[cust_id].append(row['transaction_time'])
            
            # --- RENDER UI ---
            pct = int((st.session_state.processed / total_txns) * 100)
            
            with kpi_ph.container():
                k1, k2, k3, k4, k5, k6 = st.columns(6)
                kpi_style = "height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;"
                with k1: st.markdown(f"<div class='soc-kpi' style='{kpi_style}'><div class='kpi-glow'></div><div class='kpi-title'>Total Transactions</div><div class='kpi-value'>{total_txns}</div></div>", unsafe_allow_html=True)
                with k2: st.markdown(f"<div class='soc-kpi' style='{kpi_style}'><div class='kpi-glow'></div><div class='kpi-title'>Processed</div><div class='kpi-value'>{st.session_state.processed}</div></div>", unsafe_allow_html=True)
                with k3: st.markdown(f"<div class='soc-kpi' style='{kpi_style} border-color:var(--risk-crit);'><div class='kpi-glow'></div><div class='kpi-title' style='color:var(--risk-crit);'>Fraud Detected</div><div class='kpi-value' style='color:var(--risk-crit);'>{st.session_state.fraud_count}</div></div>", unsafe_allow_html=True)
                with k4: st.markdown(f"<div class='soc-kpi' style='{kpi_style}'><div class='kpi-glow'></div><div class='kpi-title' style='color:var(--risk-low);'>Safe Transactions</div><div class='kpi-value' style='color:var(--risk-low);'>{st.session_state.processed - st.session_state.fraud_count}</div></div>", unsafe_allow_html=True)
                with k5: st.markdown(f"<div class='soc-kpi' style='{kpi_style}'><div class='kpi-glow'></div><div class='kpi-title'>Model Accuracy</div><div class='kpi-value'>{metrics.get('accuracy', 0)*100:.1f}%</div></div>", unsafe_allow_html=True)
                with k6: st.markdown(f"<div class='soc-kpi' style='{kpi_style}'><div class='kpi-glow'></div><div class='kpi-title'>Current Risk</div><div class='kpi-value'>{risk_score}%</div></div>", unsafe_allow_html=True)

            # Replace the volatile timeline with the stable scanning bar (post-processing complete version)
            timeline_ph.markdown(f"""
<div class='scan-bar-wrap' style='animation:none;'>
    <div style='width:10px;height:10px;border-radius:50%;background:var(--risk-low);box-shadow:0 0 8px var(--risk-low);flex-shrink:0;'></div>
    <div class='scan-label' style='color:var(--risk-low); font-weight:600;'>✓ Transaction {txn_id} processed completely.</div>
    <div class='scan-progress-bg'><div class='scan-progress-fill' style='width:{pct}%; background: linear-gradient(90deg, #10b981, #06b6d4);'></div></div>
    <div class='scan-pct' style='color:var(--risk-low);'>{pct}%</div>
</div>
""".replace('\n', ''), unsafe_allow_html=True)

            with panels_ph.container():
                c1, c2 = st.columns(2)
                c3, c4 = st.columns(2)
                
                with c1:
                    st.markdown(f"""
<div class='soc-panel'>
  <div class='soc-header'>💳 Current Transaction</div>
  <div class='data-group'>
    <div class='data-group-title'>👤 Customer</div>
    <div class='field-row'><span class='field-label'>Name</span><span class='field-value'>{cust_row['customer_name']}</span></div>
    <div class='field-row'><span class='field-label'>Account</span><span class='field-value' style='font-family:monospace;'>{cust_row['account_number']}</span></div>
  </div>
  <div class='data-group'>
    <div class='data-group-title'>💳 Transaction</div>
    <div class='field-row'><span class='field-label'>Amount</span><span class='field-value' style='font-size:1.35rem; font-weight:800; color:var(--accent-blue);'>₹{row['amount']:,.2f}</span></div>
    <div class='field-row'><span class='field-label'>Time</span><span class='field-value'>{row['transaction_time'].strftime('%H:%M:%S')}</span></div>
    <div class='field-row'><span class='field-label'>ID</span><span class='field-value' style='font-family:monospace; font-size:0.8rem;'>{txn_id}</span></div>
  </div>
  <div class='data-group'>
    <div class='data-group-title'>🏢 Merchant</div>
    <div class='field-row'><span class='field-label'>Name</span><span class='field-value'>{row['merchant_name']}</span></div>
    <div class='field-row'><span class='field-label'>Category</span><span class='field-value'><span class='badge bg-outline'>{row['merchant_category']}</span></span></div>
  </div>
  <div class='data-group'>
    <div class='data-group-title'>📍 Location &amp; Payment</div>
    <div class='field-row'><span class='field-label'>Location</span><span class='field-value'>{row['transaction_location']}</span></div>
    <div class='field-row'><span class='field-label'>Method</span><span class='field-value'><span class='badge bg-blue'>{row['payment_method']}</span></span></div>
  </div>
</div>
""".replace('\n', ''), unsafe_allow_html=True)
                    
                with c2:
                    vpn_badge = "<span class='badge bg-red'>ACTIVE</span>" if sec_row['vpn_used'] else "<span class='badge bg-green'>INACTIVE</span>"
                    otp_badge = "<span class='badge bg-green'>VERIFIED</span>" if sec_row['otp_verified'] else "<span class='badge bg-yellow'>PENDING</span>"
                    failed_color = "var(--risk-crit)" if sec_row["failed_login_count"] > 0 else "var(--risk-low)"
                    st.markdown(f"""
<div class='soc-panel'>
  <div class='soc-header'>🛡️ Cybersecurity Panel</div>
  <div class='data-group'>
    <div class='data-group-title'>🔐 Authentication</div>
    <div class='field-row'><span class='field-label'>OTP Status</span><span class='field-value'>{otp_badge}</span></div>
    <div class='field-row'><span class='field-label'>Password Reset</span><span class='field-value'>{'Yes' if sec_row['password_reset'] else 'No'}</span></div>
    <div class='field-row'><span class='field-label'>Failed Logins</span><span class='field-value' style='color:{failed_color}; font-weight:800;'>{sec_row['failed_login_count']}</span></div>
  </div>
  <div class='data-group'>
    <div class='data-group-title'>💻 Device</div>
    <div class='field-row'><span class='field-label'>Type &amp; OS</span><span class='field-value'>{sec_row['device_type']} · {sec_row['operating_system']}</span></div>
    <div class='field-row'><span class='field-label'>Browser</span><span class='field-value'>{sec_row['browser']}</span></div>
  </div>
  <div class='data-group'>
    <div class='data-group-title'>🌐 Network</div>
    <div class='field-row'><span class='field-label'>IP Address</span><span class='field-value' style='font-family:monospace; font-size:0.82rem;'>{sec_row['ip_address']}</span></div>
    <div class='field-row'><span class='field-label'>VPN</span><span class='field-value'>{vpn_badge}</span></div>
    <div class='field-row'><span class='field-label'>Reputation</span><span class='field-value'>{sec_row['ip_reputation_score']}/100</span></div>
  </div>
  <div class='data-group'>
    <div class='data-group-title'>⏱️ Session</div>
    <div class='field-row'><span class='field-label'>Login City</span><span class='field-value'>{sec_row['login_location']}</span></div>
    <div class='field-row'><span class='field-label'>Previous City</span><span class='field-value'>{sec_row['previous_login_city']}</span></div>
    <div class='field-row'><span class='field-label'>Duration</span><span class='field-value'>{sec_row['session_duration_minutes']} mins</span></div>
  </div>
</div>
""".replace('\n', ''), unsafe_allow_html=True)
    
                with c3:
                    rc_html = "<div class='soc-panel'><div class='soc-header'>🔗 Correlation Engine</div><div class='corr-container'>"
                    rc_html += "<div style='display:flex; justify-content:space-between; margin-bottom: 12px; border-bottom: 1px solid var(--border-subtle); padding-bottom: 8px;'><div style='font-size:0.75rem; font-weight:700; color:var(--text-secondary); text-transform:uppercase; letter-spacing: 1px;'>Anomaly Breakdown</div><div style='font-size:0.75rem; font-weight:700; color:var(--text-secondary); text-transform:uppercase; letter-spacing: 1px;'>Risk Contribution</div></div>"
                    
                    total_behavior_risk = 0
                    for m in mappings:
                        if m['match']: 
                            val = "+0"
                            col = "var(--risk-low)"
                        else:
                            val = f"+{m['risk_val']}"
                            total_behavior_risk += m['risk_val']
                            col = "var(--risk-crit)"
                            
                        rc_html += f"<div class='field-row' style='padding:6px 0; border:none;'><span style='color:var(--text-primary); font-size:0.85rem;'>{m['label']}</span><span style='color:{col}; font-weight:800; font-size:0.9rem;'>{val}</span></div>"
                    
                    if decision == "SAFE": total_behavior_risk = min(total_behavior_risk, risk_score)
                    
                    rc_html += f"<div style='margin-top:15px; padding-top:15px; border-top:1px dashed var(--border-subtle); display:flex; justify-content:space-between; align-items:center;'><span style='font-size:0.8rem; font-weight:700; color:var(--text-secondary); text-transform:uppercase; letter-spacing: 1px;'>Total Behaviour Risk</span><span style='font-size:1.6rem; font-weight:800; color:{'var(--risk-crit)' if decision=='FRAUD' else 'var(--risk-low)'};'>{total_behavior_risk} / 100</span></div>"
                    rc_html += "</div></div>"
                    st.markdown(rc_html, unsafe_allow_html=True)
                    
                with c4:
                    if risk_score < 25: 
                        rec_action = "Approve"
                        action_col = "var(--risk-low)"
                    elif risk_score < 60: 
                        rec_action = "OTP Verification"
                        action_col = "var(--risk-med)"
                    elif risk_score < 85: 
                        rec_action = "Manual Review"
                        action_col = "var(--risk-high)"
                    else: 
                        rec_action = "Block Transaction"
                        action_col = "var(--risk-crit)"
                        
                    pulse_class = "danger-pulse" if decision == "FRAUD" else ""
                    reason = "Multiple Behavioural Risk Factors Detected" if decision == "FRAUD" else "No Behavioural Anomaly Detected"
                    
                    st.markdown(f"""
<div class='soc-panel {pulse_class}'>
  <div class='soc-header'>🧠 AI Decision Panel</div>
  <div style='display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px;'>
    <div style='background:rgba(0,0,0,0.2); border-radius:8px; padding:14px; text-align:center;'>
      <div style='font-size:0.7rem; color:var(--text-muted); letter-spacing:1.5px; text-transform:uppercase; margin-bottom:6px;'>Prediction</div>
      <div style='font-size:1.8rem; font-weight:800; color:{action_col};'>{decision}</div>
    </div>
    <div style='background:rgba(0,0,0,0.2); border-radius:8px; padding:14px; text-align:center;'>
      <div style='font-size:0.7rem; color:var(--text-muted); letter-spacing:1.5px; text-transform:uppercase; margin-bottom:6px;'>Confidence</div>
      <div style='font-size:1.8rem; font-weight:800; color:var(--text-primary);'>{confidence}%</div>
    </div>
  </div>
  <div style='margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;'>
    <div>
      <div style='font-size:0.7rem; color:var(--text-muted); letter-spacing:1.5px; text-transform:uppercase; margin-bottom:8px;'>Risk Level</div>
      {get_risk_badge(risk_score)}
    </div>
    <div style='text-align:right;'>
      <div style='font-size:0.7rem; color:var(--text-muted); letter-spacing:1.5px; text-transform:uppercase; margin-bottom:8px;'>Probability</div>
      <div style='font-size:1.2rem; font-weight:800; color:var(--text-primary);'>{(prob):.2f}</div>
    </div>
  </div>
  <div style='margin-bottom:16px;'>
    <div style='font-size:0.7rem; color:var(--text-muted); letter-spacing:1.5px; text-transform:uppercase; margin-bottom:8px;'>Reason</div>
    <div style='font-size:0.85rem; color:var(--text-primary); font-weight:600; padding:8px 12px; border-left:3px solid {action_col}; background:rgba(255,255,255,0.03);'>{reason}</div>
  </div>
  <div>
    <div style='font-size:0.7rem; color:var(--text-muted); letter-spacing:1.5px; text-transform:uppercase; margin-bottom:8px;'>Recommended Action</div>
    <div style='background:{action_col}22; border:1px solid {action_col}; color:{action_col}; font-weight:800; padding:12px; text-align:center; border-radius:8px; letter-spacing:1px; font-size:1rem; text-transform:uppercase;'>{rec_action}</div>
  </div>
</div>
""".replace('\n', ''), unsafe_allow_html=True)
                    st.plotly_chart(render_risk_gauge(risk_score), use_container_width=True, config={'displayModeBar':False}, key=f"gauge_{idx}")
            
            # --- LIVE HISTORY ---
            hist_pred = f"<span style='color:{'var(--risk-crit)' if decision=='FRAUD' else 'var(--risk-low)'}; font-weight:800;'>{decision}</span>"
            hist_act = f"<span class='badge bg-{'red' if action=='BLOCKED' else 'green'}'>{action}</span>"
            
            st.session_state.history.insert(0, f"""
<tr>
    <td>{row['transaction_time'].strftime("%H:%M:%S")}</td>
    <td style='font-family:monospace; color:var(--accent-blue);'>{txn_id}</td>
    <td>{cust_row['customer_name']}</td>
    <td style='font-weight:700;'>₹{row['amount']:,.2f}</td>
    <td>{hist_pred}</td>
    <td style='font-weight: 700;'>{confidence}%</td>
    <td>{get_risk_badge(risk_score)}</td>
    <td>{hist_act}</td>
</tr>
""".replace('\n', ''))
            if len(st.session_state.history) > 20: st.session_state.history.pop()
            
            with history_ph.container():
                st.markdown(f"""
<style>
.soc-table tr:nth-child(even) td {{ background: rgba(255,255,255,0.015); }}
</style>
<div class='soc-panel' style='margin-top: 10px;'>
    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;'>
        <div class='soc-header' style='margin-bottom:0; border:none; padding:0;'>📋 Live Event History</div>
        <div style='display:flex; gap:8px;'>
            <span class='badge bg-outline' style='cursor:default; padding: 5px 14px; border-radius:15px;'>All Events</span>
            <span class='badge bg-red' style='cursor:default; padding: 5px 14px; border-radius:15px;'>Fraud Only</span>
        </div>
    </div>
    <div class='table-container'>
        <table class='soc-table'>
            <tr><th>Time</th><th>Transaction ID</th><th>Customer</th><th>Amount</th><th>Prediction</th><th>Confidence</th><th>Risk</th><th>Action</th></tr>
            {"".join(st.session_state.history)}
        </table>
    </div>
</div>
""".replace('\n', ''), unsafe_allow_html=True)
                
            # --- ANALYTICS GRID ---
            safe_count = st.session_state.processed - st.session_state.fraud_count
            with analytics_ph.container():
                ac1, ac2 = st.columns(2)
                with ac1:
                    st.markdown("<div class='soc-panel' style='padding:0;'><div class='soc-header' style='padding: 20px 20px 0 20px;'>📊 Fraud vs Safe Ratio</div>", unsafe_allow_html=True)
                    fig1 = go.Figure(data=[go.Pie(labels=['Safe', 'Fraud'], values=[safe_count, st.session_state.fraud_count], hole=.7, marker_colors=['#10b981', '#ef4444'])])
                    fig1.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", font={'color':"#f3f4f6"}, margin=dict(t=20, b=20, l=20, r=20), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                    st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False}, key=f"pie_{idx}")
                    st.markdown("</div>", unsafe_allow_html=True)
                with ac2:
                    st.markdown("<div class='soc-panel' style='padding:0;'><div class='soc-header' style='padding: 20px 20px 0 20px;'>📈 Risk Distribution</div>", unsafe_allow_html=True)
                    rd = s['risk_dist']
                    fig2 = go.Figure(data=[go.Bar(x=list(rd.keys()), y=list(rd.values()), marker_color=['#10b981', '#f59e0b', '#f97316', '#ef4444'], text=list(rd.values()), textposition='auto')])
                    fig2.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color':"#f3f4f6"}, margin=dict(t=20, b=20, l=20, r=20))
                    fig2.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', visible=False)
                    fig2.update_xaxes(showgrid=False)
                    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False}, key=f"bar_{idx}")
                    st.markdown("</div>", unsafe_allow_html=True)
                
            time.sleep(1.0) # Pause to let judge view
            
        # FINISH LOOP
        st.session_state.run_state = "FINISHED"
        st.session_state.stats['end_time'] = datetime.now()
        st.rerun()

    # ---------------------------------------------------------
    # VIEW 3: END SCREEN
    # ---------------------------------------------------------
    if st.session_state.run_state == "FINISHED":
        s = st.session_state.stats
        duration = s['end_time'] - s['start_time']
        avg_conf = s['sum_conf'] / max(1, st.session_state.processed)
        avg_risk = s['sum_risk'] / max(1, st.session_state.processed)
        
        top_layout_ph.empty()
        anim_ph.empty()
        panels_ph.empty()
        history_ph.empty()
        
        with finish_ph.container():
            st.markdown(f"""
                <div class='soc-panel' style='text-align:center; padding: 60px 40px; background: radial-gradient(circle at center, rgba(16, 185, 129, 0.1) 0%, var(--bg-panel) 70%); border: 1px solid rgba(16, 185, 129, 0.3); box-shadow: 0 0 50px rgba(16, 185, 129, 0.1); margin-top: 20px;'>
                    <h1 style='color:var(--risk-low); font-size: 3.5rem; margin-bottom: 15px;'>✅ AI Monitoring Completed</h1>
                    <p style='color:var(--text-secondary); font-size: 1.3rem; margin-bottom: 50px;'>Dataset fully processed and correlated successfully.</p>
                    
                    <div style='display:flex; justify-content:center; gap:40px; margin-bottom: 50px; flex-wrap: wrap;'>
                        <div style='background: rgba(255,255,255,0.03); padding: 25px; border-radius: 12px; min-width: 200px;'>
                            <div style='font-size:0.95rem; color:var(--text-secondary); letter-spacing:1px; margin-bottom: 8px;'>TRANSACTIONS PROCESSED</div>
                            <div style='font-size:2.8rem; font-weight:800; color:white;'>{st.session_state.processed}</div>
                        </div>
                        <div style='background: rgba(239, 68, 68, 0.05); padding: 25px; border-radius: 12px; min-width: 200px; border: 1px solid rgba(239, 68, 68, 0.2);'>
                            <div style='font-size:0.95rem; color:var(--risk-crit); letter-spacing:1px; margin-bottom: 8px;'>FRAUD DETECTED</div>
                            <div style='font-size:2.8rem; font-weight:800; color:var(--risk-crit);'>{st.session_state.fraud_count}</div>
                        </div>
                        <div style='background: rgba(16, 185, 129, 0.05); padding: 25px; border-radius: 12px; min-width: 200px; border: 1px solid rgba(16, 185, 129, 0.2);'>
                            <div style='font-size:0.95rem; color:var(--risk-low); letter-spacing:1px; margin-bottom: 8px;'>SAFE TRANSACTIONS</div>
                            <div style='font-size:2.8rem; font-weight:800; color:var(--risk-low);'>{st.session_state.processed - st.session_state.fraud_count}</div>
                        </div>
                        <div style='background: rgba(255,255,255,0.03); padding: 25px; border-radius: 12px; min-width: 200px;'>
                            <div style='font-size:0.95rem; color:var(--text-secondary); letter-spacing:1px; margin-bottom: 8px;'>DETECTION ACCURACY</div>
                            <div style='font-size:2.8rem; font-weight:800; color:var(--accent-blue);'>{metrics.get('accuracy', 0)*100:.1f}%</div>
                        </div>
                    </div>
                    
                    <div style='display:flex; justify-content:center; gap:30px; margin-bottom: 50px; flex-wrap: wrap;'>
                        <div style='background: rgba(0,0,0,0.2); padding: 15px 35px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.05);'>
                            <span style='color:var(--text-secondary); font-size:1rem; margin-right: 12px;'>Average Confidence:</span>
                            <span style='color:white; font-size:1.4rem; font-weight:700;'>{avg_conf:.1f}%</span>
                        </div>
                        <div style='background: rgba(0,0,0,0.2); padding: 15px 35px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.05);'>
                            <span style='color:var(--text-secondary); font-size:1rem; margin-right: 12px;'>Average Risk Score:</span>
                            <span style='color:white; font-size:1.4rem; font-weight:700;'>{avg_risk:.1f}%</span>
                        </div>
                        <div style='background: rgba(0,0,0,0.2); padding: 15px 35px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.05);'>
                            <span style='color:var(--text-secondary); font-size:1rem; margin-right: 12px;'>Monitoring Time:</span>
                            <span style='color:white; font-size:1.4rem; font-weight:700;'>{duration.total_seconds():.1f}s</span>
                        </div>
                    </div>
                    
                    <div style='display:flex; justify-content:center; gap:30px; margin-top: 30px;'>
                        <div style='background: rgba(239, 68, 68, 0.1); border: 1px solid var(--risk-crit); padding: 25px; border-radius: 12px; width: 350px; text-align: left;'>
                            <div style='font-size:0.8rem; color:var(--risk-crit); letter-spacing:1px; margin-bottom:12px;'>HIGHEST RISK TRANSACTION</div>
                            <div style='font-size:1.4rem; font-family:monospace; color:white; font-weight: 700;'>{s['highest_risk'].get('txn', 'N/A')}</div>
                            <div style='font-size:1rem; color:var(--text-secondary); margin-top:8px;'>{s['highest_risk'].get('cust', '')} • <span style='color: white; font-weight: 700;'>{s['highest_risk']['score']}% Risk</span></div>
                        </div>
                        <div style='background: rgba(16, 185, 129, 0.1); border: 1px solid var(--risk-low); padding: 25px; border-radius: 12px; width: 350px; text-align: left;'>
                            <div style='font-size:0.8rem; color:var(--risk-low); letter-spacing:1px; margin-bottom:12px;'>LOWEST RISK TRANSACTION</div>
                            <div style='font-size:1.4rem; font-family:monospace; color:white; font-weight: 700;'>{s['lowest_risk'].get('txn', 'N/A')}</div>
                            <div style='font-size:1rem; color:var(--text-secondary); margin-top:8px;'>{s['lowest_risk'].get('cust', '')} • <span style='color: white; font-weight: 700;'>{s['lowest_risk']['score']}% Risk</span></div>
                        </div>
                    </div>
                </div>
            """.replace('\n', ''), unsafe_allow_html=True)