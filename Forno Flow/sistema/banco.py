import sqlite3
import hashlib


def gerar_hash(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def conectar():
    conexao = sqlite3.connect("sistema.db")
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON;")
    return conexao


def inicializar_banco():
    conexao = conectar()
    try:
        with conexao:
            cursor = conexao.cursor()

            # 1. Tabela de Acessos (usuários e perfis do sistema)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS acessos (
                    id INTEGER PRIMARY KEY,
                    usuario TEXT NOT NULL UNIQUE,
                    tipo INTEGER NOT NULL CHECK (tipo IN (1, 2, 3, 4)),
                    senha_hash TEXT NOT NULL
                )
            """)

            senha_padrao = gerar_hash("1234")
            cursor.executemany(
                """
                INSERT OR IGNORE INTO acessos (usuario, tipo, senha_hash)
                VALUES (?, ?, ?)
                """,
                [
                    ("gerente", 1, senha_padrao),
                    ("cozinha", 2, senha_padrao),
                    ("financeiro", 3, senha_padrao),
                    ("delivery", 4, senha_padrao),
                ],
            )

            # 2. Tabela de Estoque (insumos, custos e faixas de alerta)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS estoque (
                    id INTEGER PRIMARY KEY,
                    ingrediente TEXT NOT NULL UNIQUE,
                    unidade TEXT NOT NULL CHECK (unidade IN ('g', 'ml', 'un', 'l', 'kg')),
                    quantidade REAL NOT NULL CHECK (quantidade >= 0),
                    custo_unitario REAL NOT NULL CHECK (custo_unitario >= 0),
                    estoque_minimo REAL NOT NULL DEFAULT 0 CHECK (estoque_minimo >= 0),
                    estoque_ideal REAL NOT NULL CHECK (estoque_ideal > 0),
                    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
                    CHECK (estoque_ideal >= estoque_minimo)
                )
            """)

            try:
                cursor.execute(
                    "ALTER TABLE estoque ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))"
                )
            except sqlite3.OperationalError:
                pass

            # 3. Tabela de Produtos (cardápio vendido ao cliente)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY,
                    nome TEXT NOT NULL UNIQUE,
                    categoria TEXT NOT NULL,
                    preco REAL NOT NULL CHECK (preco >= 0),
                    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
                )
            """)

            try:
                cursor.execute(
                    "ALTER TABLE produtos ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))"
                )
            except sqlite3.OperationalError:
                pass

            # 4. Tabela de Receitas (ficha técnica: Produto <-> Estoque)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS receitas (
                    id INTEGER PRIMARY KEY,
                    produto_id INTEGER NOT NULL,
                    ingrediente_id INTEGER NOT NULL,
                    quantidade_necessaria REAL NOT NULL CHECK (quantidade_necessaria > 0),
                    UNIQUE (produto_id, ingrediente_id),
                    FOREIGN KEY (produto_id) REFERENCES produtos(id),
                    FOREIGN KEY (ingrediente_id) REFERENCES estoque(id)
                )
            """)

            # 5. Tabela de Pedidos (vendas, financeiro e delivery)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos (
                    id INTEGER PRIMARY KEY,
                    cliente TEXT NOT NULL,
                    produto_id INTEGER NOT NULL,
                    quantidade INTEGER NOT NULL DEFAULT 1 CHECK (quantidade > 0),
                    valor_total REAL NOT NULL CHECK (valor_total >= 0),
                    custo_total REAL NOT NULL CHECK (custo_total >= 0),
                    forma_pagamento TEXT NOT NULL,
                    tipo_entrega TEXT NOT NULL,
                    bairro TEXT,
                    taxa_entrega REAL NOT NULL DEFAULT 0 CHECK (taxa_entrega >= 0),
                    status TEXT NOT NULL DEFAULT 'aprovado'
                        CHECK (status IN ('aprovado', 'em preparo', 'saiu para entrega', 'concluido', 'cancelado')),
                    data_hora TEXT NOT NULL,
                    FOREIGN KEY (produto_id) REFERENCES produtos(id)
                )
            """)

            # 6. Tabela de Movimentações de Estoque (histórico de compras, saídas, perdas e ajustes)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
                    id INTEGER PRIMARY KEY,
                    ingrediente_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida_venda', 'perda', 'ajuste', 'estorno')),
                    quantidade REAL NOT NULL,
                    custo_total REAL NOT NULL CHECK (custo_total >= 0),
                    data_hora TEXT NOT NULL,
                    CHECK (
                        (tipo = 'ajuste' AND quantidade != 0)
                        OR (tipo != 'ajuste' AND quantidade > 0)
                    ),
                    FOREIGN KEY (ingrediente_id) REFERENCES estoque(id)
                )
            """)
    finally:
        conexao.close()