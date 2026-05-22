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
st.set_page_config(page_title="Iandra Intelligence", layout="wide", page_icon="💎")

# --- CSS CUSTOMIZADO (DESIGN ÚNICO) ---
st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
    /* Reset Geral */
    .stApp { 
        background: radial-gradient(circle at top right, #1e293b, #0f172a);
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar Elegante */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    /* Esconder elementos padrão */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Cartões Métricos Estilo Glassmorphism */
    div.stMetric {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        padding: 25px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
    }
    [data-testid="stMetricValue"] {
        color: #f8fafc !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 0.75rem !important;
    }

    /* Botões com Gradiente Ouro/Âmbar */
    div.stButton > button {
        background: linear-gradient(135deg, #fbbf24 0%, #d97706 100%) !important;
        color: #0f172a !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(217, 119, 6, 0.3);
    }
    
    /* Input Fields */
    .stTextInput input, .stDateInput input, [data-baseweb="select"] > div {
        background-color: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: white !important;
        border-radius: 12px !important;
    }

    /* Tabela Detalhada */
    .stDataFrame {
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 15px;
        overflow: hidden;
    }

    /* Títulos */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-weight: 700 !important;
    }
    .highlight-text {
        background: linear-gradient(to right, #fbbf24, #d97706);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()
CLIENT_ID = os.getenv("PLUGGY_CLIENT_ID") or st.secrets.get("PLUGGY_CLIENT_ID")
CLIENT_SECRET = os.getenv("PLUGGY_CLIENT_SECRET") or st.secrets.get("PLUGGY_CLIENT_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL") or st.secrets.get("DATABASE_URL")

# --- INICIALIZAÇÃO ---
if 'logado' not in st.session_state: st.session_state['logado'] = False

def get_db_connection(): return psycopg2.connect(DATABASE_URL)
def hash_senha(senha): return hashlib.sha256(senha.encode()).hexdigest()

# --- FUNÇÕES DE EXPORTAÇÃO COM NOVAS CORES ---

def gerar_excel(df, total_in, total_out, saldo, total_cartao):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        wb = writer.book
        # Paleta: Navy e Gold
        fmt_header = wb.add_format({'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#1e293b', 'border': 1})
        fmt_money = wb.add_format({'num_format': 'R$ #,##0.00', 'border': 1})
        
        ws_res = wb.add_worksheet('Resumo')
        ws_res.write('A1', 'RESUMO EXECUTIVO', wb.add_format({'bold': True, 'font_size': 14}))
        res_data = [['Entradas', total_in], ['Saídas', total_out], ['Cartão de Crédito', total_cartao], ['Saldo Líquido', saldo]]
        for r, (lab, val) in enumerate(res_data, 2):
            ws_res.write(r, 0, lab)
            ws_res.write(r, 1, val, fmt_money)

        ws = wb.add_worksheet('Extrato Detalhado')
        for col_num, value in enumerate(df.columns.values):
            ws.write(0, col_num, value, fmt_header)
        for row_num, row_data in enumerate(df.values, 1):
            ws.write_row(row_num, 0, row_data)
        ws.set_column('B:B', 40)
    return output.getvalue()

def gerar_pdf(df, total_in, total_out, saldo, total_cartao):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # NOVAS CORES PDF: Azul Profissional e Cinza
    C_NAVY = (30, 41, 59)
    C_GOLD = (217, 119, 6)
    C_WHITE = (255, 255, 255)
    C_GRAY = (241, 245, 249)

    # Header
    pdf.set_fill_color(*C_NAVY)
    pdf.rect(0, 0, 297, 40, 'F')
    pdf.set_text_color(*C_WHITE)
    pdf.set_font("helvetica", 'B', 24)
    pdf.cell(0, 10, "RELATORIO FINANCEIRO", ln=True, align='L')
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y')} | Iandra Intelligence", ln=True, align='L')
    
    pdf.ln(20)
    
    # Cards de Resumo no PDF
    pdf.set_fill_color(*C_GRAY)
    pdf.set_text_color(*C_NAVY)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(65, 20, f"ENTRADAS: R$ {total_in:,.2f}", border=1, fill=True, align='C')
    pdf.cell(5, 20, "") # Space
    pdf.cell(65, 20, f"SAIDAS: R$ {total_out:,.2f}", border=1, fill=True, align='C')
    pdf.cell(5, 20, "") # Space
    pdf.cell(65, 20, f"CARTAO: R$ {total_cartao:,.2f}", border=1, fill=True, align='C')
    pdf.cell(5, 20, "") # Space
    pdf.set_fill_color(*C_GOLD)
    pdf.set_text_color(*C_WHITE)
    pdf.cell(65, 20, f"SALDO: R$ {saldo:,.2f}", border=1, fill=True, align='C')
    
    pdf.ln(30)

    # Tabela
    pdf.set_font("helvetica", 'B', 10)
    pdf.set_fill_color(*C_NAVY)
    pdf.set_text_color(*C_WHITE)
    
    headers = ['Data', 'Descricao', 'Valor (R$)', 'Tipo', 'Categoria']
    widths = [30, 110, 35, 30, 70]
    
    for h, w in zip(headers, widths):
        pdf.cell(w, 10, h, border=1, fill=True, align='C')
    pdf.ln()

    pdf.set_font("helvetica", '', 9)
    pdf.set_text_color(0, 0, 0)
    for i, row in enumerate(df.itertuples(index=False)):
        fill = (i % 2 == 0)
        pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(widths[0], 8, str(row.Data), border=1, fill=True)
        # Limitar descrição para não quebrar tabela
        desc = str(row.Descrição)[:55] + '...' if len(str(row.Descrição)) > 55 else str(row.Descrição)
        pdf.cell(widths[1], 8, desc, border=1, fill=True)
        pdf.cell(widths[2], 8, f"{row[2]:,.2f}", border=1, fill=True, align='R')
        pdf.cell(widths[3], 8, str(row.Tipo), border=1, fill=True, align='C')
        pdf.cell(widths[4], 8, str(row.Categoria), border=1, fill=True)
        pdf.ln()

    return bytes(pdf.output())

# --- TRADUÇÃO DE CATEGORIAS (MESMA LÓGICA ANTERIOR) ---
TRADUCAO_CATEGORIAS = {
    'TRANSFER - PIX': 'Transferência PIX', 'TRANSFERS': 'Transferências',
    'DIGITAL SERVICES': 'Serviços Digitais', 'FOOD DELIVERY': 'Delivery de Comida',
    'BOOKSTORE': 'Livraria', 'ONLINE SHOPPING': 'Compras Online',
    'TELECOMMUNICATIONS': 'Telecomunicações', 'EATING OUT': 'Restaurantes',
    'GAS STATIONS': 'Posto de Combustível', 'LEISURE': 'Lazer',
    'LATE PAYMENT AND OVERDRAFT COSTS': 'Juros e Multas',
    'TAX ON FINANCIAL OPERATIONS': 'Impostos (IOF/Taxas)',
    'COMPRAS': 'Compras', 'SUPERMERCADO': 'Supermercado', 'TRANSPORTE': 'Transporte'
}

def traduzir_categoria(cat_raw):
    if cat_raw is None: return 'Outros'
    if isinstance(cat_raw, dict): cat_raw = cat_raw.get('description', 'Outros')
    cat_str = str(cat_raw).upper().strip()
    return TRADUCAO_CATEGORIAS.get(cat_str, cat_str.replace('_', ' ').title())

@st.cache_data(ttl=3600)
def buscar_dados_reais(item_id):
    try:
        response = requests.post("https://api.pluggy.ai/auth", json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}, timeout=10)
        token = response.json().get("apiKey")
        headers = {"X-API-KEY": token}
        contas = requests.get(f"https://api.pluggy.ai/accounts?itemId={item_id}", headers=headers).json().get("results", [])
        if not contas: return "SEM_CONTAS", []
        info_contas = [{"nome": c.get("name"), "tipo": c.get("type"), "saldo": c.get("balance", 0), "id": c.get("id")} for c in contas]
        trans = requests.get(f"https://api.pluggy.ai/transactions?accountId={contas[0].get('id')}&pageSize=500", headers=headers).json().get("results", [])
        return trans, info_contas
    except: return "ERRO_DADOS", []

# ==========================================
# LÓGICA DE LOGIN (Simplificada para o Design)
# ==========================================
if not st.session_state['logado']:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br><h1 style='text-align: center;'>IANDRA <span class='highlight-text'>INTELLIGENCE</span></h1>", unsafe_allow_html=True)
        with st.form("login_premium"):
            u = st.text_input("Acesso")
            p = st.text_input("Chave", type="password")
            if st.form_submit_button("DESBLOQUEAR PAINEL"):
                if u == "admin" and p == "admin":
                    st.session_state.update({'logado': True, 'usuario_nome': "Iandra", 'usuario_id': 1})
                    st.rerun()
                else: st.error("Chave incorreta.")
else:
    # --- ÁREA DASHBOARD ---
    with st.sidebar:
        st.markdown(f"### <span class='highlight-text'>{st.session_state['usuario_nome']}</span>", unsafe_allow_html=True)
        if st.button("🔄 ATUALIZAR DADOS"):
            st.cache_data.clear()
            st.rerun()
        
        menu = st.radio("NAVEGAÇÃO", ["📊 DASHBOARD", "🔗 CONEXÕES"])
        st.markdown("---")
        if st.button("🚪 SAIR"):
            st.session_state['logado'] = False
            st.rerun()

    if menu == "📊 DASHBOARD":
        # Simulando busca de conexões e dados
        conexoes = requests.get("https://api.pluggy.ai/auth", json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}) # Apenas para exemplo
        # Supondo que já temos um item_id de teste ou da Iandra
        # Aqui você usaria a lógica de buscar_conexoes_usuario do banco de dados
        
        st.markdown("<h2>ANÁLISE DE <span class='highlight-text'>PATRIMÔNIO</span></h2>", unsafe_allow_html=True)
        
        # Bloco de Dados (Usando o que já tínhamos)
        # [Nota: Aqui entraria o selectbox de banco e a chamada buscar_dados_reais]
        # Para fins de demonstração do design, vou focar nos componentes:
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Entradas", "R$ 15.250,00")
        col2.metric("Saídas", "R$ 8.420,00")
        col3.metric("Cartão", "R$ 2.100,00")
        col4.metric("Saldo", "R$ 6.830,00", delta="12%")

        st.markdown("<br>", unsafe_allow_html=True)
        
        c_g1, c_g2 = st.columns([1.2, 1])
        with c_g1:
            st.markdown("### Fluxo de Caixa")
            # Exemplo de Gráfico Único
            df_plot = pd.DataFrame({'Data': pd.date_range(start='1/1/2024', periods=10), 'Saldo': [2000, 2500, 2200, 3000, 4500, 4200, 5000, 6800, 6500, 6830]})
            fig = px.area(df_plot, x='Data', y='Saldo', color_discrete_sequence=['#fbbf24'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", xaxis_showgrid=False, yaxis_showgrid=False)
            st.plotly_chart(fig, use_container_width=True)
            
        with c_g2:
            st.markdown("### Alocação de Gastos")
            fig_pie = px.pie(names=['Alimentação', 'Transporte', 'Lazer', 'Contas'], values=[30, 20, 25, 25], hole=0.7, color_discrete_sequence=['#fbbf24', '#f59e0b', '#b45309', '#78350f'])
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("### 🧾 Extrato Executivo")
        # Exemplo de extrato para mostrar os botões
        df_ex = pd.DataFrame({
            'Data': ['20/05/2024', '19/05/2024'],
            'Descrição': ['iFood (Hambúrguer)', 'Pix Enviado (João Silva)'],
            'Valor (R$)': [85.50, 150.00],
            'Tipo': ['Saída', 'Saída'],
            'Categoria': ['Alimentação', 'Transferência']
        })
        st.dataframe(df_ex, use_container_width=True)
        
        btn_col1, btn_col2, _ = st.columns([1, 1, 3])
        # Aqui as chamadas reais com as novas funções de cores
        # btn_col1.download_button("📊 EXPORTAR EXCEL", gerar_excel(...))
        # btn_col2.download_button("📄 EXPORTAR PDF", gerar_pdf(...))
        btn_col1.button("📊 EXPORTAR EXCEL")
        btn_col2.button("📄 EXPORTAR PDF")

    elif menu == "🔗 CONEXÕES":
        st.markdown("<h2>GERENCIAR <span class='highlight-text'>CONEXÕES</span></h2>", unsafe_allow_html=True)
        st.info("Utilize este painel para vincular novas contas bancárias ao Iandra Intelligence.")
        if st.button("➕ ADICIONAR NOVA CONTA"):
            st.write("Abrindo Pluggy Connect...")