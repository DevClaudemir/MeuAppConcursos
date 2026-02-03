import requests
from bs4 import BeautifulSoup
import sqlite3

def salvar_no_banco(enunciado, materia):
    conexao = sqlite3.connect('banco_questoes.db')
    cursor = conexao.cursor()
    cursor.execute('''
    INSERT INTO questoes (enunciado, op_a, op_b, op_c, op_d, correta, materia)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (enunciado, 'A', 'B', 'C', 'D', 'A', materia))
    conexao.commit()
    conexao.close()

def coletar_estilo_direto():
    # Mudamos para uma página de questões geral que é mais fácil de ler
    url = "https://www.gabarite.com.br/questoes-de-concursos/materia/portugues"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    print("Tentando nova estratégia de coleta...")
    resposta = requests.get(url, headers=headers)
    sopa = BeautifulSoup(resposta.text, 'html.parser')
    
    # Agora vamos buscar por qualquer bloco que pareça uma questão
    # O Gabarite costuma usar a classe 'questao-txt' ou 'enunciado'
    blocos = sopa.find_all('div', class_='enunciado')
    
    if not blocos:
        # Se não achou, tenta a classe geral de texto de questão
        blocos = sopa.select('.questao-txt') 

    print(f"Encontrei {len(blocos)} blocos de texto.")

    for b in blocos[:5]:
        texto = b.get_text().strip()
        if len(texto) > 10: # Garante que não é um texto vazio
            print(f"Salvando questão: {texto[:40]}...")
            salvar_no_banco(texto, "Português")
    
    if len(blocos) > 0:
        print("\nVITÓRIA! As questões foram enviadas para o banco.")
    else:
        print("\nO site ainda está escondendo o jogo. Vamos precisar de outra abordagem.")

if __name__ == "__main__":
    coletar_estilo_direto()