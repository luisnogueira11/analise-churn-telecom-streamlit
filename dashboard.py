import streamlit as st
import pandas as pd
import joblib
import plotly.express as px

st.set_page_config(
    page_title="Dashboard de Previsão de Churn",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def carregar_dados_e_modelos():
    df_final = pd.read_csv('data/04_final/dados_processados.csv')
    df_original = pd.read_csv('data/04_final/dados_originais.csv')
    modelo = joblib.load('models/modelo_churn.pkl')
    scaler = joblib.load('models/scaler.pkl')
    features = df_final.drop('Churn', axis=1).columns
    return df_final, df_original, modelo, scaler, features

df_final, df_original, modelo, scaler, features = carregar_dados_e_modelos()

try:
    st.sidebar.image('imagem/telecom_logo.jpg', width=150)
except:
    st.sidebar.title("Logo")

st.sidebar.header("Análise de Churn Telecom")
st.sidebar.markdown("""
---
Este dashboard apresenta uma análise interativa sobre a evasão (churn) de clientes
de uma empresa de telecomunicações, incluindo a previsão de receita e insights
para estratégias de retenção.
""")

st.title("📊 Dashboard de Análise de Churn e Receita")

tab1, tab2, tab3 = st.tabs(["Visão Geral e Impacto Financeiro", "Diagnóstico dos Fatores de Churn", "Plano de Ação e Recomendações"])

# Aba 1: Impacto Financeiro
with tab1:
    st.header("Previsão de Receita e Impacto do Churn")

    X = df_final.drop('Churn', axis=1)
    X_scaled = scaler.transform(X)
    previsoes = modelo.predict(X_scaled)
    
    df_original['ChurnPrediction'] = previsoes
    
    receita_dos_churners = df_original[df_original['ChurnPrediction'] == 1]['MonthlyCharges'].sum()
    receita_total_completa = df_original['MonthlyCharges'].sum()
    
    taxa_perda_mensal = receita_dos_churners / receita_total_completa if receita_total_completa > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Receita Mensal Atual", f"R$ {receita_total_completa:,.2f}")
    col2.metric("Perda Mensal Estimada", f"R$ {receita_dos_churners:,.2f}", f"{taxa_perda_mensal:.2%}")

    projecao = []
    receita_atual = receita_total_completa
    for _ in range(6):
        perda_mes = receita_atual * taxa_perda_mensal
        receita_atual -= perda_mes
        projecao.append(receita_atual)

    df_projecao = pd.DataFrame({
        'Mês': range(1, 7),
        'Receita Prevista': projecao
    })

    col3.metric("Receita Prevista (6 meses)", f"R$ {projecao[-1]:,.2f}")

    fig_projecao = px.line(df_projecao, x='Mês', y='Receita Prevista', title='Projeção de Receita para os Próximos 6 Meses', markers=True)
    fig_projecao.update_layout(yaxis_title='Receita (R$)', xaxis_title='Mês')
    st.plotly_chart(fig_projecao, use_container_width=True)

# Aba 2: Diagnóstico
with tab2:
    st.header("Diagnóstico: Por que os Clientes Saem?")
    
    importancia_features = pd.DataFrame({
        'Feature': features,
        'Importance': abs(modelo.coef_[0])
    }).sort_values(by='Importance', ascending=False)

    fig_importancia = px.bar(importancia_features.head(10), x='Importance', y='Feature', orientation='h', title='Top 10 Fatores que Influenciam o Churn')
    st.plotly_chart(fig_importancia, use_container_width=True)

    st.markdown("### Análise Detalhada por Fator")
    fator_selecionado = st.selectbox("Selecione um fator para analisar:", ['Contract', 'InternetService', 'tenure', 'PaymentMethod'])

    if fator_selecionado == 'tenure':
        bins = [0, 12, 24, 48, 60, 100] 
        labels = ['0-1 ano', '1-2 anos', '2-4 anos', '4-5 anos', '> 5 anos']
        df_original['TenureGroup'] = pd.cut(df_original['tenure'], bins=bins, labels=labels, right=False)
        df_analise_churn = df_original.groupby('TenureGroup')['Churn'].value_counts(normalize=True).mul(100).rename('percent').reset_index()
        fig_detalhe = px.bar(df_analise_churn[df_analise_churn['Churn']=='Yes'], x='TenureGroup', y='percent', title=f'Taxa de Churn por Tempo de Contrato', labels={'percent': '% de Churn', 'TenureGroup': 'Tempo de Contrato'})
    else:
        df_analise_churn = df_original.groupby(fator_selecionado)['Churn'].value_counts(normalize=True).mul(100).rename('percent').reset_index()
        fig_detalhe = px.bar(df_analise_churn[df_analise_churn['Churn']=='Yes'], x=fator_selecionado, y='percent', title=f'Taxa de Churn por {fator_selecionado}', labels={'percent': '% de Churn'})
    
    st.plotly_chart(fig_detalhe, use_container_width=True)


# Aba 3: Plano de Ação
with tab3:
    st.header("Plano de Ação e Recomendações Estratégicas")

    st.subheader("Foco em Contratos de Curto Prazo")
    st.markdown("""
    - **Insight:** Clientes com contratos mensais (`Month-to-month`) apresentam a maior taxa de churn.
    - **Ação Sugerida:** Desenvolver campanhas de marketing para incentivar a migração para planos anuais ou bianuais, oferecendo descontos progressivos ou benefícios exclusivos (ex: um serviço de streaming gratuito).
    """)

    st.subheader("Fortalecimento de Serviços de Suporte e Segurança")
    st.markdown("""
    - **Insight:** A ausência de serviços como Suporte Técnico (`TechSupport`) e Segurança Online (`OnlineSecurity`) é um forte indicador de churn.
    - **Ação Sugerida:** Criar um "pacote de valor" com esses serviços e oferecê-lo de forma proativa para clientes que não os possuem, possivelmente com um período de teste gratuito para demonstrar seu valor.
    """)

    st.subheader("Programa de Onboarding para Novos Clientes")
    st.markdown("""
    - **Insight:** O churn é significativamente maior nos primeiros 12 meses de contrato.
    - **Ação Sugerida:** Implementar um programa de "onboarding" robusto nos primeiros 3 meses. Isso pode incluir contatos proativos da equipe de sucesso do cliente, tutoriais sobre como usar os serviços e ofertas personalizadas para aumentar o engajamento inicial.
    """)