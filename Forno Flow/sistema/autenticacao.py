import sqlite3
from banco import gerar_hash
               
def autenticar():
    conexao = sqlite3.connect("sistema.db")
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    tentativas = 0
    limite = 3
    while tentativas < limite:
        usuario = input("Digite o usuário: ")
        login_senha = input("Digite sua senha para entrar: ")
        tentativas += 1
        login_hash = gerar_hash(login_senha)
        
        cursor.execute(
            "SELECT id, usuario, tipo FROM acessos WHERE usuario = ? AND senha_hash = ?",
            (usuario, login_hash)
        )
        registro = cursor.fetchone()
        
        if registro is None:
            print("Usuário ou senha inválido.")
            if tentativas < limite:
                print(f"Acesso negado. Você tem {limite - tentativas} tentativas restantes.")
            elif tentativas == limite:
                print("Número máximo de tentativas atingido. Acesso negado.")
                break
            continue
        print("Bem-vindo(a) ao sistema, funcionário!")
        conexao.close()
        return registro
        
    conexao.close()
    return None