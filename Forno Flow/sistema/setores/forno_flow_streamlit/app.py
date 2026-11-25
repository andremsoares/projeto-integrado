import html
import base64
from pathlib import Path
from collections import Counter
import sqlite3
import streamlit as st
import plotly.graph_objects as go
from dados import (carregar_painel, cadastrar_ingrediente, cadastrar_produto, salvar_receita,
                   movimentar, UNIDADES, STATUS)

st.set_page_config(page_title='Fazbear Pizzaria • Produtos e Estoque', page_icon='🍕', layout='wide')
PASTA = Path(__file__).resolve().parent


def asset(nome):
    arq = PASTA / 'assets' / f'{nome}.webp'
    return 'data:image/webp;base64,' + base64.b64encode(arq.read_bytes()).decode() if arq.exists() else ''


def esc(x):
    return html.escape(str(x), quote=True)


def moeda(x):
    if x is None:
        return 'Não informado'
    return 'R$ ' + f'{x:,.2f}'.translate(str.maketrans(',.','.,'))


def qtd(x, unidade):
    if x is None:
        return 'Não informado'
    return f'{x:g}'.replace('.', ',') + (' ' + unidade if unidade else ' (sem unidade)')


st.markdown('''<style>
:root {color-scheme:dark;}
.stApp {background:radial-gradient(ellipse at 74% 0%,#3b220d 0%,#1b130c 32%,#100c09 72%);color:#f8f1e4;}
[data-testid="stHeader"] {background:transparent;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#241407,#130e0a 55%,#2b190d);border-right:1px solid #9b6a20;}
[data-testid="stSidebar"] [data-testid="stImage"] img {border-radius:8px;}
.block-container {max-width:1550px;padding-top:2.1rem;padding-bottom:2rem;}
h1,h2,h3 {color:#fff4dd!important;letter-spacing:-.025em;}
.hero {display:flex;align-items:center;justify-content:space-between;min-height:112px;margin:0 0 16px;padding:12px 20px;border-bottom:1px solid #79531f;overflow:hidden;background:linear-gradient(100deg,#301b0c,#18110b);border-radius:12px;}
.hero-copy {position:relative;z-index:1;flex:1;}
.hero h1 {font-size:clamp(24px,3vw,41px);margin:0;line-height:1.15;}
.hero p {color:#e0cbae;margin:7px 0 0;font-size:15px;}
.hero img {width:33%;max-height:120px;object-fit:cover;object-position:center;mask-image:linear-gradient(to right,transparent,black 17%);}
.kpi {height:105px;border:1px solid #c99426;border-radius:12px;padding:12px 14px;background:linear-gradient(145deg,#3b280e,#21150b);box-shadow:inset 0 0 14px #efac1412;display:flex;gap:12px;align-items:center;}
.kpi.alert {border-color:#e97237;background:linear-gradient(145deg,#4b2314,#28130c);}
.kpi-icon {font-size:27px;color:#ffd15a;flex-shrink:0;}
.kpi-label {font-size:13px;color:#e8d9c5;line-height:1.2;}
.kpi-value {font-size:clamp(19px,2.1vw,30px);font-weight:800;color:#fff6dd;white-space:nowrap;line-height:1.25;}
.kpi-note {font-size:11px;color:#bca688;}
[data-testid="stRadio"] [role="radiogroup"] {gap:.3rem;}
[data-testid="stRadio"] [role="radiogroup"] label {border:1px solid #735122;border-radius:8px;padding:7px 12px;background:#261b12;}
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {border-color:#ffcc43;background:#765018;}
.stButton button, [data-testid="stFormSubmitButton"] button {border:1px solid #e2a425;border-radius:8px;background:linear-gradient(180deg,#51330e,#30200c);color:#ffe7a3;font-weight:650;}
.stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] {background:linear-gradient(180deg,#f9b932,#bb6509);color:#211405;border-color:#ffd771;}
.stButton button:hover {border-color:#ffe08b;color:#fff;}
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {background:#231910;}
[data-testid="stExpander"] {border-color:#805b2a;border-radius:10px;}
.table-wrap {overflow-x:auto;border:1px solid #8b6b38;border-radius:12px;background:#1a130e;}
.inv {width:100%;border-collapse:collapse;white-space:nowrap;font-size:14px;}
.inv th {text-align:left;padding:13px 12px;background:#36291c;color:#f7e9cf;font-weight:650;border-bottom:1px solid #916f37;}
.inv td {padding:11px 12px;border-bottom:1px solid #4b3825;color:#f1e8d9;}
.inv tr:nth-child(even) {background:#251c13;}.inv tbody tr:last-child td {border-bottom:none;}.inv tbody tr:hover {background:#3c2a14;}
.inv td:first-child {font-weight:700;color:#eed4a0;font-size:12px;}
.tag {display:inline-block;border-radius:6px;padding:3px 8px;font-size:12px;font-weight:650;border:1px solid #99712a;background:#503812;color:#ffd77c;}
.status {display:inline-block;padding:4px 9px;border-radius:6px;font-size:12px;font-weight:700;border:1px solid;}
.ideal {background:#124a24;color:#b4f9be;border-color:#31984c;}.medio {background:#544113;color:#ffe08a;border-color:#b59530;}.baixo {background:#624015;color:#ffc373;border-color:#c37e22;}.critico {background:#67291d;color:#ffc1a6;border-color:#d95e40;}.fora {background:#412024;color:#ff9ca0;border-color:#bc4650;}.desconhecido {background:#38342d;color:#d3c9b8;border-color:#786c5d;}
.chart-title {font-size:17px;font-weight:750;color:#ffdf8a;padding:10px 14px;background:linear-gradient(90deg,#4b3215,#261a10);border:1px solid #91672b;border-radius:9px;margin-top:10px;}
.smallnote {font-size:12px;color:#bba88e;}
@media(max-width:800px){.hero img{display:none}.kpi{height:auto;min-height:85px}.inv{font-size:13px}}
</style>''', unsafe_allow_html=True)

