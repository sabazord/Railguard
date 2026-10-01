"""
RailGuard AI — Motor de Risco
==============================
v0.4 — Adicionado:
  - calcular_risco_matriz()   → Matriz Probabilidade × Consequência (1–25)
  - detectar_zonas_criticas() → Clustering espacial de defeitos por km
  - analisar_causa_raiz()     → Análise encadeada de falhas em cascata

A função calcular_risco_operacional() (score 0–100) permanece inalterada.
As duas metodologias são complementares e exibidas em paralelo no sistema.
"""

from __future__ import annotations
import pandas as pd
from models import CRITICIDADE_PESO, CONDICAO_PESO, MATRIZ_RISCO_CLASSIFICACAO


# ═══════════════════════════════════════════════════════
#  RISCO OPERACIONAL — score ponderado 0–100
# ═══════════════════════════════════════════════════════

def calcular_risco_operacional(
    idade_anos: float,
    dias_desde_manutencao: int,
    criticidade_operacional: str,
    fissura: bool,
    desgaste: bool,
    corrosao: bool,
    falha_fixacao: bool,
    nivel_vibracao: float,
    carga_operacional: float,
    condicao_visual: str = "Bom",
) -> tuple[float, str, dict]:
    """Score de risco ponderado 0–100. Retorna (score, nivel, contribuicoes)."""
    contrib = {}
    contrib["idade"]          = min(idade_anos / 20.0 * 20.0, 20.0)
    contrib["manutencao"]     = min(dias_desde_manutencao / 365.0 * 15.0, 15.0)
    crit_peso = CRITICIDADE_PESO.get(criticidade_operacional, 2)
    contrib["criticidade"]    = (crit_peso / 4.0) * 15.0
    contrib["fissura"]        = 15.0 if fissura else 0.0
    contrib["desgaste"]       = 8.0  if desgaste else 0.0
    contrib["corrosao"]       = 8.0  if corrosao else 0.0
    contrib["falha_fixacao"]  = 10.0 if falha_fixacao else 0.0
    contrib["vibracao"]       = min(nivel_vibracao / 10.0 * 10.0, 10.0)
    cond_peso = CONDICAO_PESO.get(condicao_visual, 2)
    contrib["condicao_visual"]= (cond_peso / 4.0) * 10.0

    score = round(min(max(sum(contrib.values()), 0.0), 100.0), 2)
    return score, _classificar_risco(score), contrib


def _classificar_risco(score: float) -> str:
    if score <= 25:  return "Baixo"
    elif score <= 50: return "Médio"
    elif score <= 75: return "Alto"
    return "Crítico"


# ═══════════════════════════════════════════════════════
#  RCRS — Railway Compliance Risk Score
# ═══════════════════════════════════════════════════════

def calcular_rcrs(
    score_risco_operacional: float,
    criticidade_trecho: str,
    historico_falhas: int,
    impacto_regulatorio: float,
    risco_esg: float,
    confiabilidade_dado: float,
) -> tuple[float, str, str]:
    """RCRS composto: 35% risco op. + 20% criticidade + 15% histórico
       + 15% regulatório + 10% ESG + 5% penalidade confiabilidade."""
    crit_peso        = CRITICIDADE_PESO.get(criticidade_trecho, 2)
    score_criticidade = (crit_peso / 4.0) * 100.0
    score_historico   = min(historico_falhas * 10.0, 100.0)
    penalidade        = (100.0 - confiabilidade_dado) * 0.05

    rcrs = round(min(max(
        score_risco_operacional * 0.35
        + score_criticidade     * 0.20
        + score_historico       * 0.15
        + impacto_regulatorio   * 0.15
        + risco_esg             * 0.10
        + penalidade, 0.0), 100.0), 2)

    if rcrs <= 25:
        return rcrs, "Conforme", (
            "Ativo dentro dos parâmetros de conformidade. "
            "Manter rotina de inspeções preventivas.")
    elif rcrs <= 50:
        return rcrs, "Atenção", (
            "Agendar inspeção técnica detalhada nos próximos 30 dias "
            "e revisar histórico de manutenção.")
    elif rcrs <= 75:
        return rcrs, "Não conformidade potencial", (
            "Acionar equipe de manutenção com urgência, revisar processos "
            "de controle e documentar evidências para auditoria regulatória.")
    return rcrs, "Crítico", (
        "SITUAÇÃO CRÍTICA. Intervenção imediata. Considerar interdição preventiva "
        "do trecho e acionar plano de contingência operacional.")


