import sqlite3
import math
from datetime import datetime
from banco import conectar
from setores.telas.receitas import (
    calcular_custo_receita,
    verificar_disponibilidade,
    consumir_estoque_receita,
    capacidade_producao,
    listar_produtos_ativos
)


horario = datetime.now().strftime("%H:%M")

# consultar cardápio

def consultar_cardapio():
    cardapio = listar_produtos_ativos()

    if not cardapio:
        print("Nenhum produto ativo disponível no cardápio.")
        return False

    print("\n--- CARDÁPIO DISPONÍVEL ---")
    for item in cardapio:
        status = f"{item['disponivel']} un" if item["disponivel"] > 0 else "ESGOTADO"
        print(f"ID {item['id']} | {item['nome']} ({item['categoria']}) - R$ {item['preco']:.2f} | Disponível: {status}")

    return True

# validar pedido

def validar_pedido(cliente, produto_id, quantidade,
                   forma_pagamento, tipo_entrega,
                   bairro, taxa_entrega):

    if not cliente:
        raise ValueError("Informe o nome do cliente.")

    if produto_id <= 0:
        raise ValueError("ID do produto inválido.")

    if quantidade <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")

    if forma_pagamento not in ("pix", "dinheiro", "crédito", "débito"):
        raise ValueError("Forma de pagamento inválida.")

    if tipo_entrega not in ("entrega", "retirada"):
        raise ValueError("Tipo de entrega inválido.")

    if not math.isfinite(taxa_entrega) or taxa_entrega < 0:
        raise ValueError("Taxa de entrega inválida.")

    if tipo_entrega == "entrega" and not bairro:
        raise ValueError("Informe o bairro do cliente.")

    if tipo_entrega == "retirada" and (bairro or taxa_entrega != 0):
        raise ValueError("Retirada não deve possuir taxa ou bairro.")

    return True

# calcular valor do pedido

def calcular_valor_pedido(preco, quantidade, taxa_entrega=0):
    subtotal = preco * quantidade
    valor_total = subtotal + taxa_entrega

    return round(valor_total, 2)

# aprovar pedido

def aprovar_pedido(cliente, produto_id, quantidade,
                   forma_pagamento, tipo_entrega,
                   bairro, taxa_entrega):

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        # Iniciar transação
        cursor.execute("BEGIN IMMEDIATE")

        # Consultar produto selecionado
        cursor.execute("""
            SELECT id, nome, categoria, preco
            FROM produtos
            WHERE id = ?
            AND ativo = 1
        """, (produto_id,))

        produto = cursor.fetchone()

        if not produto:
            print("Produto não encontrado ou inativo.")
            conexao.rollback()
            return False

        # Motor de receitas: verificar disponibilidade
        disponivel, mensagem = verificar_disponibilidade(
            produto_id, quantidade
        )

        if not disponivel:
            print("\n========== PEDIDO RECUSADO ==========")
            print(f"Motivo: {mensagem}")
            conexao.rollback()
            return False

        # Motor de pedidos: calcular valor da venda
        valor_total = calcular_valor_pedido(
            produto["preco"], quantidade, taxa_entrega
        )

        # Motor de receitas: calcular custo de produção
        custo_unitario = calcular_custo_receita(produto_id)
        custo_total = round(custo_unitario * quantidade, 2)

        # Registrar data e horário
        data_hora = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Cadastrar pedido aprovado
        cursor.execute("""
            INSERT INTO pedidos (
                cliente,
                produto_id,
                quantidade,
                valor_total,
                custo_total,
                forma_pagamento,
                tipo_entrega,
                bairro,
                taxa_entrega,
                status,
                data_hora
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente,
            produto_id,
            quantidade,
            valor_total,
            custo_total,
            forma_pagamento,
            tipo_entrega,
            bairro,
            taxa_entrega,
            "aprovado",
            data_hora
        ))

        pedido_id = cursor.lastrowid

        # Motor de receitas: descontar ingredientes
        # e registrar movimentações
        consumir_estoque_receita(
            cursor,
            produto_id,
            quantidade,
            data_hora
        )

        # Confirmar todas as operações
        conexao.commit()

        print("\n========== PEDIDO APROVADO ==========")
        print(f"ID: #PED{pedido_id:03d}")
        print(f"Cliente: {cliente}")
        print(f"Produto: {produto['nome']}")
        print(f"Categoria: {produto['categoria']}")
        print(f"Quantidade: {quantidade}")
        print(f"Valor total: R$ {valor_total:.2f}")
        print(f"Custo de produção: R$ {custo_total:.2f}")
        print(f"Pagamento: {forma_pagamento}")
        print(f"Tipo de entrega: {tipo_entrega}")
        print(f"Bairro: {bairro or 'Não se aplica'}")
        print(f"Taxa de entrega: R$ {taxa_entrega:.2f}")
        print(f"Data e horário: {data_hora}")
        print("\nEstoque atualizado automaticamente!")

        return True

    except (sqlite3.Error, ValueError, OverflowError) as erro:
        conexao.rollback()
        print(f"Erro ao processar pedido: {erro}")
        return False

    finally:
        conexao.close()

# Registrar novo pedido

def registrar_pedido():
    print("\n========== REGISTRAR PEDIDO ==========")

    try:
        if not consultar_cardapio():
            return False

        # Informações do cliente e do produto
        cliente = input("\nNome do cliente: ").strip()
        produto_id = int(input("ID numérico do produto: ").strip())
        quantidade = int(input("Quantidade: ").strip())

        # Forma de pagamento
        print("\nFormas de pagamento:")
        print("Pix | Dinheiro | Crédito | Débito")

        forma_pagamento = input(
            "Forma de pagamento: "
        ).strip().lower()

        # Tipo de entrega
        print("\nTipos de entrega:")
        print("Entrega | Retirada")

        tipo_entrega = input(
            "Tipo de entrega: "
        ).strip().lower()

        bairro = None
        taxa_entrega = 0.0

        if tipo_entrega == "entrega":
            bairro = input("Bairro: ").strip()

            taxa_entrega = float(
                input("Taxa de entrega: R$ ")
                .strip().replace(",", ".")
            )

        # Motor de validação
        validar_pedido(
            cliente,
            produto_id,
            quantidade,
            forma_pagamento,
            tipo_entrega,
            bairro,
            taxa_entrega
        )

        taxa_entrega = round(taxa_entrega, 2)

        # Motor de aprovação automática
        return aprovar_pedido(
            cliente,
            produto_id,
            quantidade,
            forma_pagamento,
            tipo_entrega,
            bairro,
            taxa_entrega
        )

    except (ValueError, OverflowError) as erro:
        print(f"Dados inválidos: {erro}")
        return False

    except sqlite3.Error as erro:
        print(f"Erro no banco de dados: {erro}")
        return False

def menu_pedidos():
    while True:
        print("\nVocê está na aba pedidos!")
        print("1 - Registrar pedidos")
        print("0 - Voltar")

        opcao = input("Escolha sua opção: ").strip()

        if opcao == "1":
            registrar_pedido()
        elif opcao == "0":
            print("Saindo da aba receitas...")
            break
        else:
            print("Opção inválida.")