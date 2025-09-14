# 🚍 RoadWise – ClickBus | FIAP Enterprise Challenge

Este projeto apresenta o desenvolvimento completo de um **Data Warehouse moderno com Machine Learning aplicado à previsão de recompra de clientes da ClickBus**, realizado no contexto do **Enterprise Challenge FIAP**.  
A solução integra múltiplas fontes de dados, aplica técnicas avançadas de segmentação e previsão, e disponibiliza um **dashboard interativo** para apoiar a tomada de decisão do time de marketing.

---

## 📌 Visão Geral do Projeto
- **Arquitetura:** Camadas Bronze, Silver, Gold (Medallion Architecture) com extensão para **ML Layer**.  
- **Tech Stack:** SQL Server, Python (pandas, scikit-learn, XGBoost), Streamlit, GitHub, Notion, Draw.io.  
- **Pipeline:** ETL/ELT completo desde arquivos CSV brutos até insights de negócio consumíveis.  
- **Modelagem:** Estrutura dimensional em camadas e cálculo de features de clientes.  
- **Use Case:** Segmentação de clientes e previsão de recompra em 7 e 30 dias, priorizando ações de marketing.  

---

## 🗺️ Data Flow Diagram
O fluxo de dados percorre todas as camadas do Data Warehouse:

1. **Ingestão de dados brutos (ERP/CRM em CSV).**  
2. **Bronze Layer:** armazenamento fiel, sem transformações.  
3. **Silver Layer:** limpeza, padronização e enriquecimento de dados.  
4. **ML Layer:** segmentação de clientes (KMeans) e previsão de recompra (XGBoost).  
5. **Gold Layer:** disponibilização dos resultados finais em tabelas/views de consumo.  
6. **Dashboard RoadWise:** visualização executiva e ranking de clientes prioritários.  

---

## 🧱 Arquitetura

### 🔹 Bronze Layer
- **Propósito:** armazenar dados crus exatamente como recebidos.  
- **Dados:** tabelas físicas criadas via `ddl_bronze.sql`.  
- **Carga:** `proc_load_bronze.sql` com estratégia **TRUNCATE + INSERT**.  
- **Observação:** nenhuma transformação aplicada nesta camada.  

### 🔸 Silver Layer
- **Propósito:** limpar, padronizar e enriquecer os dados.  
- **Transformações:**  
  - Remoção de duplicidades (ROW_NUMBER).  
  - Tratamento de valores nulos/default.  
  - Enriquecimento com metadados.  
- **Tabelas principais:**  
  - `silver.purchases_clean`  
  - `silver.clients_features`  
- **Carga:** `proc_load_silver.sql`.  

### 🤖 ML Layer
- **Segmentação:** KMeans com 4 clusters (frequência, ticket médio, recência).  
- **Previsão de recompra:** modelos supervisionados XGBoost para janelas de 7 e 30 dias.  
- **Score de Prioridade:** cálculo ponderado entre outputs de ML + segmentação.  
- **Script principal:** [`predictions.py`](predictions.py).  
- **Exportação:** resultados gravados em `gold.customer_predictions` e `predictions.csv`.  

### 🟡 Gold Layer
- **Propósito:** servir dados prontos para análise e tomada de decisão.  
- **Objeto:** `gold.customer_predictions`.  
- **Conteúdo:**  
  - Probabilidades de recompra (7d e 30d).  
  - Segmento/persona atribuída.  
  - Score de prioridade para ação de marketing.  

---

## ⭐ Personas e Segmentos
A segmentação do RoadWise gerou quatro personas estratégicas:

1. **Clientes Regulares de Baixo Ticket**  
   - Ticket médio em torno de R$140  
   - Compras esporádicas (~3 na vida)  
   - Última compra há mais de 500 dias  

2. **Clientes de Alto Ticket e Baixa Frequência**  
   - Ticket médio elevado (~R$590)  
   - 1–2 compras na vida  
   - Última compra há mais de 800 dias  

3. **Clientes Frequentes e Fiéis**  
   - Ticket médio ~R$134  
   - Alta frequência (33 compras em média)  
   - Última compra recente (~70 dias)  

4. **Clientes Inativos ou Perdidos**  
   - Ticket médio ~R$146  
   - Poucas compras (1–2 na vida)  
   - Última compra há mais de 2000 dias  

---

## 🚀 ETL e ML – Passo a Passo

1. **Ingestão (Bronze):**  
   - Arquivos CSV carregados com `BULK INSERT`.  

2. **Transformação (Silver):**  
   - Normalização de colunas.  
   - Cálculo de métricas por cliente (recência, frequência, ticket médio).  

3. **Machine Learning (ML Layer):**  
   - Segmentação em clusters (KMeans).  
   - Previsão de recompra com XGBoost.  
   - Score de prioridade (clientes quentes).  

4. **Consumo (Gold + Dashboard):**  
   - Criação da tabela `gold.customer_predictions`.  
   - Exportação para `predictions.csv`.  
   - Visualização via dashboard interativo em Streamlit.  

---

## 📊 Dashboard RoadWise
Construído em **Streamlit** ([`app.py`](app.py)):

- **KPIs principais:**  
  - Clientes totais  
  - Ticket médio  
  - % clientes quentes (score ≥ 0.7)  
  - Receita potencial em 30 dias  

- **Funcionalidades:**  
  - Ranking filtrável de clientes por score, ticket e recência.  
  - Exportação de CSV para campanhas.  
  - Tabela interativa (AgGrid).  
  - Presets rápidos para diferentes estratégias de marketing.  

---

## 🔧 Tecnologias Utilizadas
- **Banco de Dados:** SQL Server Express  
- **ETL/ELT:** Procedures SQL (Bronze e Silver)  
- **Machine Learning:** Python (pandas, scikit-learn, XGBoost, pyodbc)  
- **Visualização:** Streamlit + AgGrid  
- **Documentação e Gestão:** GitHub, Notion, Draw.io  

---

## 📘 Conceitos Aplicados
- Medallion Architecture (Bronze → Silver → Gold + ML Layer)  
- ETL vs. ELT  
- Segmentação de clientes (KMeans)  
- Previsão de recompra (XGBoost)  
- Criação de personas acionáveis  
- Data cleansing e enrichment  
- Integração de DWH com ML e dashboard  

---

## 🗂️ Documentação
- **Scripts SQL:** `ddl_bronze.sql`, `ddl_silver.sql`, `proc_load_bronze.sql`, `proc_load_silver.sql`  
- **Scripts Python:** `predictions.py`, `app.py`  
- **Diagramas:** Arquitetura no Draw.io  
- **Versionamento:** GitHub  

---

## ✅ Entregáveis
- Data Warehouse em camadas (Bronze, Silver, Gold).  
- ML Layer integrado com segmentação e previsão.  
- Dashboard executivo em Streamlit.  
- Personas e score de prioridade para ação de marketing.  
- Documentação completa versionada no repositório.  

---

## 📈 Próximos Passos
- Implementar **Slowly Changing Dimensions (SCD Type 2)**.  
- Criar tabelas de snapshot para análises históricas.  
- Agendar cargas com **SQL Agent**.  
- Adicionar monitoramento e data quality checks.  
- Evoluir modelos de ML com labels reais e tuning avançado.  

---