# ═══════════════════════════════════════════════════════
#  MATRIZ P×C — Probabilidade × Consequência (v0.4)
#  Metodologia: ISO 31000:2018 | ERA Railway Safety
# ═══════════════════════════════════════════════════════

def calcular_risco_matriz(probabilidade: int, consequencia: int) -> tuple[int, str]:
    """
    Calcula o risco pela Matriz Probabilidade × Consequência.

    Escala de Probabilidade (1–5):
      1 = Muito Baixa  2 = Baixa  3 = Média  4 = Alta  5 = Muito Alta

    Escala de Consequência (1–5):
      1 = Insignificante  2 = Pequena  3 = Moderada  4 = Grave  5 = Catastrófica

    Score P×C = produto (1–25)
    Classificação:
      1–4   → Baixo
      5–9   → Moderado
      10–16 → Alto
      17–25 → Crítico

    Retorna:
        (score: int, nivel: str)
    """
    p = max(1, min(int(probabilidade), 5))
    c = max(1, min(int(consequencia), 5))
    score = p * c

    for min_v, max_v, nivel, _ in MATRIZ_RISCO_CLASSIFICACAO:
        if min_v <= score <= max_v:
            return score, nivel
    return score, "Crítico"


def get_recomendacao_matriz(score_matriz: int) -> str:
    """Retorna a recomendação de ação baseada no score da Matriz P×C."""
    for min_v, max_v, _, recomendacao in MATRIZ_RISCO_CLASSIFICACAO:
        if min_v <= score_matriz <= max_v:
            return recomendacao
    return "Interdição imediata e intervenção de emergência"


def score_ponderado_para_matriz(score_ponderado: float) -> tuple[int, int]:
    """
    Converte score ponderado (0–100) em valores P e C estimados para a Matriz.
    Útil para comparação entre as duas metodologias.
    Retorna (probabilidade_estimada, consequencia_estimada).
    """
    if score_ponderado <= 25:   return 1, 2
    elif score_ponderado <= 40: return 2, 2
    elif score_ponderado <= 50: return 2, 3
    elif score_ponderado <= 62: return 3, 3
    elif score_ponderado <= 75: return 3, 4
    elif score_ponderado <= 87: return 4, 4
    return 5, 5


# ═══════════════════════════════════════════════════════
#  ZONA CRÍTICA — Análise Espacial (v0.4)
# ═══════════════════════════════════════════════════════

def detectar_zonas_criticas(
    df_ativos: pd.DataFrame,
    df_riscos: pd.DataFrame,
    janela_km: float = 0.5,
    min_defeitos: int = 3,
) -> list[dict]:
    """
    Detecta concentrações espaciais de defeitos em uma janela deslizante de km.

    Parâmetros:
        df_ativos   : DataFrame de ativos com coluna 'km_posicao'
        df_riscos   : DataFrame de riscos com últimos scores por ativo
        janela_km   : largura da janela de clustering (padrão 500m = 0.5 km)
        min_defeitos: mínimo de ativos com risco Alto/Crítico para formar zona

    Retorna:
        lista de dicionários descrevendo cada zona crítica detectada
    """
    # Filtra ativos com km_posicao registrada
    df = df_ativos[df_ativos["km_posicao"].notna()].copy()
    if df.empty or df_riscos.empty:
        return []

    # Junta com scores de risco
    if "ativo_id" not in df_riscos.columns and "id" in df_riscos.columns:
        df_r = df_riscos.rename(columns={"id": "ativo_id"})
    else:
        df_r = df_riscos.copy()

    # Pega o último risco por ativo
    ultimo_risco = (df_r.sort_values("data_calculo", ascending=False)
                    .drop_duplicates(subset=["ativo_id"], keep="first"))

    df_merged = df.merge(
        ultimo_risco[["ativo_id", "score_risco", "nivel_risco"]].rename(
            columns={"ativo_id": "id"}),
        on="id", how="left"
    )

    # Filtra apenas ativos com risco Alto ou Crítico
    df_risco = df_merged[df_merged["nivel_risco"].isin(["Alto", "Crítico"])].copy()
    df_risco = df_risco.sort_values("km_posicao").reset_index(drop=True)

    if len(df_risco) < min_defeitos:
        return []

    # A posição km só é comparável dentro do mesmo trecho — clusteriza por trecho
    if "trecho_id" not in df_risco.columns:
        df_risco["trecho_id"] = None

    zonas = []

    for trecho_id, grupo in df_risco.groupby("trecho_id", dropna=False):
        grupo = grupo.sort_values("km_posicao").reset_index(drop=True)
        if len(grupo) < min_defeitos:
            continue
        zonas.extend(_clusterizar_trecho(grupo, trecho_id, janela_km, min_defeitos))

    return zonas


