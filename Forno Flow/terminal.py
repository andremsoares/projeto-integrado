# teste da lógica do sistema ai papai macetei o andré matheus soares guloso

# Login e cadastro

def gerente():
    tentativas = 0
    limite = 5
    criacao_senha = input("Cadastre sua senha: ")
    while tentativas < limite:
        login_senha = input("Digite sua senha para entrar: ")
        tentativas += 1
        if login_senha != criacao_senha and tentativas < limite:
            print(f"Senha incorreta. Acesso negado. Você tem {limite - tentativas} tentativas restantes.")
        elif login_senha != criacao_senha and tentativas == limite:
            print("Número máximo de tentativas atingido. Acesso negado.")
            break
        else:
            print("Bem-vindo(a) ao sistema, gerente!")
            break


def cozinha():
    tentativas = 0
    limite = 5
    criacao_senha = input("Cadastre sua senha: ")
    while tentativas < limite:
        login_senha = input("Digite sua senha para entrar: ")
        tentativas += 1
        if login_senha != criacao_senha and tentativas < limite:
            print(f"Senha incorreta. Acesso negado. Você tem {limite - tentativas} tentativas restantes.")
        elif login_senha != criacao_senha and tentativas == limite:
            print("Número máximo de tentativas atingido. Acesso negado.")
            break
        else:
            print("Bem-vindo(a) ao sistema, gerente!")
            break
               
def caixa():
    tentativas = 0
    limite = 5
    criacao_senha = input("Cadastre sua senha: ")

    while True:
        login_senha = input("Digite sua senha para entrar: ")
        tentativas += 1
        if login_senha != criacao_senha and tentativas < limite:
            print(f"Senha incorreta. Acesso negado. Você tem {limite - tentativas} tentativas restantes.")
        elif login_senha != criacao_senha and tentativas == limite:
            print("Número máximo de tentativas atingido. Acesso negado.")
            break
        else:
            print("Bem-vindo(a) ao sistema, gerente!")
            break
    

def delivery():
    tentativas = 0
    limite = 5
    criacao_senha = input("Cadastre sua senha: ")

    while True:
        login_senha = input("Digite sua senha para entrar: ")
        tentativas += 1
        if login_senha != criacao_senha and tentativas < limite:
            print(f"Senha incorreta. Acesso negado. Você tem {limite - tentativas} tentativas restantes.")
        elif login_senha != criacao_senha and tentativas == limite:
            print("Número máximo de tentativas atingido. Acesso negado.")
            break
        else:
            print("Bem-vindo(a) ao sistema, gerente!")
            break
    
    


while True:
    print("1 - Gerente")
    print("2 - Cozinha")
    print("3 - Caixa")
    print("4 - Delivery")
    print("0 - Sair")

    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        gerente()
    elif opcao == "2":
        cozinha()
    elif opcao == "3":
        caixa()
    elif opcao == "4":
        delivery()
    elif opcao == "0":
        print("Saindo do programa...")
        break
    else:
        print("Opção inválida. Tente novamente.")