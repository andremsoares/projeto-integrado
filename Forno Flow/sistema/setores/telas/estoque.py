import sqlite3
from datetime import datetime
from banco import conectar

horario = datetime.now().strftime("%H:%M")

# garantir com que os pedidos possam ser feitos somente com o que tem no estoque, passando por uma conferência no banco de dados para validar o pedido

#cadastro de item no estoque

def cadastrar_estoque():
    print("\n--- CADASTRAR INGREDIENTE ---")
    conexao = conectar()
    try:
        cursor = conexao.cursor()

        ingrediente = input("Digite o nome do ingrediente: ").strip()
        unidade = input("Digite a unidade de medida (g, ml, un, l, kg): ").strip().lower()
        quantidade = float(input("Digite a quantidade disponível: ").replace(",", "."))
        custo_unitario = float(input("Digite o custo unitário: ").replace(",", "."))
        estoque_minimo = float(input("Digite a quantidade mínima de estoque: ").replace(",", "."))
        estoque_ideal = float(input("Digite a quantidade ideal de estoque: ").replace(",", "."))

        cursor.execute("""
            INSERT INTO estoque (ingrediente, unidade, quantidade, custo_unitario, estoque_minimo, estoque_ideal)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ingrediente, unidade, quantidade, custo_unitario, estoque_minimo, estoque_ideal))

        ingrediente_id = cursor.lastrowid

        if quantidade > 0:
            agora = horario
            custo_total = round(quantidade * custo_unitario, 2)
            cursor.execute("""
                INSERT INTO movimentacoes_estoque (ingrediente_id, tipo, quantidade, custo_total, data_hora)
                VALUES (?, 'entrada', ?, ?, ?)
            """, (ingrediente_id, quantidade, custo_total, agora))

        conexao.commit()
        print(f"Ingrediente '{ingrediente.capitalize()}' cadastrado com sucesso no estoque!")
    except ValueError:
        conexao.rollback()
        print("Erro: digite apenas números válidos para quantidade e valores.")
    except sqlite3.IntegrityError as erro:
        conexao.rollback()
        print(f"Erro ao salvar no banco (verifique se o nome já existe, se a unidade é válida ou se o estoque ideal é maior que o mínimo): {erro}")
    finally:
        conexao.close()

# calculo de status de estoque

def calcular_status_estoque(quantidade, estoque_minimo, estoque_ideal):

    if quantidade is None:
        return "Não informado"
    if quantidade == 0:
        return "Fora de estoque"
    if estoque_minimo is None or estoque_ideal is None:
        return "Não informado"
    if quantidade >= estoque_ideal:
        return "Estoque ideal"
    elif quantidade <= estoque_minimo:
        return "Estoque crítico"

    porcentagem = (quantidade - estoque_minimo) / (estoque_ideal - estoque_minimo) * 100

    if porcentagem >= 50:
        return "Estoque médio"
    else:
        return "Estoque baixo"

# consulta o estoque

def consultar_estoque(nome="", prioridade=""):
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id, ingrediente, unidade, quantidade,
                   custo_unitario, estoque_minimo, estoque_ideal
            FROM estoque
            ORDER BY ingrediente ASC
        """)
        ingredientes = cursor.fetchall()
    finally:
        conexao.close()

    print("\n========== INGREDIENTES E ESTOQUE ==========")
    print("ID | Ingrediente | Custo Unit. | Estoque | Status")

    if not ingredientes:
        print("Nenhum item cadastrado.")
        return

    encontrados = 0  # NOVO

    for registro in ingredientes:
        id_ingrediente = registro["id"]
        ingrediente = registro["ingrediente"]
        unidade = registro["unidade"]
        quantidade = registro["quantidade"]
        custo_unitario = registro["custo_unitario"]
        estoque_minimo = registro["estoque_minimo"]
        estoque_ideal = registro["estoque_ideal"]

        # NOVO: filtro por nome
        if nome and nome not in ingrediente.lower():
            continue

        codigo = f"#ING{id_ingrediente:03d}"

        if custo_unitario is None:
            preco = "Não informado"
        else:
            preco = f"R$ {custo_unitario:.2f}"

        if quantidade is None:
            estoque_atual = "Não informado"
        elif unidade is None or unidade == "":
            estoque_atual = f"{quantidade:g} (sem unidade)"
        else:
            estoque_atual = f"{quantidade:g} {unidade}"

        status = calcular_status_estoque(quantidade, estoque_minimo, estoque_ideal)

        # NOVO: filtro por status
        if prioridade and prioridade not in status.lower():
            continue

        print(f"{codigo} | {ingrediente.capitalize()} | {preco} | {estoque_atual} | {status}")

        encontrados += 1  # NOVO

    # NOVO: caso nenhum ingrediente passe pelos filtros
    if encontrados == 0:
        print("Nenhum ingrediente corresponde aos filtros.")