def _clusterizar_trecho(
    df_risco: pd.DataFrame,
    trecho_id,
    janela_km: float,
    min_defeitos: int,
) -> list[dict]:
    """Janela deslizante de km sobre os ativos Alto/Crítico de um único trecho."""
    zonas = []
    restantes = df_risco

    # A cada rodada escolhe a janela mais concentrada entre os ativos ainda livres:
    # mais ativos primeiro; no empate, a de menor extensão (cluster mais denso).
    while len(restantes) >= min_defeitos:
        melhor = None
        for km_ini in restantes["km_posicao"].unique():
            candidatos = restantes[
                (restantes["km_posicao"] >= km_ini) &
                (restantes["km_posicao"] <= km_ini + janela_km)
            ]
            chave = (-len(candidatos), candidatos["km_posicao"].max() - km_ini)
            if melhor is None or chave < melhor[0]:
                melhor = (chave, km_ini, candidatos)

        _, km_ini, na_janela = melhor
        if len(na_janela) < min_defeitos:
            break
        restantes = restantes.drop(na_janela.index)

        tipos = na_janela["tipo_ativo"].dropna().unique().tolist()
        score_medio = na_janela["score_risco"].mean()
        nivel_zona  = "Crítico" if score_medio >= 76 else "Alto"

        causa_raiz = _inferir_causa_raiz(tipos, na_janela)

        zonas.append({
            "trecho_id":          trecho_id,
            "km_inicio":          round(float(km_ini), 3),
            "km_fim":             round(float(na_janela["km_posicao"].max()), 3),
            "total_defeitos":     len(na_janela),
            "tipos_ativo":        ", ".join(tipos),
            "nivel_risco_zona":   nivel_zona,
            "score_medio":        round(float(score_medio), 1),
            "causa_raiz_provavel": causa_raiz,
            "ativos":             na_janela["codigo"].tolist(),
            "descricao": (
                f"Zona com {len(na_janela)} ativos em risco {nivel_zona} "
                f"entre Km {km_ini:.3f} e Km {na_janela['km_posicao'].max():.3f}. "
                f"Score médio: {score_medio:.1f}/100."
            ),
        })

    zonas.sort(key=lambda z: z["km_inicio"])
    return zonas


def _inferir_causa_raiz(tipos: list[str], df_zona: pd.DataFrame) -> str:
    """
    Infere a causa raiz mais provável com base nos tipos de ativo presentes.
    Implementa a lógica encadeada do estudo de caso:
      Drenagem → Dormente → Fixação → AMV (falha em cascata)
    """
    tipos_set = set(t.lower() for t in tipos)

    # Cadeia principal do estudo de caso
    if "drenagem" in tipos_set and "dormente" in tipos_set:
        return (
            "Obstrução de drenagem causando acúmulo de água → "
            "degradação do lastro e sub-leito → deterioração dos dormentes → "
            "perda de fixação → instabilidade geométrica da via."
        )
    if "dormente" in tipos_set and "fixação" in tipos_set:
        return (
            "Deterioração de dormentes comprometendo o apoio das fixações → "
            "perda de aperto e deslocamento de trilho."
        )
    if "fixação" in tipos_set and "amv" in tipos_set:
        return (
            "Falhas em fixações próximas ao AMV causando instabilidade geométrica → "
            "irregularidade no contato roda/trilho no aparelho de mudança de via."
        )
    if "trilho" in tipos_set and "dormente" in tipos_set:
        return (
            "Desgaste conjunto de trilhos e dormentes indicando fadiga acelerada → "
            "possível excesso de carga ou vibração acumulada."
        )
    if "drenagem" in tipos_set:
        return (
            "Deficiência de drenagem causando saturação do subleito → "
            "potencial deterioração progressiva dos elementos de via."
        )
    if len(tipos_set) >= 3:
        return (
            "Múltiplos tipos de ativo em falha simultânea → "
            "possível causa sistêmica: excesso de carga, vibração ou deficiência de manutenção."
        )
    return (
        f"Concentração de falhas em {', '.join(tipos)} → "
        "inspeção detalhada recomendada para identificação da causa raiz."
    )


