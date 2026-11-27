import sqlite3
from banco import conectar, gerar_hash

# motores de autentição

def gerente_configurado():
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT senha_hash
            FROM acessos
            WHERE usuario = 'gerente'
        """)
        registro = cursor.fetchone()
        return registro is not None and registro["senha_hash"] is not None
    finally:
        conexao.close()

def listar_usuarios_acesso():
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id,
                   usuario,
                   tipo,
                   CASE WHEN senha_hash IS NOT NULL THEN 1 ELSE 0 END AS configurada
            FROM acessos
            ORDER BY tipo ASC
        """)
        return cursor.fetchall()
    finally:
        conexao.close()

def definir_senha_motor(usuario, nova_senha):
    usuario_limpo = usuario.strip().lower()
    senha_limpa = nova_senha.strip()

    if len(senha_limpa) < 4:
        return False, "A senha deve ter pelo menos 4 caracteres."

    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id
            FROM acessos
            WHERE usuario = ?
        """, (usuario_limpo,))

        if not cursor.fetchone():
            return False, f"Usuário '{usuario_limpo}' não encontrado."

        novo_hash = gerar_hash(senha_limpa)
        cursor.execute("""
            UPDATE acessos
            SET senha_hash = ?
            WHERE usuario = ?
        """, (novo_hash, usuario_limpo))
        conexao.commit()

        return True, f"Senha de '{usuario_limpo}' definida com sucesso!"
    except sqlite3.Error as erro:
        conexao.rollback()
        return False, f"Erro no banco de dados: {erro}"
    finally:
        conexao.close()

def autenticar_motor(usuario, senha):
    usuario_limpo = usuario.strip().lower()
    senha_limpa = senha.strip()

    if not usuario_limpo or not senha_limpa:
        return None, "Informe usuário e senha."

    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id, usuario, tipo, senha_hash
            FROM acessos
            WHERE usuario = ?
        """, (usuario_limpo,))
        registro = cursor.fetchone()

        if registro is None:
            return None, "Usuário ou senha inválidos."

        if registro["senha_hash"] is None:
            return None, (
                f"A senha da área '{registro['usuario']}' ainda não foi criada. "
                "Solicite ao gerente para liberar o acesso."
            )

        if registro["senha_hash"] != gerar_hash(senha_limpa):
            return None, "Usuário ou senha inválidos."

        return registro, "OK"
    finally:
        conexao.close()

# telas de autenticação

def solicitar_nova_senha(nome_usuario):
    while True:
        senha = input(f"Digite a nova senha para '{nome_usuario}' (mín. 4 caracteres): ").strip()
        confirmacao = input(f"Confirme a senha para '{nome_usuario}': ").strip()

        if senha != confirmacao:
            print("Erro: As senhas não coincidem. Tente novamente.\n")
            continue

        sucesso, mensagem = definir_senha_motor(nome_usuario, senha)
        if sucesso:
            print(f"{mensagem}\n")
            return True

        print(f"Erro: {mensagem}\n")

def configurar_primeiro_acesso():
    print("\n========== PRIMEIRO ACESSO: CONFIGURAÇÃO DO GERENTE ==========")
    print("Nenhuma senha de administrador foi definida ainda.")
    print("Crie a senha do usuário 'gerente' para inicializar o sistema.\n")

    solicitar_nova_senha("gerente")

    resposta = input(
        "Deseja criar agora as senhas das outras áreas (cozinha, financeiro, delivery)? (S/N): "
    ).strip().upper()

    if resposta == "S":
        print("\n--- CONFIGURAÇÃO DAS ÁREAS ---")
        for setor in ("cozinha", "financeiro", "delivery"):
            cadastrar = input(f"Definir senha para '{setor}' agora? (S/N): ").strip().upper()
            if cadastrar == "S":
                solicitar_nova_senha(setor)
            else:
                print(f"Área '{setor}' mantida bloqueada (poderá ser configurada depois no menu do gerente).\n")

    print("Configuração inicial concluída! Faça login com o usuário 'gerente'.\n")

def autenticar():
    print("\n--- LOGIN NO SISTEMA ---")
    usuarios = listar_usuarios_acesso()
    mapa_usuarios = {u["tipo"]: u for u in usuarios}

    tentativas = 0
    limite = 3

    while tentativas < limite:
        print("\n+-------+--------------+--------------------+")
        print("| Opção | Perfil       | Status             |")
        print("+-------+--------------+--------------------+")
        for u in usuarios:
            status = "Ativo" if u["configurada"] == 1 else "Bloqueado"
            print(f"|   {u['tipo']}   | {u['usuario'].capitalize():<12} | {status:<18} |")
        print("+-------+--------------+--------------------+")

        opcao = input("Escolha o número do perfil: ").strip()

        try:
            tipo_escolhido = int(opcao)
        except ValueError:
            print("Opção inválida. Digite apenas o número correspondente ao perfil.")
            continue

        if tipo_escolhido not in mapa_usuarios:
            print("Perfil não encontrado. Escolha uma das opções da tabela.")
            continue

        perfil = mapa_usuarios[tipo_escolhido]

        if perfil["configurada"] == 0:
            print(
                f"A senha da área '{perfil['usuario']}' ainda não foi criada. "
                "Solicite ao gerente para liberar o acesso."
            )
            continue

        login_senha = input(f"Digite a senha de '{perfil['usuario'].capitalize()}': ").strip()
        tentativas += 1

        registro, mensagem = autenticar_motor(perfil["usuario"], login_senha)

        if registro is None:
            print(mensagem)
            if tentativas < limite:
                print(f"Você tem {limite - tentativas} tentativa(s) restante(s).\n")
            else:
                print("Número máximo de tentativas atingido. Acesso negado.")
            continue

        print(f"\nBem-vindo(a) ao sistema, {registro['usuario'].capitalize()}!")
        return registro

    return None

def gerenciar_senhas():
    while True:
        print("\n========== GERENCIAR SENHAS DE ACESSO ==========")
        usuarios = listar_usuarios_acesso()

        for u in usuarios:
            status = "Senha ativa" if u["configurada"] == 1 else "PENDENTE (Acesso bloqueado)"
            print(f"  {u['tipo']} - {u['usuario']:<12} | {status}")

        print("\nDigite o número do perfil para criar/redefinir a senha (ou 0 para voltar):")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "0":
            break

        try:
            tipo_escolhido = int(opcao)
        except ValueError:
            print("Erro: Digite um número válido.")
            continue

        mapa_usuarios = {u["tipo"]: u["usuario"] for u in usuarios}
        if tipo_escolhido not in mapa_usuarios:
            print("Erro: Perfil não encontrado.")
            continue

        usuario_alvo = mapa_usuarios[tipo_escolhido]
        print(f"\nDefinindo senha para o perfil '{usuario_alvo}':")
        solicitar_nova_senha(usuario_alvo)