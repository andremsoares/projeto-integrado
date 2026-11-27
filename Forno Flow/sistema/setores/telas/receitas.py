import sqlite3
from banco import conectar


# cálculo de custo de receita

def calcular_custo_receita(produto_id, cursor=None):
    conexao = None
    if cursor is None:
        conexao = conectar()
        cursor = conexao.cursor()
    try:
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
        if conexao is not None:
            conexao.close()


# verificar disponibilidade

def verificar_disponibilidade(produto_id, quantidade_pedida=1, cursor=None):
    if quantidade_pedida <= 0:
        return False, "A quantidade pedida deve ser maior que zero."

    conexao = None
    if cursor is None:
        conexao = conectar()
        cursor = conexao.cursor()
    try:
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
        if conexao is not None:
            conexao.close()


# capacidade de produção

def capacidade_producao(produto_id, cursor=None):
    conexao = None
    if cursor is None:
        conexao = conectar()
        cursor = conexao.cursor()
    try:
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
        if conexao is not None:
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


# estorno de estoque por cancelamento de pedido

def estornar_estoque_receita(cursor, produto_id, qtd_pedida, data_hora):
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
        quantidade_estornada = round(item["quantidade_necessaria"] * qtd_pedida, 4)
        custo_estorno = round(quantidade_estornada * item["custo_unitario"], 2)

        cursor.execute("""
            UPDATE estoque
            SET quantidade = ROUND(quantidade + ?, 4)
            WHERE id = ?
        """, (quantidade_estornada, item["ingrediente_id"]))

        # Certifique-se de que o CHECK de movimentacoes_estoque.tipo no banco.py inclui 'estorno'
        cursor.execute("""
            INSERT INTO movimentacoes_estoque (ingrediente_id, tipo, quantidade, custo_total, data_hora)
            VALUES (?, 'estorno', ?, ?, ?)
        """, (item["ingrediente_id"], quantidade_estornada, custo_estorno, data_hora))


# cadastrar receita

def cadastrar_receita():
    print("\n--- CADASTRAR PRODUTO E FICHA TÉCNICA ---")
    conexao = conectar()
    try:
        cursor = conexao.cursor()

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

        cursor.execute("""
            INSERT INTO produtos (nome, categoria, preco, ativo)
            VALUES (?, ?, ?, 1)
        """, (nome, categoria, round(preco, 2)))
        produto_id = cursor.lastrowid

        print("\n--- MONTAGEM DA RECEITA (Digite 0 no ID para finalizar) ---")
        ids_validos = {item["id"]: item for item in insumos_disponiveis}
        ingredientes_adicionados = set()

        while True:
            try:
                ing_id = int(input("\nID do ingrediente (ou 0 para concluir): ").strip())
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

        conexao.commit()

        custo_producao = calcular_custo_receita(produto_id, cursor=cursor)
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
            custo = calcular_custo_receita(prod["id"], cursor=cursor)
            lucro = round(prod["preco"] - custo, 2)
            margem_pct = round((lucro / prod["preco"]) * 100, 1) if prod["preco"] > 0 else 0.0
            disponivel = capacidade_producao(prod["id"], cursor=cursor)

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


# consultar ficha técnica

