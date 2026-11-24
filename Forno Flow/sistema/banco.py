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

    conexao.commit()
    conexao.close()

def gerar_hash(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()