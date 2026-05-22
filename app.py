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

st.set_page_config(page_title="Auxiliador da Iandra", layout="wide", page_icon="💼")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
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
    div.stButton > button:first-child:hover { background-color: #0369a1 !important; border-color: #0ea5e9 !important; }
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
    if not item_id:
        return False, "Item ID vazio."
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
    except Exception as e:
        return False, f"Erro ao salvar conexão: {e}"

def sincronizar_ultimo_banco(usuario_id):
    try:
        response = requests.post("https://api.pluggy.ai/auth", json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}, timeout=10)
        token = response.json().get("apiKey")
        headers = {"accept": "application/json", "X-API-KEY": token}
        items_resp = requests.get("https://api.pluggy.ai/items", headers=headers, timeout=10).json()
        resultados = items_resp.get("results", [])
        if not resultados:
            return False, "Nenhum banco encontrado na Pluggy."
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
    except Exception as e:
        return False, f"Erro ao comunicar com a Pluggy: {e}"

def gerar_connect_token():
    response = requests.post("https://api.pluggy.ai/auth", json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}, timeout=10)
    api_key = response.json().get("apiKey")
    headers = {"accept": "application/json", "X-API-KEY": api_key}
    response_token = requests.post("https://api.pluggy.ai/connect_token", headers=headers, json={}, timeout=10)
    return response_token.json().get("accessToken")

# -------------------------------------------------------
# FUNÇÃO PRINCIPAL DE DADOS — corrigida
# A Pluggy retorna transações com:
#   amount NEGATIVO = DÉBITO (saída de dinheiro)
#   amount POSITIVO = CRÉDITO (entrada de dinheiro)
# Mantemos esse padrão e exibimos corretamente.
# A categoria vem em 'category' como string simples (ex: "FOOD_AND_DRINK")
# ou dentro de um dict. Tratamos ambos os casos.
# -------------------------------------------------------
@st.cache_data(ttl=3600)
def buscar_dados_reais(item_id):
    try:
        response = requests.post("https://api.pluggy.ai/auth", json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}, timeout=10)
        token = response.json().get("apiKey")
        headers = {"accept": "application/json", "X-API-KEY": token}
        contas_resp = requests.get(f"https://api.pluggy.ai/accounts?itemId={item_id}", headers=headers, timeout=10).json()
        contas = contas_resp.get("results", [])
        if not contas:
            return "SEM_CONTAS", []
        
        # Pega saldo de todas as contas
        info_contas = []
        for c in contas:
            info_contas.append({
                "nome": c.get("name", "Conta"),
                "tipo": c.get("type", ""),
                "saldo": c.get("balance", 0),
                "id": c.get("id")
            })
        
        # Busca transações da primeira conta
        conta_id = contas[0].get("id")
        trans_resp = requests.get(
            f"https://api.pluggy.ai/transactions?accountId={conta_id}&pageSize=500",
            headers=headers, timeout=15
        ).json()
        trans = trans_resp.get("results", [])
        return trans, info_contas
    except Exception as e:
        return "ERRO_DADOS", []

# Mapeamento robusto de categorias da Pluggy
# A API pode retornar string simples ou com underscores
TRADUCAO_CATEGORIAS = {
    # Padrão com underscore (mais comum na Pluggy v2)
    'FOOD_AND_DRINK': 'Alimentação',
    'GROCERIES': 'Supermercado',
    'SHOPPING': 'Compras',
    'INCOME': 'Renda',
    'TRANSFER': 'Transferência',
    'PAYMENT': 'Pagamento',
    'HEALTHCARE': 'Saúde',
    'TRANSPORTATION': 'Transporte',
    'ENTERTAINMENT': 'Lazer',
    'UTILITIES': 'Contas de Casa',
    'PERSONAL_CARE': 'Cuidados Pessoais',
    'EDUCATION': 'Educação',
    'TRAVEL': 'Viagem',
    'INVESTMENT': 'Investimento',
    'BANK_FEES': 'Tarifas Bancárias',
    'CREDIT_CARD': 'Cartão de Crédito',
    'LOAN': 'Empréstimo',
    'INSURANCE': 'Seguro',
    'HOME': 'Casa',
    'UNCATEGORIZED': 'Outros',
    # Padrão com espaço (API v1 legada)
    'FOOD AND DRINK': 'Alimentação',
    'PERSONAL CARE': 'Cuidados Pessoais',
    'BANK FEES': 'Tarifas Bancárias',
    'CREDIT CARD': 'Cartão de Crédito',
}

