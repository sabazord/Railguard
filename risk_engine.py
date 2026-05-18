"""
RailGuard AI — Motor de Risco
==============================
Contém as funções centrais de cálculo de risco operacional (score 0–100),
do Railway Compliance Risk Score (RCRS) e de indicadores ESG simplificados.

Nota sobre explicabilidade:
  As funções aqui retornam dicionários com contribuição por fator,
  preparando a estrutura para futura integração com SHAP ou LIME.
"""

from __future__ import annotations
from models import CRITICIDADE_PESO, CONDICAO_PESO


# ===================================================
# RISCO OPERACIONAL
# ===================================================

def calcular_risco_operacional(
    idade_anos: float,
    dias_desde_manutencao: int,
    criticidade_operacional: str,
    fissura: bool,
    desgaste: bool,
    corrosao: bool,
    falha_fixacao: bool,
    nivel_vibracao: float,       # 0–10
    carga_operacional: float,    # 0–100 %
    condicao_visual: str = "Bom",
) -> tuple[float, str, dict]:
    """
    Calcula o score de risco operacional de 0 a 100.

    Retorna:
        (score: float, nivel: str, contribuicoes: dict)
        contribuicoes → preparado para futura integração com SHAP/LIME
    """
    contrib = {}

    # 1. Idade do ativo — peso máximo 20 pts
    #    Ativo com ≥ 20 anos recebe pontuação máxima.
    contrib["idade"] = min(idade_anos / 20.0 * 20.0, 20.0)

    # 2. Tempo desde a última manutenção — peso máximo 15 pts
    #    > 365 dias sem manutenção → pontuação máxima.
    contrib["manutencao"] = min(dias_desde_manutencao / 365.0 * 15.0, 15.0)

    # 3. Criticidade operacional do trecho — peso máximo 15 pts
    crit_peso = CRITICIDADE_PESO.get(criticidade_operacional, 2)
    contrib["criticidade"] = (crit_peso / 4.0) * 15.0

    # 4. Fissura — peso fixo 15 pts (maior risco estrutural)
    contrib["fissura"] = 15.0 if fissura else 0.0

    # 5. Desgaste — peso fixo 8 pts
    contrib["desgaste"] = 8.0 if desgaste else 0.0

    # 6. Corrosão — peso fixo 8 pts
    contrib["corrosao"] = 8.0 if corrosao else 0.0

    # 7. Falha de fixação — peso fixo 10 pts
    contrib["falha_fixacao"] = 10.0 if falha_fixacao else 0.0

    # 8. Nível de vibração — peso máximo 10 pts
    contrib["vibracao"] = min(nivel_vibracao / 10.0 * 10.0, 10.0)

    # 9. Condição visual — peso máximo 10 pts
    cond_peso = CONDICAO_PESO.get(condicao_visual, 2)
    contrib["condicao_visual"] = (cond_peso / 4.0) * 10.0

    # Score total (os pesos somam até 111 pts; clampamos em 100)
    score = sum(contrib.values())
    score = round(min(max(score, 0.0), 100.0), 2)

    nivel = _classificar_risco(score)
    return score, nivel, contrib


def _classificar_risco(score: float) -> str:
    """Mapeia score numérico para categoria textual."""
    if score <= 25:
        return "Baixo"
    elif score <= 50:
        return "Médio"
    elif score <= 75:
        return "Alto"
    return "Crítico"


# ===================================================
# RCRS — Railway Compliance Risk Score
# ===================================================

def calcular_rcrs(
    score_risco_operacional: float,
    criticidade_trecho: str,
    historico_falhas: int,
    impacto_regulatorio: float,   # 0–100
    risco_esg: float,             # 0–100
    confiabilidade_dado: float,   # 0–100 (100 = totalmente confiável)
) -> tuple[float, str, str]:
    """
    Calcula o Railway Compliance Risk Score (RCRS).

    Pesos:
      35% Risco operacional
      20% Criticidade do trecho
      15% Histórico de falhas
      15% Impacto regulatório
      10% Risco ESG
       5% Penalidade por baixa confiabilidade do dado

    Retorna:
        (rcrs: float, classificacao: str, recomendacao: str)
    """
    crit_peso = CRITICIDADE_PESO.get(criticidade_trecho, 2)
    score_criticidade = (crit_peso / 4.0) * 100.0

    # Histórico de falhas: cada ocorrência adiciona 10 pts, limitado a 100
    score_historico = min(historico_falhas * 10.0, 100.0)

    # Penalidade de confiabilidade: dados pouco confiáveis ampliam a incerteza
    penalidade = (100.0 - confiabilidade_dado) * 0.05

    rcrs = (
        score_risco_operacional * 0.35
        + score_criticidade       * 0.20
        + score_historico         * 0.15
        + impacto_regulatorio     * 0.15
        + risco_esg               * 0.10
        + penalidade
    )
    rcrs = round(min(max(rcrs, 0.0), 100.0), 2)

    if rcrs <= 25:
        classificacao = "Conforme"
        recomendacao = (
            "Ativo dentro dos parâmetros de conformidade. "
            "Manter rotina de inspeções preventivas e monitoramento periódico."
        )
    elif rcrs <= 50:
        classificacao = "Atenção"
        recomendacao = (
            "Situação requer atenção. Agendar inspeção técnica detalhada "
            "nos próximos 30 dias e revisar histórico de manutenção."
        )
    elif rcrs <= 75:
        classificacao = "Não conformidade potencial"
        recomendacao = (
            "Não conformidade potencial identificada. Acionar equipe de manutenção "
            "com urgência, revisar processos de controle e documentar evidências "
            "para auditoria regulatória."
        )
    else:
        classificacao = "Crítico"
        recomendacao = (
            "⚠️ SITUAÇÃO CRÍTICA. Intervenção imediata necessária. "
            "Considerar interdição preventiva do trecho, notificar gestor responsável "
            "e acionar plano de contingência operacional."
        )

    return rcrs, classificacao, recomendacao


