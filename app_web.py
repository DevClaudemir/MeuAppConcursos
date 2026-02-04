import streamlit as st
import sqlite3
import pandas as pd
import random
import re
import time
import hashlib
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
try:
    from config import ADMIN_DONO, VALOR_ASSINATURA
except ImportError:
    ADMIN_DONO = "admin"  # Fallback
    VALOR_ASSINATURA = 5.00

# ==============================
# 1. CONFIGURAÇÕES E ESTILO
# ==============================
st.set_page_config(page_title="Plataforma de Questões | Concursos", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* Tema azul e branco - bom contraste */
    .stApp { background: #f0f4f8; }
    [data-testid="stSidebar"] { background: #1e3a5f; }
    [data-testid="stSidebar"] .stMarkdown { color: #e8eef4 !important; }
    [data-testid="stSidebar"] label { color: #e8eef4 !important; }
    h1, h2, h3 { color: #1e3a5f !important; font-weight: 600 !important; }
    p, span, div[data-testid="stMarkdown"] { color: #1a1a2e !important; }
    .breadcrumb { color: #2563eb; font-size: 0.9rem; margin-bottom: 1rem; }
    .teoria-box {
        background: #ffffff;
        border-left: 4px solid #2563eb;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 1rem 0;
        color: #1a1a2e;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .teoria-box h4 { color: #1e3a5f !important; margin-top: 0 !important; }
    div[data-testid="stExpander"] { background: #fff; border: 1px solid #cbd5e1; border-radius: 10px; }
    .stButton > button { border-radius: 8px; font-weight: 500; }
    .stButton > button[kind="primary"] { background: #2563eb !important; color: #fff !important; border: none !important; }
    [data-testid="stMetricValue"] { color: #1e3a5f !important; }
    [data-testid="stMetricLabel"] { color: #475569 !important; }
</style>
""", unsafe_allow_html=True)

# ==============================
# 2. BANCO DE DADOS
# ==============================
def acessar_banco():
    return sqlite3.connect("banco_questoes.db", check_same_thread=False)

def criar_tabelas():
    conn = acessar_banco()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL UNIQUE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)
    conn.commit()
    conn.close()

criar_tabelas()

def existe_algum_admin():
    """Verifica se já existe pelo menos um admin"""
    conn = acessar_banco()
    try:
        r = conn.execute("SELECT 1 FROM admins LIMIT 1").fetchone()
        return r is not None
    finally:
        conn.close()

# ==============================
# 3. SEGURANÇA E ADMIN
# ==============================
def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def eh_admin(usuario_id, nome_usuario=None):
    """Verifica se o usuário é admin (dono do site)"""
    if nome_usuario and nome_usuario.lower() == ADMIN_DONO.lower():
        # Garante que o dono está na tabela admins
        conn = acessar_banco()
        try:
            admin = conn.execute("SELECT id FROM admins WHERE usuario_id = ?", (usuario_id,)).fetchone()
            if not admin:
                conn.execute("INSERT OR IGNORE INTO admins (usuario_id) VALUES (?)", (usuario_id,))
                conn.commit()
            return True
        finally:
            conn.close()
    conn = acessar_banco()
    try:
        admin = conn.execute("SELECT id FROM admins WHERE usuario_id = ?", (usuario_id,)).fetchone()
        return admin is not None
    finally:
        conn.close()

def obter_usuario_id(nome):
    """Obtém ID do usuário pelo nome"""
    conn = acessar_banco()
    try:
        user = conn.execute("SELECT id FROM usuarios WHERE nome = ?", (nome,)).fetchone()
        return user[0] if user else None
    finally:
        conn.close()

def verificar_assinatura_ativa(usuario_id):
    """Verifica se o usuário tem assinatura ativa"""
    conn = acessar_banco()
    try:
        hoje = datetime.now().date()
        assinatura = conn.execute("""
            SELECT data_fim, status FROM assinaturas 
            WHERE usuario_id = ? AND status = 'ativa' AND data_fim >= ?
            ORDER BY data_fim DESC LIMIT 1
        """, (usuario_id, hoje)).fetchone()
        if assinatura:
            return True, assinatura[0]  # Retorna True e data_fim
        return False, None
    finally:
        conn.close()

def criar_assinatura(usuario_id, meses=1, metodo="manual"):
    """Cria uma nova assinatura"""
    conn = acessar_banco()
    try:
        hoje = datetime.now().date()
        data_fim = hoje + timedelta(days=30 * meses)
        conn.execute("""
            INSERT INTO assinaturas (usuario_id, data_inicio, data_fim, valor_pago, status, metodo_pagamento)
            VALUES (?, ?, ?, ?, 'ativa', ?)
        """, (usuario_id, hoje, data_fim, VALOR_ASSINATURA * meses, metodo))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao criar assinatura: {e}")
        return False
    finally:
        conn.close()

def obter_id_questao_atual():
    """Obtém o ID da questão atual no simulado"""
    # Como carregamos questões sem ID, precisamos buscar pelo hash ou outros campos
    # Por enquanto, retornamos None e usamos índice
    return None

def adicionar_comentario(questao_id, usuario_id, comentario):
    """Adiciona um comentário a uma questão"""
    conn = acessar_banco()
    try:
        conn.execute("""
            INSERT INTO comentarios_questoes (questao_id, usuario_id, comentario)
            VALUES (?, ?, ?)
        """, (questao_id, usuario_id, comentario))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao adicionar comentário: {e}")
        return False
    finally:
        conn.close()

def listar_comentarios(questao_id):
    """Lista comentários de uma questão"""
    conn = acessar_banco()
    try:
        df = pd.read_sql("""
            SELECT c.id, u.nome, c.comentario, c.data_criacao
            FROM comentarios_questoes c
            JOIN usuarios u ON c.usuario_id = u.id
            WHERE c.questao_id = ?
            ORDER BY c.data_criacao DESC
        """, conn, params=(questao_id,))
        return df
    finally:
        conn.close()

# ==============================
# 4. DADOS POR CONCURSO / CARGO / MATÉRIA
# ==============================
def listar_concursos():
    conn = acessar_banco()
    try:
        df = pd.read_sql("SELECT id, nome FROM concursos ORDER BY nome", conn)
        return [(int(r.id), r.nome) for _, r in df.iterrows()]
    except Exception:
        return []
    finally:
        conn.close()

def listar_cargos(concurso_id):
    if concurso_id is None:
        return [(None, "Geral")]
    conn = acessar_banco()
    try:
        df = pd.read_sql(
            "SELECT c.id, c.nome FROM cargos c WHERE c.concurso_id = ? ORDER BY c.nome",
            conn, params=(concurso_id,)
        )
        return [(int(r.id), r.nome) for _, r in df.iterrows()]
    finally:
        conn.close()

def listar_materias(cargo_id):
    conn = acessar_banco()
    try:
        if cargo_id is None:
            df = pd.read_sql(
                "SELECT DISTINCT materia FROM questoes WHERE cargo_id IS NULL ORDER BY materia",
                conn
            )
        else:
            df = pd.read_sql(
                "SELECT DISTINCT materia FROM questoes WHERE cargo_id = ? ORDER BY materia",
                conn, params=(cargo_id,)
            )
        return df["materia"].tolist()
    finally:
        conn.close()

def carregar_questoes(cargo_id, config):
    """config = {materia: qtd}. Retorna lista de tuplas (enunciado, op_a..op_d, correta, materia, explicacao_teorica)."""
    todas = []
    conn = acessar_banco()
    for materia, qtd in config.items():
        if cargo_id is None:
            rows = conn.execute(
                "SELECT id FROM questoes WHERE cargo_id IS NULL AND materia = ?",
                (materia,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id FROM questoes WHERE cargo_id = ? AND materia = ?",
                (cargo_id, materia)
            ).fetchall()
        if not rows:
            continue
        ids = [r[0] for r in rows]
        escolhidos = random.sample(ids, min(qtd, len(ids)))
        for qid in escolhidos:
            q = conn.execute("""
                SELECT id, enunciado, op_a, op_b, op_c, op_d, correta, materia,
                       COALESCE(explicacao_teorica, '') AS explicacao_teorica
                FROM questoes WHERE id = ?
            """, (qid,)).fetchone()
            if q:
                todas.append(q)  # Agora inclui ID como primeiro elemento
    conn.close()
    random.shuffle(todas)
    return todas

# ==============================
# 5. SESSION STATE
# ==============================
for k, v in {
    "usuario_logado": None,
    "historico_respostas": {},
    "indice_atual": 0,
    "simulado_ativo": False,
    "modo_revisao": False,
    "questoes": [],
    "resultado_final": None,
    "concurso_selecionado": None,
    "concurso_nome": "",
    "cargo_selecionado": None,
    "cargo_nome": "",
    "modo_admin": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==============================
# 6. SIDEBAR - LOGIN
# ==============================
with st.sidebar:
    st.markdown("### 🔐 Área do Aluno")
    st.markdown("---")

    if st.session_state.usuario_logado is None:
        aba_login, aba_cadastro = st.tabs(["Entrar", "Criar Conta"])
        with aba_login:
            u = st.text_input("Usuário", key="user")
            s = st.text_input("Senha", type="password", key="pass")
            if st.button("Fazer Login", use_container_width=True):
                conn = acessar_banco()
                user = conn.execute(
                    "SELECT nome FROM usuarios WHERE nome=? AND senha=?",
                    (u, hash_senha(s))
                ).fetchone()
                conn.close()
                if user:
                    st.session_state.usuario_logado = user[0]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos")
        with aba_cadastro:
            nu = st.text_input("Novo Usuário", key="new_user")
            ns = st.text_input("Nova Senha", type="password", key="new_pass")
            if st.button("Cadastrar", use_container_width=True):
                if nu and ns:
                    conn = acessar_banco()
                    try:
                        conn.execute(
                            "INSERT INTO usuarios (nome, senha) VALUES (?,?)",
                            (nu, hash_senha(ns))
                        )
                        conn.commit()
                        st.success("Conta criada! Faça login para continuar.")
                    except sqlite3.IntegrityError:
                        st.error("Usuário já existe.")
                    conn.close()
    else:
        st.success(f"**{st.session_state.usuario_logado}**")
        usuario_id = obter_usuario_id(st.session_state.usuario_logado)
        is_admin = usuario_id and eh_admin(usuario_id, st.session_state.usuario_logado)
        
        # Verifica assinatura
        tem_assinatura, data_fim = verificar_assinatura_ativa(usuario_id) if usuario_id else (False, None)
        
        st.markdown("---")
        if is_admin:
            st.markdown("### 👑 Administrador")
            if st.button("Acessar Painel Admin", use_container_width=True, type="primary"):
                st.session_state.modo_admin = True
                st.rerun()
        else:
            if tem_assinatura:
                st.success(f"✅ Assinatura ativa até {data_fim}")
            else:
                st.warning("⚠️ Assinatura necessária")
                st.markdown(f"**R$ {VALOR_ASSINATURA:.2f}/mês**")
                if st.button("💳 Assinar Agora", use_container_width=True, type="primary"):
                    st.session_state.modo_assinatura = True
                    st.rerun()
        
        if st.button("Sair", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ==============================
# 7. BLOQUEIO SEM LOGIN
# ==============================
if st.session_state.usuario_logado is None:
    st.markdown("# 🎯 Plataforma de Questões para Concursos")
    st.info("Faça login na barra lateral para acessar simulados por concurso, cargo e matéria.")
    st.stop()

# ==============================
# 7.3. VERIFICAÇÃO DE ASSINATURA
# ==============================
usuario_id = obter_usuario_id(st.session_state.usuario_logado) if st.session_state.usuario_logado else None
is_admin = usuario_id and eh_admin(usuario_id, st.session_state.usuario_logado)

# Bloqueia acesso se não for admin e não tiver assinatura
if usuario_id and not is_admin:
    tem_assinatura, data_fim = verificar_assinatura_ativa(usuario_id)
    if not tem_assinatura:
        # Mostra tela de assinatura
        if not st.session_state.get("modo_assinatura", False):
            st.markdown("# 💳 Assinatura Necessária")
            st.warning("Você precisa de uma assinatura ativa para acessar os simulados.")
            st.markdown(f"### Por apenas **R$ {VALOR_ASSINATURA:.2f}/mês**, você tem acesso a:")
            st.markdown("""
            - ✅ Simulados ilimitados por concurso e cargo
            - ✅ Conteúdo teórico completo nas questões
            - ✅ Comentários e explicações detalhadas
            - ✅ Histórico de desempenho
            - ✅ Questões atualizadas constantemente
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💳 Assinar Agora", use_container_width=True, type="primary"):
                    st.session_state.modo_assinatura = True
                    st.rerun()
            with col2:
                if st.button("← Voltar", use_container_width=True):
                    st.session_state.modo_assinatura = False
                    st.rerun()
            st.stop()
        else:
            # Tela de pagamento/assinatura
            st.markdown("# 💳 Assinar Plataforma")
            st.markdown(f"### Valor: **R$ {VALOR_ASSINATURA:.2f}/mês**")
            
            meses = st.selectbox("Quantos meses?", [1, 3, 6, 12], format_func=lambda x: f"{x} mês(es) - R$ {VALOR_ASSINATURA * x:.2f}")
            
            st.markdown("---")
            st.markdown("### Método de Pagamento")
            metodo = st.radio("Escolha:", ["PIX", "Cartão de Crédito", "Boleto", "Manual (Admin)"])
            
            if metodo == "Manual (Admin)":
                st.info("Entre em contato com o administrador para ativar sua assinatura manualmente.")
                if st.button("Solicitar Ativação Manual", use_container_width=True):
                    st.success("Solicitação enviada! O administrador será notificado.")
            else:
                st.info(f"💡 **Em desenvolvimento**: Integração com gateway de pagamento em breve.")
                st.info("Por enquanto, entre em contato com o administrador para ativar sua assinatura.")
            
            # Botão temporário para admin ativar manualmente (para testes)
            if st.button("🔓 Ativar Assinatura (TESTE - Admin)", use_container_width=True):
                if criar_assinatura(usuario_id, meses, metodo.lower()):
                    st.success(f"✅ Assinatura ativada por {meses} mês(es)! Válida até {datetime.now().date() + timedelta(days=30*meses)}")
                    st.session_state.modo_assinatura = False
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Erro ao ativar assinatura.")
            
            if st.button("← Cancelar", use_container_width=True):
                st.session_state.modo_assinatura = False
                st.rerun()
            st.stop()

# ==============================
# 7.5. PAINEL ADMIN
# ==============================

# Acesso ao painel: apenas admin (dono)
pode_acessar_admin = st.session_state.modo_admin and is_admin

if pode_acessar_admin:
    st.markdown("# 👑 Painel Administrativo")
    
    if st.button("← Voltar ao Menu Principal"):
        st.session_state.modo_admin = False
        st.rerun()
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Conteúdo Teórico", "🔍 Gerenciar Questões", "🕷️ Scraping", "💳 Assinaturas", "💬 Comentários"])
    
    with tab1:
        st.markdown("### Adicionar/Editar Conteúdo Teórico")
        conn = acessar_banco()
        
        # Buscar questões sem conteúdo teórico ou para editar
        df = pd.read_sql("""
            SELECT id, enunciado, materia, banca, orgao, 
                   COALESCE(explicacao_teorica, '') AS explicacao_teorica
            FROM questoes
            ORDER BY id DESC
            LIMIT 100
        """, conn)
        conn.close()
        
        if len(df) > 0:
            questao_id = st.selectbox(
                "Selecione a questão",
                options=df['id'].tolist(),
                format_func=lambda x: f"ID {x}: {df[df['id']==x]['enunciado'].iloc[0][:80]}..."
            )
            
            questao_selecionada = df[df['id'] == questao_id].iloc[0]
            
            st.markdown("**Enunciado:**")
            st.write(questao_selecionada['enunciado'])
            st.markdown(f"**Matéria:** {questao_selecionada['materia']} | **Banca:** {questao_selecionada.get('banca', 'N/A')} | **Órgão:** {questao_selecionada.get('orgao', 'N/A')}")
            
            explicacao_atual = questao_selecionada['explicacao_teorica'] if questao_selecionada['explicacao_teorica'] else ""
            nova_explicacao = st.text_area(
                "Conteúdo Teórico",
                value=explicacao_atual,
                height=200,
                help="Digite a explicação teórica sobre esta questão. Use **negrito** para destacar conceitos importantes."
            )
            
            if st.button("💾 Salvar Conteúdo Teórico", type="primary"):
                conn = acessar_banco()
                conn.execute(
                    "UPDATE questoes SET explicacao_teorica = ? WHERE id = ?",
                    (nova_explicacao, questao_id)
                )
                conn.commit()
                conn.close()
                st.success("Conteúdo teórico salvo com sucesso!")
                st.rerun()
        else:
            st.info("Nenhuma questão encontrada.")
    
    with tab2:
        st.markdown("### Gerenciar Questões")
        conn = acessar_banco()
        
        # Estatísticas
        stats = pd.read_sql("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN explicacao_teorica IS NULL OR explicacao_teorica = '' THEN 1 ELSE 0 END) as sem_teoria,
                SUM(CASE WHEN origem = 'scraping' THEN 1 ELSE 0 END) as do_scraping,
                SUM(CASE WHEN origem = 'manual' THEN 1 ELSE 0 END) as manuais
            FROM questoes
        """, conn)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", int(stats['total'].iloc[0]))
        col2.metric("Sem Teoria", int(stats['sem_teoria'].iloc[0]))
        col3.metric("Do Scraping", int(stats['do_scraping'].iloc[0]))
        col4.metric("Manuais", int(stats['manuais'].iloc[0]))
        
        # Buscar questões
        filtro = st.selectbox("Filtrar", ["Todas", "Sem conteúdo teórico", "Do scraping", "Manuais"])
        query = "SELECT id, enunciado, materia, banca, orgao, origem FROM questoes"
        if filtro == "Sem conteúdo teórico":
            query += " WHERE explicacao_teorica IS NULL OR explicacao_teorica = ''"
        elif filtro == "Do scraping":
            query += " WHERE origem = 'scraping'"
        elif filtro == "Manuais":
            query += " WHERE origem = 'manual'"
        query += " ORDER BY id DESC LIMIT 50"
        
        df_questoes = pd.read_sql(query, conn)
        conn.close()
        
        if len(df_questoes) > 0:
            st.dataframe(df_questoes, use_container_width=True)
            
            questao_para_deletar = st.selectbox("Deletar questão (ID)", df_questoes['id'].tolist())
            if st.button("🗑️ Deletar Questão", type="primary"):
                conn = acessar_banco()
                conn.execute("DELETE FROM questoes WHERE id = ?", (questao_para_deletar,))
                conn.commit()
                conn.close()
                st.success(f"Questão {questao_para_deletar} deletada!")
                st.rerun()
        else:
            st.info("Nenhuma questão encontrada com este filtro.")
    
    with tab3:
        st.markdown("### Sistema de Scraping")
        st.info("Use o script **scraper_questoes.py** para coletar questões automaticamente.")
        
        st.markdown("#### Processar URLs")
        urls_text = st.text_area(
            "Cole as URLs das questões (uma por linha)",
            height=150,
            help="Exemplo:\nhttps://exemplo.com/questao1\nhttps://exemplo.com/questao2"
        )
        
        # Listar todos os cargos
        todos_cargos = []
        for conc_id, conc_nome in listar_concursos():
            cargos = listar_cargos(conc_id)
            todos_cargos.extend([(c[0], f"{conc_nome} - {c[1]}") for c in cargos])
        todos_cargos.insert(0, (None, "Nenhum"))
        
        cargo_id_scraping = st.selectbox(
            "Cargo (opcional)",
            options=[c[0] for c in todos_cargos],
            format_func=lambda x: next(c[1] for c in todos_cargos if c[0] == x)
        )
        
        if st.button("🕷️ Executar Scraping", type="primary"):
            if urls_text.strip():
                from scraper_questoes import ScraperQuestoes
                urls = [u.strip() for u in urls_text.split('\n') if u.strip()]
                scraper = ScraperQuestoes()
                
                with st.spinner(f"Processando {len(urls)} URLs..."):
                    sucesso, erros, duplicatas = scraper.processar_urls(urls, cargo_id=cargo_id_scraping)
                
                st.success(f"✅ {sucesso} questões salvas | ❌ {erros} erros | 🔄 {duplicatas} duplicatas")
            else:
                st.error("Cole pelo menos uma URL")
        
        st.markdown("---")
        st.markdown("#### Limpeza de Duplicatas")
        if st.button("🧹 Remover Questões Manuais Duplicadas"):
            from scraper_questoes import ScraperQuestoes
            scraper = ScraperQuestoes()
            scraper.marcar_questoes_manuais_para_remocao()
            scraper.remover_duplicatas_manuais()
            st.success("Limpeza concluída!")
            st.rerun()
    
    with tab4:
        st.markdown("### 💳 Gerenciar Assinaturas")
        
        # Estatísticas
        conn = acessar_banco()
        stats = pd.read_sql("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'ativa' AND data_fim >= date('now') THEN 1 ELSE 0 END) as ativas,
                SUM(CASE WHEN status = 'ativa' AND data_fim < date('now') THEN 1 ELSE 0 END) as expiradas
            FROM assinaturas
        """, conn)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", int(stats['total'].iloc[0]))
        col2.metric("Ativas", int(stats['ativas'].iloc[0]))
        col3.metric("Expiradas", int(stats['expiradas'].iloc[0]))
        
        st.markdown("---")
        st.markdown("#### Ativar Assinatura Manualmente")
        usuarios_df = pd.read_sql("SELECT id, nome FROM usuarios", conn)
        usuario_assinatura = st.selectbox("Usuário", usuarios_df['nome'].tolist())
        meses_assinatura = st.number_input("Meses", 1, 12, 1)
        
        if st.button("✅ Ativar Assinatura", type="primary"):
            uid = obter_usuario_id(usuario_assinatura)
            if criar_assinatura(uid, meses_assinatura, "manual"):
                st.success(f"Assinatura de {meses_assinatura} mês(es) ativada para {usuario_assinatura}!")
                st.rerun()
            else:
                st.error("Erro ao ativar assinatura")
        
        st.markdown("---")
        st.markdown("#### Lista de Assinaturas")
        assinaturas_df = pd.read_sql("""
            SELECT a.id, u.nome, a.data_inicio, a.data_fim, a.valor_pago, a.status, a.metodo_pagamento
            FROM assinaturas a
            JOIN usuarios u ON a.usuario_id = u.id
            ORDER BY a.data_fim DESC
        """, conn)
        conn.close()
        
        if len(assinaturas_df) > 0:
            st.dataframe(assinaturas_df, use_container_width=True)
        else:
            st.info("Nenhuma assinatura cadastrada.")
    
    with tab5:
        st.markdown("### 💬 Gerenciar Comentários")
        
        conn = acessar_banco()
        comentarios_df = pd.read_sql("""
            SELECT c.id, c.questao_id, q.enunciado, u.nome as usuario, c.comentario, c.data_criacao
            FROM comentarios_questoes c
            JOIN questoes q ON c.questao_id = q.id
            JOIN usuarios u ON c.usuario_id = u.id
            ORDER BY c.data_criacao DESC
            LIMIT 50
        """, conn)
        conn.close()
        
        if len(comentarios_df) > 0:
            for idx, row in comentarios_df.iterrows():
                with st.expander(f"Questão {row['questao_id']} - {row['usuario']} ({row['data_criacao']})"):
                    st.write(f"**Enunciado:** {row['enunciado'][:100]}...")
                    st.write(f"**Comentário:** {row['comentario']}")
                    if st.button(f"🗑️ Deletar", key=f"del_com_{row['id']}"):
                        conn = acessar_banco()
                        conn.execute("DELETE FROM comentarios_questoes WHERE id = ?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
        else:
            st.info("Nenhum comentário cadastrado.")
    
    st.stop()

# ==============================
# 8. MENU PRINCIPAL: CONCURSO → CARGO → MATÉRIAS
# ==============================
if not st.session_state.simulado_ativo and not st.session_state.modo_revisao:
    st.markdown("# 📑 Escolha o Concurso e o Cargo")
    concursos = listar_concursos()
    # Incluir "Banco Geral" para questões sem concurso
    if concursos:
        concursos = [(None, "📂 Banco Geral (questões avulsas)")] + concursos

    if not concursos:
        st.warning("Nenhum concurso cadastrado. Execute: **python database.py** e depois **python seed_concursos.py**")
        st.stop()

    # Passo 1: Concurso
    st.markdown("### 1️⃣ Selecione o concurso")
    opcoes_conc = [nome for _, nome in concursos]
    concurso_escolhido = st.selectbox("Concurso", opcoes_conc, key="sel_concurso", label_visibility="collapsed")
    concurso_id = next(cid for cid, nome in concursos if nome == concurso_escolhido)

    cargos = listar_cargos(concurso_id)
    if not cargos:
        st.warning("Este concurso não possui cargos com questões. Use **Banco Geral** ou execute o seed.")
        st.stop()

    # Passo 2: Cargo
    st.markdown("### 2️⃣ Selecione o cargo")
    cargo_escolhido = st.selectbox("Cargo", [n for _, n in cargos], key="sel_cargo", label_visibility="collapsed")
    cargo_id = next(cid for cid, nome in cargos if nome == cargo_escolhido)

    materias = listar_materias(cargo_id)
    if not materias:
        st.warning("Não há questões para este cargo. Execute **python seed_concursos.py** ou importe questões.")
        st.stop()

    # Passo 3: Matérias e quantidades
    st.markdown("### 3️⃣ Matérias e quantidade de questões")
    config = {}
    with st.expander("Selecione as matérias e a quantidade por uma", expanded=True):
        for mat in materias:
            c1, c2 = st.columns([3, 1])
            if c1.checkbox(mat, key=f"check_{cargo_id}_{mat}"):
                config[mat] = c2.number_input("Qtd", 1, 100, 5, key=f"num_{cargo_id}_{mat}")

    if st.button("🚀 Iniciar simulado", type="primary", use_container_width=True):
        if config:
            st.session_state.questoes = carregar_questoes(cargo_id, config)
            st.session_state.indice_atual = 0
            st.session_state.historico_respostas = {}
            st.session_state.simulado_ativo = True
            st.session_state.resultado_final = None
            st.session_state.concurso_selecionado = concurso_id
            st.session_state.concurso_nome = concurso_escolhido
            st.session_state.cargo_selecionado = cargo_id
            st.session_state.cargo_nome = cargo_escolhido
            st.rerun()
        else:
            st.error("Selecione ao menos uma matéria.")

# ==============================
# 9. TELA DE SIMULADO / REVISÃO
# ==============================
else:
    if not st.session_state.questoes:
        st.session_state.simulado_ativo = False
        st.session_state.modo_revisao = False
        st.session_state.questoes = []
        st.rerun()

    if not st.session_state.modo_revisao:
        st_autorefresh(interval=1000, key="timer")

    # Cada questão: (id, enunciado, op_a, op_b, op_c, op_d, correta, materia, explicacao_teorica)
    q = st.session_state.questoes[st.session_state.indice_atual]
    questao_id = q[0]  # ID da questão
    enunciado, op_a, op_b, op_c, op_d, correta, materia, explicacao_teorica = q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8] if len(q) > 8 else ""

    # Breadcrumb e cabeçalho
    st.markdown(f'<p class="breadcrumb">📂 {st.session_state.concurso_nome} → {st.session_state.cargo_nome} → Simulado</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 1, 1])
    c1.subheader("📝 Simulado" if not st.session_state.modo_revisao else "🧐 Revisão das respostas")
    if not st.session_state.modo_revisao:
        if "t_inicio" not in st.session_state or st.session_state.indice_atual != st.session_state.get("last"):
            st.session_state.t_inicio = time.time()
            st.session_state.last = st.session_state.indice_atual
        tempo = max(0, 120 - int(time.time() - st.session_state.t_inicio))
        c2.metric("⏱️ Tempo", f"{tempo}s")
    c2.metric("Questão", f"{st.session_state.indice_atual + 1} / {len(st.session_state.questoes)}")
    if c3.button("🏠 Voltar ao menu"):
        st.session_state.simulado_ativo = False
        st.session_state.modo_revisao = False
        st.session_state.resultado_final = None
        st.rerun()

    st.markdown("---")
    st.markdown(f"**Matéria:** {materia}")
    st.markdown(f"### {enunciado}")

    resp = st.session_state.historico_respostas.get(st.session_state.indice_atual)
    opcoes = {"A": op_a, "B": op_b, "C": op_c, "D": op_d}

    for letra, texto in opcoes.items():
        if st.session_state.modo_revisao:
            if letra == correta:
                st.success(f"✅ **{letra})** {texto}")
            elif resp == letra:
                st.error(f"❌ **{letra})** {texto}")
            else:
                st.markdown(f"{letra}) {texto}")
        else:
            is_selected = resp == letra
            if st.button(
                f"{letra}) {texto}",
                key=f"btn_{letra}_{st.session_state.indice_atual}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                if resp is None:
                    st.session_state.historico_respostas[st.session_state.indice_atual] = letra
                    st.rerun()

    # Conteúdo teórico (só no modo revisão)
    if st.session_state.modo_revisao:
        st.markdown("---")
        st.markdown("#### 📚 Conteúdo teórico")
        if explicacao_teorica and explicacao_teorica.strip():
            html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', explicacao_teorica)
            html = html.replace('\n', '<br>')
            st.markdown(f'<div class="teoria-box"><h4>💡 Aprenda com esta questão</h4><div>{html}</div></div>', unsafe_allow_html=True)
        else:
            st.info("Não há explicação teórica cadastrada para esta questão. Estude a matéria **" + materia + "** para aprofundar.")

    # Navegação
    st.markdown("---")
    col_prev, col_spacer, col_next = st.columns([1, 1, 1])
    if st.session_state.indice_atual > 0:
        if col_prev.button("⬅️ Anterior", use_container_width=True):
            st.session_state.indice_atual -= 1
            st.rerun()
    if st.session_state.indice_atual < len(st.session_state.questoes) - 1:
        if col_next.button("Próxima ➡️", use_container_width=True):
            st.session_state.indice_atual += 1
            st.rerun()
    else:
        if not st.session_state.modo_revisao:
            if col_next.button("📊 Finalizar simulado", use_container_width=True, type="primary"):
                acertos = sum(1 for i, r in st.session_state.historico_respostas.items()
                             if r == st.session_state.questoes[i][6])  # Correta agora está em índice 6
                total = len(st.session_state.questoes)
                st.session_state.resultado_final = (acertos, total)
                st.session_state.modo_revisao = True
                st.session_state.simulado_ativo = False
                st.session_state.indice_atual = 0
                st.balloons()
                st.rerun()

    if st.session_state.modo_revisao and st.session_state.resultado_final:
        a, t = st.session_state.resultado_final
        percent = int(a / t * 100) if t > 0 else 0
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Desempenho")
        st.sidebar.metric("Acertos", f"{a} / {t}")
        st.sidebar.metric("Aproveitamento", f"{percent}%")
        if st.session_state.indice_atual == 0:
            st.success(f"### Resultado: {a}/{t} ({percent}%)")
