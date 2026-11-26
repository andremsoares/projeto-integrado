import sqlite3
from banco import conectar

# cálculo de custo de receita

def calcular_custo_receita(produto_id):
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT r.quantidade_necessaria, e.custo_unitario
            FROM receitas r
            INNER JOIN estoque e ON r.ingrediente_id = e.id
            WHERE r.produto_id = ?
        """, (produto_id,))
        itens = cursor.fetchall()

        if not itens:
            return 0.0

        custo_total = sum(
            item["quantidade_necessaria"] * item["custo_unitario"]
            for item in itens
        )
        return round(custo_total, 2)
    finally:
        conexao.close()
# verificar disponibilidade

def verificar_disponibilidade(produto_id, quantidade_pedida=1):
    if quantidade_pedida <= 0:
        return False, "A quantidade pedida deve ser maior que zero."

    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT nome, ativo
            FROM produtos
            WHERE id = ?
        """, (produto_id,))
        produto = cursor.fetchone()

        if not produto or produto["ativo"] == 0:
            return False, "Produto não encontrado ou inativo no cardápio."

        cursor.execute("""
            SELECT r.quantidade_necessaria,
                   e.ingrediente,
                   e.unidade,
                   e.quantidade AS saldo_atual,
                   e.ativo AS ingrediente_ativo
            FROM receitas r
            INNER JOIN estoque e ON r.ingrediente_id = e.id
            WHERE r.produto_id = ?
        """, (produto_id,))
        ingredientes = cursor.fetchall()

        if not ingredientes:
            return False, f"O produto '{produto['nome']}' não possui receita cadastrada."

        for item in ingredientes:
            if item["ingrediente_ativo"] == 0:
                return False, f"Ingrediente '{item['ingrediente']}' está desativado no estoque."

            necessario = round(item["quantidade_necessaria"] * quantidade_pedida, 4)
            if item["saldo_atual"] < necessario:
                return (
                    False,
                    f"Estoque insuficiente de '{item['ingrediente']}' "
                    f"(necessário: {necessario:g} {item['unidade']}, "
                    f"disponível: {item['saldo_atual']:g} {item['unidade']})."
                )

        return True, "OK"
    finally:
        conexao.close()

# capacidade de produção

