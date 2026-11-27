import sys
sys.dont_write_bytecode = True

from autenticacao import (
    autenticar,
    gerente_configurado,
    configurar_primeiro_acesso
)
from banco import inicializar_banco
from setores.gerente import menu_gerente
from setores.cozinha import menu_cozinha


def main():
    print("Bem-vindo(a) ao sistema de gerenciamento do Forno Flow!")
    inicializar_banco()

    if not gerente_configurado():
        configurar_primeiro_acesso()

    while True:
        print("\n========== FORNO FLOW ==========")
        print("1 - Fazer login")
        print("0 - Encerrar sistema")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "0":
            print("Encerrando aplicação...")
            break
        elif opcao != "1":
            print("Opção inválida.")
            continue

        registro = autenticar()

        if registro is None:
            sys.exit("Acesso negado. Encerrando aplicação.")

        tipo = registro["tipo"]

        match tipo:
            case 1:
                menu_gerente()
            case 2:
                menu_cozinha()
            case 3:
                print("Financeiro (em desenvolvimento)")
            case 4:
                print("Delivery (em desenvolvimento)")
            case _:
                print("Tipo desconhecido")


if __name__ == "__main__":
    main()