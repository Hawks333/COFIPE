# README.md
- Lista editável de contas fixas (internet, aluguel, academia, etc.) e valor para diversão.


3. **Planejamento anual automático**
- Geração de tabela com receitas, despesas, metas e saldo de cada mês.
- Exibição de saldo médio mensal.


4. **Mensagens inteligentes**
- Se o saldo for negativo, o app recomenda um planejamento alternativo e oferece eBooks diferentes conforme a situação escolhida (CLT, empreendedor, redução de metas etc.).


5. **Acompanhamento mensal**
- Marcação de contas pagas mês a mês.
- Atualização manual de valores recebidos e gastos reais.
- Indicador de progresso mostrando se o usuário está no caminho certo.


6. **Exportação**
- Download do plano financeiro completo em formato CSV.


---


## 🧩 Instalação e execução


1. **Clone o repositório:**
```bash
git clone https://github.com/SEU_USUARIO/mapa-de-sonhos.git
cd mapa-de-sonhos
```


2. **Crie um ambiente virtual (opcional, mas recomendado):**
```bash
python -m venv venv
source venv/bin/activate # (Linux/macOS)
venv\Scripts\activate # (Windows)
```


3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```


4. **Execute o aplicativo:**
```bash
streamlit run streamlit_mapa_de_sonhos.py
```


5. **Acesse no navegador:**
O Streamlit exibirá um link como:
```
Local URL: http://localhost:8501
```
Abra esse endereço e teste o app.


---


## 📊 Exemplo de uso


1. Adicione metas com seus valores reais.
2. Informe sua renda mensal e as despesas fixas.
3. Veja o custo mensal total e o saldo estimado.
4. Se o saldo for negativo, o app sugerirá planos alternativos.
5. Atualize mensalmente quanto recebeu e gastou para acompanhar seu progresso.


---


## 🎨 Visual e personalização


O aplicativo utiliza um layout simples e claro, adequado para MVPs. Pode ser facilmente aprimorado com:
- Temas customizados via `st.markdown()` e CSS;
- Ícones e cores personalizadas com emojis;
- Integração com banco de dados (Firebase, Supabase) para salvar dados do usuário.


---


## 🚀 Próximos passos sugeridos
- [ ] Implementar login e múltiplos usuários.
- [ ] Adicionar backup em nuvem.
- [ ] Criar versão mobile-friendly.
- [ ] Adicionar gráficos de evolução financeira.
- [ ] Publicar na Streamlit Cloud.


---


## 👨‍💻 Autor
Desenvolvido por **[Seu Nome]** — MVP inspirado no conceito *Mapa de Sonhos*, para ajudar pessoas a planejarem e realizarem suas metas financeiras de forma prática e inspiradora.


📧 Contato: seuemail@exemplo.com
