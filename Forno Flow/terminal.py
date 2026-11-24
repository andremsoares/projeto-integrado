# teste da lógica do sistema ai papai macetei o andré matheus soares guloso

# Login e cadastro

def gerente():
    criacao_senha = input("Escreva sua senha: ")
    print("Sua senha foi cadastrada com sucesso!")
    login_senha = input("Digite sua senha para entrar: ")
    if login_senha == criacao_senha:
        print("Bem-vindo, gerente!")
    else:
        print("Senha incorreta. Acesso negado.")


def cozinha()
    criacao_senha = input("Escreva sua senha: ")
    print("Sua senha foi cadastrada com sucesso!")
    login_senha = input("Digite sua senha para entrar: ")
    if login_senha == criacao_senha:
        print("Bem-vindo(a) à cozinha!")
    else: 
        print("Senha incorreta. Acesso negado.")
        



while True:
    print("1 - Gerente")
    print("2 - Cozinha")
    print("3 - Caixa")
    print("4 - Delivery")

    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        gerente()
    if opcao == "2":
        cozinha()