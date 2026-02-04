"""
Script para tornar o primeiro usuário cadastrado em admin
Execute: python criar_admin.py
"""
import sqlite3

def criar_admin():
    conn = sqlite3.connect("banco_questoes.db")
    c = conn.cursor()
    
    # Busca o primeiro usuário
    usuario = c.execute("SELECT id, nome FROM usuarios LIMIT 1").fetchone()
    
    if not usuario:
        print("Nenhum usuário encontrado. Crie um usuário primeiro no app.")
        conn.close()
        return
    
    usuario_id, nome = usuario
    
    # Verifica se já é admin
    ja_admin = c.execute("SELECT id FROM admins WHERE usuario_id = ?", (usuario_id,)).fetchone()
    
    if ja_admin:
        print(f"O usuário '{nome}' já é admin.")
    else:
        c.execute("INSERT INTO admins (usuario_id) VALUES (?)", (usuario_id,))
        conn.commit()
        print(f"✅ Usuário '{nome}' agora é ADMIN!")
    
    conn.close()

if __name__ == "__main__":
    criar_admin()
