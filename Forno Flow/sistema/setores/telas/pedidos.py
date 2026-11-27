import sqlite3
import math
from datetime import datetime
from banco import conectar
from setores.telas.receitas import (
    calcular_custo_receita,
    verificar_disponibilidade,
    consumir_estoque_receita,
    listar_produtos_ativos,
    estornar_estoque_receita
)


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

        # Iniciar transação atômica
        cursor.execute("BEGIN IMMEDIATE")

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

        # Motor de receitas usando o mesmo cursor da transação
        disponivel, mensagem = verificar_disponibilidade(
            produto_id, quantidade, cursor=cursor
        )

        if not disponivel:
            print("\n========== PEDIDO RECUSADO ==========")
            print(f"Motivo: {mensagem}")
            conexao.rollback()
            return False

        valor_total = calcular_valor_pedido(
            produto["preco"], quantidade, taxa_entrega
        )

        custo_unitario = calcular_custo_receita(produto_id, cursor=cursor)
        custo_total = round(custo_unitario * quantidade, 2)

        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

        consumir_estoque_receita(
            cursor,
            produto_id,
            quantidade,
            data_hora
        )

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


# listar pedidos (fila ativa ou histórico)

def listar_pedidos(apenas_ativos=True):
    conexao = conectar()
    try:
        cursor = conexao.cursor()

        if apenas_ativos:
            cursor.execute("""
                SELECT p.id,
                       p.cliente,
                       pr.nome AS produto_nome,
                       p.quantidade,
                       p.valor_total,
                       p.forma_pagamento,
                       p.tipo_entrega,
                       p.bairro,
                       p.status,
                       p.data_hora
                FROM pedidos p
                INNER JOIN produtos pr ON p.produto_id = pr.id
                WHERE p.status IN ('aprovado', 'em preparo', 'saiu para entrega')
                ORDER BY p.id ASC
            """)
        else:
            cursor.execute("""
                SELECT p.id,
                       p.cliente,
                       pr.nome AS produto_nome,
                       p.quantidade,
                       p.valor_total,
                       p.forma_pagamento,
                       p.tipo_entrega,
                       p.bairro,
                       p.status,
                       p.data_hora
                FROM pedidos p
                INNER JOIN produtos pr ON p.produto_id = pr.id
                WHERE p.status IN ('concluido', 'cancelado')
                ORDER BY p.id DESC
            """)

        return cursor.fetchall()
    finally:
        conexao.close()


# avançar status do pedido

def avancar_status_motor(pedido_id):
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT status, tipo_entrega
            FROM pedidos
            WHERE id = ?
        """, (pedido_id,))
        pedido = cursor.fetchone()

        if not pedido:
            return False, "Pedido não encontrado."

        status_atual = pedido["status"]
        tipo_entrega = pedido["tipo_entrega"]

        if status_atual == "aprovado":
            novo_status = "em preparo"
        elif status_atual == "em preparo":
            novo_status = "saiu para entrega" if tipo_entrega == "entrega" else "concluido"
        elif status_atual == "saiu para entrega":
            novo_status = "concluido"
        else:
            return False, f"Pedido já está '{status_atual}' e não pode avançar."

        cursor.execute("""
            UPDATE pedidos
            SET status = ?
            WHERE id = ?
        """, (novo_status, pedido_id))
        conexao.commit()

        return True, novo_status

    except sqlite3.Error as erro:
        conexao.rollback()
        return False, f"Erro no banco de dados: {erro}"
    finally:
        conexao.close()


# cancelar pedido com estorno condicional

def cancelar_pedido_motor(pedido_id):
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            SELECT produto_id, quantidade, status
            FROM pedidos
            WHERE id = ?
        """, (pedido_id,))
        pedido = cursor.fetchone()

        if not pedido:
            conexao.rollback()
            return False, "Pedido não encontrado."

        status_atual = pedido["status"]

        if status_atual in ("concluido", "cancelado"):
            conexao.rollback()
            return False, f"Não é possível cancelar um pedido já '{status_atual}'."

        cursor.execute("""
            UPDATE pedidos
            SET status = 'cancelado'
            WHERE id = ?
        """, (pedido_id,))

        if status_atual == "aprovado":
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            estornar_estoque_receita(
                cursor,
                pedido["produto_id"],
                pedido["quantidade"],
                data_hora
            )
            mensagem = "Pedido cancelado e insumos devolvidos ao estoque."
        else:
            mensagem = (
                f"Pedido cancelado (estava '{status_atual}'). "
                "Insumos não estornados pois já entraram em produção."
            )

        conexao.commit()
        return True, mensagem

    except sqlite3.Error as erro:
        conexao.rollback()
        return False, f"Erro no banco de dados: {erro}"
    finally:
        conexao.close()


# registrar novo pedido

