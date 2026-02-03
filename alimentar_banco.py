import sqlite3

def alimentar():
    conexao = sqlite3.connect('banco_questoes.db')
    cursor = conexao.cursor()

    # Uma lista de questões reais (Simulando o que o robô colheria)
    questoes_reais = [
        (
            "Assinale a alternativa em que todos os vocábulos estejam acentuados pela mesma regra:",
            "vênus, hífen, fáceis", "saúde, egoísmo, atribuí-lo", "têm, convêm, mantém", "público, parágrafo, ética",
            "D", "Português"
        ),
        (
            "O servidor público que agir com dolo ou culpa responderá por seus atos perante a administração. Isso se refere à responsabilidade:",
            "Penal", "Civil", "Administrativa", "Política",
            "C", "Direito Administrativo"
        ),
        (
            "Qual o valor de x na equação 2x + 10 = 30?",
            "5", "10", "15", "20",
            "B", "Matemática"
        ),
        (
            "A Constituição Federal de 1988 é classificada como:",
            "Outorgada", "Promulgada", "Cesarista", "Dualista",
            "B", "Direito Constitucional"
        ),
        (
            "Sinônimo de 'Efêmero' é:",
            "Duradouro", "Passageiro", "Eterno", "Fixo",
            "B", "Português"
        )
    ]

    # Comando para inserir várias de uma vez
    cursor.executemany('''
    INSERT INTO questoes (enunciado, op_a, op_b, op_c, op_d, correta, materia)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', questoes_reais)

    conexao.commit()
    conexao.close()
    print(f"Sucesso! {len(questoes_reais)} questões reais foram adicionadas ao seu banco.")

if __name__ == "__main__":
    alimentar()