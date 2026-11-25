"""Camada de dados da página: não depende do Streamlit nem de input()/print()."""
import os
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from decimal import Decimal
from contextlib import contextmanager
import math

PASTA = Path(__file__).resolve().parent
UNIDADES = ('g', 'ml', 'un', 'l', 'kg')
STATUS = ('Estoque ideal', 'Estoque médio', 'Estoque baixo', 'Estoque crítico', 'Fora de estoque', 'Não informado')
# Ajuste aqui se o setor de pedidos utilizar outros estados de venda confirmada.
VENDAS = ('aprovado', 'pago', 'concluido', 'concluído', 'entregue', 'finalizado')


def conectar():
    caminho = os.environ.get('FORNO_DB')
    if caminho:
        arquivo = Path(caminho).expanduser().resolve()
        if not arquivo.is_file():
            raise FileNotFoundError(f'Banco não encontrado: {arquivo}')
        conexao = sqlite3.connect(arquivo)
    else:
        # Permite deixar a pasta da interface ao lado de banco.py ou dentro de sistema/.
        for pasta in (PASTA, PASTA.parent, PASTA.parent / 'sistema', PASTA.parent.parent / 'sistema'):
            if (pasta / 'banco.py').is_file():
                if str(pasta) not in sys.path:
                    sys.path.insert(0, str(pasta))
                break
        try:
            from banco import conectar as conectar_projeto
        except ModuleNotFoundError as erro:
            if erro.name != 'banco':
                raise
            raise RuntimeError('Coloque esta pasta ao lado de banco.py ou defina FORNO_DB com o caminho do banco existente.') from erro
        conexao = conectar_projeto()
    conexao.row_factory = sqlite3.Row
    conexao.execute('PRAGMA foreign_keys = ON')
    return conexao


@contextmanager
def sessao(escrita=False):
    con = conectar()
    try:
        if escrita:
            con.execute('BEGIN IMMEDIATE')
        else:
            con.execute('BEGIN')
        yield con
        if escrita:
            con.commit()
    except Exception:
        if escrita:
            con.rollback()
        raise
    finally:
        con.close()


def calcular_status_estoque(quantidade, estoque_minimo, estoque_ideal):
    # A mesma regra construída no cozinha.py: 50% do intervalo mínimo–ideal.
    if quantidade is None:
        return 'Não informado'
    if quantidade == 0:
        return 'Fora de estoque'
    if estoque_minimo is None or estoque_ideal is None:
        return 'Não informado'
    if quantidade >= estoque_ideal:
        return 'Estoque ideal'
    if quantidade <= estoque_minimo:
        return 'Estoque crítico'
    porcentagem = (quantidade - estoque_minimo) / (estoque_ideal - estoque_minimo) * 100
    return 'Estoque médio' if porcentagem >= 50 else 'Estoque baixo'


