import sqlite3

def criar_tabela():
    # Conecta ao banco (cria o arquivo se ele não existir)
    conexao = sqlite3.connect('banco_questoes.db')
    cursor = conexao.cursor()

    # Tabela de usuários (precisa existir antes de admins)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL
    )
    ''')

    # Tabela de concursos (ex.: Câmara dos Deputados, SEFAZ PA)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS concursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE
    )
    ''')

    # Tabela de cargos (ex.: Policial Legislativo, Fiscal)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cargos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concurso_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        UNIQUE(concurso_id, nome),
        FOREIGN KEY (concurso_id) REFERENCES concursos(id)
    )
    ''')

    # Tabela de admins (apenas dono)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL UNIQUE,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    ''')

    # Tabela de assinaturas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS assinaturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        data_inicio DATE NOT NULL,
        data_fim DATE NOT NULL,
        valor_pago REAL NOT NULL DEFAULT 5.00,
        status TEXT NOT NULL DEFAULT 'ativa',
        metodo_pagamento TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    ''')

    # Tabela de comentários nas questões
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comentarios_questoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        questao_id INTEGER NOT NULL,
        usuario_id INTEGER NOT NULL,
        comentario TEXT NOT NULL,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (questao_id) REFERENCES questoes(id),
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    ''')

    # Cria a estrutura da tabela de questões
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cargo_id INTEGER,
        enunciado TEXT NOT NULL,
        op_a TEXT NOT NULL,
        op_b TEXT NOT NULL,
        op_c TEXT NOT NULL,
        op_d TEXT NOT NULL,
        op_e TEXT,
        correta TEXT NOT NULL,
        materia TEXT NOT NULL,
        explicacao_teorica TEXT,
        banca TEXT,
        ano INTEGER,
        orgao TEXT,
        origem TEXT DEFAULT 'manual',
        hash_enunciado TEXT,
        FOREIGN KEY (cargo_id) REFERENCES cargos(id)
    )
    ''')

    # Colunas novas (se a tabela já existir sem elas)
    try:
        cursor.execute('ALTER TABLE questoes ADD COLUMN cargo_id INTEGER')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('ALTER TABLE questoes ADD COLUMN explicacao_teorica TEXT')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('ALTER TABLE questoes ADD COLUMN banca TEXT')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('ALTER TABLE questoes ADD COLUMN ano INTEGER')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('ALTER TABLE questoes ADD COLUMN orgao TEXT')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('ALTER TABLE questoes ADD COLUMN origem TEXT DEFAULT "manual"')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('ALTER TABLE questoes ADD COLUMN hash_enunciado TEXT')
    except sqlite3.OperationalError:
        pass

    conexao.commit()
    conexao.close()
    print("Sucesso: Arquivo 'banco_questoes.db' e tabelas criados!")

if __name__ == "__main__":
    criar_tabela()

def criar_tabela_historico():
    conexao = sqlite3.connect('banco_questoes.db')
    cursor = conexao.cursor()
    # Cria uma tabela para guardar cada simulado feito
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        acertos INTEGER,
        total INTEGER,
        percentual REAL
    )
    ''')
    conexao.commit()
    conexao.close()
    print("Tabela de histórico pronta!")

if __name__ == "__main__":
    criar_tabela_historico()