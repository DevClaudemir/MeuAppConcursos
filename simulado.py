import sqlite3
import random

def rodar_simulado():
    conexao = sqlite3.connect('banco_questoes.db')
    cursor = conexao.cursor()
    cursor.execute('SELECT enunciado, op_a, op_b, op_c, op_d, correta, materia FROM questoes')
    questoes = cursor.fetchall()
    conexao.close()

    if not questoes:
        print("Adicione questões primeiro!")
        return

    pontos = 0
    total = 5 # Vamos fazer rodadas de 5 questões
    random.shuffle(questoes) # Embaralha as questões para não ser sempre igual

    print(f"\n=== INICIANDO SIMULADO DE {total} QUESTÕES ===")

    for i in range(total):
        q = questoes[i]
        enunciado, a, b, c, d, correta, materia = q

        print(f"\nQUESTÃO {i+1} [{materia}]")
        print(enunciado)
        print(f"A) {a}\nB) {b}\nC) {c}\nD) {d}")

        res = input("Sua resposta: ").strip().upper()

        if res == correta:
            print("✔ Boa!")
            pontos += 1
        else:
            print(f"✘ Errou. Era a letra {correta}.")

    print(f"\n=== FIM DO SIMULADO ===")
    print(f"Você acertou {pontos} de {total} questões. ({int(pontos/total*100)}%)")

if __name__ == "__main__":
    rodar_simulado()