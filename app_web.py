import streamlit as st
import sqlite3
import pandas as pd
import random
import time
import hashlib
from streamlit_autorefresh import st_autorefresh


# ==============================
# 1. CONFIGURAÇÕES INICIAIS
# ==============================
st.set_page_config(page_title="SimuConcursos 2026", layout="centered")

# ==============================
# 2. BANCO DE DADOS
# ==============================
def acessar_banco():
    return sqlite3.connect("banco_questoes.db", check_same_thread=False)

def criar_tabela_usuarios():
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

criar_tabela_usuarios()

# ==============================
# 3. SEGURANÇA
# ==============================
def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

# ==============================
# 4. SESSION STATE
# ==============================
for k, v in {
    "usuario_logado": None,
    "historico_respostas": {},
    "indice_atual": 0,
    "simulado_ativo": False,
    "modo_revisao": False,
    "questoes": [],
    "resultado_final": None
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==============================
# 5. SIDEBAR
# ==============================
with st.sidebar:
    st.title("🔐 Área do Aluno")

    if st.session_state.usuario_logado is None:
        aba_login, aba_cadastro = st.tabs(["Entrar", "Criar Conta"])

        with aba_login:
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")

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
            nu = st.text_input("Novo Usuário")
            ns = st.text_input("Nova Senha", type="password")

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
        st.write(f"Conectado como: **{st.session_state.usuario_logado}**")
        if st.button("Sair / Logoff", type="primary", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ==============================
# 6. BLOQUEIO DE SEGURANÇA
# ==============================
if st.session_state.usuario_logado is None:
    st.title("🎯 SimuConcursos 2026")
    st.info("Faça login para acessar.")
    st.stop()

# ==============================
# 7. FUNÇÃO DE CARREGAMENTO
# ==============================
def carregar_questoes(config):
    todas = []
    conn = acessar_banco()

    for materia, qtd in config.items():
        rows = conn.execute(
            "SELECT ROWID FROM questoes WHERE materia=?",
            (materia,)
        ).fetchall()

        if not rows:
            continue

        ids = [r[0] for r in rows]
        escolhidos = random.sample(ids, min(qtd, len(ids)))

        for rid in escolhidos:
            q = conn.execute("""
                SELECT enunciado, op_a, op_b, op_c, op_d, correta, materia
                FROM questoes WHERE ROWID=?
            """, (rid,)).fetchone()
            if q:
                todas.append(q)

    conn.close()
    random.shuffle(todas)
    return todas

# ==============================
# 8. TELA DE CONFIGURAÇÃO (MENU)
# ==============================
if not st.session_state.simulado_ativo and not st.session_state.modo_revisao:
    st.title("📑 Painel de Simulados")

    conn = acessar_banco()
    materias_df = pd.read_sql("SELECT DISTINCT materia FROM questoes", conn)
    materias = materias_df["materia"].tolist()
    conn.close()

    config = {}
    with st.expander("Selecione as Matérias", expanded=True):
        for mat in materias:
            c1, c2 = st.columns([3, 1])
            if c1.checkbox(mat.upper(), key=f"check_{mat}"):
                config[mat] = c2.number_input("Qtd", 1, 100, 5, key=f"num_{mat}")

    if st.button("🚀 INICIAR SIMULADO", use_container_width=True):
        if config:
            st.session_state.questoes = carregar_questoes(config)
            st.session_state.indice_atual = 0
            st.session_state.historico_respostas = {}
            st.session_state.simulado_ativo = True
            st.session_state.resultado_final = None
            st.rerun()
        else:
            st.error("Selecione ao menos uma matéria!")

# ==============================
# 9. TELA DE SIMULADO / REVISÃO
# ==============================
else:
    # Proteção: se não houver questões, volta ao menu
    if not st.session_state.questoes:
        st.session_state.simulado_ativo = False
        st.session_state.modo_revisao = False
        st.session_state.questoes = []
        st.rerun()

    # Gerenciamento de tempo e refresh
    if not st.session_state.modo_revisao:
        st_autorefresh(interval=1000, key="timer")

    q = st.session_state.questoes[st.session_state.indice_atual]

    c1, c2, c3 = st.columns([2, 1, 1])
    c1.subheader("📝 Simulado Ativo" if not st.session_state.modo_revisao else "🧐 Modo Revisão")

    if not st.session_state.modo_revisao:
        if "t_inicio" not in st.session_state or st.session_state.indice_atual != st.session_state.get("last"):
            st.session_state.t_inicio = time.time()
            st.session_state.last = st.session_state.indice_atual

        tempo = max(0, 120 - int(time.time() - st.session_state.t_inicio))
        c2.metric("⏱️ Tempo", f"{tempo}s")

    if c3.button("🏠 Menu"):
        st.session_state.simulado_ativo = False
        st.session_state.modo_revisao = False
        st.session_state.resultado_final = None
        st.rerun()

    st.divider()
    st.write(f"**Matéria:** {q[6]} | Questão {st.session_state.indice_atual + 1} de {len(st.session_state.questoes)}")
    st.markdown(f"#### {q[0]}")

    resp = st.session_state.historico_respostas.get(st.session_state.indice_atual)
    opcoes = {"A": q[1], "B": q[2], "C": q[3], "D": q[4]}

    # Exibição das alternativas
    for l, t in opcoes.items():
        if st.session_state.modo_revisao:
            if l == q[5]:
                st.success(f"✅ {l}) {t}")
            elif resp == l:
                st.error(f"❌ {l}) {t}")
            else:
                st.write(f"{l}) {t}")
        else:
            is_selected = (resp == l)
            if st.button(f"{l}) {t}", key=f"btn_{l}_{st.session_state.indice_atual}", 
                         use_container_width=True, type="primary" if is_selected else "secondary"):
                if resp is None:
                    st.session_state.historico_respostas[st.session_state.indice_atual] = l
                    st.rerun()

    # Barra de Navegação Inferior
    st.divider()
    col_prev, col_spacer, col_next = st.columns([1, 1, 1])

    if st.session_state.indice_atual > 0:
        if col_prev.button("⬅️ Voltar", use_container_width=True):
            st.session_state.indice_atual -= 1
            st.rerun()

    if st.session_state.indice_atual < len(st.session_state.questoes) - 1:
        if col_next.button("Próxima ➡️", use_container_width=True):
            st.session_state.indice_atual += 1
            st.rerun()
    else:
        if not st.session_state.modo_revisao:
            if col_next.button("📊 FINALIZAR", use_container_width=True, type="primary"):
                acertos = sum(1 for i, r in st.session_state.historico_respostas.items() 
                              if r == st.session_state.questoes[i][5])
                total = len(st.session_state.questoes)
                st.session_state.resultado_final = (acertos, total)
                st.session_state.modo_revisao = True
                st.session_state.simulado_ativo = False
                st.session_state.indice_atual = 0
                st.balloons()
                st.rerun()

    # ==============================
    # 10. RESULTADO FINAL (DENTRO DO MODO REVISÃO)
    # ==============================
    if st.session_state.modo_revisao and st.session_state.resultado_final:
        a, t = st.session_state.resultado_final
        percent = int(a/t*100) if t > 0 else 0
        
        st.sidebar.divider()
        st.sidebar.subheader("📊 Seu Desempenho")
        st.sidebar.metric("Acertos", f"{a}/{t}")
        st.sidebar.metric("Aproveitamento", f"{percent}%")
        
        if st.session_state.indice_atual == 0: # Só mostra o banner principal na primeira questão da revisão
            st.info(f"### Resultado Final: {a}/{t} ({percent}%)")