def capacidade_producao(produto_id):
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT ativo
            FROM produtos
            WHERE id = ?
        """, (produto_id,))
        produto = cursor.fetchone()

        if not produto or produto["ativo"] == 0:
            return 0
        cursor.execute("""
            SELECT r.quantidade_necessaria,
                   e.quantidade AS saldo_atual,
                   e.ativo AS ingrediente_ativo
            FROM receitas r
            INNER JOIN estoque e ON r.ingrediente_id = e.id
            WHERE r.produto_id = ?
        """, (produto_id,))
        ingredientes = cursor.fetchall()

        if not ingredientes:
            return 0

        limites = []
        for item in ingredientes:
            if item["ingrediente_ativo"] == 0 or item["quantidade_necessaria"] <= 0:
                return 0

            unidades_possiveis = int(round(item["saldo_atual"] / item["quantidade_necessaria"], 6))
            limites.append(unidades_possiveis)

        return min(limites)
    finally:
        conexao.close()

# consumo de estoque para receita

def consumir_estoque_receita(cursor, produto_id, qtd_pedida, data_hora):
    cursor.execute("""
        SELECT r.ingrediente_id,
               r.quantidade_necessaria,
               e.custo_unitario
        FROM receitas r
        INNER JOIN estoque e ON r.ingrediente_id = e.id
        WHERE r.produto_id = ?
    """, (produto_id,))
    ingredientes = cursor.fetchall()

    for item in ingredientes:
        qtd_consumida = round(item["quantidade_necessaria"] * qtd_pedida, 4)
        custo_saida = round(qtd_consumida * item["custo_unitario"], 2)

        cursor.execute("""
            UPDATE estoque
            SET quantidade = ROUND(quantidade - ?, 4)
            WHERE id = ?
        """, (qtd_consumida, item["ingrediente_id"]))

        cursor.execute("""
            INSERT INTO movimentacoes_estoque (ingrediente_id, tipo, quantidade, custo_total, data_hora)
            VALUES (?, 'saida_venda', ?, ?, ?)
        """, (item["ingrediente_id"], qtd_consumida, custo_saida, data_hora))

# cadastrar receita

def cadastrar_receita():
    print("\n--- CADASTRAR PRODUTO E FICHA TÉCNICA ---")
    conexao = conectar()
    try:
        cursor = conexao.cursor()

        # 1. Lista os insumos ativos para facilitar a montagem da receita
        cursor.execute("""
            SELECT id, ingrediente, unidade, custo_unitario
            FROM estoque
            WHERE ativo = 1
            ORDER BY id
        """)
        insumos_disponiveis = cursor.fetchall()

        if not insumos_disponiveis:
            print("Erro: Cadastre ao menos um ingrediente ativo no estoque antes de criar uma receita.")
            return

        print("\nInsumos disponíveis no estoque:")
        for insumo in insumos_disponiveis:
            print(f"  ID {insumo['id']} | {insumo['ingrediente']} ({insumo['unidade']}) - R$ {insumo['custo_unitario']:.2f}/{insumo['unidade']}")

        # 2. Dados do produto no cardápio
        nome = input("\nNome do produto (ex: Pizza Calabresa): ").strip()
        if not nome:
            print("Erro: O nome do produto não pode ficar vazio.")
            return

        categoria = input("Categoria (ex: Pizza, Bebida, Sobremesa): ").strip()
        if not categoria:
            print("Erro: A categoria não pode ficar vazia.")
            return

        try:
            preco = float(input("Preço de venda (R$): ").replace(",", "."))
            if preco < 0:
                print("Erro: O preço não pode ser negativo.")
                return
        except ValueError:
            print("Erro: Digite um valor numérico válido para o preço.")
            return

        # 3. Insere o produto (ainda sem commit, aguardando os ingredientes)
        cursor.execute("""
            INSERT INTO produtos (nome, categoria, preco, ativo)
            VALUES (?, ?, ?, 1)
        """, (nome, categoria, round(preco, 2)))
        produto_id = cursor.lastrowid

        # 4. Loop para vincular os ingredientes da ficha técnica
        print("\n--- MONTAGEM DA RECEITA (Digite 0 no ID para finalizar) ---")
        ids_validos = {item["id"]: item for item in insumos_disponiveis}
        ingredientes_adicionados = set()

        while True:
            try:
                ing_id = int(input("\nID do ingrediente (ou 0 para concluir): "))
            except ValueError:
                print("Digite apenas o número do ID.")
                continue

            if ing_id == 0:
                if not ingredientes_adicionados:
                    print("A receita precisa ter pelo menos 1 ingrediente.")
                    continue
                break

            if ing_id not in ids_validos:
                print("ID inválido ou ingrediente desativado.")
                continue

            if ing_id in ingredientes_adicionados:
                print("Este ingrediente já foi adicionado a esta receita.")
                continue

            insumo_escolhido = ids_validos[ing_id]
            try:
                qtd_necessaria = float(
                    input(f"Quantidade de '{insumo_escolhido['ingrediente']}' por unidade ({insumo_escolhido['unidade']}): ").replace(",", ".")
                )
                if qtd_necessaria <= 0:
                    print("A quantidade deve ser maior que zero.")
                    continue
            except ValueError:
                print("Digite um número válido para a quantidade.")
                continue

            cursor.execute("""
                INSERT INTO receitas (produto_id, ingrediente_id, quantidade_necessaria)
                VALUES (?, ?, ?)
            """, (produto_id, ing_id, round(qtd_necessaria, 4)))
            ingredientes_adicionados.add(ing_id)
            print(f"  + {insumo_escolhido['ingrediente']} ({qtd_necessaria:g} {insumo_escolhido['unidade']}) adicionado.")

        # 5. Salva produto e ficha técnica juntos no banco
        conexao.commit()

        custo_producao = calcular_custo_receita(produto_id)
        lucro_bruto = round(preco - custo_producao, 2)
        print(f"\nProduto '{nome}' (ID {produto_id}) cadastrado com sucesso!")
        print(f"Custo de produção: R$ {custo_producao:.2f} | Preço: R$ {preco:.2f} | Margem bruta: R$ {lucro_bruto:.2f}")

    except sqlite3.IntegrityError:
        conexao.rollback()
        print("Erro: Já existe um produto cadastrado com esse nome.")
    except Exception as erro:
        conexao.rollback()
        print(f"Erro inesperado ao cadastrar receita: {erro}")
    finally:
        conexao.close()

# listar produtos ativos

def listar_produtos_ativos():
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id, nome, categoria, preco
            FROM produtos
            WHERE ativo = 1
            ORDER BY id
        """)
        produtos = cursor.fetchall()

        cardapio = []
        for prod in produtos:
            custo = calcular_custo_receita(prod["id"])
            lucro = round(prod["preco"] - custo, 2)
            margem_pct = round((lucro / prod["preco"]) * 100, 1) if prod["preco"] > 0 else 0.0
            disponivel = capacidade_producao(prod["id"])

            cardapio.append({
                "id": prod["id"],
                "nome": prod["nome"],
                "categoria": prod["categoria"],
                "preco": prod["preco"],
                "custo": custo,
                "lucro": lucro,
                "margem_pct": margem_pct,
                "disponivel": disponivel
            })
        return cardapio
    finally:
        conexao.close()

