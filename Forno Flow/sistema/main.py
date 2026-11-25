from autenticacao import autenticar
from banco import inicializar_banco
import sys

print("Bem-vindo(a) ao sistema de gerenciamento do Forno Flow!")
input("Pressione ENTER para continuar...")

inicializar_banco()

registro = autenticar()

if registro is None:
    sys.exit("Acesso negado. Encerrando aplicação.")
# verificar qual o tipo de usuario
# exibir telas para o tipo especifico
tipo = registro["tipo"]

match tipo:
    case 1:
        print("Gerente")
    case 2:
        print("Cozinha")
    case 3:
        print("Financeiro")
    case 4:
        print("Delivery")
    case _:
        print("Tipo desconhecido")