with st.sidebar:
    if (PASTA/'assets/marca.webp').exists():
        st.image(str(PASTA/'assets/marca.webp'), use_container_width=True)
    else:
        st.title('🍕 Fazbear Pizzaria')
    st.caption('FORNO FLOW • GESTÃO DA PIZZARIA')
    pagina = st.radio('Navegação', ['⌂  Início','▤  Pedidos','♧  Delivery','▣  Produtos e Estoque','▥  Relatórios','⚙  Configurações'], index=3, label_visibility='collapsed')
    st.divider()
    st.caption('Esta entrega implementa Produtos e Estoque. As demais páginas serão integradas posteriormente.')
    if (PASTA/'assets/rodape.webp').exists():
        st.image(str(PASTA/'assets/rodape.webp'), use_container_width=True)

if pagina != '▣  Produtos e Estoque':
    st.title(pagina)
    st.info('Esta seção ainda não foi implementada. Volte a Produtos e Estoque pelo menu lateral.')
    st.stop()

st.markdown(f'''<div class="hero"><div class="hero-copy"><h1>▣ Produtos e Estoque</h1><p>Cadastro de pizzas, ingredientes e controle de estoque</p></div><img alt="" src="{asset('cabecalho')}"></div>''', unsafe_allow_html=True)
try:
    painel = carregar_painel()
except (sqlite3.Error, OSError, RuntimeError) as erro:
    st.error(f'Não foi possível consultar o banco: {erro}')
    st.info('Confirme a função conectar() de banco.py, o caminho do arquivo .db e se as cinco tabelas já foram criadas. A interface não cria nem substitui o banco.')
    st.stop()

if 'aviso' in st.session_state:
    st.success(st.session_state.pop('aviso'))
itens = painel['itens']
fisicos = [r for r in itens if r['tipo']=='ingrediente']
contagem = Counter(r['status'] for r in fisicos)


def kpi(col, icone, titulo, valor, nota, alerta=False):
    col.markdown(f'<div class="kpi {"alert" if alerta else ""}"><div class="kpi-icon">{esc(icone)}</div><div><div class="kpi-label">{esc(titulo)}</div><div class="kpi-value">{esc(valor)}</div><div class="kpi-note">{esc(nota)}</div></div></div>', unsafe_allow_html=True)


