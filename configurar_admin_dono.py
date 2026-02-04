"""
Script para configurar o admin dono do site
Execute: python configurar_admin_dono.py
"""
import sqlite3
import hashlib
from config import ADMIN_DONO

def configurar_admin():
    conn = sqlite3.connect("banco_questoes.db")
    c = conn.cursor()
    
    # Busca o usuário admin
    usuario = c.execute("SELECT id, nome FROM usuarios WHERE nome = ?", (ADMIN_DONO,)).fetchone()
    
    if not usuario:
        print(f"❌ Usuário '{ADMIN_DONO}' não encontrado!")
        print(f"\nCrie o usuário '{ADMIN_DONO}' primeiro:")
        print("1. Execute: streamlit run app_web.py")
        print("2. Cadastre o usuário com nome:", ADMIN_DONO)
        print("3. Execute este script novamente")
        conn.close()
        return
    
    usuario_id, nome = usuario
    
    # Verifica se já é admin
    ja_admin = c.execute("SELECT id FROM admins WHERE usuario_id = ?", (usuario_id,)).fetchone()
    
    if ja_admin:
        print(f"✅ Usuário '{nome}' já é ADMIN!")
    else:
        c.execute("INSERT OR IGNORE INTO admins (usuario_id) VALUES (?)", (usuario_id,))
        conn.commit()
        print(f"✅ Usuário '{nome}' agora é ADMIN DONO!")
    
    conn.close()

if __name__ == "__main__":
    print("=== Configuração do Admin Dono ===")
    print(f"Configurando usuário: {ADMIN_DONO}")
    print()
    configurar_admin()
