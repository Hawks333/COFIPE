import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Mapa de Sonhos - MVP", layout="wide")

st.title("Mapa de Sonhos — MVP (Streamlit)")
st.write("Planeje suas metas para os próximos 12 meses, acompanhe receitas, despesas e o progresso das suas conquistas.")

# --- Helpers ---
if 'goals' not in st.session_state:
    st.session_state.goals = []
if 'fixed_expenses_list' not in st.session_state:
    st.session_state.fixed_expenses_list = [
        'Internet', 'Luz', 'Conta de celular', 'Faculdade', 'Academia', 'Gasolina', 'Água', 'Aluguel', 'Parcela do carro', 'Corte de cabelo', 'Unha'
    ]
if 'paid' not in st.session_state:
    # paid structure: {month_index: {expense_name: bool}}
    st.session_state.paid = {m: {e: False for e in st.session_state.fixed_expenses_list} for m in range(1,13)}


def add_goal(name, value):
    st.session_state.goals.append({'name': name, 'value': float(value)})


def remove_goal(idx):
    st.session_state.goals.pop(idx)


# --- Left column: Goals input ---
col1, col2 = st.columns([2,3])
with col1:
    st.header("1) Defina suas metas (12 meses)")
    with st.form(key='goal_form'):
        name = st.text_input('Nome da meta (ex: Carro, Viagem, Reserva de emergência)')
        value = st.number_input('Valor total da meta (R$)', min_value=0.0, value=1000.0, step=100.0, format="%.2f")
        submitted = st.form_submit_button('Adicionar meta')
        if submitted and name.strip():
            add_goal(name.strip(), value)

    if st.session_state.goals:
        df_goals = pd.DataFrame(st.session_state.goals)
        df_goals.index = df_goals.index + 1
        st.write("### Metas adicionadas")
        st.table(df_goals.rename(columns={'name':'Meta','value':'Valor (R$)'}))
        # allow remove
        to_remove = st.number_input('Remover meta (digite o índice)', min_value=0, max_value=len(st.session_state.goals), value=0)
        if to_remove != 0:
            remove_goal(int(to_remove)-1)

    total_goals = sum(g['value'] for g in st.session_state.goals)
    monthly_goal_cost = total_goals / 12 if total_goals>0 else 0
    st.metric('Total de metas (R$)', f"R$ {total_goals:,.2f}")
    st.metric('Custo mensal para todas as metas (R$)', f"R$ {monthly_goal_cost:,.2f}")

    st.info('Orientação: liste os sonhos que deseja alcançar nos próximos 12 meses. Seja realista nos valores. Se uma meta for maior que o que pode pagar em 12 meses, considere um plano alternativo ou parcelamento.')

# --- Right column: Income and expenses ---
with col2:
    st.header("2) Receitas e despesas")
    with st.form(key='income_form'):
        st.subheader('Receitas mensais')
        salary = st.number_input('Salário fixo (R$)', min_value=0.0, value=5000.0, step=100.0, format="%.2f")
        extra = st.number_input('Renda extra média mensal (R$)', min_value=0.0, value=1200.0, step=100.0, format="%.2f")
        st.subheader('Contas fixas (previsíveis)')
        # editable list of fixed expenses
        fixed_items = st.session_state.fixed_expenses_list.copy()
        edited = st.text_area('Lista de contas fixas (um por linha) — edite se necessário', '\n'.join(fixed_items), height=120)
        if st.form_submit_button('Salvar receita & despesas'):
            # update fixed expenses list
            new_list = [x.strip() for x in edited.split('\n') if x.strip()]
            st.session_state.fixed_expenses_list = new_list
            # reset paid structure for months to include new items
            for m in range(1,13):
                for e in new_list:
                    if e not in st.session_state.paid[m]:
                        st.session_state.paid[m][e] = False
            st.success('Receita e lista de contas fixas atualizadas')

    # Input values for each fixed expense
    st.write('---')
    st.write('### Defina o valor mensal de cada conta fixa')
    fixed_values = {}
    for exp in st.session_state.fixed_expenses_list:
        fixed_values[exp] = st.number_input(f'R$ - {exp}', min_value=0.0, value=100.0, step=50.0, format="%.2f", key=f'val_{exp}')

    fun_value = st.number_input('Conta de diversão mensal (R$)', min_value=0.0, value=300.0, step=50.0, format="%.2f")

# --- Compute planning ---
income_total = salary + extra
fixed_total = sum(fixed_values.values())
monthly_goal_cost = total_goals / 12 if total_goals>0 else 0
monthly_balance = income_total - (fixed_total + fun_value + monthly_goal_cost)

st.write('---')
st.header('3) Planejamento 12 meses')

# Build months table
months = [ (datetime.now().replace(day=1) + pd.DateOffset(months=i)).strftime('%b %Y') for i in range(12) ]
plan_rows = []
for i, m in enumerate(months, start=1):
    plan_rows.append({
        'Mês': m,
        'Receita (R$)': income_total,
        'Despesas Fixas (R$)': fixed_total,
        'Diversão (R$)': fun_value,
        'Meta Mensal (R$)': monthly_goal_cost,
        'Saldo Mensal (R$)': income_total - (fixed_total + fun_value + monthly_goal_cost)
    })
plan_df = pd.DataFrame(plan_rows)

st.dataframe(plan_df.style.format('{:,.2f}', subset=['Receita (R$)','Despesas Fixas (R$)','Diversão (R$)','Meta Mensal (R$)','Saldo Mensal (R$)']))

