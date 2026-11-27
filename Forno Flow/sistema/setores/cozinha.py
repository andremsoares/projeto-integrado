from setores.telas.estoque import menu_estoque
from setores.telas.pedidos import menu_pedidos
from setores.telas.receitas import menu_receitas

def menu_cozinha():
    while True:
        print("\n--- ABA COZINHA ---")
        print("1 - Pedidos")
        print("2 - Estoque")
        print("3 - Receitas")
        print("0 - Voltar")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            menu_pedidos()
        elif opcao == "2":
            menu_estoque()
        elif opcao == "3":
            menu_receitas()
        elif opcao == "0":
            print("Voltando ao menu principal...")
            break
        else:
            print("Opção inválida. Tente novamente.")