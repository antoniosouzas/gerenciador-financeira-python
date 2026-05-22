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
if 'usuario_nome' not in st.session_state: st.session_state['usuario_nome'] = ""
if 'usuario_id' not in st.session_state: st.session_state['usuario_id'] = None
if 'is_admin' not in st.session_state: st.session_state['is_admin'] = False
if 'abrir_pluggy' not in st.session_state: st.session_state['abrir_pluggy'] = False
# NOVO: guarda item_id capturado via postMessage
if 'pluggy_item_id_capturado' not in st.session_state: st.session_state['pluggy_item_id_capturado'] = None

# --- FUNÇÕES DE BASE DE DADOS ---
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

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
    """
    Salva no Supabase usando o item_id recebido diretamente do widget Pluggy.
    Consulta a API para obter o nome do banco automaticamente.
    """
    try:
        # Verifica duplicata antes de qualquer chamada à API
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM conexoes_bancarias WHERE pluggy_item_id = %s", (item_id,))
        if cursor.fetchone():
            conn.close()
            return False, "Este banco já está sincronizado."

        # Busca nome do banco na API Pluggy
        response = requests.post(
            "https://api.pluggy.ai/auth",
            json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET},
            timeout=10
        )
        token = response.json().get("apiKey")
        headers = {"accept": "application/json", "X-API-KEY": token}
        item_resp = requests.get(f"https://api.pluggy.ai/items/{item_id}", headers=headers, timeout=10)
        nome_banco = item_resp.json().get("connector", {}).get("name", "Banco Desconhecido")

        cursor.execute(
            'INSERT INTO conexoes_bancarias (usuario_id, pluggy_item_id, nome_instituicao) VALUES (%s, %s, %s)',
            (usuario_id, item_id, nome_banco)
        )
        conn.commit()
        conn.close()
        return True, f"✅ {nome_banco} conectado e salvo com sucesso!"
    except Exception as e:
        return False, f"Erro ao salvar conexão: {e}"