# Summary metrics
st.metric('Saldo mensal médio', f"R$ {monthly_balance:,.2f}")

if monthly_balance < 0:
    deficit = abs(monthly_balance)
    st.error('Para atingir sua meta, será preciso criar um planejamento alternativo.')
    st.warning(f'O nosso planejamento alternativo possui uma meta de R$ {deficit:,.2f} por mês para cobrir o déficit.')
    st.write('Como você deseja prosseguir?')
    option = st.radio('Escolha uma opção', [
        'Trabalho CLT e gostaria de ser promovido',
        'Quero empreender',
        'Empreendo mas estou com dificuldades',
        'Quero reduzir o valor da meta'
    ])
    # Simple eBooks as text for download
    ebooks = {
        'Trabalho CLT e gostaria de ser promovido': 'Ebook: Promocao_CLT.txt',
        'Quero empreender': 'Ebook: Comecar_empreender.txt',
        'Empreendo mas estou com dificuldades': 'Ebook: Empreendedor_Dificuldades.txt',
        'Quero reduzir o valor da meta': 'Ebook: Reduzir_Meta.txt'
    }
    st.markdown('**Material recomendado:**')
    if st.button('Receber eBook de orientação'):
        text = ''
        if option == 'Trabalho CLT e gostaria de ser promovido':
            text = ("Guia rapido para avancar na carreira:\n- Melhore visibilidade;\n- Peça feedback;\n- Documente conquistas;\n- Busque cursos estrategicos.")
        elif option == 'Quero empreender':
            text = ("Guia para iniciar um negocio:\n- Valide a ideia;\n- Teste MVP;\n- Estruture preco e fluxo de caixa;\n- Busque microcrédito/mentoria.")
        elif option == 'Empreendo mas estou com dificuldades':
            text = ("Guia para quem ja empreende:\n- Analise funil de vendas;\n- Reduza custos fixos;\n- Foque em clientes recorrentes;\n- Busque parceiros e mentors.")
        else:
            text = ("Guia para reduzir metas:\n- Priorize 3 metas principais;\n- Ajuste prazos;\n- Renegocie valores;\n- Considere parcelamento inteligente.")
        b = io.BytesIO()
        b.write(text.encode('utf-8'))
        b.seek(0)
        st.download_button('Baixar eBook', data=b, file_name=ebooks[option], mime='text/plain')

else:
    st.success('Ótimo — suas metas cabem no plano atual!')
    st.info('Você pode reduzir metas manualmente se quiser aumentar folga financeira ou manter o plano para cumprir tudo em 12 meses.')

# --- Acompanhamento e marcar contas pagas ---
st.write('---')
st.header('4) Acompanhamento mensal e marcar contas fixas pagas')
selected_month = st.selectbox('Escolha o mês que deseja atualizar', list(range(1,13)), format_func=lambda x: months[x-1])
col_a, col_b = st.columns([2,1])
with col_a:
    st.subheader(f'Contas fixas — {months[selected_month-1]}')
    paid_any = False
    for exp in st.session_state.fixed_expenses_list:
        key = f'paid_{selected_month}_{exp}'
        # initialize if missing
        if exp not in st.session_state.paid[selected_month]:
            st.session_state.paid[selected_month][exp] = False
        val = st.checkbox(exp + f' - R$ {fixed_values.get(exp,0):,.2f}', value=st.session_state.paid[selected_month].get(exp, False), key=key)
        st.session_state.paid[selected_month][exp] = val
        if val:
            paid_any = True
    if st.button('Salvar pagamentos deste mês'):
        st.success('Pagamentos salvos para o mês selecionado')

with col_b:
    st.subheader('Atualizar entrada/saída real deste mês')
    received = st.number_input('Quanto você recebeu este mês (R$)', min_value=0.0, value=income_total, step=100.0, format="%.2f", key='received')
    real_fixed_spent = st.number_input('Quanto gastou em contas fixas este mês (R$)', min_value=0.0, value=fixed_total, step=50.0, format="%.2f", key='real_fixed')
    real_fun = st.number_input('Quanto gastou em diversão este mês (R$)', min_value=0.0, value=fun_value, step=50.0, format="%.2f", key='real_fun')
    if st.button('Atualizar e calcular indicador'):
        real_balance = received - (real_fixed_spent + real_fun + monthly_goal_cost)
        st.metric('Saldo real deste mês (R$)', f"R$ {real_balance:,.2f}")
        # indicator: progress towards monthly goal funding
        if monthly_goal_cost > 0:
            funded = max(0.0, (received - (real_fixed_spent + real_fun)) / monthly_goal_cost)
            pct = min(1.0, funded)
            st.progress(pct)
            if funded >= 1.0:
                st.success('Você está financiando sua meta mensal!')
            elif funded >= 0.6:
                st.warning('Quase lá — ajuste pequenas despesas para alcançar a meta.')
            else:
                st.error('Atenção: você está longe do valor mensal necessário para as metas.')

# --- Export / download plan ---
st.write('---')
st.header('Exportar')
if st.button('Exportar plano para CSV'): 
    csv = plan_df.to_csv(index=False).encode('utf-8')
    st.download_button('Download CSV do plano', data=csv, file_name='mapa_de_sonhos_plano.csv', mime='text/csv')

st.write('\n---\n')
st.caption('MVP construído para testar ideia: funcionalidades principais implementadas. Para transformar em produto, recomendamos adicionar autenticação, backup em nuvem, testes automatizados, melhorias de UX e visual.')
