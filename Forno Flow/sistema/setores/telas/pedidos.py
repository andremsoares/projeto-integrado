import sqlite3
import math
import random
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
        return []

    print("\n--- CARDÁPIO DISPONÍVEL ---")
    for item in cardapio:
        status = f"{item['disponivel']} un" if item["disponivel"] > 0 else "ESGOTADO"
        print(f"ID {item['id']} | {item['nome']} ({item['categoria']}) - R$ {item['preco']:.2f} | Disponível: {status}")

    return cardapio


# validar pedido

def validar_pedido(cliente, itens, forma_pagamento, tipo_entrega, bairro, taxa_entrega):
    if not cliente:
        raise ValueError("Informe o nome do cliente.")

    if not itens:
        raise ValueError("Adicione pelo menos um produto ao pedido.")

    for produto_id, quantidade in itens:
        if produto_id <= 0:
            raise ValueError("ID do produto inválido.")
        if quantidade <= 0:
            raise ValueError("A quantidade de cada produto deve ser maior que zero.")

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

def calcular_valor_pedido(subtotal, taxa_entrega=0):
    return round(subtotal + taxa_entrega, 2)


# aprovar pedido (com múltiplos produtos)

def aprovar_pedido(cliente, itens, forma_pagamento, tipo_entrega, bairro, taxa_entrega):
    conexao = conectar()

    try:
        cursor = conexao.cursor()
        cursor.execute("BEGIN IMMEDIATE")

        # Agrupa produtos repetidos no mesmo pedido
        itens_agrupados = {}
        for produto_id, quantidade in itens:
            itens_agrupados[produto_id] = itens_agrupados.get(produto_id, 0) + quantidade

        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        itens_processados = []
        subtotal = 0.0
        custo_total = 0.0

        # Valida disponibilidade e consome estoque item a item dentro da transação
        for produto_id, quantidade in itens_agrupados.items():
            cursor.execute("""
                SELECT id, nome, categoria, preco
                FROM produtos
                WHERE id = ?
                  AND ativo = 1
            """, (produto_id,))
            produto = cursor.fetchone()

            if not produto:
                print(f"Produto ID {produto_id} não encontrado ou inativo.")
                conexao.rollback()
                return False

            disponivel, mensagem = verificar_disponibilidade(
                produto_id, quantidade, cursor=cursor
            )

            if not disponivel:
                print("\n========== PEDIDO RECUSADO ==========")
                print(f"Produto: {produto['nome']} ({quantidade}x)")
                print(f"Motivo: {mensagem}")
                conexao.rollback()
                return False

            consumir_estoque_receita(cursor, produto_id, quantidade, data_hora)

            custo_unitario = calcular_custo_receita(produto_id, cursor=cursor)
            subtotal += produto["preco"] * quantidade
            custo_total += custo_unitario * quantidade

            itens_processados.append({
                "produto_id": produto_id,
                "nome": produto["nome"],
                "quantidade": quantidade,
                "preco_unitario": produto["preco"],
                "custo_unitario": custo_unitario
            })

        valor_total = calcular_valor_pedido(subtotal, taxa_entrega)
        custo_total = round(custo_total, 2)

        cursor.execute("""
            INSERT INTO pedidos (
                cliente,
                valor_total,
                custo_total,
                forma_pagamento,
                tipo_entrega,
                bairro,
                taxa_entrega,
                status,
                codigo_confirmacao,
                data_hora
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente,
            valor_total,
            custo_total,
            forma_pagamento,
            tipo_entrega,
            bairro,
            taxa_entrega,
            "aprovado",
            None,
            data_hora
        ))

        pedido_id = cursor.lastrowid

        for item in itens_processados:
            cursor.execute("""
                INSERT INTO itens_pedido (
                    pedido_id,
                    produto_id,
                    quantidade,
                    preco_unitario,
                    custo_unitario
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                pedido_id,
                item["produto_id"],
                item["quantidade"],
                item["preco_unitario"],
                item["custo_unitario"]
            ))

        conexao.commit()

        print("\n========== PEDIDO APROVADO ==========")
        print(f"ID: #PED{pedido_id:03d}")
        print(f"Cliente: {cliente}")
        print("Itens:")
        for item in itens_processados:
            total_item = item["preco_unitario"] * item["quantidade"]
            print(f"  - {item['quantidade']}x {item['nome']} (R$ {total_item:.2f})")
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
            status_filtro = "('aprovado', 'em preparo', 'saiu para entrega')"
            ordem = "ORDER BY p.id ASC"
        else:
            status_filtro = "('concluido', 'cancelado')"
            ordem = "ORDER BY p.id DESC"

        cursor.execute(f"""
            SELECT p.id,
                   p.cliente,
                   GROUP_CONCAT(ip.quantidade || 'x ' || pr.nome, ', ') AS itens_resumo,
                   p.valor_total,
                   p.forma_pagamento,
                   p.tipo_entrega,
                   p.bairro,
                   p.status,
                   p.data_hora
            FROM pedidos p
            INNER JOIN itens_pedido ip ON p.id = ip.pedido_id
            INNER JOIN produtos pr ON ip.produto_id = pr.id
            WHERE p.status IN {status_filtro}
            GROUP BY p.id
            {ordem}
        """)

        return cursor.fetchall()
    finally:
        conexao.close()


