# RailGuard AI — Contexto para Claude Code
# Versão: 0.4 | Atualizado: 2026-09

## O que é esse projeto
MVP de compliance preditivo ferroviário desenvolvido em Python + Streamlit.
Dados 100% simulados para fins acadêmicos/demonstrativos.
Projeto de Allan Sabá — estudante de Engenharia Ferroviária e Logística (UFPA).
Deploy: Streamlit Cloud → https://github.com/sabazord/Railguard (branch: main)

---

## Stack
- Python 3.11+
- Streamlit (interface web)
- SQLite via sqlite3 nativo (banco local em data/railguard.db)
- Pandas + NumPy (dados)
- Plotly (gráficos dark theme corporativo)
- Scikit-learn RandomForestClassifier (modelo preditivo)

---

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| app.py | Interface completa, roteamento, todas as páginas (~3300 linhas) |
| database.py | Banco SQLite, CRUD, todas as queries, migração de colunas |
| models.py | Constantes de domínio (pesos, listas, cores, escala P×C) |
| risk_engine.py | Motor de risco: score ponderado 0–100, RCRS, Matriz P×C, zona crítica |
| ml_model.py | RandomForest: treino, predição, importância de features |
| reports.py | Geração de relatórios e exportação CSV |
| seed_data.py | Dados fictícios de demonstração + Estudo de Caso Heavy Haul |
| requirements.txt | Dependências do projeto |
| data/railguard.db | Banco SQLite (criado automaticamente na 1ª execução) |

---

## Tema visual — Dark Industrial Ferroviário
Todas as cores são definidas como constantes no topo do app.py:

```python
PRIMARY   = "#080F1D"   # fundo principal
CARD_BG   = "#101F38"   # cards
BORDER    = "#1A3357"   # bordas
ACCENT2   = "#2A8FD4"   # azul elétrico (info/IA)
C_CRITICO = "#E63946"   # vermelho (crítico)
C_ALTO    = "#F47B35"   # laranja (alto risco)
C_MEDIO   = "#F4A62A"   # âmbar (atenção)
C_BAIXO   = "#0CB87A"   # verde (ok/baixo)
C_COMP    = "#7B5EA7"   # roxo (compliance)
TEXT_PRI  = "#ECF1F7"   # texto principal
TEXT_SEC  = "#92AFCA"   # texto secundário
TEXT_MUT  = "#435D77"   # texto mutado/label
```

Todo CSS é injetado via `st.markdown(CSS, unsafe_allow_html=True)` no topo do app.py.
A variável `CSS` é uma f-string que interpola as constantes de cor do Python diretamente.

---

## Navegação e roteamento
- Navegação via `st.session_state["pagina"]`
- Menu lateral com botões nativos do Streamlit + CSS customizado
- Menu dividido em 3 categorias: Operação / Inteligência / Gestão
- Roteamento no final do arquivo via dicionário `_ROTAS`

```python
# CATEGORIAS do menu lateral
CATEGORIAS = {
    "Operação":    ["Dashboard", "Trechos", "Ativos", "Inspeções", "Zona Crítica"],
    "Inteligência":["Modelo Preditivo", "Compliance", "Auditoria"],
    "Gestão":      ["ESG", "Relatórios", "Configurações"],
}

# Roteamento (final do app.py)
_ROTAS = {
    "Dashboard":        page_dashboard,
    "Trechos":          page_trechos,
    "Ativos":           page_ativos,
    "Inspeções":        page_inspecoes,
    "Zona Crítica":     page_zona_critica,   # NOVO v0.4
    "Modelo Preditivo": page_ml,
    "Compliance":       page_compliance,
    "Auditoria":        page_auditoria,
    "ESG":              page_esg,
    "Relatórios":       page_relatorios,
    "Configurações":    page_config,
}
```

---

## Banco de dados — tabelas

