import streamlit as st
import os
import glob
import pandas as pd
from datetime import datetime, date, timedelta
import altair as alt
import numpy as np

# Configuração da página (deve ser a primeira linha de código)
st.set_page_config(page_title="Hub de Operações", layout="wide")

# --- CONFIGURAÇÃO DE PASTAS ---
PASTA_RAIZ = os.path.dirname(os.path.abspath(__file__))

def localizar_arquivo_recente(prefixo):
    """Busca o arquivo mais recente que começa com o prefixo na pasta do projeto"""
    # Criamos o caminho de busca usando a PASTA_RAIZ dinâmica
    padrao = os.path.join(PASTA_RAIZ, f"{prefixo}*.csv")
    arquivos = glob.glob(padrao)
    
    if not arquivos:
        # Fallback: se não achar com o caminho absoluto da pasta raiz, 
        # tenta buscar na pasta de execução atual (comum em servidores Cloud)
        arquivos = glob.glob(f"{prefixo}*.csv")
        
    if not arquivos:
        return None
    
    # Retorna o caminho do arquivo mais recente
    return max(arquivos, key=os.path.getmtime)

# --- DEFINIÇÃO DAS VARIÁVEIS DE BASE ---
# O código agora é agnóstico: não importa se é Windows ou Linux
BASE_DADOS_ENT = localizar_arquivo_recente("salesforce_entrantes_hoje_2026")
BASE_DADOS_FIN = localizar_arquivo_recente("salesforce_finalizados_2026")
BASE_DADOS_CAN = localizar_arquivo_recente("salesforce_cancelados_hoje_2026")
BASE_DADOS_SOB = localizar_arquivo_recente("salesforce_sobras_ontem_2026")

@st.cache_data(ttl=3600)
def carregar_entrantes():
    if not BASE_DADOS_ENT: return pd.DataFrame()
    try:
        df_temp = pd.read_csv(BASE_DADOS_ENT, sep=";", encoding='utf-8')
        df_temp.columns = df_temp.columns.str.strip().str.lower()
        
        mapeamento = {
            'created_at': 'data', 
            'descrição': 'desc_limpa', 
            'Regional': 'regional', 
            'cidade': 'cidade', 
            'motivo': 'motivo',
            'OLT' : 'OLT'
        }
        df_temp = df_temp.rename(columns=mapeamento)
        
        if 'data' in df_temp.columns:
            # REMOVIDO O .dt.date PARA MANTER A HORA NA COLUNA DATA
            df_temp['data'] = pd.to_datetime(df_temp['data'], dayfirst=True, errors='coerce')
        
        for c in ['regional', 'desc_limpa']:
            if c not in df_temp.columns: df_temp[c] = "Não Informado"
            
        return df_temp
    except:
        return pd.DataFrame()

def carregar_finalizados():
    if not BASE_DADOS_FIN: return pd.DataFrame()
    try:
        # 1. Carregamento inicial
        df_temp = pd.read_csv(BASE_DADOS_FIN, sep=";", encoding='utf-8')
        df_temp.columns = df_temp.columns.str.strip().str.lower()
        
        # 2. Mapeamento
        mapeamento = {
            'data_encerramento_prot': 'data', 
            'regional': 'regional', 
            'cidade': 'cidade',
            'descrição': 'desc_limpa', 
            'motivo da conclusão': 'motv_concl'
        }
        df_temp = df_temp.rename(columns=mapeamento)
        
        if 'data' in df_temp.columns:
            # CONVERSÃO COMPLETA (Preserva Data e Hora)
            df_temp['timestamp_completo'] = pd.to_datetime(df_temp['data'], dayfirst=True, errors='coerce')
            
            # CRIAMOS A COLUNA 'data_original' para o gráfico de horas usar depois
            df_temp['data_original'] = df_temp['timestamp_completo']
            
            # MANTEMOS A COLUNA 'data' apenas como data (para os filtros de calendário não quebrarem)
            df_temp['data'] = df_temp['timestamp_completo'].dt.date
            
        if 'regional' not in df_temp.columns: 
            df_temp['regional'] = "Não Informado"
            
        return df_temp
    except Exception as e:
        # Opcional: print(f"Erro ao carregar: {e}") para debug
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def carregar_cancelados():
    if not BASE_DADOS_CAN: return pd.DataFrame()
    try:
        # Lendo com utf-8-sig para evitar erro em acentos como 'descrição'
        df_temp = pd.read_csv(BASE_DADOS_CAN, sep=";", encoding='utf-8-sig')
        df_temp.columns = df_temp.columns.str.strip().str.lower()
        
        # MAPEAMENTO ATUALIZADO (Case Insensitive)
        # Note que agora mapeamos também o Setor e o Motivo Real
        mapeamento = {
            'data_encerramento_prot' : 'data',
            'descrição': 'desc_limpa', 
            'regional': 'regional', 
            'cidade': 'cidade', 
            'motivo do cancelamento': 'motivo_canc_real', # Coluna nova do gerador
            'setor que cancelou': 'setor_canc',           # Coluna nova do gerador
            'olt' : 'olt'
        }
        df_temp = df_temp.rename(columns=mapeamento)
        
        if 'data' in df_temp.columns:
            df_temp['data'] = pd.to_datetime(df_temp['data'], dayfirst=True, errors='coerce')
        
        # Preenchimento preventivo para não quebrar filtros
        for c in ['regional', 'desc_limpa', 'setor_canc', 'motivo_canc_real']:
            if c not in df_temp.columns: df_temp[c] = "Não Informado"
            
        return df_temp
    except Exception as e:
        st.error(f"Erro ao carregar cancelados: {e}")
        return pd.DataFrame()
    
@st.cache_data(ttl=3600)
def carregar_sobras():
    if not BASE_DADOS_SOB: return pd.DataFrame()
    try:
        df = pd.read_csv(BASE_DADOS_SOB, sep=";", encoding='utf-8-sig')
        df.columns = df.columns.str.strip().str.lower()
        
        # Mapeamento para seguir o seu padrão
        mapeamento = {
            'data_encerramento_prot': 'data', 
            'descrição': 'desc_limpa',
            'regional': 'regional',
            'cidade': 'cidade',
            'motivo da pendência': 'motivo_pendencia'
        }
        df = df.rename(columns=mapeamento)
        
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
        
        # Preenchimento preventivo
        if 'motivo_pendencia' not in df.columns: df['motivo_pendencia'] = "Não Informado"
            
        return df
    except:
        return pd.DataFrame()

# 1. Carregamento Inicial
df_entrantes_base = carregar_entrantes()
df_finalizados_base = carregar_finalizados()
df_cancelados_base = carregar_cancelados()
df_sobras_base = carregar_sobras()




# 2. Criação das listas para os filtros (Proteção contra KeyError)
reg_ent = set(df_entrantes_base['regional'].unique()) if 'regional' in df_entrantes_base.columns else set()
reg_fin = set(df_finalizados_base['regional'].unique()) if 'regional' in df_finalizados_base.columns else set()
reg_can = set(df_cancelados_base['regional'].unique()) if 'regional' in df_cancelados_base.columns else set()
all_regionais = sorted(list(reg_ent | reg_fin | reg_can))
all_regionais = [r for r in all_regionais if "CENTRO-OESTE" not in str(r).upper() and pd.notna(r)]

desc_ent = set(df_entrantes_base['desc_limpa'].unique()) if 'desc_limpa' in df_entrantes_base.columns else set()
desc_fin = set(df_finalizados_base['desc_limpa'].unique()) if 'desc_limpa' in df_finalizados_base.columns else set()
desc_can = set(df_cancelados_base['desc_limpa'].unique()) if 'desc_limpa' in df_cancelados_base.columns else set()
all_descricoes = sorted(list(desc_ent | desc_fin | desc_can))
all_descricoes = [r for r in all_descricoes if "Retirada de Equipamento" not in str(r).upper() and pd.notna(r)]


# =========================================================
# 3. TRATAMENTO DE DATAS
# =========================================================
datas_ent = pd.to_datetime(df_entrantes_base["data"], errors='coerce').dropna()
datas_fin = pd.to_datetime(df_finalizados_base["data"], errors='coerce').dropna()
hoje = datetime.now().date()

if not datas_ent.empty and not datas_fin.empty:
    min_d = min(datas_ent.min().date(), datas_fin.min().date())
    max_d = max(datas_ent.max().date(), datas_fin.max().date())
elif not datas_ent.empty:
    min_d, max_d = datas_ent.min().date(), datas_ent.max().date()
elif not datas_fin.empty:
    min_d, max_d = datas_fin.min().date(), datas_fin.max().date()
else:
    min_d, max_d = hoje, hoje


def aplicar_filtros_globais(df, ignorar_data=False):
    if df.empty: return df
    df_temp = df.copy()
    
    # Padronização para comparação (Remove espaços e coloca em caixa alta)
    for col in ['regional', 'desc_limpa']:
        if col in df_temp.columns:
            df_temp[col] = df_temp[col].astype(str).str.strip().str.upper()

    # 1. Filtro de Regionais (Cidades agora)
    if "Todos" not in selecao_reg and selecao_reg:
        # Transformamos a seleção do usuário em maiúsculo também
        selecao_reg_upper = [str(r).strip().upper() for r in selecao_reg]
        df_temp = df_temp[df_temp['regional'].isin(selecao_reg_upper)]

    # 2. Filtro de Descrição
    if "Todos" not in selecao_desc and selecao_desc:
        selecao_desc_upper = [str(d).strip().upper() for d in selecao_desc]
        df_temp = df_temp[df_temp['desc_limpa'].isin(selecao_desc_upper)]
    
    # 3. Filtro de Data
    if not ignorar_data and isinstance(intervalo, tuple) and len(intervalo) == 2:
        df_temp['data_only_tmp'] = pd.to_datetime(df_temp["data"]).dt.date
        mask_data = (df_temp["data_only_tmp"] >= intervalo[0]) & \
                    (df_temp["data_only_tmp"] <= intervalo[1])
        df_temp = df_temp[mask_data].drop(columns=['data_only_tmp'])
        
    return df_temp

