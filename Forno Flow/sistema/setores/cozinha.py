import sqlite3
from datetime import datetime
from banco import conectar

horario = datetime.now().strftime("%H:%M")

# garantir com que os pedidos possam ser feitos somente com o que tem no estoque, passando por uma conferência no banco de dados para validar o pedido

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

def consultar_estoque():
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

def menu_cozinha():
    while True:
        print("1 - Pedidos")
        print("2 - Estoque")
        print("0 - Voltar")
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == "1":
            print("Você está na aba pedidos")
        elif opcao == "2":
            print("\nVocê está na aba estoque")
            print("1 - Cadastrar ingrediente")
            print("2 - Consultar estoque")
            opcao_estoque = input("Escolha sua opção: ").strip()

            if opcao_estoque == "1":
                cadastrar_estoque()
            elif opcao_estoque == "2":
                consultar_estoque()
            else:
                print("Opção inválida.")
        elif opcao == "0":
            break
        else:
            print("Opção inválida. Tente novamente.")