```sql
trechos           -- trechos ferroviários (+ velocidade_max, carga_max, trens_por_dia)
ativos            -- ativos (+ km_posicao para localização precisa na malha)
inspecoes         -- inspeções (+ probabilidade_risco, consequencia_risco, score_matriz)
riscos            -- scores calculados por inspeção
alertas           -- alertas operacionais gerados automaticamente
auditoria         -- log imutável de todas as ações
indicadores_esg   -- métricas ESG por trecho
zonas_criticas    -- clusters espaciais de defeitos (NOVO v0.4)
```

**IMPORTANTE — Migração automática:** `init_database()` chama `_migrate_columns()` que
faz `ALTER TABLE` para adicionar colunas novas em bancos antigos sem destruir dados.
Nunca remova essa função.

---

## Motor de risco — risk_engine.py

### Função 1: Score ponderado 0–100
```python
calcular_risco_operacional(idade_anos, dias_desde_manutencao, criticidade_operacional,
    fissura, desgaste, corrosao, falha_fixacao, nivel_vibracao, carga_operacional,
    condicao_visual) → (score: float, nivel: str, contrib: dict)
```
Classificação: 0–25 Baixo | 26–50 Médio | 51–75 Alto | 76–100 Crítico

### Função 2: RCRS — Railway Compliance Risk Score
```python
calcular_rcrs(score_risco_operacional, criticidade_trecho, historico_falhas,
    impacto_regulatorio, risco_esg, confiabilidade_dado) → (rcrs, classificacao, recomendacao)
```
Pesos: 35% risco op. | 20% criticidade | 15% histórico | 15% regulatório | 10% ESG | 5% confiabilidade

### Função 3: Matriz P×C (NOVO v0.4)
```python
calcular_risco_matriz(probabilidade: int, consequencia: int) → (score: int, nivel: str)
# score = P × C (1–25)
# Classificação: 1–4 Baixo | 5–9 Moderado | 10–16 Alto | 17–25 Crítico
```
Metodologia: ISO 31000:2018 | ERA (European Union Agency for Railways)

### Função 4: Detecção de Zona Crítica (NOVO v0.4)
```python
detectar_zonas_criticas(df_ativos, df_riscos, janela_km=0.5, min_defeitos=3)
→ list[dict]
```
Janela deslizante de 500m. Detecta ≥ 3 ativos Alto/Crítico no mesmo trecho
(agrupa por `trecho_id` antes de clusterizar; cada zona retorna `trecho_id`).
A cada rodada escolhe a janela mais concentrada (mais ativos; no empate, a menor
extensão) — com o seed detecta exatamente Km 7.1–7.3 no TRC-CASO.
Infere causa raiz com a cadeia: Drenagem → Dormente → Fixação → AMV.
Exibida em tempo real no bloco 5 da página Zona Crítica.

---

## Estudo de Caso Heavy Haul — TRC-CASO (NOVO v0.4)

Trecho demonstrativo com dados baseados em metodologia real de inspeção:
- **Extensão:** 10 km | **Carga:** 32,5 t/eixo | **Velocidade:** 60 km/h
- **Tráfego:** 18 trens/dia × 4.500 t/trem
- **Zona Crítica:** Km 7+100 a 7+300 (200m) com 5 tipos de defeito correlacionados

### Cadeia causal identificada (falha em cascata):
```
Obstrução drenagem (Km 7+300)
    → Saturação do lastro/sub-leito
    → Deterioração dormentes (Km 7+200) — 5 consecutivos severos em curva R=500m
    → Falha fixações (Km 7+150–7+250) — 10 consecutivas defeituosas
    → Comprometimento AMV-04 (Km 7+180)
    + Sinalização deficiente (Km 7+100) — agravante
    = RISCO DE DESCARRILAMENTO (P=5 × C=5 = 25 — Crítico)
```

