import sqlite3

def inserir_uma_questao():
    # 1. Conecta ao arquivo que você já criou
    conexao = sqlite3.connect('banco_questoes.db')
    cursor = conexao.cursor()

    # 2. Prepara os dados de uma questão fictícia
    enunciado = "Qual é a capital do Brasil?"
    a = "São Paulo"
    b = "Rio de Janeiro"
    c = "Brasília"
    d = "Salvador"
    correta = "C"
    materia = "Geografia"

    # 3. Manda o comando para o banco de dados salvar esses dados
    cursor.execute('''
    INSERT INTO questoes (enunciado, op_a, op_b, op_c, op_d, correta, materia)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (enunciado, a, b, c, d, correta, materia))

    # 4. Salva (commit) e fecha a conexão
    conexao.commit()
    conexao.close()
    print("Missa cumprida: Questão de teste inserida com sucesso!")

if __name__ == "__main__":
    inserir_uma_questao()