# ===================================================
# EXPLICABILIDADE
# ===================================================

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
    """
    Gera texto explicativo em linguagem natural sobre a classificação de risco.

    A estrutura de `contrib` (contribuições por fator) está preparada
    para futura integração com SHAP values — basta substituir os valores
    pelos SHAP values calculados pelo modelo.

    Retorna:
        str: Explicação em português
    """
    # Ordena fatores por contribuição decrescente
    top = sorted(contrib.items(), key=lambda x: x[1], reverse=True)

    motivos = []

    label_map = {
        "fissura":          ("fissura estrutural registrada", 1.0),
        "falha_fixacao":    ("falha de fixação detectada (risco de descarrilamento)", 0.9),
        "corrosao":         ("presença de corrosão avançada", 0.6),
        "desgaste":         ("desgaste identificado", 0.5),
        "vibracao":         (f"nível de vibração elevado ({nivel_vibracao:.1f}/10)", nivel_vibracao / 10),
        "criticidade":      (f"criticidade operacional {criticidade_operacional.lower()}", 0.7),
        "manutencao":       (f"longo período sem manutenção ({dias_desde_manutencao} dias)", 0.6),
        "idade":            (f"ativo com {idade_anos:.0f} anos de uso", 0.4),
        "condicao_visual":  (f"condição visual {condicao_visual.lower()}", 0.3),
    }

    for fator, valor in top:
        if valor > 2.0 and fator in label_map:
            descricao, _ = label_map[fator]
            motivos.append(descricao)
        if len(motivos) >= 5:
            break

    if not motivos:
        return (
            f"O ativo foi classificado como **{nivel}** "
            f"(score {score:.0f}/100). A combinação de múltiplos fatores "
            "com baixa magnitude individual determinou este nível."
        )

    if len(motivos) == 1:
        fatores_str = motivos[0]
    elif len(motivos) == 2:
        fatores_str = f"{motivos[0]} e {motivos[1]}"
    else:
        fatores_str = ", ".join(motivos[:-1]) + f" e {motivos[-1]}"

    return (
        f"O ativo foi classificado como **{nivel}** "
        f"(score {score:.0f}/100) principalmente devido a: {fatores_str}.\n\n"
        "_Nota técnica: esta explicação é baseada nos pesos do motor de risco. "
        "Para explicabilidade baseada em valores SHAP, integre o módulo SHAP ao ml_model.py._"
    )


# ===================================================
# INDICADORES ESG
# ===================================================

def calcular_esg_indicators(
    trecho_codigo: str,
    criticidade: str,
    num_ativos_criticos: int,
    comprimento_km: float,
    ultima_manutencao_media_dias: float,
) -> dict:
    """
    Calcula indicadores ESG simplificados para um trecho ferroviário.

    Retorna:
        dict com métricas e recomendações ESG
    """
    crit_peso = CRITICIDADE_PESO.get(criticidade, 2)

    # Risco ambiental (0–100)
    risco_ambiental = min(
        (crit_peso / 4.0) * 50.0 + num_ativos_criticos * 5.0, 100.0
    )

    # Impacto de paralisação operacional (0–100)
    impacto_paralisacao = min(comprimento_km * 1.5 + (crit_peso / 4.0) * 30.0, 100.0)

    # Eficiência de manutenção (0–100; 100 = manutenção em dia)
    eficiencia_manutencao = max(0.0, min(100.0 - (ultima_manutencao_media_dias / 4.0), 100.0))

    # Emissão estimada de CO₂ por evento de paralisação (toneladas — valor simulado)
    emissao_co2 = round(comprimento_km * 0.4 * crit_peso, 2)

    # Área de impacto estimada (km²)
    area_impacto = round(comprimento_km * 0.12, 2)

    # Score ESG composto
    score_esg = (
        risco_ambiental    * 0.40
        + impacto_paralisacao * 0.40
        + (100 - eficiencia_manutencao) * 0.20
    )

    if score_esg <= 25:
        prioridade = "Baixa"
    elif score_esg <= 50:
        prioridade = "Média"
    elif score_esg <= 75:
        prioridade = "Alta"
    else:
        prioridade = "Crítica"

    recomendacoes = []
    if risco_ambiental > 60:
        recomendacoes.append("Elaborar Plano de Gestão Ambiental para o trecho")
    if impacto_paralisacao > 60:
        recomendacoes.append("Desenvolver plano de contingência para minimizar impacto de paralisações")
    if eficiencia_manutencao < 50:
        recomendacoes.append("Intensificar o programa de manutenção preventiva")
    if num_ativos_criticos > 3:
        recomendacoes.append("Priorizar substituição de ativos em estado crítico")
    if not recomendacoes:
        recomendacoes.append("Manter práticas atuais de gestão ambiental e operacional")

    return {
        "risco_ambiental":       round(risco_ambiental, 2),
        "impacto_paralisacao":   round(impacto_paralisacao, 2),
        "eficiencia_manutencao": round(eficiencia_manutencao, 2),
        "prioridade_esg":        prioridade,
        "emissao_co2_estimada":  emissao_co2,
        "area_impacto_km2":      area_impacto,
        "score_esg":             round(score_esg, 2),
        "recomendacoes":         " | ".join(recomendacoes),
    }
