import streamlit as st
import sqlite3
import pandas as pd
import random

# No início do arquivo, após os imports
with st.sidebar:
    st.title("🔐 Área do Aluno")
    
    aba_login, aba_cadastro = st.tabs(["Entrar", "Criar Conta"])

    with aba_login:
        usuario = st.text_input("Usuário", key="user_login")
        senha = st.text_input("Senha", type="password", key="pass_login")
        if st.button("Fazer Login"):
            conn = acessar_banco()
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM usuarios WHERE nome = ? AND senha = ?", (usuario, senha))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                st.session_state.usuario_logado = user[0]
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")

    with aba_cadastro:
        novo_user = st.text_input("Novo Usuário")
        nova_senha = st.text_input("Nova Senha", type="password")
        if st.button("Cadastrar"):
            if novo_user and nova_senha:
                conn = acessar_banco()
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO usuarios (nome, senha) VALUES (?, ?)", (novo_user, nova_senha))
                    conn.commit()
                    st.success("Conta criada! Agora faça login.")
                except:
                    st.error("Erro ao cadastrar. Tente outro nome.")
                conn.close()

def acessar_banco():
    return sqlite3.connect('banco_questoes.db')

# --- INICIALIZAÇÃO DE VARIÁVEIS DE SESSÃO ---
if 'historico_respostas' not in st.session_state:
    st.session_state.historico_respostas = {}
if 'indice_atual' not in st.session_state:
    st.session_state.indice_atual = 0
if 'simulado_ativo' not in st.session_state:
    st.session_state.simulado_ativo = False
if 'questoes' not in st.session_state:
    st.session_state.questoes = []

# --- FUNÇÕES ---
def carregar_questoes(config):
    todas = []
    conn = acessar_banco()
    cursor = conn.cursor()
    for mat, qtd in config.items():
        if qtd > 0:
            cursor.execute('SELECT enunciado, op_a, op_b, op_c, op_d, correta, materia FROM questoes WHERE materia = ? ORDER BY RANDOM() LIMIT ?', (mat, qtd))
            todas.extend(cursor.fetchall())
    conn.close()
    random.shuffle(todas)
    return todas

# --- INTERFACE: MENU INICIAL ---
if not st.session_state.simulado_ativo:
    st.title("🎯 SimuConcursos Web 2026")
    st.subheader("Configure seu Simulado")
    
    conn = acessar_banco()
    materias = pd.read_sql_query("SELECT DISTINCT materia FROM questoes", conn)['materia'].tolist()
    conn.close()

    config = {}
    with st.expander("Escolher Matérias e Quantidades", expanded=True):
        for mat in materias:
            col1, col2 = st.columns([3, 1])
            selecionada = col1.checkbox(mat.upper(), key=f"check_{mat}")
            qtd = col2.number_input("Qtd", min_value=1, max_value=50, value=5, key=f"qtd_{mat}")
            if selecionada:
                config[mat] = qtd

    if st.button("🚀 INICIAR SIMULADO", use_container_width=True):
        questoes = carregar_questoes(config)
        if questoes:
            st.session_state.questoes = questoes
            st.session_state.simulado_ativo = True
            st.session_state.indice_atual = 0
            st.session_state.historico_respostas = {}
            st.rerun()

# --- INTERFACE: TELA DE QUESTÕES ---
else:
    q_atual = st.session_state.questoes[st.session_state.indice_atual]
    
    # Cabeçalho
    col_topo1, col_topo2 = st.columns([3, 1])
    col_topo1.write(f"**Questão {st.session_state.indice_atual + 1} de {len(st.session_state.questoes)}**")
    if col_topo2.button("❌ Encerrar"):
        st.session_state.simulado_ativo = False
        st.rerun()

    st.divider()
    st.info(f"Matéria: {q_atual[6]}")
    st.write(f"### {q_atual[0]}")

    # Opções
    opcoes = {
        'A': f"A) {q_atual[1]}",
        'B': f"B) {q_atual[2]}",
        'C': f"C) {q_atual[3]}",
        'D': f"D) {q_atual[4]}"
    }

    # Verifica se já respondeu
    resposta_dada = st.session_state.historico_respostas.get(st.session_state.indice_atual)
    
    for letra, texto in opcoes.items():
        if st.button(texto, use_container_width=True, key=f"btn_{letra}_{st.session_state.indice_atual}"):
            if not resposta_dada:
                st.session_state.historico_respostas[st.session_state.indice_atual] = letra
                st.rerun()

    # Feedback visual após responder
    if resposta_dada:
        if resposta_dada == q_atual[5]:
            st.success(f"Correto! Você marcou {resposta_dada}")
        else:
            st.error(f"Errado! Você marcou {resposta_dada}. A correta é {q_atual[5]}")

    # Navegação
    st.divider()
    col_nav1, col_nav2, col_nav3 = st.columns(3)
    if st.session_state.indice_atual > 0:
        if col_nav1.button("⬅️ Anterior"):
            st.session_state.indice_atual -= 1
            st.rerun()
    
    if st.session_state.indice_atual < len(st.session_state.questoes) - 1:
        if col_nav3.button("Próxima ➡️"):
            st.session_state.indice_atual += 1
            st.rerun()
    else:
        if col_nav3.button("📊 Finalizar"):
            # Lógica de salvar histórico no DB aqui
            st.balloons()
            st.session_state.simulado_ativo = False
            st.rerun()
def criar_tabela_usuarios():
    conn = acessar_banco()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            senha TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

criar_tabela_usuarios()