# avançar status na cozinha

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
            if tipo_entrega == "retirada":
                novo_status = "concluido"
            else:
                return False, (
                    "Este pedido é de entrega e já está em preparo. "
                    "A liberação e a conclusão devem ser feitas na aba Delivery."
                )
        elif status_atual == "saiu para entrega":
            return False, (
                "Este pedido já está em rota. "
                "A conclusão com código deve ser feita na aba Delivery."
            )
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


# motor delivery: aprovar saída para entrega e gerar código do cliente

def liberar_entrega_motor(pedido_id):
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

        if pedido["tipo_entrega"] != "entrega":
            return False, "Este pedido é de retirada e não pertence ao Delivery."

        if pedido["status"] != "em preparo":
            return False, (
                f"Não é possível liberar este pedido (status atual: '{pedido['status']}'). "
                "Ele precisa estar 'em preparo'."
            )

        codigo = f"{random.randint(1000, 9999)}"

        cursor.execute("""
            UPDATE pedidos
            SET status = 'saiu para entrega',
                codigo_confirmacao = ?
            WHERE id = ?
        """, (codigo, pedido_id))
        conexao.commit()

        return True, codigo

    except sqlite3.Error as erro:
        conexao.rollback()
        return False, f"Erro no banco de dados: {erro}"
    finally:
        conexao.close()


# motor delivery: concluir entrega validando o código do cliente

def concluir_entrega_com_codigo_motor(pedido_id, codigo_informado):
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT status, tipo_entrega, codigo_confirmacao
            FROM pedidos
            WHERE id = ?
        """, (pedido_id,))
        pedido = cursor.fetchone()

        if not pedido:
            return False, "Pedido não encontrado."

        if pedido["tipo_entrega"] != "entrega":
            return False, "Este pedido é de retirada e não pertence ao Delivery."

        if pedido["status"] != "saiu para entrega":
            return False, (
                f"Este pedido está '{pedido['status']}' e não está aguardando confirmação de entrega."
            )

        if not codigo_informado or codigo_informado.strip() != pedido["codigo_confirmacao"]:
            return False, "Código de confirmação incorreto! Entrega não concluída."

        cursor.execute("""
            UPDATE pedidos
            SET status = 'concluido'
            WHERE id = ?
        """, (pedido_id,))
        conexao.commit()

        return True, "concluido"

    except sqlite3.Error as erro:
        conexao.rollback()
        return False, f"Erro no banco de dados: {erro}"
    finally:
        conexao.close()


# cancelar pedido com estorno condicional de todos os itens

def cancelar_pedido_motor(pedido_id):
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            SELECT status
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
            cursor.execute("""
                SELECT produto_id, quantidade
                FROM itens_pedido
                WHERE pedido_id = ?
            """, (pedido_id,))
            itens = cursor.fetchall()

            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for item in itens:
                estornar_estoque_receita(
                    cursor,
                    item["produto_id"],
                    item["quantidade"],
                    data_hora
                )
            mensagem = "Pedido cancelado e insumos de todos os itens devolvidos ao estoque."
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


# registrar novo pedido (com vários produtos)

def registrar_pedido():
    print("\n========== REGISTRAR PEDIDO ==========")

    try:
        cardapio = consultar_cardapio()
        if not cardapio:
            return False

        mapa_produtos = {item["id"]: item for item in cardapio}

        cliente = input("\nNome do cliente: ").strip()
        if not cliente:
            print("Dados inválidos: Informe o nome do cliente.")
            return False

        itens = []
        while True:
            try:
                produto_id = int(input("\nID numérico do produto (ou 0 para encerrar seleção): ").strip())
            except ValueError:
                print("Digite um número de ID válido.")
                continue

            if produto_id == 0:
                if itens:
                    break
                print("Operação cancelada (nenhum produto adicionado).")
                return False

            if produto_id not in mapa_produtos:
                print("Produto não encontrado no cardápio ativo. Tente novamente.")
                continue

            try:
                quantidade = int(input(f"Quantidade de '{mapa_produtos[produto_id]['nome']}': ").strip())
            except ValueError:
                print("Digite uma quantidade válida.")
                continue

            if quantidade <= 0:
                print("A quantidade deve ser maior que zero.")
                continue

            itens.append((produto_id, quantidade))
            print(f"Adicionado ao pedido: {quantidade}x {mapa_produtos[produto_id]['nome']}")

            continuar = input("Deseja adicionar outro produto a este pedido? (S/N): ").strip().upper()
            if continuar != "S":
                break

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
            itens,
            forma_pagamento,
            tipo_entrega,
            bairro,
            taxa_entrega
        )

        taxa_entrega = round(taxa_entrega, 2)

        return aprovar_pedido(
            cliente,
            itens,
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


# função auxiliar de exibição

def exibir_lista_pedidos(pedidos):
    for pedido in pedidos:
        entrega = (
            f"Entrega ({pedido['bairro']})"
            if pedido["tipo_entrega"] == "entrega"
            else "Retirada"
        )
        print(
            f"ID {pedido['id']} (#PED{pedido['id']:03d}) | {pedido['status'].upper()} | "
            f"{pedido['cliente']} | {pedido['itens_resumo']} | "
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


# avançar status do pedido (cozinha)

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