# --- DESIGN SYSTEM: HORIZONTAL NAV + GLASS SIDEBAR + GLASSPAD METRICS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }

    /* Fundo da Página */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }

    /* 1. Estilização da Sidebar (Filtros Glassmorphism) */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.9) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* FORÇAR BRANCO NO st.title E LABELS DA SIDEBAR */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: white !important;
    }

    /* 2. Estilização das TABS (Navegação Horizontal Glass) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background-color: rgba(255, 255, 255, 0.4);
        padding: 12px 20px;
        border-radius: 20px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 12px;
        color: #475569;
        font-weight: 600;
        transition: all 0.3s;
    }

    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }

    /* 3. Estilo GLASSPAD para Métricas (Corrigido para não cortar informações) */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.45) !important;
        backdrop-filter: blur(15px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
        border-radius: 30px !important;
        padding: 25px !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.04) !important;
        overflow: visible !important; /* Ajuda a não cortar se o valor for grande */
    }

    /* 4. CORREÇÃO DOS GRÁFICOS: Evita que bordas cubram informações */
    [data-testid="stVerticalBlock"] > div:has(div[data-testid="stArrowVegaLiteChart"]),
    [data-testid="stVerticalBlock"] > div:has(div[data-testid="stPlotlyChart"]) {
        background: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(10px);
        border-radius: 30px !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        padding: 30px !important; /* Respiro extra para os nomes nos eixos */
        margin-bottom: 20px;
        overflow: visible !important;
    }

    </style>
    """, unsafe_allow_html=True)

# --- 1. FILTROS NA SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div style='margin-bottom: 20px;'>
            <h2 style='color: white; font-size: 26px; font-weight: 700; margin-bottom: 0;'>🚀 BI Horizon</h2>
            <p style='color: rgba(255,255,255,0.6); font-size: 11px; text-transform: uppercase; letter-spacing: 1px;'>Workplace Intelligence</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.title("⚙️ Filtros Gerais")
    
    # SEUS COMPONENTES ORIGINAIS
    selecao_reg = st.multiselect("Regionais:", ["Todos"] + all_regionais, default=["Todos"], key="global_reg")
    selecao_desc = st.multiselect("Descrição:", ["Todos"] + all_descricoes, default=["Todos"], key="global_desc")
    intervalo = st.date_input("Período Global:", value=(min_d, max_d), key="global_date")

    # SUA LOGICA DE VALIDAÇÃO ORIGINAL
    if isinstance(intervalo, tuple) and len(intervalo) == 2:
        data_inicio, data_fim = intervalo
        dias_no_periodo = (data_fim - data_inicio).days + 1
    else:
        st.warning("Selecione a data de início e fim no calendário.")
        st.stop()

    # Badge de Usuário Estilizado
    st.markdown(f"""
        <div style='margin-top: 30px; background: rgba(255,255,255,0.08); padding: 15px; border-radius: 18px; border: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; gap: 12px;'>
            <div style='width: 35px; height: 35px; background: #3b82f6; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white;'>KF</div>
            <div>
                <p style='color: white; font-size: 14px; margin: 0; font-weight: 600;'>Kevyn Ferrezin</p>
                <p style='color: #94a3b8; font-size: 11px; margin: 0;'>Administrator</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Função Auxiliar para calcular projeção (Evita erro de variável não definida)
def calcular_valor_projecao(df, d_inicio, d_fim):
    if df is None or df.empty: 
        return 0, []
    
    df_temp = df.copy()
    
    # Força conversão e limpa NaTs
    df_temp['data'] = pd.to_datetime(df_temp['data'], errors='coerce', dayfirst=True)
    df_temp = df_temp.dropna(subset=['data'])
    df_temp['data_only'] = df_temp['data'].dt.date
    
    # 1. Tenta pegar o histórico (28 dias antes do início)
    limite_hist = d_inicio - timedelta(days=28)
    df_hist = df_temp[(df_temp['data_only'] < d_inicio) & (df_temp['data_only'] >= limite_hist)].copy()
    
    # 2. SE O HISTÓRICO ESTIVER VAZIO (ex: início de janeiro), usa o período atual como base
    if df_hist.empty:
        df_hist = df_temp[(df_temp['data_only'] >= d_inicio) & (df_temp['data_only'] <= d_fim)].copy()
    
    # 3. Se ainda assim estiver vazio, retorna 0 (não há dados mesmo)
    if df_hist.empty:
        return 0, [0] * ((d_fim - d_inicio).days + 1)

    # 4. Cálculo da média por dia da semana
    df_hist['dia_sem'] = df_hist['data'].dt.dayofweek
    vol_hist = df_hist.groupby(['data_only', 'dia_sem']).size().reset_index(name='v')
    media_map = vol_hist.groupby('dia_sem')['v'].mean().to_dict()
    media_geral = vol_hist['v'].mean()

    # 5. Gera a projeção diária
    d_range = pd.date_range(start=d_inicio, end=d_fim)
    lista_proj = [int(round(media_map.get(d.dayofweek, media_geral))) for d in d_range]
    
    return sum(lista_proj), lista_proj

# --- 1. DEFINIÇÃO DAS DATAS ---
if isinstance(intervalo, tuple) and len(intervalo) == 2:
    data_inicio, data_fim = intervalo
    dia_foco = data_fim 
    dia_anterior = data_inicio - timedelta(days=1)
else:
    st.stop()

# --- 2. CÁLCULO DAS PROJEÇÕES ---
# Entrantes
df_ent_filtrado = aplicar_filtros_globais(df_entrantes_base)
_, lista_ent = calcular_valor_projecao(df_ent_filtrado, data_inicio, data_fim)
total_projetado_ent = lista_ent[-1] if lista_ent else 0 

# Finalizados
df_fin_filtrado = aplicar_filtros_globais(df_finalizados_base)
_, lista_fin = calcular_valor_projecao(df_fin_filtrado, data_inicio, data_fim)
total_projetado_fin = lista_fin[-1] if lista_fin else 0 

# Cancelados
df_can_filtrado = aplicar_filtros_globais(df_cancelados_base)
_, lista_can = calcular_valor_projecao(df_can_filtrado, data_inicio, data_fim)
total_projetado_can = lista_can[-1] if lista_can else 0 

# --- 3. CÁLCULO DAS SOBRAS (D-1) ---
df_sob_proc = aplicar_filtros_globais(df_sobras_base, ignorar_data=True)
if not df_sob_proc.empty:
    df_sob_proc['created_at'] = pd.to_datetime(df_sob_proc['created_at'], errors='coerce', dayfirst=True)
    mask_sobras = df_sob_proc['created_at'].dt.date == dia_anterior
    total_sobras = len(df_sob_proc[mask_sobras])
else:
    total_sobras = 0

# --- 4. CÁLCULO DA ROTA INICIAL ---
carga_total_hoje = total_projetado_ent + total_sobras
vazao_total_hoje = total_projetado_fin + total_projetado_can
rota_inicial_amanha = carga_total_hoje - vazao_total_hoje

# =========================================================
# 5. PREPARO PARA A HOME (NOMES IGUAIS AO SEU WITH)
# =========================================================
df_aging_foco = df_sob_proc.copy()
if not df_aging_foco.empty:
    df_aging_foco['data_dt'] = pd.to_datetime(df_aging_foco['created_at'], errors='coerce')
    df_aging_foco['aging_dias'] = (datetime.now() - df_aging_foco['data_dt']).dt.days
    
    # CRIANDO O df_plot QUE SUA HOME PEDE
    def classificar_home(d):
        if d <= 1: return "🟢 0-24h"
        if d <= 2: return "🟡 24-48h"
        return "🔴 +48h"
    df_aging_foco['faixa_sla'] = df_aging_foco['aging_dias'].apply(classificar_home)
    df_plot = df_aging_foco.groupby('faixa_sla').size().reset_index(name='qtd')
    
    # CRIANDO O df_cid_age QUE SUA HOME PEDE
    df_cid_age = df_aging_foco.groupby('cidade')['aging_dias'].mean().reset_index().sort_values('aging_dias', ascending=False)
else:
    df_plot = pd.DataFrame(columns=['faixa_sla', 'qtd'])
    df_cid_age = pd.DataFrame(columns=['cidade', 'aging_dias'])

# Função de Card ajustada para o seu uso
def criar_card_membro(coluna, nome, cargo):
    with coluna:
        st.markdown(f"""
            <div style="background:#f0f2f6; padding:10px; border-radius:10px; text-align:center; border: 1px solid #d1d5db;">
                <p style="margin:0; font-weight:bold; color:#1e3a8a;">{nome}</p>
                <p style="margin:0; font-size:12px; color:#64748b;">{cargo}</p>
            </div>
        """, unsafe_allow_html=True)

# --- 2. NAVEGAÇÃO HORIZONTAL (TOPO) ---
tab_home, tab_entrante, tab_finalizado, tab_cancelado, tab_rota_inicial, tab_aging, tab_eficiencia = st.tabs([
    "🏠 Visão Geral", 
    "📈 Projeção Entrantes", 
    "🔍 Projeção Finalizados", 
    "❌ Projeção Cancelados",
    "🚛 Rota Inicial",
    "⏳ Aging",
    "⚡ Eficiência"

])



