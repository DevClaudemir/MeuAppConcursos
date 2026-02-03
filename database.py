import sqlite3

def criar_tabela():
    # Conecta ao banco (cria o arquivo se ele não existir)
    conexao = sqlite3.connect('banco_questoes.db')
    cursor = conexao.cursor()

    # Cria a estrutura da tabela de questões
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enunciado TEXT NOT NULL,
        op_a TEXT NOT NULL,
        op_b TEXT NOT NULL,
        op_c TEXT NOT NULL,
        op_d TEXT NOT NULL,
        op_e TEXT,
        correta TEXT NOT NULL,
        materia TEXT NOT NULL
    )
    ''')

    conexao.commit()
    conexao.close()
    print("Sucesso: Arquivo 'banco_questoes.db' criado!")

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