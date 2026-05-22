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
st.set_page_config(page_title="Iandra Intelligence - Digital Bank", layout="wide", page_icon="🔹")

# --- CSS DARK FINTECH (Nova Days Style) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

    :root {
        --bg-base:       #0f1117;
        --bg-sidebar:    #161b27;
        --bg-card:       #1a2035;
        --bg-card-hover: #1e2640;
        --bg-input:      #1e2640;
        --accent-cyan:   #00d4e8;
        --accent-blue:   #3b8beb;
        --accent-green:  #00c896;
        --accent-red:    #ff5e6c;
        --accent-gold:   #f5a623;
        --text-primary:  #e8edf5;
        --text-secondary:#8896b0;
        --text-muted:    #4a5568;
        --border:        rgba(255,255,255,0.06);
        --border-accent: rgba(0,212,232,0.3);
        --glow-cyan:     0 0 24px rgba(0,212,232,0.15);
        --glow-blue:     0 0 24px rgba(59,139,235,0.15);
        --shadow-card:   0 4px 24px rgba(0,0,0,0.4);
        --radius-card:   16px;
        --radius-btn:    10px;
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        color: var(--text-primary);
    }

    /* ── BACKGROUND ── */
    .stApp {
        background-color: var(--bg-base);
        background-image:
            radial-gradient(ellipse 80% 50% at 20% 0%, rgba(59,139,235,0.08) 0%, transparent 60%),
            radial-gradient(ellipse 60% 40% at 80% 100%, rgba(0,212,232,0.06) 0%, transparent 60%);
    }

    /* ── HIDE STREAMLIT CHROME ── */
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }

    /* ── SIDEBAR ── */
    [data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border) !important;
        box-shadow: 4px 0 24px rgba(0,0,0,0.3) !important;
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

    /* Sidebar profile section */
    .profile-section {
        padding: 28px 20px 20px;
        text-align: center;
        border-bottom: 1px solid var(--border);
        margin-bottom: 8px;
    }
    .profile-pic {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 12px;
        color: #ffffff;
        font-size: 22px;
        font-weight: 700;
        box-shadow: 0 0 0 3px rgba(0,212,232,0.25), var(--glow-cyan);
        letter-spacing: -0.5px;
    }
    .profile-name {
        font-weight: 600;
        font-size: 0.95rem;
        color: var(--text-primary);
        margin-bottom: 2px;
    }
    .profile-role {
        font-size: 0.75rem;
        color: var(--text-secondary);
        letter-spacing: 0.5px;
    }
    .brand-header {
        padding: 20px 20px 0;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 4px;
    }
    .brand-logo {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
    }
    .brand-name {
        font-size: 0.85rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    /* ── SIDEBAR NAV RADIO ── */
    div[role="radiogroup"] { gap: 2px !important; display: flex; flex-direction: column; }
    div[role="radiogroup"] > label {
        background-color: transparent !important;
        border-radius: var(--radius-btn) !important;
        padding: 12px 16px !important;
        border: none !important;
        transition: all 0.2s ease;
        margin: 1px 8px !important;
    }
    div[role="radiogroup"] > label:hover {
        background-color: rgba(255,255,255,0.05) !important;
    }
    div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(135deg, rgba(0,212,232,0.18), rgba(59,139,235,0.12)) !important;
        border-left: 3px solid var(--accent-cyan) !important;
        box-shadow: var(--glow-cyan) !important;
    }
    div[role="radiogroup"] > label[data-checked="true"] p {
        color: var(--accent-cyan) !important;
        font-weight: 600 !important;
    }
    div[role="radiogroup"] > label p {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }

    /* ── HEADINGS & TEXT ── */
    h1, h2, h3, h4, h5, h6 { color: var(--text-primary) !important; font-weight: 700 !important; }
    p { color: var(--text-secondary) !important; }

    /* ── METRIC CARDS ── */
    [data-testid="stMetricContainer"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-card) !important;
        padding: 24px !important;
        box-shadow: var(--shadow-card) !important;
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
        overflow: hidden;
    }
    [data-testid="stMetricContainer"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--accent-blue), var(--accent-cyan));
        border-radius: var(--radius-card) var(--radius-card) 0 0;
    }
    [data-testid="stMetricContainer"]:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-card), var(--glow-blue) !important;
    }
    [data-testid="stMetricLabel"] p {
        color: var(--text-secondary) !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    [data-testid="stMetricValue"] div {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        font-size: 1.6rem !important;
        font-family: 'DM Mono', monospace !important;
    }
    [data-testid="stMetricDelta"] div { font-size: 0.8rem !important; }

    /* ── INPUTS & SELECTS ── */
    .stTextInput input,
    .stDateInput input,
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div {
        background-color: var(--bg-input) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stTextInput input:focus,
    .stDateInput input:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 0 2px rgba(0,212,232,0.15) !important;
    }
    [data-baseweb="select"] * { color: var(--text-primary) !important; }
    [data-baseweb="menu"] { background-color: var(--bg-card) !important; border: 1px solid var(--border) !important; }
    [data-baseweb="option"]:hover { background-color: var(--bg-card-hover) !important; }

    /* ── BUTTONS ── */
    .stButton > button {
        background: linear-gradient(135deg, rgba(0,212,232,0.12), rgba(59,139,235,0.12)) !important;
        color: var(--accent-cyan) !important;
        border: 1px solid rgba(0,212,232,0.3) !important;
        border-radius: var(--radius-btn) !important;
        padding: 0.55rem 1.1rem !important;
        font-weight: 600 !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.3px;
        transition: all 0.25s ease;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)) !important;
        color: #0f1117 !important;
        border-color: transparent !important;
        box-shadow: var(--glow-cyan) !important;
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan)) !important;
        color: #0f1117 !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: var(--glow-cyan), var(--glow-blue) !important;
        transform: translateY(-2px);
    }

    /* ── FORMS ── */
    [data-testid="stForm"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-card) !important;
        padding: 28px !important;
        box-shadow: var(--shadow-card) !important;
    }

    /* ── DATAFRAME / TABLE ── */
    .stDataFrame {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-card) !important;
        box-shadow: var(--shadow-card) !important;
        overflow: hidden;
    }
    .stDataFrame iframe { border-radius: var(--radius-card) !important; }

    /* ── SELECTBOX ── */
    .stSelectbox > div { border-radius: 10px !important; }

    /* ── MULTISELECT TAGS ── */
    span[data-baseweb="tag"] {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan)) !important;
        color: #0f1117 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }

    /* ── RADIO BUTTONS (filters) ── */
    .stRadio > div > label { color: var(--text-secondary) !important; }
    .stRadio > div > label[data-checked="true"] { color: var(--accent-cyan) !important; }

    /* ── ALERTS / MESSAGES ── */
    .stAlert {
        background: rgba(26, 32, 53, 0.9) !important;
        border-radius: 12px !important;
        border: 1px solid var(--border) !important;
    }
    .stSuccess {
        background: rgba(0, 200, 150, 0.1) !important;
        border-left: 3px solid var(--accent-green) !important;
    }
    .stWarning {
        background: rgba(245, 166, 35, 0.1) !important;
        border-left: 3px solid var(--accent-gold) !important;
    }
    .stError {
        background: rgba(255, 94, 108, 0.1) !important;
        border-left: 3px solid var(--accent-red) !important;
    }
    .stInfo {
        background: rgba(59, 139, 235, 0.1) !important;
        border-left: 3px solid var(--accent-blue) !important;
    }

    /* ── EXPANDER ── */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }
    .streamlit-expanderContent {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
    }

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card) !important;
        border-radius: 12px !important;
        padding: 4px !important;
        gap: 4px !important;
        border: 1px solid var(--border) !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-secondary) !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        font-weight: 500 !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan)) !important;
        color: #0f1117 !important;
        font-weight: 700 !important;
    }

    /* ── SPINNER ── */
    .stSpinner > div { border-top-color: var(--accent-cyan) !important; }

    /* ── DOWNLOAD BUTTON ── */
    .stDownloadButton > button {
        background: rgba(0,212,232,0.08) !important;
        color: var(--accent-cyan) !important;
        border: 1px solid rgba(0,212,232,0.25) !important;
        border-radius: var(--radius-btn) !important;
        font-weight: 600 !important;
    }
    .stDownloadButton > button:hover {
        background: var(--accent-cyan) !important;
        color: #0f1117 !important;
    }

    /* ── HR DIVIDER ── */
    hr { border-color: var(--border) !important; }

    /* ── CHECKBOX ── */
    .stCheckbox > label > span { color: var(--text-secondary) !important; }

    /* ── PASSWORD INPUT ── */
    .stTextInput input[type="password"] {
        background-color: var(--bg-input) !important;
        color: var(--text-primary) !important;
    }

    /* ── LOGIN PAGE CARD ── */
    .login-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 40px 36px;
        box-shadow: var(--shadow-card), var(--glow-blue);
        backdrop-filter: blur(12px);
    }

    /* ── PAGE TITLE STYLE ── */
    .page-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--border);
    }
    .page-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text-primary) !important;
        margin: 0 !important;
    }
    .page-subtitle {
        font-size: 0.85rem;
        color: var(--text-secondary) !important;
        margin-top: 2px;
    }

    /* ── SIDEBAR LABEL ── */
    .sidebar-section-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: var(--text-muted);
        padding: 16px 24px 8px;
    }

    /* ── SCROLLBAR ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-base); }
    ::-webkit-scrollbar-thumb { background: var(--text-muted); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()
CLIENT_ID = os.getenv("PLUGGY_CLIENT_ID") or st.secrets.get("PLUGGY_CLIENT_ID")
CLIENT_SECRET = os.getenv("PLUGGY_CLIENT_SECRET") or st.secrets.get("PLUGGY_CLIENT_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL") or st.secrets.get("DATABASE_URL")

defaults = {
    'logado': False, 'usuario_nome': "", 'usuario_id': None,
    'is_admin': False, 'abrir_pluggy': False,
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
            info_contas.append({
                "nome": c.get("name", "Conta"),
                "tipo": c.get("type", ""),
                "saldo": c.get("balance", 0),
                "id": c.get("id")
            })
        
        conta_id = contas[0].get("id")
        trans_resp = requests.get(
            f"https://api.pluggy.ai/transactions?accountId={conta_id}&pageSize=500",
            headers=headers, timeout=15
        ).json()
        return trans_resp.get("results", []), info_contas
    except Exception as e: return "ERRO_DADOS", []

TRADUCAO_CATEGORIAS = {
    'TRANSFER - PIX': 'Transferência PIX',
    'TRANSFERS': 'Transferências',
    'DIGITAL SERVICES': 'Serviços Digitais',
    'FOOD DELIVERY': 'Delivery de Comida',
    'BOOKSTORE': 'Livraria',
    'ONLINE SHOPPING': 'Compras Online',
    'TELECOMMUNICATIONS': 'Telecomunicações',
    'EATING OUT': 'Restaurantes',
    'GAS STATIONS': 'Posto de Combustível',
    'LEISURE': 'Lazer',
    'LATE PAYMENT AND OVERDRAFT COSTS': 'Juros e Multas',
    'TAX ON FINANCIAL OPERATIONS': 'Impostos (IOF/Taxas)',
    'COMPRAS': 'Compras',
    'SUPERMERCADO': 'Supermercado',
    'TRANSPORTE': 'Transporte',
    'INTERNET': 'Internet',
    'FOOD_AND_DRINK': 'Alimentação',
    'FOOD AND DRINK': 'Alimentação',
    'RESTAURANT': 'Restaurante',
    'GROCERIES': 'Supermercado',
    'COFFEE': 'Cafeteria',
    'HOME': 'Casa',
    'RENT': 'Aluguel',
    'MORTGAGE': 'Hipoteca',
    'UTILITIES': 'Contas de Casa',
    'ELECTRICITY': 'Energia Elétrica',
    'WATER': 'Água',
    'TRANSPORTATION': 'Transporte',
    'GAS_STATION': 'Posto de Combustível',
    'GAS': 'Combustível',
    'PARKING': 'Estacionamento',
    'PUBLIC_TRANSIT': 'Transporte Público',
    'HEALTHCARE': 'Saúde',
    'PHARMACY': 'Farmácia',
    'DOCTOR': 'Médico/Clínica',
    'PERSONAL_CARE': 'Cuidados Pessoais',
    'GYM': 'Academia',
    'ENTERTAINMENT': 'Lazer e Entretenimento',
    'SUBSCRIPTIONS': 'Assinaturas',
    'SHOPPING': 'Compras',
    'CLOTHING': 'Roupas',
    'ELECTRONICS': 'Eletrônicos',
    'EDUCATION': 'Educação',
    'TRAVEL': 'Viagem',
    'INCOME': 'Renda',
    'SALARY': 'Salário',
    'TRANSFER': 'Transferência',
    'INTERNAL_TRANSFER': 'Transferência Interna',
    'PAYMENT': 'Pagamento',
    'CREDIT_CARD_PAYMENT': 'Pagamento de Fatura',
    'INVESTMENT': 'Investimento',
    'BANK_FEES': 'Tarifas Bancárias',
    'CREDIT_CARD': 'Cartão de Crédito',
    'LOAN': 'Empréstimo',
    'INSURANCE': 'Seguro',
    'TAXES': 'Impostos',
    'DEPOSIT': 'Depósito',
    'UNCATEGORIZED': 'Outros',
    'OTHER': 'Outros'
}

def traduzir_categoria(cat_raw):
    if cat_raw is None:
        return 'Outros'
    if isinstance(cat_raw, dict):
        cat_raw = cat_raw.get('description', cat_raw.get('name', 'UNCATEGORIZED'))
    cat_str = str(cat_raw).upper().strip()
    if cat_str in TRADUCAO_CATEGORIAS:
        return TRADUCAO_CATEGORIAS[cat_str]
    cat_str_under = cat_str.replace(' - ', '_').replace('-', '_').replace(' ', '_')
    if cat_str_under in TRADUCAO_CATEGORIAS:
        return TRADUCAO_CATEGORIAS[cat_str_under]
    cat_str_espaco = cat_str.replace('_', ' ')
    if cat_str_espaco in TRADUCAO_CATEGORIAS:
        return TRADUCAO_CATEGORIAS[cat_str_espaco]
    return cat_str_espaco.title() if cat_str else 'Outros'

def gerar_excel(df, total_in, total_out, saldo, total_cartao):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        wb = writer.book

        fmt_titulo    = wb.add_format({'bold': True, 'font_size': 14, 'font_color': '#FFFFFF', 'bg_color': '#0288d1', 'align': 'center', 'valign': 'vcenter'})
        fmt_header    = wb.add_format({'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#039be5', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 11})
        fmt_resumo_k  = wb.add_format({'bold': True, 'font_color': '#2c3e50', 'bg_color': '#e1f5fe', 'border': 1, 'font_size': 11})
        fmt_resumo_v  = wb.add_format({'num_format': 'R$ #,##0.00', 'border': 1, 'font_size': 11, 'align': 'right'})
        fmt_entrada   = wb.add_format({'bg_color': '#e8f5e9', 'font_color': '#2e7d32', 'border': 1, 'font_size': 10})
        fmt_saida     = wb.add_format({'bg_color': '#ffebee', 'font_color': '#c62828', 'border': 1, 'font_size': 10})
        fmt_moeda_in  = wb.add_format({'num_format': 'R$ #,##0.00', 'bg_color': '#e8f5e9', 'font_color': '#2e7d32', 'border': 1, 'font_size': 10, 'align': 'right'})
        fmt_moeda_out = wb.add_format({'num_format': 'R$ #,##0.00', 'bg_color': '#ffebee', 'font_color': '#c62828', 'border': 1, 'font_size': 10, 'align': 'right'})

        ws_res = wb.add_worksheet('Resumo')
        ws_res.set_column('A:A', 28)
        ws_res.set_column('B:B', 20)
        ws_res.set_row(0, 30)
        ws_res.merge_range('A1:B1', 'Resumo Financeiro', fmt_titulo)

        resumo_dados = [
            ('Total de Entradas',    total_in),
            ('Total de Saídas',      total_out),
            ('Gastos Cartão de Crédito', total_cartao),
            ('Saldo Líquido',        saldo),
            ('Número de Transações', len(df)),
        ]
        for i, (label, val) in enumerate(resumo_dados, start=1):
            ws_res.write(i, 0, label, fmt_resumo_k)
            if isinstance(val, int):
                ws_res.write(i, 1, val, wb.add_format({'border': 1, 'font_size': 11, 'align': 'right'}))
            else:
                ws_res.write(i, 1, val, fmt_resumo_v)

        ws = wb.add_worksheet('Extrato')
        ws.set_column('A:A', 14)
        ws.set_column('B:B', 48)
        ws.set_column('C:C', 16)
        ws.set_column('D:D', 12)
        ws.set_column('E:E', 22)
        ws.set_row(0, 22)

        colunas = list(df.columns)
        for col_idx, col_name in enumerate(colunas):
            ws.write(0, col_idx, col_name, fmt_header)

        for row_idx, (_, row) in enumerate(df.iterrows(), start=1):
            is_entrada = str(row.get('Tipo', '')).strip() == 'Entrada'
            fmt_txt = fmt_entrada if is_entrada else fmt_saida
            fmt_val = fmt_moeda_in if is_entrada else fmt_moeda_out

            for col_idx, col_name in enumerate(colunas):
                val = row[col_name]
                if col_name == 'Valor (R$)':
                    try:
                        ws.write(row_idx, col_idx, float(val), fmt_val)
                    except:
                        ws.write(row_idx, col_idx, 0, fmt_val)
                else:
                    ws.write(row_idx, col_idx, str(val) if val is not None else '', fmt_txt)

        ws.freeze_panes(1, 0)

    output.seek(0)
    return output.getvalue()


def gerar_pdf(df, total_in, total_out, saldo, total_cartao):
    from datetime import datetime

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    largura_pagina = 277

    data_fim = df['Data'].iloc[0][:10] if not df.empty else 'N/A'
    data_inicio = df['Data'].iloc[-1][:10] if not df.empty else 'N/A'

    pdf.set_fill_color(2, 136, 209)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(largura_pagina, 12, "Relatorio Financeiro - Auxiliador da Iandra", ln=False, align='C', fill=True)
    pdf.ln(12)

    pdf.set_font("helvetica", '', 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(largura_pagina, 6, f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}  |  Período: {data_inicio} a {data_fim}", ln=True, align='C')
    pdf.ln(4)

    pdf.set_font("helvetica", 'B', 10)
    pdf.set_fill_color(3, 169, 244)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(largura_pagina, 8, "  Resumo do Período", ln=True, fill=True)
    pdf.ln(1)

    resumo = [
        ("Total de Entradas",    f"R$ {total_in:,.2f}",  (209, 250, 229), (6, 95, 70)),
        ("Total de Saídas",      f"R$ {total_out:,.2f}", (254, 226, 226), (127, 29, 29)),
        ("Cartão de Crédito",    f"R$ {total_cartao:,.2f}", (254, 215, 170), (154, 52, 18)),
        ("Saldo Líquido",        f"R$ {saldo:,.2f}",     (225, 245, 254), (2, 136, 209)),
        ("Transações",           f"{len(df)}",           (248, 250, 252), (51, 65, 85)),
    ]

    col_w = largura_pagina / 2
    for i in range(0, len(resumo), 2):
        for j in range(2):
            if i + j < len(resumo):
                label, valor, bg, fg = resumo[i + j]
                pdf.set_fill_color(*bg)
                pdf.set_draw_color(203, 213, 225)
                pdf.set_text_color(*fg)
                pdf.set_font("helvetica", 'B', 9)
                pdf.cell(col_w * 0.55, 7, f"  {label}", border=1, fill=True)
                pdf.set_font("helvetica", '', 9)
                pdf.cell(col_w * 0.45, 7, f"  {valor}", border=1, fill=True, align='R')
        pdf.ln()
    pdf.ln(4)

    pdf.set_font("helvetica", 'B', 10)
    pdf.set_fill_color(3, 169, 244)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(largura_pagina, 8, f"  Extrato de Transações ({len(df)} registros)", ln=True, fill=True)
    pdf.ln(1)

    col_widths = [24, 98, 28, 22, 42, 30]
    headers = list(df.columns)
    col_widths = col_widths[:len(headers)]
    while len(col_widths) < len(headers):
        col_widths.append(30)

    pdf.set_font("helvetica", 'B', 8)
    pdf.set_fill_color(38, 50, 56)
    pdf.set_text_color(226, 232, 240)
    pdf.set_draw_color(207, 216, 220)
    for h, w in zip(headers, col_widths):
        pdf.cell(w, 7, f" {h}", border=1, fill=True)
    pdf.ln()

    pdf.set_font("helvetica", '', 8)
    pdf.set_draw_color(207, 216, 220)

    for i, row in enumerate(df.itertuples(index=False)):
        tipo = str(getattr(row, 'Tipo', '')).strip()
        is_entrada = tipo == 'Entrada'

        if is_entrada:
            pdf.set_fill_color(200, 230, 201); pdf.set_text_color(46, 125, 50)
        elif i % 2 == 0:
            pdf.set_fill_color(248, 250, 252); pdf.set_text_color(38, 50, 56)
        else:
            pdf.set_fill_color(241, 245, 249); pdf.set_text_color(38, 50, 56)

        if pdf.get_y() > 185:
            pdf.add_page()
            pdf.set_font("helvetica", 'B', 8)
            pdf.set_fill_color(38, 50, 56)
            pdf.set_text_color(226, 232, 240)
            for h, w in zip(headers, col_widths):
                pdf.cell(w, 7, f" {h}", border=1, fill=True)
            pdf.ln()
            pdf.set_font("helvetica", '', 8)
            if is_entrada:
                pdf.set_fill_color(200, 230, 201); pdf.set_text_color(46, 125, 50)
            elif i % 2 == 0:
                pdf.set_fill_color(248, 250, 252); pdf.set_text_color(38, 50, 56)
            else:
                pdf.set_fill_color(241, 245, 249); pdf.set_text_color(38, 50, 56)

        valores = list(row)
        for val, w in zip(valores, col_widths):
            txt = str(val) if val is not None else ''
            while pdf.get_string_width(f" {txt}") > w - 2 and len(txt) > 3:
                txt = txt[:-1]
            if len(str(val) if val is not None else '') > len(txt):
                txt = txt[:-1] + '...'
            pdf.cell(w, 6, f" {txt}", border=1, fill=True)
        pdf.ln()

    pdf.ln(4)
    pdf.set_font("helvetica", 'I', 8)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(largura_pagina, 5, "Documento gerado automaticamente pelo Auxiliador Financeiro da Iandra.", align='C')

    return bytes(pdf.output())

# ==========================================
# LOGIN — DARK FINTECH STYLE
# ==========================================
if not st.session_state['logado']:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align:center; margin-bottom: 32px;'>
                <div style='
                    width: 56px; height: 56px;
                    background: linear-gradient(135deg, #3b8beb, #00d4e8);
                    border-radius: 16px;
                    display: flex; align-items: center; justify-content: center;
                    margin: 0 auto 16px;
                    font-size: 26px;
                    box-shadow: 0 0 32px rgba(0,212,232,0.3);
                '>🔹</div>
                <div style='font-size: 1.5rem; font-weight: 800; color: #e8edf5; letter-spacing: -0.5px;'>IANDRA INTELLIGENCE</div>
                <div style='font-size: 0.9rem; color: #8896b0; margin-top: 6px;'>Acesse sua conta digital corporativa</div>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("E-mail ou CPF", placeholder="seu@email.com")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            if st.form_submit_button("ENTRAR NA CONTA", type="primary"):
                if email == "admin" and senha == "admin":
                    st.session_state.update({'logado': True, 'usuario_id': 999, 'usuario_nome': "Administrador Mestre", 'is_admin': True})
                    st.rerun()
                else:
                    usuario = verificar_login(email, senha)
                    if usuario:
                        st.session_state.update({'logado': True, 'usuario_id': usuario[0], 'usuario_nome': usuario[1], 'is_admin': bool(usuario[2])})
                        st.rerun()
                    else:
                        st.error("Acesso negado. Verifique os seus dados.")

# ==========================================
# ÁREA LOGADA
# ==========================================
else:
    with st.sidebar:
        # Brand header
        st.markdown(f"""
            <div class="brand-header">
                <div class="brand-logo">🔹</div>
                <div class="brand-name">Nova Days</div>
            </div>
        """, unsafe_allow_html=True)

        # Profile
        st.markdown(f"""
            <div class="profile-section">
                <div class="profile-pic">{st.session_state['usuario_nome'][0].upper()}</div>
                <div class="profile-name">Bem-vindo(a), {st.session_state['usuario_nome'].split()[0]}</div>
                <div class="profile-role">Painel Executivo</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section-label">Navegação</div>', unsafe_allow_html=True)

        menu = st.radio(
            "nav",
            ["📊  Dashboard", "🔗  Gerir Bancos", "⚙️  Admin"] if st.session_state['is_admin']
            else ["📊  Dashboard", "🔗  Gerir Bancos"],
            label_visibility="collapsed"
        )

        st.markdown("<div style='flex: 1; height: 60px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section-label">Conta</div>', unsafe_allow_html=True)

        if st.button("🔄  Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()

        if st.button("🚪  Sair da Conta"):
            st.session_state.update({'logado': False, 'is_admin': False})
            st.rerun()

    # Normalize menu labels (strip extra spaces)
    menu_clean = menu.strip()

    # --- ADMIN ---
    if "Admin" in menu_clean:
        st.markdown("""
            <div class="page-header">
                <div class="page-title">⚙️ Painel de Controle</div>
            </div>
            <div class="page-subtitle">Gerencie clientes e configurações do sistema.</div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

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
                    if u[0] != st.session_state['usuario_id']:
                        if st.button("🗑 Eliminar Conta", key=f"del_{u[0]}"):
                            deletar_usuario_completo(u[0])
                            st.rerun()

    # --- GERIR BANCOS ---
    elif "Gerir" in menu_clean:
        st.markdown("""
            <div class="page-header">
                <div class="page-title">🔗 Conexões Bancárias</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='color:#8896b0; margin-bottom: 20px;'>Conecte as contas bancárias para sincronizar as transações automaticamente.</div>", unsafe_allow_html=True)

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
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: transparent; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
#widget-area {{ min-height: 460px; }}
#success-box {{
  display: none; background: rgba(0,200,150,0.1); border: 1px solid #00c896;
  border-radius: 12px; padding: 32px 24px; margin: 16px 0; text-align: center;
}}
#success-box h2 {{ color: #00c896; font-size: 1.3rem; margin-bottom: 8px; }}
#success-box p  {{ color: #8896b0; font-size: 0.95rem; margin-bottom: 20px; }}
#id-display {{
  background: #1a2035; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px;
  padding: 14px 16px; font-family: monospace; font-size: 0.9rem; color: #00d4e8;
  word-break: break-all; margin-bottom: 16px; text-align: left;
}}
#copy-btn {{
  background: linear-gradient(135deg, #3b8beb, #00d4e8); color: #0f1117; border: none;
  border-radius: 20px; padding: 10px 28px; font-size: 0.95rem; cursor: pointer; font-weight: 700;
}}
#copy-btn:hover {{ opacity: 0.9; }}
#copy-hint {{ color: #00c896; font-size: 0.85rem; margin-top: 10px; display: none; }}
</style></head><body>
<div id="widget-area"></div>
<div id="success-box">
  <h2>✅ Banco conectado com sucesso!</h2>
  <p>Copie o ID abaixo e cole no campo que apareceu na página:</p>
  <div id="id-display">Aguardando...</div>
  <button id="copy-btn" onclick="copiarID()">📋 Copiar ID</button>
  <p id="copy-hint">✓ Copiado! Agora cole no campo acima e clique em Salvar.</p>
</div>
<script src="https://cdn.pluggy.ai/pluggy-connect/v2.8.2/pluggy-connect.js"></script>
<script>
var capturedItemId = '';
function copiarID() {{
  navigator.clipboard.writeText(capturedItemId).then(function() {{
    document.getElementById('copy-hint').style.display = 'block';
    document.getElementById('copy-btn').textContent = '✓ Copiado!';
  }});
}}
var connect = new PluggyConnect({{
  connectToken: '{token}',
  onSuccess: function(data) {{
    capturedItemId = data.item.id;
    document.getElementById('widget-area').style.display = 'none';
    document.getElementById('id-display').textContent = capturedItemId;
    document.getElementById('success-box').style.display = 'block';
  }},
  onClose: function() {{
    document.getElementById('widget-area').innerHTML = '<p style="color:#8896b0;text-align:center;padding:60px;">Conexão encerrada.</p>';
  }},
  onError: function(err) {{
    document.getElementById('widget-area').innerHTML = '<p style="color:#ff5e6c;text-align:center;padding:60px;">Erro na conexão. Tente novamente.</p>';
  }}
}});
connect.init();
</script></body></html>
""", height=540)

                st.markdown("<p style='color:#8896b0; font-size:0.9rem; margin-top:8px;'>👆 Após conectar o banco acima, copie o ID exibido e cole aqui:</p>", unsafe_allow_html=True)
                item_id_input = st.text_input("ID da Conexão", placeholder="Cole aqui o ID copiado do widget acima...", label_visibility="collapsed")
                if st.button("💾 Salvar Conexão", type="primary", disabled=not item_id_input.strip()):
                    with st.spinner("Salvando no Supabase..."):
                        sucesso, msg = salvar_conexao_por_item_id(st.session_state['usuario_id'], item_id_input)
                    if sucesso:
                        st.session_state.update({'pluggy_sucesso': True, 'pluggy_item_id': item_id_input.strip(), 'abrir_pluggy': False})
                        st.success(msg)
                        st.rerun()
                    else:
                        st.warning(msg)

        if st.session_state['pluggy_sucesso']:
            st.success("🎉 Banco conectado! Acesse o **Dashboard** para ver seus dados.")

        st.markdown("<hr>", unsafe_allow_html=True)
        c_b1, c_b2 = st.columns([3, 1])
        c_b1.markdown("#### 🏦 Bancos Ativos")
        if c_b2.button("🔄 Sincronizar", type="primary"):
            with st.spinner("A comunicar com os servidores da Pluggy..."):
                sucesso, msg = sincronizar_ultimo_banco(st.session_state['usuario_id'])
            if sucesso:
                st.success(msg)
                st.rerun()
            else:
                st.warning(msg)

        conexoes = buscar_conexoes_usuario(st.session_state['usuario_id'])
        if not conexoes:
            st.info("Ainda não há nenhum banco sincronizado.")
        else:
            for i, cx in enumerate(conexoes):
                c1, c2 = st.columns([7, 1])
                c1.info(f"🏦 {cx[2]} | ID: {cx[1][:15]}...")
                if c2.button("🗑", key=f"del_cx_{i}"):
                    deletar_conexao(cx[0])
                    st.rerun()

    # --- DASHBOARD ---
    elif "Dashboard" in menu_clean:
        today_str = datetime.now().strftime("%A, %d %B, %Y")
        st.markdown(f"""
            <div class="page-header">
                <div>
                    <div class="page-title">📊 Dashboard</div>
                    <div class="page-subtitle">Today is {today_str}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        conexoes = buscar_conexoes_usuario(st.session_state['usuario_id'])
        if not conexoes:
            st.warning("Nenhum banco conectado. Vá em '🔗 Gerir Bancos' para começar.")
        else:
            bancos_dict = {f"{c[2]} ({c[1][:5]})": c[1] for c in conexoes}
            sel_banco = st.selectbox("Selecione a conta para visualizar:", list(bancos_dict.keys()))

            with st.spinner("Carregando dados bancários..."):
                resultado = buscar_dados_reais(bancos_dict[sel_banco])

            if resultado[0] == "SEM_CONTAS":
                st.warning("Este banco não possui contas associadas ainda.")
            elif resultado[0] == "ERRO_DADOS":
                st.error("Não foi possível carregar os dados deste banco. Tente novamente.")
            else:
                trans, info_contas = resultado

                if not trans:
                    st.info("Nenhuma transação encontrada para este período.")
                else:
                    for t in trans:
                        desc_original = str(t.get('description', '')).strip()
                        nome_extra = ""
                        amount = float(t.get('amount', 0)) if t.get('amount') is not None else 0

                        if isinstance(t.get('merchant'), dict):
                            nome_extra = t['merchant'].get('name', '') or t['merchant'].get('businessName', '')

                        if not nome_extra and isinstance(t.get('paymentData'), dict):
                            pdata = t['paymentData']
                            if amount < 0:
                                nome_extra = pdata.get('receiverName', '')
                                if not nome_extra and isinstance(pdata.get('payee'), dict):
                                    nome_extra = pdata['payee'].get('name', '')
                                if not nome_extra and isinstance(pdata.get('receiver'), dict):
                                    nome_extra = pdata['receiver'].get('name', '')
                            else:
                                nome_extra = pdata.get('payerName', '')
                                if not nome_extra and isinstance(pdata.get('payer'), dict):
                                    nome_extra = pdata['payer'].get('name', '')

                        if not nome_extra and t.get('descriptionRaw'):
                            raw = str(t['descriptionRaw']).strip()
                            if raw.upper() != desc_original.upper():
                                if desc_original.upper() in raw.upper():
                                    nome_extra = raw.upper().replace(desc_original.upper(), '').strip(' -/*\\:')
                                else:
                                    nome_extra = raw

                        if nome_extra:
                            nome_extra = str(nome_extra).title()
                            if len(nome_extra) > 40:
                                nome_extra = nome_extra[:40] + "..."
                            t['descricao_completa'] = f"{desc_original} ({nome_extra})"
                        else:
                            t['descricao_completa'] = desc_original

                    df = pd.DataFrame(trans)
                    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
                    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)

                    if 'category' in df.columns:
                        df['categoria'] = df['category'].apply(traduzir_categoria)
                    else:
                        df['categoria'] = 'Outros'

                    if 'type' in df.columns:
                        df['tipo'] = df['type'].apply(lambda x: 'Entrada' if str(x).upper() == 'CREDIT' else 'Saída')
                    else:
                        df['tipo'] = df['amount'].apply(lambda x: 'Entrada' if x > 0 else 'Saída')

                    df['valor_abs'] = df['amount'].abs()

                    # --- FILTROS NA SIDEBAR ---
                    st.sidebar.markdown("<hr style='border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
                    st.sidebar.markdown('<div class="sidebar-section-label">🔍 Filtros</div>', unsafe_allow_html=True)

                    d1 = st.sidebar.date_input("Data de Início", df['date'].min().date())
                    d2 = st.sidebar.date_input("Data de Fim", df['date'].max().date())

                    categorias_disponiveis = sorted(df['categoria'].unique().tolist())
                    cats_selecionadas = st.sidebar.multiselect(
                        "Categorias",
                        options=categorias_disponiveis,
                        default=categorias_disponiveis,
                        placeholder="Todas as categorias"
                    )

                    tipo_filtro = st.sidebar.radio(
                        "Tipo de Movimentação",
                        ["Todos", "Apenas Entradas", "Apenas Saídas"],
                        index=0
                    )

                    df_f = df[
                        (df['date'].dt.date >= d1) &
                        (df['date'].dt.date <= d2)
                    ]
                    if cats_selecionadas:
                        df_f = df_f[df_f['categoria'].isin(cats_selecionadas)]
                    if tipo_filtro == "Apenas Entradas":
                        df_f = df_f[df_f['tipo'] == 'Entrada']
                    elif tipo_filtro == "Apenas Saídas":
                        df_f = df_f[df_f['tipo'] == 'Saída']

                    if df_f.empty:
                        st.warning("Nenhuma transação encontrada com os filtros selecionados.")
                    else:
                        # --- MÉTRICAS ---
                        entradas = df_f[df_f['tipo'] == 'Entrada']['valor_abs'].sum()
                        saidas = df_f[df_f['tipo'] == 'Saída']['valor_abs'].sum()
                        total_cartao = df_f[(df_f['tipo'] == 'Saída') & (df_f['categoria'] == 'Cartão de Crédito')]['valor_abs'].sum()
                        saldo = entradas - saidas
                        total_trans = len(df_f)

                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("⬇️ Entradas", f"R$ {entradas:,.2f}")
                        m2.metric("⬆️ Saídas", f"R$ {saidas:,.2f}")
                        m3.metric("💰 Saldo Líquido", f"R$ {saldo:,.2f}")
                        m4.metric("📋 Transações", f"{total_trans}")

                        if info_contas:
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown("<h5 style='color:#8896b0; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;'>💳 Saldo Atual nas Contas</h5>", unsafe_allow_html=True)
                            cols_contas = st.columns(len(info_contas))
                            for idx, conta in enumerate(info_contas):
                                cols_contas[idx].metric(
                                    f"{'💳' if conta['tipo']=='CREDIT' else '🏦'} {conta['nome']}",
                                    f"R$ {conta['saldo']:,.2f}"
                                )

                        st.markdown("<br>", unsafe_allow_html=True)

                        # Dark-mode chart colors (cyan/blue palette)
                        grafico_cores = ['#00d4e8', '#3b8beb', '#00c896', '#f5a623', '#a78bfa', '#f472b6', '#34d399', '#60a5fa', '#fb923c', '#94a3b8']

                        # Chart layout base
                        chart_layout = dict(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#8896b0', family='DM Sans'),
                            margin=dict(t=20, b=20, l=20, r=20),
                        )

                        col_g1, col_g2 = st.columns(2)

                        with col_g1:
                            st.markdown("<h5>💸 Gastos por Categoria</h5>", unsafe_allow_html=True)
                            df_saidas = df_f[df_f['tipo'] == 'Saída']
                            if not df_saidas.empty:
                                cat_group = df_saidas.groupby('categoria')['valor_abs'].sum().reset_index()
                                cat_group = cat_group.sort_values('valor_abs', ascending=False)
                                fig_p = px.pie(
                                    cat_group,
                                    values='valor_abs',
                                    names='categoria',
                                    hole=0.5,
                                    color_discrete_sequence=grafico_cores
                                )
                                fig_p.update_traces(
                                    textposition='inside',
                                    textinfo='percent+label',
                                    textfont=dict(color='#e8edf5', size=11),
                                    marker=dict(line=dict(color='#0f1117', width=2))
                                )
                                fig_p.update_layout(
                                    **chart_layout,
                                    showlegend=True,
                                    legend=dict(font=dict(color='#8896b0'), bgcolor='rgba(0,0,0,0)', orientation='v'),
                                )
                                st.plotly_chart(fig_p, use_container_width=True)
                            else:
                                st.info("Nenhuma saída no período filtrado.")

                        with col_g2:
                            st.markdown("<h5>📈 Evolução do Caixa</h5>", unsafe_allow_html=True)
                            df_day = df_f.copy()
                            df_day['valor_sinal'] = df_day.apply(
                                lambda r: r['valor_abs'] if r['tipo'] == 'Entrada' else -r['valor_abs'], axis=1
                            )
                            df_day_grp = df_day.groupby(df_day['date'].dt.date)['valor_sinal'].sum().reset_index()
                            df_day_grp.columns = ['date', 'amount']
                            df_day_grp['saldo_acumulado'] = df_day_grp['amount'].cumsum()

                            fig_l = px.area(
                                df_day_grp, x='date', y='saldo_acumulado',
                                line_shape='spline',
                                color_discrete_sequence=['#00d4e8'],
                                labels={'saldo_acumulado': 'Saldo Acumulado', 'date': 'Data'}
                            )
                            fig_l.update_traces(
                                fill='tozeroy',
                                fillcolor='rgba(0,212,232,0.08)',
                                line=dict(color='#00d4e8', width=2.5)
                            )
                            fig_l.update_layout(
                                **chart_layout,
                                xaxis_title=None,
                                yaxis_title="R$",
                                yaxis=dict(gridcolor='rgba(255,255,255,0.05)', tickprefix='R$ ', color='#8896b0'),
                                xaxis=dict(showgrid=False, color='#8896b0'),
                            )
                            st.plotly_chart(fig_l, use_container_width=True)

                        st.markdown("<h5>📊 Entradas vs Saídas por Mês</h5>", unsafe_allow_html=True)
                        df_mensal = df_f.copy()
                        df_mensal['mes'] = df_mensal['date'].dt.to_period('M').astype(str)
                        df_mensal_grp = df_mensal.groupby(['mes', 'tipo'])['valor_abs'].sum().reset_index()
                        fig_bar = px.bar(
                            df_mensal_grp, x='mes', y='valor_abs', color='tipo',
                            barmode='group',
                            color_discrete_map={'Entrada': '#00c896', 'Saída': '#ff5e6c'},
                            labels={'valor_abs': 'Valor (R$)', 'mes': 'Mês', 'tipo': 'Tipo'}
                        )
                        fig_bar.update_layout(
                            **chart_layout,
                            legend=dict(font=dict(color='#8896b0'), bgcolor='rgba(0,0,0,0)'),
                            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', tickprefix='R$ ', color='#8896b0'),
                            xaxis=dict(showgrid=False, color='#8896b0'),
                            bargap=0.3,
                            bargroupgap=0.1,
                        )
                        fig_bar.update_traces(marker_line_width=0)
                        st.plotly_chart(fig_bar, use_container_width=True)

                        # --- EXTRATO ---
                        st.markdown("<h5>🧾 Extrato Detalhado</h5>", unsafe_allow_html=True)
                        df_extrato = df_f[['date', 'descricao_completa', 'valor_abs', 'tipo', 'categoria']].copy()
                        df_extrato = df_extrato.sort_values('date', ascending=False)
                        df_extrato.columns = ['Data', 'Descrição', 'Valor (R$)', 'Tipo', 'Categoria']
                        df_extrato['Valor (R$)'] = df_extrato['Valor (R$)'].round(2)
                        df_extrato['Data'] = df_extrato['Data'].dt.strftime('%d/%m/%Y')

                        st.dataframe(df_extrato, use_container_width=True, hide_index=True)

                        c_ex1, c_ex2, _ = st.columns([1, 1, 4])
                        df_export = df_extrato.copy()
                        c_ex1.download_button("📊 Baixar Excel", gerar_excel(df_export, entradas, saidas, saldo, total_cartao), "extrato.xlsx")
                        c_ex2.download_button("📄 Baixar PDF", gerar_pdf(df_export, entradas, saidas, saldo, total_cartao), "relatorio.pdf")

                        # --- MODO DESENVOLVEDOR ---
                        st.markdown("---")
                        with st.expander("🛠️ Modo Desenvolvedor: Inspecionar Dados do Banco"):
                            st.info("Veja abaixo como o banco envia os dados puros.")
                            pix_brutos = []
                            for t in trans:
                                desc = str(t.get('description', '')).lower()
                                raw_desc = str(t.get('descriptionRaw', '')).lower()
                                if 'pix' in desc or 'pix' in raw_desc:
                                    pix_brutos.append(t)
                            if pix_brutos:
                                st.json(pix_brutos[:5])
                            else:
                                st.warning("Nenhuma transação PIX encontrada nos dados puros.")