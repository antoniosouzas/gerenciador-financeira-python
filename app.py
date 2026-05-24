import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
import hashlib
from dotenv import load_dotenv
import io
from fpdf import FPDF
import streamlit.components.v1 as components
import psycopg2
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GFI Financeiro", layout="wide", page_icon="💼", initial_sidebar_state="expanded")

# --- CSS IDÊNTICO AO NOVA DAYS DE REFERÊNCIA ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --sidebar-w: 260px;
    --bg:        #0C0C0C;
    --sidebar:   #1E1E1E;
    --card:      #1E1E1E;
    --card2:     #252525;
    --input-bg:  #252525;
    --accent:    #00FF94; /* Um verde neon para o estilo financeiro moderno */
    --cyan:      #00FF94;
    --blue:      #3b8beb;
    --green:     #00FF94;
    --red:       #FF3B3B;
    --gold:      #FFD700;
    --t1:        #FFFFFF;
    --t2:        #B0B0B0;
    --t3:        #666666;
    --border:    rgba(255,255,255,0.08);
    --r:         20px;
}

/* ── BASE BACKGROUND & LAYOUT ── */
html, body {
    color: var(--t1);
}

/* OCULTA O BOTAO DE RECOLHER A BARRA LATERAL (DEIXA ELA FIXA) E REMOVE O TEXTO BUGADO */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
.st-emotion-cache-1vt4ygl,
.st-emotion-cache-6qob1r,
[kind="header"],
button[title="Collapse sidebar"],
button[title="Expand sidebar"],
.st-emotion-cache-90s44j,
.st-emotion-cache-18ni7ap {
    display: none !important;
    visibility: hidden !important;
}

/* ESCONDE O TOOLBAR/MENU DO STREAMLIT NO CANTO INFERIOR (BOTÃO QUE APARECE NA PRINT) */
[data-testid="stStatusWidget"],
footer + div,
div[data-testid="stStatusWidget"] {
    display: none !important;
}

/* GARANTE QUE A SIDEBAR NÃO POSSA SER RECOLHIDA E FIQUE FIXA */
[data-testid="stSidebar"] {
    min-width: 200px !important;
    max-width: 200px !important;
    transform: none !important;
    transition: none !important;
}
[data-testid="stSidebar"][aria-expanded="false"] {
    margin-left: 0px !important;
}

/* REMOVE DEFINITIVAMENTE O TEXTO BUGADO DO STREAMLIT */
header, [data-testid="stHeader"] {
    display: none !important;
    background: transparent !important;
    color: transparent !important;
    user-select: none !important;
    pointer-events: none !important;
    height: 0px !important;
}
header *, [data-testid="stHeader"] * {
    display: none !important;
}

.stApp { background-color: var(--bg) !important; }

footer { visibility: hidden !important; }
.stAppDeployButton { display: none !important; }

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background-color: var(--sidebar) !important;
    border-right: 1px solid var(--border) !important;
    min-width: 200px !important;
    max-width: 200px !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
    display: flex;
    flex-direction: column;
}
[data-testid="stSidebar"] .block-container {
    padding: 0 !important;
}

/* Brand logo top */
.gfi-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 20px 16px 14px;
    border-bottom: 1px solid var(--border);
}
.gfi-logo-box {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, #3b8beb 0%, #00d4e8 100%);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; font-weight: 800; color: #fff;
    flex-shrink: 0;
    box-shadow: 0 0 16px rgba(0,212,232,0.25);
}
.gfi-brand-name {
    font-size: 0.8rem; font-weight: 700;
    color: var(--t1); letter-spacing: 0.8px;
    text-transform: uppercase; line-height: 1.2;
}
.gfi-brand-sub {
    font-size: 0.62rem; color: var(--t2); letter-spacing: 0.3px;
}

/* Avatar section */
.gfi-avatar-section {
    padding: 16px 16px 12px;
    border-bottom: 1px solid var(--border);
    display: flex; flex-direction: column; align-items: center;
    text-align: center;
}
.gfi-avatar {
    width: 52px; height: 52px; border-radius: 50%;
    background: linear-gradient(135deg, #3b8beb, #00d4e8);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; font-weight: 700; color: #fff;
    margin-bottom: 8px;
    box-shadow: 0 0 0 3px rgba(0,212,232,0.2);
}
.gfi-username { font-size: 0.82rem; font-weight: 600; color: var(--t1); }
.gfi-userrole { font-size: 0.68rem; color: var(--t2); margin-top: 1px; }

/* Section labels */
.gfi-section-lbl {
    font-size: 0.62rem; font-weight: 700;
    color: var(--t3); text-transform: uppercase;
    letter-spacing: 1.2px;
    padding: 14px 16px 6px;
}

/* ── NAV RADIO = sidebar nav ── */
div[role="radiogroup"] {
    gap: 8px !important;
    display: flex !important;
    flex-direction: column !important;
    padding: 12px !important;
}
div[role="radiogroup"] > label {
    background: #151515 !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    border: 1px solid rgba(255,255,255,0.03) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin: 0 !important;
    cursor: pointer;
    width: 100% !important;
    display: block !important;
}
/* Ocultar rádio nativo totalmente */
div[role="radiogroup"] [data-testid="stWidgetSelectionResult"],
div[role="radiogroup"] input[type="radio"] {
    display: none !important;
}
div[role="radiogroup"] > label:hover {
    background: #252525 !important;
    border-color: rgba(255,255,255,0.1) !important;
}
div[role="radiogroup"] > label[data-checked="true"] {
    background: #252525 !important;
    border-color: var(--accent) !important;
    box-shadow: 0 4px 12px rgba(0, 255, 148, 0.05) !important;
}
div[role="radiogroup"] > label[data-checked="true"] p {
    color: var(--accent) !important;
    font-weight: 700 !important;
}
div[role="radiogroup"] > label p {
    color: #888;
    font-size: 0.9rem !important;
    margin: 0 !important;
    transition: color 0.3s;
}

/* ── HORIZONTAL RADIO (Filtros de Tempo) ── */
div[data-testid="stHorizontalBlock"] div[role="radiogroup"] {
    flex-direction: row !important;
    background: #1E1E1E !important;
    padding: 4px !important;
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    width: fit-content !important;
}
div[data-testid="stHorizontalBlock"] div[role="radiogroup"] > label {
    padding: 6px 14px !important;
    border-radius: 7px !important;
    width: auto !important;
}
div[data-testid="stHorizontalBlock"] div[role="radiogroup"] > label[data-checked="true"] {
    background: var(--accent) !important;
}
div[data-testid="stHorizontalBlock"] div[role="radiogroup"] > label[data-checked="true"] p {
    color: #000 !important;
}
div[data-testid="stHorizontalBlock"] div[role="radiogroup"] > label p {
    color: var(--t2) !important; font-weight: 500 !important;
    font-size: 0.85rem !important;
}

/* ── BUTTONS ── */
.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    background: transparent !important;
    color: var(--accent) !important;
    border: 1.5px solid var(--accent) !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.2rem !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    transition: all 0.25s;
    width: 100%;
    font-family: 'Inter', sans-serif !important;
}
.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    background: rgba(162, 233, 229, 0.05) !important;
    transform: translateY(-1px);
}
.stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
    background: var(--accent) !important;
    color: #10141d !important;
    border: none !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 15px rgba(162, 233, 229, 0.2) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #c2f3f0 !important;
    box-shadow: 0 6px 20px rgba(162, 233, 229, 0.3) !important;
}