# consultar receita

def consultar_receitas():
    print("\n--- CARDÁPIO E RENTABILIDADE DAS RECEITAS ---")
    cardapio = listar_produtos_ativos()

    if not cardapio:
        print("Nenhum produto ativo cadastrado no cardápio.")
        return

    for item in cardapio:
        status_estoque = f"{item['disponivel']} un" if item["disponivel"] > 0 else "ESGOTADO (falta insumo)"
        print(
            f"ID {item['id']} | {item['nome']} ({item['categoria']}) | "
            f"Venda: R$ {item['preco']:.2f} | Custo: R$ {item['custo']:.2f} | "
            f"Lucro: R$ {item['lucro']:.2f} ({item['margem_pct']}%) | Disponível hoje: {status_estoque}"
        )
    print("\n--- CARDÁPIO E RENTABILIDADE DAS RECEITAS ---")
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id, nome, categoria, preco
            FROM produtos
            WHERE ativo = 1
            ORDER BY id
        """)
        produtos = cursor.fetchall()

        if not produtos:
            print("Nenhum produto ativo cadastrado no cardápio.")
            return

        for prod in produtos:
            custo = calcular_custo_receita(prod["id"])
            lucro = round(prod["preco"] - custo, 2)
            margem_pct = round((lucro / prod["preco"]) * 100, 1) if prod["preco"] > 0 else 0.0
            disponivel = capacidade_producao(prod["id"])

            status_estoque = f"{disponivel} un" if disponivel > 0 else "ESGOTADO (falta insumo)"

            print(
                f"ID {prod['id']} | {prod['nome']} ({prod['categoria']}) | "
                f"Venda: R$ {prod['preco']:.2f} | Custo: R$ {custo:.2f} | "
                f"Lucro: R$ {lucro:.2f} ({margem_pct}%) | Disponível hoje: {status_estoque}"
            )
    finally:
        conexao.close()

def menu_receitas():
    while True:
        print("\nVocê está na aba receitas!")
        print("1 - Cadastrar receita")
        print("2 - Consultar receitas")
        print("3 - Consultar ficha técnica")
        print("4 - Pesquisar receitas")
        print("5 - Editar receita")
        print("6 - Remover ingrediente da receita")
        print("7 - Consultar custo de produção")
        print("8 - Consultar capacidade de produção")
        print("0 - Voltar para a aba cozinha")

        opcao = input("Escolha sua opção: ").strip()

        if opcao == "1":
            cadastrar_receita()
        elif opcao == "2":
            consultar_receitas()
        elif opcao == "0":
            print("Saindo da aba receitas...")
            break
        else:
            print("Opção inválida.")