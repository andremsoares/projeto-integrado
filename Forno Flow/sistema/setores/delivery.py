import sqlite3
from banco import conectar
from setores.telas.pedidos import (
    liberar_entrega_motor,
    concluir_entrega_com_codigo_motor
)

# buscar entregas (fila ativa ou histórico, com filtro opcional por bairro)

def buscar_entregas(apenas_ativas=True, bairro=""):
    conexao = conectar()
    try:
        cursor = conexao.cursor()

        if apenas_ativas:
            status_filtro = "('aprovado', 'em preparo', 'saiu para entrega')"
            ordem = "ORDER BY p.id ASC"
        else:
            status_filtro = "('concluido', 'cancelado')"
            ordem = "ORDER BY p.id DESC"

        query = f"""
            SELECT p.id,
                   p.cliente,
                   GROUP_CONCAT(ip.quantidade || 'x ' || pr.nome, ', ') AS itens_resumo,
                   p.valor_total,
                   p.taxa_entrega,
                   p.forma_pagamento,
                   p.bairro,
                   p.status,
                   p.codigo_confirmacao,
                   p.data_hora
            FROM pedidos p
            INNER JOIN itens_pedido ip ON p.id = ip.pedido_id
            INNER JOIN produtos pr ON ip.produto_id = pr.id
            WHERE p.tipo_entrega = 'entrega'
              AND p.status IN {status_filtro}
        """
        parametros = []

        if bairro:
            query += " AND LOWER(p.bairro) LIKE ?"
            parametros.append(f"%{bairro.lower()}%")

        query += f" GROUP BY p.id {ordem}"
        cursor.execute(query, parametros)
        return cursor.fetchall()
    finally:
        conexao.close()

# função auxiliar para imprimir os dados da entrega

def exibir_entregas(entregas):
    for item in entregas:
        print(
            f"ID {item['id']} (#PED{item['id']:03d}) | {item['status'].upper()} | "
            f"Bairro: {item['bairro']} | Cliente: {item['cliente']} | "
            f"{item['itens_resumo']} | "
            f"Total: R$ {item['valor_total']:.2f} (Taxa: R$ {item['taxa_entrega']:.2f} | "
            f"{item['forma_pagamento']}) | {item['data_hora']}"
        )

# tela 1: visualizar a fila de entregas dividida por etapa

def consultar_fila_entregas():
    print("\n========== FILA DE ENTREGAS ==========")
    entregas = buscar_entregas(apenas_ativas=True)

    if not entregas:
        print("Nenhuma entrega pendente ou em rota no momento.")
        return

    em_rota = [e for e in entregas if e["status"] == "saiu para entrega"]
    aguardando_delivery = [e for e in entregas if e["status"] == "em preparo"]
    aguardando_cozinha = [e for e in entregas if e["status"] == "aprovado"]

    print("\n--- EM ROTA (SAIU PARA ENTREGA) ---")
    if em_rota:
        exibir_entregas(em_rota)
    else:
        print("Nenhum pedido na rua no momento.")

    print("\n--- AGUARDANDO APROVAÇÃO DO DELIVERY (EM PREPARO) ---")
    if aguardando_delivery:
        exibir_entregas(aguardando_delivery)
    else:
        print("Nenhum pedido aguardando saída para entrega.")

    print("\n--- AGUARDANDO INÍCIO NA COZINHA (APROVADO) ---")
    if aguardando_cozinha:
        exibir_entregas(aguardando_cozinha)
    else:
        print("Nenhum pedido aguardando início na cozinha.")

# tela 2: aprovar entrega (muda para 'saiu para entrega' e gera código do cliente)