with tab_home:
    st.title("🚀 Executive Overview – Operação Telecom")
    
    # Linha 1: O Pulso da Operação
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Entrantes (Proj)", f"{int(total_projetado_ent)}", delta="Demanda")
    with c2:
        st.metric("Vazão (Fin+Can)", f"{int(total_projetado_fin + total_projetado_can)}", delta="Capacidade")
    with c3:
        st.metric("Rota Inicial D+1", f"{int(rota_inicial_amanha)}", delta="Sobrecarga", delta_color="inverse")
    with c4:
        # Usamos o df_aging_foco que definimos lá no processamento
        val_aging = df_aging_foco['aging_dias'].mean() if not df_aging_foco.empty else 0
        st.metric("Aging Médio", f"{val_aging:.1f} Dias", delta="SLA")

    st.markdown("---")

    # Linha 2: Diagnóstico Rápido
    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        st.subheader("📈 Tendência de Fluxo (Entrada vs. Saída)")
        df_tendencia = pd.DataFrame({
            'Data': pd.date_range(start=data_inicio, end=data_fim),
            'Entrantes': lista_ent,
            'Finalizados': lista_fin
        }).set_index('Data')
        st.line_chart(df_tendencia)

    with col_r:
        st.subheader("🎯 Saúde da Fila")
        # AGORA df_plot EXISTE!
        fig_donut = alt.Chart(df_plot).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="qtd", type="quantitative"),
            color=alt.Color(field="faixa_sla", type="nominal", scale=alt.Scale(range=['#22c55e', '#eab308', '#f97316', '#ef4444'])),
            tooltip=['faixa_sla', 'qtd']
        ).properties(height=300)
        st.altair_chart(fig_donut, use_container_width=True)

    # Linha 3: O "Insight do Sênior"
    if not df_cid_age.empty:
        st.info(f"💡 **Insight da Operação:** Atualmente, a cidade de **{df_cid_age.iloc[0]['cidade']}** apresenta o maior gargalo de Aging. Recomenda-se deslocar força técnica.")
    
    st.markdown("---")
    
    # RESOLVENDO O ERRO col_e1: Criamos as colunas aqui!
    st.subheader("👥 Equipe do Projeto")
    col_e1, col_e2, col_e3 = st.columns(3)
    
    # Agora passamos a coluna criada para a função
    criar_card_membro(col_e1, "Kevyn Ribeiro Ferrezin", "Cientista de Dados")

