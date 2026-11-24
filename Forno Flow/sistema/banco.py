import sqlite3
import hashlib

def inicializar_banco():
    conexao = sqlite3.connect("sistema.db")
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS acesso_gerente (
            id INTEGER PRIMARY KEY,
            senha_hash TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS acesso_cozinha (
            id INTEGER PRIMARY KEY,
            senha_hash TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS acesso_caixa (
            id INTEGER PRIMARY KEY,
            senha_hash TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS acesso_delivery (
            id INTEGER PRIMARY KEY,
            senha_hash TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY,
            cliente TEXT NOT NULL
            item TEXT NOT NULL
            valor REAL NOT NULL
            status TEXT NOT NULL DEFAULT 'aguardando'
            CHECK (status IN ('concluido', 'em preparo', 'aguardando', 'em entrega'))
            horario TEXT NOT NULL
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY,
            produto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            preco REAL NOT NULL
            estoque INTEGER NOT NULL
            status TEXT NOT NULL
            CHECK (status IN ('em estoque', 'estoque baixo', 'estoque critico', 'fora de estoque')
        )
    """)

    conexao.commit()
    conexao.close()

def gerar_hash(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()