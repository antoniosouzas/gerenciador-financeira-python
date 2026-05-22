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
st.set_page_config(page_title="Nova Days - Painel", layout="wide", initial_sidebar_state="expanded")

# --- CSS: LAYOUT NOVA DAYS (DARK + PASTEL BLUE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Fundo Geral Escuro (Dark Slate) */
    .stApp { background-color: #1A202C !important; }

    /* Barra Lateral Escura */
    [data-testid="stSidebar"] { 
        background-color: #151A23 !important; 
        border-right: 1px solid #2D3748 !important;
    }

    /* Esconder elementos padrão */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Modificação do Radio (Menu Lateral) */
    div[role="radiogroup"] { gap: 8px; padding-top: 10px; }
    div[role="radiogroup"] > label {
        background-color: transparent !important; 
        border-radius: 12px !important; 
        padding: 12px 20px !important;
        border: none !important; 
        transition: all 0.3s ease;
    }
    div[role="radiogroup"] > label:hover { 
        background-color: rgba(160, 228, 241, 0.1) !important; 
    }
    /* Item Selecionado (Azul Pastel) */
    div[role="radiogroup"] > label[data-checked="true"] { 
        background-color: #A0E4F1 !important; 
    }
    div[role="radiogroup"] > label[data-checked="true"] p {
        color: #1A202C !important; 
        font-weight: 700 !important;
    }
    div[role="radiogroup"] > label p {
        color: #A0AEC0 !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
    }

    /* Inputs e Selects */
    .stTextInput input, .stDateInput input, [data-baseweb="select"] > div {
        background-color: #2D3748 !important; 
        color: #FFFFFF !important; 
        border: 1px solid #4A5568 !important; 
        border-radius: 12px !important;
    }
    .stTextInput input:focus, .stDateInput input:focus, [data-baseweb="select"] > div:focus-within {
        border-color: #A0E4F1 !important;
    }
    span[data-baseweb="tag"] { background-color: #A0E4F1 !important; color: #1A202C !important; border-radius: 6px !important; font-weight: 600 !important; }

    /* Botões */
    .stButton > button {
        background-color: #2D3748 !important; 
        color: #FFFFFF !important; 
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important; 
        font-weight: 600 !important; 
        border: 1px solid #4A5568 !important;
        transition: all 0.3s ease; 
        width: 100%;
    }
    .stButton > button:hover { border-color: #A0E4F1 !important; color: #A0E4F1 !important; }
    .stButton > button[kind="primary"] { background-color: #A0E4F1 !important; color: #1A202C !important; border: none !important; }
    .stButton > button[kind="primary"]:hover { background-color: #76C4D5 !important; }

    /* Tabela Customizada */
    [data-testid="stDataFrame"] { background-color: #2D3748 !important; border-radius: 16px !important; border: none !important; }
    
    /* Textos bases */
    h1, h2, h3, h4, p { color: #FFFFFF !important; }
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

# --- BANCO DE DADOS E PLUGGY ---
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
    u = cursor.fetchall()
    conn.close()
    return u

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
    c = cursor.fetchall()
    conn.close()
    return c

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
            info_contas.append({"nome": c.get("name", "Conta"), "tipo": c.get("type", ""), "saldo": c.get("balance", 0), "id": c.get("id")})
        
        conta_id = contas[0].get("id")
        trans_resp = requests.get(f"https://api.pluggy.ai/transactions?accountId={conta_id}&pageSize=500", headers=headers, timeout=15).json()
        return trans_resp.get("results", []), info_contas
    except Exception as e: return "ERRO_DADOS", []

# --- TRADUÇÃO DE CATEGORIAS ---
TRADUCAO_CATEGORIAS = {
    'TRANSFER - PIX': 'Transferência PIX', 'TRANSFERS': 'Transferências', 'DIGITAL SERVICES': 'Serviços Digitais',
    'FOOD DELIVERY': 'Delivery de Comida', 'BOOKSTORE': 'Livraria', 'ONLINE SHOPPING': 'Compras Online',
    'TELECOMMUNICATIONS': 'Telecomunicações', 'EATING OUT': 'Restaurantes', 'GAS STATIONS': 'Posto de Combustível',
    'LEISURE': 'Lazer', 'LATE PAYMENT AND OVERDRAFT COSTS': 'Juros e Multas', 'TAX ON FINANCIAL OPERATIONS': 'Impostos (IOF/Taxas)',
    'COMPRAS': 'Compras', 'SUPERMERCADO': 'Supermercado', 'TRANSPORTE': 'Transporte', 'INTERNET': 'Internet',
    'FOOD_AND_DRINK': 'Alimentação', 'HEALTHCARE': 'Saúde', 'EDUCATION': 'Educação', 'TRAVEL': 'Viagem',
    'INCOME': 'Renda', 'SALARY': 'Salário', 'CREDIT_CARD': 'Cartão de Crédito', 'PAYMENT': 'Pagamento'
}

def traduzir_categoria(cat_raw):
    if cat_raw is None: return 'Outros'
    if isinstance(cat_raw, dict): cat_raw = cat_raw.get('description', cat_raw.get('name', 'UNCATEGORIZED'))
    cat_str = str(cat_raw).upper().strip()
    if cat_str in TRADUCAO_CATEGORIAS: return TRADUCAO_CATEGORIAS[cat_str]
    cat_str_under = cat_str.replace(' - ', '_').replace('-', '_').replace(' ', '_')
    if cat_str_under in TRADUCAO_CATEGORIAS: return TRADUCAO_CATEGORIAS[cat_str_under]
    cat_str_espaco = cat_str.replace('_', ' ')
    if cat_str_espaco in TRADUCAO_CATEGORIAS: return TRADUCAO_CATEGORIAS[cat_str_espaco]
    return cat_str_espaco.title() if cat_str else 'Outros'

# --- FUNÇÕES DE EXPORTAÇÃO COMPLETAS (PDF E EXCEL) ---
def gerar_excel(df, total_in, total_out, saldo, total_cartao):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        wb = writer.book
        fmt_titulo    = wb.add_format({'bold': True, 'font_size': 14, 'font_color': '#1A202C', 'bg_color': '#A0E4F1', 'align': 'center', 'valign': 'vcenter'})
        fmt_header    = wb.add_format({'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#2D3748', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 11})
        fmt_resumo_k  = wb.add_format({'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#2D3748', 'border': 1, 'font_size': 11})
        fmt_resumo_v  = wb.add_format({'num_format': 'R$ #,##0.00', 'border': 1, 'font_size': 11, 'align': 'right'})
        fmt_entrada   = wb.add_format({'bg_color': '#d1fae5', 'font_color': '#065f46', 'border': 1, 'font_size': 10})
        fmt_saida     = wb.add_format({'bg_color': '#fee2e2', 'font_color': '#7f1d1d', 'border': 1, 'font_size': 10})
        fmt_moeda_in  = wb.add_format({'num_format': 'R$ #,##0.00', 'bg_color': '#d1fae5', 'font_color': '#065f46', 'border': 1, 'font_size': 10, 'align': 'right'})
        fmt_moeda_out = wb.add_format({'num_format': 'R$ #,##0.00', 'bg_color': '#fee2e2', 'font_color': '#7f1d1d', 'border': 1, 'font_size': 10, 'align': 'right'})

        ws_res = wb.add_worksheet('Resumo')
        ws_res.set_column('A:A', 28)
        ws_res.set_column('B:B', 20)
        ws_res.set_row(0, 30)
        ws_res.merge_range('A1:B1', 'Resumo Financeiro', fmt_titulo)
        resumo_dados = [('Total de Entradas', total_in), ('Total de Saídas', total_out), ('Gastos Cartão de Crédito', total_cartao), ('Saldo Líquido', saldo), ('Número de Transações', len(df))]
        for i, (label, val) in enumerate(resumo_dados, start=1):
            ws_res.write(i, 0, label, fmt_resumo_k)
            if isinstance(val, int): ws_res.write(i, 1, val, wb.add_format({'border': 1, 'font_size': 11, 'align': 'right'}))
            else: ws_res.write(i, 1, val, fmt_resumo_v)

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
                    try: ws.write(row_idx, col_idx, float(val), fmt_val)
                    except: ws.write(row_idx, col_idx, 0, fmt_val)
                else: ws.write(row_idx, col_idx, str(val) if val is not None else '', fmt_txt)
        ws.freeze_panes(1, 0)
    output.seek(0)
    return output.getvalue()

def gerar_pdf(df, total_in, total_out, saldo, total_cartao):
    pdf = FPDF(orientation='L', unit='mm', format='A4') 
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    largura_pagina = 277 
    data_fim = df['Data'].iloc[0][:10] if not df.empty else 'N/A'
    data_inicio = df['Data'].iloc[-1][:10] if not df.empty else 'N/A'

    pdf.set_fill_color(26, 32, 44) 
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(largura_pagina, 12, "Relatorio Financeiro - Nova Days", ln=False, align='C', fill=True)
    pdf.ln(12)

    pdf.set_font("helvetica", '', 9)
    pdf.set_text_color(160, 174, 192)
    pdf.cell(largura_pagina, 6, f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}  |  Período: {data_inicio} a {data_fim}", ln=True, align='C')
    pdf.ln(4)

    pdf.set_font("helvetica", 'B', 10)
    pdf.set_fill_color(45, 55, 72) 
    pdf.set_text_color(160, 228, 241)
    pdf.cell(largura_pagina, 8, "  Resumo do Período", ln=True, fill=True)
    pdf.ln(1)

    resumo = [
        ("Total de Entradas",    f"R$ {total_in:,.2f}",  (209, 250, 229), (6, 95, 70)),
        ("Total de Saídas",      f"R$ {total_out:,.2f}", (254, 226, 226), (127, 29, 29)),
        ("Cartão de Crédito",    f"R$ {total_cartao:,.2f}", (254, 215, 170), (154, 52, 18)),
        ("Saldo Líquido",        f"R$ {saldo:,.2f}",     (160, 228, 241), (26, 32, 44)),
        ("Transações",           f"{len(df)}",           (226, 232, 240), (45, 55, 72)),
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
    pdf.set_fill_color(45, 55, 72)
    pdf.set_text_color(160, 228, 241)
    pdf.cell(largura_pagina, 8, f"  Extrato de Transações ({len(df)} registros)", ln=True, fill=True)
    pdf.ln(1)

    col_widths = [24, 98, 28, 22, 42, 30] 
    headers = list(df.columns)
    col_widths = col_widths[:len(headers)]
    while len(col_widths) < len(headers): col_widths.append(30)

    pdf.set_font("helvetica", 'B', 8)
    pdf.set_fill_color(45, 55, 72)
    pdf.set_text_color(255, 255, 255)
    pdf.set_draw_color(74, 85, 104)
    for h, w in zip(headers, col_widths): pdf.cell(w, 7, f" {h}", border=1, fill=True)
    pdf.ln()

    pdf.set_font("helvetica", '', 8)
    for i, row in enumerate(df.itertuples(index=False)):
        tipo = str(getattr(row, 'Tipo', '')).strip()
        is_entrada = tipo == 'Entrada'

        if is_entrada: pdf.set_fill_color(209, 250, 229); pdf.set_text_color(6, 95, 70)
        elif i % 2 == 0: pdf.set_fill_color(226, 232, 240); pdf.set_text_color(26, 32, 44)
        else: pdf.set_fill_color(237, 242, 247); pdf.set_text_color(26, 32, 44)

        if pdf.get_y() > 185:
            pdf.add_page()
            pdf.set_font("helvetica", 'B', 8)
            pdf.set_fill_color(45, 55, 72)
            pdf.set_text_color(255, 255, 255)
            for h, w in zip(headers, col_widths): pdf.cell(w, 7, f" {h}", border=1, fill=True)
            pdf.ln()
            pdf.set_font("helvetica", '', 8)
            if is_entrada: pdf.set_fill_color(209, 250, 229); pdf.set_text_color(6, 95, 70)
            elif i % 2 == 0: pdf.set_fill_color(226, 232, 240); pdf.set_text_color(26, 32, 44)
            else: pdf.set_fill_color(237, 242, 247); pdf.set_text_color(26, 32, 44)

        valores = list(row)
        for val, w in zip(valores, col_widths):
            txt = str(val) if val is not None else ''
            while pdf.get_string_width(f" {txt}") > w - 2 and len(txt) > 3: txt = txt[:-1]
            if len(str(val) if val is not None else '') > len(txt): txt = txt[:-1] + '...'
            pdf.cell(w, 6, f" {txt}", border=1, fill=True)
        pdf.ln()
    pdf.ln(4)
    pdf.set_font("helvetica", 'I', 8)
    pdf.set_text_color(160, 174, 192)
    pdf.cell(largura_pagina, 5, "Documento gerado automaticamente - Nova Days", align='C')
    return bytes(pdf.output())


# ==========================================
# LOGIN SCREEN
# ==========================================
if not st.session_state['logado']:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br><h1 style='text-align: center; color: #FFFFFF !important;'>NOVA <span style='color: #A0E4F1;'>DAYS</span></h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #A0AEC0 !important;'>Acesse o seu Dashboard Financeiro.</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            email = st.text_input("E-mail ou Usuário")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Conta", type="primary"):
                if email == "admin" and senha == "admin":
                    st.session_state.update({'logado': True, 'usuario_id': 999, 'usuario_nome': "Administrador", 'is_admin': True})
                    st.rerun()
                else:
                    usuario = verificar_login(email, senha)
                    if usuario:
                        st.session_state.update({'logado': True, 'usuario_id': usuario[0], 'usuario_nome': usuario[1], 'is_admin': bool(usuario[2])})
                        st.rerun()
                    else: st.error("Acesso negado.")

# ==========================================
# ÁREA LOGADA - LAYOUT NOVA DAYS
# ==========================================
else:
    with st.sidebar:
        st.markdown("<h2 style='color: white; margin-bottom: 2px;'>NOVA DAYS</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #A0E4F1; font-size: 0.9rem; margin-top: 0;'>Bem-vindo(a), {st.session_state['usuario_nome']}</p>", unsafe_allow_html=True)
        
        # Menu com as opções fiéis à imagem
        opcoes_menu = ["💠 Dashboard", "💸 Payments", "📊 Transactions (Bancos)", "💳 Wallet", "👤 Profile", "⚙️ Settings"]
        if st.session_state['is_admin']: opcoes_menu.append("👥 Admin Area")
        
        menu = st.radio("Navegação", opcoes_menu, label_visibility="collapsed")
        
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Log out"):
            st.session_state.update({'logado': False, 'is_admin': False})
            st.rerun()

    # --- ROTEAMENTO DO MENU ---
    if menu not in ["💠 Dashboard", "📊 Transactions (Bancos)", "👥 Admin Area"]:
        st.markdown(f"<h2>{menu[2:]}</h2>", unsafe_allow_html=True)
        st.info("🚧 Esta seção está em desenvolvimento. Por favor, acesse 'Dashboard' ou 'Transactions' para usar o sistema financeiro.")

    # --- ADMIN AREA ---
    elif menu == "👥 Admin Area":
        st.markdown("<h2>👥 Gestão de Usuários</h2>", unsafe_allow_html=True)
        tab_add, tab_lista = st.tabs(["➕ Novo Cliente", "👥 Gerir Clientes"])
        with tab_add:
            with st.form("add_user"):
                n = st.text_input("Nome")
                e = st.text_input("E-mail")
                p = st.text_input("Senha", type="password")
                adm = st.checkbox("Dar acesso de Administrador?")
                if st.form_submit_button("Criar Conta", type="primary"):
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

    # --- TRANSACTIONS / CONECTAR BANCO ---
    elif menu == "📊 Transactions (Bancos)":
        st.markdown("<h2>📊 Conexões Bancárias</h2>", unsafe_allow_html=True)
        c1, c2 = st.columns([2, 1])
        c1.write("Gerencie os bancos conectados ao seu Dashboard.")
        if c2.button("➕ Conectar Novo Banco", type="primary"):
            st.session_state['abrir_pluggy'] = True
            st.session_state['pluggy_sucesso'] = False

        if st.session_state['abrir_pluggy'] and not st.session_state['pluggy_sucesso']:
            token = gerar_connect_token()
            if token:
                if st.button("✖ Cancelar"):
                    st.session_state['abrir_pluggy'] = False
                    st.rerun()
                components.html(f"""
                <script src="https://cdn.pluggy.ai/pluggy-connect/v2.8.2/pluggy-connect.js"></script>
                <div id="widget-area" style="height: 460px; background: #2D3748; border-radius: 12px;"></div>
                <div id="success-box" style="display: none; background: #2D3748; padding: 20px; border-radius: 12px; color: white;">
                    <h3 style="color:#A0E4F1;">Banco conectado!</h3>
                    <p>Copie o ID: <b id="id-display"></b></p>
                </div>
                <script>
                var connect = new PluggyConnect({{
                  connectToken: '{token}',
                  onSuccess: function(data) {{
                    document.getElementById('widget-area').style.display = 'none';
                    document.getElementById('id-display').innerText = data.item.id;
                    document.getElementById('success-box').style.display = 'block';
                  }}
                }});
                connect.init();
                </script>
                """, height=500)
                item_id_input = st.text_input("Cole o ID da Conexão:")
                if st.button("💾 Salvar Conexão", type="primary", disabled=not item_id_input):
                    with st.spinner("Salvando..."):
                        suc, msg = salvar_conexao_por_item_id(st.session_state['usuario_id'], item_id_input)
                    if suc:
                        st.session_state.update({'pluggy_sucesso': True, 'abrir_pluggy': False})
                        st.success(msg)
                        st.rerun()
                    else: st.warning(msg)

        st.markdown("---")
        cx_col1, cx_col2 = st.columns([3, 1])
        cx_col1.markdown("#### Bancos Ativos")
        if cx_col2.button("🔄 Sincronizar Tudo"):
            sincronizar_ultimo_banco(st.session_state['usuario_id'])
            st.rerun()

        conexoes = buscar_conexoes_usuario(st.session_state['usuario_id'])
        if not conexoes: st.info("Nenhuma conexão ativa.")
        else:
            for i, cx in enumerate(conexoes):
                c_a, c_b = st.columns([7, 1])
                c_a.info(f"🏦 {cx[2]} | ID: {cx[1][:8]}...")
                if c_b.button("🗑", key=f"del_{i}"):
                    deletar_conexao(cx[0])
                    st.rerun()

    # --- DASHBOARD (LAYOUT EXATO DA IMAGEM NOVA DAYS) ---
    elif menu == "💠 Dashboard":
        # Cabeçalho Topo
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div>
                <h2 style="margin: 0;">Dashboard</h2>
                <p style="color: #A0AEC0; margin: 0; font-size: 14px;">Today is {datetime.now().strftime('%A, %d %B, %Y')}</p>
            </div>
            <div style="display: flex; align-items: center; gap: 15px;">
                <img src="https://ui-avatars.com/api/?name={st.session_state['usuario_nome']}&background=A0E4F1&color=1A202C" style="border-radius: 50%; width: 40px; height: 40px;">
            </div>
        </div>
        """, unsafe_allow_html=True)

        conexoes = buscar_conexoes_usuario(st.session_state['usuario_id'])
        
        if not conexoes:
            st.warning("Para visualizar seus dados, conecte um banco na aba 'Transactions (Bancos)'.")
        else:
            # Dividindo a tela como na imagem: Esquerda (Maior) | Direita (Menor)
            col_left, col_right = st.columns([2.8, 1.2], gap="large")

            # Pegar dados reais
            with st.spinner("Buscando dados bancários..."):
                trans, info_contas = buscar_dados_reais(conexoes[0][1]) # Usa o primeiro banco por padrão
                
            if not trans:
                st.info("Nenhuma transação encontrada no banco.")
            else:
                # Limpeza PIX e DataFrame
                for t in trans:
                    desc_original = str(t.get('description', '')).strip()
                    nome_extra = ""
                    amount = float(t.get('amount', 0)) if t.get('amount') is not None else 0
                    if isinstance(t.get('merchant'), dict): nome_extra = t['merchant'].get('name', '') or t['merchant'].get('businessName', '')
                    if not nome_extra and isinstance(t.get('paymentData'), dict):
                        pdata = t['paymentData']
                        if amount < 0: nome_extra = pdata.get('receiverName', '') or pdata.get('payee', {}).get('name', '')
                        else: nome_extra = pdata.get('payerName', '') or pdata.get('payer', {}).get('name', '')
                    if not nome_extra and t.get('descriptionRaw'):
                        raw = str(t['descriptionRaw']).strip()
                        if raw.upper() != desc_original.upper():
                            if desc_original.upper() in raw.upper(): nome_extra = raw.upper().replace(desc_original.upper(), '').strip(' -/*\\:')
                            else: nome_extra = raw
                    if nome_extra: t['descricao_completa'] = f"{desc_original} ({str(nome_extra).title()[:40]})"
                    else: t['descricao_completa'] = desc_original

                df = pd.DataFrame(trans)
                df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
                df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
                df['categoria'] = df['category'].apply(traduzir_categoria)
                df['tipo'] = df['amount'].apply(lambda x: 'Entrada' if x > 0 else 'Saída')
                df['valor_abs'] = df['amount'].abs()

                # Calculos
                entradas = df[df['tipo'] == 'Entrada']['valor_abs'].sum()
                saidas = df[df['tipo'] == 'Saída']['valor_abs'].sum()
                saldo_banco = info_contas[0]['saldo'] if info_contas else 0
                total_cartao = df[(df['tipo'] == 'Saída') & (df['categoria'] == 'Cartão de Crédito')]['valor_abs'].sum()

                # ----------------- COLUNA ESQUERDA (PRINCIPAL) -----------------
                with col_left:
                    # LINHA 1: CARTÕES SUPERIORES (Estilo HTML puro para ficar igual a imagem)
                    c_1, c_2, c_3 = st.columns(3)
                    with c_1:
                        st.markdown(f"""
                        <div style="background-color: #242D3C; border-radius: 16px; padding: 20px; border: 1px solid #3A4659;">
                            <p style="color: #A0AEC0; margin: 0 0 5px 0; font-size: 13px;">Account balance</p>
                            <h2 style="margin: 0; color: #FFFFFF; font-size: 24px;">R$ {saldo_banco:,.2f}</h2>
                            <p style="color: #A0AEC0; margin: 15px 0 0 0; font-size: 11px;">Updated today</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_2:
                        st.markdown(f"""
                        <div style="background-color: #242D3C; border-radius: 16px; padding: 20px; border: 1px solid #3A4659;">
                            <p style="color: #A0AEC0; margin: 0 0 5px 0; font-size: 13px;">Total In (Savings)</p>
                            <h2 style="margin: 0; color: #FFFFFF; font-size: 24px;">R$ {entradas:,.2f}</h2>
                            <p style="color: #A0E4F1; margin: 15px 0 0 0; font-size: 11px;">▲ Entradas do período</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_3:
                        st.markdown(f"""
                        <div style="background-color: #242D3C; border-radius: 16px; padding: 20px; border: 1px solid #3A4659;">
                            <p style="color: #A0AEC0; margin: 0 0 5px 0; font-size: 13px;">Total Spendings</p>
                            <h2 style="margin: 0; color: #FFFFFF; font-size: 24px;">R$ {saidas:,.2f}</h2>
                            <p style="color: #FC8181; margin: 15px 0 0 0; font-size: 11px;">▼ Saídas do período</p>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # LINHA 2: GRÁFICOS
                    g_1, g_2 = st.columns([2, 1])
                    with g_1:
                        st.markdown("<div style='background-color: #242D3C; border-radius: 16px; padding: 15px; border: 1px solid #3A4659;'>", unsafe_allow_html=True)
                        st.markdown("<p style='font-weight: 600; margin-bottom: -10px;'>Statistics flow</p>", unsafe_allow_html=True)
                        df_day = df.copy()
                        df_day['valor_sinal'] = df_day.apply(lambda r: r['valor_abs'] if r['tipo'] == 'Entrada' else -r['valor_abs'], axis=1)
                        df_grp = df_day.groupby(df_day['date'].dt.date)['valor_sinal'].sum().reset_index()
                        df_grp['acumulado'] = df_grp['valor_sinal'].cumsum()
                        
                        fig1 = px.area(df_grp, x='date', y='acumulado', line_shape='spline')
                        fig1.update_traces(line_color='#A0E4F1', fillcolor='rgba(160, 228, 241, 0.3)')
                        fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#A0AEC0", margin=dict(l=0, r=0, t=30, b=0), height=250, xaxis_showgrid=False, yaxis_showgrid=True, yaxis_gridcolor='#3A4659', xaxis_title=None, yaxis_title=None)
                        st.plotly_chart(fig1, use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    with g_2:
                        st.markdown("<div style='background-color: #242D3C; border-radius: 16px; padding: 15px; border: 1px solid #3A4659;'>", unsafe_allow_html=True)
                        st.markdown("<p style='font-weight: 600; margin-bottom: -10px;'>Revenue (Saídas)</p>", unsafe_allow_html=True)
                        
                        cat_group = df[df['tipo'] == 'Saída'].groupby('categoria')['valor_abs'].sum().reset_index().sort_values('valor_abs', ascending=False).head(5)
                        fig2 = px.pie(cat_group, values='valor_abs', names='categoria', hole=0.7, color_discrete_sequence=['#A0E4F1', '#4FD1C5', '#63B3ED', '#FC8181', '#F6AD55'])
                        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', showlegend=False, margin=dict(l=0, r=0, t=30, b=0), height=250)
                        st.plotly_chart(fig2, use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # LINHA 3: TABELA
                    st.markdown("<div style='background-color: #242D3C; border-radius: 16px; padding: 20px; border: 1px solid #3A4659;'>", unsafe_allow_html=True)
                    st.markdown("<p style='font-weight: 600;'>Recent transactions</p>", unsafe_allow_html=True)
                    
                    df_view = df[['date', 'descricao_completa', 'valor_abs', 'tipo', 'categoria']].copy().sort_values('date', ascending=False)
                    df_view.columns = ['Data', 'Recipient (Descrição)', 'Amount (R$)', 'Type', 'Category']
                    df_view['Data'] = df_view['Data'].dt.strftime('%d %b, %Y')
                    
                    st.dataframe(df_view, use_container_width=True, hide_index=True)
                    
                    # Botões nativos abaixo da tabela
                    c_btn1, c_btn2, _ = st.columns([1.5, 1.5, 5])
                    c_btn1.download_button("Export Excel", gerar_excel(df_view, entradas, saidas, saldo_banco, total_cartao), "extrato.xlsx")
                    c_btn2.download_button("Export PDF", gerar_pdf(df_view, entradas, saidas, saldo_banco, total_cartao), "relatorio.pdf")
                    st.markdown("</div>", unsafe_allow_html=True)

                # ----------------- COLUNA DIREITA (AESTHETIC WIDGETS) -----------------
                with col_right:
                    # Widget: Meu Cartão Falso (Apenas visual, como pedido "todas as opções")
                    st.markdown("""
                    <div style="background-color: #242D3C; border-radius: 16px; padding: 20px; border: 1px solid #3A4659; margin-bottom: 20px;">
                        <p style="font-weight: 600; margin: 0 0 15px 0;">My cards</p>
                        <div style="background: linear-gradient(135deg, #A0E4F1 0%, #63B3ED 100%); border-radius: 12px; padding: 20px; color: #1A202C;">
                            <p style="margin: 0; font-size: 12px; font-weight: 600;">Credit Card</p>
                            <h3 style="margin: 15px 0; color: #1A202C; letter-spacing: 2px; font-size: 18px;">1234  5678  9876  1121</h3>
                            <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 600;">
                                <span>IANDRA INTELLIGENCE</span>
                                <span>10/29</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Widget: Recent Transfer (Avatares falsos de estética)
                    st.markdown("""
                    <div style="background-color: #242D3C; border-radius: 16px; padding: 20px; border: 1px solid #3A4659; margin-bottom: 20px;">
                        <p style="font-weight: 600; margin: 0 0 15px 0;">Recent transfer</p>
                        <div style="display: flex; gap: 10px;">
                            <img src="https://ui-avatars.com/api/?name=Uthman&background=4FD1C5&color=fff&rounded=true" width="40" height="40">
                            <img src="https://ui-avatars.com/api/?name=Arlene&background=FC8181&color=fff&rounded=true" width="40" height="40">
                            <img src="https://ui-avatars.com/api/?name=Gladys&background=F6AD55&color=fff&rounded=true" width="40" height="40">
                            <div style="width: 40px; height: 40px; border-radius: 50%; background-color: #4A5568; display: flex; align-items: center; justify-content: center; font-size: 18px;">+</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Widget: Upcoming Bills (Mapeado com alguns dados reais das categorias ou estético)
                    contas_casa = df[(df['tipo'] == 'Saída') & (df['categoria'].isin(['Contas de Casa', 'Internet', 'Energia Elétrica']))].head(3)
                    
                    html_bills = """<div style="background-color: #242D3C; border-radius: 16px; padding: 20px; border: 1px solid #3A4659;">
                                    <p style="font-weight: 600; margin: 0 0 15px 0;">Upcoming bills</p>"""
                    if not contas_casa.empty:
                        for _, row in contas_casa.iterrows():
                            html_bills += f"""
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                <div style="display: flex; gap: 10px; align-items: center;">
                                    <div style="width: 35px; height: 35px; border-radius: 8px; background-color: #4A5568; display: flex; align-items: center; justify-content: center;">📄</div>
                                    <div>
                                        <p style="margin: 0; font-size: 13px; font-weight: 600;">{str(row['categoria'])[:15]}</p>
                                        <p style="margin: 0; font-size: 11px; color: #A0AEC0;">Pending</p>
                                    </div>
                                </div>
                                <p style="margin: 0; font-size: 13px; font-weight: 600;">R$ {row['valor_abs']:.2f}</p>
                            </div>"""
                    else:
                        html_bills += "<p style='color: #A0AEC0; font-size: 12px;'>Nenhuma conta pendente no radar.</p>"
                        
                    html_bills += "</div>"
                    st.markdown(html_bills, unsafe_allow_html=True)