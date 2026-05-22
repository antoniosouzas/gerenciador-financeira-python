import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
import sqlite3
import hashlib
from dotenv import load_dotenv
import io
from fpdf import FPDF
import streamlit.components.v1 as components

# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO CSS
st.set_page_config(page_title="Fintech Pro | Dashboard", layout="wide", page_icon="💰")

# Injeção de CSS para transformar a interface
st.markdown("""
    <style>
    /* Cores Globais e Fundo */
    .main { background-color: #f8f9fa; }
    
    /* Estilização de Botões */
    div.stButton > button:first-child {
        background-color: #0066ff;
        color: white;
        border-radius: 12px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 6px rgba(0, 102, 255, 0.2);
        transition: all 0.3s ease;
        width: 100%;
    }
    div.stButton > button:first-child:hover {
        background-color: #0052cc;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 102, 255, 0.3);
    }
    
    /* Botão de Destaque (Conectar) */
    .connect-btn button {
        background: linear-gradient(135deg, #0066ff 0%, #00d1b2 100%) !important;
        font-size: 1.2rem !important;
        height: 4rem !important;
    }

    /* Estilização de Cards e Containers */
    [data-testid="stMetricContainer"] {
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #efefef;
    }
    
    /* Títulos e Textos */
    h1, h2, h3 { color: #1e293b; font-family: 'Inter', sans-serif; }
    .stMarkdown p { color: #64748b; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    
    /* Esconder o menu padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

load_dotenv()
CLIENT_ID = os.getenv("PLUGGY_CLIENT_ID")
CLIENT_SECRET = os.getenv("PLUGGY_CLIENT_SECRET")

# --- INICIALIZAÇÃO DA SESSÃO ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario_nome' not in st.session_state: st.session_state['usuario_nome'] = ""
if 'usuario_id' not in st.session_state: st.session_state['usuario_id'] = None
if 'is_admin' not in st.session_state: st.session_state['is_admin'] = False
if 'abrir_pluggy' not in st.session_state: st.session_state['abrir_pluggy'] = False

# --- FUNÇÕES DE BASE DE DADOS ---
def hash_senha(senha): return hashlib.sha256(senha.encode()).hexdigest()

def verificar_login(email, senha):
    conn = sqlite3.connect('dashboard_financeiro.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, is_admin FROM usuarios WHERE email = ? AND senha = ?", (email, hash_senha(senha)))
    usuario = cursor.fetchone()
    conn.close()
    return usuario 

def registrar_usuario(nome, email, senha, is_admin=0):
    conn = sqlite3.connect('dashboard_financeiro.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (nome, email, senha, is_admin) VALUES (?, ?, ?, ?)", (nome, email, hash_senha(senha), is_admin))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def buscar_todos_usuarios():
    conn = sqlite3.connect('dashboard_financeiro.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, email, is_admin, data_cadastro FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios

def deletar_usuario_completo(usuario_id):
    conn = sqlite3.connect('dashboard_financeiro.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conexoes_bancarias WHERE usuario_id = ?", (usuario_id,))
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    conn.commit()
    conn.close()

def salvar_conexao(usuario_id, pluggy_item_id, nome_instituicao="Nova Conta"):
    conn = sqlite3.connect('dashboard_financeiro.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO conexoes_bancarias (usuario_id, pluggy_item_id, nome_instituicao) VALUES (?, ?, ?)', (usuario_id, pluggy_item_id, nome_instituicao))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def buscar_conexoes_usuario(usuario_id):
    conn = sqlite3.connect('dashboard_financeiro.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, pluggy_item_id, nome_instituicao, data_conexao FROM conexoes_bancarias WHERE usuario_id = ?', (usuario_id,))
    conexoes = cursor.fetchall()
    conn.close()
    return conexoes

def deletar_conexao(conexao_id):
    conn = sqlite3.connect('dashboard_financeiro.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conexoes_bancarias WHERE id = ?", (conexao_id,))
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
        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #0066ff;'>Fintech Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Gestão financeira inteligente para o seu negócio.</p>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("<div style='background-color: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
            with st.form("login_form"):
                email = st.text_input("E-mail")
                senha = st.text_input("Palavra-passe", type="password")
                if st.form_submit_button("Entrar no Dashboard"):
                    usuario = verificar_login(email, senha)
                    if usuario:
                        st.session_state['logado'], st.session_state['usuario_id'], st.session_state['usuario_nome'], st.session_state['is_admin'] = True, usuario[0], usuario[1], bool(usuario[2])
                        st.rerun()
                    else: st.error("Acesso negado. Verifique os seus dados.")
            st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# ÁREA LOGADA
# ==========================================
else:
    # Sidebar Estilizada
    with st.sidebar:
        st.markdown(f"### Bem-vindo, <br><span style='color: #0066ff;'>{st.session_state['usuario_nome']}</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        menu = st.radio("Navegação", ["📊 Dashboard", "🔗 Gerir Bancos", "⚙️ Admin"] if st.session_state['is_admin'] else ["📊 Dashboard", "🔗 Gerir Bancos"])
        
        st.markdown("<div style='height: 250px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sair do Sistema"):
            st.session_state.update({'logado': False, 'is_admin': False})
            st.rerun()

    # --- TELA: ADMIN ---
    if menu == "⚙️ Admin":
        st.title("⚙️ Painel de Controle")
        tab_add, tab_lista = st.tabs(["➕ Novo Cliente", "👥 Gerir Clientes"])
        
        with tab_add:
            with st.form("add_user"):
                n, e, p = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
                adm = st.checkbox("Dar acesso de Administrador?")
                if st.form_submit_button("Criar Conta do Cliente"):
                    if n and e and p:
                        if registrar_usuario(n, e, p, 1 if adm else 0): st.success(f"Cliente {n} criado!")
                        else: st.error("Erro ou e-mail já existe.")
        
        with tab_lista:
            for u in buscar_todos_usuarios():
                with st.expander(f"{u[1]} ({u[2]})"):
                    if u[0] != st.session_state['usuario_id']:
                        if st.button("Eliminar", key=f"del_{u[0]}"):
                            deletar_usuario_completo(u[0])
                            st.rerun()

    # --- TELA: GERIR BANCOS ---
    elif menu == "🔗 Gerir Bancos":
        st.title("🔗 Conexões Bancárias")
        
        # Header de Conexão com Botão Estilizado
        col_txt, col_btn = st.columns([2, 1])
        with col_txt:
            st.write("Conecte os seus bancos para sincronizar as transações em tempo real.")
        with col_btn:
            st.markdown('<div class="connect-btn">', unsafe_allow_html=True)
            if st.button("➕ Conectar Novo Banco"):
                st.session_state['abrir_pluggy'] = True
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state['abrir_pluggy']:
            token = gerar_connect_token()
            if token:
                if st.button("✖ Fechar Janela de Conexão"): 
                    st.session_state['abrir_pluggy'] = False
                    st.rerun()
                components.html(f"""
                    <script src="https://cdn.pluggy.ai/pluggy-connect/v2.8.2/pluggy-connect.js"></script>
                    <div id="pluggy-area"></div>
                    <script>
                        const connect = new PluggyConnect({{
                            connectToken: '{token}',
                            onSuccess: (data) => {{ window.parent.location.href = '/?novo_item_id=' + data.item.id; }},
                            onClose: () => {{ document.getElementById('pluggy-area').innerHTML = 'Conexão encerrada.'; }}
                        }});
                        connect.init();
                    </script>
                """, height=600)

        st.markdown("### Bancos Ativos")
        for i, cx in enumerate(buscar_conexoes_usuario(st.session_state['usuario_id'])):
            c1, c2 = st.columns([7, 1])
            c1.info(f"🏦 {cx[2]} | Adicionado em {cx[3][:10]}")
            if c2.button("🗑", key=f"del_cx_{i}"):
                deletar_conexao(cx[0])
                st.rerun()

    # --- TELA: DASHBOARD ---
    elif menu == "📊 Dashboard":
        st.title("📊 Seu Resumo Financeiro")
        
        conexoes = buscar_conexoes_usuario(st.session_state['usuario_id'])
        if not conexoes:
            st.warning("Nenhum banco conectado. Vá em 'Gerir Bancos' para começar.")
        else:
            bancos_dict = {f"{c[2]} ({c[1][:5]})": c[1] for c in conexoes}
            sel_banco = st.selectbox("Selecione a conta para visualizar:", list(bancos_dict.keys()))
            
            with st.spinner("Sincronizando dados..."):
                dados = buscar_dados_reais(bancos_dict[sel_banco])
                
            if isinstance(dados, list):
                df = pd.DataFrame(dados)
                df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
                df['amount'] = pd.to_numeric(df['amount'])
                df['category'] = df['category'].apply(lambda x: TRADUCAO_CATEGORIAS.get(str(x).upper(), "Outros"))

                # Filtros de Data Modernos
                st.sidebar.markdown("---")
                d1 = st.sidebar.date_input("Início", df['date'].min())
                d2 = st.sidebar.date_input("Fim", df['date'].max())
                
                df_f = df[(df['date'].dt.date >= d1) & (df['date'].dt.date <= d2)]
                in_v = df_f[df_f['amount'] > 0]['amount'].sum()
                out_v = df_f[df_f['amount'] < 0]['amount'].sum()
                saldo = in_v + out_v

                # Métricas em Cards
                m1, m2, m3 = st.columns(3)
                m1.metric("Entradas", f"R$ {in_v:,.2f}", delta_color="normal")
                m2.metric("Saídas", f"R$ {abs(out_v):,.2f}", delta_color="inverse")
                m3.metric("Saldo Líquido", f"R$ {saldo:,.2f}")

                st.markdown("<br>", unsafe_allow_html=True)
                
                # Gráficos de Alta Performance
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.markdown("##### Gastos por Categoria")
                    fig_p = px.pie(df_f[df_f['amount'] < 0], values=df_f[df_f['amount'] < 0]['amount'].abs(), names='category', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_p.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
                    st.plotly_chart(fig_p, use_container_width=True)
                
                with col_g2:
                    st.markdown("##### Evolução Diária")
                    df_day = df_f.groupby(df_f['date'].dt.date)['amount'].sum().reset_index()
                    fig_l = px.area(df_day, x='date', y='amount', line_shape='spline', color_discrete_sequence=['#0066ff'])
                    fig_l.update_layout(margin=dict(t=0, b=0, l=0, r=0), xaxis_title=None, yaxis_title=None)
                    st.plotly_chart(fig_l, use_container_width=True)

                st.markdown("##### Extrato Recente")
                st.dataframe(df_f[['date', 'description', 'amount', 'category']].sort_values('date', ascending=False), use_container_width=True, hide_index=True)
                
                # Exportação
                c_ex1, c_ex2, _ = st.columns([1, 1, 4])
                c_ex1.download_button("Excel", gerar_excel(df_f, in_v, out_v, saldo), "extrato.xlsx")
                c_ex2.download_button("PDF", gerar_pdf(df_f, in_v, out_v, saldo), "relatorio.pdf")
            else: st.error("Não foi possível carregar os dados deste banco.")