/* danger button */
.stButton > button[title*="Sair"], .stButton > button[title*="sair"] {
    background: rgba(255,94,108,0.1) !important;
    border-color: rgba(255,94,108,0.2) !important;
    color: var(--red) !important;
}
.stButton > button[title*="Sair"]:hover, .stButton > button[title*="sair"]:hover {
    background: var(--red) !important;
    color: #fff !important;
}

/* ── METRICS ── */
[data-testid="stMetricContainer"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    padding: 24px !important;
    box-shadow: none !important;
}
[data-testid="stMetricContainer"]::after {
    display: none !important; /* Remove a linha de gradiente no topo */
}
[data-testid="stMetricLabel"] p {
    color: var(--t2) !important;
    font-size: 0.85rem !important; font-weight: 500 !important;
    text-transform: none !important; letter-spacing: normal !important;
}
[data-testid="stMetricValue"] div {
    color: var(--t1) !important; font-weight: 700 !important;
    font-size: 1.8rem !important; font-family: 'Inter', sans-serif !important;
    margin-top: 4px;
}

/* ── INPUTS ── */
.stTextInput input,
.stDateInput input,
.stTextArea textarea,
[data-baseweb="input"] input {
    background-color: var(--input-bg) !important;
    color: var(--t1) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
}
.stTextInput input:focus, .stDateInput input:focus {
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 2px rgba(0,212,232,0.15) !important;
}

/* ── SELECTBOX ── */
[data-baseweb="select"] > div {
    background-color: var(--input-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--t1) !important;
}
[data-baseweb="select"] * { color: var(--t1) !important; }
[data-baseweb="menu"] {
    background: var(--card2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
[data-baseweb="option"]:hover { background: rgba(0,212,232,0.08) !important; }

/* ── MULTISELECT ── */
span[data-baseweb="tag"] {
    background: rgba(0,212,232,0.15) !important;
    color: var(--cyan) !important;
    border-radius: 6px !important; font-weight: 600 !important;
    border: 1px solid rgba(0,212,232,0.3) !important;
}

/* ── FORMS ── */
[data-testid="stForm"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    padding: 24px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
}

/* ── DATAFRAME ── */
.stDataFrame {
    border-radius: var(--r) !important;
    border: 1px solid var(--border) !important;
    overflow: hidden;
    background: var(--card) !important;
}
.stDataFrame iframe { background: var(--card) !important; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    padding: 0px !important;
    border-radius: 0px !important;
    gap: 24px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--t2) !important;
    border-radius: 0px !important;
    padding: 10px 4px !important;
    font-weight: 500 !important; font-size: 0.9rem !important;
    font-family: 'Inter', sans-serif !important;
}
.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    font-weight: 700 !important;
}

/* ── ALERTS ── */
.stSuccess { background: rgba(0,200,150,0.08) !important; border-left: 3px solid var(--green) !important; border-radius: 8px !important; }
.stWarning { background: rgba(245,166,35,0.08) !important; border-left: 3px solid var(--gold) !important; border-radius: 8px !important; }
.stError   { background: rgba(255,94,108,0.08) !important; border-left: 3px solid var(--red) !important; border-radius: 8px !important; }
.stInfo    { background: rgba(59,139,235,0.08) !important; border-left: 3px solid var(--blue) !important; border-radius: 8px !important; }
.stAlert { border-radius: 8px !important; }

/* ── EXPANDER ── */
.streamlit-expanderHeader {
    background: var(--card) !important; border-radius: 8px !important;
    color: var(--t1) !important; border: 1px solid var(--border) !important;
}
.streamlit-expanderContent {
    background: var(--card) !important;
    border: 1px solid var(--border) !important; border-top: none !important;
}

/* ── HEADINGS ── */
h1,h2,h3,h4,h5,h6 { color: var(--t1) !important; font-family: 'Inter', sans-serif !important; }
p, span, div { font-family: 'Inter', sans-serif !important; }

/* ── CHECKBOX ── */
.stCheckbox label span { color: var(--t2) !important; }

/* ── DOWNLOAD BUTTON ── */
.stDownloadButton > button {
    background: #1c2333 !important;
    color: var(--t1) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    width: 100%;
    transition: all 0.2s;
    box-shadow: 0 4px 6px rgba(0,0,0,0.4) !important;
}
.stDownloadButton > button:hover {
    background: #252e44 !important;
    transform: translateY(-2px);
    box-shadow: 0 8px 15px rgba(0,0,0,0.5) !important;
}

/* ── RADIO (filters) ── */
.stRadio > div > label > div:last-child { color: var(--t2) !important; }

/* ── SPINNER ── */
.stSpinner > div { border-top-color: var(--cyan) !important; }

/* ── HR ── */
hr { border-color: var(--border) !important; }

