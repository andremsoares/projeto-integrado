import sqlite3
from banco import inicializar_banco
from datetime import datetime

horario = datetime.now().strftime("%H:%M")

def cadastrar_pedido():
    

def pedidos():
    



def estoque():
    

def menu_cozinha():
    while True:
        print("1 - Pedidos")
        print("2 - Estoque")
        print("0 - Voltar")
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == "1":
            pedidos()
        elif opcao == "2":
            estoque()
        elif opcao == "0":
            break
        else:
            print("Opção inválida. Tente novamente.")