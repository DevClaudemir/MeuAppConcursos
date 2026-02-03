import sqlite3
import pandas as pd
import os

def importar_dados():
    arquivo_csv = 'questoes_para_importar.csv'
    
    # 1. Se o arquivo não existir, o script cria um modelo para você preencher
    if not os.path.exists(arquivo_csv):
        exemplo = {
            'enunciado': ['Exemplo: Quanto é 5+5?', 'Exemplo: Qual a capital da França?'],
            'op_a': ['10', 'Londres'],
            'op_b': ['15', 'Paris'],
            'op_c': ['20', 'Madri'],
            'op_d': ['25', 'Lisboa'],
            'correta': ['A', 'B'],
            'materia': ['Matemática', 'Geografia']
        }
        df_modelo = pd.DataFrame(exemplo)
        # Salva o modelo usando ponto e vírgula como separador (padrão Excel Brasil)
        df_modelo.to_csv(arquivo_csv, index=False, sep=';', encoding='utf-8-sig')
        print(f"--- ATENÇÃO ---")
        print(f"O arquivo '{arquivo_csv}' foi criado na sua pasta.")
        print("Abra ele, apague os exemplos, cole suas questões e salve.")
        print("Depois, rode este script novamente para importar.")
        return

    # 2. Se o arquivo já existe, ele lê e envia para o Banco de Dados
    try:
        # Lendo o CSV (usando ; como separador)
        df = pd.read_csv(arquivo_csv, sep=';', encoding='utf-8-sig')
        
        # Conectando ao seu banco de dados
        conexao = sqlite3.connect('banco_questoes.db')
        
        # 'append' significa que ele vai ADICIONAR ao que já existe, sem apagar nada
        df.to_sql('questoes', conexao, if_exists='append', index=False)
        
        conexao.close()
        print(f"--- SUCESSO ---")
        print(f"Foram importadas {len(df)} questões com sucesso!")
        
    except Exception as e:
        print(f"Erro ao importar: {e}")
        print("Verifique se o arquivo está aberto no Excel. Se estiver, feche-o e tente de novo.")

if __name__ == "__main__":
    importar_dados()