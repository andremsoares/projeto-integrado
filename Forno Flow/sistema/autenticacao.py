# teste da lógica do sistema ai papai macetei o andré matheus soares guloso

# Login e cadastro
import sqlite3
from banco import inicializar_banco, gerar_hash

def gerente():
    conexao = sqlite3.connect("sistema.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT senha_hash FROM acesso_gerente WHERE id = 1")
    registro = cursor.fetchone()

    if registro is None:
        criacao_senha = input("Cadastre sua senha: ")
        senha_salva_hash = gerar_hash(criacao_senha)
        cursor.execute(
            "INSERT INTO acesso_gerente (id, senha_hash) VALUES (1, ?)", (senha_salva_hash,)
            )
        conexao.commit()
    else:
        senha_salva_hash = registro[0]

    conexao.close()

    tentativas = 0
    limite = 5
    while tentativas < limite:
        login_senha = input("Digite sua senha para entrar: ")
        tentativas += 1
        login_hash = gerar_hash(login_senha)

        if login_hash != senha_salva_hash and tentativas < limite:
            print(f"Senha incorreta. Acesso negado. Você tem {limite - tentativas} tentativas restantes.")
        elif login_hash != senha_salva_hash and tentativas == limite:
            print("Número máximo de tentativas atingido. Acesso negado.")
            break
        else:
            print("Bem-vindo(a) ao sistema, gerente!")
            break

def cozinha():
    conexao = sqlite3.connect("sistema.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT senha_hash FROM acesso_cozinha WHERE id = 1")
    registro = cursor.fetchone()

    if registro is None:
        criacao_senha = input("Cadastre sua senha: ")
        senha_salva_hash = gerar_hash(criacao_senha)
        cursor.execute(
            "INSERT INTO acesso_cozinha (id, senha_hash) VALUES (1, ?)", (senha_salva_hash,)
            )
        conexao.commit()
    else:
        senha_salva_hash = registro[0]

    conexao.close()

    tentativas = 0
    limite = 5
    while tentativas < limite:
        login_senha = input("Digite sua senha para entrar: ")
        tentativas += 1
        login_hash = gerar_hash(login_senha)

        if login_hash != senha_salva_hash and tentativas < limite:
            print(f"Senha incorreta. Acesso negado. Você tem {limite - tentativas} tentativas restantes.")
        elif login_hash != senha_salva_hash and tentativas == limite:
            print("Número máximo de tentativas atingido. Acesso negado.")
            break
        else:
            print("Bem-vindo(a) ao sistema, funcionário!")
            break
               
def caixa():
    conexao = sqlite3.connect("sistema.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT senha_hash FROM acesso_caixa WHERE id = 1")
    registro = cursor.fetchone()

    if registro is None:
        criacao_senha = input("Cadastre sua senha: ")
        senha_salva_hash = gerar_hash(criacao_senha)
        cursor.execute(
            "INSERT INTO acesso_caixa (id, senha_hash) VALUES (1, ?)", (senha_salva_hash,)
            )
        conexao.commit()
    else:
        senha_salva_hash = registro[0]

    conexao.close()

    tentativas = 0
    limite = 5
    while tentativas < limite:
        login_senha = input("Digite sua senha para entrar: ")
        tentativas += 1
        login_hash = gerar_hash(login_senha)

        if login_hash != senha_salva_hash and tentativas < limite:
            print(f"Senha incorreta. Acesso negado. Você tem {limite - tentativas} tentativas restantes.")
        elif login_hash != senha_salva_hash and tentativas == limite:
            print("Número máximo de tentativas atingido. Acesso negado.")
            break
        else:
            print("Bem-vindo(a) ao sistema, funcionário!")
            break

def delivery():
    conexao = sqlite3.connect("sistema.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT senha_hash FROM acesso_delivery WHERE id = 1")
    registro = cursor.fetchone()

    if registro is None:
        criacao_senha = input("Cadastre sua senha: ")
        senha_salva_hash = gerar_hash(criacao_senha)
        cursor.execute(
            "INSERT INTO acesso_delivery (id, senha_hash) VALUES (1, ?)", (senha_salva_hash,)
            )
        conexao.commit()
    else:
        senha_salva_hash = registro[0]

    conexao.close()

    tentativas = 0
    limite = 5
    while tentativas < limite:
        login_senha = input("Digite sua senha para entrar: ")
        tentativas += 1
        login_hash = gerar_hash(login_senha)

        if login_hash != senha_salva_hash and tentativas < limite:
            print(f"Senha incorreta. Acesso negado. Você tem {limite - tentativas} tentativas restantes.")
        elif login_hash != senha_salva_hash and tentativas == limite:
            print("Número máximo de tentativas atingido. Acesso negado.")
            break
        else:
            print("Bem-vindo(a) ao sistema, funcionário!")
            break

def menu_autenticacao():
    while True:
        print("1 - Gerente")
        print("2 - Cozinha")
        print("3 - Caixa")
        print("4 - Delivery")
        print("0 - Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            inicializar_banco()
            gerente()
        elif opcao == "2":
            inicializar_banco()
            cozinha()
        elif opcao == "3":
            inicializar_banco()
            caixa()
        elif opcao == "4":
            inicializar_banco()
            delivery()
        elif opcao == "0":
            print("Saindo do programa...")
            break
        else:
            print("Opção inválida. Tente novamente.")