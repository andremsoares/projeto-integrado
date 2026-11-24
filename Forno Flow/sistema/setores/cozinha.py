import sqlite3
from banco import inicializar_banco

def menu_cozinha():
    while True:
        print("1 - Pedidos")
        print("2 - Estoque")
        print("0 - Voltar")
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == "1":
            
        elif opcao == "0":
            break
        else:
            print("Opção inválida. Tente novamente.")