def registrar_pedido():
    print("\n========== REGISTRAR PEDIDO ==========")

    try:
        if not consultar_cardapio():
            return False

        cliente = input("\nNome do cliente: ").strip()
        produto_id = int(input("ID numérico do produto: ").strip())
        quantidade = int(input("Quantidade: ").strip())

        print("\nFormas de pagamento:")
        print("Pix | Dinheiro | Crédito | Débito")

        forma_pagamento = input("Forma de pagamento: ").strip().lower()
        mapa_pagamento = {
            "pix": "pix",
            "dinheiro": "dinheiro",
            "credito": "crédito",
            "crédito": "crédito",
            "debito": "débito",
            "débito": "débito"
        }
        forma_pagamento = mapa_pagamento.get(forma_pagamento, forma_pagamento)

        print("\nTipos de entrega:")
        print("Entrega | Retirada")

        tipo_entrega = input("Tipo de entrega: ").strip().lower()

        bairro = None
        taxa_entrega = 0.0

        if tipo_entrega == "entrega":
            bairro = input("Bairro: ").strip()
            taxa_entrega = float(
                input("Taxa de entrega: R$ ").strip().replace(",", ".")
            )

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


# função auxiliar de exibição para reaproveitar nas telas

def exibir_lista_pedidos(pedidos):
    for pedido in pedidos:
        entrega = (
            f"Entrega ({pedido['bairro']})"
            if pedido["tipo_entrega"] == "entrega"
            else "Retirada"
        )
        print(
            f"ID {pedido['id']} (#PED{pedido['id']:03d}) | {pedido['status'].upper()} | "
            f"{pedido['cliente']} | {pedido['quantidade']}x {pedido['produto_nome']} | "
            f"R$ {pedido['valor_total']:.2f} ({pedido['forma_pagamento']}) | "
            f"{entrega} | {pedido['data_hora']}"
        )


# consultar fila ativa e histórico

def consultar_pedidos():
    print("\n========== FILA DE PEDIDOS ATIVOS ==========")
    ativos = listar_pedidos(apenas_ativos=True)

    if not ativos:
        print("Nenhum pedido em andamento no momento.")
    else:
        exibir_lista_pedidos(ativos)

    print("\n1 - Ver histórico (concluídos e cancelados)")
    print("0 - Voltar")
    opcao = input("Escolha uma opção: ").strip()

    if opcao == "1":
        print("\n========== HISTÓRICO DE PEDIDOS ==========")
        historico = listar_pedidos(apenas_ativos=False)

        if not historico:
            print("Nenhum pedido concluído ou cancelado até o momento.")
        else:
            exibir_lista_pedidos(historico)
    elif opcao != "0":
        print("Opção inválida.")


# avançar status do pedido

def avancar_status_pedido():
    print("\n========== AVANÇAR STATUS DO PEDIDO ==========")
    ativos = listar_pedidos(apenas_ativos=True)

    if not ativos:
        print("Nenhum pedido em andamento para avançar.")
        return

    exibir_lista_pedidos(ativos)

    try:
        pedido_id = int(
            input("\nDigite o ID numérico do pedido (ou 0 para voltar): ").strip()
        )
    except ValueError:
        print("Erro: Digite um número de ID válido.")
        return

    if pedido_id == 0:
        print("Operação cancelada.")
        return

    sucesso, resultado = avancar_status_motor(pedido_id)

    if sucesso:
        print(f"\nStatus do pedido #PED{pedido_id:03d} atualizado para: {resultado.upper()}!")
    else:
        print(f"Erro: {resultado}")


# cancelar pedido

def cancelar_pedido():
    print("\n========== CANCELAR PEDIDO ==========")
    ativos = listar_pedidos(apenas_ativos=True)

    if not ativos:
        print("Nenhum pedido ativo disponível para cancelamento.")
        return

    exibir_lista_pedidos(ativos)

    try:
        pedido_id = int(
            input("\nDigite o ID numérico do pedido para cancelar (ou 0 para voltar): ").strip()
        )
    except ValueError:
        print("Erro: Digite um número de ID válido.")
        return

    if pedido_id == 0:
        print("Operação cancelada.")
        return

    mapa_ativos = {pedido["id"]: pedido for pedido in ativos}
    if pedido_id not in mapa_ativos:
        print("Erro: Pedido não encontrado na fila ativa.")
        return

    pedido = mapa_ativos[pedido_id]

    if pedido["status"] == "aprovado":
        print("\nAviso: O pedido ainda está 'aprovado'. Os ingredientes serão devolvidos ao estoque.")
    else:
        print(
            f"\nAviso: O pedido já está '{pedido['status']}'. "
            "Os ingredientes NÃO serão estornados ao estoque."
        )

    confirmacao = input(
        f"Tem certeza que deseja cancelar o pedido #PED{pedido_id:03d} de {pedido['cliente']}? (S/N): "
    ).strip().upper()

    if confirmacao != "S":
        print("Operação cancelada.")
        return

    sucesso, mensagem = cancelar_pedido_motor(pedido_id)

    if sucesso:
        print(f"\n{mensagem}")
    else:
        print(f"Erro: {mensagem}")


def menu_pedidos():
    while True:
        print("\nVocê está na aba pedidos!")
        print("1 - Registrar pedido")
        print("2 - Consultar pedidos (Fila e Histórico)")
        print("3 - Avançar status do pedido")
        print("4 - Cancelar pedido")
        print("0 - Voltar para a aba cozinha")

        opcao = input("Escolha sua opção: ").strip()

        if opcao == "1":
            registrar_pedido()
        elif opcao == "2":
            consultar_pedidos()
        elif opcao == "3":
            avancar_status_pedido()
        elif opcao == "4":
            cancelar_pedido()
        elif opcao == "0":
            print("Saindo da aba pedidos...")
            break
        else:
            print("Opção inválida.")