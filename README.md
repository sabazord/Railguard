# 🚂 RailGuard AI — Plataforma de Compliance Preditivo Ferroviário

> **MVP Demonstrativo — Dados 100% Simulados**
>
> Esta plataforma é um MVP acadêmico/demonstrativo. Todos os dados, métricas, scores
> e indicadores são fictícios e simulados. Não há integração com órgãos reguladores
> (ANTT, ANAC, etc.) nem com operadores ferroviários reais.

---

## 📋 Sumário

1. [Sobre o Projeto](#sobre-o-projeto)
2. [Funcionalidades](#funcionalidades)
3. [Estrutura de Arquivos](#estrutura-de-arquivos)
4. [Requisitos](#requisitos)
5. [Instalação](#instalação)
6. [Como Rodar](#como-rodar)
7. [Módulos e Arquitetura](#módulos-e-arquitetura)
8. [Motor de Risco](#motor-de-risco)
9. [RCRS — Railway Compliance Risk Score](#rcrs)
10. [Modelo Preditivo (ML)](#modelo-preditivo)
11. [Dados de Demonstração](#dados-de-demonstração)
12. [Migração para PostgreSQL](#migração-para-postgresql)
13. [Roadmap de Evolução](#roadmap-de-evolução)
14. [Tecnologias](#tecnologias)

---

## Sobre o Projeto

**RailGuard AI** é uma plataforma inteligente voltada para:

- **Manutenção Preditiva Ferroviária** — score de risco calculado por motor de regras e validado por modelo de ML
- **Compliance Regulatório** — Railway Compliance Risk Score (RCRS) integrado
- **Rastreabilidade Técnica** — registro completo de inspeções, ativos e trechos
- **Auditoria Operacional** — log imutável de todas as ações no sistema
- **Indicadores ESG** — métricas ambientais, sociais e de governança simplificadas

---

## Funcionalidades

| Módulo | Descrição |
|---|---|
| 📊 **Dashboard** | KPIs gerais, gráficos de risco e alertas ativos |
| 🛤️ **Trechos** | Cadastro e consulta de trechos ferroviários |
| ⚙️ **Ativos** | Cadastro de trilhos, dormentes, pontes, AMVs e outros |
| 🔍 **Inspeções** | Registro de inspeções com cálculo automático de risco |
| 🤖 **Modelo Preditivo** | RandomForest com métricas, importância de variáveis e predição interativa |
| 📋 **Compliance** | Visão geral do RCRS e cálculo manual |
| 🗂️ **Auditoria** | Log completo de todas as ações com filtros |
| 🌿 **ESG** | Indicadores ambientais, de paralisação e eficiência de manutenção |
| 📄 **Relatórios** | Relatório completo por ativo ou trecho com exportação CSV |
| ⚙️ **Configurações** | Informações do sistema e instruções de migração para PostgreSQL |

---

## Estrutura de Arquivos

```
railguard_ai/
│
├── app.py              # Aplicação Streamlit principal (roteamento e UI)
├── database.py         # Conexão, criação de tabelas e todas as operações CRUD
├── models.py           # Constantes de domínio: tipos, pesos, listas de opções
├── risk_engine.py      # Motor de risco: calcular_risco_operacional() e calcular_rcrs()
├── ml_model.py         # Modelo preditivo RandomForest com treino, métricas e predição
├── reports.py          # Geração e exportação de relatórios de compliance
├── seed_data.py        # Dados de demonstração fictícios para popular o banco
├── requirements.txt    # Dependências do projeto
├── README.md           # Esta documentação
│
└── data/
    └── railguard.db    # Banco SQLite (criado automaticamente ao rodar)
```

---

## Requisitos

- **Python** 3.11 ou superior
- **pip** atualizado
- Sistema Operacional: Windows, macOS ou Linux

---

## Instalação

### 1. Clone ou copie o projeto

```bash
# Se usar git:
git clone https://github.com/seu-usuario/railguard-ai.git
cd railguard-ai

# Ou simplesmente acesse a pasta onde os arquivos foram salvos:
cd railguard_ai
```

### 2. Crie e ative o ambiente virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Como Rodar

```bash
streamlit run app.py
```

O Streamlit abrirá automaticamente no navegador em `http://localhost:8501`.

Na **primeira execução**, o sistema:
1. Cria o banco SQLite em `data/railguard.db`
2. Cria todas as tabelas automaticamente
3. Popula o banco com dados de demonstração (3 ferrovias, 8 trechos, 22 ativos, 40+ inspeções)

> Para resetar os dados, acesse **Configurações → Recarregar Demo** na barra lateral.

---

## Módulos e Arquitetura

### `database.py`
Responsável por toda a camada de persistência:
- `init_database()` — cria as tabelas ao iniciar
- `get_connection()` — retorna conexão SQLite (substituir por SQLAlchemy na migração)
- Funções CRUD para cada entidade: `insert_*`, `get_*`, `update_*`
- `get_dashboard_stats()` — totalizadores para o painel
- `insert_auditoria()` — registra log em toda operação de escrita

### `models.py`
Define constantes do domínio ferroviário:
- Listas de tipos, estados, ferrovias
- Pesos numéricos para criticidade e condição visual
- Mapeamentos de cores por nível de risco
- Nomes das features de ML

### `risk_engine.py`
Motor central de cálculo de risco:
- `calcular_risco_operacional()` — score 0–100 com contribuições por fator
- `calcular_rcrs()` — Railway Compliance Risk Score com recomendação automática
- `gerar_explicabilidade()` — texto em linguagem natural sobre a classificação
- `calcular_esg_indicators()` — indicadores ESG paramétricos

### `ml_model.py`
Módulo de Machine Learning:
- `gerar_dados_sinteticos()` — dataset gerado pelo motor de risco (oráculo)
- `preparar_features_reais()` — constrói matriz de features dos dados reais
- `treinar_modelo()` — RandomForestClassifier com split 80/20
- `get_feature_importance()` — importância das variáveis
- `prever_risco()` — predição com probabilidades por classe

### `seed_data.py`
Gerador de dados de demonstração:
- 3 ferrovias reais do Brasil (dados públicos genéricos)
- 8 trechos com características variadas
- 22 ativos de diferentes tipos
- 40+ inspeções com anomalias distribuídas por perfil de risco
- Scores RCRS calculados automaticamente

### `reports.py`
Geração e exportação de relatórios:
- `gerar_relatorio_ativo()` — consolida dados completos de um ativo
- `relatorio_para_csv()` — exporta relatório em formato CSV
- `relatorio_trecho_para_csv()` — relatório completo de um trecho

---

## Motor de Risco

A função `calcular_risco_operacional()` gera um score de 0 a 100 com base nos seguintes fatores e pesos:

| Fator | Peso Máximo |
|---|---|
| Presença de fissura | 15 pts |
| Falha de fixação | 10 pts |
| Idade do ativo | 20 pts |
| Tempo sem manutenção | 15 pts |
| Criticidade operacional | 15 pts |
| Vibração | 10 pts |
| Desgaste | 8 pts |
| Corrosão | 8 pts |
| Condição visual | 10 pts |

**Classificação:**

| Score | Nível |
|---|---|
| 0 – 25 | 🟢 Baixo |
| 26 – 50 | 🟡 Médio |
| 51 – 75 | 🟠 Alto |
| 76 – 100 | 🔴 Crítico |

---

## RCRS

O **Railway Compliance Risk Score** combina múltiplas dimensões:

| Componente | Peso |
|---|---|
| Score de Risco Operacional | 35% |
| Criticidade do Trecho | 20% |
| Histórico de Falhas | 15% |
| Impacto Regulatório | 15% |
| Risco ESG | 10% |
| Penalidade por baixa confiabilidade do dado | 5% |

**Classificação RCRS:**

| Score | Classificação |
|---|---|
| 0 – 25 | ✅ Conforme |
| 26 – 50 | ⚠️ Atenção |
| 51 – 75 | 🔶 Não conformidade potencial |
| 76 – 100 | 🔴 Crítico |

---

## Modelo Preditivo

- **Algoritmo:** `RandomForestClassifier` (scikit-learn)
- **Target:** Nível de risco (Baixo / Médio / Alto / Crítico)
- **Features:** 10 variáveis (idade, manutenção, criticidade, anomalias, vibração, carga, condição visual)
- **Dataset:** Dados sintéticos gerados pelo motor de risco como oráculo (600–1000 amostras) + dados reais cadastrados
- **Split:** 80% treino / 20% teste, estratificado
- **Métrica principal:** Acurácia + Relatório de Classificação por classe

### Extensões futuras previstas

```python
# Integração com SHAP (explicabilidade baseada em valores de Shapley)
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)
shap.summary_plot(shap_values, X_test, feature_names=ML_FEATURE_NAMES)
```

---

## Dados de Demonstração

Os dados de demonstração incluem:

- **3 ferrovias:** MRS Logística, Rumo Malha Paulista, VLI — Ferrovia Centro-Atlântica
- **8 trechos** distribuídos nos estados SP, PR, MG, BA, PA, RS
- **22 ativos** de tipos variados (trilho, dormente, ponte, AMV, sinalização, fixação)
- **Perfis de risco** distribuídos: Ótimo, Bom, Regular, Ruim e Crítico
- **40+ inspeções** com parâmetros gerados por perfil de condição visual
- **Scores RCRS e alertas** calculados automaticamente

> ⚠️ Todos os dados são **fictícios** e criados apenas para fins de demonstração.

---

## Migração para PostgreSQL

Para migrar de SQLite para PostgreSQL em ambiente de produção:

### 1. Instalar dependências

```bash
pip install psycopg2-binary sqlalchemy
```

### 2. Substituir `get_connection()` em `database.py`

```python
# Antes (SQLite):
import sqlite3
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

# Depois (PostgreSQL com SQLAlchemy):
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://railguard_user:senha_segura@localhost:5432/railguard_db"
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10)

def get_connection():
    return engine.connect()
```

### 3. Ajustar os placeholders de parâmetros

```python
# SQLite usa '?'
cur.execute("SELECT * FROM ativos WHERE id = ?", (ativo_id,))

# PostgreSQL com psycopg2 usa '%s'
cur.execute("SELECT * FROM ativos WHERE id = %s", (ativo_id,))

# PostgreSQL com SQLAlchemy usa ':param'
conn.execute(text("SELECT * FROM ativos WHERE id = :id"), {"id": ativo_id})
```

### 4. Ajustar o DDL de criação de tabelas

```sql
-- SQLite:
id INTEGER PRIMARY KEY AUTOINCREMENT

-- PostgreSQL:
id SERIAL PRIMARY KEY

-- Timestamps:
-- SQLite: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- PostgreSQL: TIMESTAMPTZ DEFAULT NOW()
```

### 5. Migrar dados existentes

```python
import pandas as pd
from sqlalchemy import create_engine

src = sqlite3.connect("data/railguard.db")
dst = create_engine("postgresql://user:senha@host/railguard_db")

for tabela in ["trechos", "ativos", "inspecoes", "riscos", "alertas", "auditoria", "indicadores_esg"]:
    df = pd.read_sql_query(f"SELECT * FROM {tabela}", src)
    df.to_sql(tabela, dst, if_exists="append", index=False)
    print(f"✅ {tabela}: {len(df)} registros migrados")
```

---

## Roadmap de Evolução

| Fase | Recurso |
|---|---|
| v0.2 | Integração SHAP para explicabilidade avançada |
| v0.2 | Upload e visualização de imagens de inspeção |
| v0.2 | Exportação de relatórios em PDF (fpdf2 / reportlab) |
| v0.3 | Autenticação de usuários (streamlit-authenticator) |
| v0.3 | Migração para PostgreSQL + Docker Compose |
| v0.4 | Ingestão de dados via API REST (FastAPI) |
| v0.4 | Integração com sensores IoT (MQTT / Kafka) |
| v0.5 | Modelos de séries temporais para previsão de degradação |
| v0.5 | Dashboard gerencial com mapa geoespacial dos trechos |
| v1.0 | Deploy em nuvem (AWS / Azure / GCP) com CI/CD |

---

## Tecnologias

| Tecnologia | Versão | Uso |
|---|---|---|
| Python | 3.11+ | Linguagem principal |
| Streamlit | ≥ 1.35 | Interface web |
| SQLite | embutido | Banco de dados (MVP) |
| Pandas | ≥ 2.1 | Manipulação de dados |
| NumPy | ≥ 1.26 | Cálculos numéricos |
| Plotly | ≥ 5.20 | Gráficos interativos |
| scikit-learn | ≥ 1.4 | Modelo preditivo |

---

## Licença

Este projeto é disponibilizado para fins acadêmicos e demonstrativos.
Adapte livremente para suas necessidades.

---

*RailGuard AI — Compliance inteligente para a infraestrutura ferroviária do futuro.*