cols = st.columns(4)
kpi(cols[0],'🍕','Produtos cadastrados',len(painel['produtos']),f'{len(fisicos)} ingredientes cadastrados')
kpi(cols[1],'⚠','Estoque baixo',contagem['Estoque baixo'],'Ingredientes físicos',True)
kpi(cols[2],'◉','Ingredientes críticos',contagem['Estoque crítico'],'Abaixo ou no mínimo',True)
kpi(cols[3],'◈','Receita do cardápio',moeda(painel['faturamento']),'Vendas confirmadas • acumulado')
st.caption(f"Vendas datadas: hoje {moeda(painel['hoje'])} • ontem {moeda(painel['ontem'])}")
st.write('')
aba = st.radio('Visualização', ['🍕 Pizzas','🥤 Bebidas','🌿 Ingredientes','▣ Estoque'],index=3,horizontal=True,label_visibility='collapsed')
base = [r for r in itens if ('pizza' in r['categoria'].casefold() and r['tipo']=='produto')] if aba=='🍕 Pizzas' else [r for r in itens if ('bebida' in r['categoria'].casefold() and r['tipo']=='produto')] if aba=='🥤 Bebidas' else fisicos if aba=='🌿 Ingredientes' else itens
f1,f2,f3,f4 = st.columns([2.0,1.25,1.35,1.2],vertical_alignment='bottom')
with f1:
    busca=st.text_input('Buscar produto',placeholder='Digite o nome ou ID do produto...')
with f2:
    categorias=['Todas as categorias']+sorted({r['categoria'] for r in base})
    categoria=st.selectbox('Categoria',categorias,key=f'categoria_{aba}')
with f3:
    filtro_status=st.selectbox('Status do estoque',['Todos os status',*STATUS])
with f4:
    if st.button('＋ Novo produto',type='primary',use_container_width=True):
        st.session_state['cadastro_aberto']=not st.session_state.get('cadastro_aberto',False)


def executar(acao, mensagem):
    try:
        acao()
    except (ValueError, sqlite3.Error) as erro:
        st.error(f'Não foi possível salvar: {erro}')
    else:
        st.session_state['aviso']=mensagem
        st.rerun()


if st.session_state.get('cadastro_aberto',False):
    with st.container(border=True):
        st.subheader('Novo cadastro')
        tipo=st.radio('Tipo de cadastro',['Ingrediente','Produto do cardápio'],horizontal=True)
        if tipo=='Ingrediente':
            with st.form('novo_ingrediente',clear_on_submit=True):
                nome=st.text_input('Nome do ingrediente')
                a,b,c=st.columns(3)
                unidade=a.selectbox('Unidade',UNIDADES)
                quantidade=b.number_input('Quantidade inicial',min_value=0.0,value=None,step=0.1)
                custo=c.number_input('Custo por unidade de medida (R$)',min_value=0.0,value=None,step=0.01,format='%.2f')
                a,b=st.columns(2)
                minimo=a.number_input('Estoque mínimo',min_value=0.0,value=None,step=0.1)
                ideal=b.number_input('Estoque ideal',min_value=0.000001,value=None,step=0.1,format='%.6f')
                if st.form_submit_button('Cadastrar ingrediente',type='primary'):
                    executar(lambda:cadastrar_ingrediente(nome,unidade,quantidade,custo,minimo,ideal),'Ingrediente cadastrado!')
        else:
            with st.form('novo_produto',clear_on_submit=True):
                nome=st.text_input('Nome do produto')
                categoria_nova=st.selectbox('Categoria',['Pizza','Bebida','Sobremesa','Outro'])
                preco=st.number_input('Preço de venda (R$)',min_value=0.0,value=None,step=0.01,format='%.2f')
                if st.form_submit_button('Cadastrar produto',type='primary'):
                    executar(lambda:cadastrar_produto(nome,categoria_nova,preco),'Produto cadastrado! Cadastre a receita para calcular sua disponibilidade.')
        st.caption('Os campos seguem as restrições atuais do banco. A receita pode ser cadastrada depois.')

