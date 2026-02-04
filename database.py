import sqlite3

def criar_tabela():
    # Conecta ao banco (cria o arquivo se ele não existir)
    conexao = sqlite3.connect('banco_questoes.db')
    cursor = conexao.cursor()

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