with tab_entrante:
    st.title("📈 Dashboard – Projeção de Entrantes")
    st.caption(f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # ==============================
    # 1. PROCESSAMENTO COM FILTRO GLOBAL
    # ==============================
    df_filtrado = aplicar_filtros_globais(df_entrantes_base)

    # --- EXCLUSÃO ESPECÍFICA ---
    if not df_filtrado.empty and 'regional' in df_filtrado.columns:
        df_filtrado = df_filtrado[~df_filtrado['regional'].str.contains('CENTRO-OESTE', case=False, na=False)]

    # Carga do Clima
    try:
        df_clima = pd.read_csv("clima_atual.csv", sep=",")
        df_clima.columns = df_clima.columns.str.lower()
        df_clima['cidade'] = df_clima['cidade'].str.strip().str.title()
    except:
        df_clima = pd.DataFrame(columns=['cidade', 'fator', 'risco'])

    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados.")
        st.stop()

    data_inicio, data_fim = intervalo

    # ==============================
    # 2. LÓGICA DE DADOS (FOCO X HISTÓRICO)
    # ==============================
    # Usamos .dt.date para nivelar a comparação com o calendário do Streamlit
    df_foco = df_filtrado[(pd.to_datetime(df_filtrado["data"]).dt.date >= data_inicio) & 
                        (pd.to_datetime(df_filtrado["data"]).dt.date <= data_fim)]

    df_hist_ref = df_filtrado[pd.to_datetime(df_filtrado["data"]).dt.date < data_inicio]

    if df_hist_ref.empty: 
        df_hist_ref = df_foco.copy()

  # ==============================================================================
    # CORE: PROJEÇÃO PURA - ÚLTIMAS 4 SEMANAS (CORRIGIDO)
    # ==============================================================================

    # 1. Filtro preventivo para não inflar a média
    # df_foco já vem filtrado lá de cima
    df_foco = df_foco[df_foco['desc_limpa'] != "Retirada de Equipamento"]

    # Chamada da função com o novo parâmetro para pegar o histórico filtrado por regional
    df_hist_filtrado = aplicar_filtros_globais(df_entrantes_base, ignorar_data=True)

    # Criar colunas de apoio
    df_hist_filtrado['data_only'] = pd.to_datetime(df_hist_filtrado['data']).dt.date
    
    # 2. Janela de 28 dias antes do início do filtro
    data_limite_hist = data_inicio - pd.Timedelta(days=28)
    
    df_hist_recente = df_hist_filtrado[
        (df_hist_filtrado['data_only'] < data_inicio) & 
        (df_hist_filtrado['data_only'] >= data_limite_hist)
    ].copy()

    # Identificar dia da semana
    df_hist_recente['dia_semana_num'] = pd.to_datetime(df_hist_recente['data_only']).dt.dayofweek

    # 3. Média Real por Dia da Semana
    vol_diario_hist = df_hist_recente.groupby(['data_only', 'dia_semana_num']).size().reset_index(name='vol')
    media_por_dia_semana = vol_diario_hist.groupby('dia_semana_num')['vol'].mean().to_dict()
    media_diaria_hist = vol_diario_hist['vol'].mean() if not vol_diario_hist.empty else 0

    # 4. Cálculo da Projeção
    datas_periodo = pd.date_range(start=data_inicio, end=data_fim)
    qtd_dias_base = df_hist_recente['data_only'].nunique() or 1
    projecao_lista = []

    for dt in datas_periodo:
        d_sem = dt.dayofweek
        valor_base = media_por_dia_semana.get(d_sem, media_diaria_hist)
        projecao_lista.append(int(round(valor_base)))

    # df_proj_dia para o gráfico
    df_proj_dia = pd.DataFrame({
        'data': [d.date() for d in datas_periodo],
        'Projeção': projecao_lista
    })

    # 5. Métricas Finais
    realizado_total = len(df_foco)
    total_projetado = sum(projecao_lista)
    aderencia = (realizado_total / total_projetado * 100) if total_projetado > 0 else 0
    gap = realizado_total - total_projetado

    # --- SEÇÃO 1: METRICAS ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Entrante ({dias_no_periodo}d)", f"{realizado_total:,}")
    c2.metric("Projeção", f"{total_projetado:,}")
    c3.metric("Aderência (E/P)", f"{aderencia:.1f}%", delta=f"{aderencia-100:.1f}%")
    c4.metric("Gap", f"{gap:,}", delta=gap, delta_color="inverse")

    # --- SEÇÃO 2: EVOLUÇÃO (REALIZADO X PROJEÇÃO) ---
    st.markdown("---")
    st.subheader("📈 Tendência Histórica (Realizado x Projeção)")

    if not df_foco.empty:
        # 1. Preparação dos dados de Realizado
        # Garantimos a criação da coluna temporária 'data_temp' para não dar KeyError
        df_realizado_dia = df_foco.copy()
        df_realizado_dia['data_temp'] = pd.to_datetime(df_realizado_dia['data']).dt.date
        
        # Agrupamos pelo dia (sem hora)
        df_realizado_dia = df_realizado_dia.groupby("data_temp").size().reset_index(name="Realizado")
        df_realizado_dia.columns = ['data', 'Realizado']
        
        # 2. Merge dos dados com o df_proj_dia (que vem do Core)
        df_evolucao = pd.merge(df_proj_dia, df_realizado_dia, on="data", how="left").fillna(0)
        
        # 3. Valor fixo do Realizado Total para o Tooltip
        total_realizado_periodo = len(df_foco)
        df_evolucao['Realizado_Total_Periodo'] = total_realizado_periodo
        
        # Formatação da data para o eixo X
        df_evolucao['data_str'] = df_evolucao['data'].apply(lambda x: x.strftime('%d/%m'))

        # --- Gráfico Altair ---
        base = alt.Chart(df_evolucao).encode(
            x=alt.X('data_str:N', title=None, sort=None, axis=alt.Axis(labelAngle=-45))
        )

        # Camada de BARRAS (Tooltip com Realizado Total e SEM Projeção)
        barras = base.mark_bar(color="#0059FF", opacity=0.7).encode(
            y=alt.Y('Realizado:Q', title="Volume"),
            tooltip=[
                alt.Tooltip('data_str:N', title='Data'),
                alt.Tooltip('Realizado:Q', title='Realizado no Dia'),
                alt.Tooltip('Realizado_Total_Periodo:Q', title='Realizado Total (Filtro)')
            ]
        )

        # Camada de LINHA (Projeção)
        linha = base.mark_line(color="#000000", strokeWidth=3).encode(
            y=alt.Y('Projeção:Q'),
            tooltip=[
                alt.Tooltip('data_str:N', title='Data'),
                alt.Tooltip('Projeção:Q', title='Projeção do Dia')
            ]
        )
        
        pontos = base.mark_point(color="#000000", size=60, filled=True).encode(
            y=alt.Y('Projeção:Q'),
            tooltip=[
                alt.Tooltip('data_str:N', title='Data'),
                alt.Tooltip('Projeção:Q', title='Projeção do Dia')
            ]
        )

        chart_final = alt.layer(barras, linha, pontos).properties(height=350)
        st.altair_chart(chart_final, use_container_width=True)
    else:
        st.warning("Sem dados suficientes para gerar o gráfico de evolução.")

    # --- SEÇÃO 4: CALENDÁRIO (PADRONIZADO) ---
    st.markdown("---")
    st.subheader("🗓️ Intensidade de Volume (Calendário)")

    if not df_foco.empty:
        df_cal = df_foco.copy()
        
        # 1. Normalização da data e criação de colunas de tempo
        df_cal['data_limpa'] = pd.to_datetime(df_cal['data']).dt.date
        df_cal['Dia'] = pd.to_datetime(df_cal['data_limpa']).dt.day
        
        # 2. Lógica de Semana Relativa (Para os dias ficarem na mesma linha corretamente)
        # Em vez de isocalendar, usamos strftime para definir a linha do calendário
        df_cal['Semana_Eixo'] = pd.to_datetime(df_cal['data_limpa']).dt.strftime('%Y-%U')
        
        # 3. Mapeamento Correto (Pandas: 0=Segunda ... 6=Domingo)
        # Se você quer o Domingo na primeira coluna, o mapeamento deve ser este:
        dias_map = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
        df_cal['Dia_Semana'] = pd.to_datetime(df_cal['data_limpa']).dt.dayofweek.map(dias_map)
        
        # Ordem das colunas (Iniciando na Segunda para alinhar com o padrão .dayofweek)
        ordem_dias = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']

        # 4. Agrupamento
        df_cal_diario = df_cal.groupby(['data_limpa', 'Dia', 'Semana_Eixo', 'Dia_Semana']).size().reset_index(name='Volume')
        df_cal_diario = df_cal_diario.rename(columns={'data_limpa': 'Data'})

        # 5. Construção do Gráfico Altair
        base = alt.Chart(df_cal_diario).encode(
            x=alt.X('Dia_Semana:N', sort=ordem_dias, title=None, 
                    axis=alt.Axis(orient='top', labelAngle=0, domain=False)),
            y=alt.Y('Semana_Eixo:O', title=None, axis=None), # Oculta o eixo Y para parecer calendário
        ).properties(height=250)

        retangulos = base.mark_rect(stroke='white', strokeWidth=2, cornerRadius=4).encode(
            color=alt.Color('Volume:Q', scale=alt.Scale(scheme='blues'), legend=None),
            tooltip=[
                alt.Tooltip('Data:T', format='%d/%m/%Y'), 
                alt.Tooltip('Volume:Q', title='Volume Realizado')
            ]
        )

        texto = base.mark_text(baseline='middle', fontSize=14, fontWeight='bold').encode(
            text='Dia:Q',
            color=alt.condition(
                alt.datum.Volume > df_cal_diario['Volume'].mean(), 
                alt.value('white'), 
                alt.value('black')
            )
        )
        
        st.altair_chart(retangulos + texto, use_container_width=True)

    # --- SEÇÃO 5: PLANO DE AÇÃO ---
    st.markdown("---")
    st.header("🎯 Foco Operacional (Plano de Ação)")

    if not df_foco.empty:
        df_cidades_foco = df_foco.groupby("cidade").size().reset_index(name="Realizado")
        df_hist_ref = df_entrantes_base # Garantindo que usa a base correta conforme o Core anterior
        cidade_hist = df_hist_ref.groupby("cidade").size().reset_index(name="soma_hist")
        
        tab_acao = df_cidades_foco.merge(cidade_hist[['cidade', 'soma_hist']], on='cidade', how='left')
        tab_acao = tab_acao.merge(df_clima[['cidade', 'fator']], on='cidade', how='left').fillna({'fator':1.0, 'soma_hist':0})
        
        # Mantemos o cálculo interno se precisar, mas não exibiremos
        tab_acao['Média_Histórica'] = (tab_acao['soma_hist'] / qtd_dias_base).round(0).astype(int)
        
        media_esperada_linear = (media_diaria_hist * dias_no_periodo)
        peso_periodo = total_projetado / media_esperada_linear if media_esperada_linear > 0 else 1

        tab_acao['Projeção'] = ((tab_acao['soma_hist'] / qtd_dias_base) * tab_acao['fator'] * dias_no_periodo * peso_periodo).round(0).astype(int)
        
        tab_acao['Gap'] = (tab_acao['Projeção'] - tab_acao['Realizado']).astype(int)
        tab_acao['Aderência %'] = (tab_acao['Projeção'] / tab_acao['Realizado'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0).round(1)

        col_1, col_2 = st.columns(2)
        
        with col_1:
            st.write("**Top 10 Cidades (Maior Desvio Negativo)**")
            # REMOVIDO 'Média_Histórica' da lista abaixo:
            df_exibir = tab_acao[['cidade', 'Realizado', 'Projeção', 'Gap', 'Aderência %']].sort_values("Gap", ascending=True).head(10)
            
            st.dataframe(
                df_exibir, 
                column_config={
                    "Aderência %": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                    "Gap": st.column_config.NumberColumn(format="%d 🚩")
                },
                hide_index=True, 
                use_container_width=True
            )

        with col_2:
            if 'regional' in df_foco.columns:
                st.write("**Volume por Regional**")
                reg_data = df_foco.groupby("regional").size().reset_index(name="Vol").sort_values("Vol", ascending=False)
                st.bar_chart(reg_data.set_index("regional"), color="#0059FF")

    # --- SEÇÃO 6: DESCRIÇÃO ---
    st.markdown("---")
    st.header("📦 Volume por tipo de serviço")

    if not df_foco.empty:
        possiveis_colunas = ['desc_limpa', 'descrição', 'descricao', 'servico']
        col_ativa = next((c for c in possiveis_colunas if c in df_foco.columns), None)

        if col_ativa:
            df_desc = df_foco.groupby(col_ativa).size().reset_index(name="Quantidade").sort_values("Quantidade", ascending=False)
            
            col_t, col_g = st.columns([1, 2])
            with col_t:
                st.dataframe(df_desc, hide_index=True, use_container_width=True)
            with col_g:
                chart_desc = alt.Chart(df_desc).mark_bar(color="#0059FF").encode(
                    x=alt.X("Quantidade:Q", title="Volume"), 
                    y=alt.Y(f"{col_ativa}:N", sort="-x", title=None),
                    tooltip=[col_ativa, "Quantidade"]
                ).properties(height=350)
                st.altair_chart(chart_desc, use_container_width=True)
        else:
            st.info("💡 Nenhuma coluna de descrição encontrada.")

# --- SEÇÃO 7: ANÁLISE POR OLT ---
    st.markdown("---")
    st.header("📡 Volume de Entrantes por OLT")

    # Busca a coluna ignorando maiúsculas/minúsculas e espaços
    cols_norm = {c.strip().upper(): c for c in df_foco.columns}
    col_olt = cols_norm.get('OLT') 

    if not df_foco.empty:
        if col_olt:
            # Agrupamento e Cálculos
            df_olt = df_foco.groupby(col_olt).size().reset_index(name="Quantidade")
            df_olt = df_olt.sort_values("Quantidade", ascending=False)
            total_olt = df_olt["Quantidade"].sum()
            df_olt["Participação %"] = (df_olt["Quantidade"] / total_olt * 100).round(1)

            # Layout das colunas
            col_t_olt, col_g_olt = st.columns([1, 2])
            
            with col_t_olt:
                st.dataframe(
                    df_olt, 
                    column_config={
                        col_olt: "Identificação OLT",
                        "Participação %": st.column_config.ProgressColumn(
                            min_value=0, max_value=100, format="%.1f%%"
                        ),
                        "Quantidade": st.column_config.NumberColumn(format="%d 📡")
                    },
                    hide_index=True, 
                    use_container_width=True
                )
            
            with col_g_olt:
                # Gráfico Altair com a coluna correta encontrada
                chart_olt = alt.Chart(df_olt.head(15)).mark_bar(color="#0059FF").encode(
                    x=alt.X("Quantidade:Q", title="Volume de Entrantes"),
                    y=alt.Y(f"{col_olt}:N", sort="-x", title=None),
                    tooltip=[col_olt, "Quantidade", "Participação %"]
                ).properties(height=400)
                st.altair_chart(chart_olt, use_container_width=True)
        else:
            # Se não achar, mostra as colunas disponíveis para te ajudar a debugar
            st.warning(f"⚠️ Coluna 'OLT' não encontrada. Colunas disponíveis: {list(df_foco.columns)}")

    # --- SEÇÃO 8: ENTRANTES POR HORA ---
    st.markdown("---")
    st.header("⏰ Distribuição de Entrantes por Hora")

    if not df_foco.empty:
        # 1. Extrai a hora e conta o volume
        df_hora_raw = pd.to_datetime(df_foco['data'])
        df_vol_hora = df_hora_raw.dt.hour.value_counts().reset_index()
        df_vol_hora.columns = ['hora', 'Volume']
        
        # 2. Garante as 24h no gráfico
        template_horas = pd.DataFrame({'hora': range(24)})
        df_final_horas = template_horas.merge(df_vol_hora, on='hora', how='left').fillna(0)
        df_final_horas['Hora_Label'] = df_final_horas['hora'].apply(lambda x: f"{int(x):02d}h")

        # 3. Identifica o volume máximo para o destaque
        max_vol_hora = df_final_horas['Volume'].max()
        
        # Criamos a flag de destaque (apenas se o volume for maior que zero)
        df_final_horas['Destaque'] = df_final_horas.apply(
            lambda x: 'Pico' if x['Volume'] == max_vol_hora and max_vol_hora > 0 else 'Normal', axis=1
        )

        # 4. Gráfico com a lógica de cor por escala
        chart_hora = alt.Chart(df_final_horas).mark_bar().encode(
            x=alt.X('Hora_Label:N', title="Hora do Dia", sort=None), # sort=None mantém a ordem das 00h às 23h
            y=alt.Y('Volume:Q', title="Quantidade"),
            # Mapeamento de cor: Pico = Vermelho, Normal = Verde
            color=alt.Color('Destaque:N',
                scale=alt.Scale(
                    domain=['Pico', 'Normal'],
                    range=['#D62728', '#0059FF']
                ),
                legend=None
            ),
            tooltip=[
                alt.Tooltip('Hora_Label:N', title='Horário'),
                alt.Tooltip('Volume:Q', title='Volume')
            ]
        ).properties(height=300)

        st.altair_chart(chart_hora, use_container_width=True)

        
    # --- SEÇÃO 8: MOTIVO ---
    st.markdown("---")
    st.header("🔍 Detalhamento por Motivo")

    cols_norm_motivo = {c.strip().upper(): c for c in df_foco.columns}
    col_motivo_real = cols_norm_motivo.get('MOTIVO') 

    if df_foco.empty:
        st.warning("⚠️ Não há dados disponíveis para os filtros selecionados.")
    elif not col_motivo_real:
        st.info(f"💡 Coluna 'Motivo' não encontrada.")
    else:
        df_motivo_count = df_foco.copy()
        df_motivo_count[col_motivo_real] = df_motivo_count[col_motivo_real].fillna("Não Informado").astype(str).str.strip()
        
        df_motivo_plot = df_motivo_count.groupby(col_motivo_real).size().reset_index(name="Quantidade")
        df_motivo_plot = df_motivo_plot.sort_values("Quantidade", ascending=False)
        
        total_motivos = df_motivo_plot["Quantidade"].sum()
        df_motivo_plot["Participação %"] = (df_motivo_plot["Quantidade"] / total_motivos * 100).round(1)

        # --- LÓGICA DE COR EXPLÍCITA ---
        # Criamos uma coluna 'Cor' onde o maior valor ganha o código do vermelho
        max_v = df_motivo_plot["Quantidade"].max()
        df_motivo_plot['Cor'] = df_motivo_plot['Quantidade'].apply(lambda x: '#D62728' if x == max_v else '#0059FF')

        col_t_motivo, col_g_motivo = st.columns([1, 2])
        
        with col_t_motivo:
            st.dataframe(
                df_motivo_plot[[col_motivo_real, 'Quantidade', 'Participação %']],
                column_config={
                    col_motivo_real: "Motivo Chamado",
                    "Participação %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
                    "Quantidade": st.column_config.NumberColumn(format="%d 🛠️")
                },
                hide_index=True,
                use_container_width=True
            )
            
        with col_g_motivo:
            # Agora o gráfico lê a cor diretamente da coluna 'Cor' do DataFrame
            chart_motivo = alt.Chart(df_motivo_plot.head(15)).mark_bar().encode(
                x=alt.X("Quantidade:Q", title="Volume"),
                y=alt.Y(f"{col_motivo_real}:N", sort="-x", title=None),
                color=alt.Color('Cor:N', scale=None), # scale=None diz ao Altair para usar as cores hex que estão na coluna
                tooltip=[col_motivo_real, "Quantidade", "Participação %"]
            ).properties(height=400)
            
            st.altair_chart(chart_motivo, use_container_width=True)

with tab_finalizado:
    st.title("🔍 Dashboard – Detalhamento de Finalizados")
    st.caption(f"Base de Dados: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # ==============================================================================
    # 1. PROCESSAMENTO COM FILTRO GLOBAL (REALIZADO)
    # ==============================================================================
    df_foco = aplicar_filtros_globais(df_finalizados_base, ignorar_data=False)

    if df_foco.empty:
        st.warning("⚠️ Nenhum dado de FINALIZADOS encontrado para os filtros selecionados.")
        st.stop()

    data_inicio, data_fim = intervalo 

    # ==============================================================================
    # 2. CORE: PROJEÇÃO FINALIZADOS - PADRÃO ENTRANTE (SEM CLIMA)
    # ==============================================================================

    # Buscamos a base histórica filtrada (Regional/Descrição) sem o corte da data atual
    df_hist_filtrado = aplicar_filtros_globais(df_finalizados_base, ignorar_data=True)
    
    # Garantimos que a data seja datetime
    df_hist_filtrado['data'] = pd.to_datetime(df_hist_filtrado['data'], errors='coerce')
    df_hist_filtrado['data_only'] = df_hist_filtrado['data'].dt.date

    # Janela de 28 dias antes do início do filtro
    data_limite_hist = data_inicio - pd.Timedelta(days=28)
    
    df_hist_recente = df_hist_filtrado[
        (df_hist_filtrado['data_only'] < data_inicio) & 
        (df_hist_filtrado['data_only'] >= data_limite_hist)
    ].copy()

    # Identificar dia da semana (0=Segunda, 6=Domingo)
    df_hist_recente['dia_semana_num'] = pd.to_datetime(df_hist_recente['data_only']).dt.dayofweek

    # 3. Média Real por Dia da Semana (Histórico de 4 semanas)
    vol_diario_hist = df_hist_recente.groupby(['data_only', 'dia_semana_num']).size().reset_index(name='vol')
    media_por_dia_semana = vol_diario_hist.groupby('dia_semana_num')['vol'].mean().to_dict()
    media_diaria_hist = vol_diario_hist['vol'].mean() if not vol_diario_hist.empty else 0

    # 4. Cálculo da Projeção para o período selecionado
    datas_periodo = pd.date_range(start=data_inicio, end=data_fim)
    qtd_dias_base = df_hist_recente['data_only'].nunique() or 1
    projecao_lista = []

    for dt in datas_periodo:
        d_sem = dt.dayofweek
        # Busca a média do dia da semana. Se não houver, usa a média geral do período.
        valor_base = media_por_dia_semana.get(d_sem, media_diaria_hist)
        projecao_lista.append(int(round(valor_base)))

    # df_proj_dia para o gráfico de evolução de Finalizados
    df_proj_dia = pd.DataFrame({
        'data': [d.date() for d in datas_periodo],
        'Projeção': projecao_lista
    })

    # 5. Métricas Finais para os Cards
    realizado_total = len(df_foco)
    total_projetado = sum(projecao_lista)
    aderencia = (realizado_total / total_projetado * 100) if total_projetado > 0 else 0
    gap = int(realizado_total - total_projetado)


    # --- SEÇÃO 1: METRICAS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"Finalizados ({dias_no_periodo}d)", f"{realizado_total:,}")
    m2.metric("Projeção", f"{total_projetado:,}")
    m3.metric("Aderência (F/P)", f"{aderencia:.1f}%")
    m4.metric("Gap", f"{gap:,}", delta=gap, delta_color="normal")

    # --- SEÇÃO 2: TENDÊNCIA HISTÓRICA ---
    st.markdown("---")
    st.subheader("📈 Tendência Histórica")

    if not df_foco.empty:
        # 1. Agrupar realizado por data
        df_realizado_dia = df_foco.groupby("data").size().reset_index(name="Realizado")
        
        # 2. Garantir que as datas no dataframe de realizado sejam do tipo 'date' para o merge
        df_realizado_dia['data'] = pd.to_datetime(df_realizado_dia['data']).dt.date

        # 3. Criar o DataFrame de evolução usando o df_proj_dia que já calculamos no CORE
        # O df_proj_dia já contém as datas e os valores de Projeção sem o fator_clima
        df_evolucao = pd.merge(df_proj_dia, df_realizado_dia, on="data", how="left").fillna(0)
        
        # 4. Formatação para o gráfico
        df_evolucao['data_str'] = df_evolucao['data'].apply(lambda x: x.strftime('%d/%m'))

        # 5. Construção do Gráfico Altair
        base = alt.Chart(df_evolucao).encode(
            x=alt.X('data_str:N', title="Dia/Mês", sort=None, axis=alt.Axis(labelAngle=-90))
        )
        
        barras = base.mark_bar(color="#2FB53A", opacity=0.7).encode(
            y=alt.Y('Realizado:Q', title="Volume")
        )
        
        linha = base.mark_line(color="#000000", strokeWidth=3).encode(
            y=alt.Y('Projeção:Q')
        )
        
        pontos = base.mark_point(color="#000000", size=60).encode(
            y='Projeção:Q'
        )
        
        # Renderizar gráfico com camada de Barras (Realizado) e Linha (Projeção)
        st.altair_chart(alt.layer(barras, linha, pontos).properties(height=350), use_container_width=True)

    # --- SEÇÃO 4: CALENDÁRIO ---
    st.markdown("---")
    st.subheader("🗓️ Intensidade de Volume (Calendário)")

    if not df_foco.empty:
        df_cal = df_foco.copy()
        df_cal['data'] = pd.to_datetime(df_cal['data'])
        df_cal['Dia'] = df_cal['data'].dt.day
        
        # CORREÇÃO DA SEMANA: Criamos um índice de semana relativo ao início do gráfico
        # Isso evita que o dia 01 fique sozinho em uma linha gigante se ele for fim/início de semana iso
        df_cal['Semana_Acumulada'] = df_cal['data'].apply(lambda x: x.strftime('%V')) # Semana ISO
        
        # Se o gráfico ainda quebrar estranho, usamos a diferença de dias para criar as linhas
        min_date = df_cal['data'].min()
        df_cal['Semana_Relativa'] = df_cal['data'].apply(lambda x: ((x - min_date).days + min_date.weekday() + 1) // 7)

        dias_map = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
        df_cal['Dia_Semana'] = df_cal['data'].dt.dayofweek.map(dias_map)
        ordem_dias = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']

        df_cal_diario = df_cal.groupby(['data', 'Dia', 'Semana_Relativa', 'Dia_Semana']).size().reset_index(name='Volume')

        # Ajuste do gráfico para parecer um calendário
        base = alt.Chart(df_cal_diario).encode(
            x=alt.X('Dia_Semana:N', sort=ordem_dias, title=None, 
                    axis=alt.Axis(orient='top', labelAngle=0, domain=False, ticks=False)),
            y=alt.Y('Semana_Relativa:O', title=None, axis=None), # Removemos o eixo Y para não mostrar números de semanas
        ).properties(height=200) # Altura menor para parecer uma fita de calendário

        retangulos = base.mark_rect(stroke='white', strokeWidth=3, cornerRadius=4).encode(
            color=alt.Color('Volume:Q', scale=alt.Scale(scheme='greens'), legend=None),
            tooltip=['data:T', 'Volume:Q']
        )

        texto = base.mark_text(baseline='middle', fontSize=16, fontWeight='bold').encode(
            text='Dia:Q',
            color=alt.condition(alt.datum.Volume > df_cal_diario['Volume'].median(), alt.value('white'), alt.value('black'))
        )

        st.altair_chart(retangulos + texto, use_container_width=True)

    # --- SEÇÃO 5: PLANO DE AÇÃO ---
    st.markdown("---")
    st.header("🎯 Foco Operacional (Plano de Ação)")

    if not df_foco.empty:
        # 1. Agrupamento por cidade (Realizado no período selecionado)
        df_cidades_foco = df_foco.groupby("cidade").size().reset_index(name="Realizado")
        
        # 2. Histórico por cidade (Usando df_hist_recente que filtramos no CORE)
        # df_hist_recente contém os dados das últimas 4 semanas
        cidade_hist = df_hist_recente.groupby("cidade").size().reset_index(name="soma_hist")
        
        # 3. Cruzamento de dados
        tab_acao = df_cidades_foco.merge(cidade_hist[['cidade', 'soma_hist']], on='cidade', how='left')
        tab_acao['soma_hist'] = tab_acao['soma_hist'].fillna(0)
        
        # 4. Cálculos de Projeção por Cidade (Proporcional ao período)
        # Média diária da cidade * quantidade de dias selecionados no filtro
        tab_acao['Média_Histórica'] = (tab_acao['soma_hist'] / qtd_dias_base).round(1)
        
        # Projeção da Cidade para o período atual
        # Calculamos a proporção baseada no total_projetado geral para manter a mesma régua
        media_esperada_linear = (media_diaria_hist * dias_no_periodo)
        peso_periodo = total_projetado / media_esperada_linear if media_esperada_linear > 0 else 1

        tab_acao['Projeção'] = ((tab_acao['soma_hist'] / qtd_dias_base) * dias_no_periodo * peso_periodo).round(0).astype(int)
        
        # Gap e Aderência
        # Gap Positivo = Cidade está acima da projeção (trabalhou mais que a média)
        # Gap Negativo = Cidade está abaixo da projeção
        tab_acao['Gap'] = (tab_acao['Realizado'] - tab_acao['Projeção']).astype(int)
        tab_acao['Aderência %'] = (tab_acao['Realizado'] / tab_acao['Projeção'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0).round(1)

        # 5. Interface Visual
        col_1, col_2 = st.columns(2)
        
        with col_1:
            st.write("**Top 10 Cidades (Menor Aderência)**")
            # Ordenamos pelas cidades que estão mais distantes da meta (Gap negativo)
            df_exibir = tab_acao[['cidade', 'Realizado', 'Projeção', 'Gap', 'Aderência %']].sort_values("Gap", ascending=True).head(10)
            
            st.dataframe(
                df_exibir, 
                column_config={
                    "Aderência %": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                    "Gap": st.column_config.NumberColumn(format="%d 🚩")
                },
                hide_index=True, 
                use_container_width=True
            )

        with col_2:
            if 'regional' in df_foco.columns:
                st.write("**Volume por Regional (Realizado)**")
                reg_data = df_foco.groupby("regional").size().reset_index(name="Vol").sort_values("Vol", ascending=False)
                st.bar_chart(reg_data.set_index("regional"), color="#2FB53A")

    # --- SEÇÃO DE DESCRIÇÃO (COM DETECÇÃO DE COLUNA) ---
        st.markdown("---")
        st.subheader("📦 Finalizados por Tipo de Serviço")
        
        possiveis_cols = ['desc_limpa', 'descrição', 'descricao', 'tipo_servico']
        col_ativa = next((c for c in possiveis_cols if c in df_foco.columns), None)

        if col_ativa:
            df_grafico = df_foco.groupby(col_ativa).size().reset_index(name="Qtd").sort_values("Qtd", ascending=False)
            st.bar_chart(df_grafico.set_index(col_ativa),
            color="#2FB53A")
        else:
            st.info("Coluna de descrição não encontrada nesta base.")


    # --- SEÇÃO 7: ANÁLISE POR OLT ---
    st.markdown("---")
    st.header("📡 Volume de Finalizados por OLT")

    # Forçamos a limpeza dos nomes das colunas para evitar espaços invisíveis
    df_foco.columns = df_foco.columns.str.strip()

    # Verifica se a coluna OLT existe (mesmo que esteja 'olt' minúsculo)
    col_olt = None
    for c in df_foco.columns:
        if c.upper() == 'OLT':
            col_olt = c
            break

    if not df_foco.empty:
        if col_olt:
            # Agrupamento por OLT
            df_olt = df_foco.groupby(col_olt).size().reset_index(name="Quantidade")
            df_olt = df_olt.sort_values("Quantidade", ascending=False)
            
            # Cálculo de Participação
            total_olt = df_olt["Quantidade"].sum()
            df_olt["Participação %"] = (df_olt["Quantidade"] / total_olt * 100).round(1)

            col_t_olt, col_g_olt = st.columns([1, 2])
            
            with col_t_olt:
                st.write(f"**Ranking de OLTs**")
                st.dataframe(
                    df_olt, 
                    column_config={
                        "Participação %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
                        "Quantidade": st.column_config.NumberColumn(format="%d 📡")
                    },
                    hide_index=True, 
                    use_container_width=True
                )

            with col_g_olt:
                st.write(f"**Top 15 OLTs por Volume**")
                chart_olt = alt.Chart(df_olt.head(15)).mark_bar(color="#2FB53A").encode(
                    x=alt.X("Quantidade:Q", title="Volume de Finalizados"),
                    y=alt.Y(f"{col_olt}:N", sort="-x", title=None),
                    tooltip=[col_olt, "Quantidade", "Participação %"]
                ).properties(height=400)
                
                st.altair_chart(chart_olt, use_container_width=True)
        else:
            # Caso não ache, mostramos as colunas reais para você ver o nome exato
            st.warning(f"⚠️ Coluna 'OLT' não encontrada. Colunas na base: {list(df_foco.columns)}")


   # --- SEÇÃO: ANÁLISE POR HORA ---
    st.markdown("---")
    st.header("⏰ Distribuição de Finalizados por Hora")

    if not df_foco.empty:
        try:
            df_hora = df_foco.copy()
            
            # 1. Tentar encontrar a coluna com maior riqueza de detalhes (com hora)
            colunas_busca = ['data_encerramento_prot', 'data_abertura_prot', 'data_original', 'data']
            col_data_hora = next((c for c in colunas_busca if c in df_hora.columns), None)

            if col_data_hora:
                # IMPORTANTE: Converter garantindo que o Pandas tente ler a hora
                df_hora['timestamp_formatado'] = pd.to_datetime(df_hora[col_data_hora], errors='coerce')
                
                # Verificação se os dados possuem apenas data (sem hora)
                if df_hora['timestamp_formatado'].dt.hour.nunique() <= 1:
                    st.info("ℹ️ A base atual parece conter apenas datas. A análise por hora requer o campo de horário completo.")

                # --- TRAVA DE SEGURANÇA: REMOVE HORAS FUTURAS SE FOR HOJE ---
                agora = datetime.now()
                if data_inicio == agora.date():
                    hora_atual = agora.hour
                    df_hora = df_hora[df_hora['timestamp_formatado'].dt.hour <= hora_atual]
                
                # 2. Extrai a HORA numérica
                df_hora['hora_num'] = df_hora['timestamp_formatado'].dt.hour
                
                # 3. Agrupamento e Garantia das 24h
                df_vol_hora = df_hora.dropna(subset=['hora_num']).groupby('hora_num').size().reset_index(name='Volume')
                df_completo = pd.DataFrame({'hora_num': range(24)})
                df_vol_hora = df_completo.merge(df_vol_hora, on='hora_num', how='left').fillna(0)
                
                # 4. Formatação para exibição
                df_vol_hora['Hora_Label'] = df_vol_hora['hora_num'].apply(lambda x: f"{int(x):02d}h")

                # --- Visualização ---
                col_chart, col_data = st.columns([3, 1])
                
                with col_chart:
                    max_vol = float(df_vol_hora['Volume'].max())
                    
                    bar_hora = alt.Chart(df_vol_hora).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                        x=alt.X('Hora_Label:N', title="Hora do Dia", axis=alt.Axis(labelAngle=0), sort=None),
                        y=alt.Y('Volume:Q', title="Volume de Finalizados"),
                        color=alt.condition(
                            (alt.datum.Volume == max_vol) & (alt.datum.Volume > 0),
                            alt.value('#F63366'), # Rosa para o Pico
                            alt.value('#2FB53A')  # Azul padrão
                        ),
                        tooltip=[
                            alt.Tooltip('Hora_Label', title='Hora'), 
                            alt.Tooltip('Volume', title='Qtd Finalizada')
                        ]
                    ).properties(height=350)
                    
                    st.altair_chart(bar_hora, use_container_width=True)

                with col_data:
                    st.write("**Top Horários**")
                    df_top = df_vol_hora[['Hora_Label', 'Volume']].sort_values('Volume', ascending=False).head(5)
                    st.dataframe(df_top, hide_index=True, use_container_width=True)
            else:
                st.warning("⚠️ Coluna de data/hora não encontrada para análise.")

        except Exception as e:
            st.error(f"Erro ao processar horas: {e}")

with tab_cancelado:
    st.title("❌ Dashboard – Projeção de Cancelados")
    st.caption(f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # =========================================================
    # 1. NORMALIZAÇÃO PREVENTIVA (Garante que o filtro funcione)
    # =========================================================
    if not df_cancelados_base.empty:
        # Forçamos as colunas de filtro para String e tira espaços
        df_cancelados_base['regional'] = df_cancelados_base['regional'].astype(str).str.strip()
        df_cancelados_base['desc_limpa'] = df_cancelados_base['desc_limpa'].astype(str).str.strip()
        
        # Garante que a coluna de data seja datetime para o filtro de data_input
        df_cancelados_base['data'] = pd.to_datetime(df_cancelados_base['data'], errors='coerce')

    # ==============================
    # 2. PROCESSAMENTO COM FILTRO GLOBAL
    # ==============================
    df_filtrado = aplicar_filtros_globais(df_cancelados_base)

    if df_filtrado.empty:
        st.error("⚠️ Nenhum dado encontrado para os filtros selecionados.")
        st.info("💡 Verifique se o intervalo de datas no topo abrange o ano de 2026 e se as cidades selecionadas existem na base.")
        st.stop()

    data_inicio, data_fim = intervalo

    # ==============================
    # 3. LÓGICA DE DADOS (FOCO X HISTÓRICO)
    # ==============================
    df_foco = df_filtrado[(df_filtrado["data"].dt.date >= data_inicio) & 
                        (df_filtrado["data"].dt.date <= data_fim)].copy()

    df_hist_filtrado = aplicar_filtros_globais(df_cancelados_base, ignorar_data=True)
    df_hist_filtrado['data_only'] = df_hist_filtrado['data'].dt.date
    
    data_limite_hist = data_inicio - pd.Timedelta(days=28)
    df_hist_recente = df_hist_filtrado[
        (df_hist_filtrado['data_only'] < data_inicio) & 
        (df_hist_filtrado['data_only'] >= data_limite_hist)
    ].copy()

    # Média por Dia da Semana
    df_hist_recente['dia_semana_num'] = df_hist_recente['data'].dt.dayofweek
    vol_diario_hist = df_hist_recente.groupby(['data_only', 'dia_semana_num']).size().reset_index(name='vol')
    media_por_dia_semana = vol_diario_hist.groupby('dia_semana_num')['vol'].mean().to_dict()
    media_diaria_hist = vol_diario_hist['vol'].mean() if not vol_diario_hist.empty else 0

    # Projeção
    datas_periodo = pd.date_range(start=data_inicio, end=data_fim)
    projecao_lista = [int(round(media_por_dia_semana.get(d.dayofweek, media_diaria_hist))) for d in datas_periodo]
    df_proj_dia = pd.DataFrame({'data': [d.date() for d in datas_periodo], 'Projeção': projecao_lista})

    # Métricas
    realizado_total = len(df_foco)
    total_projetado = sum(projecao_lista)
    aderencia = (realizado_total / total_projetado * 100) if total_projetado > 0 else 0
    gap = realizado_total - total_projetado

    # --- SEÇÃO 1: METRICAS ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Cancelados ({len(df_proj_dia)}d)", f"{realizado_total:,}")
    c2.metric("Projeção", f"{total_projetado:,}")
    c3.metric("Aderência (C/P)", f"{aderencia:.1f}%", delta=f"{aderencia-100:.1f}%")
    c4.metric("Gap", f"{gap:,}", delta=gap, delta_color="inverse")

    # --- SEÇÃO 2: EVOLUÇÃO ---
    st.markdown("---")
    st.subheader("📈 Tendência de Cancelamento (Realizado x Projeção)")

    df_realizado_dia = df_foco.copy()
    df_realizado_dia['data_temp'] = df_realizado_dia['data'].dt.date
    df_realizado_dia = df_realizado_dia.groupby("data_temp").size().reset_index(name="Realizado")
    df_realizado_dia.columns = ['data', 'Realizado']
    
    df_evolucao = pd.merge(df_proj_dia, df_realizado_dia, on="data", how="left").fillna(0)
    df_evolucao['data_str'] = df_evolucao['data'].apply(lambda x: x.strftime('%d/%m'))

    base = alt.Chart(df_evolucao).encode(x=alt.X('data_str:N', title=None, sort=None))
    barras = base.mark_bar(color="#FF4B4B", opacity=0.7).encode(
        y=alt.Y('Realizado:Q', title="Volume"),
        tooltip=['data_str', 'Realizado']
    )
    linha = base.mark_line(color="#000000", strokeWidth=3).encode(y='Projeção:Q') 
    st.altair_chart((barras + linha).properties(height=350), use_container_width=True)

    # --- SEÇÃO 3: ANÁLISE DE MOTIVOS (CHURN DEEP DIVE) ---
    st.markdown("---")
    st.header("🔍 Detalhamento de Churn")
    
    col_set, col_mot = st.columns(2)

    with col_set:
        st.subheader("🏢 Cancelamento por Setor")
        # Tentamos as duas variações de nome de coluna
        col_setor = 'setor_canc' if 'setor_canc' in df_foco.columns else 'setor que cancelou'
        if col_setor in df_foco.columns:
            df_setor = df_foco.groupby(col_setor).size().reset_index(name='Qtd').sort_values('Qtd', ascending=False)
            chart_setor = alt.Chart(df_setor).mark_bar(color="#000000", cornerRadiusTopRight=8, cornerRadiusBottomRight=8).encode(
                x=alt.X('Qtd:Q', title="Volume"),
                y=alt.Y(f'{col_setor}:N', sort='-x', title=None),
                tooltip=[col_setor, 'Qtd']
            ).properties(height=300)
            st.altair_chart(chart_setor, use_container_width=True)

    with col_mot:
        st.subheader("🚩 Motivo Real do Churn")
        col_motivo_real = 'motivo_canc_real' if 'motivo_canc_real' in df_foco.columns else 'motivo do cancelamento'
        if col_motivo_real in df_foco.columns:
            df_mot_real = df_foco.groupby(col_motivo_real).size().reset_index(name='Qtd').sort_values('Qtd', ascending=False)
            chart_mot_real = alt.Chart(df_mot_real).mark_bar(color="#FF4B4B", cornerRadiusTopRight=8, cornerRadiusBottomRight=8).encode(
                x=alt.X('Qtd:Q', title="Volume"),
                y=alt.Y(f'{col_motivo_real}:N', sort='-x', title=None),
                tooltip=[col_motivo_real, 'Qtd']
            ).properties(height=300)
            st.altair_chart(chart_mot_real, use_container_width=True)

    # --- SEÇÃO 4: CALENDÁRIO E CIDADES ---
    st.markdown("---")
    c_cal, c_cid = st.columns([1.5, 1])

    with c_cal:
        st.subheader("🗓️ Intensidade Diária")
        if not df_foco.empty:
            df_cal = df_foco.copy()
            df_cal['Data'] = df_cal['data'].dt.date
            df_cal['Dia'] = df_cal['data'].dt.day
            df_cal['Semana_Eixo'] = df_cal['data'].dt.strftime('%Y-%U')
            df_cal['Dia_Semana'] = df_cal['data'].dt.dayofweek.map({0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'})
            df_cal_diario = df_cal.groupby(['Data', 'Dia', 'Semana_Eixo', 'Dia_Semana']).size().reset_index(name='Volume')
            
            cal_chart = alt.Chart(df_cal_diario).encode(
                x=alt.X('Dia_Semana:N', sort=['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'], title=None, axis=alt.Axis(orient='top')),
                y=alt.Y('Semana_Eixo:O', axis=None)
            ).mark_rect(stroke='white', cornerRadius=4).encode(
                color=alt.Color('Volume:Q', scale=alt.Scale(scheme='reds'), legend=None),
                tooltip=['Data', 'Volume']
            )
            st.altair_chart(cal_chart.properties(height=200), use_container_width=True)

    with c_cid:
        st.subheader("🎯 Cidades Críticas")
        df_cidades = df_foco.groupby("cidade").size().reset_index(name="Realizado").sort_values("Realizado", ascending=False).head(10)
        st.dataframe(df_cidades, hide_index=True, use_container_width=True, 
                     column_config={"Realizado": st.column_config.NumberColumn(format="%d 🚨")})

    # --- SEÇÃO 5: DISTRIBUIÇÃO POR HORA ---
    st.markdown("---")
    st.subheader("⏰ Distribuição por Hora")
    try:
        df_hora = df_foco.copy()
        df_hora['ts'] = pd.to_datetime(df_hora['data'], errors='coerce')
        agora = datetime.now()
        if data_inicio == agora.date():
            df_hora = df_hora[df_hora['ts'].dt.hour <= agora.hour]

        df_vol_h = df_hora['ts'].dt.hour.value_counts().reset_index()
        df_vol_h.columns = ['hora', 'Volume']
        df_vol_h = pd.DataFrame({'hora': range(24)}).merge(df_vol_h, on='hora', how='left').fillna(0)
        df_vol_h['Label'] = df_vol_h['hora'].apply(lambda x: f"{int(x):02d}h")
        
        chart_h = alt.Chart(df_vol_h).mark_bar().encode(
            x=alt.X('Label:N', sort=None, title="Hora"),
            y=alt.Y('Volume:Q'),
            color=alt.condition(alt.datum.Volume == float(df_vol_h['Volume'].max()) and float(df_vol_h['Volume'].max()) > 0, alt.value("#000000"), alt.value("#FF4B4B")),
            tooltip=['Label', 'Volume']
        ).properties(height=250)
        st.altair_chart(chart_h, use_container_width=True)
    except:
        st.info("Análise de horas indisponível para este conjunto de dados.")

with tab_rota_inicial:
    st.title("🚛 Projeção de Rota Inicial (D+1)")
    
    # 1. DEFINIÇÃO DAS DATAS DE REFERÊNCIA
    # Se o filtro é dia 18, o dia_foco é 18 e o dia_anterior (sobras) é 17
    data_inicio_f, data_fim_f = intervalo
    dia_foco = data_fim_f
    dia_anterior = data_inicio_f - timedelta(days=1)
    
    st.caption(f"Análise baseada em Sobras de {dia_anterior.strftime('%d/%m')} e Projeções de {dia_foco.strftime('%d/%m')}")

    # 2. PROCESSAMENTO DAS SOBRAS (D-1)
    # Ignoramos a data no filtro global para buscar o dia anterior (17), 
    # mas mantemos os filtros de Cidade e Serviço selecionados.
    df_sobras_raw = aplicar_filtros_globais(df_sobras_base, ignorar_data=True)
    
    if not df_sobras_raw.empty:
        # Garantimos a conversão da created_at para filtrar o dia anterior
        df_sobras_raw['created_at_dt'] = pd.to_datetime(df_sobras_raw['created_at'], errors='coerce', dayfirst=True).dt.date
        df_sobras_foco = df_sobras_raw[df_sobras_raw['created_at_dt'] == dia_anterior]
        total_sobras = len(df_sobras_foco)
    else:
        total_sobras = 0

    # 3. RECUPERAÇÃO DAS PROJEÇÕES UNITÁRIAS (ÚLTIMO DIA)
    # Pegamos apenas o último valor das listas calculadas no processamento central
    proj_ent = lista_ent[-1] if 'lista_ent' in locals() and lista_ent else 0
    proj_fin = lista_fin[-1] if 'lista_fin' in locals() and lista_fin else 0
    proj_can = lista_can[-1] if 'lista_can' in locals() and lista_can else 0
    
    # =========================================================
    # 4. CÁLCULO DA MÉTRICA OPERACIONAL (FÓRMULA)
    # =========================================================
    # Carga: Novos de Hoje + Pendentes de Ontem
    entradas_totais = proj_ent + total_sobras
    # Vazão: O que esperamos limpar hoje
    saidas_totais = proj_fin + proj_can
    
    # Rota Inicial de Amanhã
    rota_inicial_amanha = entradas_totais - saidas_totais

    # --- EXIBIÇÃO ---
    c1, c2, c3 = st.columns([1, 1, 2])
    
    with c1:
        st.metric("Carga Hoje (Proj. + Sobras)", f"{entradas_totais:,}", help=f"Proj. Entrantes ({proj_ent}) + Sobras D-1 ({total_sobras})")
    with c2:
        st.metric("Vazão Hoje (Fin. + Can.)", f"{saidas_totais:,}", help=f"Proj. Finalizados ({proj_fin}) + Proj. Cancelados ({proj_can})")
    
    # Destaque visual do resultado final
    cor_box = "rgba(59, 130, 246, 0.1)" if rota_inicial_amanha >= 0 else "rgba(34, 197, 94, 0.1)"
    borda_box = "#3b82f6" if rota_inicial_amanha >= 0 else "#22c55e"
    
    st.markdown(f"""
        <div style="background: {cor_box}; padding: 30px; border-radius: 20px; border: 2px solid {borda_box}; text-align: center;">
            <h3 style="margin:0; color: #1e3a8a;">🚛 Rota Inicial Projetada (Amanhã)</h3>
            <h1 style="margin:0; font-size: 60px; color: #1e40af;">{int(rota_inicial_amanha):,}</h1>
            <p style="color: #64748b;">Saldo estimado para abertura da rota no dia seguinte</p>
        </div>
    """, unsafe_allow_html=True)

    # --- GRÁFICOS DE APOIO ---
    st.markdown("---")
    if total_sobras > 0:
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader(f"⚠️ Motivos das {total_sobras} Sobras")
            df_m = df_sobras_foco.groupby('motivo_pendencia').size().reset_index(name='qtd').sort_values('qtd', ascending=False)
            st.altair_chart(alt.Chart(df_m).mark_bar(color="#3b82f6", cornerRadiusTopRight=10, cornerRadiusBottomRight=10).encode(
                x='qtd:Q', y=alt.Y('motivo_pendencia:N', sort='-x', title=None), tooltip=['qtd']
            ).properties(height=300), use_container_width=True)
        
        with col_r:
            st.subheader("📍 Sobras por Cidade (D-1)")
            df_c = df_sobras_foco.groupby('cidade').size().reset_index(name='qtd').sort_values('qtd', ascending=False)
            st.dataframe(df_c, hide_index=True, use_container_width=True, column_config={"qtd": "Volume 📦"})
    else:
        st.info(f"Nenhuma sobra encontrada criada em {dia_anterior.strftime('%d/%m/%Y')}.")


with tab_aging:
    st.title("⏳ Saúde da Fila – SLA & Aging")
    st.caption(f"Análise de tempo de vida dos chamados pendentes | {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # 1. PROCESSAMENTO DOS DADOS
    # Usamos a base de sobras para analisar o que ainda não foi limpo
    df_aging_foco = aplicar_filtros_globais(df_sobras_base, ignorar_data=True)

    if df_aging_foco.empty:
        st.warning("⚠️ Nenhuma sobra encontrada para análise de Aging.")
        st.stop()

    # Garantimos que as colunas existam ou calculamos na hora
    if 'aging_dias' not in df_aging_foco.columns:
        df_aging_foco['data_dt'] = pd.to_datetime(df_aging_foco['data'], errors='coerce')
        df_aging_foco['aging_dias'] = (datetime.now() - df_aging_foco['data_dt']).dt.days

    # 2. DEFINIÇÃO DOS BUCKETS (FAIXAS DE IDADE)
    def classificar_sla(dias):
        if dias <= 1: return "🟢 0-24h (Fresco)"
        if dias <= 2: return "🟡 24-48h (Atenção)"
        if dias <= 3: return "🟠 48-72h (Crítico)"
        return "🔴 +72h (Vencido)"

    df_aging_foco['faixa_sla'] = df_aging_foco['aging_dias'].apply(classificar_sla)

    # 3. MÉTRICAS DE IMPACTO
    avg_aging = df_aging_foco['aging_dias'].mean()
    casos_vencidos = len(df_aging_foco[df_aging_foco['aging_dias'] > 2])
    percent_vencido = (casos_vencidos / len(df_aging_foco)) * 100

    m1, m2, m3 = st.columns(3)
    m1.metric("Aging Médio", f"{avg_aging:.1f} Dias", help="Tempo médio que um chamado está parado na rota.")
    m2.metric("Fora do SLA (+48h)", f"{casos_vencidos} Casos", delta="Atenção", delta_color="inverse")
    m3.metric("% Da Fila Vencida", f"{percent_vencido:.1f}%")

    # 4. GRÁFICO DE DISTRIBUIÇÃO (BUCKETS)
    st.markdown("---")
    st.subheader("📊 Distribuição por Faixa de Envelhecimento")
    
    df_plot = df_aging_foco.groupby('faixa_sla').size().reset_index(name='qtd')
    ordem_sla = ["🟢 0-24h (Fresco)", "🟡 24-48h (Atenção)", "🟠 48-72h (Crítico)", "🔴 +72h (Vencido)"]
    
    chart_sla = alt.Chart(df_plot).mark_bar(cornerRadiusTopRight=10, cornerRadiusTopLeft=10).encode(
        x=alt.X('faixa_sla:N', sort=ordem_sla, title=None),
        y=alt.Y('qtd:Q', title="Volume de Ordens"),
        color=alt.Color('faixa_sla:N', scale=alt.Scale(
            domain=ordem_sla,
            range=['#22c55e', '#eab308', '#f97316', '#ef4444'] # Verde, Amarelo, Laranja, Vermelho
        ), legend=None),
        tooltip=['faixa_sla', 'qtd']
    ).properties(height=350)

    st.altair_chart(chart_sla, use_container_width=True)

    # 5. LISTA DE PRIORIDADE (O QUE ATENDER AGORA)
    st.markdown("---")
    col_t1, col_t2 = st.columns([2, 1])

    with col_t1:
        st.subheader("🚩 Top 10 Casos Críticos (Mais Antigos)")
        # Mostra os casos que precisam de ação imediata
        df_top_aging = df_aging_foco.sort_values('aging_dias', ascending=False).head(10)
        st.dataframe(
            df_top_aging[['protocolo', 'cidade', 'desc_limpa', 'aging_dias', 'motivo_pendencia']],
            hide_index=True,
            use_container_width=True,
            column_config={
                "aging_dias": st.column_config.NumberColumn("Dias ⏳", format="%.1f"),
                "protocolo": "Protocolo ID"
            }
        )

    with col_t2:
        st.subheader("📍 Aging Médio por Cidade")
        df_cid_age = df_aging_foco.groupby('cidade')['aging_dias'].mean().reset_index().sort_values('aging_dias', ascending=False)
        st.dataframe(
            df_cid_age,
            hide_index=True,
            use_container_width=True,
            column_config={
                "aging_dias": st.column_config.NumberColumn("Média Dias", format="%.1f 🗓️")
            }
        )

with tab_eficiencia:
    st.title("⚡ Eficiência & Produtividade Técnica")
    st.caption("Análise de performance individual e ocupação da força de trabalho.")

    # 1. PREPARAÇÃO DOS DADOS (JOIN DE PRODUTIVIDADE)
    # Pegamos os finalizados e as sobras para ver o "Total que foi pra rua"
    df_fin_ef = aplicar_filtros_globais(df_finalizados_base)
    df_sob_ef = aplicar_filtros_globais(df_sobras_base, ignorar_data=True) # Sobras de ontem

    # Agrupando por técnico
    prod_fin = df_fin_ef.groupby('nome do técnico').size().reset_index(name='Finalizados')
    prod_sob = df_sob_ef.groupby('nome do técnico').size().reset_index(name='Pendentes')

    # Merge para ter a visão completa por técnico
    df_perf = pd.merge(prod_fin, prod_sob, on='nome do técnico', how='outer').fillna(0)
    df_perf['Total'] = df_perf['Finalizados'] + df_perf['Pendentes']
    
    # Cálculo da Eficiência Individual: (Finalizados / Total de Visitas)
    df_perf['Eficiência (%)'] = (df_perf['Finalizados'] / df_perf['Total'] * 100).round(1)

    # 2. MÉTRICAS GLOBAIS DE CAPACIDADE
    num_tecnicos = len(df_perf)
    media_visitas = df_perf['Total'].mean()
    # Premissa Sênior: Se cada técnico fizesse 6 serviços/dia (meta padrão)
    meta_servicos = 6 
    capacidade_total = num_tecnicos * meta_servicos
    ocupacao_real = (df_perf['Total'].sum() / capacidade_total * 100) if capacidade_total > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Técnicos Ativos", f"{num_tecnicos}")
    m2.metric("Ocupação da Rede", f"{ocupacao_real:.1f}%", help="Total de visitas vs Capacidade teórica (6/dia)")
    m3.metric("Taxa de Sucesso (First-Time)", f"{(df_perf['Finalizados'].sum() / df_perf['Total'].sum() * 100):.1f}%")

    # 3. GRÁFICO DE PERFORMANCE (RANKING)
    st.markdown("---")
    st.subheader("🏆 Ranking de Produtividade vs. Pendência")
    
    # Criando gráfico de barras empilhadas
    df_melted = df_perf.melt(id_vars='nome do técnico', value_vars=['Finalizados', 'Pendentes'], 
                            var_name='Status', value_name='Quantidade')
    
    chart_perf = alt.Chart(df_melted).mark_bar().encode(
        y=alt.Y('nome do técnico:N', sort='-x', title=None),
        x=alt.X('Quantidade:Q', title="Volume de Atendimentos"),
        color=alt.Color('Status:N', scale=alt.Scale(domain=['Finalizados', 'Pendentes'], range=['#22c55e', '#ef4444'])),
        tooltip=['nome do técnico', 'Status', 'Quantidade']
    ).properties(height=400)
    
    st.altair_chart(chart_perf, use_container_width=True)

    # 4. ALERTA DE CAPACIDADE (INSIGHT SÊNIOR)
    st.markdown("---")
    if ocupacao_real > 90:
        st.error(f"🚨 **ALERTA DE SOBRECARGA:** A ocupação está em {ocupacao_real:.1f}%. A equipe está operando no limite. Risco alto de aumento na Rota Inicial.")
    elif ocupacao_real < 60:
        st.warning(f"⚠️ **BAIXA OCUPAÇÃO:** A equipe está com {ocupacao_real:.1f}% de carga. Possível ociosidade ou falta de entrantes.")
    else:
        st.success(f"✅ **DASHBOARD SAUDÁVEL:** Ocupação equilibrada em {ocupacao_real:.1f}%.")

    # 5. TABELA DETALHADA
    st.subheader("📋 Detalhamento por Colaborador")
    st.dataframe(
        df_perf.sort_values('Eficiência (%)', ascending=False),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Eficiência (%)": st.column_config.ProgressColumn("Eficiência (%)", format="%d%%", min_value=0, max_value=100),
            "Total": "Carga Total",
            "nome do técnico": "Técnico"
        }
    )