### Ativos do estudo de caso (com km_posicao):
```
CASO-SIN-01  Sinalização  km=7.10  Ruim      P=3 C=3 score=9  Moderado
CASO-FIX-01  Fixação      km=7.20  Crítico   P=4 C=5 score=20 Crítico
CASO-AMV-04  AMV          km=7.18  Ruim      P=4 C=5 score=20 Crítico
CASO-DOR-01  Dormente     km=7.20  Crítico   P=5 C=5 score=25 Crítico
CASO-DRE-01  Drenagem     km=7.30  Crítico   P=5 C=5 score=25 Crítico
CASO-TRI-T4  Trilho       km=6.70  Ruim      P=4 C=4 score=16 Alto
```

---

## Página Zona Crítica — page_zona_critica()

Localização no app.py: antes do bloco `_ROTAS` (última função de página).
Contém 5 blocos:
1. Resumo das NC quantificadas (cards por tipo de ativo)
2. Linha do tempo espacial — scatter plot por km com zona sombreada
3. Visualização da Matriz P×C 5×5 (heatmap colorido) + scores dos ativos do caso
4. Análise visual da falha em cascata (HTML com cadeia causal)
5. Zonas críticas registradas no banco + detecção automática (`detectar_zonas_criticas`)
   sobre os dados atuais + comparação das duas metodologias

A faixa sombreada do gráfico do bloco 2 vem de `zonas_criticas` (TRC-CASO), com
fallback 7.1–7.3. Os blocos 1 e 3 são dados fixos do estudo de caso (narrativa).

---

## Bugs já resolvidos — NÃO reverter

### Bug 1 — KeyError tipo_ativo no heatmap do dashboard
`df_riscos` já vem com `tipo_ativo` do JOIN em `get_all_riscos()`.
Fazer merge com `df_ativos` cria `tipo_ativo_x` e `tipo_ativo_y` — a coluna some.
**Solução correta:**
```python
if "tipo_ativo" in df_riscos.columns:
    dhm = df_riscos[["tipo_ativo", "nivel_risco"]].copy()
else:
    # fallback via map (não via merge)
    _map_tipo = df_a2.set_index("id")["tipo_ativo"].to_dict()
    dhm["tipo_ativo"] = dhm["ativo_id"].map(_map_tipo)
```

### Bug 2 — Score lookup nos alertas
Usar `df_riscos["ativo_codigo"] == ativo_cod` dentro de try/except.
NUNCA usar `df_riscos.get(...)` — DataFrame não tem esse método.

### Bug 3 — Brace escaping no CSS f-string
O CSS está dentro de `CSS = f"""..."""`. Todas as chaves `{}` do CSS
devem ser escritas como `{{}}` para não serem interpretadas como variáveis Python.
Ao adicionar novos blocos CSS, sempre dobrar as chaves.

### Bug 4 — `return` antecipado dentro de `with tab1:` escondia as outras abas
Um `return` (ex.: banco vazio, botão "Gerar" não clicado) dentro de `with tab1:`
sai da função da página inteira e a `tab2` nunca é renderizada.
**Solução correta:** o conteúdo da aba vai numa função aninhada
(`def _aba_lista(): ...` e depois `with tab1: _aba_lista()`).
Usado em Trechos, Ativos, Inspeções, Compliance e Relatórios.

### Bug 5 — Mensagem de sucesso sumia com `st.rerun()`
Qualquer `info()`/`st.markdown()` antes de `st.rerun()` é descartado.
**Solução correta:** `flash(html, kind)` guarda a mensagem em
`st.session_state["_flash"]` e `mostrar_flash()` (chamado no roteamento) exibe.

### Bug 6 — Linha em branco dentro de HTML no `st.markdown`
Uma linha vazia (ou só com espaços) encerra o bloco HTML do Markdown e o resto,
se indentado, vira bloco de código. Ao interpolar trechos de HTML numa f-string,
não comece o trecho com `\n`. Era o que fazia o bloco 4 da Zona Crítica (cadeia
causal) aparecer como código cru — as linhas em branco internas foram removidas.

### Bug 8 — `use_container_width` obsoleto
O Streamlit marcou `use_container_width` para remoção. Usar sempre
`width="stretch"` (exige streamlit>=1.52, já no requirements.txt).

