"""
RailGuard AI — Aplicação Principal v3 (UX Redesign)
=====================================================
Plataforma de Compliance Preditivo Ferroviário
MVP demonstrativo — dados simulados.

Execução:
    streamlit run app.py
"""

import os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta

import database as db
import models as m
import risk_engine as re_
import ml_model as ml
import reports as rp
import seed_data

# ═══════════════════════════════════════════════════════════════════════════
#  CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="RailGuard AI · Centro de Controle Ferroviário",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════
#  PALETA — DARK INDUSTRIAL FERROVIÁRIO
# ═══════════════════════════════════════════════════════════════════════════

PRIMARY   = "#080F1D"   # fundo principal — azul naval profundo
SECONDARY = "#0D1E35"   # superfície de card
SURFACE   = "#0C1A2E"   # superfície elevada
CARD_BG   = "#101F38"   # card padrão
CARD_HI   = "#132545"   # card destacado
BORDER    = "#1A3357"   # borda sutil
BORDER_HI = "#1F4070"   # borda de hover/focus
ACCENT    = "#E63946"   # vermelho trilho — crítico/brand
ACCENT2   = "#2A8FD4"   # azul elétrico — info/IA
ACCENT3   = "#7B5EA7"   # roxo — auditoria/compliance

TEXT_PRI  = "#ECF1F7"   # texto principal
TEXT_SEC  = "#92AFCA"   # texto secundário
TEXT_MUT  = "#435D77"   # texto mutado/label
TEXT_MONO = "#7EC8E3"   # texto monoespaçado (códigos)

C_BAIXO   = "#0CB87A"   # verde esmeralda
C_MEDIO   = "#F4A62A"   # âmbar
C_ALTO    = "#F47B35"   # laranja queimado
C_CRITICO = "#E63946"   # vermelho trilho
C_COMP    = "#7B5EA7"   # roxo compliance
C_INFO    = "#2A8FD4"   # azul info

RISK_C = {"Baixo": C_BAIXO, "Médio": C_MEDIO, "Alto": C_ALTO, "Crítico": C_CRITICO}
RCRS_C = {
    "Conforme": C_BAIXO, "Atenção": C_MEDIO,
    "Não conformidade potencial": C_ALTO, "Crítico": C_CRITICO,
}

# ═══════════════════════════════════════════════════════════════════════════
#  CSS — SISTEMA DE DESIGN COMPLETO
# ═══════════════════════════════════════════════════════════════════════════

CSS = f"""
<style>
/* ── Fontes ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Reset base ── */
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif !important; }}
* {{ box-sizing: border-box; }}

/* ── Fundo da aplicação ── */
.stApp {{
    background-color: {PRIMARY};
    background-image:
        radial-gradient(circle at 20% 50%, rgba(42,143,212,0.04) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(123,94,167,0.04) 0%, transparent 50%),
        linear-gradient(rgba(26,51,87,0.10) 1px, transparent 1px),
        linear-gradient(90deg, rgba(26,51,87,0.10) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 48px 48px, 48px 48px;
}}

/* ── Container principal ── */
.main .block-container {{
    padding: 2rem 2.5rem 4rem 2.5rem;
    max-width: 1700px;
}}

/* ══════════════════════════════════════════
   SIDEBAR
══════════════════════════════════════════ */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {SECONDARY} 0%, {PRIMARY} 100%) !important;
    border-right: 1px solid {BORDER} !important;
    min-width: 240px !important;
}}
[data-testid="stSidebar"] > div {{ padding-top: 0 !important; }}

.sidebar-brand-wrap {{
    padding: 22px 20px 16px 20px;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 8px;
}}
.sidebar-logo-text {{
    font-size: 1.2rem; font-weight: 900;
    color: {TEXT_PRI}; letter-spacing: -0.02em;
}}
.sidebar-logo-text span {{ color: {ACCENT}; }}
.sidebar-tagline {{
    font-size: 0.67rem; font-weight: 500;
    color: {TEXT_MUT}; letter-spacing: 0.08em;
    text-transform: uppercase; margin-top: 3px;
}}
.sidebar-status {{
    display: flex; align-items: center; gap: 7px;
    margin-top: 10px; font-size: 0.73rem; color: {C_BAIXO}; font-weight: 500;
}}
.status-dot {{
    width: 7px; height: 7px; border-radius: 50%;
    background: {C_BAIXO}; flex-shrink: 0;
    box-shadow: 0 0 8px {C_BAIXO};
    animation: blink 2.2s ease-in-out infinite;
}}
@keyframes blink {{
    0%, 100% {{ opacity: 1; box-shadow: 0 0 8px {C_BAIXO}; }}
    50% {{ opacity: 0.5; box-shadow: 0 0 3px {C_BAIXO}; }}
}}

/* Nav category labels */
.nav-category {{
    font-size: 0.62rem; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: {TEXT_MUT}; padding: 16px 20px 6px 20px;
    border-top: 1px solid {BORDER};
    margin-top: 4px;
}}
.nav-category:first-of-type {{ border-top: none; margin-top: 0; }}

/* Nav buttons */
.stButton > button.nav-btn {{
    background: transparent !important;
    border: none !important; border-radius: 8px !important;
    color: {TEXT_SEC} !important;
    font-size: 0.875rem !important; font-weight: 500 !important;
    padding: 9px 16px !important; width: 100% !important;
    text-align: left !important; justify-content: flex-start !important;
    box-shadow: none !important; margin-bottom: 2px !important;
    transition: all 0.15s ease !important;
}}
.stButton > button.nav-btn:hover {{
    background: rgba(42,143,212,0.10) !important;
    color: {TEXT_PRI} !important;
    transform: none !important;
    box-shadow: none !important;
}}

/* Sidebar quick stats */
.sidebar-stats {{
    background: {SURFACE}; border: 1px solid {BORDER};
    border-radius: 12px; padding: 16px 18px;
    margin: 12px 16px 12px 16px;
}}
.sidebar-stats-title {{
    font-size: 0.62rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: {TEXT_MUT}; margin-bottom: 12px;
}}
.sidebar-stats-grid {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
}}
.sidebar-stat-item {{}}
.sidebar-stat-value {{
    font-size: 1.4rem; font-weight: 800;
    line-height: 1; font-variant-numeric: tabular-nums;
}}
.sidebar-stat-label {{
    font-size: 0.67rem; color: {TEXT_MUT}; margin-top: 2px;
}}
.sidebar-footer {{
    padding: 8px 20px 16px;
    font-size: 0.63rem; color: {TEXT_MUT}; text-align: center;
    line-height: 1.6;
}}

/* ══════════════════════════════════════════
   CABEÇALHO DE PÁGINA
══════════════════════════════════════════ */
.page-header {{
    display: flex; align-items: center; gap: 16px;
    padding: 8px 0 24px 0;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 28px;
}}
.page-accent {{
    width: 4px; height: 48px; flex-shrink: 0;
    background: linear-gradient(180deg, {ACCENT2}, {ACCENT3});
    border-radius: 2px;
}}
.page-title {{
    font-size: 1.65rem; font-weight: 800;
    color: {TEXT_PRI}; letter-spacing: -0.025em; line-height: 1.2;
}}
.page-subtitle {{
    font-size: 0.82rem; color: {TEXT_SEC}; margin-top: 3px; line-height: 1.5;
}}

/* ══════════════════════════════════════════
   BLOCOS DE SEÇÃO DO DASHBOARD
══════════════════════════════════════════ */
.bloco-header {{
    display: flex; align-items: center; gap: 12px;
    margin: 32px 0 20px 0;
}}
.bloco-number {{
    width: 28px; height: 28px; border-radius: 8px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.78rem; font-weight: 800; color: white;
}}
.bloco-title {{
    font-size: 0.78rem; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: {TEXT_SEC};
}}
.bloco-line {{ flex: 1; height: 1px; background: {BORDER}; }}

/* ══════════════════════════════════════════
   RESUMO INTELIGENTE
══════════════════════════════════════════ */
.resumo-box {{
    background: linear-gradient(135deg, {CARD_HI}, {CARD_BG});
    border: 1px solid {ACCENT2}33;
    border-left: 4px solid {ACCENT2};
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 32px;
    position: relative; overflow: hidden;
}}
.resumo-box::before {{
    content: '';
    position: absolute; top: 0; right: 0;
    width: 120px; height: 120px;
    background: radial-gradient(circle, {ACCENT2}12 0%, transparent 70%);
    pointer-events: none;
}}
.resumo-header {{
    display: flex; align-items: center; gap: 10px; margin-bottom: 12px;
}}
.resumo-ai-tag {{
    display: inline-flex; align-items: center; gap: 5px;
    background: {ACCENT2}1A; border: 1px solid {ACCENT2}44;
    border-radius: 20px; padding: 3px 10px;
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.06em; text-transform: uppercase; color: {ACCENT2};
}}
.resumo-ai-dot {{
    width: 5px; height: 5px; border-radius: 50%;
    background: {ACCENT2}; animation: blink 1.5s infinite;
}}
.resumo-timestamp {{
    font-size: 0.68rem; color: {TEXT_MUT};
    font-family: 'JetBrains Mono', monospace;
}}
.resumo-texto {{
    font-size: 0.92rem; color: {TEXT_SEC};
    line-height: 1.75; font-weight: 400;
}}
.resumo-texto strong {{ color: {TEXT_PRI}; font-weight: 600; }}
.resumo-texto .highlight-critico {{ color: {C_CRITICO}; font-weight: 700; }}
.resumo-texto .highlight-info {{ color: {ACCENT2}; font-weight: 600; }}

/* ══════════════════════════════════════════
   KPI CARDS v3
══════════════════════════════════════════ */
.kpi-v3 {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 20px 22px 18px;
    position: relative; overflow: hidden;
    transition: border-color 0.2s, transform 0.15s;
    height: 100%;
}}
.kpi-v3:hover {{ border-color: {BORDER_HI}; transform: translateY(-2px); }}
.kpi-v3::after {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    border-radius: 14px 14px 0 0;
}}
.kpi-v3.kpi-info::after    {{ background: linear-gradient(90deg, {C_INFO}, transparent); }}
.kpi-v3.kpi-success::after {{ background: linear-gradient(90deg, {C_BAIXO}, transparent); }}
.kpi-v3.kpi-warning::after {{ background: linear-gradient(90deg, {C_MEDIO}, transparent); }}
.kpi-v3.kpi-danger::after  {{ background: linear-gradient(90deg, {C_CRITICO}, transparent); }}
.kpi-v3.kpi-comp::after    {{ background: linear-gradient(90deg, {C_COMP}, transparent); }}
.kpi-v3.kpi-neutral::after {{ background: linear-gradient(90deg, {ACCENT2}, transparent); }}
.kpi-label-v3 {{
    font-size: 0.73rem; font-weight: 600; letter-spacing: 0.09em;
    text-transform: uppercase; color: {TEXT_MUT}; margin-bottom: 10px;
}}
.kpi-value-v3 {{
    font-size: 2.4rem; font-weight: 900;
    color: {TEXT_PRI}; line-height: 1;
    font-variant-numeric: tabular-nums;
    margin-bottom: 6px;
}}
.kpi-sub-v3 {{
    font-size: 0.79rem; color: {TEXT_SEC}; line-height: 1.4;
    margin-bottom: 12px;
}}
.kpi-status-row {{
    display: flex; align-items: center; gap: 6px;
    padding-top: 10px;
    border-top: 1px solid {BORDER};
    font-size: 0.72rem;
}}
.kpi-status-dot {{
    width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
}}

/* ══════════════════════════════════════════
   CARDS DE CONTEÚDO
══════════════════════════════════════════ */
.rg-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 16px;
}}
.rg-card-title {{
    font-size: 0.8rem; font-weight: 700;
    letter-spacing: 0.09em; text-transform: uppercase;
    color: {TEXT_SEC}; margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
}}
.rg-card-title::before {{
    content: ''; display: block;
    width: 3px; height: 14px;
    background: {ACCENT2}; border-radius: 2px; flex-shrink: 0;
}}

/* ══════════════════════════════════════════
   INTERPRETAÇÃO DE GRÁFICO
══════════════════════════════════════════ */
.chart-insight {{
    background: {SURFACE}; border: 1px solid {BORDER};
    border-radius: 8px; padding: 12px 16px; margin-top: 12px;
    font-size: 0.8rem; color: {TEXT_SEC}; line-height: 1.6;
}}
.chart-insight strong {{ color: {TEXT_PRI}; }}
.chart-insight .num {{ 
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600; font-size: 0.84rem;
}}

/* ══════════════════════════════════════════
   ALERTAS v3 — COM ACTION CHIPS
══════════════════════════════════════════ */
.alert-v3 {{
    border-radius: 12px; padding: 18px 20px;
    margin-bottom: 12px; border: 1px solid;
    position: relative; overflow: hidden;
    transition: border-color 0.2s;
}}
.alert-v3::before {{
    content: ''; position: absolute; top: 0; left: 0;
    width: 100%; height: 2px;
}}
.alert-critico {{
    background: linear-gradient(135deg, rgba(230,57,70,0.08), rgba(230,57,70,0.03));
    border-color: rgba(230,57,70,0.30);
}}
.alert-critico::before {{ background: {C_CRITICO}; }}
.alert-alto {{
    background: linear-gradient(135deg, rgba(244,123,53,0.08), rgba(244,123,53,0.03));
    border-color: rgba(244,123,53,0.30);
}}
.alert-alto::before {{ background: {C_ALTO}; }}
.alert-medio {{
    background: linear-gradient(135deg, rgba(244,166,42,0.08), rgba(244,166,42,0.03));
    border-color: rgba(244,166,42,0.30);
}}
.alert-medio::before {{ background: {C_MEDIO}; }}

.alert-top-row {{
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 8px;
}}
.alert-badge {{
    display: inline-flex; align-items: center; gap: 5px;
    padding: 3px 10px; border-radius: 20px;
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.06em; text-transform: uppercase;
}}
.badge-critico {{ background: rgba(230,57,70,0.15); color:{C_CRITICO}; border:1px solid rgba(230,57,70,0.3); }}
.badge-alto    {{ background: rgba(244,123,53,0.15); color:{C_ALTO};    border:1px solid rgba(244,123,53,0.3); }}
.badge-medio   {{ background: rgba(244,166,42,0.15); color:{C_MEDIO};   border:1px solid rgba(244,166,42,0.3); }}
.badge-baixo   {{ background: rgba(12,184,122,0.15); color:{C_BAIXO};   border:1px solid rgba(12,184,122,0.3); }}
.badge-comp    {{ background: rgba(123,94,167,0.15); color:{C_COMP};    border:1px solid rgba(123,94,167,0.3); }}
.badge-pulse {{
    width: 6px; height: 6px; border-radius: 50%;
    animation: blink 1.6s infinite; flex-shrink: 0;
}}
.pulse-critico {{ background: {C_CRITICO}; }}
.pulse-alto    {{ background: {C_ALTO}; }}
.pulse-medio   {{ background: {C_MEDIO}; }}

.alert-timestamp {{ font-size: 0.67rem; color: {TEXT_MUT}; font-family: 'JetBrains Mono',monospace; }}
.alert-titulo-v3 {{ font-size: 0.9rem; font-weight: 700; color: {TEXT_PRI}; margin-bottom: 5px; }}
.alert-descricao {{ font-size: 0.8rem; color: {TEXT_SEC}; line-height: 1.55; margin-bottom: 10px; }}
.alert-meta-row {{
    display: flex; align-items: center; gap: 16px;
    font-size: 0.74rem; color: {TEXT_MUT};
    margin-bottom: 12px; flex-wrap: wrap;
}}
.alert-meta-item {{
    display: flex; align-items: center; gap: 4px;
}}
.alert-meta-label {{ color: {TEXT_MUT}; }}
.alert-meta-value {{ color: {TEXT_SEC}; font-weight: 500; font-family: 'JetBrains Mono',monospace; }}
.alert-acao {{
    font-size: 0.74rem; color: {TEXT_MUT};
    border-top: 1px solid rgba(255,255,255,0.06);
    padding-top: 10px; line-height: 1.5;
}}
.alert-acao strong {{ color: {TEXT_SEC}; }}

.chips-row {{
    display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px;
}}
.chip {{
    display: inline-block;
    padding: 4px 12px; border-radius: 20px;
    font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.04em; cursor: default;
    border: 1px solid; white-space: nowrap;
}}
.chip-primary {{ background: {ACCENT2}1A; color: {ACCENT2}; border-color: {ACCENT2}44; }}
.chip-neutral {{ background: {SURFACE}; color: {TEXT_MUT}; border-color: {BORDER}; }}
.chip-warn    {{ background: rgba(244,166,42,0.10); color: {C_MEDIO}; border-color: rgba(244,166,42,0.3); }}
.chip-comp    {{ background: rgba(123,94,167,0.12); color: {C_COMP};  border-color: rgba(123,94,167,0.3); }}

/* ══════════════════════════════════════════
   DIVISORES DE SEÇÃO
══════════════════════════════════════════ */
.section-divider {{
    display: flex; align-items: center; gap: 12px;
    margin: 28px 0 18px 0;
}}
.section-divider-line {{ flex: 1; height: 1px; background: {BORDER}; }}
.section-divider-text {{
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.13em;
    text-transform: uppercase; color: {TEXT_MUT}; padding: 0 6px;
    white-space: nowrap;
}}

/* ══════════════════════════════════════════
   BADGES DE RISCO
══════════════════════════════════════════ */
.rbadge {{
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em;
    text-transform: uppercase;
}}
.rbadge-baixo   {{ background:rgba(12,184,122,0.15); color:{C_BAIXO};   border:1px solid rgba(12,184,122,0.35); }}
.rbadge-medio   {{ background:rgba(244,166,42,0.15); color:{C_MEDIO};   border:1px solid rgba(244,166,42,0.35); }}
.rbadge-alto    {{ background:rgba(244,123,53,0.15); color:{C_ALTO};    border:1px solid rgba(244,123,53,0.35); }}
.rbadge-critico {{ background:rgba(230,57,70,0.15);  color:{C_CRITICO}; border:1px solid rgba(230,57,70,0.35); }}

/* ══════════════════════════════════════════
   COMPONENTES NATIVOS — OVERRIDES
══════════════════════════════════════════ */
[data-testid="metric-container"] {{
    background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 12px; padding: 18px;
}}
[data-testid="stMetricValue"]  {{ color: {TEXT_PRI} !important; font-weight: 700 !important; font-size: 1.5rem !important; }}
[data-testid="stMetricLabel"]  {{ color: {TEXT_SEC} !important; font-size: 0.8rem !important; }}

[data-testid="stForm"] {{
    background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 14px; padding: 24px !important;
}}
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stTextArea>div>div>textarea {{
    background: {SURFACE} !important; border: 1px solid {BORDER} !important;
    color: {TEXT_PRI} !important; border-radius: 8px !important; font-size: 0.88rem !important;
}}
.stSelectbox>div>div, .stMultiSelect>div>div {{
    background: {SURFACE} !important; border: 1px solid {BORDER} !important;
    border-radius: 8px !important; color: {TEXT_PRI} !important;
}}
label {{ color: {TEXT_SEC} !important; font-size: 0.84rem !important; font-weight: 500 !important; }}

[data-testid="stTabs"] [role="tablist"] {{
    background: {SURFACE}; border-radius: 10px; padding: 4px;
    border: 1px solid {BORDER}; gap: 3px;
}}
[data-testid="stTabs"] [role="tab"] {{
    color: {TEXT_MUT} !important; border-radius: 7px !important;
    font-size: 0.84rem !important; font-weight: 600 !important;
    padding: 9px 18px !important; border: none !important;
    transition: all 0.15s !important;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    background: {ACCENT2} !important; color: white !important;
}}
[data-testid="stTabs"] [role="tabpanel"] {{ padding-top: 22px; }}

.stButton > button {{
    background: linear-gradient(135deg, {ACCENT2}, #1A6BA0) !important;
    color: white !important; border: none !important;
    border-radius: 9px !important; font-weight: 600 !important;
    font-size: 0.86rem !important; padding: 10px 22px !important;
    box-shadow: 0 4px 15px rgba(42,143,212,0.25) !important;
    transition: all 0.2s !important;
}}
.stButton > button:hover {{
    box-shadow: 0 6px 22px rgba(42,143,212,0.40) !important;
    transform: translateY(-1px) !important;
}}
.stButton > button[kind="secondary"] {{
    background: {SURFACE} !important; border: 1px solid {BORDER} !important;
    box-shadow: none !important; color: {TEXT_SEC} !important;
}}
.stDownloadButton > button {{
    background: linear-gradient(135deg, #1FA060, #16784A) !important;
    color: white !important; border: none !important;
    border-radius: 9px !important; font-weight: 600 !important;
    box-shadow: 0 4px 15px rgba(31,160,96,0.25) !important;
}}

[data-testid="stExpander"] {{
    background: {CARD_BG} !important; border: 1px solid {BORDER} !important; border-radius: 10px !important;
}}
[data-testid="stExpander"] summary {{ color: {TEXT_PRI} !important; font-weight: 600 !important; font-size: 0.88rem !important; }}

[data-testid="stDataFrame"] {{ border-radius: 10px; overflow: hidden; border: 1px solid {BORDER}; }}

/* Boxes de feedback */
.info-box  {{ background:rgba(42,143,212,0.10); border-left:4px solid {ACCENT2};  border-radius:0 9px 9px 0; padding:13px 18px; margin:10px 0; font-size:0.86rem; color:{TEXT_SEC}; line-height:1.6; }}
.warn-box  {{ background:rgba(244,166,42,0.09); border-left:4px solid {C_MEDIO};  border-radius:0 9px 9px 0; padding:13px 18px; margin:10px 0; font-size:0.86rem; color:{TEXT_SEC}; line-height:1.6; }}
.danger-box {{ background:rgba(230,57,70,0.09); border-left:4px solid {C_CRITICO}; border-radius:0 9px 9px 0; padding:13px 18px; margin:10px 0; font-size:0.86rem; color:{TEXT_SEC}; line-height:1.6; }}

/* Relatório executivo */
.exec-report-header {{
    background: linear-gradient(135deg, {CARD_HI}, {CARD_BG});
    border: 1px solid {BORDER}; border-radius: 16px;
    padding: 28px 32px; margin-bottom: 24px; position: relative; overflow: hidden;
}}
.exec-title {{ font-size: 1.4rem; font-weight: 800; color: {TEXT_PRI}; letter-spacing:-0.02em; }}
.exec-subtitle {{ font-size: 0.84rem; color: {TEXT_SEC}; margin-top: 5px; }}
.exec-badge {{ display:inline-block; margin-top:14px; padding:6px 14px; border-radius:20px; font-size:0.75rem; font-weight:700; letter-spacing:0.06em; text-transform:uppercase; }}

/* ESG bars */
.esg-bar-wrap {{ margin-bottom: 14px; }}
.esg-bar-label {{ display:flex; justify-content:space-between; font-size:0.79rem; color:{TEXT_SEC}; margin-bottom:6px; }}
.esg-bar-track {{ height:8px; background:{BORDER}; border-radius:4px; overflow:hidden; }}
.esg-bar-fill  {{ height:100%; border-radius:4px; transition: width 0.6s ease; }}

/* Key-value rows */
.kv-row {{ display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid {BORDER}; }}
.kv-label {{ font-size:0.79rem; color:{TEXT_MUT}; }}
.kv-value {{ font-size:0.82rem; color:{TEXT_PRI}; font-weight:500; font-family:'JetBrains Mono',monospace; }}

/* Scrollbar */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {PRIMARY}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {ACCENT2}; }}


/* ══════════════════════════════════════════
   RESPONSIVIDADE — MOBILE / TABLET
══════════════════════════════════════════ */

/* Tablet (≤ 1024px) */
@media (max-width: 1024px) {{
    .main .block-container {{ padding: 1.2rem 1.2rem 3rem 1.2rem !important; }}
    .kpi-value-v3 {{ font-size: 1.9rem !important; }}
    .resumo-texto {{ font-size: 0.87rem !important; }}
    .page-title   {{ font-size: 1.35rem !important; }}
    .bloco-title  {{ font-size: 0.72rem !important; }}
}}

/* Mobile (≤ 768px) */
@media (max-width: 768px) {{
    /* Layout principal */
    .main .block-container {{
        padding: 0.8rem 0.8rem 2rem 0.8rem !important;
    }}

    /* Títulos */
    .page-title      {{ font-size: 1.15rem !important; }}
    .page-subtitle   {{ font-size: 0.74rem !important; }}
    .page-accent     {{ height: 36px !important; }}
    .exec-title      {{ font-size: 1.1rem !important; }}
    .exec-subtitle   {{ font-size: 0.76rem !important; }}

    /* Resumo inteligente */
    .resumo-box      {{ padding: 14px 16px !important; }}
    .resumo-texto    {{ font-size: 0.82rem !important; line-height: 1.6 !important; }}
    .resumo-ai-tag   {{ font-size: 0.62rem !important; }}

    /* KPI cards — empilhar em coluna única em telas muito pequenas */
    .kpi-v3          {{ padding: 14px 14px 12px !important; border-radius: 10px !important; }}
    .kpi-value-v3    {{ font-size: 1.7rem !important; }}
    .kpi-label-v3    {{ font-size: 0.66rem !important; }}
    .kpi-sub-v3      {{ font-size: 0.73rem !important; }}

    /* Cards de conteúdo */
    .rg-card         {{ padding: 14px 14px !important; border-radius: 10px !important; }}
    .rg-card-title   {{ font-size: 0.73rem !important; margin-bottom: 10px !important; }}

    /* Alertas */
    .alert-v3            {{ padding: 12px 14px !important; border-radius: 9px !important; }}
    .alert-titulo-v3     {{ font-size: 0.84rem !important; }}
    .alert-descricao     {{ font-size: 0.75rem !important; }}
    .alert-meta-row      {{ gap: 10px !important; font-size: 0.68rem !important; }}
    .alert-acao          {{ font-size: 0.69rem !important; }}
    .chips-row           {{ gap: 4px !important; margin-top: 8px !important; }}
    .chip                {{ font-size: 0.63rem !important; padding: 3px 9px !important; }}
    .alert-timestamp     {{ font-size: 0.62rem !important; }}

    /* Bloco headers */
    .bloco-header    {{ margin: 20px 0 12px 0 !important; }}
    .bloco-number    {{ width: 24px !important; height: 24px !important; font-size: 0.72rem !important; }}
    .bloco-title     {{ font-size: 0.66rem !important; }}

    /* Divisores */
    .section-divider      {{ margin: 18px 0 12px 0 !important; }}
    .section-divider-text {{ font-size: 0.62rem !important; }}

    /* Chart insight */
    .chart-insight   {{ font-size: 0.74rem !important; padding: 10px 12px !important; }}

    /* Sidebar (colapsa naturalmente no Streamlit mobile) */
    [data-testid="stSidebar"] {{ min-width: 200px !important; }}
    .sidebar-logo-text   {{ font-size: 1rem !important; }}
    .sidebar-stats       {{ padding: 12px 14px !important; margin: 8px 10px !important; }}
    .sidebar-stat-value  {{ font-size: 1.2rem !important; }}

    /* Formulários */
    [data-testid="stForm"] {{ padding: 14px !important; }}

    /* Abas */
    [data-testid="stTabs"] [role="tab"] {{
        font-size: 0.75rem !important;
        padding: 7px 10px !important;
    }}

    /* Relatório executivo */
    .exec-report-header  {{ padding: 18px 20px !important; border-radius: 12px !important; }}

    /* Métricas nativas */
    [data-testid="stMetricValue"] {{ font-size: 1.25rem !important; }}

    /* Scrollbar mais fina */
    ::-webkit-scrollbar {{ width: 3px !important; height: 3px !important; }}
}}

/* Telas muito pequenas (≤ 480px) */
@media (max-width: 480px) {{
    .main .block-container {{ padding: 0.6rem 0.6rem 2rem 0.6rem !important; }}
    .page-title      {{ font-size: 1rem !important; }}
    .kpi-value-v3    {{ font-size: 1.5rem !important; }}
    .resumo-texto    {{ font-size: 0.78rem !important; }}
    .alert-v3        {{ padding: 10px 12px !important; }}

    /* Colunas de alertas ficam empilhadas */
    .chips-row       {{ flex-direction: column !important; }}
    .chip            {{ width: 100% !important; text-align: center !important; }}
}}

/* Forçar colunas Streamlit a empilharem em mobile */
@media (max-width: 640px) {{
    [data-testid="column"] {{
        min-width: 100% !important;
        width: 100% !important;
    }}
    /* Plots ficam full width */
    [data-testid="stPlotlyChart"] {{
        width: 100% !important;
    }}
}}

/* Ocultar elementos desnecessários */
#MainMenu {{ visibility: hidden; }}
footer    {{ visibility: hidden; }}
header    {{ visibility: hidden; }}
div[data-testid="stSidebarNav"] {{ display: none; }}
</style>
"""