# ═══════════════════════════════════════════════════════
#  EXPLICABILIDADE
# ═══════════════════════════════════════════════════════

def gerar_explicabilidade(
    score: float,
    nivel: str,
    contrib: dict,
    fissura: bool,
    desgaste: bool,
    corrosao: bool,
    falha_fixacao: bool,
    nivel_vibracao: float,
    idade_anos: float,
    dias_desde_manutencao: int,
    criticidade_operacional: str,
    condicao_visual: str,
) -> str:
    top = sorted(contrib.items(), key=lambda x: x[1], reverse=True)
    label_map = {
        "fissura":         ("fissura estrutural registrada", 1.0),
        "falha_fixacao":   ("falha de fixação detectada (risco de descarrilamento)", 0.9),
        "corrosao":        ("presença de corrosão avançada", 0.6),
        "desgaste":        ("desgaste identificado", 0.5),
        "vibracao":        (f"nível de vibração elevado ({nivel_vibracao:.1f}/10)", nivel_vibracao/10),
        "criticidade":     (f"criticidade operacional {criticidade_operacional.lower()}", 0.7),
        "manutencao":      (f"longo período sem manutenção ({dias_desde_manutencao} dias)", 0.6),
        "idade":           (f"ativo com {idade_anos:.0f} anos de uso", 0.4),
        "condicao_visual": (f"condição visual {condicao_visual.lower()}", 0.3),
    }
    motivos = [label_map[f][0] for f, v in top if v > 2.0 and f in label_map][:5]
    if not motivos:
        return (f"O ativo foi classificado como **{nivel}** (score {score:.0f}/100). "
                "Combinação de múltiplos fatores com baixa magnitude individual.")
    fatores_str = (motivos[0] if len(motivos) == 1
                   else f"{motivos[0]} e {motivos[1]}" if len(motivos) == 2
                   else ", ".join(motivos[:-1]) + f" e {motivos[-1]}")
    return (f"O ativo foi classificado como **{nivel}** (score {score:.0f}/100) "
            f"principalmente devido a: {fatores_str}.\n\n"
            "_Estrutura preparada para integração com SHAP — veja ml_model.py._")


# ═══════════════════════════════════════════════════════
#  ESG
# ═══════════════════════════════════════════════════════

def calcular_esg_indicators(
    trecho_codigo: str,
    criticidade: str,
    num_ativos_criticos: int,
    comprimento_km: float,
    ultima_manutencao_media_dias: float,
) -> dict:
    crit_peso           = CRITICIDADE_PESO.get(criticidade, 2)
    risco_ambiental     = min((crit_peso/4.0)*50.0 + num_ativos_criticos*5.0, 100.0)
    impacto_paralisacao = min(comprimento_km*1.5 + (crit_peso/4.0)*30.0, 100.0)
    eficiencia_manutencao = max(0.0, min(100.0-(ultima_manutencao_media_dias/4.0), 100.0))
    emissao_co2         = round(comprimento_km*0.4*crit_peso, 2)
    area_impacto        = round(comprimento_km*0.12, 2)
    score_esg           = (risco_ambiental*0.40 + impacto_paralisacao*0.40
                           + (100-eficiencia_manutencao)*0.20)

    prioridade = ("Baixa" if score_esg <= 25 else "Média" if score_esg <= 50
                  else "Alta" if score_esg <= 75 else "Crítica")

    recs = []
    if risco_ambiental > 60:      recs.append("Elaborar Plano de Gestão Ambiental")
    if impacto_paralisacao > 60:  recs.append("Desenvolver plano de contingência operacional")
    if eficiencia_manutencao < 50: recs.append("Intensificar manutenção preventiva")
    if num_ativos_criticos > 3:   recs.append("Priorizar substituição de ativos críticos")
    if not recs:                   recs.append("Manter práticas atuais de gestão")

    return {
        "risco_ambiental":       round(risco_ambiental, 2),
        "impacto_paralisacao":   round(impacto_paralisacao, 2),
        "eficiencia_manutencao": round(eficiencia_manutencao, 2),
        "prioridade_esg":        prioridade,
        "emissao_co2_estimada":  emissao_co2,
        "area_impacto_km2":      area_impacto,
        "score_esg":             round(score_esg, 2),
        "recomendacoes":         " | ".join(recs),
    }
