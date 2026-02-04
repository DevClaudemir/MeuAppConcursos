import streamlit as st
import sqlite3
import pandas as pd
import random
import re
import time
import hashlib
from streamlit_autorefresh import st_autorefresh

# ==============================
# 1. CONFIGURAÇÕES E ESTILO
# ==============================
st.set_page_config(page_title="Plataforma de Questões | Concursos", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* Tema profissional - tons escuros e verdes */
    .stApp { background: linear-gradient(180deg, #0e1a14 0%, #16251e 50%, #0d1812 100%); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f1f17 0%, #132118 100%); }
    [data-testid="stSidebar"] .stMarkdown { color: #b8d4c4; }
    h1, h2, h3 { color: #7dd3a0 !important; font-weight: 600 !important; }
    .concurso-card {
        background: linear-gradient(145deg, #1a2e24 0%, #0f1f17 100%);
        border: 1px solid #2d4a3a;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 0.5rem 0;
        transition: all 0.2s;
    }
    .concurso-card:hover { border-color: #3d7a5c; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    .breadcrumb { color: #8fbc9a; font-size: 0.9rem; margin-bottom: 1rem; }
    .teoria-box {
        background: linear-gradient(145deg, #1a2e24 0%, #0d1812 100%);
        border-left: 4px solid #3d7a5c;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 1rem 0;
        color: #c8e6d0;
    }
    .teoria-box h4 { color: #7dd3a0 !important; margin-top: 0 !important; }
    .metric-card { background: #1a2e24; border-radius: 10px; padding: 1rem; border: 1px solid #2d4a3a; }
    div[data-testid="stExpander"] { background: #132218; border: 1px solid #2d4a3a; border-radius: 10px; }
    .stButton > button { border-radius: 8px; font-weight: 500; }
    .stButton > button[kind="primary"] { background: linear-gradient(90deg, #2d6a4f 0%, #40916c 100%); border: none; }
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
    conn.commit()
    conn.close()

criar_tabelas()

# ==============================
# 3. SEGURANÇA
# ==============================
def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

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
                SELECT enunciado, op_a, op_b, op_c, op_d, correta, materia,
                       COALESCE(explicacao_teorica, '') AS explicacao_teorica
                FROM questoes WHERE id = ?
            """, (qid,)).fetchone()
            if q:
                todas.append(q)
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
                        st.success("Conta criada! Vá para Entrar.")
                    except sqlite3.IntegrityError:
                        st.error("Usuário já existe.")
                    conn.close()
    else:
        st.success(f"**{st.session_state.usuario_logado}**")
        if st.button("Sair", type="primary", use_container_width=True):
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

    # Cada questão: (enunciado, op_a, op_b, op_c, op_d, correta, materia, explicacao_teorica)
    q = st.session_state.questoes[st.session_state.indice_atual]
    enunciado, op_a, op_b, op_c, op_d, correta, materia, explicacao_teorica = q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7] if len(q) > 7 else ""

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
                             if r == st.session_state.questoes[i][5])
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