def aprovar_entrega():
    print("\n========== APROVAR / LIBERAR ENTREGA ==========")
    entregas = buscar_entregas(apenas_ativas=True)
    prontos = [e for e in entregas if e["status"] == "em preparo"]

    if not prontos:
        print("Nenhum pedido 'em preparo' aguardando aprovação de entrega.")
        print("(A cozinha precisa primeiro alterar o pedido de 'aprovado' para 'em preparo'.)")
        return

    exibir_entregas(prontos)

    try:
        pedido_id = int(
            input("\nDigite o ID numérico do pedido para aprovar a entrega (ou 0 para voltar): ").strip()
        )
    except ValueError:
        print("Erro: Digite um número de ID válido.")
        return

    if pedido_id == 0:
        print("Operação cancelada.")
        return

    ids_prontos = {e["id"] for e in prontos}
    if pedido_id not in ids_prontos:
        print("Erro: Este pedido não está na lista de pedidos aguardando aprovação.")
        return

    sucesso, resultado = liberar_entrega_motor(pedido_id)

    if sucesso:
        print(f"\nEntrega do pedido #PED{pedido_id:03d} aprovada! Status: SAIU PARA ENTREGA.")
        print("==================================================")
        print(f"CÓDIGO DE CONFIRMAÇÃO DO CLIENTE: {resultado}")
        print("==================================================")
        print("Use este código na opção 'Concluir Entrega' para finalizar o pedido.")
    else:
        print(f"Erro: {resultado}")

# tela 3: concluir entrega validando o código de aprovação do cliente

def confirmar_entrega():
    print("\n========== CONCLUIR ENTREGA (COM CÓDIGO) ==========")
    entregas = buscar_entregas(apenas_ativas=True)
    em_rota = [e for e in entregas if e["status"] == "saiu para entrega"]

    if not em_rota:
        print("Nenhum pedido com status 'saiu para entrega' para concluir.")
        return

    exibir_entregas(em_rota)

    try:
        pedido_id = int(
            input("\nDigite o ID numérico do pedido entregue (ou 0 para voltar): ").strip()
        )
    except ValueError:
        print("Erro: Digite um número de ID válido.")
        return

    if pedido_id == 0:
        print("Operação cancelada.")
        return

    ids_em_rota = {e["id"] for e in em_rota}
    if pedido_id not in ids_em_rota:
        print("Erro: Este pedido não está na lista de 'saiu para entrega'.")
        return

    codigo = input("Digite o código de confirmação fornecido pelo cliente: ").strip()

    sucesso, resultado = concluir_entrega_com_codigo_motor(pedido_id, codigo)

    if sucesso:
        print(
            f"\nCódigo validado! Entrega do pedido #PED{pedido_id:03d} concluída ({resultado.upper()}). "
            "Pedido finalizado automaticamente no sistema."
        )
    else:
        print(f"\nErro: {resultado}")

# tela 4: histórico de entregas concluídas/canceladas e soma das taxas

def historico_entregas():
    print("\n========== HISTÓRICO DE ENTREGAS E TAXAS ==========")
    historico = buscar_entregas(apenas_ativas=False)

    if not historico:
        print("Nenhuma entrega concluída ou cancelada até o momento.")
        return

    exibir_entregas(historico)

    concluidas = [e for e in historico if e["status"] == "concluido"]
    total_taxas = sum(e["taxa_entrega"] for e in concluidas)
    total_pedidos = sum(e["valor_total"] for e in concluidas)

    print("-" * 75)
    print(
        f"Entregas concluídas: {len(concluidas)} | "
        f"Total arrecadado: R$ {total_pedidos:.2f} | "
        f"Total em taxas de entrega: R$ {total_taxas:.2f}"
    )

def menu_delivery():
    while True:
        print("\n========== ABA DELIVERY ==========")
        print("1 - Fila de Entregas")
        print("2 - Aprovar / Liberar Entrega (Gerar Código)")
        print("3 - Concluir Entrega (Validar Código)")
        print("4 - Histórico de Entregas e Taxas")
        print("0 - Voltar")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            consultar_fila_entregas()
        elif opcao == "2":
            aprovar_entrega()
        elif opcao == "3":
            confirmar_entrega()
        elif opcao == "4":
            historico_entregas()
        elif opcao == "0":
            print("Encerrando sessão do delivery...")
            break
        else:
            print("Opção inválida. Tente novamente.")