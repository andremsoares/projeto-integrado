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

def consultar_estoque(nome, prioridade):
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

    for registro in ingredientes:
        id_ingrediente = registro["id"]
        ingrediente = registro["ingrediente"]
        unidade = registro["unidade"]
        quantidade = registro["quantidade"]
        custo_unitario = registro["custo_unitario"]
        estoque_minimo = registro["estoque_minimo"]
        estoque_ideal = registro["estoque_ideal"]

        codigo = f"#ING{id_ingrediente:03d}"
        preco = f"R$ {custo_unitario:.2f}"
        estoque_atual = f"{quantidade:g} {unidade}"
        status = calcular_status_estoque(quantidade, estoque_minimo, estoque_ideal)


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

        print(f"{codigo.capitalize()} | {ingrediente.capitalize()} | {preco.capitalize()} | {estoque_atual.capitalize()} | {status.capitalize()}")

#busca por prioridade

def prioridade_estoque():
    print("\n--- PESQUISAR ESTOQUE ---")
    print("Pressione ENTER para ignorar um filtro.")

    nome = input("Nome do ingrediente: ").strip().lower()
    prioridade = input("Status do estoque: ").strip().lower()


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

def menu_estoque():
    while True:
        print("\nVocê está na aba estoque!")
        print("1 - Cadastrar ingrediente")
        print("2 - Consultar estoque")
        print("3 - Editar estoque")
        print("0 - Voltar para a aba cozinha")
        opcao = input("Escolha sua opção: ").strip()

        if opcao == "1":
            cadastrar_estoque()
        elif opcao == "2":
            consultar_estoque()
        elif opcao == "3":
            editar_estoque()
        elif opcao == "0":
            print("Saindo da aba estoque...")
            break
        else:
            print("Opção inválida.")