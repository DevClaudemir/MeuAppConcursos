import sqlite3
import matplotlib.pyplot as plt

def gerar_grafico():
    conexao = sqlite3.connect('banco_questoes.db')
    cursor = conexao.cursor()
    
    # Busca os percentuais de acerto na ordem que foram feitos
    cursor.execute('SELECT id, percentual FROM historico ORDER BY id')
    dados = cursor.fetchall()
    conexao.close()

    if not dados:
        print("Faça pelo menos um simulado para gerar o gráfico!")
        return

    # Organiza os dados para o gráfico
    tentativas = [d[0] for d in dados]
    notas = [d[1] for d in dados]

    # Cria o desenho do gráfico
    plt.figure(figsize=(10, 5))
    plt.plot(tentativas, notas, marker='o', linestyle='-', color='b', label='Sua Nota %')
    
    # Adiciona uma linha de "Corte" (ex: 70% para passar)
    plt.axhline(y=70, color='r', linestyle='--', label='Meta (70%)')

    plt.title('Evolução no Simulado de Concursos')
    plt.xlabel('Número do Simulado')
    plt.ylabel('Percentual de Acerto (%)')
    plt.ylim(0, 105) # Escala de 0 a 100
    plt.legend()
    plt.grid(True)
    
    print("Exibindo gráfico...")
    plt.show()

if __name__ == "__main__":
    gerar_grafico()