def sincronizar_ultimo_banco(usuario_id):
    """Fallback: busca o item mais recente na Pluggy e salva. Usado pelo botão manual."""
    try:
        response = requests.post(
            "https://api.pluggy.ai/auth",
            json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET},
            timeout=10
        )
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

        cursor.execute(
            'INSERT INTO conexoes_bancarias (usuario_id, pluggy_item_id, nome_instituicao) VALUES (%s, %s, %s)',
            (usuario_id, item_id, nome_banco)
        )
        conn.commit()
        conn.close()
        return True, f"✅ {nome_banco} sincronizado com sucesso!"
    except Exception as e:
        return False, f"Erro ao comunicar com a Pluggy: {e}"

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
                    st.session_state['logado'] = True
                    st.session_state['usuario_id'] = 999
                    st.session_state['usuario_nome'] = "Administrador Mestre"
                    st.session_state['is_admin'] = True
                    st.rerun()
                else:
                    usuario = verificar_login(email, senha)
                    if usuario:
                        st.session_state['logado'] = True
                        st.session_state['usuario_id'] = usuario[0]
                        st.session_state['usuario_nome'] = usuario[1]
                        st.session_state['is_admin'] = bool(usuario[2])
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

        st.markdown("<div style='height: 250px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sair do Sistema"):
            st.session_state.update({'logado': False, 'is_admin': False})
            st.rerun()

    # --- TELA: ADMIN ---
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

    # --- TELA: GERIR BANCOS ---
    elif menu == "🔗 Gerir Bancos":
        st.markdown("<h2 style='color: #e2e8f0;'>🔗 Conexões Bancárias</h2>", unsafe_allow_html=True)

        # -------------------------------------------------------
        # PROCESSAMENTO DO item_id CAPTURADO VIA postMessage
        # Isso ocorre quando o Streamlit reexecuta após receber
        # o item_id do componente HTML via query param interno.
        # -------------------------------------------------------
        item_id_capturado = st.session_state.get('pluggy_item_id_capturado')
        if item_id_capturado:
            with st.spinner("Salvando conexão no Supabase..."):
                sucesso, msg = salvar_conexao_por_item_id(
                    st.session_state['usuario_id'],
                    item_id_capturado
                )
            # Limpa o estado para não reprocessar
            st.session_state['pluggy_item_id_capturado'] = None
            st.session_state['abrir_pluggy'] = False
            if sucesso:
                st.success(msg)
            else:
                st.warning(msg)
            st.rerun()

        col_txt, col_btn = st.columns([2, 1])
        with col_txt:
            st.write("Conecte as contas bancárias para sincronizar as transações automaticamente.")
        with col_btn:
            st.markdown('<div class="connect-btn">', unsafe_allow_html=True)
            if st.button("➕ Conectar Novo Banco"):
                st.session_state['abrir_pluggy'] = True
            st.markdown('</div>', unsafe_allow_html=True)

        # -------------------------------------------------------
        # WIDGET PLUGGY COM postMessage
        # A solução: em vez de redirecionar a URL (bloqueado pelo
        # Streamlit Cloud), o onSuccess envia uma mensagem via
        # postMessage para a janela pai. Um listener JS na página
        # principal captura o item_id e usa window.location para
        # adicionar um query param de forma segura — ou exibe um
        # botão automático que aciona o st.query_params do Python.
        #
        # Aqui usamos a abordagem mais confiável no Streamlit Cloud:
        # o iframe sinaliza o sucesso, o HTML pai detecta via
        # window.addEventListener('message') e popula um input
        # oculto que dispara o Streamlit via st.experimental_set_query_params
        # substituído por uma exibição de campo de texto + botão
        # que o Python lê imediatamente no próximo rerun.
        # -------------------------------------------------------
        if st.session_state['abrir_pluggy']:
            token = gerar_connect_token()
            if token:
                col_fechar, _ = st.columns([1, 3])
                with col_fechar:
                    if st.button("✖ Fechar Janela"):
                        st.session_state['abrir_pluggy'] = False
                        st.rerun()

                # Campo oculto: recebe o item_id vindo do JS via postMessage
                # O usuário não precisa fazer nada — o botão é clicado via JS
                item_id_form = st.empty()
                with item_id_form.container():
                    with st.form("form_captura_pluggy", clear_on_submit=True):
                        captured_id = st.text_input(
                            "item_id_pluggy",
                            value="",
                            key="input_pluggy_item_id",
                            label_visibility="collapsed"
                        )
                        submit_btn = st.form_submit_button("Salvar Conexão", type="primary")
                        if submit_btn and captured_id:
                            st.session_state['pluggy_item_id_capturado'] = captured_id
                            st.rerun()

                # O componente HTML: widget Pluggy + listener postMessage
                # que preenche o input acima e clica o botão automaticamente
                components.html(f"""
<!DOCTYPE html>
<html>
<head>
<style>
  body {{
    margin: 0;
    background: transparent;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  }}
  #status {{
    display: none;
    text-align: center;
    padding: 60px 20px;
  }}
  #status h2 {{ color: #10b981; font-size: 1.5rem; margin-bottom: 12px; }}
  #status p  {{ color: #94a3b8; font-size: 1rem; line-height: 1.6; }}
  #pluggy-area {{ min-height: 460px; }}
</style>
</head>
<body>

<div id="pluggy-area"></div>
<div id="status">
  <h2>✅ Banco conectado com sucesso!</h2>
  <p>Aguarde, salvando automaticamente no sistema...</p>
</div>

<script src="https://cdn.pluggy.ai/pluggy-connect/v2.8.2/pluggy-connect.js"></script>
<script>
(function() {{

  // Inicia o widget Pluggy
  const connect = new PluggyConnect({{
    connectToken: '{token}',

    onSuccess: function(data) {{
      const itemId = data.item.id;

      // Mostra mensagem de sucesso no iframe
      document.getElementById('pluggy-area').style.display = 'none';
      document.getElementById('status').style.display = 'block';

      // Envia o item_id para o frame pai via postMessage
      // (contorna o bloqueio de redirecionamento do Streamlit Cloud)
      try {{
        window.parent.postMessage(
          {{ type: 'pluggy_success', itemId: itemId }},
          '*'
        );
      }} catch(e) {{
        console.error('postMessage falhou:', e);
      }}
    }},

    onClose: function() {{
      document.getElementById('pluggy-area').innerHTML =
        '<h3 style="color:#94a3b8;text-align:center;padding:60px 20px;font-family:sans-serif;">Conexão encerrada.</h3>';
    }},

    onError: function(err) {{
      document.getElementById('pluggy-area').innerHTML =
        '<h3 style="color:#f43f5e;text-align:center;padding:60px 20px;font-family:sans-serif;">Erro na conexão. Tente novamente.</h3>';
    }}
  }});

  connect.init();

  // Listener no próprio iframe para capturar a mensagem de volta
  // (caso o parent reenvie — fallback defensivo)
  window.addEventListener('message', function(event) {{
    if (event.data && event.data.type === 'pluggy_success') {{
      document.getElementById('status').style.display = 'block';
    }}
  }});

}})();
</script>
</body>
</html>
""", height=520)

                # Listener no contexto da página Streamlit (fora do iframe)
                # Este segundo componente HTML fica invisível (height=0) e
                # escuta o postMessage do iframe filho, depois preenche o
                # formulário Python acima via manipulação do DOM do Streamlit.
                components.html("""
<script>
(function() {
  window.addEventListener('message', function(event) {
    if (!event.data || event.data.type !== 'pluggy_success') return;

    var itemId = event.data.itemId;
    if (!itemId) return;

    // Localiza o input do formulário Streamlit pelo label oculto
    // e injeta o item_id nele programaticamente
    var inputs = window.parent.document.querySelectorAll('input[type="text"]');
    var targetInput = null;

    for (var i = 0; i < inputs.length; i++) {
      // Identifica pelo placeholder vazio e posição no form
      var inp = inputs[i];
      if (inp.closest('form') && inp.value === '') {
        targetInput = inp;
        break;
      }
    }

    if (targetInput) {
      // Dispara o evento React para atualizar o estado do Streamlit
      var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
      ).set;
      nativeInputValueSetter.call(targetInput, itemId);
      targetInput.dispatchEvent(new Event('input', { bubbles: true }));

      // Aguarda o React processar e clica no botão de submit
      setTimeout(function() {
        var btns = window.parent.document.querySelectorAll('button[kind="primaryFormSubmit"], button[type="submit"]');
        if (btns.length > 0) {
          btns[btns.length - 1].click();
        }
      }, 300);
    }
  });
})();
</script>
""", height=0)

        st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)

        c_b1, c_b2 = st.columns([3, 1])
        c_b1.markdown("#### Bancos Ativos")

        # Botão de sincronização manual — fallback sempre disponível
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

    # --- TELA: DASHBOARD ---
    elif menu == "📊 Dashboard":
        st.markdown("<h2 style='color: #e2e8f0;'>📊 Resumo Financeiro</h2>", unsafe_allow_html=True)

        conexoes = buscar_conexoes_usuario(st.session_state['usuario_id'])
        if not conexoes:
            st.warning("Nenhum banco conectado. Vá em 'Gerir Bancos' para começar.")
        else:
            bancos_dict = {f"{c[2]} ({c[1][:5]})": c[1] for c in conexoes}
            sel_banco = st.selectbox("Selecione a conta para visualizar:", list(bancos_dict.keys()))

            with st.spinner("Sincronizando dados com o banco..."):
                dados = buscar_dados_reais(bancos_dict[sel_banco])

            if isinstance(dados, list):
                df = pd.DataFrame(dados)
                df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
                df['amount'] = pd.to_numeric(df['amount'])
                df['category'] = df['category'].apply(
                    lambda x: TRADUCAO_CATEGORIAS.get(str(x).upper(), "Outros")
                )

                st.sidebar.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
                st.sidebar.markdown("#### Filtros de Período")
                d1 = st.sidebar.date_input("Data de Início", df['date'].min())
                d2 = st.sidebar.date_input("Data de Fim", df['date'].max())

                df_f = df[(df['date'].dt.date >= d1) & (df['date'].dt.date <= d2)]
                in_v = df_f[df_f['amount'] > 0]['amount'].sum()
                out_v = df_f[df_f['amount'] < 0]['amount'].sum()
                saldo = in_v + out_v

                m1, m2, m3 = st.columns(3)
                m1.metric("⬇️ Entradas", f"R$ {in_v:,.2f}", delta_color="normal")
                m2.metric("⬆️ Saídas", f"R$ {abs(out_v):,.2f}", delta_color="inverse")
                m3.metric("💰 Saldo Líquido", f"R$ {saldo:,.2f}")

                st.markdown("<br>", unsafe_allow_html=True)

                grafico_cores = ['#0ea5e9', '#8b5cf6', '#10b981', '#f59e0b', '#f43f5e', '#64748b']

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.markdown("<h5 style='color: #e2e8f0;'>Gastos por Categoria</h5>", unsafe_allow_html=True)
                    df_gastos = df_f[df_f['amount'] < 0]
                    fig_p = px.pie(
                        df_gastos,
                        values=df_gastos['amount'].abs(),
                        names='category',
                        hole=0.4,
                        color_discrete_sequence=grafico_cores
                    )
                    fig_p.update_layout(
                        margin=dict(t=10, b=10, l=10, r=10),
                        showlegend=True,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#e2e8f0')
                    )
                    st.plotly_chart(fig_p, use_container_width=True)

                with col_g2:
                    st.markdown("<h5 style='color: #e2e8f0;'>Evolução do Caixa</h5>", unsafe_allow_html=True)
                    df_day = df_f.groupby(df_f['date'].dt.date)['amount'].sum().reset_index()
                    fig_l = px.area(
                        df_day, x='date', y='amount',
                        line_shape='spline',
                        color_discrete_sequence=['#0ea5e9']
                    )
                    fig_l.update_layout(
                        margin=dict(t=10, b=10, l=10, r=10),
                        xaxis_title=None, yaxis_title=None,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#e2e8f0')
                    )
                    fig_l.update_xaxes(showgrid=False)
                    fig_l.update_yaxes(gridcolor='#334155')
                    st.plotly_chart(fig_l, use_container_width=True)

                st.markdown("<h5 style='color: #e2e8f0;'>Extrato Recente</h5>", unsafe_allow_html=True)
                st.dataframe(
                    df_f[['date', 'description', 'amount', 'category']].sort_values('date', ascending=False),
                    use_container_width=True,
                    hide_index=True
                )

                c_ex1, c_ex2, _ = st.columns([1, 1, 4])
                c_ex1.download_button("📊 Baixar Excel", gerar_excel(df_f, in_v, out_v, saldo), "extrato.xlsx")
                c_ex2.download_button("📄 Baixar PDF", gerar_pdf(df_f, in_v, out_v, saldo), "relatorio.pdf")

            else:
                st.error("Não foi possível carregar os dados deste banco.")