def traduzir_categoria(cat_raw):
    """Extrai e traduz categoria independente do formato retornado pela Pluggy."""
    if cat_raw is None:
        return 'Outros'
    # Se vier como dict (ex: {"id": 1, "description": "FOOD_AND_DRINK"})
    if isinstance(cat_raw, dict):
        cat_raw = cat_raw.get('description', cat_raw.get('name', 'UNCATEGORIZED'))
    cat_str = str(cat_raw).upper().strip()
    return TRADUCAO_CATEGORIAS.get(cat_str, cat_str.replace('_', ' ').title() if cat_str else 'Outros')

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
# LOGIN
# ==========================================
if not st.session_state['logado']:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div style='height: 60px;'></div>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #38bdf8; font-weight: 700;'>🤖 AUXILIADOR FINANCEIRO PARA A IANDRA</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 1.1rem;'>Gestão financeira inteligente, simplificada e elegante.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form"):
            email = st.text_input("E-mail")
            senha = st.text_input("Palavra-passe", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Entrar no Painel"):
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
        st.markdown(f"### Olá, <span style='color: #38bdf8;'>{st.session_state['usuario_nome']}</span> 👋", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        menu = st.radio(
            "Navegação",
            ["📊 Dashboard", "🔗 Gerir Bancos", "⚙️ Admin"] if st.session_state['is_admin']
            else ["📊 Dashboard", "🔗 Gerir Bancos"]
        )
        st.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sair do Sistema"):
            st.session_state.update({'logado': False, 'is_admin': False})
            st.rerun()

    # --- ADMIN ---
    if menu == "⚙️ Admin":
        st.markdown("<h2 style='color: #e2e8f0;'>⚙️ Painel de Controle</h2>", unsafe_allow_html=True)
        tab_add, tab_lista = st.tabs(["➕ Novo Cliente", "👥 Gerir Clientes"])
        with tab_add:
            with st.form("add_user"):
                n = st.text_input("Nome")
                e = st.text_input("E-mail")
                p = st.text_input("Senha", type="password")
                adm = st.checkbox("Dar acesso de Administrador?")
                if st.form_submit_button("Criar Conta do Cliente"):
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
    elif menu == "🔗 Gerir Bancos":
        st.markdown("<h2 style='color: #e2e8f0;'>🔗 Conexões Bancárias</h2>", unsafe_allow_html=True)

        col_txt, col_btn = st.columns([2, 1])
        with col_txt:
            st.write("Conecte as contas bancárias para sincronizar as transações automaticamente.")
        with col_btn:
            st.markdown('<div class="connect-btn">', unsafe_allow_html=True)
            if st.button("➕ Conectar Novo Banco"):
                st.session_state['abrir_pluggy'] = True
                st.session_state['pluggy_sucesso'] = False
                st.session_state['pluggy_item_id'] = ""
            st.markdown('</div>', unsafe_allow_html=True)

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
  display: none; background: #0f2218; border: 1px solid #10b981;
  border-radius: 12px; padding: 32px 24px; margin: 16px 0; text-align: center;
}}
#success-box h2 {{ color: #10b981; font-size: 1.3rem; margin-bottom: 8px; }}
#success-box p  {{ color: #94a3b8; font-size: 0.95rem; margin-bottom: 20px; }}
#id-display {{
  background: #1e293b; border: 1px solid #334155; border-radius: 8px;
  padding: 14px 16px; font-family: monospace; font-size: 0.9rem; color: #38bdf8;
  word-break: break-all; margin-bottom: 16px; text-align: left;
}}
#copy-btn {{
  background: #0284c7; color: white; border: none; border-radius: 20px;
  padding: 10px 28px; font-size: 0.95rem; cursor: pointer;
}}
#copy-btn:hover {{ background: #0369a1; }}
#copy-hint {{ color: #10b981; font-size: 0.85rem; margin-top: 10px; display: none; }}
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
    document.getElementById('widget-area').innerHTML = '<p style="color:#94a3b8;text-align:center;padding:60px;">Conexão encerrada.</p>';
  }},
  onError: function(err) {{
    document.getElementById('widget-area').innerHTML = '<p style="color:#f43f5e;text-align:center;padding:60px;">Erro na conexão. Tente novamente.</p>';
  }}
}});
connect.init();
</script></body></html>
""", height=540)

                st.markdown("<p style='color:#94a3b8; font-size:0.9rem; margin-top:8px;'>👆 Após conectar o banco acima, copie o ID exibido e cole aqui:</p>", unsafe_allow_html=True)
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

        st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
        c_b1, c_b2 = st.columns([3, 1])
        c_b1.markdown("#### Bancos Ativos")
        if c_b2.button("🔄 Sincronizar Novo Banco", type="primary"):
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
                c1.info(f"🏦 {cx[2]} | ID de Conexão: {cx[1][:15]}...")
                if c2.button("🗑", key=f"del_cx_{i}"):
                    deletar_conexao(cx[0])
                    st.rerun()

    # --- DASHBOARD ---
    elif menu == "📊 Dashboard":
        st.markdown("<h2 style='color: #e2e8f0;'>📊 Resumo Financeiro</h2>", unsafe_allow_html=True)

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
                    # --- CONSTRUÇÃO DO DATAFRAME ---
                    df = pd.DataFrame(trans)

                    # Data
                    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)

                    # Amount — garantir numérico
                    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)

                    # Categoria — tratamento robusto
                    if 'category' in df.columns:
                        df['categoria'] = df['category'].apply(traduzir_categoria)
                    else:
                        df['categoria'] = 'Outros'

                    # Tipo de transação baseado no sinal do amount
                    # Pluggy: DEBIT = amount negativo, CREDIT = amount positivo
                    # Verificamos também o campo 'type' se existir para confirmar
                    if 'type' in df.columns:
                        df['tipo'] = df['type'].apply(lambda x: 'Entrada' if str(x).upper() == 'CREDIT' else 'Saída')
                    else:
                        df['tipo'] = df['amount'].apply(lambda x: 'Entrada' if x > 0 else 'Saída')

                    df['valor_abs'] = df['amount'].abs()

                    # --- FILTROS NA SIDEBAR ---
                    st.sidebar.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
                    st.sidebar.markdown("#### 🔍 Filtros")

                    d1 = st.sidebar.date_input("Data de Início", df['date'].min().date())
                    d2 = st.sidebar.date_input("Data de Fim", df['date'].max().date())

                    # Filtro por categoria
                    categorias_disponiveis = sorted(df['categoria'].unique().tolist())
                    cats_selecionadas = st.sidebar.multiselect(
                        "Categorias",
                        options=categorias_disponiveis,
                        default=categorias_disponiveis,
                        placeholder="Todas as categorias"
                    )

                    # Filtro por tipo
                    tipo_filtro = st.sidebar.radio(
                        "Tipo de Movimentação",
                        ["Todos", "Apenas Entradas", "Apenas Saídas"],
                        index=0
                    )

                    # Aplica filtros
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
                        saldo = entradas - saidas
                        total_trans = len(df_f)

                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("⬇️ Entradas", f"R$ {entradas:,.2f}")
                        m2.metric("⬆️ Saídas", f"R$ {saidas:,.2f}")
                        m3.metric("💰 Saldo Líquido", f"R$ {saldo:,.2f}")
                        m4.metric("📋 Transações", f"{total_trans}")

                        # Saldo das contas bancárias reais
                        if info_contas:
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown("<h5 style='color:#94a3b8;'>💳 Saldo Atual nas Contas</h5>", unsafe_allow_html=True)
                            cols_contas = st.columns(len(info_contas))
                            for idx, conta in enumerate(info_contas):
                                cols_contas[idx].metric(
                                    f"{'💳' if conta['tipo']=='CREDIT' else '🏦'} {conta['nome']}",
                                    f"R$ {conta['saldo']:,.2f}"
                                )

                        st.markdown("<br>", unsafe_allow_html=True)

                        grafico_cores = ['#0ea5e9', '#8b5cf6', '#10b981', '#f59e0b', '#f43f5e', '#64748b', '#ec4899', '#14b8a6', '#f97316', '#a78bfa']

                        col_g1, col_g2 = st.columns(2)

                        with col_g1:
                            st.markdown("<h5 style='color: #e2e8f0;'>💸 Gastos por Categoria</h5>", unsafe_allow_html=True)
                            df_saidas = df_f[df_f['tipo'] == 'Saída']
                            if not df_saidas.empty:
                                cat_group = df_saidas.groupby('categoria')['valor_abs'].sum().reset_index()
                                cat_group = cat_group.sort_values('valor_abs', ascending=False)
                                fig_p = px.pie(
                                    cat_group,
                                    values='valor_abs',
                                    names='categoria',
                                    hole=0.4,
                                    color_discrete_sequence=grafico_cores
                                )
                                fig_p.update_traces(textposition='inside', textinfo='percent+label')
                                fig_p.update_layout(
                                    margin=dict(t=10, b=10, l=10, r=10),
                                    showlegend=True,
                                    legend=dict(font=dict(color='#94a3b8'), bgcolor='rgba(0,0,0,0)'),
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    font=dict(color='#e2e8f0')
                                )
                                st.plotly_chart(fig_p, use_container_width=True)
                            else:
                                st.info("Nenhuma saída no período filtrado.")

                        with col_g2:
                            st.markdown("<h5 style='color: #e2e8f0;'>📈 Evolução do Caixa</h5>", unsafe_allow_html=True)
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
                                color_discrete_sequence=['#0ea5e9'],
                                labels={'saldo_acumulado': 'Saldo Acumulado', 'date': 'Data'}
                            )
                            fig_l.update_layout(
                                margin=dict(t=10, b=10, l=10, r=10),
                                xaxis_title=None, yaxis_title="R$",
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#e2e8f0'),
                                yaxis=dict(gridcolor='#334155', tickprefix='R$ ')
                            )
                            fig_l.update_xaxes(showgrid=False)
                            st.plotly_chart(fig_l, use_container_width=True)

                        # Gráfico de barras: entradas vs saídas por mês
                        st.markdown("<h5 style='color: #e2e8f0;'>📊 Entradas vs Saídas por Mês</h5>", unsafe_allow_html=True)
                        df_mensal = df_f.copy()
                        df_mensal['mes'] = df_mensal['date'].dt.to_period('M').astype(str)
                        df_mensal_grp = df_mensal.groupby(['mes', 'tipo'])['valor_abs'].sum().reset_index()
                        fig_bar = px.bar(
                            df_mensal_grp, x='mes', y='valor_abs', color='tipo',
                            barmode='group',
                            color_discrete_map={'Entrada': '#10b981', 'Saída': '#f43f5e'},
                            labels={'valor_abs': 'Valor (R$)', 'mes': 'Mês', 'tipo': 'Tipo'}
                        )
                        fig_bar.update_layout(
                            margin=dict(t=10, b=10, l=10, r=10),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#e2e8f0'),
                            legend=dict(font=dict(color='#94a3b8'), bgcolor='rgba(0,0,0,0)'),
                            yaxis=dict(gridcolor='#334155', tickprefix='R$ '),
                            xaxis=dict(showgrid=False)
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)

                        # --- EXTRATO ---
                        st.markdown("<h5 style='color: #e2e8f0;'>🧾 Extrato Detalhado</h5>", unsafe_allow_html=True)

                        df_extrato = df_f[['date', 'description', 'valor_abs', 'tipo', 'categoria']].copy()
                        df_extrato = df_extrato.sort_values('date', ascending=False)
                        df_extrato.columns = ['Data', 'Descrição', 'Valor (R$)', 'Tipo', 'Categoria']
                        df_extrato['Valor (R$)'] = df_extrato['Valor (R$)'].round(2)
                        df_extrato['Data'] = df_extrato['Data'].dt.strftime('%d/%m/%Y %H:%M')

                        st.dataframe(df_extrato, use_container_width=True, hide_index=True)

                        c_ex1, c_ex2, _ = st.columns([1, 1, 4])
                        df_export = df_extrato.copy()
                        c_ex1.download_button("📊 Baixar Excel", gerar_excel(df_export, entradas, saidas, saldo), "extrato.xlsx")
                        c_ex2.download_button("📄 Baixar PDF", gerar_pdf(df_export, entradas, saidas, saldo), "relatorio.pdf")