filtrados=[r for r in base if (not busca.strip() or busca.casefold().strip() in (r['nome']+' '+r['codigo']).casefold()) and (categoria=='Todas as categorias' or r['categoria']==categoria) and (filtro_status=='Todos os status' or r['status']==filtro_status)]
with st.expander('Ordenação da tabela'):
    o1,o2=st.columns(2)
    ordenar=o1.selectbox('Ordenar por',['Ordem padrão','ID','Produto','Categoria','Preço','Estoque','Status'])
    decrescente=o2.checkbox('Ordem decrescente')
    campos={'ID':'codigo','Produto':'nome','Categoria':'categoria','Preço':'preco','Estoque':'quantidade','Status':'status'}
    if ordenar in campos:
        campo=campos[ordenar]
        if ordenar=='Estoque':
            st.caption('Ordenação pelo valor numérico, sem converter ou comparar unidades diferentes.')
        presentes=[r for r in filtrados if r[campo] is not None]
        ausentes=[r for r in filtrados if r[campo] is None]
        filtrados=sorted(presentes,key=lambda r:r[campo].casefold() if isinstance(r[campo],str) else r[campo],reverse=decrescente)+ausentes
classes={'Estoque ideal':('ideal','✓'),'Estoque médio':('medio','◐'),'Estoque baixo':('baixo','⚠'),'Estoque crítico':('critico','!'),'Fora de estoque':('fora','×'),'Não informado':('desconhecido','–')}
linhas=[]
for r in filtrados:
    classe,icone=classes.get(r['status'],('desconhecido','–'))
    emoji='🌿' if r['tipo']=='ingrediente' else '🥤' if 'bebida' in r['categoria'].casefold() else '🍕' if 'pizza' in r['categoria'].casefold() else '◈'
    preco=moeda(r['preco'])
    if r['tipo']=='ingrediente' and r['preco'] is not None and r['unidade']:
        preco+=f" / {r['unidade']}"
    linhas.append(f'''<tr><td>{esc(r['codigo'])}</td><td>{emoji} {esc(r['nome'])}</td><td><span class="tag">{esc(r['categoria'])}</span></td><td>{esc(preco)}</td><td>{esc(qtd(r['quantidade'],r['unidade']))}</td><td><span class="status {classe}">{icone} {esc(r['status'])}</span></td></tr>''')
if not linhas:
    linhas.append('<tr><td colspan="6" style="text-align:center;padding:36px;color:#c8b698">Nenhum item cadastrado ou encontrado com esses filtros.</td></tr>')
st.markdown('<div class="table-wrap"><table class="inv"><thead><tr><th># ID</th><th>Produto</th><th>Categoria</th><th>Preço</th><th>Estoque</th><th>Status</th></tr></thead><tbody>'+''.join(linhas)+'</tbody></table></div>',unsafe_allow_html=True)
st.caption(f'{len(filtrados)} de {len(base)} itens • Ingredientes: custo de compra por unidade de medida. Produtos: preço de venda e capacidade de produção (não é estoque físico).')

