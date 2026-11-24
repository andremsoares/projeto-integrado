import sqlite3
from banco import inicializar_banco
from datetime import datetime

horario = datetime.now().strftime("%H:%M")

def salvar_pedido(cliente, item, valor, status, horari):
    conexao = sqlite3.connect("sistema.db")
    cursor = conexao.cursor()
    cursor.execute(
        "INSERT INTO pedidos (cliente, item, valor, horario) VALUES (?, ?, ?, ?)", (cliente, item, valor, horario)
        )
    conexao.commit()
    conexao.close()

def cadastrar_pedido():
    cliente = input("Digite o nome do cliente: ")
    quantidade_item = input("Você deseja mais de um item?")
    if quantidade_item.lower() == "sim":
        item = input("Digite os itens separados por vírgula: ")
    else:
        input("Digite o item: ")
    valor = float(input("Digite o valor do pedido: "))
    

def salvar_produto():
    conexao = sqlite3.connect("sistema.db")
    cursor = conexao.curso()
    cursor.execute(
        "INSERT INTO produtos (produto, categoria, preco, estoque, status) VALUES (?, ?, ?, ?, ?) ",  (produto, categoria, preco, estoque, status)
        )

    conexao.commit()
    conexao.close()

def cadastrar_produto():

    produto = input("Digite o nome do produto: ")
    categoria = input("Digite a categoria do produto: ")
    preco = float(input("Digite o preço do produto: "))
    estoque = int(input("Digite a quantidade em estoque: "))
    status = input("Digite o status do produto (disponível/indisponível): ")

    salvar_produto(produto, categoria, preco, estoque, status)
    print("Produto cadastrado com sucesso!")
    

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