# busca por prioridade

def prioridade_estoque():
    print("\n--- PESQUISAR ESTOQUE ---")
    print("Pressione ENTER para ignorar um filtro.")

    nome = input("Nome do ingrediente: ").strip().lower()
    prioridade = input("Status do estoque: ").strip().lower()

    consultar_estoque(nome, prioridade)

# modificar estoque

def editar_estoque():
    print("\n--- EDITAR INGREDIENTE ---")
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT id, ingrediente, quantidade, unidade FROM estoque ORDER BY id ASC")
        itens = cursor.fetchall()

        if not itens:
            print("Nenhum ingrediente cadastrado para editar.")
            return

        for item in itens:
            print(f"{item['id']} - {item['ingrediente']} ({item['quantidade']:g} {item['unidade']})")

        id_ingrediente = int(input("\nDigite o ID do ingrediente que deseja editar: ").strip())

        cursor.execute("""
            SELECT id, ingrediente, unidade, quantidade,
                   custo_unitario, estoque_minimo, estoque_ideal
            FROM estoque
            WHERE id = ?
        """, (id_ingrediente,))
        registro = cursor.fetchone()

        if not registro:
            print("Ingrediente não encontrado.")
            return

        print("\nPressione ENTER para manter o valor atual.")

        novo_nome = input(f"Nome [{registro['ingrediente']}]: ").strip() or registro["ingrediente"]
        nova_unidade = input(f"Unidade (g, ml, un, l, kg) [{registro['unidade']}]: ").strip().lower() or registro["unidade"]

        entrada_quantidade = input(f"Quantidade [{registro['quantidade']:g}]: ").strip()
        nova_quantidade = float(entrada_quantidade.replace(",", ".")) if entrada_quantidade else registro["quantidade"]

        entrada_custo = input(f"Custo unitário [R$ {registro['custo_unitario']:.2f}]: ").strip()
        novo_custo = float(entrada_custo.replace(",", ".")) if entrada_custo else registro["custo_unitario"]

        entrada_min = input(f"Estoque mínimo [{registro['estoque_minimo']:g}]: ").strip()
        novo_min = float(entrada_min.replace(",", ".")) if entrada_min else registro["estoque_minimo"]

        entrada_ideal = input(f"Estoque ideal [{registro['estoque_ideal']:g}]: ").strip()
        novo_ideal = float(entrada_ideal.replace(",", ".")) if entrada_ideal else registro["estoque_ideal"]

        cursor.execute("""
            UPDATE estoque
            SET ingrediente = ?,
                unidade = ?,
                quantidade = ?,
                custo_unitario = ?,
                estoque_minimo = ?,
                estoque_ideal = ?
            WHERE id = ?
        """, (novo_nome, nova_unidade, nova_quantidade, novo_custo, novo_min, novo_ideal, id_ingrediente))

        if nova_quantidade != registro["quantidade"]:
            diferenca = abs(nova_quantidade - registro["quantidade"])
            custo_diferenca = round(diferenca * novo_custo, 2)
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO movimentacoes_estoque (ingrediente_id, tipo, quantidade, custo_total, data_hora)
                VALUES (?, 'ajuste', ?, ?, ?)
            """, (id_ingrediente, diferenca, custo_diferenca, agora))

        conexao.commit()

        novo_status = calcular_status_estoque(nova_quantidade, novo_min, novo_ideal)
        print(f"\nIngrediente '{novo_nome.capitalize()}' atualizado com sucesso!")
        print(f"Saldo atual: {nova_quantidade:g} {nova_unidade} | Status: {novo_status}")

    except ValueError:
        conexao.rollback()
        print("Erro: digite apenas números válidos para ID, quantidade e valores.")
    except sqlite3.IntegrityError as erro:
        conexao.rollback()
        print(f"Erro ao atualizar no banco (verifique nome duplicado, unidade válida ou estoque ideal >= mínimo): {erro}")
    finally:
        conexao.close()

# registrar compra

def registrar_compra():
    print("\n--- REGISTRAR COMPRA / REPOSIÇÃO ---")
    conexao = conectar()
    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT id, ingrediente, quantidade, unidade, custo_unitario
            FROM estoque
            ORDER BY ingrediente ASC
        """)
        itens = cursor.fetchall()

        if not itens:
            print("Nenhum ingrediente cadastrado. Cadastre o item antes de registrar uma compra.")
            return

        for item in itens:
            print(f"{item['id']} - {item['ingrediente']} (Atual: {item['quantidade']:g} {item['unidade']} | Custo: R$ {item['custo_unitario']:.2f})")

        id_ingrediente = int(input("\nDigite o ID do ingrediente comprado: ").strip())

        cursor.execute("""
            SELECT id, ingrediente, unidade, quantidade,
                   custo_unitario, estoque_minimo, estoque_ideal
            FROM estoque
            WHERE id = ?
        """, (id_ingrediente,))
        registro = cursor.fetchone()

        if not registro:
            print("Ingrediente não encontrado.")
            return

        quantidade_comprada = float(input(f"Quantidade comprada (em {registro['unidade']}): ").replace(",", "."))

        if quantidade_comprada <= 0:
            print("Erro: a quantidade comprada deve ser maior que zero.")
            return

        entrada_custo = input(f"Novo custo unitário [ENTER para manter R$ {registro['custo_unitario']:.2f}]: ").strip()
        novo_custo = float(entrada_custo.replace(",", ".")) if entrada_custo else registro["custo_unitario"]

        nova_quantidade_total = registro["quantidade"] + quantidade_comprada
        custo_total_compra = round(quantidade_comprada * novo_custo, 2)
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            UPDATE estoque
            SET quantidade = ?,
                custo_unitario = ?
            WHERE id = ?
        """, (nova_quantidade_total, novo_custo, id_ingrediente))

        cursor.execute("""
            INSERT INTO movimentacoes_estoque (ingrediente_id, tipo, quantidade, custo_total, data_hora)
            VALUES (?, 'entrada', ?, ?, ?)
        """, (id_ingrediente, quantidade_comprada, custo_total_compra, agora))

        conexao.commit()

        novo_status = calcular_status_estoque(
            nova_quantidade_total,
            registro["estoque_minimo"],
            registro["estoque_ideal"]
        )
        print(f"\nCompra de '{registro['ingrediente']}' registrada com sucesso! (Total gasto: R$ {custo_total_compra:.2f})")
        print(f"Novo saldo: {nova_quantidade_total:g} {registro['unidade']} | Status: {novo_status}")

    except ValueError:
        conexao.rollback()
        print("Erro: digite apenas números válidos para ID, quantidade e valores.")
    except sqlite3.IntegrityError as erro:
        conexao.rollback()
        print(f"Erro ao registrar compra no banco: {erro}")
    finally:
        conexao.close()

# registrar perda

def registrar_perda():
    print("\n--- REGISTRAR PERDA / DESPERDÍCIO ---")
    conexao = conectar()
    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT id, ingrediente, quantidade, unidade, custo_unitario
            FROM estoque
            ORDER BY ingrediente ASC
        """)
        itens = cursor.fetchall()

        if not itens:
            print("Nenhum ingrediente cadastrado no estoque.")
            return

        for item in itens:
            print(f"{item['id']} - {item['ingrediente']} (Atual: {item['quantidade']:g} {item['unidade']} | Custo: R$ {item['custo_unitario']:.2f})")

        id_ingrediente = int(input("\nDigite o ID do ingrediente perdido: ").strip())

        cursor.execute("""
            SELECT id, ingrediente, unidade, quantidade,
                   custo_unitario, estoque_minimo, estoque_ideal
            FROM estoque
            WHERE id = ?
        """, (id_ingrediente,))
        registro = cursor.fetchone()

        if not registro:
            print("Ingrediente não encontrado.")
            return

        if registro["quantidade"] == 0:
            print(f"O ingrediente '{registro['ingrediente']}' já está com saldo zerado.")
            return

        quantidade_perdida = float(input(f"Quantidade perdida (em {registro['unidade']}): ").replace(",", "."))

        if quantidade_perdida <= 0:
            print("Erro: a quantidade perdida deve ser maior que zero.")
            return

        if quantidade_perdida > registro["quantidade"]:
            print(f"Erro: quantidade perdida ({quantidade_perdida:g} {registro['unidade']}) maior que o saldo atual ({registro['quantidade']:g} {registro['unidade']}).")
            return

        nova_quantidade_total = registro["quantidade"] - quantidade_perdida
        custo_total_perda = round(quantidade_perdida * registro["custo_unitario"], 2)
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            UPDATE estoque
            SET quantidade = ?
            WHERE id = ?
        """, (nova_quantidade_total, id_ingrediente))

        cursor.execute("""
            INSERT INTO movimentacoes_estoque (ingrediente_id, tipo, quantidade, custo_total, data_hora)
            VALUES (?, 'perda', ?, ?, ?)
        """, (id_ingrediente, quantidade_perdida, custo_total_perda, agora))

        conexao.commit()

        novo_status = calcular_status_estoque(
            nova_qtd_total,
            registro["estoque_minimo"],
            registro["estoque_ideal"]
        )
        print(f"\nPerda de '{registro['ingrediente']}' registrada com sucesso! (Prejuízo: R$ {custo_total_perda:.2f})")
        print(f"Novo saldo: {nova_quantidade_total:g} {registro['unidade']} | Status: {novo_status}")

    except ValueError:
        conexao.rollback()
        print("Erro: digite apenas números válidos para ID e quantidade.")
    except sqlite3.IntegrityError as erro:
        conexao.rollback()
        print(f"Erro ao registrar perda no banco: {erro}")
    finally:
        conexao.close()

# histórico de movimentações

def consultar_movimentacoes():
    print("\n--- HISTÓRICO DE MOVIMENTAÇÕES ---")
    print("1 - Todas as movimentações")
    print("2 - Filtrar por tipo (entrada, venda, perda, ajuste)")
    print("3 - Filtrar por ingrediente")
    filtro = input("Escolha uma opção [ENTER para todas]: ").strip()

    conexao = conectar()
    try:
        cursor = conexao.cursor()

        query_base = """
            SELECT 
                m.id,
                m.data_hora,
                e.ingrediente,
                e.unidade,
                m.tipo,
                m.quantidade,
                m.custo_total
            FROM movimentacoes_estoque m
            INNER JOIN estoque e ON m.ingrediente_id = e.id
        """

        if filtro == "2":
            print("\nTipos disponíveis: entrada | saida_venda | perda | ajuste")
            tipo_escolhido = input("Digite o tipo desejado: ").strip().lower()
            cursor.execute(
                query_base + " WHERE m.tipo = ? ORDER BY m.data_hora DESC, m.id DESC",
                (tipo_escolhido,)
            )
        elif filtro == "3":
            cursor.execute("SELECT id, ingrediente FROM estoque ORDER BY ingrediente ASC")
            itens = cursor.fetchall()

            if not itens:
                print("Nenhum ingrediente cadastrado.")
                return

            for item in itens:
                print(f"{item['id']} - {item['ingrediente']}")

            id_ingrediente = int(input("\nDigite o ID do ingrediente: ").strip())
            cursor.execute(
                query_base + " WHERE m.ingrediente_id = ? ORDER BY m.data_hora DESC, m.id DESC",
                (id_ingrediente,)
            )
        else:
            cursor.execute(query_base + " ORDER BY m.data_hora DESC, m.id DESC")

        movimentacoes = cursor.fetchall()

    except ValueError:
        print("Erro: digite apenas números válidos para o ID.")
        return
    finally:
        conexao.close()

    print("\n========== EXTRATO DO ESTOQUE ==========")
    print("ID | Data/Hora | Ingrediente | Tipo | Quantidade | Valor Total")

    if not movimentacoes:
        print("Nenhuma movimentação encontrada.")
        return

    nomes_tipos = {
        "entrada": "Entrada",
        "saida_venda": "Saída (Venda)",
        "perda": "Perda",
        "ajuste": "Ajuste"
    }

    for mov in movimentacoes:
        codigo = f"#MOV{mov['id']:03d}"
        tipo_formatado = nomes_tipos.get(mov["tipo"], mov["tipo"])
        quantidade_formatada = f"{mov['quantidade']:g} {mov['unidade']}"
        valor_formatado = f"R$ {mov['custo_total']:.2f}"

        print(f"{codigo} | {mov['data_hora']} | {mov['ingrediente']} | {tipo_formatado} | {quantidade_formatada} | {valor_formatado}")

# desativar ingrediente

def desativar_ingrediente():
    print("\n--- DESATIVAR INGREDIENTE ---")
    conexao = conectar()
    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT id, ingrediente, quantidade, unidade, custo_unitario
            FROM estoque
            WHERE ativo = 1
            ORDER BY ingrediente ASC
        """)
        itens = cursor.fetchall()

        if not itens:
            print("Nenhum ingrediente ativo no estoque.")
            return

        for item in itens:
            print(f"{item['id']} - {item['ingrediente']} (Saldo: {item['quantidade']:g} {item['unidade']})")

        id_ingrediente = int(input("\nDigite o ID do ingrediente que deseja desativar: ").strip())

        cursor.execute("""
            SELECT id, ingrediente, quantidade, unidade, custo_unitario
            FROM estoque
            WHERE id = ? AND ativo = 1
        """, (id_ingrediente,))
        registro = cursor.fetchone()

        if not registro:
            print("Ingrediente não encontrado ou já está desativado.")
            return

        if registro["quantidade"] > 0:
            valor_parado = round(registro["quantidade"] * registro["custo_unitario"], 2)
            print(f"\nAtenção: ainda restam {registro['quantidade']:g} {registro['unidade']} de '{registro['ingrediente']}' (R$ {valor_parado:.2f}) no estoque.")
            print("Dica: se esse saldo foi descartado, registre como 'perda' antes para contabilizar no financeiro.")

        confirmacao = input(f"Tem certeza que deseja desativar '{registro['ingrediente']}'? (s/n): ").strip().lower()

        if confirmacao != "s":
            print("Operação cancelada.")
            return

        cursor.execute("""
            UPDATE estoque
            SET ativo = 0
            WHERE id = ?
        """, (id_ingrediente,))

        conexao.commit()
        print(f"\nIngrediente '{registro['ingrediente']}' desativado com sucesso!")
        print("Ele não aparecerá mais na rotina da cozinha, mas todo o histórico financeiro foi mantido.")

    except ValueError:
        conexao.rollback()
        print("Erro: digite apenas números válidos para o ID.")
    except sqlite3.IntegrityError as erro:
        conexao.rollback()
        print(f"Erro ao desativar ingrediente no banco: {erro}")
    finally:
        conexao.close()

