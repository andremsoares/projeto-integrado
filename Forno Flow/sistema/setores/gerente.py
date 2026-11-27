from autenticacao import gerenciar_senhas


def menu_gerente():
    while True:
        print("\n========== PAINEL DO GERENTE ==========")
        print("1 - Gerenciar senhas das áreas")
        print("0 - Sair")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            gerenciar_senhas()
        elif opcao == "0":
            print("Encerrando sessão do gerente...")
            break
        else:
            print("Opção inválida. Tente novamente.")