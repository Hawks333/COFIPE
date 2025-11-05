import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import math

# --- Configuração Inicial ---
st.set_page_config(page_title="Mapa de Sonhos - Acompanhamento de Metas", layout="wide")

# --- Funções Auxiliares ---
def get_current_month_index():
    """Retorna o índice do mês atual (0 a 11) baseado no estado da sessão."""
    if 'current_month_index' not in st.session_state:
        st.session_state.current_month_index = 0
    return st.session_state.current_month_index

def get_month_info(index):
    """Retorna o objeto datetime e o nome formatado do mês para um dado índice (0-11)."""
    start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    target_date = start_date + pd.DateOffset(months=index)
    return target_date, target_date.strftime('%B/%Y').capitalize()

def add_goal(name, value):
    """Adiciona uma nova meta à lista de metas."""
    st.session_state.goals.append({'name': name, 'value': float(value), 'saved': 0.0})

def remove_goal(idx):
    """Remove uma meta pelo índice."""
    try:
        st.session_state.goals.pop(idx)
    except:
        pass

def format_currency(value):
    """Formata um valor numérico para a moeda brasileira."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Inicialização do Estado da Sessão ---
if 'goals' not in st.session_state:
    # Adicionando 'saved' para rastrear o progresso
    st.session_state.goals = [
        {'name': 'Viagem para Europa', 'value': 10000.0, 'saved': 5000.0},
        {'name': 'Sofá Novo', 'value': 5000.0, 'saved': 1000.0},
        {'name': 'Reserva de Emergência', 'value': 15000.0, 'saved': 0.0}
    ]

# --- Lógica de Migração (Corrige KeyError: 'saved') ---
# Garante que todas as metas, incluindo as adicionadas pelo código original do usuário,
# tenham a chave 'saved' inicializada.
for goal in st.session_state.goals:
    if 'saved' not in goal:
        goal['saved'] = 0.0
if 'fixed_expenses_list' not in st.session_state:
    st.session_state.fixed_expenses_list = [
        'Internet', 'Luz', 'Conta de celular', 'Faculdade', 'Academia', 'Gasolina', 'Água', 'Aluguel', 'Parcela do carro', 'Corte de cabelo', 'Unha'
    ]
if 'paid' not in st.session_state:
    # paid structure: {month_index: {expense_name: bool}}
    st.session_state.paid = {m: {e: False for e in st.session_state.fixed_expenses_list} for m in range(12)}
if 'salary' not in st.session_state:
    st.session_state.salary = 5000.0
if 'extra' not in st.session_state:
    st.session_state.extra = 1200.0
if 'fun_value' not in st.session_state:
    st.session_state.fun_value = 300.0
# Inicializa os valores das despesas fixas (mantendo a estrutura original para compatibilidade)
for exp in st.session_state.fixed_expenses_list:
    keyname = f'val_{exp}'
    if keyname not in st.session_state:
        st.session_state[keyname] = 100.0

# --- Lógica de Cálculo Central ---
def calculate_financials():
    """Calcula o total de metas, custo mensal e balanço financeiro."""
    total_goals = sum(g['value'] for g in st.session_state.goals)
    
    # Soma dos valores das despesas fixas
    fixed_values = {exp: st.session_state.get(f'val_{exp}', 0.0) for exp in st.session_state.fixed_expenses_list}
    fixed_total = sum(fixed_values.values())
    
    income_total = st.session_state.salary + st.session_state.extra
    
    # Custo mensal para atingir todas as metas em 12 meses
    monthly_goal_cost = total_goals / 12 if total_goals > 0 else 0
    
    # Saldo mensal médio (o quanto sobra após despesas e meta de poupança)
    monthly_balance = income_total - (fixed_total + st.session_state.fun_value + monthly_goal_cost)
    
    return {
        'total_goals': total_goals,
        'fixed_values': fixed_values,
        'fixed_total': fixed_total,
        'income_total': income_total,
        'monthly_goal_cost': monthly_goal_cost,
        'monthly_balance': monthly_balance
    }

financials = calculate_financials()

# --- Layout Principal ---
st.title("💰 Mapa de Sonhos - Acompanhamento de Metas")
st.write("Planeje suas metas, acompanhe receitas, despesas e o progresso das suas conquistas.")

# --- Painel de Metas Atingidas (Novo Requisito) ---
st.header("✨ Metas Concluídas")
completed_goals = [g for g in st.session_state.goals if g['saved'] >= g['value']]

if completed_goals:
    for goal in completed_goals:
        st.success(f"**Parabéns!** Você já atingiu 100% da meta **{goal['name']}** ({format_currency(goal['value'])}). Que tal realizar este sonho?")
    st.balloons()
else:
    st.info("Nenhuma meta concluída ainda. Continue economizando!")

st.write("---")

# --- Colunas de Configuração ---
col_config, col_goals = st.columns([1, 1])

with col_config:
    st.header("1) Receitas e Despesas Fixas")
    with st.expander("Configurar Receitas e Despesas", expanded=False):
        with st.form(key='income_form'):
            st.subheader('Receitas mensais')
            salary = st.number_input('Salário fixo (R$)', min_value=0.0, value=st.session_state.salary, step=100.0, format="%.2f")
            extra = st.number_input('Renda extra média mensal (R$)', min_value=0.0, value=st.session_state.extra, step=100.0, format="%.2f")
            
            st.subheader('Contas fixas (previsíveis)')
            fixed_items = st.session_state.fixed_expenses_list.copy()
            edited = st.text_area('Lista de contas fixas (um por linha) — edite se necessário', '\n'.join(fixed_items), height=120)
            
            if st.form_submit_button('Salvar Receita & Lista de Contas'):
                new_list = [x.strip() for x in edited.split('\n') if x.strip()]
                if not new_list:
                    st.error("A lista de contas fixas não pode ficar vazia.")
                else:
                    # Atualiza a lista de despesas fixas
                    st.session_state.fixed_expenses_list = new_list
                    # Atualiza a estrutura 'paid' para incluir novos itens nos 12 meses
                    for m in range(12):
                        for e in new_list:
                            if e not in st.session_state.paid[m]:
                                st.session_state.paid[m][e] = False
                    st.session_state.salary = salary
                    st.session_state.extra = extra
                    st.success('Receita e lista de contas fixas atualizadas com sucesso!')
                    st.experimental_rerun() # Força o recálculo e re-renderização

        st.write('---')
        st.subheader('Defina o valor mensal de cada conta fixa')
        for exp in st.session_state.fixed_expenses_list:
            keyname = f'val_{exp}'
            default_val = st.session_state.get(keyname, 100.0)
            st.session_state[keyname] = st.number_input(f'R$ - {exp}', min_value=0.0, value=default_val, step=50.0, format="%.2f", key=keyname)

        st.write('---')
        st.subheader('Outras Despesas')
        st.session_state.fun_value = st.number_input('Conta de diversão mensal (R$)', min_value=0.0, value=st.session_state.fun_value, step=50.0, format="%.2f", key='fun_value')

with col_goals:
    st.header("2) Defina suas Metas (Sonhos)")
    with st.expander("Adicionar/Remover Metas", expanded=True):
        with st.form(key='goal_form'):
            name = st.text_input('Nome da meta (ex: Carro, Viagem, Reserva de emergência)')
            value = st.number_input('Valor total da meta (R$)', min_value=0.0, value=1000.0, step=100.0, format="%.2f")
            submitted = st.form_submit_button('Adicionar meta')
            if submitted and name.strip():
                add_goal(name.strip(), value)
                st.experimental_rerun()

        if st.session_state.goals:
            df_goals = pd.DataFrame(st.session_state.goals)
            df_goals['Valor (R$)'] = df_goals['value'].apply(format_currency)
            df_goals['Guardado (R$)'] = df_goals['saved'].apply(format_currency)
            df_goals['Progresso (%)'] = (df_goals['saved'] / df_goals['value'] * 100).clip(upper=100).round(1)
            df_goals.index = df_goals.index + 1
            
            st.write("### Metas adicionadas")
            st.dataframe(df_goals[['name', 'Valor (R$)', 'Guardado (R$)', 'Progresso (%)']].rename(columns={'name':'Meta'}), use_container_width=True)
            
            # Interface de remoção
            to_remove = st.number_input('Remover meta (digite o índice, 0 = nenhum)', min_value=0, max_value=len(st.session_state.goals), value=0)
            if to_remove != 0:
                remove_goal(int(to_remove)-1)
                st.experimental_rerun()

    st.write("---")
    st.subheader("Resumo Financeiro")
    st.metric('Total de Metas', format_currency(financials['total_goals']))
    st.metric('Custo Mensal para Metas (12 meses)', format_currency(financials['monthly_goal_cost']))
    st.metric('Saldo Mensal Estimado', format_currency(financials['monthly_balance']))
    
    if financials['monthly_balance'] < 0:
        st.error('Atenção: Seu planejamento atual está com déficit. Reduza despesas ou aumente a renda.')
    else:
        st.success('Ótimo: Suas metas cabem no plano atual!')

st.write("---")

# --- Acompanhamento Mensal (Foco no Mês Atual) ---
st.header("3) Acompanhamento Mensal")

# Navegação entre meses
col_prev, col_title, col_next = st.columns([1, 2, 1])

with col_prev:
    if col_prev.button("⬅️ Mês Anterior", disabled=(get_current_month_index() == 0)):
        st.session_state.current_month_index -= 1
        st.experimental_rerun()

with col_title:
    current_date, current_month_name = get_month_info(get_current_month_index())
    st.subheader(f"Mês em Foco: {current_month_name}", anchor=False)

with col_next:
    if col_next.button("Próximo Mês ➡️", disabled=(get_current_month_index() == 11)):
        st.session_state.current_month_index += 1
        st.experimental_rerun()

st.write("---")

# Colunas para o acompanhamento do mês
col_fixed, col_real, col_progress = st.columns([1, 1, 1])
month_index = get_current_month_index()

with col_fixed:
    st.subheader("Contas Fixas Pagas")
    
    # Usando um formulário para salvar todos os pagamentos de uma vez
    with st.form(key=f'paid_form_{month_index}'):
        for exp in st.session_state.fixed_expenses_list:
            key = f'paid_{month_index}_{exp}'
            # Garante que o estado 'paid' está sincronizado
            if exp not in st.session_state.paid[month_index]:
                st.session_state.paid[month_index][exp] = False
            
            default_val = financials['fixed_values'].get(exp, 0.0)
            val = st.checkbox(f"{exp} - {format_currency(default_val)}", 
                              value=st.session_state.paid[month_index].get(exp, False), 
                              key=key)
            st.session_state.paid[month_index][exp] = val
        
        if st.form_submit_button('Salvar Pagamentos'):
            st.success(f'Pagamentos salvos para {current_month_name}!')
            st.experimental_rerun()

with col_real:
    st.subheader("Entradas e Saídas Reais")
    
    # Campos para entrada de dados reais do mês
    received_key = f'received_{month_index}'
    real_fixed_key = f'real_fixed_{month_index}'
    real_fun_key = f'real_fun_{month_index}'
    
    # Inicializa valores reais com os valores planejados como sugestão
    if received_key not in st.session_state:
        st.session_state[received_key] = financials['income_total']
    if real_fixed_key not in st.session_state:
        st.session_state[real_fixed_key] = financials['fixed_total']
    if real_fun_key not in st.session_state:
        st.session_state[real_fun_key] = st.session_state.fun_value

    received = st.number_input('Recebido Real (R$)', min_value=0.0, value=st.session_state[received_key], step=100.0, format="%.2f", key=received_key)
    real_fixed_spent = st.number_input('Contas Fixas Reais (R$)', min_value=0.0, value=st.session_state[real_fixed_key], step=50.0, format="%.2f", key=real_fixed_key)
    real_fun = st.number_input('Diversão Real (R$)', min_value=0.0, value=st.session_state[real_fun_key], step=50.0, format="%.2f", key=real_fun_key)
    
    # Cálculo do saldo real e quanto foi guardado
    real_saved = received - (real_fixed_spent + real_fun)
    real_balance = real_saved - financials['monthly_goal_cost']
    
    st.write("---")
    st.metric('Saldo Real do Mês', format_currency(real_balance))
    st.metric('Valor Guardado para Metas', format_currency(real_saved))
    
    # Atualiza o progresso das metas (simplificado: distribui o valor guardado igualmente entre as metas)
    if st.button('Atualizar Progresso das Metas'):
        if financials['total_goals'] > 0:
            # Distribui o valor guardado proporcionalmente ao valor de cada meta
            total_value = financials['total_goals']
            for goal in st.session_state.goals:
                # Calcula a proporção da meta em relação ao total
                proportion = goal['value'] / total_value
                # Adiciona o valor guardado proporcionalmente
                goal['saved'] += real_saved * proportion
                # Garante que o valor guardado não exceda o valor da meta
                goal['saved'] = min(goal['saved'], goal['value'])
            st.success("Progresso das metas atualizado!")
            st.experimental_rerun()
        else:
            st.warning("Nenhuma meta definida para atualizar o progresso.")

with col_progress:
    st.subheader("Progresso das Metas")
    
    if st.session_state.goals:
        for goal in st.session_state.goals:
            progress_pct = (goal['saved'] / goal['value']) if goal['value'] > 0 else 0
            progress_pct = min(1.0, progress_pct) # Limita a 100%
            
            st.write(f"**{goal['name']}** ({format_currency(goal['saved'])} / {format_currency(goal['value'])})")
            st.progress(progress_pct)
            
            if progress_pct >= 1.0:
                st.success("Meta Concluída!")
            elif progress_pct >= 0.75:
                st.info("Quase lá! Foco final.")
            elif progress_pct > 0:
                st.warning("Progresso em andamento.")
            else:
                st.error("Ainda não iniciada.")

st.write("---")

# --- Exportar / Download (Mantido) ---
st.header('4) Exportar Planejamento')

# Recria o DataFrame de planejamento para exportação (agora com 12 meses)
months_full = [get_month_info(i)[1] for i in range(12)]
plan_rows = []
for i, m in enumerate(months_full):
    plan_rows.append({
        'Mês': m,
        'Receita Planejada (R$)': financials['income_total'],
        'Despesas Fixas Planejadas (R$)': financials['fixed_total'],
        'Diversão Planejada (R$)': st.session_state.fun_value,
        'Meta Mensal (R$)': financials['monthly_goal_cost'],
        'Saldo Mensal Estimado (R$)': financials['monthly_balance']
    })
plan_df = pd.DataFrame(plan_rows)

st.dataframe(plan_df.style.format('{:,.2f}', subset=['Receita Planejada (R$)','Despesas Fixas Planejadas (R$)','Diversão Planejada (R$)','Meta Mensal (R$)','Saldo Mensal Estimado (R$)']), height=200, use_container_width=True)

if st.button('Exportar plano para CSV'):
    csv = plan_df.to_csv(index=False).encode('utf-8')
    st.download_button('Download CSV do plano', data=csv, file_name='mapa_de_sonhos_plano.csv', mime='text/csv')

st.write('\n---\n')
st.caption('Desenvolvido por Manus. Este é um MVP (Produto Mínimo Viável) para planejamento financeiro.')