### Bug 7 — Heatmap do dashboard usava `pivot` indefinido
Com `dhm` vazio o gráfico era montado fora do `else` → `NameError`. O gráfico agora
fica dentro do `else`.

---

## Convenções de interface
- **Sem emojis** em nenhum texto da interface, logs ou strings (decisão do autor).
  O cabeçalho de página usa uma barra de destaque (`.page-accent`) no lugar de ícone.
- Formulários de cadastro coletam os campos v0.4: trecho (velocidade, carga/eixo,
  trens/dia — opcionais), ativo (`km_posicao` — opcional), inspeção (P e C da
  Matriz — opcionais, mas ambos ou nenhum).

---

## Estado atual do banco (após seed v0.4)
- 9 trechos (8 padrão + TRC-CASO)
- 36 ativos (22 padrão + 14 do estudo de caso)
- 55 inspeções (41 padrão + 14 do caso)
- 22 alertas abertos
- 1 zona crítica registrada (Km 7.1 → 7.3)

---

## Helpers globais disponíveis em app.py
```python
ph(title, subtitle)                # Cabeçalho de página (sem ícone)
bloco(numero, titulo, cor)         # Divisor de bloco numerado
kpi_v3(label, value, sub, status_text, status_cor, variant)  # Card KPI com status
flash(html, kind) / mostrar_flash()# Mensagem que sobrevive ao st.rerun()
sdiv(label)                        # Divisor de seção
info(msg) / warn(msg) / danger(msg)# Caixas de feedback
row_kv(label, value)               # Linha chave-valor
chart_insight(texto)               # Bloco de interpretação de gráfico
gauge_risco(score, nivel, h)       # Gauge Plotly de risco
_pt(fig, h)                        # Aplica tema dark a figura Plotly
alert_card_v3(...)                 # Card de alerta com chips de ação
gerar_resumo_inteligente(...)      # Texto de análise automática
```

---

## Ambiente local (Windows do Allan)
- Python 3.14 em `C:\Users\sabad\AppData\Local\Programs\Python\Python314`
- Ambiente virtual fora do OneDrive: `C:\Users\sabad\.venvs\railguard`
- Rodar: `C:\Users\sabad\.venvs\railguard\Scripts\python.exe -m streamlit run app.py`
- O Smart App Control do Windows bloqueia um binário do scikit-learn 1.9.1;
  localmente está instalado `scikit-learn<1.9` (1.8.0). Não afeta o Streamlit Cloud.

## Como subir alterações para o Streamlit Cloud
```bash
git add .
git commit -m "descricao da alteracao"
git push origin main
# O Streamlit Cloud atualiza automaticamente
```

---

## Roadmap — o que ainda NÃO foi feito
- v0.5 → Autenticação (streamlit-authenticator)
- v0.5 → Migração para PostgreSQL + Docker
- v0.6 → API REST com FastAPI para sensores IoT
- v0.7 → Explicabilidade via SHAP (estrutura preparada em ml_model.py)
- v0.8 → Mapa geoespacial dos trechos (folium/pydeck)
- v1.0 → Deploy em nuvem (AWS/Azure) com CI/CD
- v1.x → Integração com LLM (Claude API + RAG normativo) — arquitetura já documentada

## Próxima melhoria sugerida
SHAP para explicabilidade do RandomForest.
Estrutura já preparada em ml_model.py (comentários indicam onde adicionar).
Instalação: `pip install shap`
Adicionar função `explicar_com_shap(model, X_test)` em ml_model.py
e exibir `shap.summary_plot()` na página Modelo Preditivo.

## Referências técnicas utilizadas no projeto
- ISO 31000:2018 — Gestão de Riscos (base para Matriz P×C)
- ERA — European Union Agency for Railways (metodologia P×C ferroviária)
- Resoluções ANTT 3.695/2011 e 5.910/2020 (compliance regulatório)
- ABNT NBR 7480/7482 (estruturas ferroviárias)
- GRI Standards GRI 305 (indicadores ESG — emissões CO₂)
