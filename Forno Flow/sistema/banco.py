import sqlite3
import hashlib

def gerar_hash(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def inicializar_banco():
    conexao = sqlite3.connect("sistema.db")
    cursor = conexao.cursor()    
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS acessos (
                id INTEGER PRIMARY KEY,
                usuario TEXT NOT NULL,
                tipo INTEGER NOT NULL,
                senha_hash TEXT NOT NULL
            )
        """)
        
    senha_padrao = gerar_hash("1234")
    
    cursor.executemany("""
    INSERT OR IGNORE INTO acessos (usuario, tipo, senha_hash)
    VALUES
    (?, ?, ?)
    """,
    [("gerente", 1, senha_padrao),
    ("cozinha", 2, senha_padrao),
    ("financeiro", 3, senha_padrao),
    ("delivery", 4, senha_padrao)]
    )


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY,
            cliente TEXT NOT NULL,
            produto TEXT NOT NULL,
            valor REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'aguardando',
            horario TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY,
            item TEXT NOT NULL,
            categoria TEXT NOT NULL,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL,
            status TEXT NOT NULL
        )
    """)

    conexao.commit()
    conexao.close()