def capacidade(qtd, necessario):
    # Decimal a partir da representação armazenada evita casos comuns como 0.3 // 0.1.
    return int(Decimal(str(qtd)) // Decimal(str(necessario)))


def disponibilidade(receita):
    if not receita:
        return None, 'Não informado'
    capacidades, alertas = [], []
    incompleto = False
    for linha in receita:
        q, n = linha['quantidade'], linha['quantidade_necessaria']
        if q is None or n is None or n <= 0 or q < 0 or not linha['unidade']:
            incompleto = True
            continue
        capacidades.append(capacidade(q, n))
        alertas.append(calcular_status_estoque(q, linha['estoque_minimo'], linha['estoque_ideal']))
    if 0 in capacidades:
        return 0, 'Fora de estoque'
    if incompleto or not capacidades:
        return None, 'Não informado'
    qtd = min(capacidades)
    if 'Não informado' in alertas:
        return qtd, 'Não informado'
    # Regra proposta para produtos: pior alerta entre os ingredientes da receita.
    return qtd, max(alertas, key=STATUS.index)


def carregar_painel():
    with sessao() as con:
        ingredientes = [dict(r) for r in con.execute('''SELECT id, ingrediente, unidade, quantidade,
            custo_unitario, estoque_minimo, estoque_ideal FROM estoque ORDER BY ingrediente COLLATE NOCASE''')]
        produtos = [dict(r) for r in con.execute('SELECT id, nome, categoria, preco FROM produtos ORDER BY nome COLLATE NOCASE')]
        receitas = [dict(r) for r in con.execute('''SELECT r.produto_id, r.ingrediente_id, r.quantidade_necessaria,
            e.ingrediente, e.unidade, e.quantidade, e.estoque_minimo, e.estoque_ideal
            FROM receitas r LEFT JOIN estoque e ON e.id = r.ingrediente_id''')]
        marcadores = ','.join('?' for _ in VENDAS)
        filtro = f'LOWER(TRIM(p.status)) IN ({marcadores})'
        vendas = [dict(r) for r in con.execute(f'''SELECT pr.nome AS produto, SUM(p.quantidade) AS quantidade
            FROM pedidos p JOIN produtos pr ON pr.id = p.produto_id WHERE {filtro}
            GROUP BY pr.id, pr.nome ORDER BY quantidade DESC, pr.nome LIMIT 5''', VENDAS)]
        total = con.execute(f'SELECT COALESCE(SUM(p.valor_total),0) FROM pedidos p WHERE {filtro}', VENDAS).fetchone()[0]
        hoje = date.today().isoformat()
        ontem = (date.today() - timedelta(days=1)).isoformat()
        diarios = dict(con.execute(f'''SELECT DATE(p.data_hora), SUM(p.valor_total) FROM pedidos p
            WHERE {filtro} AND DATE(p.data_hora) IN (?,?) GROUP BY DATE(p.data_hora)''', (*VENDAS, hoje, ontem)).fetchall())
    por_produto = {}
    for r in receitas:
        por_produto.setdefault(r['produto_id'], []).append(r)
    itens = []
    for r in produtos:
        qtd, status = disponibilidade(por_produto.get(r['id'], []))
        cat = r['categoria'] or 'Não informado'
        prefixo = 'PZ' if 'pizza' in cat.casefold() else 'BEB' if 'bebida' in cat.casefold() else 'PRD'
        itens.append(dict(id=r['id'], codigo=f"#{prefixo}{r['id']:03d}", nome=r['nome'], categoria=cat,
                          preco=r['preco'], quantidade=qtd, unidade='un', status=status, tipo='produto'))
    for r in ingredientes:
        itens.append(dict(id=r['id'], codigo=f"#ING{r['id']:03d}", nome=r['ingrediente'], categoria='Ingrediente',
                          preco=r['custo_unitario'], quantidade=r['quantidade'], unidade=r['unidade'],
                          status=calcular_status_estoque(r['quantidade'], r['estoque_minimo'], r['estoque_ideal']), tipo='ingrediente'))
    return dict(itens=itens, ingredientes=ingredientes, produtos=produtos, receitas=por_produto,
                vendas=vendas, faturamento=total, hoje=diarios.get(hoje,0), ontem=diarios.get(ontem,0))


def validar_numero(valor, minimo=0, estrito=False):
    if valor is None or not math.isfinite(valor) or valor < minimo or (estrito and valor == minimo):
        raise ValueError('Informe um número válido dentro dos limites permitidos.')


def cadastrar_ingrediente(nome, unidade, quantidade, custo, minimo, ideal):
    nome = nome.strip()
    if not nome or unidade not in UNIDADES:
        raise ValueError('Informe nome e unidade de medida válida.')
    for valor in (quantidade,custo,minimo):
        validar_numero(valor)
    validar_numero(ideal, estrito=True)
    if ideal < minimo:
        raise ValueError('O estoque ideal não pode ser menor que o mínimo.')
    with sessao(escrita=True) as con:
        cur = con.execute('''INSERT INTO estoque (ingrediente, unidade, quantidade, custo_unitario, estoque_minimo, estoque_ideal)
            VALUES (?,?,?,?,?,?)''', (nome,unidade,quantidade,custo,minimo,ideal))
        if quantidade > 0:
            con.execute('''INSERT INTO movimentacoes_estoque (ingrediente_id,tipo,quantidade,custo_total,data_hora)
                VALUES (?,'entrada',?,?,?)''', (cur.lastrowid,quantidade,round(quantidade*custo,2),datetime.now().isoformat(sep=' ',timespec='seconds')))


def cadastrar_produto(nome,categoria,preco):
    nome, categoria = nome.strip(), categoria.strip()
    if not nome or not categoria:
        raise ValueError('Informe nome e categoria.')
    validar_numero(preco)
    with sessao(escrita=True) as con:
        con.execute('INSERT INTO produtos (nome,categoria,preco) VALUES (?,?,?)',(nome,categoria,preco))


def salvar_receita(produto_id, ingrediente_id, quantidade):
    validar_numero(quantidade,estrito=True)
    with sessao(escrita=True) as con:
        con.execute('''INSERT INTO receitas (produto_id,ingrediente_id,quantidade_necessaria) VALUES (?,?,?)
            ON CONFLICT(produto_id,ingrediente_id) DO UPDATE SET quantidade_necessaria=excluded.quantidade_necessaria''',
            (produto_id,ingrediente_id,quantidade))


def movimentar(ingrediente_id,tipo,quantidade):
    validar_numero(quantidade,estrito=True)
    if tipo not in ('entrada','perda'):
        raise ValueError('Movimentação inválida.')
    with sessao(escrita=True) as con:
        r = con.execute('SELECT quantidade,custo_unitario,unidade FROM estoque WHERE id=?',(ingrediente_id,)).fetchone()
        if r is None or r['quantidade'] is None or r['custo_unitario'] is None or not r['unidade']:
            raise ValueError('Complete quantidade, custo e unidade antes de movimentar o ingrediente.')
        novo = r['quantidade'] + quantidade if tipo=='entrada' else r['quantidade'] - quantidade
        if novo < 0:
            raise ValueError('Não há estoque suficiente para essa saída.')
        con.execute('UPDATE estoque SET quantidade=? WHERE id=?',(novo,ingrediente_id))
        con.execute('''INSERT INTO movimentacoes_estoque (ingrediente_id,tipo,quantidade,custo_total,data_hora)
            VALUES (?,?,?,?,?)''',(ingrediente_id,tipo,quantidade,round(quantidade*r['custo_unitario'],2),datetime.now().isoformat(sep=' ',timespec='seconds')))
