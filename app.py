import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
import hashlib
from dotenv import load_dotenv
import io
from fpdf import FPDF
import streamlit.components.v1 as components
import psycopg2

# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO CSS
st.set_page_config(page_title="Auxiliador da Iandra", layout="wide", page_icon="💼")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stForm"], [data-testid="stMetricContainer"] {
        background-color: #1e293b !important; border: 1px solid #334155 !important;
        border-radius: 16px !important; padding: 20px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
    }
    [data-testid="stMetricValue"] { color: #e2e8f0 !important; }
    div.stButton > button:first-child {
        background-color: #0284c7 !important; color: #ffffff !important; border-radius: 20px !important;
        padding: 0.5rem 2rem !important; font-weight: 500 !important; border: 1px solid #0369a1 !important;
        transition: all 0.3s ease; width: 100%;
    }
    div.stButton > button:first-child:hover { background-color: #0369a1 !important; border-color: #0ea5e9 !important; box-shadow: 0 0 10px rgba(14, 165, 233, 0.2) !important; }
    .connect-btn button { background: linear-gradient(135deg, #0284c7 0%, #0d9488 100%) !important; border: none !important; height: 3.5rem !important; font-size: 1.1rem !important; }
    div[role="radiogroup"] { gap: 12px; }
    div[role="radiogroup"] > label {
        background-color: #0f172a !important; border-radius: 25px !important; padding: 12px 20px !important;
        border: 1px solid #334155 !important; cursor: pointer; transition: all 0.3s ease;
    }
    div[role="radiogroup"] > label:hover { border-color: #0ea5e9 !important; background-color: #162032 !important; }
    div[role="radiogroup"] > label[data-checked="true"] { background-color: #0ea5e9 !important; border-color: #0ea5e9 !important; }
    .stTextInput input, .stDateInput input, [data-baseweb="select"] > div {
        background-color: #0f172a !important; color: #e2e8f0 !important; border: 1px solid #334155 !important; border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()
CLIENT_ID = os.getenv("PLUGGY_CLIENT_ID") or st.secrets.get("PLUGGY_CLIENT_ID")
CLIENT_SECRET = os.getenv("PLUGGY_CLIENT_SECRET") or st.secrets.get("PLUGGY_CLIENT_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL") or st.secrets.get("DATABASE_URL")

# --- INICIALIZAÇÃO DA SESSÃO ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario_id' not in st.session_state: st.session_state['usuario_id'] = None
if 'is_admin' not in st.session_state: st.session_state['is_admin'] = False
if 'abrir_pluggy' not in st.session_state: st.session_state['abrir_pluggy'] = False

# --- FUNÇÕES DE BASE DE DADOS ---
def get_db_connection(): return psycopg2.connect(DATABASE_URL)
def hash_senha(senha): return hashlib.sha256(senha.encode()).hexdigest()

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
    except: return False
    finally: conn.close()

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

def salvar_conexao(usuario_id, pluggy_item_id, nome_instituicao="Nova Conta"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO conexoes_bancarias (usuario_id, pluggy_item_id, nome_instituicao) VALUES (%s, %s, %s)', (usuario_id, pluggy_item_id, nome_instituicao))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

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

# --- FUNÇÕES PLUGGY E EXPORTAÇÃO ---
def gerar_connect_token():
    url_auth = "https://api.pluggy.ai/auth"
    response = requests.post(url_auth, json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}, timeout=10)
    api_key = response.json().get("apiKey")
    url_token = "https://api.pluggy.ai/connect_token"
    headers = {"accept": "application/json", "X-API-KEY": api_key}
    response_token = requests.post(url_token, headers=headers, json={}, timeout=10)
    return response_token.json().get("accessToken")

@st.cache_data(ttl=3600)
def buscar_dados_reais(item_id):
    url_auth = "https://api.pluggy.ai/auth"
    try:
        response = requests.post(url_auth, json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}, timeout=10)
        token = response.json().get("apiKey")
        headers = {"accept": "application/json", "X-API-KEY": token}
        contas = requests.get(f"https://api.pluggy.ai/accounts?itemId={item_id}", headers=headers, timeout=10).json().get("results", [])
        if not contas: return "SEM_CONTAS"
        conta_id = contas[0].get("id")
        trans = requests.get(f"https://api.pluggy.ai/transactions?accountId={conta_id}&pageSize=500", headers=headers, timeout=10).json().get("results", [])
        return trans
    except: return "ERRO_DADOS"

TRADUCAO_CATEGORIAS = {
    'INCOME': 'Renda', 'SHOPPING': 'Compras', 'GROCERIES': 'Supermercado', 'FOOD AND DRINK': 'Alimentação',
    'HEALTHCARE': 'Saúde', 'TRANSPORTATION': 'Transporte', 'ENTERTAINMENT': 'Lazer', 'UTILITIES': 'Contas de Casa',
    'PERSONAL CARE': 'Cuidados Pessoais', 'UNCATEGORIZED': 'Outros'
}

def gerar_excel(df, total_in, total_out, saldo):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Extrato')
    return output.getvalue()

def gerar_pdf(df, total_in, total_out, saldo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(0, 10, "Relatorio Financeiro", ln=True, align='C')
    pdf.set_font("helvetica", '', 12)
    pdf.cell(0, 10, f"Entradas: R$ {total_in:.2f} | Saidas: R$ {total_out:.2f} | Saldo: R$ {saldo:.2f}", ln=True, align='C')
    return bytes(pdf.output())

# ==========================================
# ECRÃ DE LOGIN
# ==========================================
if not st.session_state['logado']:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("E-mail")
            senha = st.text_input("Palavra-passe", type="password")
            if st.form_submit_button("Entrar no Painel"):
                if email == "admin" and senha == "admin":
                    st.session_state.update({'logado': True, 'usuario_id': 999, 'usuario_nome': "Admin", 'is_admin': True})
                    st.rerun()
                else:
                    usuario = verificar_login(email, senha)
                    if usuario:
                        st.session_state.update({'logado': True, 'usuario_id': usuario[0], 'usuario_nome': usuario[1], 'is_admin': bool(usuario[2])})
                        st.rerun()
                    else: st.error("Acesso negado.")

else:
    # CAPTURA DO ID
    if 'novo_item_id' in st.query_params:
        salvar_conexao(st.session_state['usuario_id'], st.query_params['novo_item_id'])
        st.query_params.clear()
        st.rerun()

    # SIDEBAR
    with st.sidebar:
        menu = st.radio("Navegação", ["📊 Dashboard", "🔗 Gerir Bancos", "⚙️ Admin"] if st.session_state['is_admin'] else ["📊 Dashboard", "🔗 Gerir Bancos"])
        if st.button("🚪 Sair"):
            st.session_state.update({'logado': False, 'is_admin': False})
            st.rerun()

    # --- TELA: GERIR BANCOS ---
    if menu == "🔗 Gerir Bancos":
        st.markdown("## 🔗 Conexões Bancárias")
        if st.button("➕ Conectar Novo Banco"):
            st.session_state['abrir_pluggy'] = True
        
        if st.session_state.get('abrir_pluggy'):
            token = gerar_connect_token()
            components.html(f"""
                <script src="https://cdn.pluggy.ai/pluggy-connect/v2.8.2/pluggy-connect.js"></script>
                <div id="pluggy-area"></div>
                <script>
                    const connect = new PluggyConnect({{
                        connectToken: '{token}',
                        onSuccess: (data) => {{ window.parent.location.href = '/?novo_item_id=' + data.item.id; }},
                    }});
                    connect.init();
                </script>
            """, height=500)

        for cx in buscar_conexoes_usuario(st.session_state['usuario_id']):
            st.info(f"🏦 {cx[2]}")
            if st.button("🗑", key=f"del_{cx[0]}"): deletar_conexao(cx[0]); st.rerun()

    # --- TELA: DASHBOARD ---
    elif menu == "📊 Dashboard":
        conexoes = buscar_conexoes_usuario(st.session_state['usuario_id'])
        if not conexoes: st.warning("Conecte um banco.")
        else:
            sel = st.selectbox("Conta:", [c[2] for c in conexoes])
            item_id = [c[1] for c in conexoes if c[2] == sel][0]
            dados = buscar_dados_reais(item_id)
            if isinstance(dados, list):
                df = pd.DataFrame(dados)
                st.metric("Saldo", f"R$ {df['amount'].sum():,.2f}")
                st.dataframe(df[['description', 'amount']])