/* ── PAGE TITLE ROW ── */
.page-title-row {
    display: flex; align-items: flex-start;
    gap: 12px; padding-bottom: 20px;
    border-bottom: 1px solid var(--border); margin-bottom: 20px;
}
.page-icon-box {
    width: 38px; height: 38px; border-radius: 10px;
    background: linear-gradient(135deg, #3b8beb, #00d4e8);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
}
.page-title-txt { font-size: 1.6rem; font-weight: 800; color: var(--t1); line-height: 1.1; }
.page-subtitle-txt { font-size: 0.8rem; color: var(--t2); margin-top: 2px; }

/* ── PROFILE CARD ── */
.profile-info-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
}
.profile-info-row {
    display: flex; justify-content: space-between;
    align-items: center; padding: 10px 0;
    border-bottom: 1px solid var(--border);
}
.profile-info-row:last-child { border-bottom: none; }
.profile-info-label { font-size: 0.75rem; color: var(--t2); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.profile-info-value { font-size: 0.9rem; color: var(--t1); font-weight: 500; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 3px; }

/* ── LOGIN ── */
.login-wrap {
    display: flex; align-items: center; justify-content: center;
    min-height: 80vh;
}
</style>
""", unsafe_allow_html=True)

load_dotenv()
CLIENT_ID = os.getenv("PLUGGY_CLIENT_ID") or st.secrets.get("PLUGGY_CLIENT_ID")
CLIENT_SECRET = os.getenv("PLUGGY_CLIENT_SECRET") or st.secrets.get("PLUGGY_CLIENT_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL") or st.secrets.get("DATABASE_URL")

defaults = {
    'logado': False, 'usuario_nome': "", 'usuario_id': None,
    'usuario_email': "", 'is_admin': False, 'abrir_pluggy': False,
    'pluggy_sucesso': False, 'pluggy_item_id': ""
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- BANCO DE DADOS ---
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_login(email, senha):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, is_admin FROM usuarios WHERE email = %s AND senha = %s", (email, hash_senha(senha)))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def registrar_usuario(nome, email, senha, is_admin=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (nome, email, senha, is_admin) VALUES (%s, %s, %s, %s)", (nome, email, hash_senha(senha), is_admin))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def buscar_todos_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, email, is_admin, data_cadastro FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios

def deletar_usuario_completo(usuario_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conexoes_bancarias WHERE usuario_id = %s", (usuario_id,))
    cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
    conn.commit()
    conn.close()

def buscar_conexoes_usuario(usuario_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, pluggy_item_id, nome_instituicao, data_conexao FROM conexoes_bancarias WHERE usuario_id = %s', (usuario_id,))
    conexoes = cursor.fetchall()
    conn.close()
    return conexoes

def deletar_conexao(conexao_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conexoes_bancarias WHERE id = %s", (conexao_id,))
    conn.commit()
    conn.close()

def salvar_conexao_por_item_id(usuario_id, item_id):
    item_id = item_id.strip()
    if not item_id: return False, "Item ID vazio."
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM conexoes_bancarias WHERE pluggy_item_id = %s", (item_id,))
        if cursor.fetchone():
            conn.close()
            return False, "Este banco já está sincronizado."
        response = requests.post("https://api.pluggy.ai/auth", json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}, timeout=10)
        token = response.json().get("apiKey")
        headers = {"accept": "application/json", "X-API-KEY": token}
        item_resp = requests.get(f"https://api.pluggy.ai/items/{item_id}", headers=headers, timeout=10)
        nome_banco = item_resp.json().get("connector", {}).get("name", "Banco Desconhecido")
        cursor.execute('INSERT INTO conexoes_bancarias (usuario_id, pluggy_item_id, nome_instituicao) VALUES (%s, %s, %s)', (usuario_id, item_id, nome_banco))
        conn.commit()
        conn.close()
        return True, f"✅ {nome_banco} conectado e salvo com sucesso!"
    except Exception as e: return False, f"Erro ao salvar conexão: {e}"

def sincronizar_ultimo_banco(usuario_id):
    try:
        response = requests.post("https://api.pluggy.ai/auth", json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}, timeout=10)
        token = response.json().get("apiKey")
        headers = {"accept": "application/json", "X-API-KEY": token}
        items_resp = requests.get("https://api.pluggy.ai/items", headers=headers, timeout=10).json()
        resultados = items_resp.get("results", [])
        if not resultados: return False, "Nenhum banco encontrado na Pluggy."
        ultimo_item = resultados[0]
        item_id = ultimo_item.get("id")
        nome_banco = ultimo_item.get("connector", {}).get("name", "Banco Desconhecido")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM conexoes_bancarias WHERE pluggy_item_id = %s", (item_id,))
        if cursor.fetchone():
            conn.close()
            return False, f"O banco {nome_banco} já está sincronizado."
        cursor.execute('INSERT INTO conexoes_bancarias (usuario_id, pluggy_item_id, nome_instituicao) VALUES (%s, %s, %s)', (usuario_id, item_id, nome_banco))
        conn.commit()
        conn.close()
        return True, f"✅ {nome_banco} sincronizado com sucesso!"
    except Exception as e: return False, f"Erro ao comunicar com a Pluggy: {e}"

def gerar_connect_token():
    response = requests.post("https://api.pluggy.ai/auth", json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}, timeout=10)
    api_key = response.json().get("apiKey")
    headers = {"accept": "application/json", "X-API-KEY": api_key}
    response_token = requests.post("https://api.pluggy.ai/connect_token", headers=headers, json={}, timeout=10)
    return response_token.json().get("accessToken")

def atualizar_perfil(usuario_id, nome, email):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE usuarios SET nome = %s, email = %s WHERE id = %s", (nome, email, usuario_id))
        conn.commit()
        return True, "Perfil atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar perfil: {e}"
    finally:
        conn.close()

def trocar_senha_usuario(usuario_id, senha_atual, nova_senha):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE id = %s AND senha = %s", (usuario_id, hash_senha(senha_atual)))
    if not cursor.fetchone():
        conn.close()
        return False, "Senha atual incorreta."
    cursor.execute("UPDATE usuarios SET senha = %s WHERE id = %s", (hash_senha(nova_senha), usuario_id))
    conn.commit()
    conn.close()
    return True, "Senha alterada com sucesso!"

def buscar_dados_usuario(usuario_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, email, is_admin, data_cadastro FROM usuarios WHERE id = %s", (usuario_id,))
        u = cursor.fetchone()
        conn.close()
        return u
    except:
        return None

@st.cache_data(ttl=3600)
def buscar_dados_reais(item_id):
    try:
        response = requests.post("https://api.pluggy.ai/auth", json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}, timeout=10)
        token = response.json().get("apiKey")
        headers = {"accept": "application/json", "X-API-KEY": token}
        contas_resp = requests.get(f"https://api.pluggy.ai/accounts?itemId={item_id}", headers=headers, timeout=10).json()
        contas = contas_resp.get("results", [])
        if not contas: return "SEM_CONTAS", []
        info_contas = []
        for c in contas:
            info_contas.append({"nome": c.get("name","Conta"), "tipo": c.get("type",""), "saldo": c.get("balance",0), "id": c.get("id")})
        conta_id = contas[0].get("id")
        trans_resp = requests.get(f"https://api.pluggy.ai/transactions?accountId={conta_id}&pageSize=500", headers=headers, timeout=15).json()
        return trans_resp.get("results", []), info_contas
    except Exception as e: return "ERRO_DADOS", []

TRADUCAO_CATEGORIAS = {
    'TRANSFER - PIX': 'Transferência PIX','TRANSFERS': 'Transferências','DIGITAL SERVICES': 'Serviços Digitais',
    'FOOD DELIVERY': 'Delivery de Comida','BOOKSTORE': 'Livraria','ONLINE SHOPPING': 'Compras Online',
    'TELECOMMUNICATIONS': 'Telecomunicações','EATING OUT': 'Restaurantes','GAS STATIONS': 'Posto de Combustível',
    'LEISURE': 'Lazer','LATE PAYMENT AND OVERDRAFT COSTS': 'Juros e Multas','TAX ON FINANCIAL OPERATIONS': 'Impostos (IOF/Taxas)',
    'COMPRAS': 'Compras','SUPERMERCADO': 'Supermercado','TRANSPORTE': 'Transporte','INTERNET': 'Internet',
    'FOOD_AND_DRINK': 'Alimentação','FOOD AND DRINK': 'Alimentação','RESTAURANT': 'Restaurante','GROCERIES': 'Supermercado',
    'COFFEE': 'Cafeteria','HOME': 'Casa','RENT': 'Aluguel','MORTGAGE': 'Hipoteca','UTILITIES': 'Contas de Casa',
    'ELECTRICITY': 'Energia Elétrica','WATER': 'Água','TRANSPORTATION': 'Transporte','GAS_STATION': 'Posto de Combustível',
    'GAS': 'Combustível','PARKING': 'Estacionamento','PUBLIC_TRANSIT': 'Transporte Público','HEALTHCARE': 'Saúde',
    'PHARMACY': 'Farmácia','DOCTOR': 'Médico/Clínica','PERSONAL_CARE': 'Cuidados Pessoais','GYM': 'Academia',
    'ENTERTAINMENT': 'Lazer e Entretenimento','SUBSCRIPTIONS': 'Assinaturas','SHOPPING': 'Compras','CLOTHING': 'Roupas',
    'ELECTRONICS': 'Eletrônicos','EDUCATION': 'Educação','TRAVEL': 'Viagem','INCOME': 'Renda','SALARY': 'Salário',
    'TRANSFER': 'Transferência','INTERNAL_TRANSFER': 'Transferência Interna','PAYMENT': 'Pagamento',
    'CREDIT_CARD_PAYMENT': 'Pagamento de Fatura','INVESTMENT': 'Investimento','BANK_FEES': 'Tarifas Bancárias',
    'CREDIT_CARD': 'Cartão de Crédito','LOAN': 'Empréstimo','INSURANCE': 'Seguro','TAXES': 'Impostos',
    'DEPOSIT': 'Depósito','UNCATEGORIZED': 'Outros','OTHER': 'Outros'
}

def traduzir_categoria(cat_raw):
    if cat_raw is None: return 'Outros'
    if isinstance(cat_raw, dict): cat_raw = cat_raw.get('description', cat_raw.get('name','UNCATEGORIZED'))
    cat_str = str(cat_raw).upper().strip()
    if cat_str in TRADUCAO_CATEGORIAS: return TRADUCAO_CATEGORIAS[cat_str]
    cat_str_under = cat_str.replace(' - ','_').replace('-','_').replace(' ','_')
    if cat_str_under in TRADUCAO_CATEGORIAS: return TRADUCAO_CATEGORIAS[cat_str_under]
    cat_str_espaco = cat_str.replace('_',' ')
    if cat_str_espaco in TRADUCAO_CATEGORIAS: return TRADUCAO_CATEGORIAS[cat_str_espaco]
    return cat_str_espaco.title() if cat_str else 'Outros'

def gerar_excel(df, total_in, total_out, saldo, total_cartao):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        wb = writer.book
        fmt_titulo    = wb.add_format({'bold':True,'font_size':14,'font_color':'#FFFFFF','bg_color':'#0288d1','align':'center','valign':'vcenter'})
        fmt_header    = wb.add_format({'bold':True,'font_color':'#FFFFFF','bg_color':'#039be5','align':'center','valign':'vcenter','border':1,'font_size':11})
        fmt_resumo_k  = wb.add_format({'bold':True,'font_color':'#2c3e50','bg_color':'#e1f5fe','border':1,'font_size':11})
        fmt_resumo_v  = wb.add_format({'num_format':'R$ #,##0.00','border':1,'font_size':11,'align':'right'})
        fmt_entrada   = wb.add_format({'bg_color':'#e8f5e9','font_color':'#2e7d32','border':1,'font_size':10})
        fmt_saida     = wb.add_format({'bg_color':'#ffebee','font_color':'#c62828','border':1,'font_size':10})
        fmt_moeda_in  = wb.add_format({'num_format':'R$ #,##0.00','bg_color':'#e8f5e9','font_color':'#2e7d32','border':1,'font_size':10,'align':'right'})
        fmt_moeda_out = wb.add_format({'num_format':'R$ #,##0.00','bg_color':'#ffebee','font_color':'#c62828','border':1,'font_size':10,'align':'right'})
        ws_res = wb.add_worksheet('Resumo')
        ws_res.set_column('A:A',28); ws_res.set_column('B:B',20); ws_res.set_row(0,30)
        ws_res.merge_range('A1:B1','Resumo Financeiro',fmt_titulo)
        resumo_dados = [('Total de Entradas',total_in),('Total de Saídas',total_out),('Gastos Cartão de Crédito',total_cartao),('Saldo Líquido',saldo),('Número de Transações',len(df))]
        for i,(label,val) in enumerate(resumo_dados,start=1):
            ws_res.write(i,0,label,fmt_resumo_k)
            if isinstance(val,int): ws_res.write(i,1,val,wb.add_format({'border':1,'font_size':11,'align':'right'}))
            else: ws_res.write(i,1,val,fmt_resumo_v)
        ws = wb.add_worksheet('Extrato')
        ws.set_column('A:A',14); ws.set_column('B:B',48); ws.set_column('C:C',16); ws.set_column('D:D',12); ws.set_column('E:E',22); ws.set_row(0,22)
        colunas = list(df.columns)
        for col_idx,col_name in enumerate(colunas): ws.write(0,col_idx,col_name,fmt_header)
        for row_idx,(_,row) in enumerate(df.iterrows(),start=1):
            is_entrada = str(row.get('Tipo','')).strip()=='Entrada'
            fmt_txt = fmt_entrada if is_entrada else fmt_saida
            fmt_val = fmt_moeda_in if is_entrada else fmt_moeda_out
            for col_idx,col_name in enumerate(colunas):
                val = row[col_name]
                if col_name=='Valor (R$)':
                    try: ws.write(row_idx,col_idx,float(val),fmt_val)
                    except: ws.write(row_idx,col_idx,0,fmt_val)
                else: ws.write(row_idx,col_idx,str(val) if val is not None else '',fmt_txt)
        ws.freeze_panes(1,0)
    output.seek(0)
    return output.getvalue()

def gerar_pdf(df, total_in, total_out, saldo, total_cartao):
    pdf = FPDF(orientation='L',unit='mm',format='A4'); pdf.set_auto_page_break(auto=True,margin=12); pdf.add_page()
    largura_pagina = 277
    data_fim = df['Data'].iloc[0].strftime('%Y-%m-%d') if not df.empty else 'N/A'
    data_inicio = df['Data'].iloc[-1].strftime('%Y-%m-%d') if not df.empty else 'N/A'
    pdf.set_fill_color(2,136,209); pdf.set_text_color(255,255,255); pdf.set_font("helvetica",'B',16)
    pdf.cell(largura_pagina,12,"GFI Financeiro - Relatorio Financeiro",ln=False,align='C',fill=True); pdf.ln(12)
    pdf.set_font("helvetica",'',9); pdf.set_text_color(100,116,139)
    pdf.cell(largura_pagina,6,f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}  |  Período: {data_inicio} a {data_fim}",ln=True,align='C'); pdf.ln(4)
    pdf.set_font("helvetica",'B',10); pdf.set_fill_color(3,169,244); pdf.set_text_color(255,255,255)
    pdf.cell(largura_pagina,8,"  Resumo do Período",ln=True,fill=True); pdf.ln(1)
    resumo=[("Total de Entradas",f"R$ {total_in:,.2f}",(209,250,229),(6,95,70)),("Total de Saídas",f"R$ {total_out:,.2f}",(254,226,226),(127,29,29)),("Cartão de Crédito",f"R$ {total_cartao:,.2f}",(254,215,170),(154,52,18)),("Saldo Líquido",f"R$ {saldo:,.2f}",(225,245,254),(2,136,209)),("Transações",f"{len(df)}",(248,250,252),(51,65,85))]
    col_w = largura_pagina/2
    for i in range(0,len(resumo),2):
        for j in range(2):
            if i+j<len(resumo):
                label,valor,bg,fg=resumo[i+j]; pdf.set_fill_color(*bg); pdf.set_draw_color(203,213,225); pdf.set_text_color(*fg)
                pdf.set_font("helvetica",'B',9); pdf.cell(col_w*0.55,7,f"  {label}",border=1,fill=True)
                pdf.set_font("helvetica",'',9); pdf.cell(col_w*0.45,7,f"  {valor}",border=1,fill=True,align='R')
        pdf.ln()
    pdf.ln(4)
    pdf.set_font("helvetica",'B',10); pdf.set_fill_color(3,169,244); pdf.set_text_color(255,255,255)
    pdf.cell(largura_pagina,8,f"  Extrato de Transações ({len(df)} registros)",ln=True,fill=True); pdf.ln(1)
    col_widths=[24,98,28,22,42,30]; headers=list(df.columns)
    col_widths=col_widths[:len(headers)]
    while len(col_widths)<len(headers): col_widths.append(30)
    pdf.set_font("helvetica",'B',8); pdf.set_fill_color(38,50,56); pdf.set_text_color(226,232,240); pdf.set_draw_color(207,216,220)
    for h,w in zip(headers,col_widths): pdf.cell(w,7,f" {h}",border=1,fill=True)
    pdf.ln(); pdf.set_font("helvetica",'',8); pdf.set_draw_color(207,216,220)
    for i,row in enumerate(df.itertuples(index=False)):
        tipo=str(getattr(row,'Tipo','')).strip(); is_entrada=tipo=='Entrada'
        if is_entrada: pdf.set_fill_color(200,230,201); pdf.set_text_color(46,125,50)
        elif i%2==0: pdf.set_fill_color(248,250,252); pdf.set_text_color(38,50,56)
        else: pdf.set_fill_color(241,245,249); pdf.set_text_color(38,50,56)
        if pdf.get_y()>185:
            pdf.add_page(); pdf.set_font("helvetica",'B',8); pdf.set_fill_color(38,50,56); pdf.set_text_color(226,232,240)
            for h,w in zip(headers,col_widths): pdf.cell(w,7,f" {h}",border=1,fill=True)
            pdf.ln(); pdf.set_font("helvetica",'',8)
            if is_entrada: pdf.set_fill_color(200,230,201); pdf.set_text_color(46,125,50)
            elif i%2==0: pdf.set_fill_color(248,250,252); pdf.set_text_color(38,50,56)
            else: pdf.set_fill_color(241,245,249); pdf.set_text_color(38,50,56)
        valores=list(row)
        for val,w in zip(valores,col_widths):
            txt=str(val) if val is not None else ''
            while pdf.get_string_width(f" {txt}")>w-2 and len(txt)>3: txt=txt[:-1]
            if len(str(val) if val is not None else '')>len(txt): txt=txt[:-1]+'...'
            pdf.cell(w,6,f" {txt}",border=1,fill=True)
        pdf.ln()
    pdf.ln(4); pdf.set_font("helvetica",'I',8); pdf.set_text_color(148,163,184)
    pdf.cell(largura_pagina,5,"Documento gerado automaticamente pelo GFI Financeiro.",align='C')
    return bytes(pdf.output())

# ==========================================
# LOGIN
# ==========================================
if not st.session_state['logado']:
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)

        # Logo
        st.markdown("""
        <div style='text-align:center; margin-bottom:28px;'>
            <div style='
                width:60px;height:60px;
                background:linear-gradient(135deg,#3b8beb,#00d4e8);
                border-radius:16px; margin:0 auto 14px;
                display:flex;align-items:center;justify-content:center;
                font-size:28px; box-shadow:0 0 32px rgba(0,212,232,0.3);
            '>💼</div>
            <div style='font-size:1.5rem;font-weight:800;color:#e8edf5;letter-spacing:-0.5px;'>GFI Financeiro</div>
            <div style='font-size:0.85rem;color:#8896b0;margin-top:4px;'>Gestão Financeira Inteligente</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("E-mail", placeholder="seu@email.com")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.form_submit_button("ENTRAR", type="primary"):
                if email == "admin" and senha == "admin":
                    st.session_state.update({'logado':True,'usuario_id':999,'usuario_nome':"Administrador Mestre",'usuario_email':"admin@gfi.com",'is_admin':True})
                    st.rerun()
                else:
                    usuario = verificar_login(email, senha)
                    if usuario:
                        st.session_state.update({'logado':True,'usuario_id':usuario[0],'usuario_nome':usuario[1],'usuario_email':email,'is_admin':bool(usuario[2])})
                        st.rerun()
                    else:
                        st.error("Acesso negado. Verifique os seus dados.")

# ==========================================
# ÁREA LOGADA
# ==========================================
else:
    nome_display = st.session_state['usuario_nome'].split()[0]
    inicial = st.session_state['usuario_nome'][0].upper()

    with st.sidebar:
        # ── BRAND ──
        st.markdown(f"""
        <div style='padding: 20px 0 40px 0;'>
            <div style='color: white; font-weight: 900; font-size: 1.4rem; letter-spacing: 1px; font-family: "Inter", sans-serif;'>
                FINANCE <span style="color: var(--accent);">DASHBOARD</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── NAV ──
        st.markdown('<div class="gfi-section-lbl" style="margin-bottom: 8px;">MENU PRINCIPAL</div>', unsafe_allow_html=True)

        # Mapeamento do menu conforme pedido
        nav_options = [
            "📊 Resumo Financeiro",
            "🏦 Bancos",
            "👤 Perfil"
        ]

        # Adicionar Admin apenas se for admin
        if st.session_state['is_admin']:
            nav_options.append("🛡️ Admin")

        menu = st.radio("nav", nav_options, label_visibility="collapsed")

        st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)

        # ── USER PROFILE CARD AT BOTTOM ──
        st.markdown(f"""
        <div style='
            background: #252525;
            border-radius: 16px;
            padding: 16px;
            margin: 20px 10px;
            display: flex;
            align-items: center;
            gap: 12px;
            border: 1px solid var(--border);
        '>
            <div style='
                width: 40px; height: 40px; border-radius: 10px;
                background: var(--accent);
                display: flex; align-items: center; justify-content: center;
                font-weight: 800; color: #000; font-size: 1.1rem;
            '>{st.session_state['usuario_nome'][0].upper()}</div>
            <div style='overflow: hidden;'>
                <div style='color: white; font-weight: 600; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{st.session_state['usuario_nome']}</div>
                <div style='color: #888; font-size: 0.7rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{st.session_state['usuario_email']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.update({'logado':False,'is_admin':False})
            st.rerun()

    # ==========================================
    # PÁGINAS
    # ==========================================

    # ── ADMIN ──
    if menu == "🛡️ Admin":
        st.markdown("""
        <div class='page-title-row'>
            <div>
                <div class='page-title-txt'>Painel de Controle</div>
                <div class='page-subtitle-txt'>Gestão de clientes e configurações</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_add, tab_lista = st.tabs(["➕ Novo Cliente", "👥 Gerir Clientes"])
        with tab_add:
            with st.form("add_user"):
                n = st.text_input("Nome")
                e = st.text_input("E-mail")
                p = st.text_input("Senha", type="password")
                adm = st.checkbox("Dar acesso de Administrador?")
                if st.form_submit_button("Criar Conta do Cliente", type="primary"):
                    if n and e and p:
                        if registrar_usuario(n, e, p, adm): st.success(f"Cliente {n} criado!")
                        else: st.error("Erro ao criar. O e-mail já existe?")
        with tab_lista:
            for u in buscar_todos_usuarios():
                with st.expander(f"👤 {u[1]} ({u[2]})"):
                    st.markdown(f"<span style='color:#8896b0;font-size:0.8rem;'>Admin: {'Sim' if u[3] else 'Não'} | Cadastro: {u[4]}</span>", unsafe_allow_html=True)
                    if u[0] != st.session_state['usuario_id']:
                        if st.button("🗑 Eliminar Conta", key=f"del_{u[0]}"):
                            deletar_usuario_completo(u[0])
                            st.rerun()

    # ── MEU PERFIL ──
    elif menu == "👤 Perfil":
        st.markdown("""
        <div class='page-title-row'>
            <div>
                <div class='page-title-txt'>Meu Perfil</div>
                <div class='page-subtitle-txt'>Gerencie suas informações e segurança</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_prof, col_edit, col_pass = st.columns([1, 1, 1])

        # Tentar buscar dados reais do DB, fallback ao session_state
        dados_usuario = None
        if st.session_state['usuario_id'] != 999:
            dados_usuario = buscar_dados_usuario(st.session_state['usuario_id'])

        nome_exib  = dados_usuario[1] if dados_usuario else st.session_state['usuario_nome']
        email_exib = dados_usuario[2] if dados_usuario else st.session_state.get('usuario_email', 'N/A')
        admin_exib = "✅ Sim" if (dados_usuario[3] if dados_usuario else st.session_state['is_admin']) else "❌ Não"
        cad_exib   = str(dados_usuario[4])[:10] if dados_usuario and dados_usuario[4] else "N/A"

        with col_prof:
            st.markdown("<h5 style='color:#e8edf5;margin-bottom:12px;'>📋 Dados Atuais</h5>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="profile-info-card">
                <div style='display:flex;align-items:center;gap:16px;margin-bottom:20px;'>
                    <div style='
                        width:64px;height:64px;border-radius:50%;
                        background:var(--accent);
                        display:flex;align-items:center;justify-content:center;
                        font-size:26px;font-weight:700;color:#000;
                    '>{nome_exib[0].upper()}</div>
                    <div>
                        <div style='font-size:1.1rem;font-weight:700;color:#e8edf5;'>{nome_exib}</div>
                        <div style='font-size:0.78rem;color:#8896b0;margin-top:2px;'>{'🔑 Administrador' if st.session_state['is_admin'] else '👤 Usuário'}</div>
                    </div>
                </div>
                <div class="profile-info-row">
                    <span class="profile-info-label">E-mail</span>
                    <span class="profile-info-value">{email_exib}</span>
                </div>
                <div class="profile-info-row">
                    <span class="profile-info-label">Cadastro</span>
                    <span class="profile-info-value">{cad_exib}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_edit:
            st.markdown("<h5 style='color:#e8edf5;margin-bottom:12px;'>✏️ Editar Perfil</h5>", unsafe_allow_html=True)
            with st.form("form_editar_perfil"):
                novo_nome = st.text_input("Nome", value=nome_exib)
                novo_email = st.text_input("E-mail", value=email_exib)
                if st.form_submit_button("Atualizar Dados", type="primary"):
                    if novo_nome and novo_email:
                        sucesso, msg = atualizar_perfil(st.session_state['usuario_id'], novo_nome, novo_email)
                        if sucesso:
                            st.session_state['usuario_nome'] = novo_nome
                            st.session_state['usuario_email'] = novo_email
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Preencha todos os campos.")

        with col_pass:
            st.markdown("<h5 style='color:#e8edf5;margin-bottom:12px;'>🔒 Segurança</h5>", unsafe_allow_html=True)
            if st.session_state['usuario_id'] == 999:
                st.info("Administrador mestre.")
            else:
                with st.form("form_trocar_senha"):
                    s_atual = st.text_input("Senha Atual", type="password")
                    s_nova = st.text_input("Nova Senha", type="password")
                    s_conf = st.text_input("Confirmar", type="password")
                    if st.form_submit_button("Alterar Senha"):
                        if s_nova == s_conf and len(s_nova) >= 6:
                            ok, msg = trocar_senha_usuario(st.session_state['usuario_id'], s_atual, s_nova)
                            if ok: st.success(msg)
                            else: st.error(msg)
                        else:
                            st.error("Senhas não coincidem ou muito curta.")

    # ── MEUS BANCOS ──
    elif menu == "🏦 Bancos":
        st.markdown("""
        <div class='page-title-row'>
            <div>
                <div class='page-title-txt'>Minhas Conexões</div>
                <div class='page-subtitle-txt'>Sincronize suas contas bancárias via Pluggy</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_txt, col_btn = st.columns([3, 1])
        with col_btn:
            if st.button("➕ Conectar Novo Banco", type="primary"):
                st.session_state['abrir_pluggy'] = True
                st.session_state['pluggy_sucesso'] = False
                st.session_state['pluggy_item_id'] = ""

        if st.session_state['abrir_pluggy'] and not st.session_state['pluggy_sucesso']:
            token = gerar_connect_token()
            if token:
                if st.button("✖ Fechar Janela"):
                    st.session_state['abrir_pluggy'] = False
                    st.rerun()

                components.html(f"""
<!DOCTYPE html><html><head>
<style>
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0');
* {{ box-sizing:border-box;margin:0;padding:0; }}
body {{ background:transparent;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }}
#widget-area {{ min-height:460px; }}
#success-box {{ display:none;background:rgba(0,200,150,0.1);border:1px solid #00c896;border-radius:12px;padding:32px 24px;margin:16px 0;text-align:center; }}
#success-box h2 {{ color:#00c896;font-size:1.3rem;margin-bottom:8px; }}
#success-box p {{ color:#8896b0;font-size:0.95rem;margin-bottom:20px; }}
#id-display {{ background:#1a2035;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:14px 16px;font-family:monospace;font-size:0.9rem;color:#00d4e8;word-break:break-all;margin-bottom:16px;text-align:left; }}
#copy-btn {{ background:linear-gradient(135deg,#3b8beb,#00d4e8);color:#0e1117;border:none;border-radius:20px;padding:10px 28px;font-size:0.95rem;cursor:pointer;font-weight:700; }}
#copy-hint {{ color:#00c896;font-size:0.85rem;margin-top:10px;display:none; }}
</style></head><body>
<div id="widget-area"></div>
<div id="success-box">
  <h2>✅ Banco conectado!</h2>
  <p>Copie o ID abaixo e cole no campo:</p>
  <div id="id-display">Aguardando...</div>
  <button id="copy-btn" onclick="copiarID()">📋 Copiar ID</button>
  <p id="copy-hint">✓ Copiado!</p>
</div>
<script src="https://cdn.pluggy.ai/pluggy-connect/v2.8.2/pluggy-connect.js"></script>
<script>
var capturedItemId='';
function copiarID(){{navigator.clipboard.writeText(capturedItemId).then(function(){{document.getElementById('copy-hint').style.display='block';document.getElementById('copy-btn').textContent='✓ Copiado!';}}); }}
var connect=new PluggyConnect({{connectToken:'{token}',onSuccess:function(data){{capturedItemId=data.item.id;document.getElementById('widget-area').style.display='none';document.getElementById('id-display').textContent=capturedItemId;document.getElementById('success-box').style.display='block';}},onClose:function(){{document.getElementById('widget-area').innerHTML='<p style="color:#8896b0;text-align:center;padding:60px;">Conexão encerrada.</p>';}},onError:function(err){{document.getElementById('widget-area').innerHTML='<p style="color:#ff5e6c;text-align:center;padding:60px;">Erro na conexão.</p>';}} }});
connect.init();
</script></body></html>
""", height=540)

                st.markdown("<p style='color:#8896b0;font-size:0.85rem;margin-top:8px;'>👆 Após conectar, copie o ID e cole aqui:</p>", unsafe_allow_html=True)
                item_id_input = st.text_input("ID da Conexão", placeholder="Cole o ID aqui...", label_visibility="collapsed")
                if st.button("💾 Salvar Conexão", type="primary", disabled=not item_id_input.strip()):
                    with st.spinner("Salvando..."):
                        sucesso, msg = salvar_conexao_por_item_id(st.session_state['usuario_id'], item_id_input)
                    if sucesso:
                        st.session_state.update({'pluggy_sucesso':True,'pluggy_item_id':item_id_input.strip(),'abrir_pluggy':False})
                        st.success(msg); st.rerun()
                    else:
                        st.warning(msg)

        if st.session_state['pluggy_sucesso']:
            st.success("🎉 Banco conectado! Acesse o Dashboard para ver os dados.")

        st.markdown("<hr>", unsafe_allow_html=True)
        c_b1, c_b2 = st.columns([3, 1])
        c_b1.markdown("#### 🏦 Bancos Ativos")
        if c_b2.button("🔄 Sincronizar", type="primary"):
            with st.spinner("Comunicando com Pluggy..."):
                sucesso, msg = sincronizar_ultimo_banco(st.session_state['usuario_id'])
            if sucesso: st.success(msg); st.rerun()
            else: st.warning(msg)

        conexoes = buscar_conexoes_usuario(st.session_state['usuario_id'])
        if not conexoes:
            st.info("Nenhum banco sincronizado ainda.")
        else:
            for i, cx in enumerate(conexoes):
                c1, c2 = st.columns([7, 1])
                c1.info(f"🏦 {cx[2]} | ID: {cx[1][:15]}...")
                if c2.button("🗑", key=f"del_cx_{i}"):
                    deletar_conexao(cx[0]); st.rerun()

 # ── DASHBOARD & OTHERS ──
    elif menu == "📊 Resumo Financeiro":
        st.markdown(f"""
        <div class='page-title-row'>
            <div>
                <div class='page-title-txt'>Resumo Financeiro</div>
                <div class='page-subtitle-txt'>{"Hoje é " + datetime.now().strftime("%A, %d de %B de %Y.")}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        conexoes = buscar_conexoes_usuario(st.session_state['usuario_id'])
        if not conexoes:
            st.warning("Nenhum banco conectado. Vá em '🏦 Bancos' para começar.")
        else:
            bancos_dict = {f"{c[2]} ({c[1][:5]})": c[1] for c in conexoes}

            c_sel1, c_sel2 = st.columns([2, 1])
            sel_banco = c_sel1.selectbox("🏦 Instituição Bancária:", list(bancos_dict.keys()))

            with st.spinner("Sincronizando dados com a Pluggy..."):
                resultado = buscar_dados_reais(bancos_dict[sel_banco])

            if resultado[0] == "SEM_CONTAS":
                st.warning("Este banco não possui contas associadas ainda.")
            elif resultado[0] == "ERRO_DADOS":
                st.error("Não foi possível carregar os dados. Tente novamente.")
            else:
                trans, info_contas = resultado

                if not trans:
                    st.info("Nenhuma transação encontrada.")
                else:
                    # 1. PREPARAR OS DADOS
                    for t in trans:
                        desc_original = str(t.get('description','')).strip()
                        nome_extra = ""
                        amount = float(t.get('amount',0)) if t.get('amount') is not None else 0
                        if isinstance(t.get('merchant'),dict):
                            nome_extra = t['merchant'].get('name','') or t['merchant'].get('businessName','')
                        if not nome_extra and isinstance(t.get('paymentData'),dict):
                            pdata = t['paymentData']
                            if amount < 0:
                                nome_extra = pdata.get('receiverName','') or (pdata.get('payee',{}).get('name','') if isinstance(pdata.get('payee'),dict) else '')
                            else:
                                nome_extra = pdata.get('payerName','') or (pdata.get('payer',{}).get('name','') if isinstance(pdata.get('payer'),dict) else '')
                        t['descricao_completa'] = f"{desc_original} ({str(nome_extra).title()[:30]})" if nome_extra else desc_original

                    df = pd.DataFrame(trans)
                    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
                    df['amount'] = pd.to_numeric(df['amount'],errors='coerce').fillna(0)
                    df['tipo'] = df['amount'].apply(lambda x: 'Entrada' if x>0 else 'Saída')
                    df['valor_abs'] = df['amount'].abs()
                    df['categoria'] = df.get('category','Outros').apply(traduzir_categoria) if 'category' in df.columns else 'Outros'

                    # 2. FILTROS (DATAS E CATEGORIAS)
                    st.markdown("<hr style='border-color:rgba(255,255,255,0.05); margin-top: 0px;'>", unsafe_allow_html=True)
                    col_f1, col_f2 = st.columns([1.2, 1]) 
                    
                    with col_f1:
                        c_data_inicio, c_data_fim = st.columns(2)
                        data_atual = datetime.now()
                        data_inicio_padrao = data_atual - pd.Timedelta(days=30)
                        
                        data_inicio_selecionada = c_data_inicio.date_input("📅 Data Início:", value=data_inicio_padrao, max_value=data_atual)
                        data_fim_selecionada = c_data_fim.date_input("📅 Data Fim:", value=data_atual, max_value=data_atual)
                        
                    with col_f2:
                        lista_categorias = ["Todas as Categorias"] + sorted(list(df['categoria'].unique()))
                        cat_selecionada = st.selectbox("🏷️ Filtrar Categoria:", lista_categorias)

                    # 3. APLICAR FILTROS NO DATAFRAME
                    start_date = pd.to_datetime(data_inicio_selecionada)
                    end_date = pd.to_datetime(data_fim_selecionada) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

                    df_f = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
                    if cat_selecionada != "Todas as Categorias":
                        df_f = df_f[df_f['categoria'] == cat_selecionada]

                    # 4. CORREÇÃO DA LÓGICA DO SALDO
                    conta_ativa = info_contas[0] if info_contas else {}
                    saldo_real_atual = conta_ativa.get('saldo', 0)
                    is_credit_card = conta_ativa.get('tipo') == 'CREDIT_CARD'
                    nome_conta_ativa = conta_ativa.get('nome', 'Conta')

                    total_faturas = saldo_real_atual if is_credit_card else 0

                    entradas = df_f[df_f['tipo']=='Entrada']['valor_abs'].sum()
                    saidas = df_f[df_f['tipo']=='Saída']['valor_abs'].sum()

                    # 5. MARKET OVERVIEW TOP CARDS
                    st.markdown("""
                    <style>
                    .market-card { background: #1E1E1E; border-radius: 20px; padding: 24px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 20px; }
                    .market-label { color: #888; font-size: 0.75rem; font-weight: 600; margin-bottom: 6px; text-transform: uppercase; }
                    .market-value { color: #FFF; font-size: 1.4rem; font-weight: 800; }
                    .market-change { font-size: 0.75rem; font-weight: 600; margin-top: 4px; }
                    .up { color: #00FF94; } .down { color: #FF3B3B; } .neutral { color: #FFD700; }
                    </style>
                    """, unsafe_allow_html=True)

                    c1, c2, c3, c4 = st.columns(4)
                    
                    if is_credit_card:
                        c1.markdown(f'<div class="market-card"><div class="market-label">FATURA ATUAL ({nome_conta_ativa})</div><div class="market-value">R$ {abs(saldo_real_atual):,.2f}</div><div class="market-change neutral">Cartão de Crédito</div></div>', unsafe_allow_html=True)
                    else:
                        c1.markdown(f'<div class="market-card"><div class="market-label">SALDO EM CONTA ({nome_conta_ativa})</div><div class="market-value">R$ {saldo_real_atual:,.2f}</div><div class="market-change up">Liquidez Real</div></div>', unsafe_allow_html=True)
                        
                    c2.markdown(f'<div class="market-card"><div class="market-label">ENTRADAS</div><div class="market-value">R$ {entradas:,.2f}</div><div class="market-change up">No período filtrado</div></div>', unsafe_allow_html=True)
                    c3.markdown(f'<div class="market-card"><div class="market-label">SAÍDAS</div><div class="market-value">R$ {saidas:,.2f}</div><div class="market-change down">No período filtrado</div></div>', unsafe_allow_html=True)
                    c4.markdown(f'<div class="market-card"><div class="market-label">TRANSAÇÕES</div><div class="market-value">{len(df_f)}</div><div class="market-change up">Volume no período</div></div>', unsafe_allow_html=True)

                    # 6. MAIN CHART - Substituindo Candlestick por Gráfico de Barras (Fluxo Diário)
                    if not df_f.empty:
                        st.markdown("<div class='market-card' style='padding: 20px;'>", unsafe_allow_html=True)
                        st.markdown(f"<h5 style='margin-bottom:20px;'>📈 Fluxo Diário (Entradas vs Saídas)</h5>", unsafe_allow_html=True)

                        df_fluxo = df_f.copy()
                        df_fluxo['Data'] = df_fluxo['date'].dt.date
                        df_g = df_fluxo.groupby(['Data', 'tipo'])['valor_abs'].sum().reset_index()
                        
                        fig_fluxo = px.bar(
                            df_g, x='Data', y='valor_abs', color='tipo', barmode='group',
                            color_discrete_map={'Entrada': '#00FF94', 'Saída': '#FF3B3B'},
                            labels={'valor_abs': 'Valor (R$)', 'Data': '', 'tipo': 'Tipo'}
                        )
                        fig_fluxo.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            margin=dict(t=0,b=0,l=0,r=0), height=350,
                            xaxis=dict(showgrid=False, tickfont=dict(color='white')),
                            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='white')),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white"))
                        )
                        st.plotly_chart(fig_fluxo, use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    # 7. BOTTOM SECTIONS
                    col_b1, col_b2 = st.columns([1.5, 1.5]) 
                    with col_b1:
                        st.markdown("<h5 style='margin-bottom: 15px; color: #FFF;'>🧾 Últimas 10 Transações</h5>", unsafe_allow_html=True)
                        if not df_f.empty:
                            df_export = df_f[['date','descricao_completa','valor_abs','tipo','categoria']].copy().sort_values('date',ascending=False)
                            df_export.columns = ['Data','Descrição','Valor (R$)','Tipo','Categoria']
                            
                            df_tela = df_export.head(10).copy()
                            df_tela['Data'] = df_tela['Data'].dt.strftime('%d/%m/%Y %H:%M')
                            
                            st.dataframe(df_tela, use_container_width=True, hide_index=True)
                        else:
                            st.info("Nenhuma transação atende aos filtros selecionados.")

                    with col_b2:
                        st.markdown("<h5 style='margin-bottom: 15px; color: #FFF;'>📊 Gastos por Categoria (Saídas)</h5>", unsafe_allow_html=True)
                        
                        if not df_f.empty:
                            cat_grp = df_f[df_f['tipo']=='Saída'].groupby('categoria')['valor_abs'].sum().reset_index()
                            
                            if not cat_grp.empty:
                                cat_grp = cat_grp.sort_values('valor_abs', ascending=False)
                                cat_grp.columns = ['Categoria', 'Total Gasto (R$)']
                                
                                # Gráfico de Pizza (Menor para caber junto com a tabela)
                                fig_p = px.pie(cat_grp, values='Total Gasto (R$)', names='Categoria', hole=0.6, 
                                               color_discrete_sequence=['#00FF94', '#3b8beb', '#8b5cf6', '#FFD700', '#ff5e6c', '#00d4e8'])
                                fig_p.update_traces(textposition='inside', textinfo='percent+label')
                                fig_p.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, margin=dict(t=10,b=20,l=10,r=10), height=250)
                                st.plotly_chart(fig_p, use_container_width=True)
                                
                                # Tabela logo abaixo do Gráfico
                                st.dataframe(cat_grp, use_container_width=True, hide_index=True)
                            else:
                                st.info("Não houve gastos/saídas neste período.")
                        else:
                            st.info("Nenhuma transação atende aos filtros selecionados.")

                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # --- BOTOES NA HORIZONTAL ---
                        if not df_f.empty:
                            c_btn_xls, c_btn_pdf = st.columns(2)
                            with c_btn_xls:
                                st.download_button("📊 Excel", gerar_excel(df_export, entradas, saidas, saldo_real_atual, abs(total_faturas)), "relatorio.xlsx", use_container_width=True)
                            with c_btn_pdf:
                                st.download_button("📄 PDF", gerar_pdf(df_export, entradas, saidas, saldo_real_atual, abs(total_faturas)), "relatorio.pdf", use_container_width=True)