# ═══════════════════════════════════════════════════════════════════════════
#  INICIALIZAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_resource
def inicializar():
    db.init_database()
    if db.check_db_empty():
        seed_data.seed_database()

inicializar()
st.markdown(CSS, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  TEMA PLOTLY
# ═══════════════════════════════════════════════════════════════════════════

def _pt(fig, h=None, title_font_size=13):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=TEXT_SEC, size=12),
        title=dict(font=dict(color=TEXT_PRI, size=title_font_size, family="Inter")),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER,
                   tickfont=dict(color=TEXT_MUT, size=11), title_font=dict(color=TEXT_MUT)),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER,
                   tickfont=dict(color=TEXT_MUT, size=11), title_font=dict(color=TEXT_MUT)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_SEC, size=11),
                    bordercolor=BORDER, borderwidth=0),
        hoverlabel=dict(bgcolor=CARD_HI, bordercolor=BORDER,
                        font=dict(family="Inter", color=TEXT_PRI, size=12)),
        margin=dict(t=44, b=32, l=12, r=12),
        colorway=[ACCENT2, C_BAIXO, C_MEDIO, C_ALTO, C_CRITICO, C_COMP, "#1ABC9C"],
    )
    if h:
        fig.update_layout(height=h)
    return fig

def gauge_risco(score, nivel, h=240):
    cor = RISK_C.get(nivel, TEXT_SEC)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "/100", "font": {"size": 28, "color": cor, "family": "Inter"}},
        title={"text": f"<b>{nivel}</b>", "font": {"size": 13, "color": cor, "family": "Inter"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": BORDER,
                     "tickfont": {"color": TEXT_MUT, "size": 9}},
            "bar": {"color": cor, "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0)", "bordercolor": BORDER,
            "steps": [
                {"range": [0, 25],  "color": "rgba(12,184,122,0.10)"},
                {"range": [25, 50], "color": "rgba(244,166,42,0.10)"},
                {"range": [50, 75], "color": "rgba(244,123,53,0.10)"},
                {"range": [75, 100],"color": "rgba(230,57,70,0.10)"},
            ],
            "threshold": {"line": {"color": cor, "width": 3},
                          "thickness": 0.75, "value": score},
        },
    ))
    fig.update_layout(height=h, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=28, b=8, l=20, r=20),
                      font=dict(family="Inter"))
    return fig

# ═══════════════════════════════════════════════════════════════════════════
#  SIDEBAR — MENU CATEGORIZADO
# ═══════════════════════════════════════════════════════════════════════════

# Estado de navegação
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Dashboard"

CATEGORIAS = {
    "Operação":    ["Dashboard", "Trechos", "Ativos", "Inspeções", "Zona Crítica"],
    "Inteligência":["Modelo Preditivo", "Compliance", "Auditoria"],
    "Gestão":      ["ESG", "Relatórios", "Configurações"],
}
CAT_COLORS = {"Operação": ACCENT2, "Inteligência": C_COMP, "Gestão": C_BAIXO}

