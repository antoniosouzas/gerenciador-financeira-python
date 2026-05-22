import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
import sqlite3
import hashlib
from dotenv import load_dotenv
import io
from fpdf import FPDF
import streamlit.components.v1 as components

# Configuração da página (DEVE SER A PRIMEIRA LINHA)
st.set_page_config(page_title="Dashboard Financeiro", layout="wide")

load_dotenv()
CLIENT_ID = os.getenv("PLUGGY_CLIENT_ID")
CLIENT_SECRET = os.getenv("PLUGGY_CLIENT_SECRET")

# --- INICIALIZAÇÃO DA SESSÃO ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False
if 'usuario_nome' not in st.session_state:
    st.session_state['usuario_nome'] = ""
if 'usuario_id' not in st.session_state:
    st.session_state['usuario_id'] = None
if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False
if 'abrir_pluggy' not in st.session_state:
    st.session_state['abrir_pluggy'] = False

# --- FUNÇÕES DE BASE DE DADOS E AUTENTICAÇÃO ---
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_login(email, senha):
    conn = sqlite3.connect('dashboard_financeiro.db')
    cursor = conn.cursor()
    # Adicionado o is_admin na verificação
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
        sucesso = True
    except sqlite3.IntegrityError:
        sucesso = False 
    conn.close()
    return sucesso

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
    # Apaga as conexões bancárias do cliente primeiro para manter a limpeza
    cursor.execute("DELETE FROM conexoes_bancarias WHERE usuario_id = ?", (usuario_id,))
    # Apaga o cliente
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    conn.commit()
    conn.close()

def salvar_conexao(usuario_id, pluggy_item_id, nome_instituicao="Nova Conta Conectada"):
    conn = sqlite3.connect('dashboard_financeiro.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO conexoes_bancarias (usuario_id, pluggy_item_id, nome_instituicao) 
            VALUES (?, ?, ?)
        ''', (usuario_id, pluggy_item_id, nome_instituicao))
        conn.commit()
        sucesso = True
    except sqlite3.IntegrityError:
        sucesso = False 
    finally:
        conn.close()
    return sucesso

def buscar_conexoes_usuario(usuario_id):
    conn = sqlite3.connect('dashboard_financeiro.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, pluggy_item_id, nome_instituicao, data_conexao 
        FROM conexoes_bancarias 
        WHERE usuario_id = ?
    ''', (usuario_id,))
    conexoes = cursor.fetchall()
    conn.close()
    return conexoes

def deletar_conexao(conexao_id):
    conn = sqlite3.connect('dashboard_financeiro.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conexoes_bancarias WHERE id = ?", (conexao_id,))
    conn.commit()
    conn.close()

# --- FUNÇÕES DA API PLUGGY ---
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
        if not contas: 
            return "SEM_CONTAS"
        conta_id = contas[0].get("id")
        
        trans = requests.get(f"https://api.pluggy.ai/transactions?accountId={conta_id}&pageSize=500", headers=headers, timeout=10).json().get("results", [])
        return trans
    except:
        return "ERRO_DADOS"

# --- TRADUÇÃO E EXPORTAÇÕES ---
TRADUCAO_CATEGORIAS = {
    'INCOME': 'Renda / Recebimentos', 'LOANS AND FINANCING': 'Empréstimos / Financiamentos',
    'INVESTMENTS': 'Investimentos', 'SAME PERSON TRANSFER': 'Transferência (Mesma Titularidade)',
    'TRANSFERS': 'Transferências', 'TRANSFER': 'Transferências', 'LEGAL OBLIGATIONS': 'Obrigações Legais',
    'SERVICES': 'Serviços', 'SHOPPING': 'Compras / Varejo', 'DIGITAL SERVICES': 'Serviços Digitais (Assinaturas)',
    'GROCERIES': 'Supermercado', 'FOOD AND DRINKS': 'Alimentação / Restaurantes', 'FOOD AND DRINK': 'Alimentação',
    'TRAVEL': 'Viagens', 'DONATIONS': 'Doações', 'GAMBLING': 'Jogos e Apostas', 'TAXES': 'Impostos',
    'BANK FEES': 'Taxas Bancárias', 'HOUSING': 'Moradia / Casa', 'UTILITIES': 'Contas de Casa (Água, Luz, Internet)',
    'HEALTHCARE': 'Saúde e Farmácia', 'TRANSPORTATION': 'Transporte', 'INSURANCE': 'Seguros',
    'LEISURE': 'Lazer e Entretenimento', 'ENTERTAINMENT': 'Lazer e Entretenimento', 'PERSONAL CARE': 'Cuidados Pessoais',
    'UNCATEGORIZED': 'Outros / Não Categorizado'
}

def gerar_excel_com_totais(df, total_in, total_out, saldo_final):
    df_excel = df.copy()
    df_totais = pd.DataFrame([
        ['', '', '', ''], 
        ['', 'TOTAL DE ENTRADAS', total_in, ''], 
        ['', 'TOTAL DE SAÍDAS', total_out, ''], 
        ['', 'SALDO FINAL', saldo_final, '']
    ], columns=df_excel.columns)
    
    df_final = pd.concat([df_excel, df_totais], ignore_index=True)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, sheet_name='Extrato')
        worksheet = writer.sheets['Extrato']
        for i, col in enumerate(df_final.columns): 
            worksheet.set_column(i, i, 20)
    return output.getvalue()

