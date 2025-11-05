# streamlit_mapa_de_sonhos_v2.py
# Mapa de Sonhos - Versão aprimorada (Minimalista & Elegante)
# Requer: streamlit, pandas, numpy, matplotlib, altair, fpdf

import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
from fpdf import FPDF
import base64
import json
import matplotlib.pyplot as plt
import altair as alt

# ------- Configuração da página -------
st.set_page_config(page_title="Mapa de Sonhos — MVP", layout="wide", initial_sidebar_state="expanded")

# ------- CSS minimalista -------
st.markdown("""
<style>
:root {
  --bg: #f7f7fa;
  --card: #ffffff;
  --muted: #6b7280;
  --accent: #0f766e;
  --danger: #ef4444;
}
[data-testid="stAppViewContainer"] > .main {
  background-color: var(--bg);
}
.header {
  font-family: 'Inter', sans-serif;
}
.card {
  background: var(--card);
  padding: 18px;
  border-radius: 12px;
  box-shadow: 0 6px 18px rgba(15,23,42,0.06);
}
.small-muted { color: var(--muted); font-size:13px; }
.accent { color: var(--accent); font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ------- Helpers -------
def currency(x):
    return f"R$ {x:,.2f}"

def compute_monthly_goal_cost(goals):
    total = sum([g['value'] for g in goals])
    return total, (total / 12 if total > 0 else 0.0)

def build_plan_df(income_total, fixed_total, fun_value, monthly_goal_cost):
    start = datetime.now().replace(day=1)
    months = [(start + pd.DateOffset(months=i)).strftime('%b %Y') for i in range(12)]
    rows = []
    for m in months:
        saldo = income_total - (fixed_total + fun_value + monthly_goal_cost)
        rows.append({
            'Mês': m,
            'Receita (R$)': income_total,
            'Despesas Fixas (R$)': fixed_total,
            'Diversão (R$)': fun_value,
            'Meta Mensal (R$)': monthly_goal_cost,
            'Saldo Mensal (R$)': saldo
        })
    return pd.DataFrame(rows)

def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode('utf-8')

def save_project_to_bytes(state):
    return json.dumps(state, ensure_ascii=False, indent=2).encode('utf-8')

def create_pdf_summary(project_state: dict, plan_df: pd.DataFrame, filename="resumo_mapa_de_sonhos.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Mapa de Sonhos - Resumo", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Metas", ln=True)
    pdf.set_font("Arial", size=11)
    if project_state['goals']:
        for g in project_state['goals']:
            pdf.cell(0, 6, f"- {g['name']}: R$ {g['value']:,.2f}", ln=True)
    else:
        pdf.cell(0, 6, "Nenhuma meta cadastrada.", ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Resumo Financeiro Mensal (média)", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 6, f"Receita total mensal: R$ {project_state['income_total']:,.2f}", ln=True)
    pdf.cell(0, 6, f"Despesas fixas mensais: R$ {project_state['fixed_total']:,.2f}", ln=True)
    pdf.cell(0, 6, f"Diversão mensal: R$ {project_state['fun_value']:,.2f}", ln=True)
    pdf.cell(0, 6, f"Meta mensal total: R$ {project_state['monthly_goal_cost']:,.2f}", ln=True)
    pdf.cell(0, 6, f"Saldo mensal médio: R$ {project_state['monthly_balance']:,.2f}", ln=True)
    pdf.ln(8)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, "Observação: este PDF é um resumo gerado automaticamente pelo MVP. Para recomendações personalizadas considere validar dados reais e consultar orientação financeira.")
    # Return bytes
    return pdf.output(dest='S').encode('latin-1')

# ------- State init -------
if 'goals' not in st.session_state:
    st.session_state.goals = []
if 'fixed_expenses' not in st.session_state:
    st.session_state.fixed_expenses = {
        'Internet': 100.0, 'Luz': 150.0, 'Conta de celular': 80.0, 'Faculdade': 0.0,
        'Academia': 120.0, 'Gasolina': 300.0, 'Água': 60.0, 'Aluguel': 1200.0,
        'Parcela do carro': 0.0, 'Corte de cabelo': 60.0, 'Unha': 50.0
    }
if 'salary' not in st.session_state:
    st.session_state.salary = 5000.0
if 'extra' not in st.session_state:
    st.session_state.extra = 1200.0
if 'fun_value' not in st.session_state:
    st.session_state.fun_value = 300.0

# ------- Layout -------
st.markdown('<div class="header"><h1 style="margin:0">Mapa de Sonhos</h1><div class="small-muted">Planeje suas metas para 12 meses — versão MVP aprimorada</div></div>', unsafe_allow_html=True)
st.write('')

# Sidebar: project management
with st.sidebar:
    st.markdown("### Projeto")
    if st.button("Novo projeto (limpar)"):
        st.session_state.goals = []
        st.session_state.salary = 5000.0
        st.session_state.extra = 1200.0
        st.session_state.fixed_expenses = st.session_state.fixed_expenses  # keep template
        st.session_state.fun_value = 300.0
        st.success("Projeto resetado (dados em sessão limpos).")

    uploaded_json = st.file_uploader("Carregar projeto (JSON)", type=['json'])
    if uploaded_json is not None:
        try:
            data = json.load(uploaded_json)
            st.session_state.goals = data.get('goals', [])
            st.session_state.salary = data.get('salary', st.session_state.salary)
            st.session_state.extra = data.get('extra', st.session_state.extra)
            st.session_state.fixed_expenses = data.get('fixed_expenses', st.session_state.fixed_expenses)
            st.session_state.fun_value = data.get('fun_value', st.session_state.fun_value)
            st.success("Projeto carregado.")
        except Exception as e:
            st.error("Erro ao carregar projeto: " + str(e))

    if st.button("Salvar projeto (download JSON)"):
        proj = {
            'goals': st.session_state.goals,
            'salary': st.session_state.salary,
            'extra': st.session_state.extra,
            'fixed_expenses': st.session_state.fixed_expenses,
            'fun_value': st.session_state.fun_value
        }
        b = save_project_to_bytes(proj)
        st.download_button("Download JSON do projeto", data=b, file_name="mapa_de_sonhos_projeto.json", mime="application/json")

    st.markdown("---")
    st.markdown("### Exportar")
    # placeholder for exports filled later (main area triggers)
    st.info("Use os botões na área principal para exportar CSV / PDF do plano.")
    st.markdown("---")
    st.markdown("Versão MVP aprimorada — Minimalista • 2025")

# ------- Main: input forms -------
col1, col2 = st.columns([2, 3])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("1 — Metas (12 meses)")
    with st.form("form_goal"):
        g_name = st.text_input("Nome da meta", placeholder="Ex: Carro, Viagem, Reserva de emergência")
        g_value = st.number_input("Valor total da meta (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
        add = st.form_submit_button("Adicionar / Atualizar meta")
        if add:
            if not g_name.strip():
                st.error("Digite um nome válido para a meta.")
            else:
                # if exists by name, update
                found = False
                for g in st.session_state.goals:
                    if g['name'].lower() == g_name.strip().lower():
                        g['value'] = float(g_value)
                        found = True
                        break
                if not found:
                    st.session_state.goals.append({'name': g_name.strip(), 'value': float(g_value)})
                st.success("Meta adicionada/atualizada.")
    # list and remove
    if st.session_state.goals:
        goals_df = pd.DataFrame(st.session_state.goals)
        goals_df.index = range(1, len(goals_df)+1)
        st.table(goals_df.rename(columns={'name':'Meta','value':'Valor (R$)'}))
        idx_remove = st.number_input("Remover meta (índice, 0 = nenhum)", min_value=0, max_value=len(st.session_state.goals), value=0, step=1)
        if st.button("Remover índice"):
            if idx_remove > 0:
                try:
                    removed = st.session_state.goals.pop(int(idx_remove)-1)
                    st.success(f"Removida meta: {removed['name']}")
                except Exception as e:
                    st.error("Erro ao remover: " + str(e))
    else:
        st.write("_Nenhuma meta adicionada ainda._")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("2 — Receitas & Despesas")
    with st.form("form_income"):
        st.session_state.salary = st.number_input("Salário fixo (R$)", min_value=0.0, value=float(st.session_state.salary), step=100.0, format="%.2f")
        st.session_state.extra = st.number_input("Renda extra média mensal (R$)", min_value=0.0, value=float(st.session_state.extra), step=100.0, format="%.2f")
        st.markdown("**Contas fixas (edite os valores)**")
        fe = st.session_state.fixed_expenses.copy()
        # Editable table via inputs
        for k in list(fe.keys()):
            fe[k] = st.number_input(f"R$ - {k}", min_value=0.0, value=float(fe[k]), step=10.0, format="%.2f", key=f"fe_{k}")
        st.session_state.fixed_expenses = fe
        st.session_state.fun_value = st.number_input("Conta de diversão mensal (R$)", min_value=0.0, value=float(st.session_state.fun_value), step=10.0, format="%.2f")
        save_income = st.form_submit_button("Salvar receitas e despesas")
        if save_income:
            st.success("Receitas e despesas atualizadas.")
    st.markdown('</div>', unsafe_allow_html=True)

# ------- Calculations -------
total_goals, monthly_goal_cost = compute_monthly_goal_cost(st.session_state.goals)
income_total = float(st.session_state.salary) + float(st.session_state.extra)
fixed_total = sum([v for v in st.session_state.fixed_expenses.values()])
fun_value = float(st.session_state.fun_value)
monthly_balance = income_total - (fixed_total + fun_value + monthly_goal_cost)
plan_df = build_plan_df(income_total, fixed_total, fun_value, monthly_goal_cost)

# ------- KPIs -------
k1, k2, k3, k4 = st.columns([1.5,1.2,1.2,1.2])
k1.metric("Total metas (R$)", currency(total_goals))
k2.metric("Meta mensal (R$)", currency(monthly_goal_cost))
k3.metric("Receita mensal (R$)", currency(income_total))
k4.metric("Saldo médio (R$)", currency(monthly_balance if monthly_balance is not None else 0.0))

# ------- Feedback and action when negative -------
st.write("")
if monthly_balance < 0:
    deficit = abs(monthly_balance)
    st.error(f"Saldo médio negativo — déficit mensal: {currency(deficit)}")
    st.warning("Para atingir suas metas, será preciso criar um planejamento alternativo.")
    opt = st.selectbox("Como deseja prosseguir?", [
        "Trabalho CLT e gostaria de ser promovido",
        "Quero empreender",
        "Empreendo mas estou com dificuldades",
        "Quero reduzir o valor da meta"
    ])
    if st.button("Receber material de orientação (eBook)"):
        texts = {
            "Trabalho CLT e gostaria de ser promovido": "Guia rápido: ações para visibilidade, feedback e resultados mensuráveis para pedir promoção.",
            "Quero empreender": "Guia rápido: validar ideia, testar MVP, controlar fluxo de caixa e primeiros passos.",
            "Empreendo mas estou com dificuldades": "Guia rápido: funil, redução de custos fixos, foco em clientes recorrentes.",
            "Quero reduzir o valor da meta": "Guia rápido: priorizar metas, renegociar prazos, parcelar estrategicamente."
        }
        pdf_bytes = create_pdf_summary({
            'goals': st.session_state.goals,
            'income_total': income_total,
            'fixed_total': fixed_total,
            'fun_value': fun_value,
            'monthly_goal_cost': monthly_goal_cost,
            'monthly_balance': monthly_balance
        }, plan_df)
        st.download_button("Baixar eBook (PDF)", data=pdf_bytes, file_name="orientacao_mapa_de_sonhos.pdf", mime="application/pdf")

# ------- Visualizações -------
st.markdown("---")
colA, colB = st.columns([2,1])

with colA:
    st.subheader("Planejamento 12 meses — Tabela & Gráfico")
    st.dataframe(plan_df, height=280)
    # Line chart (saldo mensal)
    line = alt.Chart(plan_df.reset_index()).mark_line(point=True).encode(
        x='Mês',
        y=alt.Y('Saldo Mensal (R$)', title='Saldo (R$)'),
        tooltip=['Mês','Saldo Mensal (R$)']
    ).properties(width=800, height=250)
    st.altair_chart(line, use_container_width=True)

with colB:
    st.subheader("Composição mensal")
    # Pie: fixed / fun / goals
    comp = pd.DataFrame({
        'categoria': ['Despesas fixas','Diversão','Meta mensal'],
        'valor': [fixed_total, fun_value, monthly_goal_cost]
    })
    fig1, ax1 = plt.subplots(figsize=(4,4))
    ax1.pie(comp['valor'], labels=comp['categoria'], autopct=lambda pct: f"{pct:.0f}%\n({currency(pct/100*comp['valor'].sum()):s})", startangle=90, wedgeprops={'linewidth': 0.5, 'edgecolor': 'white'})
    ax1.axis('equal')
    st.pyplot(fig1)

st.markdown("---")

# ------- Progresso por meta -------
st.subheader("Progresso por meta (simulação)")
if st.session_state.goals:
    gcols = st.columns(1)
    funded_per_month = max(0.0, (income_total - (fixed_total + fun_value)))  # quanto sobra para metas
    if monthly_goal_cost > 0:
        for g in st.session_state.goals:
            percent = min(1.0, funded_per_month / monthly_goal_cost * (g['value'] / total_goals)) if total_goals>0 else 0
            pct_display = int(percent*100)
            st.markdown(f"**{g['name']}** — {currency(g['value'])}")
            st.progress(pct_display/100.0)
            st.caption(f"{pct_display}% estimado coberto por mês com base no fluxo atual (simulação).")
else:
    st.info("Adicione metas para visualizar o progresso individual.")

# ------- Acompanhamento mensal simplificado -------
st.markdown("---")
st.subheader("Atualização mensal (rápida)")
mcol1, mcol2, mcol3 = st.columns([1.2,1,1])
sel_month = st.selectbox("Mês", plan_df['Mês'].tolist())
with st.form("monthly_update"):
    received = st.number_input("Quanto recebeu este mês (R$)", min_value=0.0, value=float(income_total), step=50.0, format="%.2f")
    real_fixed = st.number_input("Gastou em contas fixas (R$)", min_value=0.0, value=float(fixed_total), step=50.0, format="%.2f")
    real_fun = st.number_input("Gastou em diversão (R$)", min_value=0.0, value=float(fun_value), step=10.0, format="%.2f")
    upd = st.form_submit_button("Atualizar e calcular indicador")
    if upd:
        real_balance = received - (real_fixed + real_fun + monthly_goal_cost)
        st.metric(f"Saldo real — {sel_month}", currency(real_balance))
        # progress toward monthly goals funding
        if monthly_goal_cost > 0:
            funded = max(0.0, (received - (real_fixed + real_fun)) / monthly_goal_cost)
            pct = min(1.0, funded)
            st.progress(pct)
            if pct >= 1.0:
                st.success("Você está financiando a meta mensal!")
            elif pct >= 0.6:
                st.warning("Quase lá — pequeno ajuste e você alcança.")
            else:
                st.error("Faltam recursos; reveja despesas ou metas.")

# ------- Export buttons -------
st.markdown("---")
st.subheader("Exportar plano e relatórios")
export_col1, export_col2, export_col3 = st.columns([1,1,1])
with export_col1:
    csv_bytes = df_to_csv_bytes(plan_df)
    st.download_button("Baixar CSV do plano", data=csv_bytes, file_name="mapa_de_sonhos_plano.csv", mime="text/csv")
with export_col2:
    # JSON project
    project = {
        'goals': st.session_state.goals,
        'salary': st.session_state.salary,
        'extra': st.session_state.extra,
        'fixed_expenses': st.session_state.fixed_expenses,
        'fun_value': st.session_state.fun_value,
        'generated_at': datetime.now().isoformat()
    }
    st.download_button("Baixar projeto (JSON)", data=json.dumps(project, ensure_ascii=False, indent=2).encode('utf-8'), file_name="mapa_de_sonhos_projeto.json", mime="application/json")
with export_col3:
    pdf_bytes = create_pdf_summary({
        'goals': st.session_state.goals,
        'income_total': income_total,
        'fixed_total': fixed_total,
        'fun_value': fun_value,
        'monthly_goal_cost': monthly_goal_cost,
        'monthly_balance': monthly_balance
    }, plan_df)
    st.download_button("Baixar resumo (PDF)", data=pdf_bytes, file_name="resumo_mapa_de_sonhos.pdf", mime="application/pdf")

st.markdown("<div class='small-muted'>Dica: use o botão JSON para salvar seu progresso entre sessões de teste.</div>", unsafe_allow_html=True)