with st.sidebar:
    # ── Logo / Branding ──
    st.markdown(f"""
    <div class="sidebar-brand-wrap">
        <div class="sidebar-logo-text">Rail<span>Guard</span> AI</div>
        <div class="sidebar-tagline">Centro de Controle Ferroviário</div>
        <div class="sidebar-status">
            <div class="status-dot"></div>
            Sistema Operacional
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Menu categorizado ──
    pagina_atual = st.session_state["pagina"]
    for cat, itens in CATEGORIAS.items():
        cor_cat = CAT_COLORS[cat]
        st.markdown(f"""
        <div style="padding:14px 20px 5px 20px; font-size:0.62rem; font-weight:700;
                    letter-spacing:0.14em; text-transform:uppercase; color:{TEXT_MUT};
                    border-top:1px solid {BORDER}; margin-top:4px;">
            <span style="color:{cor_cat}88;">▸</span> {cat}
        </div>
        """, unsafe_allow_html=True)
        for item in itens:
            # Botão nativo do Streamlit; a página ativa usa o estilo primário
            if st.button(
                item,
                key=f"nav_{item}",
                width="stretch",
                type="primary" if item == pagina_atual else "secondary",
            ):
                st.session_state["pagina"] = item
                st.rerun()

    pagina = st.session_state["pagina"]

    # ── Quick stats ──
    sb = db.get_dashboard_stats()
    st.markdown(f"""
    <div class="sidebar-stats">
        <div class="sidebar-stats-title">Visão Rápida</div>
        <div class="sidebar-stats-grid">
            <div class="sidebar-stat-item">
                <div class="sidebar-stat-value" style="color:{TEXT_PRI};">{sb["total_ativos"]}</div>
                <div class="sidebar-stat-label">Ativos</div>
            </div>
            <div class="sidebar-stat-item">
                <div class="sidebar-stat-value" style="color:{C_CRITICO};">{sb["risco_critico"]}</div>
                <div class="sidebar-stat-label">Críticos</div>
            </div>
            <div class="sidebar-stat-item">
                <div class="sidebar-stat-value" style="color:{TEXT_PRI};">{sb["total_inspecoes"]}</div>
                <div class="sidebar-stat-label">Inspeções</div>
            </div>
            <div class="sidebar-stat-item">
                <div class="sidebar-stat-value" style="color:{C_MEDIO};">{sb["total_alertas_abertos"]}</div>
                <div class="sidebar-stat-label">Alertas</div>
            </div>
        </div>
    </div>
    <div class="sidebar-footer">
        MVP v0.4 · {datetime.now().strftime("%d/%m/%Y %H:%M")}<br>
        Dados simulados — uso demonstrativo
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS GLOBAIS
# ═══════════════════════════════════════════════════════════════════════════

def ph(title, subtitle=""):
    """Cabeçalho de página."""
    st.markdown(f"""
    <div class="page-header">
        <div class="page-accent"></div>
        <div>
            <div class="page-title">{title}</div>
            {"<div class='page-subtitle'>" + subtitle + "</div>" if subtitle else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)

def bloco(numero, titulo, cor=ACCENT2):
    """Cabeçalho numerado de bloco do dashboard."""
    st.markdown(f"""
    <div class="bloco-header">
        <div class="bloco-number" style="background:{cor};">{numero}</div>
        <div class="bloco-title">{titulo}</div>
        <div class="bloco-line"></div>
    </div>
    """, unsafe_allow_html=True)

def kpi_v3(label, value, sub, status_text, status_cor, variant="neutral"):
    """Card KPI v3 com subtítulo e linha de status."""
    st.markdown(f"""
    <div class="kpi-v3 kpi-{variant}">
        <div class="kpi-label-v3">{label}</div>
        <div class="kpi-value-v3">{value}</div>
        <div class="kpi-sub-v3">{sub}</div>
        <div class="kpi-status-row">
            <div class="kpi-status-dot" style="background:{status_cor};box-shadow:0 0 5px {status_cor}55;"></div>
            <span style="color:{status_cor};font-weight:600;">{status_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def sdiv(label):
    st.markdown(f"""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <div class="section-divider-text">{label}</div>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)

def info(msg):  st.markdown(f'<div class="info-box">{msg}</div>', unsafe_allow_html=True)
def warn(msg):  st.markdown(f'<div class="warn-box">{msg}</div>', unsafe_allow_html=True)
def danger(msg):st.markdown(f'<div class="danger-box">{msg}</div>', unsafe_allow_html=True)

def row_kv(lbl, val):
    return f'<div class="kv-row"><span class="kv-label">{lbl}</span><span class="kv-value">{val}</span></div>'

def chart_insight(texto):
    st.markdown(f'<div class="chart-insight">{texto}</div>', unsafe_allow_html=True)

def flash(html, kind="info"):
    """Guarda uma mensagem para exibir após o st.rerun() (senão ela se perde)."""
    pendentes = st.session_state.get("_flash", [])
    st.session_state["_flash"] = pendentes + [(kind, html)]

def mostrar_flash():
    """Exibe e consome as mensagens pendentes gravadas por flash()."""
    render = {"info": info, "warn": warn, "danger": danger,
              "html": lambda h: st.markdown(h, unsafe_allow_html=True)}
    pendentes = st.session_state.get("_flash", [])
    st.session_state["_flash"] = []
    for kind, html in pendentes:
        render.get(kind, info)(html)

def alert_card_v3(tipo, urgencia, descricao, ativo_cod, trecho_cod, score_label, score_val, dt_str, acao):
    """Card de alerta v3 com chips de ação."""
    sev = urgencia.lower()
    if sev == "urgente":
        ac, badge_cls, pulse_cls = "critico", "badge-critico", "pulse-critico"
    elif sev == "alta":
        ac, badge_cls, pulse_cls = "alto",    "badge-alto",    "pulse-alto"
    else:
        ac, badge_cls, pulse_cls = "medio",   "badge-medio",   "pulse-medio"

    chips_html = """
    <div class="chips-row">
        <span class="chip chip-primary">Analisar ocorrência</span>
        <span class="chip chip-comp">Gerar relatório</span>
        <span class="chip chip-neutral">Em acompanhamento</span>
    </div>
    """
    st.markdown(f"""
    <div class="alert-v3 alert-{ac}">
        <div class="alert-top-row">
            <span class="alert-badge {badge_cls}">
                <span class="badge-pulse {pulse_cls}"></span>
                {urgencia}
            </span>
            <span class="alert-timestamp">{dt_str}</span>
        </div>
        <div class="alert-titulo-v3">{tipo}</div>
        <div class="alert-descricao">{descricao}</div>
        <div class="alert-meta-row">
            <div class="alert-meta-item">
                <span class="alert-meta-label">Ativo:</span>
                <span class="alert-meta-value">{ativo_cod}</span>
            </div>
            <div class="alert-meta-item">
                <span class="alert-meta-label">Trecho:</span>
                <span class="alert-meta-value">{trecho_cod}</span>
            </div>
            <div class="alert-meta-item">
                <span class="alert-meta-label">{score_label}:</span>
                <span class="alert-meta-value">{score_val}</span>
            </div>
        </div>
        <div class="alert-acao">
            <strong>Ação recomendada:</strong> {acao}
        </div>
        {chips_html}
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  RESUMO INTELIGENTE DA OPERAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

def gerar_resumo_inteligente(stats, df_riscos, df_alertas):
    """Gera texto de resumo inteligente em linguagem humana."""
    total_insp  = stats["total_inspecoes"]
    n_alto      = stats["risco_alto"]
    n_crit      = stats["risco_critico"]
    n_alertas   = stats["total_alertas_abertos"]
    n_ativos    = stats["total_ativos"]
    n_trechos   = stats["total_trechos"]
    total_risco = n_alto + n_crit
    pct_risco   = (total_risco / total_insp * 100) if total_insp > 0 else 0

    # Identifica ativos críticos para citar
    ativos_crit = []
    if not df_riscos.empty:
        crit_rows = df_riscos[df_riscos["nivel_risco"] == "Crítico"]
        if "ativo_codigo" in crit_rows.columns:
            ativos_crit = crit_rows["ativo_codigo"].dropna().unique()[:3].tolist()

    # Nível geral de atenção
    if n_crit >= 5:
        nivel_geral = f'<span class="highlight-critico">situação crítica</span>'
        recomendacao = "Recomenda-se acionar imediatamente a equipe de manutenção e revisar os planos de contingência."
    elif n_crit >= 2 or n_alto >= 5:
        nivel_geral = f'<span class="highlight-info">atenção elevada</span>'
        recomendacao = "Recomenda-se priorizar as inspeções nos ativos em nível alto e crítico nas próximas 48 horas."
    elif total_risco > 0:
        nivel_geral = "atenção moderada"
        recomendacao = "Acompanhe os ativos em nível alto e programe inspeções preventivas."
    else:
        nivel_geral = f'<span style="color:{C_BAIXO};font-weight:600;">situação sob controle</span>'
        recomendacao = "Manter rotina de inspeções preventivas conforme calendário vigente."

    citar_ativos = ""
    if ativos_crit:
        lista = ", ".join(f"<strong>{a}</strong>" for a in ativos_crit)
        citar_ativos = f" Atenção prioritária aos ativos: {lista}."

    texto = (
        f"A malha ferroviária monitorada conta com <strong>{n_trechos} trechos</strong> "
        f"e <strong>{n_ativos} ativos</strong> cadastrados. "
        f"Das <strong>{total_insp} inspeções técnicas</strong> registradas, "
        f"<strong>{total_risco}</strong> foram classificadas entre nível alto e crítico "
        f"(<strong>{pct_risco:.1f}%</strong> da amostra). "
        f"Há <strong>{n_alertas}</strong> alertas operacionais abertos, "
        f"sendo <strong>{n_crit}</strong> em nível crítico. "
        f"O sistema identifica {nivel_geral} na operação atual.{citar_ativos} "
        f"{recomendacao}"
    )
    return texto


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE — DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

def page_dashboard():
    ph("Centro de Controle Operacional",
       "Visão consolidada da malha ferroviária monitorada — RailGuard AI v0.4")

    stats     = db.get_dashboard_stats()
    df_riscos = db.get_all_riscos()
    df_ativos = db.get_all_ativos()
    df_insp   = db.get_all_inspecoes()
    df_al     = db.get_all_alertas()
    df_ab     = df_al[df_al["status"] == "Aberto"]

    # ── RESUMO INTELIGENTE ──────────────────────────────────────────────
    resumo = gerar_resumo_inteligente(stats, df_riscos, df_ab)
    st.markdown(f"""
    <div class="resumo-box">
        <div class="resumo-header">
            <div class="resumo-ai-tag">
                <div class="resumo-ai-dot"></div>
                RailGuard AI · Análise Automática
            </div>
            <span class="resumo-timestamp">{datetime.now().strftime("%d/%m/%Y %H:%M")}</span>
        </div>
        <div class="resumo-texto">{resumo}</div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    #  BLOCO 1 — SITUAÇÃO GERAL DA OPERAÇÃO
    # ══════════════════════════════════════════════════════════════════
    bloco("1", "SITUAÇÃO GERAL DA OPERAÇÃO", ACCENT2)

    c1, c2, c3, c4, c5 = st.columns(5)
    total_oc = stats["risco_alto"] + stats["risco_critico"]
    pct_oc   = (total_oc / stats["total_inspecoes"] * 100) if stats["total_inspecoes"] > 0 else 0
    n_zonas  = stats.get("total_zonas_criticas", 0)

    with c1:
        kpi_v3("Trechos Monitorados", stats["total_trechos"],
               "Malha ferroviária ativa",
               "Normal", C_BAIXO, "neutral")
    with c2:
        kpi_v3("Ativos Monitorados", stats["total_ativos"],
               "Infraestrutura em operação",
               "Monitoramento contínuo", ACCENT2, "neutral")
    with c3:
        kpi_v3("Inspeções Técnicas", stats["total_inspecoes"],
               "Registros de campo acumulados",
               "Base de análise", C_BAIXO, "success")
    with c4:
        st_cor = C_CRITICO if stats["total_alertas_abertos"] > 5 else C_MEDIO
        st_txt = "Atenção operacional" if stats["total_alertas_abertos"] > 0 else "Sem alertas"
        kpi_v3("Alertas Abertos", stats["total_alertas_abertos"],
               f"{stats['risco_critico']} requerem ação imediata",
               st_txt, st_cor, "danger")
    with c5:
        oc_txt = "Prioridade alta" if total_oc > 5 else "Monitorar"
        oc_cor = C_CRITICO if stats["risco_critico"] > 3 else C_ALTO
        kpi_v3("Ocorrências Críticas", total_oc,
               f"{stats['risco_critico']} críticos · {pct_oc:.0f}% da malha",
               oc_txt, oc_cor, "warning")

    # KPI extra: Zonas Críticas (mostra abaixo dos 5 cards principais)
    if n_zonas > 0:
        st.markdown(f"""
        <div style="background:rgba(230,57,70,0.10);border:1px solid rgba(230,57,70,0.40);
                    border-left:5px solid {C_CRITICO};border-radius:12px;
                    padding:14px 20px;margin-top:14px;
                    display:flex;align-items:center;gap:16px;">
            <div>
                <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.1em;
                            text-transform:uppercase;color:{TEXT_MUT};">
                    Zonas Críticas Ativas
                </div>
                <div style="font-size:1.4rem;font-weight:900;color:{C_CRITICO};">
                    {n_zonas} zona{"s" if n_zonas > 1 else ""} detectada{"s" if n_zonas > 1 else ""}
                </div>
                <div style="font-size:0.8rem;color:{TEXT_SEC};margin-top:2px;">
                    Concentração espacial de defeitos — acesse <b>Zona Crítica</b> no menu para análise completa
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    #  BLOCO 2 — ANÁLISE DE RISCO OPERACIONAL
    # ══════════════════════════════════════════════════════════════════
    bloco("2", "ANÁLISE DE RISCO OPERACIONAL", C_ALTO)

    ca, cb, cc = st.columns([1.1, 1.2, 1.7])

    # ── Donut distribuição ──
    with ca:
        st.markdown('<div class="rg-card"><div class="rg-card-title">Distribuição de Risco</div>',
                    unsafe_allow_html=True)
        dr = pd.DataFrame({
            "Nível": ["Baixo", "Médio", "Alto", "Crítico"],
            "Qtd":   [stats["risco_baixo"], stats["risco_medio"],
                      stats["risco_alto"],  stats["risco_critico"]],
        })
        total_dr = int(dr["Qtd"].sum())
        fig = go.Figure(go.Pie(
            labels=dr["Nível"], values=dr["Qtd"], hole=0.64,
            marker=dict(colors=[C_BAIXO, C_MEDIO, C_ALTO, C_CRITICO],
                        line=dict(color=PRIMARY, width=3)),
            textfont=dict(family="Inter", size=10, color="white"),
            hovertemplate="<b>%{label}</b><br>%{value} inspeções (%{percent})<extra></extra>",
        ))
        fig.add_annotation(
            text=f"<b>{total_dr}</b><br><span style='font-size:9px;color:{TEXT_MUT}'>INSPEÇÕES</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=17, color=TEXT_PRI, family="Inter"),
        )
        _pt(fig); fig.update_layout(
            showlegend=True, height=260,
            legend=dict(orientation="v", x=0.98, y=0.5, font=dict(size=11, color=TEXT_SEC)),
            margin=dict(t=8, b=8, l=0, r=80),
        )
        st.plotly_chart(fig, width="stretch")
        pct_ac = (total_oc / total_dr * 100) if total_dr > 0 else 0
        chart_insight(
            f"<strong>{total_dr}</strong> inspeções analisadas. "
            f"<strong>{total_oc}</strong> classificadas entre alto e crítico "
            f"(<strong class='num'>{pct_ac:.1f}%</strong> da amostra exige atenção). "
            f"Nível crítico representa <strong class='num'>{stats['risco_critico']}</strong> ocorrências."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Barras de volume ──
    with cb:
        st.markdown('<div class="rg-card"><div class="rg-card-title">Volume por Nível</div>',
                    unsafe_allow_html=True)
        fig2 = go.Figure()
        for nivel, cor, key in [
            ("Baixo",   C_BAIXO, "risco_baixo"),
            ("Médio",   C_MEDIO, "risco_medio"),
            ("Alto",    C_ALTO,  "risco_alto"),
            ("Crítico", C_CRITICO,"risco_critico"),
        ]:
            qtd = stats[key]
            fig2.add_trace(go.Bar(
                x=[nivel], y=[qtd],
                marker=dict(color=cor, opacity=0.88, cornerradius=7),
                text=[qtd], textposition="outside",
                textfont=dict(color=cor, size=14, family="Inter"),
                hovertemplate=f"<b>{nivel}</b>: {qtd} inspeções<extra></extra>",
                name=nivel,
            ))
        _pt(fig2); fig2.update_layout(
            showlegend=False, height=215, bargap=0.28,
            margin=dict(t=8, b=8, l=8, r=8),
            yaxis=dict(showgrid=True, gridcolor=BORDER),
            xaxis=dict(showgrid=False, tickfont=dict(size=12, color=TEXT_SEC)),
        )
        st.plotly_chart(fig2, width="stretch")
        maior_nivel = dr.loc[dr["Qtd"].idxmax(), "Nível"]
        chart_insight(
            f"Nível predominante: <strong>{maior_nivel}</strong>. "
            f"Relação alto/crítico representa <strong class='num'>{pct_ac:.0f}%</strong> "
            f"do total de avaliações registradas no sistema."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Linha de evolução ──
    with cc:
        st.markdown('<div class="rg-card"><div class="rg-card-title">Evolução das Inspeções Técnicas — 12 Meses</div>',
                    unsafe_allow_html=True)
        if not df_insp.empty:
            df_insp["data_inspecao"] = pd.to_datetime(df_insp["data_inspecao"])
            df_insp["mes"] = df_insp["data_inspecao"].dt.to_period("M").astype(str)
            dm = df_insp.groupby("mes").size().reset_index(name="total").tail(12)
            media = dm["total"].mean()

            fig3 = go.Figure()
            # Linha de média
            fig3.add_trace(go.Scatter(
                x=dm["mes"], y=[media] * len(dm),
                mode="lines", line=dict(color=TEXT_MUT, width=1.5, dash="dot"),
                hoverinfo="skip", name=f"Média ({media:.0f})",
            ))
            # Área preenchida
            fig3.add_trace(go.Scatter(
                x=dm["mes"], y=dm["total"],
                fill="tozeroy", fillcolor="rgba(42,143,212,0.10)",
                line=dict(color=ACCENT2, width=2.5, shape="spline"),
                mode="lines+markers",
                marker=dict(size=7, color=ACCENT2, line=dict(color=PRIMARY, width=2)),
                hovertemplate="<b>%{x}</b><br>Inspeções: <b>%{y}</b><extra></extra>",
                name="Inspeções",
            ))
            _pt(fig3); fig3.update_layout(
                showlegend=True, height=260,
                margin=dict(t=8, b=8, l=8, r=8),
                xaxis=dict(showgrid=False, tickangle=-30),
                yaxis=dict(showgrid=True, gridcolor=BORDER),
                legend=dict(orientation="h", y=1.02, font=dict(size=10)),
            )
            st.plotly_chart(fig3, width="stretch")
            pico = int(dm["total"].max())
            mes_pico = dm.loc[dm["total"].idxmax(), "mes"]
            chart_insight(
                f"Período: últimos <strong>12 meses</strong>. "
                f"Média mensal: <strong class='num'>{media:.1f}</strong> inspeções. "
                f"Pico de atividade em <strong>{mes_pico}</strong> "
                f"com <strong class='num'>{pico}</strong> registros. "
                f"Linha pontilhada indica a média histórica do período."
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    #  BLOCO 3 — COMPLIANCE FERROVIÁRIO
    # ══════════════════════════════════════════════════════════════════
    bloco("3", "COMPLIANCE FERROVIÁRIO — RCRS", C_COMP)

    cd, ce = st.columns([1.5, 1])

    # ── RCRS por ferrovia ──
    with cd:
        st.markdown('<div class="rg-card"><div class="rg-card-title">Índice RCRS Médio por Ferrovia</div>',
                    unsafe_allow_html=True)
        if not df_riscos.empty and not df_ativos.empty:
            dm2 = df_riscos.merge(
                df_ativos[["id", "ferrovia"]].rename(columns={"id": "ativo_id"}),
                on="ativo_id", how="left",
            )
            df_f = dm2.groupby("ferrovia").agg(
                rcrs_medio=("score_rcrs", "mean"),
                n=("score_rcrs", "count"),
            ).reset_index().sort_values("rcrs_medio", ascending=True)
            cores = [
                C_BAIXO if v <= 25 else C_MEDIO if v <= 50
                else C_ALTO if v <= 75 else C_CRITICO
                for v in df_f["rcrs_medio"]
            ]
            fh = go.Figure(go.Bar(
                x=df_f["rcrs_medio"], y=df_f["ferrovia"], orientation="h",
                marker=dict(color=cores, opacity=0.85, cornerradius=6),
                text=[f"  {v:.1f}" for v in df_f["rcrs_medio"]],
                textposition="outside",
                textfont=dict(color=TEXT_SEC, size=11, family="JetBrains Mono"),
                hovertemplate="<b>%{y}</b><br>RCRS Médio: %{x:.1f}/100<extra></extra>",
            ))
            fh.add_vline(x=50, line_dash="dot", line_color=C_MEDIO, line_width=1, opacity=0.5,
                         annotation_text="Atenção", annotation_font_color=C_MEDIO,
                         annotation_font_size=10)
            fh.add_vline(x=75, line_dash="dot", line_color=C_CRITICO, line_width=1, opacity=0.6,
                         annotation_text="Crítico", annotation_font_color=C_CRITICO,
                         annotation_font_size=10)
            _pt(fh); fh.update_layout(
                height=290, showlegend=False,
                margin=dict(t=10, b=10, l=10, r=70),
                xaxis=dict(range=[0, 115], title="RCRS (0–100)"),
                yaxis=dict(showgrid=False, tickfont=dict(size=11)),
            )
            st.plotly_chart(fh, width="stretch")
            n_acima75 = len(df_f[df_f["rcrs_medio"] > 75])
            n_aten    = len(df_f[(df_f["rcrs_medio"] > 50) & (df_f["rcrs_medio"] <= 75)])
            chart_insight(
                f"<strong>{len(df_f)}</strong> ferrovias avaliadas. "
                f"<strong class='num'>{n_acima75}</strong> acima do limiar crítico (75). "
                f"<strong class='num'>{n_aten}</strong> em zona de atenção (50–75). "
                f"As linhas de referência indicam os limites regulatórios de conformidade."
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Mapa de calor por tipo ──
    with ce:
        st.markdown('<div class="rg-card"><div class="rg-card-title">Risco por Tipo de Ativo</div>',
                    unsafe_allow_html=True)
        df_a2 = db.get_all_ativos()
        if not df_riscos.empty and not df_a2.empty:
            # df_riscos já contém tipo_ativo da query JOIN — usar direto (sem merge)
            # Fallback via map (merge criaria tipo_ativo_x/_y e a coluna sumiria)
            if "tipo_ativo" in df_riscos.columns:
                dhm = df_riscos[["tipo_ativo", "nivel_risco"]].copy()
            else:
                dhm = df_riscos[["ativo_id", "nivel_risco"]].copy()
                _map_tipo = df_a2.set_index("id")["tipo_ativo"].to_dict()
                dhm["tipo_ativo"] = dhm["ativo_id"].map(_map_tipo)
            dhm = dhm.dropna(subset=["tipo_ativo", "nivel_risco"])
            if dhm.empty:
                st.markdown(f'<div style="color:{TEXT_MUT};font-size:0.82rem;padding:16px 0;text-align:center;">Dados insuficientes para o mapa de calor.</div>', unsafe_allow_html=True)
            else:
                pivot = dhm.groupby(["tipo_ativo", "nivel_risco"]).size().unstack(fill_value=0)
                for col in ["Baixo", "Médio", "Alto", "Crítico"]:
                    if col not in pivot.columns: pivot[col] = 0
                pivot = pivot[["Baixo", "Médio", "Alto", "Crítico"]]
                fhm = go.Figure(go.Heatmap(
                    z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
                    colorscale=[
                        [0, "rgba(12,184,122,0.2)"], [0.33, "rgba(244,166,42,0.5)"],
                        [0.66, "rgba(244,123,53,0.75)"], [1, "rgba(230,57,70,0.95)"],
                    ],
                    text=pivot.values, texttemplate="%{text}",
                    textfont=dict(size=14, color="white", family="Inter"),
                    showscale=False,
                    hovertemplate="<b>%{y}</b><br>Risco %{x}: %{z} inspeções<extra></extra>",
                ))
                _pt(fhm); fhm.update_layout(
                    height=270, margin=dict(t=8, b=8, l=8, r=8),
                    xaxis=dict(showgrid=False, side="top",
                               tickfont=dict(size=12, color=TEXT_SEC)),
                    yaxis=dict(showgrid=False, autorange="reversed",
                               tickfont=dict(size=11, color=TEXT_SEC)),
                )
                st.plotly_chart(fhm, width="stretch")
                tipo_mais_crit = (pivot["Crítico"].idxmax()
                                  if pivot["Crítico"].sum() > 0 else "—")
                chart_insight(
                    f"Tipo com maior concentração crítica: <strong>{tipo_mais_crit}</strong>. "
                    f"Valores mais altos (vermelho) indicam maior frequência de riscos elevados "
                    f"naquele tipo de ativo."
                )
        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    #  BLOCO 4 — AÇÕES PRIORITÁRIAS
    # ══════════════════════════════════════════════════════════════════
    bloco("4", "AÇÕES PRIORITÁRIAS — ALERTAS OPERACIONAIS", C_CRITICO)

    if df_ab.empty:
        st.markdown(f"""
        <div style="background:{CARD_BG}; border:1px solid {BORDER}; border-radius:12px;
                    padding:28px; text-align:center; color:{C_BAIXO};">
            <div style="font-size:0.95rem; font-weight:600;">Nenhum alerta operacional ativo</div>
            <div style="font-size:0.82rem; color:{TEXT_MUT}; margin-top:4px;">
                A malha ferroviária encontra-se dentro dos parâmetros de normalidade.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Mapa de ações recomendadas por tipo
        acoes_map = {
            "Compliance Crítico":     "Revisar documentação regulatória e programar inspeção técnica especializada.",
            "Integridade Estrutural": "Isolar trecho preventivamente e acionar equipe de engenharia estrutural.",
            "Falha de Fixação":       "Suspender operação no trecho afetado e realizar substituição imediata.",
            "Risco Elevado":          "Programar inspeção detalhada com ultrassom e revisão do histórico de manutenção.",
        }

        c_al1, c_al2 = st.columns(2)
        alertas_list = df_ab.head(6).to_dict("records")
        metade = (len(alertas_list) + 1) // 2

        for idx, row in enumerate(alertas_list):
            col = c_al1 if idx < metade else c_al2
            with col:
                urg  = str(row.get("nivel_urgencia", "Média"))
                tipo = str(row.get("tipo_alerta", "Alerta Operacional"))
                msg  = str(row.get("mensagem", ""))[:120]
                ativo_cod  = str(row.get("ativo_codigo", "—"))
                trecho_cod = str(row.get("trecho_codigo", "—"))
                dt_str = str(row.get("data_alerta", ""))[:16]
                acao = acoes_map.get(tipo, "Avaliar situação e acionar equipe técnica responsável.")

                # Score associado — busca segura evitando KeyError
                score_lbl = "Risco"
                score_val = "—/100"
                if not df_riscos.empty and ativo_cod != "—" and "ativo_codigo" in df_riscos.columns:
                    try:
                        rr = df_riscos[df_riscos["ativo_codigo"] == ativo_cod]
                        if not rr.empty:
                            sr = rr.iloc[0]
                            score_lbl = "RCRS"
                            score_val = f"{float(sr.get('score_rcrs', 0)):.0f}/100"
                    except Exception:
                        pass

                alert_card_v3(tipo, urg, msg, ativo_cod, trecho_cod,
                              score_lbl, score_val, dt_str, acao)

        if len(df_ab) > 6:
            st.markdown(f"""
            <div style="text-align:center; padding:12px; font-size:0.8rem; color:{TEXT_MUT};">
                Exibindo 6 de {len(df_ab)} alertas abertos.
                Acesse a tela de <strong style="color:{ACCENT2};">Auditoria</strong> para ver todos.
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE — TRECHOS
# ═══════════════════════════════════════════════════════════════════════════

def page_trechos():
    ph("Trechos Ferroviários",
       "Cadastro, monitoramento e análise dos trechos da malha ferroviária")
    tab1, tab2 = st.tabs(["Trechos Cadastrados", "Cadastrar Novo Trecho"])

    # Aba em função: o `return` de banco vazio não pode impedir a aba de cadastro
    def _aba_lista():
        df = db.get_all_trechos()
        if df.empty: info("Nenhum trecho cadastrado ainda."); return

        c1, c2, c3, c4 = st.columns(4)
        for col, crit, cor in zip([c1, c2, c3, c4],
                                   ["Crítica", "Alta", "Média", "Baixa"],
                                   [C_CRITICO, C_ALTO, C_MEDIO, C_BAIXO]):
            qtd = len(df[df["criticidade_operacional"] == crit])
            col.markdown(f"""
            <div style="background:{CARD_BG};border:1px solid {BORDER};
                        border-top:3px solid {cor};border-radius:12px;
                        padding:18px;text-align:center;">
                <div style="font-size:1.8rem;font-weight:900;color:{cor};line-height:1;">{qtd}</div>
                <div style="font-size:0.73rem;color:{TEXT_MUT};text-transform:uppercase;
                            letter-spacing:0.08em;margin-top:6px;font-weight:600;">{crit}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        df["extensao_km"] = df["km_final"] - df["km_inicial"]

        cg1, cg2 = st.columns(2)
        with cg1:
            cnt = df["criticidade_operacional"].value_counts().reset_index()
            cnt.columns = ["Criticidade", "Qtd"]
            fc = go.Figure(go.Bar(
                x=cnt["Criticidade"], y=cnt["Qtd"],
                marker=dict(color=[C_BAIXO, C_MEDIO, C_ALTO, C_CRITICO][:len(cnt)],
                            cornerradius=7),
                text=cnt["Qtd"], textposition="outside",
                textfont=dict(color=TEXT_SEC, size=13),
            ))
            _pt(fc); fc.update_layout(title="Trechos por Criticidade", height=260,
                                       showlegend=False, margin=dict(t=40, b=10))
            st.plotly_chart(fc, width="stretch")

        with cg2:
            de = (df.groupby("ferrovia")["extensao_km"].sum()
                  .reset_index().sort_values("extensao_km", ascending=True))
            fe = go.Figure(go.Bar(
                x=de["extensao_km"], y=de["ferrovia"], orientation="h",
                marker=dict(color=ACCENT2, opacity=0.8, cornerradius=6),
                text=[f" {v:.1f} km" for v in de["extensao_km"]],
                textposition="outside", textfont=dict(color=TEXT_SEC, size=11),
            ))
            _pt(fe); fe.update_layout(title="Extensão Monitorada por Ferrovia (km)",
                                       height=260, showlegend=False,
                                       margin=dict(t=40, b=10, r=90))
            st.plotly_chart(fe, width="stretch")

        sdiv("TABELA DETALHADA DE TRECHOS")
        st.dataframe(df, width="stretch", hide_index=True)

    with tab1:
        _aba_lista()

    with tab2:
        with st.form("form_trecho"):
            st.markdown(f'<div class="rg-card-title">Dados do Trecho</div>',
                        unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            codigo   = c1.text_input("Código do Trecho *", placeholder="Ex.: TRC-009")
            ferrovia = c2.selectbox("Ferrovia *", m.FERROVIAS)
            c3, c4 = st.columns(2)
            km_ini = c3.number_input("Km Inicial *", min_value=0.0, step=0.5)
            km_fin = c4.number_input("Km Final *",   min_value=0.0, step=0.5, value=10.0)
            c5, c6, c7 = st.columns(3)
            estado      = c5.selectbox("Estado *",               m.ESTADOS)
            tipo_via    = c6.selectbox("Tipo de Via *",           m.TIPOS_VIA)
            criticidade = c7.selectbox("Criticidade Operacional *", m.CRITICIDADE_OPERACIONAL)
            st.markdown(f'<div class="rg-card-title" style="margin-top:16px;">Parâmetros Operacionais (opcional)</div>',
                        unsafe_allow_html=True)
            c8, c9, c10 = st.columns(3)
            vel_max = c8.number_input("Velocidade Máxima (km/h)", min_value=0.0,
                                      step=5.0, value=None)
            carga_eixo = c9.number_input("Carga Máxima por Eixo (t)", min_value=0.0,
                                         step=0.5, value=None)
            trens_dia = c10.number_input("Trens por Dia", min_value=0,
                                         step=1, value=None)
            obs = st.text_area("Observações Técnicas",
                               placeholder="Descreva características relevantes do trecho…")
            sub = st.form_submit_button("Cadastrar Trecho", type="primary")

        if sub:
            if not codigo: danger("Informe o código do trecho.")
            elif km_fin <= km_ini: danger("Km Final deve ser maior que Km Inicial.")
            else:
                try:
                    tid = db.insert_trecho(codigo, ferrovia, km_ini, km_fin,
                                           estado, tipo_via, criticidade, obs,
                                           velocidade_max_kmh=vel_max,
                                           carga_max_eixo_ton=carga_eixo,
                                           trens_por_dia=trens_dia)
                    db.insert_auditoria("INSERÇÃO", "Usuário", f"Trecho {codigo}",
                                        "Cadastrado via interface.")
                    flash(f"Trecho <b>{codigo}</b> cadastrado com sucesso (ID: {tid}).")
                    st.rerun()
                except Exception as e:
                    danger(f"Erro ao cadastrar: {e}")


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE — ATIVOS
# ═══════════════════════════════════════════════════════════════════════════

def page_ativos():
    ph("Ativos Monitorados",
       "Gestão de ativos de infraestrutura ferroviária — trilhos, dormentes, pontes, AMVs e sinalização")
    tab1, tab2 = st.tabs(["Ativos Monitorados", "Cadastrar Novo Ativo"])

    # Aba em função: o `return` de banco vazio não pode impedir a aba de cadastro
    def _aba_lista():
        df = db.get_all_ativos()
        if df.empty: info("Nenhum ativo cadastrado."); return

        c1, c2, c3 = st.columns(3)
        tf = c1.multiselect("Filtrar por Tipo",     m.TIPOS_ATIVO)
        cf = c2.multiselect("Filtrar por Condição", m.CONDICAO_VISUAL)
        bf = c3.text_input("Buscar por código ou ferrovia")

        df2 = df.copy()
        if tf: df2 = df2[df2["tipo_ativo"].isin(tf)]
        if cf: df2 = df2[df2["condicao_visual"].isin(cf)]
        if bf:
            mask = (df2["codigo"].str.contains(bf, case=False, na=False) |
                    df2["ferrovia"].str.contains(bf, case=False, na=False))
            df2 = df2[mask]

        cg1, cg2, cg3 = st.columns(3)
        with cg1:
            cnt = df["tipo_ativo"].value_counts().reset_index()
            cnt.columns = ["Tipo", "Qtd"]
            fp = go.Figure(go.Pie(
                labels=cnt["Tipo"], values=cnt["Qtd"], hole=0.55,
                marker=dict(line=dict(color=PRIMARY, width=2)),
                textfont=dict(size=10, family="Inter"),
                hovertemplate="<b>%{label}</b>: %{value}<extra></extra>",
            ))
            _pt(fp); fp.update_layout(title="Tipos de Ativo", height=240,
                                       legend=dict(font=dict(size=10)),
                                       margin=dict(t=36, b=0))
            st.plotly_chart(fp, width="stretch")

        with cg2:
            cnt2 = df["condicao_visual"].value_counts().reset_index()
            cnt2.columns = ["Condição", "Qtd"]
            cor_map = dict(zip(["Ótimo", "Bom", "Regular", "Ruim", "Crítico"],
                               [C_BAIXO, "#3498DB", C_MEDIO, C_ALTO, C_CRITICO]))
            fc2 = go.Figure(go.Bar(
                x=cnt2["Condição"], y=cnt2["Qtd"],
                marker=dict(color=[cor_map.get(c, TEXT_SEC) for c in cnt2["Condição"]],
                            cornerradius=7),
                text=cnt2["Qtd"], textposition="outside",
                textfont=dict(color=TEXT_SEC, size=13),
            ))
            _pt(fc2); fc2.update_layout(title="Condição Visual", height=240,
                                         showlegend=False, margin=dict(t=36, b=10))
            st.plotly_chart(fc2, width="stretch")

        with cg3:
            di = (df.groupby("tipo_ativo")["idade_anos"].mean()
                  .reset_index().sort_values("idade_anos", ascending=True))
            fi = go.Figure(go.Bar(
                x=di["idade_anos"], y=di["tipo_ativo"], orientation="h",
                marker=dict(color=di["idade_anos"],
                            colorscale=[[0, C_BAIXO], [0.5, C_MEDIO], [1, C_CRITICO]],
                            cornerradius=6),
                text=[f" {v:.1f} a" for v in di["idade_anos"]],
                textposition="outside", textfont=dict(color=TEXT_SEC, size=11),
            ))
            _pt(fi); fi.update_layout(title="Idade Média por Tipo (anos)", height=240,
                                       showlegend=False,
                                       margin=dict(t=36, b=10, r=60))
            st.plotly_chart(fi, width="stretch")

        sdiv("LISTA DE ATIVOS MONITORADOS")
        st.markdown(f'<div style="font-size:0.79rem;color:{TEXT_MUT};margin-bottom:8px;">'
                    f'Exibindo {len(df2)} de {len(df)} ativos</div>', unsafe_allow_html=True)
        st.dataframe(df2, width="stretch", hide_index=True)

    with tab1:
        _aba_lista()

    with tab2:
        df_t = db.get_all_trechos()
        if df_t.empty: warn("Cadastre ao menos um trecho antes de adicionar ativos."); return

        opts = {f"{r['codigo']} — {r['ferrovia']}": r["id"] for _, r in df_t.iterrows()}
        with st.form("form_ativo"):
            st.markdown(f'<div class="rg-card-title">Identificação do Ativo</div>',
                        unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            codigo     = c1.text_input("Código do Ativo *", placeholder="Ex.: ATI-023")
            tipo_ativo = c2.selectbox("Tipo de Ativo *", m.TIPOS_ATIVO)
            tsel = st.selectbox("Trecho Associado *", list(opts.keys()))
            c3, c4 = st.columns(2)
            idade   = c3.number_input("Idade do Ativo (anos) *", min_value=0.0, step=0.5)
            data_m  = c4.date_input("Data Última Manutenção *",
                                    value=date.today() - timedelta(days=90))
            c5, c6 = st.columns(2)
            condicao = c5.selectbox("Condição Visual *", m.CONDICAO_VISUAL)
            km_pos   = c6.number_input("Posição na Malha (km)", min_value=0.0,
                                       step=0.001, format="%.3f", value=None,
                                       help="Ex.: 7.200 = Km 7+200. Usado na detecção de zonas críticas.")
            obs = st.text_area("Observações Técnicas",
                               placeholder="Descreva o estado atual do ativo…")
            sub = st.form_submit_button("Cadastrar Ativo", type="primary")

        if sub:
            if not codigo: danger("Informe o código do ativo.")
            else:
                try:
                    aid = db.insert_ativo(codigo, tipo_ativo, opts[tsel],
                                          idade, str(data_m), condicao, obs, km_pos)
                    db.insert_auditoria("INSERÇÃO", "Usuário", f"Ativo {codigo}",
                                        "Cadastrado via interface.")
                    flash(f"Ativo <b>{codigo}</b> cadastrado com sucesso (ID: {aid}).")
                    st.rerun()
                except Exception as e: danger(f"Erro: {e}")


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE — INSPEÇÕES
# ═══════════════════════════════════════════════════════════════════════════

def page_inspecoes():
    ph("Inspeções Técnicas",
       "Registro de inspeções de campo com cálculo automático de risco e conformidade")
    tab1, tab2 = st.tabs(["Inspeções Registradas", "Registrar Nova Inspeção"])

    # Aba em função: o `return` de banco vazio não pode impedir a aba de registro
    def _aba_lista():
        df = db.get_all_inspecoes()
        if df.empty: info("Nenhuma inspeção registrada ainda."); return

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de Inspeções",   len(df))
        c2.metric("Métodos Utilizados",   df["tipo_inspecao"].nunique())
        c3.metric("Ativos Inspecionados", df["ativo_id"].nunique())
        c4.metric("Com Fissura Detectada", int(df["fissura"].sum()))

        cg1, cg2 = st.columns(2)
        with cg1:
            cnt = df["tipo_inspecao"].value_counts().reset_index()
            cnt.columns = ["Tipo", "Qtd"]
            ft = go.Figure(go.Bar(
                x=cnt["Tipo"], y=cnt["Qtd"],
                marker=dict(color=ACCENT2, opacity=0.85, cornerradius=7),
                text=cnt["Qtd"], textposition="outside",
                textfont=dict(color=TEXT_SEC, size=12),
            ))
            _pt(ft); ft.update_layout(title="Inspeções por Método", height=240,
                                       showlegend=False, margin=dict(t=40, b=10))
            st.plotly_chart(ft, width="stretch")

        with cg2:
            am = df.copy()
            am["data_inspecao"] = pd.to_datetime(am["data_inspecao"])
            am["mes"] = am["data_inspecao"].dt.to_period("M").astype(str)
            cm = am.groupby("mes").size().reset_index(name="total").tail(10)
            fm = go.Figure(go.Bar(
                x=cm["mes"], y=cm["total"],
                marker=dict(color=cm["total"],
                            colorscale=[[0, ACCENT2], [1, C_CRITICO]],
                            cornerradius=7),
                text=cm["total"], textposition="outside",
                textfont=dict(color=TEXT_SEC, size=11),
            ))
            _pt(fm); fm.update_layout(title="Inspeções por Mês", height=240,
                                       showlegend=False, margin=dict(t=40, b=10))
            st.plotly_chart(fm, width="stretch")

        tf2 = st.multiselect("Filtrar por Método de Inspeção", m.TIPOS_INSPECAO)
        df3 = df if not tf2 else df[df["tipo_inspecao"].isin(tf2)]
        cols_e = [c for c in ["data_inspecao", "ativo_codigo", "tipo_ativo", "tipo_inspecao",
                               "responsavel", "fissura", "desgaste", "corrosao",
                               "falha_fixacao", "nivel_vibracao", "temperatura",
                               "probabilidade_risco", "consequencia_risco",
                               "score_matriz", "nivel_matriz"] if c in df3.columns]
        sdiv("REGISTROS DE INSPEÇÃO")
        st.dataframe(df3[cols_e], width="stretch", hide_index=True)

    with tab1:
        _aba_lista()

    with tab2:
        df_a = db.get_all_ativos()
        if df_a.empty: warn("Cadastre ao menos um ativo antes de registrar inspeções."); return

        opts = {f"{r['codigo']} — {r['tipo_ativo']} ({r['trecho_codigo']})": r["id"]
                for _, r in df_a.iterrows()}

        with st.form("form_insp"):
            st.markdown(f'<div class="rg-card-title">Identificação da Inspeção</div>',
                        unsafe_allow_html=True)
            asel = st.selectbox("Ativo Inspecionado *", list(opts.keys()))
            c1, c2, c3 = st.columns(3)
            data_i = c1.date_input("Data da Inspeção *", value=date.today())
            resp   = c2.text_input("Responsável Técnico *", placeholder="Eng. Nome Sobrenome")
            tipo_i = c3.selectbox("Método de Inspeção *", m.TIPOS_INSPECAO)

            st.markdown(f'<div class="rg-card-title" style="margin-top:16px;">Anomalias Identificadas</div>',
                        unsafe_allow_html=True)
            c4, c5, c6, c7 = st.columns(4)
            fiss = c4.checkbox("Fissura Estrutural")
            desg = c5.checkbox("Desgaste")
            corr = c6.checkbox("Corrosão")
            falh = c7.checkbox("Falha de Fixação")

            st.markdown(f'<div class="rg-card-title" style="margin-top:16px;">Parâmetros Medidos</div>',
                        unsafe_allow_html=True)
            c8, c9, c10 = st.columns(3)
            vibr = c8.slider("Nível de Vibração (0–10)", 0.0, 10.0, 2.0, 0.1)
            temp = c9.number_input("Temperatura (°C)", min_value=-10.0,
                                    max_value=80.0, value=25.0, step=0.5)
            carg = c10.slider("Carga Operacional (%)", 0.0, 100.0, 50.0, 1.0)

            st.markdown(f'<div class="rg-card-title" style="margin-top:16px;">Matriz P×C — ISO 31000 (opcional)</div>',
                        unsafe_allow_html=True)
            c11, c12 = st.columns(2)
            prob = c11.selectbox("Probabilidade (P)", [None, 1, 2, 3, 4, 5],
                                 format_func=lambda v: "Não avaliada" if v is None
                                 else f"{v} — {m.PROBABILIDADE_ESCALA[v]}")
            cons = c12.selectbox("Consequência (C)", [None, 1, 2, 3, 4, 5],
                                 format_func=lambda v: "Não avaliada" if v is None
                                 else f"{v} — {m.CONSEQUENCIA_ESCALA[v]}")

            obs  = st.text_area("Observações Técnicas")
            img  = st.file_uploader("Evidência Fotográfica (opcional)",
                                    type=["jpg", "jpeg", "png"])
            sub  = st.form_submit_button("Registrar Inspeção", type="primary")

        if sub:
            if not resp: danger("Informe o responsável técnico.")
            elif (prob is None) != (cons is None):
                danger("Para usar a Matriz P×C informe Probabilidade e Consequência, ou deixe ambas em branco.")
            else:
                try:
                    aid2   = opts[asel]
                    ipath  = None
                    if img:
                        sd = os.path.join(os.path.dirname(__file__), "data", "imagens")
                        os.makedirs(sd, exist_ok=True)
                        nome = f"{datetime.now():%Y%m%d%H%M%S}_{os.path.basename(img.name)}"
                        ipath = os.path.join(sd, nome)
                        with open(ipath, "wb") as f: f.write(img.read())

                    iid = db.insert_inspecao(aid2, str(data_i), resp, tipo_i,
                                              fiss, desg, corr, falh,
                                              vibr, temp, carg, obs, ipath,
                                              probabilidade_risco=prob,
                                              consequencia_risco=cons)
                    ad = db.get_ativo_by_id(aid2)
                    td = db.get_trecho_by_id(ad["trecho_id"])
                    try:
                        dias_m = (date.today() -
                                  pd.to_datetime(ad["data_ultima_manutencao"]).date()).days
                    except: dias_m = 365

                    sc, nv, cont = re_.calcular_risco_operacional(
                        float(ad["idade_anos"]), dias_m,
                        td["criticidade_operacional"],
                        fiss, desg, corr, falh, vibr, carg, ad["condicao_visual"])
                    hist = int(fiss) + int(desg) + int(corr)
                    rc, clrc, rec = re_.calcular_rcrs(sc, td["criticidade_operacional"],
                                                       hist, sc * 0.75, sc * 0.5, 80.0)
                    db.insert_risco(iid, aid2, sc, nv, rc, clrc, rec)

                    if nv in ("Alto", "Crítico"):
                        db.insert_alerta(aid2, td["id"], "Risco Elevado",
                            "Urgente" if nv == "Crítico" else "Alta",
                            f"Risco {nv} (score {sc:.0f}/100) detectado em {ad['codigo']}.")

                    db.insert_auditoria("INSERÇÃO", resp,
                                        f"Inspeção {ad['codigo']}",
                                        f"Score:{sc:.0f} RCRS:{rc:.0f}")

                    cor_nv = RISK_C.get(nv, TEXT_SEC)
                    if prob is not None:
                        sc_pc, nv_pc = re_.calcular_risco_matriz(prob, cons)
                        cor_pc = m.MATRIZ_CORES.get(nv_pc, TEXT_SEC)
                        # Sem quebra de linha inicial: uma linha em branco encerraria o bloco HTML do Markdown
                        bloco_pc = (f'<div style="font-size:1.5rem;font-weight:800;color:{cor_pc};">{nv_pc}</div>'
                                    f'<div style="font-size:0.8rem;color:{TEXT_SEC};">P={prob} × C={cons} = {sc_pc}/25</div>')
                    else:
                        bloco_pc = (f'<div style="font-size:1.5rem;font-weight:800;color:{TEXT_MUT};">—</div>'
                                    f'<div style="font-size:0.8rem;color:{TEXT_SEC};">Não avaliada</div>')
                    flash(f"""
                    <div style="background:{CARD_BG};border:1px solid {cor_nv}55;
                                border-radius:14px;padding:22px;margin-bottom:18px;">
                        <div style="font-size:1rem;font-weight:700;color:{cor_nv};margin-bottom:14px;">
                            Inspeção registrada com sucesso — {ad['codigo']}
                        </div>
                        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:18px;">
                            <div>
                                <div style="font-size:0.68rem;color:{TEXT_MUT};text-transform:uppercase;
                                            letter-spacing:0.08em;">Risco Operacional</div>
                                <div style="font-size:1.5rem;font-weight:800;color:{cor_nv};">{nv}</div>
                                <div style="font-size:0.8rem;color:{TEXT_SEC};">Score: {sc:.0f}/100</div>
                            </div>
                            <div>
                                <div style="font-size:0.68rem;color:{TEXT_MUT};text-transform:uppercase;
                                            letter-spacing:0.08em;">RCRS</div>
                                <div style="font-size:1.5rem;font-weight:800;color:{TEXT_PRI};">{rc:.0f}/100</div>
                                <div style="font-size:0.8rem;color:{TEXT_SEC};">{clrc}</div>
                            </div>
                            <div>
                                <div style="font-size:0.68rem;color:{TEXT_MUT};text-transform:uppercase;
                                            letter-spacing:0.08em;">Matriz P×C</div>
                                {bloco_pc}
                            </div>
                            <div>
                                <div style="font-size:0.68rem;color:{TEXT_MUT};text-transform:uppercase;
                                            letter-spacing:0.08em;">ID do Registro</div>
                                <div style="font-size:1.5rem;font-weight:800;color:{ACCENT2};">#{iid}</div>
                                <div style="font-size:0.8rem;color:{TEXT_SEC};">{str(data_i)}</div>
                            </div>
                        </div>
                        <div style="margin-top:14px;font-size:0.82rem;color:{TEXT_SEC};
                                    border-top:1px solid {BORDER};padding-top:12px;line-height:1.7;">
                            <strong style="color:{TEXT_PRI};">Recomendação:</strong> {rec}
                        </div>
                    </div>
                    """, kind="html")
                    st.rerun()
                except Exception as e: danger(f"Erro ao registrar: {e}")


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE — MODELO PREDITIVO
# ═══════════════════════════════════════════════════════════════════════════

def page_ml():
    ph("Modelo Preditivo de Risco",
       "RandomForestClassifier — previsão de nível de risco operacional por ativo ferroviário")

    if "modelo_rf" not in st.session_state:
        with st.spinner("Treinando modelo preditivo com os dados do sistema…"):
            dfi   = db.get_all_inspecoes()
            dfa   = db.get_all_ativos()
            dft   = db.get_all_trechos()
            X, y  = (ml.preparar_features_reais(dfi, dfa, dft)
                     if not dfi.empty and not dfa.empty else (None, None))
            if X is None or len(X) < 20:
                X, y = ml.gerar_dados_sinteticos(700)
                st.session_state["fonte_ml"] = "Dados Sintéticos"
            else:
                Xs, ys = ml.gerar_dados_sinteticos(400)
                X = pd.concat([X, Xs], ignore_index=True)
                y = pd.concat([y, ys], ignore_index=True)
                st.session_state["fonte_ml"] = "Reais + Sintéticos"
            mod, acc, Xt, yt, rep = ml.treinar_modelo(X, y)
            st.session_state.update({"modelo_rf": mod, "ml_acc": acc, "ml_report": rep})

    mod   = st.session_state["modelo_rf"]
    acc   = st.session_state["ml_acc"]
    rep   = st.session_state["ml_report"]
    fonte = st.session_state.get("fonte_ml", "Sintéticos")

    t1, t2, t3 = st.tabs(
        ["Desempenho do Modelo", "Importância de Variáveis", "Simulação de Predição"]
    )

    with t1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Acurácia Global",  f"{acc:.1%}")
        c2.metric("Algoritmo",        "Random Forest")
        c3.metric("Estimadores",      "150 árvores")
        c4.metric("Base de Dados",    fonte)

        cr, ci = st.columns([1.2, 1])
        with cr:
            st.markdown('<div class="rg-card"><div class="rg-card-title">Relatório por Classe</div>',
                        unsafe_allow_html=True)
            st.code(rep, language="text")
            st.markdown("</div>", unsafe_allow_html=True)
        with ci:
            st.markdown('<div class="rg-card"><div class="rg-card-title">Parâmetros do Modelo</div>',
                        unsafe_allow_html=True)
            for l, v in [("Estimadores", "150"), ("Profundidade Máx.", "12"),
                         ("Min. Amostras Folha", "3"), ("Balanceamento", "balanced"),
                         ("Features", "10"), ("Classes", "4 (Baixo→Crítico)"),
                         ("Split", "80% treino / 20% teste")]:
                st.markdown(row_kv(l, v), unsafe_allow_html=True)
            st.markdown(f"""
            <div class="info-box" style="margin-top:14px;">
                <b>Roadmap v0.7:</b> Integração com SHAP para explicabilidade
                baseada em valores de Shapley.
                Use <code>shap.TreeExplainer(model)</code> em <code>ml_model.py</code>.
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            if st.button("Retreinar Modelo", type="secondary"):
                del st.session_state["modelo_rf"]
                st.rerun()

    with t2:
        fi = ml.get_feature_importance(mod)
        ff = go.Figure(go.Bar(
            x=fi["Importância"], y=fi["Variável"], orientation="h",
            marker=dict(color=fi["Importância"],
                        colorscale=[[0, ACCENT2], [0.5, C_MEDIO], [1, C_CRITICO]],
                        opacity=0.9, cornerradius=6),
            text=[f"  {v:.4f}" for v in fi["Importância"]],
            textposition="outside",
            textfont=dict(color=TEXT_SEC, size=11, family="JetBrains Mono"),
            hovertemplate="<b>%{y}</b><br>Importância: %{x:.4f}<extra></extra>",
        ))
        _pt(ff); ff.update_layout(
            height=430, showlegend=False,
            margin=dict(t=10, b=10, l=10, r=90),
            xaxis=dict(title="Importância (Gini)", showgrid=True),
            yaxis=dict(showgrid=False, autorange="reversed",
                       tickfont=dict(size=12)),
        )
        ff.add_vline(x=fi["Importância"].mean(), line_dash="dot",
                     line_color=TEXT_MUT, line_width=1.5,
                     annotation_text="Média", annotation_font_color=TEXT_MUT,
                     annotation_font_size=10)
        st.plotly_chart(ff, width="stretch")
        top1 = fi.iloc[0]["Variável"]; top2 = fi.iloc[1]["Variável"]
        chart_insight(
            f"As variáveis mais determinantes para a classificação de risco são "
            f"<strong>{top1}</strong> e <strong>{top2}</strong>. "
            f"Barras mais longas indicam maior contribuição na separação entre as classes "
            f"(Baixo / Médio / Alto / Crítico). A linha pontilhada indica a importância média."
        )

    with t3:
        st.markdown('<div class="rg-card"><div class="rg-card-title">Parâmetros da Simulação</div>',
                    unsafe_allow_html=True)
        with st.form("form_pred"):
            c1, c2 = st.columns(2)
            pi  = c1.slider("Idade do ativo (anos)", 0.0, 30.0, 10.0, 0.5)
            pm  = c2.slider("Dias sem manutenção",   0,   730,  200,  5)
            c3, c4 = st.columns(2)
            pc  = c3.selectbox("Criticidade operacional", list(m.CRITICIDADE_PESO.keys()))
            pco = c4.selectbox("Condição visual",         list(m.CONDICAO_PESO.keys()))
            c5, c6, c7, c8 = st.columns(4)
            pf  = c5.checkbox("Fissura Estrutural")
            pd_ = c6.checkbox("Desgaste")
            prr = c7.checkbox("Corrosão")
            pfx = c8.checkbox("Falha de Fixação")
            c9, c10 = st.columns(2)
            pv  = c9.slider("Nível de Vibração (0–10)", 0.0, 10.0, 3.0, 0.1)
            pcg = c10.slider("Carga Operacional (%)",   0.0, 100.0, 50.0, 1.0)
            subp = st.form_submit_button("Executar Predição", type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

        if subp:
            params = {
                "idade_anos": pi, "dias_desde_manutencao": pm,
                "criticidade_operacional": m.CRITICIDADE_PESO[pc],
                "fissura": int(pf), "desgaste": int(pd_), "corrosao": int(prr),
                "falha_fixacao": int(pfx), "nivel_vibracao": pv,
                "carga_operacional": pcg, "condicao_visual": m.CONDICAO_PESO[pco],
            }
            npred, probs = ml.prever_risco(mod, params)
            sm, nm, cont = re_.calcular_risco_operacional(
                pi, pm, pc, pf, pd_, prr, pfx, pv, pcg, pco)
            cor_np = RISK_C.get(npred, TEXT_SEC)

            cg, cp, cx = st.columns([1, 1.2, 1.4])
            with cg:
                st.plotly_chart(gauge_risco(sm, nm), width="stretch")
            with cp:
                labels = ["Baixo", "Médio", "Alto", "Crítico"]
                cores_p = [C_BAIXO, C_MEDIO, C_ALTO, C_CRITICO]
                fp2 = go.Figure(go.Bar(
                    x=labels, y=probs * 100,
                    marker=dict(color=cores_p, opacity=0.88, cornerradius=7),
                    text=[f"{v * 100:.1f}%" for v in probs],
                    textposition="outside",
                    textfont=dict(color=TEXT_SEC, size=11),
                ))
                _pt(fp2); fp2.update_layout(
                    title="Probabilidade por Classe",
                    height=250, showlegend=False,
                    margin=dict(t=40, b=10),
                    yaxis=dict(range=[0, 118]),
                )
                st.plotly_chart(fp2, width="stretch")
                st.markdown(f"""
                <div style="text-align:center;margin-top:-6px;">
                    <div style="font-size:0.68rem;color:{TEXT_MUT};text-transform:uppercase;
                                letter-spacing:0.1em;">Predição do Modelo</div>
                    <div style="font-size:1.7rem;font-weight:800;color:{cor_np};">{npred}</div>
                    <div style="font-size:0.8rem;color:{TEXT_SEC};">
                        Confiança: {max(probs)*100:.1f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with cx:
                ext = re_.gerar_explicabilidade(
                    sm, nm, cont, pf, pd_, prr, pfx, pv, pi, pm, pc, pco)
                st.markdown('<div class="rg-card"><div class="rg-card-title">Explicabilidade</div>',
                            unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:0.83rem;color:{TEXT_SEC};line-height:1.7;">{ext}</div>',
                            unsafe_allow_html=True)
                label_map = {
                    "fissura": "Fissura", "desgaste": "Desgaste", "corrosao": "Corrosão",
                    "falha_fixacao": "Falha Fixação", "vibracao": "Vibração",
                    "criticidade": "Criticidade", "manutencao": "Manutenção",
                    "idade": "Idade", "condicao_visual": "Condição Visual",
                }
                for fator, pts in sorted(cont.items(), key=lambda x: x[1], reverse=True)[:6]:
                    if pts > 0.3:
                        pct = min(pts / 15.0 * 100, 100)
                        cb2 = C_CRITICO if pct > 70 else C_ALTO if pct > 40 else C_MEDIO
                        lbl = label_map.get(fator, fator)
                        st.markdown(f"""
                        <div style="margin-bottom:9px;">
                            <div style="display:flex;justify-content:space-between;
                                        font-size:0.75rem;color:{TEXT_MUT};margin-bottom:4px;">
                                <span>{lbl}</span>
                                <span style="color:{cb2};font-family:'JetBrains Mono',monospace;">
                                    {pts:.1f} pts
                                </span>
                            </div>
                            <div style="height:6px;background:{BORDER};border-radius:3px;overflow:hidden;">
                                <div style="height:100%;width:{pct:.0f}%;background:{cb2};border-radius:3px;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE — COMPLIANCE
# ═══════════════════════════════════════════════════════════════════════════

def page_compliance():
    ph("Compliance & RCRS",
       "Índice de conformidade regulatória e risco sistêmico — Railway Compliance Risk Score")
    t1, t2 = st.tabs(["Visão Geral de Conformidade", "Calculadora RCRS"])

    # Aba em função: o `return` de banco vazio não pode esconder a calculadora
    def _aba_visao_geral():
        df_r = db.get_all_riscos()
        if df_r.empty: info("Nenhum score RCRS calculado ainda."); return

        clc = df_r["classificacao_rcrs"].value_counts()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Conformes",         clc.get("Conforme", 0))
        c2.metric("Em Atenção",        clc.get("Atenção", 0))
        c3.metric("Não Conformidades", clc.get("Não conformidade potencial", 0))
        c4.metric("Situação Crítica",  clc.get("Crítico", 0))

        ca, cb = st.columns([1, 1.6])
        with ca:
            cnt  = df_r["classificacao_rcrs"].value_counts().reset_index()
            cnt.columns = ["Classificação", "Qtd"]
            cors = [m.RCRS_COLORS.get(c, TEXT_SEC) for c in cnt["Classificação"]]
            frc  = go.Figure(go.Pie(
                labels=cnt["Classificação"], values=cnt["Qtd"], hole=0.60,
                marker=dict(colors=cors, line=dict(color=PRIMARY, width=3)),
                textfont=dict(size=10, family="Inter"),
                hovertemplate="<b>%{label}</b>: %{value}<br>%{percent}<extra></extra>",
            ))
            frc.add_annotation(
                text=f"<b>{int(cnt['Qtd'].sum())}</b><br>"
                     f"<span style='font-size:9px;color:{TEXT_MUT}'>AVALIAÇÕES</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=17, color=TEXT_PRI, family="Inter"),
            )
            _pt(frc); frc.update_layout(height=300, showlegend=True,
                legend=dict(font=dict(size=10), orientation="v"),
                margin=dict(t=10, b=10, l=0, r=80))
            st.plotly_chart(frc, width="stretch")
            n_nc = clc.get("Não conformidade potencial", 0) + clc.get("Crítico", 0)
            chart_insight(
                f"<strong>{n_nc}</strong> ativos com não conformidade potencial ou crítica. "
                f"<strong>{clc.get('Conforme', 0)}</strong> dentro dos parâmetros regulatórios. "
                f"Priorizar revisão dos ativos classificados como 'Não conformidade potencial'."
            )

        with cb:
            dsc = df_r[["ativo_codigo", "tipo_ativo", "score_risco",
                         "score_rcrs", "nivel_risco", "classificacao_rcrs"]
                       ].dropna(subset=["score_risco", "score_rcrs"])
            cores_sc = [RISK_C.get(n, TEXT_SEC) for n in dsc["nivel_risco"]]
            fsc = go.Figure(go.Scatter(
                x=dsc["score_risco"], y=dsc["score_rcrs"],
                mode="markers+text", text=dsc["ativo_codigo"],
                textposition="top center",
                textfont=dict(size=9, color=TEXT_MUT, family="JetBrains Mono"),
                marker=dict(color=cores_sc, size=11, opacity=0.85,
                            line=dict(color=PRIMARY, width=1.5)),
                hovertemplate="<b>%{text}</b><br>Risco: %{x:.1f}<br>RCRS: %{y:.1f}<extra></extra>",
            ))
            for v in [25, 50, 75]:
                fsc.add_vline(x=v, line_dash="dot", line_color=BORDER, line_width=1)
                fsc.add_hline(y=v, line_dash="dot", line_color=BORDER, line_width=1)
            _pt(fsc); fsc.update_layout(
                title="Dispersão: Risco Operacional × RCRS por Ativo",
                height=300, margin=dict(t=40, b=10),
                xaxis=dict(title="Risco Operacional (0–100)", range=[0, 115]),
                yaxis=dict(title="RCRS (0–100)", range=[0, 115]),
            )
            st.plotly_chart(fsc, width="stretch")
            chart_insight(
                "Cada ponto representa um ativo. Pontos no quadrante superior direito "
                "(alto risco e alto RCRS) são prioridade máxima de intervenção. "
                "As linhas pontilhadas delimitam os quadrantes de conformidade."
            )

        sdiv("ATIVOS COM CONFORMIDADE CRÍTICA OU POTENCIAL")
        crit_df = df_r[df_r["classificacao_rcrs"].isin(
            ["Crítico", "Não conformidade potencial"])].head(8)
        for _, row in crit_df.iterrows():
            cor = C_CRITICO if row["classificacao_rcrs"] == "Crítico" else C_ALTO
            r, g, b = int(cor[1:3], 16), int(cor[3:5], 16), int(cor[5:7], 16)
            st.markdown(f"""
            <div style="background:{CARD_BG};border:1px solid rgba({r},{g},{b},0.4);
                        border-left:4px solid {cor};border-radius:12px;
                        padding:16px 20px;margin-bottom:10px;
                        display:flex;align-items:center;gap:18px;">
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.87rem;
                            color:{ACCENT2};width:92px;flex-shrink:0;font-weight:600;">
                    {row.get('ativo_codigo','—')}
                </div>
                <div style="flex:1;">
                    <div style="font-size:0.84rem;font-weight:700;color:{TEXT_PRI};margin-bottom:3px;">
                        {row['classificacao_rcrs']}
                    </div>
                    <div style="font-size:0.77rem;color:{TEXT_SEC};line-height:1.5;">
                        {str(row.get('recomendacao',''))[:130]}…
                    </div>
                </div>
                <div style="text-align:right;flex-shrink:0;">
                    <div style="font-size:1.5rem;font-weight:900;color:{cor};">
                        {row['score_rcrs']:.0f}
                    </div>
                    <div style="font-size:0.67rem;color:{TEXT_MUT};">/100 RCRS</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with t1:
        _aba_visao_geral()

    with t2:
        st.markdown('<div class="rg-card"><div class="rg-card-title">Calculadora RCRS Interativa</div>',
                    unsafe_allow_html=True)
        with st.form("form_rcrs"):
            c1, c2 = st.columns(2)
            so  = c1.slider("Score de Risco Operacional (0–100)", 0.0, 100.0, 50.0, 1.0)
            ct  = c2.selectbox("Criticidade do Trecho", m.CRITICIDADE_OPERACIONAL)
            c3, c4 = st.columns(2)
            hf  = c3.number_input("Histórico de Falhas (ocorrências)", 0, 20, 1)
            ir  = c4.slider("Impacto Regulatório (0–100)", 0.0, 100.0, 40.0)
            c5, c6 = st.columns(2)
            re2 = c5.slider("Risco ESG (0–100)", 0.0, 100.0, 30.0)
            cd2 = c6.slider("Confiabilidade do Dado (%)", 0.0, 100.0, 80.0)
            sub_rc = st.form_submit_button("Calcular RCRS", type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

        if sub_rc:
            rc, cls, rec = re_.calcular_rcrs(so, ct, hf, ir, re2, cd2)
            cor_cls = m.RCRS_COLORS.get(cls, TEXT_SEC)
            cg2, cr2 = st.columns([1, 2])
            with cg2:
                st.plotly_chart(gauge_risco(rc, cls), width="stretch")
            with cr2:
                st.markdown(f"""
                <div style="background:{CARD_BG};border:1px solid {cor_cls}55;
                            border-radius:14px;padding:24px;margin-top:8px;">
                    <div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.1em;
                                color:{TEXT_MUT};margin-bottom:8px;">
                        CLASSIFICAÇÃO RCRS
                    </div>
                    <div style="font-size:1.9rem;font-weight:800;color:{cor_cls};">{cls}</div>
                    <div style="font-size:2.6rem;font-weight:900;color:{TEXT_PRI};margin:4px 0;">
                        {rc:.1f}
                        <span style="font-size:1.1rem;color:{TEXT_MUT};font-weight:400;">/100</span>
                    </div>
                    <div style="font-size:0.84rem;color:{TEXT_SEC};
                                border-top:1px solid {BORDER};padding-top:14px;
                                margin-top:8px;line-height:1.75;">
                        <strong style="color:{TEXT_PRI};">Recomendação:</strong> {rec}
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE — AUDITORIA
# ═══════════════════════════════════════════════════════════════════════════

def page_auditoria():
    ph("Auditoria & Rastreabilidade",
       "Registro imutável de todas as operações realizadas na plataforma")

    df = db.get_all_auditoria()
    if df.empty: info("Nenhum registro de auditoria encontrado."); return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Registros",  len(df))
    c2.metric("Tipos de Ação",       df["tipo_acao"].nunique())
    c3.metric("Usuários Ativos",     df["usuario"].nunique())
    c4.metric("Último Registro",     str(df["data_hora"].iloc[0])[:16])

    df["data_hora_dt"] = pd.to_datetime(df["data_hora"])
    df["data"]         = df["data_hora_dt"].dt.date
    cnt_d = df.groupby(["data", "tipo_acao"]).size().reset_index(name="total")

    fa = px.bar(cnt_d, x="data", y="total", color="tipo_acao",
                color_discrete_map={
                    "INSERÇÃO":   ACCENT2,
                    "ATUALIZAÇÃO": C_MEDIO,
                    "EXCLUSÃO":   C_CRITICO,
                },
                barmode="stack")
    _pt(fa); fa.update_layout(
        title="Atividade de Auditoria por Dia", height=230,
        margin=dict(t=40, b=10),
        legend=dict(orientation="h", y=-0.3, font=dict(size=11)),
    )
    st.plotly_chart(fa, width="stretch")

    sdiv("FILTROS E BUSCA")
    c1, c2, c3 = st.columns(3)
    tf = c1.multiselect("Tipo de Ação",  df["tipo_acao"].unique().tolist())
    uf = c2.multiselect("Usuário",       df["usuario"].unique().tolist())
    bf = c3.text_input("Buscar em item ou descrição")

    df2 = df.copy()
    if tf:  df2 = df2[df2["tipo_acao"].isin(tf)]
    if uf:  df2 = df2[df2["usuario"].isin(uf)]
    if bf:
        mask = (df2["item_alterado"].str.contains(bf, case=False, na=False) |
                df2["descricao"].str.contains(bf, case=False, na=False))
        df2 = df2[mask]

    st.markdown(f'<div style="font-size:0.79rem;color:{TEXT_MUT};margin-bottom:8px;">'
                f'Exibindo {len(df2)} de {len(df)} registros</div>', unsafe_allow_html=True)
    st.dataframe(
        df2[["data_hora", "tipo_acao", "usuario", "item_alterado", "descricao"]].head(100),
        width="stretch", hide_index=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE — ESG
# ═══════════════════════════════════════════════════════════════════════════

def page_esg():
    ph("Indicadores ESG",
       "Ambiental, Social e Governança — sustentabilidade e impacto da infraestrutura ferroviária")

    st.markdown(f"""
    <div class="info-box">
        <b>Nota metodológica:</b> Os indicadores ESG são calculados com modelos parametrizados
        e dados simulados. Em ambiente produtivo devem ser complementados com inventários GHG
        certificados, relatórios socioambientais e auditorias independentes.
    </div>
    """, unsafe_allow_html=True)

    df = db.get_all_esg()
    if df.empty: info("Nenhum indicador ESG calculado."); return

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Risco Ambiental Médio",   f"{df['risco_ambiental'].mean():.1f}/100")
    c2.metric("Impacto Paralisação",     f"{df['impacto_paralisacao'].mean():.1f}/100")
    c3.metric("Eficiência Manutenção",   f"{df['eficiencia_manutencao'].mean():.1f}/100")
    c4.metric("Emissão CO₂ (simulada)",  f"{df['emissao_co2_estimada'].sum():.0f} t")
    c5.metric("Área de Impacto (simul.)",f"{df['area_impacto_km2'].sum():.1f} km²")

    ca, cb = st.columns([1.4, 1])
    with ca:
        sdiv("PERFIL ESG POR TRECHO")
        inds = ["risco_ambiental", "impacto_paralisacao", "eficiencia_manutencao"]
        lbls = ["Risco Ambiental", "Impacto Paralisação", "Efic. Manutenção"]
        cors = [C_CRITICO, C_ALTO, C_BAIXO]
        fe = go.Figure()
        for ind, lbl, cor in zip(inds, lbls, cors):
            fe.add_trace(go.Bar(name=lbl, x=df["trecho_codigo"], y=df[ind],
                                marker=dict(color=cor, opacity=0.82, cornerradius=5)))
        _pt(fe); fe.update_layout(
            barmode="group", height=320,
            xaxis=dict(title="Trecho"),
            yaxis=dict(title="Score (0–100)", range=[0, 115]),
            legend=dict(orientation="h", y=1.08),
            margin=dict(t=20, b=10),
        )
        st.plotly_chart(fe, width="stretch")

    with cb:
        sdiv("PRIORIDADE ESG")
        cnt_p = df["prioridade_esg"].value_counts().reset_index()
        cnt_p.columns = ["Prioridade", "Qtd"]
        cors_p = [m.ESG_PRIORITY_COLORS.get(p, TEXT_MUT) for p in cnt_p["Prioridade"]]
        fp = go.Figure(go.Pie(
            labels=cnt_p["Prioridade"], values=cnt_p["Qtd"], hole=0.55,
            marker=dict(colors=cors_p, line=dict(color=PRIMARY, width=3)),
            textfont=dict(size=11, family="Inter"),
            hovertemplate="<b>%{label}</b>: %{value}<extra></extra>",
        ))
        _pt(fp); fp.update_layout(height=220, showlegend=True,
                                    legend=dict(font=dict(size=10)),
                                    margin=dict(t=10, b=10, l=0, r=60))
        st.plotly_chart(fp, width="stretch")

        for ind, lbl, cor in zip(inds, lbls, cors):
            val = df[ind].mean(); pct = min(val, 100)
            st.markdown(f"""
            <div class="esg-bar-wrap">
                <div class="esg-bar-label">
                    <span>{lbl}</span>
                    <span style="color:{cor};font-family:'JetBrains Mono',monospace;font-size:0.79rem;">
                        {val:.1f}/100
                    </span>
                </div>
                <div class="esg-bar-track">
                    <div class="esg-bar-fill"
                         style="width:{pct:.0f}%;background:linear-gradient(90deg,{cor},{cor}77);">
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    sdiv("RECOMENDAÇÕES PRIORITÁRIAS ESG")
    for _, row in df.iterrows():
        if row["prioridade_esg"] in ("Alta", "Crítica"):
            cor_p = C_CRITICO if row["prioridade_esg"] == "Crítica" else C_ALTO
            recs  = [r.strip() for r in str(row["recomendacoes"]).split("|") if r.strip()]
            recs_html = "".join(f"<li style='margin-bottom:5px;'>{r}</li>" for r in recs)
            st.markdown(f"""
            <div style="background:{CARD_BG};border:1px solid {cor_p}44;
                        border-left:4px solid {cor_p};border-radius:12px;
                        padding:16px 20px;margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;
                            align-items:center;margin-bottom:10px;">
                    <div>
                        <span style="font-family:'JetBrains Mono',monospace;
                                     color:{ACCENT2};font-size:0.87rem;font-weight:600;">
                            {row['trecho_codigo']}
                        </span>
                        <span style="color:{TEXT_MUT};font-size:0.75rem;margin-left:10px;">
                            {row['ferrovia']}
                        </span>
                    </div>
                    <span style="background:{cor_p}18;color:{cor_p};
                                 border:1px solid {cor_p}44;padding:3px 12px;
                                 border-radius:20px;font-size:0.72rem;font-weight:700;">
                        Prioridade {row['prioridade_esg']}
                    </span>
                </div>
                <ul style="font-size:0.8rem;color:{TEXT_SEC};margin:0;
                           padding-left:20px;line-height:1.7;">
                    {recs_html}
                </ul>
            </div>
            """, unsafe_allow_html=True)

    sdiv("DADOS DETALHADOS")
    st.dataframe(
        df[["trecho_codigo", "ferrovia", "estado", "risco_ambiental",
            "impacto_paralisacao", "eficiencia_manutencao", "prioridade_esg",
            "emissao_co2_estimada", "area_impacto_km2"]],
        width="stretch", hide_index=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE — RELATÓRIOS
# ═══════════════════════════════════════════════════════════════════════════

def page_relatorios():
    ph("Relatórios Executivos",
       "Relatórios técnicos de compliance com evidências, scores e rastreabilidade completa")

    t1, t2 = st.tabs(["Relatório por Ativo", "Relatório por Trecho"])

    # Aba em função: os `return` antecipados (ex.: botão não clicado)
    # não podem impedir a renderização da aba de trecho
    def _aba_ativo():
        df_a = db.get_all_ativos()
        if df_a.empty: info("Nenhum ativo cadastrado."); return

        opts = {
            f"{r['codigo']} — {r['tipo_ativo']} | {r['trecho_codigo']} | {r['ferrovia']}": r["id"]
            for _, r in df_a.iterrows()
        }
        cx, cy = st.columns([3, 1])
        sel = cx.selectbox("Selecionar Ativo para Relatório", list(opts.keys()))
        with cy:
            st.markdown("<br>", unsafe_allow_html=True)
            gerar = st.button("Gerar Relatório", type="primary")
        if not gerar: return

        ativo_id = opts[sel]
        rel = rp.gerar_relatorio_ativo(ativo_id)
        if not rel: danger("Ativo não encontrado."); return

        av = rel["ativo"]
        tr = rel["trecho"]
        ur = rel["riscos"].iloc[0] if not rel["riscos"].empty else None

        cor_crit = (C_CRITICO if tr and tr["criticidade_operacional"] == "Crítica" else
                    C_ALTO    if tr and tr["criticidade_operacional"] == "Alta"    else
                    C_MEDIO   if tr and tr["criticidade_operacional"] == "Média"   else C_BAIXO
                    ) if tr else ACCENT2

        # Cabeçalho executivo
        ur_html = ""
        if ur is not None:
            cv = RISK_C.get(ur["nivel_risco"], TEXT_SEC)
            cr_ = m.RCRS_COLORS.get(ur["classificacao_rcrs"], TEXT_SEC)
            ur_html = f"""
            <div style="display:flex;gap:14px;flex-shrink:0;margin-left:24px;">
                <div style="background:{cv}1A;border:1px solid {cv}44;border-radius:12px;
                            padding:14px 18px;text-align:center;">
                    <div style="font-size:0.65rem;text-transform:uppercase;color:{TEXT_MUT};
                                letter-spacing:0.08em;">Risco</div>
                    <div style="font-size:1.7rem;font-weight:900;color:{cv};">
                        {float(ur["score_risco"]):.0f}
                    </div>
                    <div style="font-size:0.72rem;color:{cv};">{ur["nivel_risco"]}</div>
                </div>
                <div style="background:{cr_}1A;border:1px solid {cr_}44;border-radius:12px;
                            padding:14px 18px;text-align:center;">
                    <div style="font-size:0.65rem;text-transform:uppercase;color:{TEXT_MUT};
                                letter-spacing:0.08em;">RCRS</div>
                    <div style="font-size:1.7rem;font-weight:900;color:{cr_};">
                        {float(ur["score_rcrs"]):.0f}
                    </div>
                    <div style="font-size:0.72rem;color:{cr_};">{ur["classificacao_rcrs"][:14]}</div>
                </div>
            </div>"""

        st.markdown(f"""
        <div class="exec-report-header">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;">
                <div>
                    <div style="font-size:0.67rem;text-transform:uppercase;letter-spacing:0.13em;
                                color:{TEXT_MUT};margin-bottom:7px;">
                        RELATÓRIO TÉCNICO DE COMPLIANCE · RailGuard AI v0.4
                        · {rel['data_relatorio']}
                    </div>
                    <div class="exec-title">{av['tipo_ativo']} — {av['codigo']}</div>
                    <div class="exec-subtitle">
                        {tr['ferrovia'] if tr else '—'} &nbsp;|&nbsp;
                        Trecho {tr['codigo'] if tr else '—'} &nbsp;|&nbsp;
                        {tr['km_inicial'] if tr else '—'}–{tr['km_final'] if tr else '—'} km
                        &nbsp;|&nbsp; {tr['estado'] if tr else '—'}
                    </div>
                    <span class="exec-badge"
                          style="background:{cor_crit}1A;color:{cor_crit};
                                 border:1px solid {cor_crit}44;">
                        Criticidade {tr['criticidade_operacional'] if tr else '—'}
                    </span>
                </div>
                {ur_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

        cd1, cd2 = st.columns(2)
        with cd1:
            st.markdown('<div class="rg-card"><div class="rg-card-title">Dados do Ativo</div>',
                        unsafe_allow_html=True)
            for l, v in [("Código", av["codigo"]), ("Tipo", av["tipo_ativo"]),
                         ("Idade", f"{av['idade_anos']} anos"),
                         ("Última Manutenção", str(av.get("data_ultima_manutencao", "—"))),
                         ("Condição Visual", av.get("condicao_visual", "—")),
                         ("Observações", str(av.get("observacoes", "—"))[:65] + "…")]:
                st.markdown(row_kv(l, v), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with cd2:
            if tr:
                st.markdown('<div class="rg-card"><div class="rg-card-title">Dados do Trecho</div>',
                            unsafe_allow_html=True)
                for l, v in [("Código", tr["codigo"]), ("Ferrovia", tr["ferrovia"]),
                             ("Extensão", f"{tr['km_inicial']}–{tr['km_final']} km"),
                             ("Estado", tr["estado"]), ("Tipo de Via", tr["tipo_via"]),
                             ("Criticidade", tr["criticidade_operacional"])]:
                    st.markdown(row_kv(l, v), unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        if ur is not None:
            sc_r = float(ur["score_risco"]); nv_r = ur["nivel_risco"]
            sc_rc = float(ur["score_rcrs"]); cl_rc = ur["classificacao_rcrs"]
            cga, cex = st.columns([1, 1.5])
            with cga:
                st.plotly_chart(gauge_risco(sc_r, nv_r, 210), width="stretch")
                st.plotly_chart(gauge_risco(sc_rc, cl_rc, 210), width="stretch")
            with cex:
                if not rel["inspecoes"].empty:
                    ui = rel["inspecoes"].iloc[0]
                    try:
                        dias_m = (date.today() -
                                  pd.to_datetime(av["data_ultima_manutencao"]).date()).days
                    except: dias_m = 365
                    _, _, cont2 = re_.calcular_risco_operacional(
                        float(av["idade_anos"]), dias_m,
                        tr["criticidade_operacional"] if tr else "Média",
                        bool(ui["fissura"]), bool(ui["desgaste"]),
                        bool(ui["corrosao"]), bool(ui["falha_fixacao"]),
                        float(ui["nivel_vibracao"]), float(ui["carga_operacional"]),
                        av["condicao_visual"])
                    ext = re_.gerar_explicabilidade(
                        sc_r, nv_r, cont2,
                        bool(ui["fissura"]), bool(ui["desgaste"]),
                        bool(ui["corrosao"]), bool(ui["falha_fixacao"]),
                        float(ui["nivel_vibracao"]),
                        float(av["idade_anos"]), dias_m,
                        tr["criticidade_operacional"] if tr else "Média",
                        av["condicao_visual"])
                    st.markdown(
                        '<div class="rg-card"><div class="rg-card-title">Explicabilidade do Score</div>',
                        unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:0.83rem;color:{TEXT_SEC};line-height:1.75;">'
                                f'{ext}</div>', unsafe_allow_html=True)
                    for fat, pts in sorted(cont2.items(), key=lambda x: x[1], reverse=True):
                        if pts > 0.5:
                            pct = min(pts / 15.0 * 100, 100)
                            cb2 = C_CRITICO if pct > 70 else C_ALTO if pct > 40 else C_MEDIO
                            st.markdown(f"""
                            <div style="margin-bottom:8px;">
                                <div style="display:flex;justify-content:space-between;
                                            font-size:0.74rem;color:{TEXT_MUT};margin-bottom:4px;">
                                    <span>{fat}</span>
                                    <span style="color:{cb2};font-family:'JetBrains Mono',monospace;">
                                        {pts:.1f} pts
                                    </span>
                                </div>
                                <div style="height:6px;background:{BORDER};border-radius:3px;overflow:hidden;">
                                    <div style="height:100%;width:{pct:.0f}%;background:{cb2};border-radius:3px;"></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                cor_rec = RISK_C.get(nv_r, TEXT_SEC)
                st.markdown(f"""
                <div style="background:{cor_rec}0D;border:1px solid {cor_rec}33;
                            border-radius:12px;padding:16px 18px;margin-top:10px;">
                    <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.09em;
                                color:{TEXT_MUT};margin-bottom:7px;">
                        Recomendação Técnica
                    </div>
                    <div style="font-size:0.84rem;color:{TEXT_SEC};line-height:1.75;">
                        {ur.get('recomendacao','—')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        sdiv("HISTÓRICO DE INSPEÇÕES")
        if not rel["inspecoes"].empty:
            cols_i = [c for c in ["data_inspecao", "tipo_inspecao", "responsavel",
                                   "fissura", "desgaste", "corrosao", "falha_fixacao",
                                   "nivel_vibracao", "temperatura", "carga_operacional"]
                      if c in rel["inspecoes"].columns]
            st.dataframe(rel["inspecoes"][cols_i], width="stretch", hide_index=True)

        sdiv("LOG DE AUDITORIA")
        if not rel["auditoria"].empty:
            st.dataframe(
                rel["auditoria"][["data_hora", "tipo_acao", "usuario", "descricao"]],
                width="stretch", hide_index=True)

        sdiv("EXPORTAR RELATÓRIO")
        csv_out = rp.relatorio_para_csv(rel)
        st.download_button(
            "Exportar Relatório Completo (CSV)",
            data=csv_out.encode("utf-8"),
            file_name=f"railguard_{av['codigo']}_{date.today()}.csv",
            mime="text/csv",
        )

    with t1:
        _aba_ativo()

    with t2:
        df_t = db.get_all_trechos()
        if df_t.empty: info("Nenhum trecho cadastrado."); return

        opts_t = {f"{r['codigo']} — {r['ferrovia']} | {r['estado']}": r["id"]
                  for _, r in df_t.iterrows()}
        cx2, cy2 = st.columns([3, 1])
        sel_t = cx2.selectbox("Selecionar Trecho", list(opts_t.keys()))
        with cy2:
            st.markdown("<br>", unsafe_allow_html=True)
            gerar_t = st.button("Gerar Relatório de Trecho", type="primary")
        if not gerar_t: return

        tid  = opts_t[sel_t]
        tr2  = db.get_trecho_by_id(tid)
        da2  = db.get_all_ativos(); da2 = da2[da2["trecho_id"] == tid]
        dr2  = db.get_all_riscos()
        de2  = db.get_all_esg(); de2t = de2[de2["trecho_id"] == tid]

        cor_c2 = (C_CRITICO if tr2["criticidade_operacional"] == "Crítica" else
                  C_ALTO    if tr2["criticidade_operacional"] == "Alta"    else
                  C_MEDIO   if tr2["criticidade_operacional"] == "Média"   else C_BAIXO)

        st.markdown(f"""
        <div class="exec-report-header">
            <div style="font-size:0.67rem;text-transform:uppercase;letter-spacing:0.13em;
                        color:{TEXT_MUT};margin-bottom:7px;">
                RELATÓRIO DE TRECHO · RailGuard AI v0.4
            </div>
            <div class="exec-title">Trecho {tr2['codigo']} — {tr2['ferrovia']}</div>
            <div class="exec-subtitle">
                {tr2['km_inicial']}–{tr2['km_final']} km &nbsp;|&nbsp;
                {tr2['tipo_via']} &nbsp;|&nbsp; {tr2['estado']}
            </div>
            <span class="exec-badge"
                  style="background:{cor_c2}1A;color:{cor_c2};border:1px solid {cor_c2}44;">
                Criticidade {tr2['criticidade_operacional']}
            </span>
        </div>
        """, unsafe_allow_html=True)

        if not da2.empty:
            ai2  = da2["id"].tolist()
            rit  = dr2[dr2["ativo_id"].isin(ai2)]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Ativos no Trecho", len(da2))
            c2.metric("RCRS Médio",
                       f"{rit['score_rcrs'].mean():.1f}/100" if not rit.empty else "—")
            c3.metric("Risco Médio",
                       f"{rit['score_risco'].mean():.1f}/100" if not rit.empty else "—")
            c4.metric("Ativos Críticos",
                       len(rit[rit["nivel_risco"] == "Crítico"]) if not rit.empty else 0)
            sdiv("ATIVOS DO TRECHO")
            st.dataframe(
                da2[["codigo", "tipo_ativo", "idade_anos",
                     "data_ultima_manutencao", "condicao_visual"]],
                width="stretch", hide_index=True)

        if not de2t.empty:
            sdiv("INDICADORES ESG")
            re2t = de2t.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Risco Ambiental",    f"{re2t['risco_ambiental']:.1f}/100")
            c2.metric("Impacto Paralisação", f"{re2t['impacto_paralisacao']:.1f}/100")
            c3.metric("Prioridade ESG",      re2t["prioridade_esg"])

        sdiv("EXPORTAR")
        csv_t2 = rp.relatorio_trecho_para_csv(tid)
        st.download_button(
            "Exportar Relatório do Trecho (CSV)",
            data=csv_t2.encode("utf-8"),
            file_name=f"railguard_trecho_{tr2['codigo']}_{date.today()}.csv",
            mime="text/csv",
        )


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE — CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════════════════

def page_config():
    ph("Configurações do Sistema",
       "Informações técnicas, status da plataforma, migração e manutenção")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="rg-card"><div class="rg-card-title">Sobre a Plataforma</div>',
                    unsafe_allow_html=True)
        for l, v in [
            ("Plataforma",     "RailGuard AI"),
            ("Versão",         "0.4 MVP"),
            ("Framework",      "Streamlit + Python 3.11+"),
            ("Banco de Dados", "SQLite (migração PostgreSQL prevista)"),
            ("ML Engine",      "RandomForestClassifier · scikit-learn"),
            ("Visualização",   "Plotly 5.x"),
            ("Status",         "Demonstrativo — dados simulados"),
        ]:
            st.markdown(row_kv(l, v), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        s2 = db.get_dashboard_stats()
        st.markdown('<div class="rg-card"><div class="rg-card-title">Status do Banco de Dados</div>',
                    unsafe_allow_html=True)
        for l, v in [
            ("Trechos Monitorados",   s2["total_trechos"]),
            ("Ativos Monitorados",    s2["total_ativos"]),
            ("Inspeções Técnicas",    s2["total_inspecoes"]),
            ("Alertas Abertos",       s2["total_alertas_abertos"]),
            ("Ocorrências Críticas",  s2["risco_critico"]),
            ("Ocorrências Altas",     s2["risco_alto"]),
            ("Arquivo de Banco",      os.path.basename(db.DB_PATH)),
        ]:
            st.markdown(row_kv(l, v), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    warn("<b>Aviso:</b> MVP acadêmico/demonstrativo. Dados simulados. "
         "Sem integração com a ANTT ou com operadores ferroviários reais.")

    sdiv("GUIA DE MIGRAÇÃO PARA POSTGRESQL")
    with st.expander("Ver instruções completas"):
        st.code("""
# 1. Instalar dependências
pip install psycopg2-binary sqlalchemy

# 2. Em database.py: substituir get_connection()
from sqlalchemy import create_engine
DATABASE_URL = "postgresql://user:senha@host:5432/railguard_db"
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10)
def get_connection():
    return engine.connect()

# 3. Ajustar placeholders: '?' → ':param' (SQLAlchemy) ou '%s' (psycopg2)
# 4. DDL: AUTOINCREMENT → SERIAL, TIMESTAMP → TIMESTAMPTZ DEFAULT NOW()

# 5. Migrar dados existentes
for tabela in ["trechos","ativos","inspecoes","riscos","alertas","auditoria",
               "indicadores_esg","zonas_criticas"]:
    df = pd.read_sql_query(f"SELECT * FROM {tabela}", sqlite_conn)
    df.to_sql(tabela, pg_engine, if_exists="append", index=False)
    print(f"{tabela}: {len(df)} registros migrados")
        """, language="python")

    sdiv("RECARREGAR DADOS DE DEMONSTRAÇÃO")
    warn("Esta ação apaga todos os dados atuais e recarrega os dados simulados de demonstração.")
    cb_, _ = st.columns([1, 3])
    with cb_:
        if st.button("Recarregar Demonstração", type="secondary"):
            if os.path.exists(db.DB_PATH):
                os.remove(db.DB_PATH)
            db.init_database()
            seed_data.seed_database()
            for k in ["modelo_rf", "fonte_ml", "ml_acc", "ml_report"]:
                if k in st.session_state:
                    del st.session_state[k]
            flash("Dados de demonstração recarregados com sucesso.")
            st.rerun()



# ═══════════════════════════════════════════════════════════════════════════
#  PAGE — ZONA CRÍTICA (v0.4) — Estudo de Caso Heavy Haul
# ═══════════════════════════════════════════════════════════════════════════

def page_zona_critica():
    ph("Análise de Zona Crítica",
       "Estudo de Caso Heavy Haul · Clustering espacial de defeitos · Matriz P×C · Causa raiz em cascata")

    # Banner de contexto do estudo de caso
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(230,57,70,0.12),rgba(244,123,53,0.08));
                border:1px solid rgba(230,57,70,0.35);border-left:5px solid {C_CRITICO};
                border-radius:14px;padding:20px 24px;margin-bottom:24px;">
        <div style="display:flex;align-items:flex-start;gap:16px;">
            <div>
                <div style="font-size:1rem;font-weight:800;color:{TEXT_PRI};margin-bottom:6px;">
                    Estudo de Caso — Trecho Heavy Haul (TRC-CASO)
                </div>
                <div style="font-size:0.84rem;color:{TEXT_SEC};line-height:1.7;">
                    Trecho de <strong>10 km</strong> · Carga máxima: <strong>32,5 t/eixo</strong> ·
                    Velocidade autorizada: <strong>60 km/h</strong> (operacional: 45 km/h) ·
                    <strong>18 trens/dia</strong> · 4.500 t/trem<br>
                    Inspeção identificou <strong>Zona Crítica</strong> entre
                    <strong>Km 7+100 e Km 7+300</strong> (200 metros) com
                    <strong>5 tipos de defeito espacialmente correlacionados</strong>.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs do estudo de caso ────────────────────────────────────────
    bloco("1", "RESUMO DA INSPEÇÃO — NÃO CONFORMIDADES QUANTIFICADAS", C_CRITICO)

    nc_data = [
        ("Dormentes",   2000, 80,  "80/2000 (4,0%)",  "5 consecutivos severos no Km 7+200 em curva R=500m", C_CRITICO),
        ("Fixações",    4000, 100, "100/4000 (2,5%)", "10 consecutivas defeituosas entre Km 7+150–7+250",   C_CRITICO),
        ("Trilhos",    "20km", 6,  "6 pontos",         "T4 (Km 6+700): desgaste severo em curva R=600m",     C_ALTO),
        ("AMV",          10,  1,  "1/10 (10%)",       "AMV-04 (Km 7+180): desgaste + irregularidade roda/trilho", C_ALTO),
        ("Drenagem",     40,  5,  "5/40 (12,5%)",     "Obstrução severa no Km 7+300 — acúmulo de água",    C_CRITICO),
        ("Sinalização",  30,  2,  "2/30 (6,7%)",      "Km 7+100: perda de visibilidade + falha de iluminação", C_MEDIO),
    ]

    cols_nc = st.columns(3)
    for i, (tipo, total, nc, pct, obs, cor) in enumerate(nc_data):
        with cols_nc[i % 3]:
            st.markdown(f"""
            <div style="background:{CARD_BG};border:1px solid {cor}55;
                        border-top:3px solid {cor};border-radius:12px;
                        padding:16px 18px;margin-bottom:14px;">
                <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                            letter-spacing:0.09em;color:{TEXT_MUT};margin-bottom:6px;">
                    {tipo}
                </div>
                <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:6px;">
                    <span style="font-size:1.8rem;font-weight:900;color:{cor};">{nc}</span>
                    <span style="font-size:0.82rem;color:{TEXT_MUT};">NC de {total} inspecionados</span>
                </div>
                <div style="font-size:0.72rem;color:{TEXT_SEC};background:{SURFACE};
                            padding:4px 10px;border-radius:20px;display:inline-block;
                            margin-bottom:8px;font-family:'JetBrains Mono',monospace;">
                    {pct}
                </div>
                <div style="font-size:0.76rem;color:{TEXT_MUT};line-height:1.5;">{obs}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Linha do tempo espacial ───────────────────────────────────────
    bloco("2", "LINHA DO TEMPO ESPACIAL — DISTRIBUIÇÃO DOS DEFEITOS NO KM", C_ALTO)

    # Cria gráfico de dispersão por km com tipo de ativo
    df_at = db.get_all_ativos()
    df_r  = db.get_all_riscos()

    df_caso = df_at[df_at["trecho_codigo"] == "TRC-CASO"].copy() if "trecho_codigo" in df_at.columns else pd.DataFrame()

    if not df_caso.empty and "km_posicao" in df_caso.columns:
        df_caso = df_caso[df_caso["km_posicao"].notna()].copy()

        # Junta com scores
        if not df_r.empty:
            ult_r = (df_r.sort_values("data_calculo", ascending=False)
                     .drop_duplicates(subset=["ativo_id"], keep="first")
                     [["ativo_id", "score_risco", "nivel_risco"]])
            df_caso = df_caso.merge(
                ult_r.rename(columns={"ativo_id": "id"}), on="id", how="left")
        if "score_risco" not in df_caso.columns:
            df_caso["score_risco"] = 50.0
        if "nivel_risco" not in df_caso.columns:
            df_caso["nivel_risco"] = "Médio"

        cores_por_nivel = {
            "Baixo": C_BAIXO, "Médio": C_MEDIO, "Alto": C_ALTO, "Crítico": C_CRITICO
        }

        fig_scatter = go.Figure()

        # Zona crítica — área sombreada (limites vindos do banco; fallback no estudo de caso)
        df_zc_caso = db.get_all_zonas_criticas()
        df_zc_caso = df_zc_caso[df_zc_caso["trecho_codigo"] == "TRC-CASO"]
        faixas_zc = (list(zip(df_zc_caso["km_inicio"], df_zc_caso["km_fim"]))
                     if not df_zc_caso.empty else [(7.1, 7.3)])
        for km_a, km_b in faixas_zc:
            fig_scatter.add_vrect(
                x0=km_a, x1=km_b,
                fillcolor="rgba(230,57,70,0.12)",
                line_color="rgba(230,57,70,0.5)",
                line_width=2,
                annotation_text="ZONA CRÍTICA",
                annotation_position="top left",
                annotation_font_color=C_CRITICO,
                annotation_font_size=11,
            )

        # Pontos dos ativos
        for nivel, cor in cores_por_nivel.items():
            df_n = df_caso[df_caso["nivel_risco"] == nivel]
            if df_n.empty:
                continue
            fig_scatter.add_trace(go.Scatter(
                x=df_n["km_posicao"],
                y=df_n["score_risco"],
                mode="markers+text",
                name=nivel,
                text=df_n["codigo"],
                textposition="top center",
                textfont=dict(size=9, color=TEXT_MUT, family="JetBrains Mono"),
                marker=dict(
                    size=df_n["score_risco"].fillna(40) / 6 + 8,
                    color=cor, opacity=0.9,
                    line=dict(color=PRIMARY, width=1.5),
                    symbol="circle",
                ),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Km: %{x:.3f}<br>"
                    "Score Risco: %{y:.0f}/100<br>"
                    f"Nível: {nivel}<extra></extra>"
                ),
            ))

        _pt(fig_scatter)
        fig_scatter.update_layout(
            title="Distribuição de Risco por Posição Quilométrica",
            height=360,
            xaxis=dict(title="Posição (km)", showgrid=True, gridcolor=BORDER, dtick=0.5),
            yaxis=dict(title="Score de Risco (0–100)", range=[0, 115]),
            margin=dict(t=40, b=30, l=10, r=10),
            legend=dict(orientation="h", y=1.08, font=dict(size=11)),
        )
        # Linha de referência crítico
        fig_scatter.add_hline(y=75, line_dash="dot", line_color=C_CRITICO,
                               line_width=1.5, opacity=0.7,
                               annotation_text="Limiar Crítico",
                               annotation_font_color=C_CRITICO,
                               annotation_font_size=10)
        fig_scatter.add_hline(y=50, line_dash="dot", line_color=C_MEDIO,
                               line_width=1, opacity=0.5,
                               annotation_text="Limiar Alto",
                               annotation_font_color=C_MEDIO,
                               annotation_font_size=10)

        st.plotly_chart(fig_scatter, width="stretch")
        chart_insight(
            "Cada ponto representa um ativo. O tamanho é proporcional ao score de risco. "
            "A área sombreada em vermelho delimita a <strong>Zona Crítica (Km 7+100–7+300)</strong> "
            "onde 5 tipos de defeito estão espacialmente correlacionados. "
            "Pontos acima da linha pontilhada vermelha exigem intervenção imediata."
        )
    else:
        info("Rode a carga de demonstração com dados do estudo de caso para visualizar o gráfico.")

    # ── Matriz P×C ────────────────────────────────────────────────────
    bloco("3", "MATRIZ PROBABILIDADE × CONSEQUÊNCIA — METODOLOGIA ISO 31000", C_COMP)

    col_m, col_t = st.columns([1.2, 1])

    with col_m:
        # Monta a matriz visual 5×5
        # numpy already imported as np
        matrix = np.zeros((5, 5), dtype=int)
        for p in range(5):
            for c in range(5):
                matrix[p, c] = (p+1) * (c+1)

        cores_mtz = []
        for p in range(5):
            row_c = []
            for c in range(5):
                v = matrix[p, c]
                if v <= 4:    row_c.append("#0CB87A")
                elif v <= 9:  row_c.append("#F4A62A")
                elif v <= 16: row_c.append("#F47B35")
                else:          row_c.append("#E63946")
            cores_mtz.append(row_c)

        # Heatmap personalizado da matriz
        fig_mtz = go.Figure(data=go.Heatmap(
            z=matrix,
            x=["C1\nInsignificante", "C2\nPequena", "C3\nModerada",
               "C4\nGrave", "C5\nCatastrófica"],
            y=["P1\nMuito Baixa", "P2\nBaixa", "P3\nMédia",
               "P4\nAlta", "P5\nMuito Alta"],
            colorscale=[
                [0,    "rgba(12,184,122,0.8)"],
                [0.16, "rgba(244,166,42,0.8)"],
                [0.36, "rgba(244,123,53,0.8)"],
                [0.64, "rgba(230,57,70,0.9)"],
                [1.0,  "rgba(180,20,30,1.0)"],
            ],
            text=matrix,
            texttemplate="%{text}",
            textfont=dict(size=14, color="white", family="Inter"),
            showscale=False,
            hovertemplate="P%{y} × C%{x} = <b>%{z}</b><extra></extra>",
        ))
        _pt(fig_mtz)
        fig_mtz.update_layout(
            title="Matriz P×C (Probabilidade × Consequência)",
            height=320,
            margin=dict(t=40, b=10, l=10, r=10),
            xaxis=dict(showgrid=False, side="top",
                       tickfont=dict(size=10, color=TEXT_SEC)),
            yaxis=dict(showgrid=False, autorange="reversed",
                       tickfont=dict(size=10, color=TEXT_SEC)),
        )
        st.plotly_chart(fig_mtz, width="stretch")
        st.markdown(f"""
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;">
            <span style="background:rgba(12,184,122,0.2);color:{C_BAIXO};border:1px solid {C_BAIXO}55;
                         padding:3px 12px;border-radius:20px;font-size:0.73rem;font-weight:700;">
                1–4 Baixo
            </span>
            <span style="background:rgba(244,166,42,0.2);color:{C_MEDIO};border:1px solid {C_MEDIO}55;
                         padding:3px 12px;border-radius:20px;font-size:0.73rem;font-weight:700;">
                5–9 Moderado
            </span>
            <span style="background:rgba(244,123,53,0.2);color:{C_ALTO};border:1px solid {C_ALTO}55;
                         padding:3px 12px;border-radius:20px;font-size:0.73rem;font-weight:700;">
                10–16 Alto
            </span>
            <span style="background:rgba(230,57,70,0.2);color:{C_CRITICO};border:1px solid {C_CRITICO}55;
                         padding:3px 12px;border-radius:20px;font-size:0.73rem;font-weight:700;">
                17–25 Crítico
            </span>
        </div>
        """, unsafe_allow_html=True)

    with col_t:
        # Scores P×C dos ativos do estudo de caso
        st.markdown(f'<div class="rg-card"><div class="rg-card-title">Scores P×C do Estudo de Caso</div>',
                    unsafe_allow_html=True)

        ativos_caso_pc = [
            ("CASO-DRE-01", "Drenagem",    "Km 7+300", 5, 5, 25, "Crítico",  "Interdição imediata"),
            ("CASO-DOR-01", "Dormente",    "Km 7+200", 5, 5, 25, "Crítico",  "Interdição imediata"),
            ("CASO-FIX-01", "Fixação",     "Km 7+200", 4, 5, 20, "Crítico",  "Interdição imediata"),
            ("CASO-AMV-04", "AMV",         "Km 7+180", 4, 5, 20, "Crítico",  "Interdição imediata"),
            ("CASO-SIN-01", "Sinalização", "Km 7+100", 3, 3,  9, "Moderado", "Ação em 30 dias"),
            ("CASO-TRI-T4", "Trilho",      "Km 6+700", 4, 4, 16, "Alto",     "Ação em 48 horas"),
        ]

        for codigo, tipo, km, p, c, score, nivel, acao in ativos_caso_pc:
            cor = (C_CRITICO if nivel == "Crítico" else
                   C_ALTO    if nivel == "Alto" else
                   C_MEDIO   if nivel == "Moderado" else C_BAIXO)
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;padding:10px 0;
                        border-bottom:1px solid {BORDER};">
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                            color:{ACCENT2};width:95px;flex-shrink:0;font-weight:600;">
                    {codigo}
                </div>
                <div style="flex:1;">
                    <div style="font-size:0.8rem;font-weight:600;color:{TEXT_PRI};">{tipo} · {km}</div>
                    <div style="font-size:0.72rem;color:{TEXT_MUT};">
                        P={p} × C={c} = <b style="color:{cor};">{score}</b> · {acao}
                    </div>
                </div>
                <span style="background:{cor}22;color:{cor};border:1px solid {cor}44;
                             padding:2px 10px;border-radius:20px;font-size:0.7rem;
                             font-weight:700;white-space:nowrap;">
                    {nivel}
                </span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Análise de Causa Raiz ─────────────────────────────────────────
    bloco("4", "ANÁLISE DE CAUSA RAIZ — FALHA EM CASCATA", "#9B59B6")

    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:14px;
                padding:24px;margin-bottom:16px;">
        <div style="font-size:0.8rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.09em;color:{TEXT_SEC};margin-bottom:18px;
                    display:flex;align-items:center;gap:8px;">
            <div style="width:3px;height:14px;background:#9B59B6;border-radius:2px;"></div>
            Sequência de Deterioração Identificada — Km 7+100 ao 7+300
        </div>
        <!-- Cadeia causal -->
        <div style="display:flex;flex-direction:column;gap:0;">
            <!-- Causa raiz -->
            <div style="background:rgba(230,57,70,0.10);border:1px solid rgba(230,57,70,0.35);
                        border-radius:10px;padding:14px 18px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="background:{C_CRITICO};color:white;padding:4px 10px;
                                 border-radius:6px;font-size:0.72rem;font-weight:800;
                                 flex-shrink:0;">CAUSA RAIZ</span>
                    <div>
                        <div style="font-size:0.88rem;font-weight:700;color:{TEXT_PRI};">
                            Obstrução Severa da Drenagem (Km 7+300)
                        </div>
                        <div style="font-size:0.78rem;color:{TEXT_SEC};margin-top:3px;">
                            Acúmulo de água próximo à plataforma durante chuvas intensas.
                            Das 40 unidades de drenagem inspecionadas, 1 com obstrução severa.
                        </div>
                    </div>
                </div>
            </div>
            <!-- Seta -->
            <div style="text-align:center;padding:6px 0;font-size:1.2rem;color:{TEXT_MUT};">↓</div>
            <!-- Efeito 1 -->
            <div style="background:rgba(230,57,70,0.08);border:1px solid rgba(230,57,70,0.30);
                        border-radius:10px;padding:14px 18px;margin-left:30px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="background:{C_CRITICO}88;color:white;padding:4px 10px;
                                 border-radius:6px;font-size:0.72rem;font-weight:800;
                                 flex-shrink:0;">EFEITO 1</span>
                    <div>
                        <div style="font-size:0.88rem;font-weight:700;color:{TEXT_PRI};">
                            Deterioração dos Dormentes (Km 7+200) — 5 consecutivos severos
                        </div>
                        <div style="font-size:0.78rem;color:{TEXT_SEC};margin-top:3px;">
                            Saturação do lastro e sub-leito → perda de capacidade de suporte →
                            apodrecimento acelerado em curva de raio 500m (geometria exigente).
                        </div>
                    </div>
                </div>
            </div>
            <div style="text-align:center;padding:6px 0;font-size:1.2rem;color:{TEXT_MUT};">↓</div>
            <!-- Efeito 2 -->
            <div style="background:rgba(244,123,53,0.08);border:1px solid rgba(244,123,53,0.30);
                        border-radius:10px;padding:14px 18px;margin-left:60px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="background:{C_ALTO};color:white;padding:4px 10px;
                                 border-radius:6px;font-size:0.72rem;font-weight:800;
                                 flex-shrink:0;">EFEITO 2</span>
                    <div>
                        <div style="font-size:0.88rem;font-weight:700;color:{TEXT_PRI};">
                            Falha em Série das Fixações (Km 7+150–7+250) — 10 consecutivas
                        </div>
                        <div style="font-size:0.78rem;color:{TEXT_SEC};margin-top:3px;">
                            Dormentes deteriorados perdem rigidez → fixações sem suporte adequado →
                            desaperto progressivo. 20 fixações em 500m (concentração 8× acima da média).
                        </div>
                    </div>
                </div>
            </div>
            <div style="text-align:center;padding:6px 0;font-size:1.2rem;color:{TEXT_MUT};">↓</div>
            <!-- Efeito 3 -->
            <div style="background:rgba(244,123,53,0.06);border:1px solid rgba(244,123,53,0.25);
                        border-radius:10px;padding:14px 18px;margin-left:90px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="background:{C_ALTO}88;color:white;padding:4px 10px;
                                 border-radius:6px;font-size:0.72rem;font-weight:800;
                                 flex-shrink:0;">EFEITO 3</span>
                    <div>
                        <div style="font-size:0.88rem;font-weight:700;color:{TEXT_PRI};">
                            AMV-04 Comprometido (Km 7+180) — 6 movimentos/dia a 40 km/h
                        </div>
                        <div style="font-size:0.78rem;color:{TEXT_SEC};margin-top:3px;">
                            Instabilidade geométrica da via → desgaste elevado do AMV →
                            irregularidade no contato roda/trilho sobre via já fragilizada.
                        </div>
                    </div>
                </div>
            </div>
            <div style="text-align:center;padding:6px 0;font-size:1.2rem;color:{TEXT_MUT};">↓</div>
            <!-- Fator agravante -->
            <div style="background:rgba(244,166,42,0.08);border:1px solid rgba(244,166,42,0.30);
                        border-radius:10px;padding:14px 18px;margin-left:30px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="background:{C_MEDIO};color:white;padding:4px 10px;
                                 border-radius:6px;font-size:0.72rem;font-weight:800;
                                 flex-shrink:0;">AGRAVANTE</span>
                    <div>
                        <div style="font-size:0.88rem;font-weight:700;color:{TEXT_PRI};">
                            Sinalização Deficiente (Km 7+100) — perda de visibilidade
                        </div>
                        <div style="font-size:0.78rem;color:{TEXT_SEC};margin-top:3px;">
                            Maquinista não recebe alerta antecipado da área de risco →
                            impossibilidade de redução preventiva de velocidade.
                        </div>
                    </div>
                </div>
            </div>
            <div style="text-align:center;padding:8px 0;font-size:1.2rem;color:{TEXT_MUT};">↓</div>
            <!-- Risco final -->
            <div style="background:rgba(230,57,70,0.15);border:2px solid rgba(230,57,70,0.60);
                        border-radius:10px;padding:16px 18px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <div>
                        <div style="font-size:0.95rem;font-weight:900;color:{C_CRITICO};">
                            RISCO IMINENTE: DESCARRILAMENTO
                        </div>
                        <div style="font-size:0.82rem;color:{TEXT_SEC};margin-top:4px;line-height:1.6;">
                            Alargamento de bitola em curva (R=500m) · Trem de 32,5 t/eixo a 60 km/h ·
                            Via geometricamente instável · Sinalização comprometida.
                            <strong style="color:{C_CRITICO};">Interdição preventiva do Km 7+100–7+300 recomendada.</strong>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Zonas críticas do banco ───────────────────────────────────────
    bloco("5", "ZONAS CRÍTICAS DETECTADAS PELO SISTEMA", ACCENT2)
    df_zc = db.get_all_zonas_criticas()
    if df_zc.empty:
        info("Nenhuma zona crítica registrada. Execute a carga de demonstração em Configurações.")
    else:
        for _, row in df_zc.iterrows():
            cor_z = C_CRITICO if row["nivel_risco_zona"] == "Crítico" else C_ALTO
            r_, g_, b_ = int(cor_z[1:3],16), int(cor_z[3:5],16), int(cor_z[5:7],16)
            st.markdown(f"""
            <div style="background:{CARD_BG};border:1px solid rgba({r_},{g_},{b_},0.45);
                        border-left:5px solid {cor_z};border-radius:12px;
                        padding:18px 22px;margin-bottom:12px;">
                <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;">
                    <div style="flex:1;">
                        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                            <span style="font-family:'JetBrains Mono',monospace;font-size:0.87rem;
                                         color:{ACCENT2};font-weight:700;">
                                {row.get("trecho_codigo","—")}
                            </span>
                            <span style="background:{cor_z}22;color:{cor_z};border:1px solid {cor_z}44;
                                         padding:2px 10px;border-radius:20px;font-size:0.72rem;font-weight:700;">
                                {row["nivel_risco_zona"]}
                            </span>
                            <span style="color:{TEXT_MUT};font-size:0.75rem;font-family:'JetBrains Mono',monospace;">
                                Km {row["km_inicio"]:.3f} → {row["km_fim"]:.3f}
                                &nbsp;({(row["km_fim"]-row["km_inicio"])*1000:.0f} m)
                            </span>
                        </div>
                        <div style="font-size:0.82rem;font-weight:600;color:{TEXT_PRI};margin-bottom:6px;">
                            {row.get("descricao","")}
                        </div>
                        <div style="font-size:0.78rem;color:{TEXT_SEC};line-height:1.6;">
                            <strong style="color:{TEXT_MUT};">Tipos de ativo afetados:</strong>
                            {row.get("tipos_ativo","—")}<br>
                            <strong style="color:{TEXT_MUT};">Causa raiz provável:</strong>
                            {row.get("causa_raiz_provavel","—")}
                        </div>
                    </div>
                    <div style="text-align:center;flex-shrink:0;">
                        <div style="font-size:2rem;font-weight:900;color:{cor_z};line-height:1;">
                            {row.get("score_medio", 0):.0f}
                        </div>
                        <div style="font-size:0.65rem;color:{TEXT_MUT};">Score Médio</div>
                        <div style="margin-top:8px;font-size:1.4rem;font-weight:800;color:{TEXT_PRI};">
                            {row.get("total_defeitos",0)}
                        </div>
                        <div style="font-size:0.65rem;color:{TEXT_MUT};">Defeitos</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Detecção automática sobre os dados atuais ────────────────────
    sdiv("DETECÇÃO AUTOMÁTICA — DADOS ATUAIS DO SISTEMA")
    zonas_vivas = re_.detectar_zonas_criticas(df_at, df_r)
    if not zonas_vivas:
        info("O motor de análise espacial não encontrou concentrações de ≥ 3 ativos "
             "Alto/Crítico numa janela de 500 m com os dados atuais.")
    else:
        mapa_trecho = df_at.drop_duplicates("trecho_id").set_index("trecho_id")["trecho_codigo"].to_dict()
        df_vivas = pd.DataFrame(zonas_vivas)
        df_vivas.insert(0, "trecho", df_vivas["trecho_id"].map(mapa_trecho))
        df_vivas["ativos"] = df_vivas["ativos"].apply(", ".join)
        st.dataframe(
            df_vivas[["trecho", "km_inicio", "km_fim", "total_defeitos", "nivel_risco_zona",
                      "score_medio", "tipos_ativo", "ativos", "causa_raiz_provavel"]],
            width="stretch", hide_index=True,
        )
        chart_insight(
            f"<strong>{len(zonas_vivas)}</strong> zona(s) detectada(s) em tempo real por "
            "<code>detectar_zonas_criticas()</code> — janela deslizante de 500 m por trecho, "
            "considerando o último score de risco de cada ativo."
        )

    # ── Comparação das duas metodologias ─────────────────────────────
    sdiv("COMPARAÇÃO DAS METODOLOGIAS DE RISCO")
    cl, cr = st.columns(2)
    with cl:
        st.markdown(f"""
        <div class="rg-card">
            <div class="rg-card-title">Score Ponderado 0–100 (RailGuard)</div>
            <div style="font-size:0.82rem;color:{TEXT_SEC};line-height:1.7;">
                <strong style="color:{TEXT_PRI};">Base:</strong> Soma ponderada de 9 fatores.<br>
                <strong style="color:{TEXT_PRI};">Vantagem:</strong> Granularidade — varia de 0 a 100,
                sensível a variações contínuas (vibração, idade).<br>
                <strong style="color:{TEXT_PRI};">Limitação:</strong> Pesos são definidos
                subjetivamente — requer validação por especialistas.<br>
                <strong style="color:{TEXT_PRI};">Melhor uso:</strong> Comparação entre ativos,
                tendência de degradação, input para modelo ML.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with cr:
        st.markdown(f"""
        <div class="rg-card">
            <div class="rg-card-title">Matriz P×C (ISO 31000 / ERA)</div>
            <div style="font-size:0.82rem;color:{TEXT_SEC};line-height:1.7;">
                <strong style="color:{TEXT_PRI};">Base:</strong> Probabilidade × Consequência (1–25).<br>
                <strong style="color:{TEXT_PRI};">Vantagem:</strong> Metodologia reconhecida
                internacionalmente, aceita por órgãos reguladores (ANTT, ERA).<br>
                <strong style="color:{TEXT_PRI};">Limitação:</strong> Escala discreta (25 valores) —
                menos precisa para monitoramento contínuo.<br>
                <strong style="color:{TEXT_PRI};">Melhor uso:</strong> Relatórios de compliance,
                priorização de interdições, comunicação com gestores.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  ROTEAMENTO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

_ROTAS = {
    "Dashboard":        page_dashboard,
    "Trechos":          page_trechos,
    "Ativos":           page_ativos,
    "Inspeções":        page_inspecoes,
    "Zona Crítica":     page_zona_critica,
    "Modelo Preditivo": page_ml,
    "Compliance":       page_compliance,
    "Auditoria":        page_auditoria,
    "ESG":              page_esg,
    "Relatórios":       page_relatorios,
    "Configurações":    page_config,
}

pagina_atual = st.session_state.get("pagina", "Dashboard")
mostrar_flash()
_ROTAS.get(pagina_atual, page_dashboard)()