# lista de reposição

def lista_reposicao():
    conexao = conectar()
    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT id, ingrediente, unidade, quantidade,
                   custo_unitario, estoque_minimo, estoque_ideal
            FROM estoque
            ORDER BY ingrediente ASC
        """)

        ingredientes = cursor.fetchall()

    finally:
        conexao.close()

    if not ingredientes:
        print("Nenhum ingrediente cadastrado.")
        return

    reposicoes = []

    for registro in ingredientes:
        id_ingrediente = registro["id"]
        ingrediente = registro["ingrediente"]
        unidade = registro["unidade"]
        quantidade = registro["quantidade"]
        custo_unitario = registro["custo_unitario"]
        estoque_minimo = registro["estoque_minimo"]
        estoque_ideal = registro["estoque_ideal"]

        if quantidade >= estoque_ideal:
            continue

        quantidade_reposicao = estoque_ideal - quantidade
        custo_reposicao = quantidade_reposicao * custo_unitario

        status = calcular_status_estoque(
            quantidade, estoque_minimo, estoque_ideal
        )

        reposicoes.append({
            "id": id_ingrediente,
            "ingrediente": ingrediente,
            "unidade": unidade,
            "quantidade": quantidade,
            "estoque_ideal": estoque_ideal,
            "quantidade_reposicao": quantidade_reposicao,
            "custo_unitario": custo_unitario,
            "custo_reposicao": custo_reposicao,
            "status": status
        })

    if not reposicoes:
        print("Nenhum ingrediente necessita de reposição.")
        return

    ordem_prioridade = {
        "Fora de estoque": 1,
        "Estoque crítico": 2,
        "Estoque baixo": 3,
        "Estoque médio": 4
    }

    reposicoes.sort(
        key=lambda item: ordem_prioridade[item["status"]]
    )

    custo_total = 0

    for item in reposicoes:
        custo_total += item["custo_reposicao"]

    print("\n========== LISTA DE REPOSIÇÃO ==========")
    print("ID | Ingrediente | Status | Atual | Ideal | Repor | Custo Unit. | Custo Reposição")

    for item in reposicoes:
        codigo = f"#ING{item['id']:03d}"
        ingrediente = item["ingrediente"].capitalize()
        unidade = item["unidade"]
        status = item["status"]

        atual = f"{item['quantidade']:g} {unidade}"
        ideal = f"{item['estoque_ideal']:g} {unidade}"
        repor = f"{item['quantidade_reposicao']:g} {unidade}"

        preco_unitario = f"R$ {item['custo_unitario']:.2f}/{unidade}"
        preco_total = f"R$ {item['custo_reposicao']:.2f}"

        print(f"{codigo} | {ingrediente} | {status} | {atual} | {ideal} | {repor} | {preco_unitario} | {preco_total}")

    print("\n========================================")
    print(f"Ingredientes a repor: {len(reposicoes)}")
    print(f"Custo total estimado: R$ {custo_total:.2f}")
    print("========================================") 
            

    print("\n--- LISTA DE REPOSIÇÃO / COMPRAS ---")
    print("1 - Todos os itens abaixo do estoque ideal")
    print("2 - Apenas itens urgentes (Fora de estoque ou Crítico)")
    filtro = input("Escolha uma opção [ENTER para todos abaixo do ideal]: ").strip()

    conexao = conectar()
    try:
        cursor = conexao.cursor()

        if filtro == "2":
            condicao = "ativo = 1 AND quantidade <= estoque_minimo"
            titulo = "LISTA DE REPOSIÇÃO URGENTE"
        else:
            condicao = "ativo = 1 AND quantidade < estoque_ideal"
            titulo = "LISTA DE REPOSIÇÃO (ABAIXO DO IDEAL)"

        cursor.execute(f"""
            SELECT id, ingrediente, unidade, quantidade,
                   custo_unitario, estoque_minimo, estoque_ideal
            FROM estoque
            WHERE {condicao}
            ORDER BY (quantidade / estoque_ideal) ASC, ingrediente ASC
        """)
        itens = cursor.fetchall()
    finally:
        conexao.close()

    print(f"\n========== {titulo} ==========")
    print("ID | Ingrediente | Atual | Ideal | Comprar | Status | Custo Est.")

    if not itens:
        print("Nenhum ingrediente precisando de reposição no momento.")
        return

    custo_total_geral = 0.0

    for item in itens:
        codigo = f"#ING{item['id']:03d}"
        unidade = item["unidade"]
        quantidade_atual = item["quantidade"]
        quantidade_ideal = item["estoque_ideal"]

        quantidade_repor = round(quantidade_ideal - quantidade_atual, 3)
        custo_estimado = round(quantidade_repor * item["custo_unitario"], 2)
        custo_total_geral += custo_estimado

        status = calcular_status_estoque(quantidade_atual, item["estoque_minimo"], quantidade_ideal)

        atual_fmt = f"{quantidade_atual:g} {unidade}"
        ideal_fmt = f"{quantidade_ideal:g} {unidade}"
        comprar_fmt = f"{quantidade_repor:g} {unidade}"
        custo_fmt = f"R$ {custo_estimado:.2f}"

        print(f"{codigo} | {item['ingrediente']} | {atual_fmt} | {ideal_fmt} | {comprar_fmt} | {status} | {custo_fmt}")

    print("-" * 75)
    print(f"Total de itens para compra: {len(itens)} | Orçamento estimado: R$ {custo_total_geral:.2f}")

def menu_estoque():
    while True:
        print("\nVocê está na aba estoque!")
        print("1 - Cadastrar ingrediente")
        print("2 - Consultar estoque")
        print("3 - Consulta por prioridade")
        print("4 - Consultar movimentações")
        print("5 - Lista de reposição")
        print("6 - Editar estoque")
        print("7 - Registrar compra")
        print("8 - Registrar perda")
        print("9 - Desativar ingrediente")
        print("0 - Voltar para a aba cozinha")
        opcao = input("Escolha sua opção: ").strip()

        if opcao == "1":
            cadastrar_estoque()
        elif opcao == "2":
            consultar_estoque()
        elif opcao == "3":
            prioridade_estoque()
        elif opcao == "4":
            consultar_movimentacoes()
        elif opcao == "5":
            lista_reposicao()
        elif opcao == "6":
            editar_estoque()
        elif opcao == "7":
            registrar_compra()
        elif opcao == "8":
            registrar_perda()
        elif opcao == "9":
            desativar_ingrediente()
        elif opcao == "0":
            print("Saindo da aba estoque...")
            break
        else:
            print("Opção inválida.")