def consultar_ficha_tecnica():
    print("\n--- CONSULTAR FICHA TÉCNICA ---")
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id, nome, categoria
            FROM produtos
            WHERE ativo = 1
            ORDER BY id
        """)
        produtos = cursor.fetchall()

        if not produtos:
            print("Nenhum produto ativo cadastrado no cardápio.")
            return

        print("\nProdutos cadastrados:")
        for prod in produtos:
            print(f"  ID {prod['id']} | {prod['nome']} ({prod['categoria']})")

        try:
            produto_id = int(input("\nDigite o ID do produto para ver a ficha técnica: ").strip())
        except ValueError:
            print("Erro: Digite um número de ID válido.")
            return

        cursor.execute("""
            SELECT id, nome, categoria, preco
            FROM produtos
            WHERE id = ? AND ativo = 1
        """, (produto_id,))
        produto = cursor.fetchone()

        if not produto:
            print("Erro: Produto não encontrado ou inativo no cardápio.")
            return

        cursor.execute("""
            SELECT e.id AS ingrediente_id,
                   e.ingrediente,
                   e.unidade,
                   e.custo_unitario,
                   e.quantidade AS saldo_atual,
                   e.ativo AS ingrediente_ativo,
                   r.quantidade_necessaria
            FROM receitas r
            INNER JOIN estoque e ON r.ingrediente_id = e.id
            WHERE r.produto_id = ?
            ORDER BY e.ingrediente
        """, (produto_id,))
        itens = cursor.fetchall()

        print(f"\n========== FICHA TÉCNICA: {produto['nome'].upper()} ==========")
        print(f"Categoria: {produto['categoria']} | Preço de venda: R$ {produto['preco']:.2f}")

        if not itens:
            print("Este produto não possui ingredientes vinculados.")
            return

        print("\nComposição por unidade produzida:")
        for item in itens:
            custo_item = round(item["quantidade_necessaria"] * item["custo_unitario"], 2)

            if item["ingrediente_ativo"] == 0:
                status_ing = " [DESATIVADO NO ESTOQUE]"
                rendimento = 0
            else:
                status_ing = ""
                rendimento = (
                    int(round(item["saldo_atual"] / item["quantidade_necessaria"], 6))
                    if item["quantidade_necessaria"] > 0 else 0
                )

            print(
                f"  - ID {item['ingrediente_id']} | {item['ingrediente']}: "
                f"{item['quantidade_necessaria']:g} {item['unidade']} | "
                f"Custo: R$ {custo_item:.2f} | "
                f"Estoque: {item['saldo_atual']:g} {item['unidade']} (rende {rendimento} un){status_ing}"
            )

        custo_total = calcular_custo_receita(produto_id, cursor=cursor)
        lucro = round(produto["preco"] - custo_total, 2)
        margem_porcentagem = round((lucro / produto["preco"]) * 100, 1) if produto["preco"] > 0 else 0.0
        capacidade = capacidade_producao(produto_id, cursor=cursor)

        print("\nResumo da Receita:")
        print(f"  Custo total de produção: R$ {custo_total:.2f}")
        print(f"  Lucro bruto unitário:    R$ {lucro:.2f} ({margem_porcentagem}%)")
        print(f"  Capacidade atual:        {capacidade} un")

    finally:
        conexao.close()


# editar receita

def editar_receita():
    print("\n--- EDITAR INGREDIENTES DA RECEITA ---")
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

        print("\nProdutos disponíveis:")
        for prod in produtos:
            print(f"  ID {prod['id']} | {prod['nome']} ({prod['categoria']})")

        try:
            produto_id = int(input("\nDigite o ID do produto que deseja editar: ").strip())
        except ValueError:
            print("Erro: Digite um número de ID válido.")
            return

        cursor.execute("""
            SELECT id, nome, preco
            FROM produtos
            WHERE id = ? AND ativo = 1
        """, (produto_id,))
        produto = cursor.fetchone()

        if not produto:
            print("Erro: Produto não encontrado ou inativo no cardápio.")
            return

        while True:
            cursor.execute("""
                SELECT e.id AS ingrediente_id,
                       e.ingrediente,
                       e.unidade,
                       e.ativo AS ingrediente_ativo,
                       r.quantidade_necessaria
                FROM receitas r
                INNER JOIN estoque e ON r.ingrediente_id = e.id
                WHERE r.produto_id = ?
                ORDER BY e.ingrediente
            """, (produto_id,))
            itens_atuais = cursor.fetchall()

            print(f"\n=== FICHA TÉCNICA ATUAL: {produto['nome'].upper()} ===")
            if not itens_atuais:
                print("  (Nenhum ingrediente vinculado)")
            else:
                for item in itens_atuais:
                    aviso = " [DESATIVADO NO ESTOQUE]" if item["ingrediente_ativo"] == 0 else ""
                    print(
                        f"  ID {item['ingrediente_id']} | {item['ingrediente']}: "
                        f"{item['quantidade_necessaria']:g} {item['unidade']}{aviso}"
                    )

            print("\nO que deseja fazer?")
            print("1 - Alterar quantidade de um ingrediente")
            print("2 - Adicionar novo ingrediente")
            print("3 - Remover ingrediente")
            print("0 - Concluir edição")

            sub_opcao = input("Escolha uma opção: ").strip()

            if sub_opcao == "1":
                if not itens_atuais:
                    print("Não há ingredientes nesta receita para alterar.")
                    continue

                ids_na_receita = {item["ingrediente_id"]: item for item in itens_atuais}
                try:
                    ing_id = int(input("ID do ingrediente a alterar: ").strip())
                except ValueError:
                    print("Digite um ID numérico válido.")
                    continue

                if ing_id not in ids_na_receita:
                    print("Este ingrediente não faz parte desta receita.")
                    continue

                ing_escolhido = ids_na_receita[ing_id]
                try:
                    nova_qtd = float(
                        input(f"Nova quantidade de '{ing_escolhido['ingrediente']}' ({ing_escolhido['unidade']}): ")
                        .strip().replace(",", ".")
                    )
                    if nova_qtd <= 0:
                        print("A quantidade deve ser maior que zero.")
                        continue
                except ValueError:
                    print("Digite um valor numérico válido.")
                    continue

                cursor.execute("""
                    UPDATE receitas
                    SET quantidade_necessaria = ?
                    WHERE produto_id = ? AND ingrediente_id = ?
                """, (round(nova_qtd, 4), produto_id, ing_id))
                conexao.commit()
                print(f"Quantidade de '{ing_escolhido['ingrediente']}' atualizada para {nova_qtd:g} {ing_escolhido['unidade']}.")

            elif sub_opcao == "2":
                ids_ja_usados = {item["ingrediente_id"] for item in itens_atuais}

                cursor.execute("""
                    SELECT id, ingrediente, unidade, custo_unitario
                    FROM estoque
                    WHERE ativo = 1
                    ORDER BY id
                """)
                todos_insumos = cursor.fetchall()
                disponiveis_para_add = [ins for ins in todos_insumos if ins["id"] not in ids_ja_usados]

                if not disponiveis_para_add:
                    print("Todos os ingredientes ativos do estoque já estão nesta receita.")
                    continue

                print("\nIngredientes disponíveis para adicionar:")
                ids_validos = {}
                for ins in disponiveis_para_add:
                    ids_validos[ins["id"]] = ins
                    print(f"  ID {ins['id']} | {ins['ingrediente']} ({ins['unidade']}) - R$ {ins['custo_unitario']:.2f}/{ins['unidade']}")

                try:
                    ing_id = int(input("\nID do ingrediente para adicionar: ").strip())
                except ValueError:
                    print("Digite um ID numérico válido.")
                    continue

                if ing_id not in ids_validos:
                    print("ID inválido ou ingrediente já presente na receita.")
                    continue

                ins_escolhido = ids_validos[ing_id]
                try:
                    qtd_nova = float(
                        input(f"Quantidade de '{ins_escolhido['ingrediente']}' por unidade ({ins_escolhido['unidade']}): ")
                        .strip().replace(",", ".")
                    )
                    if qtd_nova <= 0:
                        print("A quantidade deve ser maior que zero.")
                        continue
                except ValueError:
                    print("Digite um valor numérico válido.")
                    continue

                cursor.execute("""
                    INSERT INTO receitas (produto_id, ingrediente_id, quantidade_necessaria)
                    VALUES (?, ?, ?)
                """, (produto_id, ing_id, round(qtd_nova, 4)))
                conexao.commit()
                print(f"Ingrediente '{ins_escolhido['ingrediente']}' adicionado à receita.")

            elif sub_opcao == "3":
                if len(itens_atuais) <= 1:
                    print("Operação bloqueada: a receita precisa manter pelo menos 1 ingrediente.")
                    continue

                ids_na_receita = {item["ingrediente_id"]: item for item in itens_atuais}
                try:
                    ing_id = int(input("ID do ingrediente para remover: ").strip())
                except ValueError:
                    print("Digite um ID numérico válido.")
                    continue

                if ing_id not in ids_na_receita:
                    print("Este ingrediente não faz parte desta receita.")
                    continue

                ativos_restantes = sum(
                    1 for item in itens_atuais
                    if item["ingrediente_id"] != ing_id and item["ingrediente_ativo"] == 1
                )
                if ativos_restantes == 0 and any(item["ingrediente_ativo"] == 1 for item in itens_atuais):
                    print("Operação bloqueada: a receita precisa manter pelo menos 1 ingrediente ativo no estoque.")
                    continue

                ing_removido = ids_na_receita[ing_id]
                cursor.execute("""
                    DELETE FROM receitas
                    WHERE produto_id = ? AND ingrediente_id = ?
                """, (produto_id, ing_id))
                conexao.commit()
                print(f"Ingrediente '{ing_removido['ingrediente']}' removido da receita.")

            elif sub_opcao == "0":
                novo_custo = calcular_custo_receita(produto_id, cursor=cursor)
                nova_margem = round(produto["preco"] - novo_custo, 2)
                print(f"\nEdição concluída! Novo custo de produção: R$ {novo_custo:.2f} | Nova margem bruta: R$ {nova_margem:.2f}")
                break

            else:
                print("Opção inválida.")

    except sqlite3.Error as erro:
        conexao.rollback()
        print(f"Erro no banco de dados ao editar receita: {erro}")
    finally:
        conexao.close()


# alterar preço ou desativar produto

def editar_ou_desativar_produto():
    print("\n--- ALTERAR PREÇO OU DESATIVAR PRODUTO ---")
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

        print("\nProdutos ativos:")
        for prod in produtos:
            custo = calcular_custo_receita(prod["id"], cursor=cursor)
            print(
                f"  ID {prod['id']} | {prod['nome']} ({prod['categoria']}) | "
                f"Preço atual: R$ {prod['preco']:.2f} | Custo: R$ {custo:.2f}"
            )

        try:
            produto_id = int(input("\nDigite o ID do produto: ").strip())
        except ValueError:
            print("Erro: Digite um número de ID válido.")
            return

        cursor.execute("""
            SELECT id, nome, categoria, preco
            FROM produtos
            WHERE id = ? AND ativo = 1
        """, (produto_id,))
        produto = cursor.fetchone()

        if not produto:
            print("Erro: Produto não encontrado ou já desativado.")
            return

        print(f"\nProduto selecionado: {produto['nome']} (Preço atual: R$ {produto['preco']:.2f})")
        print("1 - Alterar preço de venda")
        print("2 - Desativar produto do cardápio")
        print("0 - Cancelar")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            try:
                novo_preco = float(
                    input("Novo preço de venda (R$): ").strip().replace(",", ".")
                )
                if novo_preco < 0:
                    print("Erro: O preço não pode ser negativo.")
                    return
            except ValueError:
                print("Erro: Digite um valor numérico válido.")
                return

            novo_preco = round(novo_preco, 2)
            cursor.execute("""
                UPDATE produtos
                SET preco = ?
                WHERE id = ?
            """, (novo_preco, produto_id))
            conexao.commit()

            custo = calcular_custo_receita(produto_id, cursor=cursor)
            lucro = round(novo_preco - custo, 2)
            margem_pct = round((lucro / novo_preco) * 100, 1) if novo_preco > 0 else 0.0

            print(f"\nPreço de '{produto['nome']}' atualizado para R$ {novo_preco:.2f}!")
            print(f"Custo: R$ {custo:.2f} | Novo lucro bruto: R$ {lucro:.2f} ({margem_pct}%)")

        elif opcao == "2":
            confirmacao = input(
                f"Tem certeza que deseja desativar '{produto['nome']}' do cardápio? (S/N): "
            ).strip().upper()

            if confirmacao != "S":
                print("Operação cancelada.")
                return

            cursor.execute("""
                UPDATE produtos
                SET ativo = 0
                WHERE id = ?
            """, (produto_id,))
            conexao.commit()

            print(
                f"\nProduto '{produto['nome']}' desativado com sucesso! "
                "Ele não aparecerá mais para novos pedidos, mas o histórico de vendas foi preservado."
            )

        elif opcao == "0":
            print("Operação cancelada.")

        else:
            print("Opção inválida.")

    except sqlite3.Error as erro:
        conexao.rollback()
        print(f"Erro no banco de dados: {erro}")
    finally:
        conexao.close()


def menu_receitas():
    while True:
        print("\nVocê está na aba receitas!")
        print("1 - Cadastrar receita")
        print("2 - Consultar receitas")
        print("3 - Consultar ficha técnica")
        print("4 - Editar receita")
        print("5 - Alterar preço ou desativar produto")
        print("0 - Voltar para a aba cozinha")

        opcao = input("Escolha sua opção: ").strip()

        if opcao == "1":
            cadastrar_receita()
        elif opcao == "2":
            consultar_receitas()
        elif opcao == "3":
            consultar_ficha_tecnica()
        elif opcao == "4":
            editar_receita()
        elif opcao == "5":
            editar_ou_desativar_produto()
        elif opcao == "0":
            print("Saindo da aba receitas...")
            break
        else:
            print("Opção inválida.")