import sqlite3
from datetime import datetime

horario = datetime.now().strftime("%H:%M")

# garantir com que os pedidos possam ser feitos somente com o que tem no estoque, passando por uma conferência no banco de dados para validar o pedido

def estoque():
    

def menu_cozinha():
    while True:
        print("1 - Pedidos")
        print("2 - Estoque")
        print("0 - Voltar")
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == "1":
            print("Você está na aba pedidos")
        elif opcao == "2":
            print("Você está na aba estoque")
        elif opcao == "0":
            break
        else:
            print("Opção inválida. Tente novamente.")