# Ações de estoque e ficha técnica: os registros são gravados no banco real.
with st.expander('⋯  Gerenciar receitas e movimentações'):
    t1,t2=st.tabs(['Ficha técnica / receita','Entrada ou perda de estoque'])
    with t1:
        if painel['produtos'] and painel['ingredientes']:
            ps={r['id']:r['nome'] for r in painel['produtos']}
            ins={r['id']:r for r in painel['ingredientes']}
            pid=st.selectbox('Produto',list(ps),format_func=lambda x:ps[x])
            rid=st.selectbox('Ingrediente',list(ins),format_func=lambda x:ins[x]['ingrediente'])
            receita=painel['receitas'].get(pid,[])
            if receita:
                st.table([{'Ingrediente':r['ingrediente'],'Quantidade por produto':qtd(r['quantidade_necessaria'],r['unidade'])} for r in receita])
            else:
                st.caption('Nenhum ingrediente cadastrado na receita.')
            atual=next((r['quantidade_necessaria'] for r in receita if r['ingrediente_id']==rid),0.1)
            with st.form(f'receita_{pid}_{rid}'):
                necessaria=st.number_input(f"Quantidade necessária ({ins[rid]['unidade'] or 'sem unidade'}) por produto",min_value=0.000001,value=float(atual),step=0.01,format='%.6f')
                if st.form_submit_button('Salvar ingrediente na receita'):
                    if not ins[rid]['unidade']:
                        st.error('O ingrediente precisa ter uma unidade definida.')
                    else:
                        executar(lambda:salvar_receita(pid,rid,necessaria),'Receita atualizada!')
        else:
            st.info('Cadastre pelo menos um produto e um ingrediente.')
    with t2:
        if painel['ingredientes']:
            ins={r['id']:r for r in painel['ingredientes']}
            iid=st.selectbox('Ingrediente para movimentação',list(ins),format_func=lambda x:ins[x]['ingrediente'])
            with st.form('movimentar'):
                tipo_mov=st.radio('Tipo',['entrada','perda'],horizontal=True,format_func=lambda x:'Reposição / entrada' if x=='entrada' else 'Retirada por perda')
                valor=st.number_input(f"Quantidade ({ins[iid]['unidade'] or 'sem unidade'})",min_value=0.000001,value=1.0,step=0.1,format='%.6f')
                if st.form_submit_button('Registrar movimentação'):
                    executar(lambda:movimentar(iid,tipo_mov,valor),'Movimentação registrada!')
        else:
            st.info('Nenhum ingrediente cadastrado.')

c1,c2=st.columns([1,1])
cores={'Estoque ideal':'#ffcf2b','Estoque médio':'#e9b75a','Estoque baixo':'#f18b25','Estoque crítico':'#ffcf9b','Fora de estoque':'#e84c4c','Não informado':'#8b8279'}

def layout(fig):
    fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(color='#f2e5d1',size=12),margin=dict(l=8,r=14,t=18,b=15),height=290)
    return fig

with c1:
    st.markdown('<div class="chart-title">▥ Itens mais vendidos</div>',unsafe_allow_html=True)
    vendas=painel['vendas']
    if vendas:
        fig=go.Figure(go.Bar(y=[r['produto'] for r in vendas],x=[r['quantidade'] for r in vendas],orientation='h',marker_color=['#ffd12f','#f9a831','#ef8d38','#e5ba6b','#f4dfb3'][:len(vendas)],text=[r['quantidade'] for r in vendas],textposition='auto',hovertemplate='%{y}: %{x} un<extra></extra>'))
        layout(fig).update_yaxes(autorange='reversed',automargin=True).update_xaxes(title='Quantidade vendida',rangemode='tozero',gridcolor='#4a3625')
        st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
    else:
        st.info('Nenhuma venda confirmada registrada.')
    st.caption('Quantidade total por produto, sem pedidos não confirmados.')
with c2:
    st.markdown('<div class="chart-title">◉ Situação do estoque</div>',unsafe_allow_html=True)
    if fisicos:
        labels=[s for s in STATUS if contagem[s]]
        fig=go.Figure(go.Pie(labels=labels,values=[contagem[s] for s in labels],hole=.63,sort=False,marker=dict(colors=[cores[s] for s in labels],line=dict(color='#21170e',width=1)),textinfo='percent',textfont=dict(color='#19120b'),hovertemplate='%{label}: %{value} itens<extra></extra>'))
        layout(fig).update_layout(legend=dict(orientation='h',y=-.12),annotations=[dict(text=f'<b>{len(fisicos)}</b><br>itens',x=.5,y=.5,showarrow=False,font=dict(size=20,color='#fff1db'))])
        st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
    else:
        st.info('Nenhum ingrediente para classificar.')
    st.caption('Somente ingredientes físicos, para não contar os mesmos insumos duas vezes.')
st.divider()
st.caption('FORNO FLOW  •  Dados do SQLite  |  Os valores são atualizados a cada interação ou nova consulta. O status dos produtos segue o pior alerta da receita; zero unidades possíveis tem prioridade.')
if st.button('↻ Atualizar dados'):
    st.rerun()