def gerar_pdf(df, data_inicio, data_fim, total_in, total_out, saldo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(0, 10, "Relatorio Financeiro", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.set_font("helvetica", '', 12)
    pdf.cell(0, 10, f"Periodo: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(65, 10, f"Entradas: R$ {total_in:,.2f}")
    pdf.cell(65, 10, f"Saidas: R$ {total_out:,.2f}")
    pdf.cell(60, 10, f"Saldo: R$ {saldo:,.2f}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(25, 10, "Data", border=1)
    pdf.cell(85, 10, "Descricao", border=1)
    pdf.cell(50, 10, "Categoria", border=1)
    pdf.cell(30, 10, "Valor (R$)", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", '', 9)
    for _, row in df.iterrows():
        desc = str(row['Descrição'])[:45].encode('latin-1', 'replace').decode('latin-1')
        cat = str(row['Categoria'])[:25].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(25, 8, str(row['Data']), border=1)
        pdf.cell(85, 8, desc, border=1)
        pdf.cell(50, 8, cat, border=1)
        pdf.cell(30, 8, f"{row['Valor (R$)']:,.2f}", border=1, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())

# ==========================================
# ECRÃ DE LOGIN (Restrito, Sem Registo Público)
# ==========================================
if not st.session_state['logado']:
    st.markdown("<h1 style='text-align: center;'>Bem-vindo ao Sistema Financeiro</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Acesso restrito a clientes autorizados.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login"):
            email_login = st.text_input("E-mail")
            senha_login = st.text_input("Palavra-passe", type="password")
            btn_login = st.form_submit_button("Aceder ao Dashboard", use_container_width=True)
            
            if btn_login:
                usuario = verificar_login(email_login, senha_login)
                if usuario:
                    st.session_state['logado'] = True
                    st.session_state['usuario_id'] = usuario[0] 
                    st.session_state['usuario_nome'] = usuario[1]
                    st.session_state['is_admin'] = bool(usuario[2]) # Regista se é Administrador
                    st.rerun()
                else:
                    st.error("E-mail ou palavra-passe incorretos!")

# ==========================================
# ÁREA PRIVADA (SISTEMA & PAINEL ADMIN)
# ==========================================
else:
    if "novo_item_id" in st.query_params:
        novo_id = st.query_params["novo_item_id"]
        if salvar_conexao(st.session_state['usuario_id'], novo_id, "Nova Conexão via Connect"):
            st.toast("✅ Banco conectado com sucesso!", icon="🎉")
        st.query_params.clear() 

    # --- MENU LATERAL DINÂMICO ---
    st.sidebar.markdown(f"### Olá, {st.session_state['usuario_nome']}! 👋")
    
    opcoes_menu = ["📊 O Meu Dashboard", "🔗 Gerir Contas"]
    # Se for Admin, ganha a funcionalidade do Painel
    if st.session_state.get('is_admin', False):
        opcoes_menu.append("⚙️ Painel Admin")
        
    menu = st.sidebar.radio("Navegação", opcoes_menu)
    
    st.sidebar.divider()
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state['logado'] = False
        st.session_state['usuario_nome'] = ""
        st.session_state['usuario_id'] = None
        st.session_state['is_admin'] = False
        st.session_state['abrir_pluggy'] = False
        st.rerun()

    # --- TELA 0: PAINEL DE ADMINISTRAÇÃO (EXCLUSIVO) ---
    if menu == "⚙️ Painel Admin":
        st.title("⚙️ Painel de Administração")
        st.write("Gira os acessos dos seus clientes ao sistema.")
        
        tab_novo, tab_lista = st.tabs(["➕ Registar Novo Cliente", "👥 Clientes Registados"])
        
        with tab_novo:
            with st.form("form_novo_cliente"):
                st.subheader("Criar Nova Conta")
                nome_novo = st.text_input("Nome Completo do Cliente")
                email_novo = st.text_input("E-mail de Acesso")
                senha_nova = st.text_input("Palavra-passe (Forneça-a ao seu cliente)", type="password")
                is_admin_novo = st.checkbox("Atribuir privilégios de Administrador a esta conta?")
                
                btn_salvar = st.form_submit_button("Criar Conta", type="primary")
                
                if btn_salvar:
                    if nome_novo and email_novo and senha_nova:
                        val_admin = 1 if is_admin_novo else 0
                        if registrar_usuario(nome_novo, email_novo, senha_nova, val_admin):
                            st.success(f"A conta de {nome_novo} foi criada com sucesso!")
                        else:
                            st.error("Este e-mail já se encontra registado no sistema.")
                    else:
                        st.warning("Por favor, preencha todos os campos obrigatórios.")
                        
        with tab_lista:
            st.subheader("Utilizadores do Sistema")
            todos_usuarios = buscar_todos_usuarios()
            
            if todos_usuarios:
                for usr in todos_usuarios:
                    u_id, u_nome, u_email, u_admin, u_data = usr
                    
                    with st.expander(f"{'👑' if u_admin else '👤'} {u_nome} - {u_email}"):
                        st.write(f"**Data de Registo:** {u_data}")
                        st.write(f"**Nível de Acesso:** {'Administrador' if u_admin else 'Cliente'}")
                        
                        if u_id != st.session_state['usuario_id']:
                            if st.button("❌ Eliminar Cliente (Apaga Dados)", key=f"del_usr_{u_id}"):
                                deletar_usuario_completo(u_id)
                                st.success("Cliente e dados associados eliminados.")
                                st.rerun()
                        else:
                            st.info("Esta é a sua sessão atual. (Não é possível eliminar a si próprio).")
            else:
                st.info("Nenhum cliente encontrado.")


    # --- TELA 1: GERIR CONTAS BANCÁRIAS ---
    elif menu == "🔗 Gerir Contas":
        st.title("🔗 Contas Conectadas")
        st.write("Conecte o seu banco de forma segura para atualizar os gráficos automaticamente.")
        
        if st.button("➕ Conectar Novo Banco", type="primary"):
            st.session_state['abrir_pluggy'] = True

        if st.session_state['abrir_pluggy']:
            with st.spinner("A gerar ambiente seguro..."):
                connect_token = gerar_connect_token()
                if connect_token:
                    if st.button("❌ Cancelar / Fechar Ecrã"):
                        st.session_state['abrir_pluggy'] = False
                        st.rerun()

                    st.components.v1.html(
                        f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <script src="https://cdn.pluggy.ai/pluggy-connect/v2.8.2/pluggy-connect.js"></script>
                        </head>
                        <body style="background-color: #ffffff; margin: 0; padding: 20px; font-family: sans-serif; display: flex; justify-content: center; height: 100vh;">
                            <div id="status" style="color: #333; margin-top: 20px;">A carregar interface do banco...</div>
                            <script>
                                window.onload = function() {{
                                    let conexaoSucesso = false; 
                                    try {{
                                        const connect = new PluggyConnect({{
                                            connectToken: '{connect_token}',
                                            onSuccess: function(itemData) {{
                                                conexaoSucesso = true; 
                                                const statusDiv = document.getElementById("status");
                                                statusDiv.style.display = "block";
                                                statusDiv.innerHTML = 
                                                    "<div style='text-align: center; margin-top: 40px; font-family: sans-serif;'>" +
                                                        "<h2 style='color: #28a745;'>✅ Conexão Realizada!</h2>" +
                                                        "<p style='color: #555; margin-bottom: 25px;'>O banco foi vinculado com sucesso. Clique no botão abaixo para voltar ao painel.</p>" +
                                                        "<a href='/?novo_item_id=" + itemData.item.id + "' target='_parent' style='background-color: #007bff; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px; cursor: pointer; border: none; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>" +
                                                            "🔄 Atualizar Dashboard" +
                                                        "</a>" +
                                                        "<p style='color: #999; margin-top: 40px; font-size: 12px;'>Se o botão não funcionar, copie este ID de conexão: <br><br> <b style='color:#000;'>" + itemData.item.id + "</b></p>" +
                                                    "</div>";
                                            }},
                                            onClose: function() {{
                                                if (!conexaoSucesso) {{
                                                    document.getElementById("status").style.display = "block";
                                                    document.getElementById("status").innerText = "Conexão cancelada. Pode fechar este ecrã clicando no botão 'Cancelar' acima.";
                                                }}
                                            }}
                                        }});
                                        connect.init();
                                        document.getElementById("status").style.display = "none";
                                    }} catch (error) {{
                                        document.getElementById("status").style.display = "block";
                                        document.getElementById("status").innerText = "Erro ao carregar o sistema: " + error.message;
                                    }}
                                }};
                            </script>
                        </body>
                        </html>
                        """,
                        height=500,
                    )
                    
                    st.info("💡 Caso o botão azul no ecrã de sucesso não funcione, copie o código exibido e cole abaixo para salvar manualmente:")
                    manual_id = st.text_input("Cole o ID da conexão aqui (opcional):")
                    if st.button("Salvar Código Manualmente"):
                        if manual_id:
                            if salvar_conexao(st.session_state['usuario_id'], manual_id, "Nova Conexão"):
                                st.success("Conta adicionada com sucesso!")
                                st.session_state['abrir_pluggy'] = False
                                st.rerun()
                            else:
                                st.warning("Este ID já foi adicionado ou é inválido.")
                        else:
                            st.error("Por favor, cole um ID válido.")
                else:
                    st.error("Erro ao comunicar com a Pluggy. Tente novamente.")

        st.divider()
        st.subheader("As Suas Conexões Ativas")
        conexoes = buscar_conexoes_usuario(st.session_state['usuario_id'])
        
        if conexoes:
            for i, cx in enumerate(conexoes):
                col1, col2 = st.columns([8, 2])
                col1.info(f"🏦 {cx[2]} (ID: {cx[1][:8]}...) - Adicionado em: {cx[3][:10]}")
                chave_unica = f"btn_remover_{i}_{cx[0]}"
                if col2.button("❌ Remover", key=chave_unica):
                    deletar_conexao(cx[0])
                    st.rerun()
        else:
            st.warning("Ainda não conectou nenhum banco.")

    # --- TELA 2: DASHBOARD FINANCEIRO ---
    elif menu == "📊 O Meu Dashboard":
        st.title("📊 Resumo Financeiro")
        
        conexoes = buscar_conexoes_usuario(st.session_state['usuario_id'])
        
        if not conexoes:
            st.info("👈 Vá a 'Gerir Contas' no menu lateral e conecte o seu primeiro banco para ver o dashboard!")
        else:
            dict_conexoes = {f"Banco {i+1} ({cx[1][:8]}...)": cx[1] for i, cx in enumerate(conexoes)}
            conta_selecionada = st.selectbox("Selecione a conta para análise:", list(dict_conexoes.keys()))
            item_id_ativo = dict_conexoes[conta_selecionada]
            
            with st.spinner("A procurar dados financeiros..."):
                resultado = buscar_dados_reais(item_id_ativo)

            if isinstance(resultado, list):
                df = pd.DataFrame(resultado)
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'], utc=True)
                    if df['date'].dt.tz is not None:
                        df['date'] = df['date'].dt.tz_localize(None)
                        
                    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
                    df['category'] = df['category'].fillna('UNCATEGORIZED')
                    df['category'] = df['category'].astype(str).str.strip().str.upper()
                    df['category'] = df['category'].apply(lambda x: TRADUCAO_CATEGORIAS.get(x, x.title()))
                    
                    st.sidebar.subheader("📅 Período de Análise")
                    data_min, data_max = df['date'].min().date(), df['date'].max().date()
                    
                    data_inicio = st.sidebar.date_input("🟢 Data Inicial", value=data_max - pd.Timedelta(days=30), max_value=data_max, format="DD/MM/YYYY")
                    data_fim = st.sidebar.date_input("🔴 Data Final", value=data_max, min_value=data_inicio, max_value=data_max, format="DD/MM/YYYY")
                    
                    categorias_disponiveis = sorted(df['category'].dropna().unique().tolist())
                    categorias_selecionadas = st.sidebar.multiselect("Filtrar Categoria", options=categorias_disponiveis, default=[])

                    mask_data = (df['date'].dt.date >= data_inicio) & (df['date'].dt.date <= data_fim)
                    df_filtrado = df[mask_data].copy()
                    
                    if categorias_selecionadas: 
                        df_filtrado = df_filtrado[df_filtrado['category'].isin(categorias_selecionadas)]
                    
                    df_filtrado = df_filtrado[['date', 'description', 'amount', 'category']]
                    df_filtrado.columns = ['Data', 'Descrição', 'Valor (R$)', 'Categoria']
                    df_filtrado['Data'] = df_filtrado['Data'].dt.strftime('%d/%m/%Y') 
                    
                    entradas = df_filtrado[df_filtrado['Valor (R$)'] > 0]['Valor (R$)'].sum()
                    saidas = df_filtrado[df_filtrado['Valor (R$)'] < 0]['Valor (R$)'].sum()
                    saldo_periodo = df_filtrado['Valor (R$)'].sum()

                    c1, c2, c3 = st.columns(3)
                    c1.metric("Entradas", f"R$ {entradas:,.2f}")
                    c2.metric("Saídas", f"R$ {saidas:,.2f}")
                    c3.metric("Saldo do Período", f"R$ {saldo_periodo:,.2f}")
                    st.divider()
                    
                    tab1, tab2, tab3 = st.tabs(["Fluxo de Gastos", "Categorias", "Evolução do Saldo"])
                    df_gastos = df_filtrado[df_filtrado['Valor (R$)'] < 0].copy()
                    df_gastos['Valor Absoluto (R$)'] = df_gastos['Valor (R$)'].abs()

                    with tab1:
                        if not df_gastos.empty:
                            df_barras = df_gastos.groupby(['Data', 'Categoria'])['Valor Absoluto (R$)'].sum().reset_index()
                            fig_barras = px.bar(df_barras, x='Data', y='Valor Absoluto (R$)', color='Categoria', text_auto='.2f')
                            st.plotly_chart(fig_barras, use_container_width=True)
                        else: 
                            st.info("Sem despesas no período.")

                    with tab2:
                        if not df_gastos.empty:
                            fig_pizza = px.pie(df_gastos, values='Valor Absoluto (R$)', names='Categoria', hole=0.4)
                            st.plotly_chart(fig_pizza, use_container_width=True)
                        else: 
                            st.info("Sem despesas no período.")

                    with tab3:
                        if not df_filtrado.empty:
                            df_fluxo = df_filtrado.groupby('Data', sort=False)['Valor (R$)'].sum().reset_index()
                            df_fluxo['Saldo Acumulado'] = df_fluxo['Valor (R$)'].cumsum()
                            fig_linha = px.line(df_fluxo, x='Data', y='Saldo Acumulado', markers=True)
                            st.plotly_chart(fig_linha, use_container_width=True)
                        else:
                            st.info("Sem dados para exibir.")

                    st.divider()
                    st.subheader("Extrato Detalhado")
                    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
                    
                    col1, col2, col3 = st.columns([1, 1, 6])
                    
                    csv = df_filtrado.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    col1.download_button("📥 Baixar CSV", data=csv, file_name='extrato.csv', mime='text/csv')
                    
                    excel_data = gerar_excel_com_totais(df_filtrado, entradas, saidas, saldo_periodo)
                    col2.download_button("📊 Baixar Excel", data=excel_data, file_name='extrato_com_totais.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    
                    pdf_data = gerar_pdf(df_filtrado, data_inicio, data_fim, entradas, saidas, saldo_periodo)
                    col3.download_button("📄 Baixar Relatório PDF", data=pdf_data, file_name='relatorio_financeiro.pdf', mime='application/pdf')

                else: 
                    st.warning("Nenhuma transação encontrada no banco.")
            else: 
                st.error("Erro na conexão com a API da Pluggy.")