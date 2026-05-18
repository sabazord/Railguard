"""
RailGuard AI — Módulo de Relatórios
=====================================
Gera relatórios de compliance, exporta para CSV e prepara estrutura para PDF.
"""

from __future__ import annotations

import io
from datetime import datetime

import pandas as pd

import database as db


def gerar_relatorio_ativo(ativo_id: int) -> dict | None:
    """
    Consolida todos os dados de um ativo em um dicionário de relatório.

    Retorna None se o ativo não for encontrado.
    """
    ativo = db.get_ativo_by_id(ativo_id)
    if not ativo:
        return None

    trecho = db.get_trecho_by_id(ativo["trecho_id"])

    inspecoes = db.get_inspecoes_by_ativo(ativo_id)

    conn = db.get_connection()
    riscos = pd.read_sql_query(
        "SELECT * FROM riscos WHERE ativo_id = ? ORDER BY data_calculo DESC LIMIT 5",
        conn, params=(ativo_id,),
    )
    alertas = pd.read_sql_query(
        "SELECT * FROM alertas WHERE ativo_id = ? ORDER BY data_alerta DESC",
        conn, params=(ativo_id,),
    )
    conn.close()

    # Filtra log de auditoria relacionado ao ativo
    auditoria = db.get_all_auditoria()
    auditoria_ativo = auditoria[
        auditoria["item_alterado"].str.contains(ativo["codigo"], na=False, case=False)
    ].copy()

    return {
        "ativo":          ativo,
        "trecho":         trecho,
        "inspecoes":      inspecoes,
        "riscos":         riscos,
        "alertas":        alertas,
        "auditoria":      auditoria_ativo,
        "data_relatorio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def relatorio_para_csv(relatorio: dict) -> str:
    """
    Converte o dicionário de relatório em texto CSV.

    Retorna:
        str: conteúdo do CSV pronto para download
    """
    buf = io.StringIO()
    ativo  = relatorio["ativo"]
    trecho = relatorio["trecho"]

    buf.write("RAILGUARD AI — RELATÓRIO DE COMPLIANCE FERROVIÁRIO\n")
    buf.write(f"Data de Geração: {relatorio['data_relatorio']}\n")
    buf.write("Nota: dados simulados para fins de demonstração do MVP.\n\n")

    # Dados do ativo
    buf.write("=== DADOS DO ATIVO ===\n")
    for k, v in ativo.items():
        buf.write(f"{k};{v}\n")
    buf.write("\n")

    # Dados do trecho
    if trecho:
        buf.write("=== DADOS DO TRECHO ===\n")
        for k, v in trecho.items():
            buf.write(f"{k};{v}\n")
        buf.write("\n")

    # Inspeções
    buf.write("=== ÚLTIMAS INSPEÇÕES ===\n")
    if not relatorio["inspecoes"].empty:
        relatorio["inspecoes"].to_csv(buf, index=False, sep=";")
    else:
        buf.write("Nenhuma inspeção registrada.\n")
    buf.write("\n")

    # Scores de risco
    buf.write("=== SCORES DE RISCO (RCRS) ===\n")
    if not relatorio["riscos"].empty:
        relatorio["riscos"].to_csv(buf, index=False, sep=";")
    else:
        buf.write("Nenhum score calculado.\n")
    buf.write("\n")

    # Alertas
    buf.write("=== ALERTAS ===\n")
    if not relatorio["alertas"].empty:
        relatorio["alertas"].to_csv(buf, index=False, sep=";")
    else:
        buf.write("Nenhum alerta registrado.\n")
    buf.write("\n")

    # Auditoria
    buf.write("=== LOG DE AUDITORIA ===\n")
    if not relatorio["auditoria"].empty:
        relatorio["auditoria"].to_csv(buf, index=False, sep=";")
    else:
        buf.write("Nenhum registro de auditoria encontrado.\n")

    return buf.getvalue()


def relatorio_trecho_para_csv(trecho_id: int) -> str:
    """
    Gera relatório CSV consolidado de um trecho inteiro.
    """
    trecho = db.get_trecho_by_id(trecho_id)
    if not trecho:
        return "Trecho não encontrado."

    ativos_df  = db.get_all_ativos()
    ativos_df  = ativos_df[ativos_df["trecho_id"] == trecho_id]
    riscos_df  = db.get_all_riscos()
    alertas_df = db.get_all_alertas()
    esg_df     = db.get_all_esg()
    esg_df     = esg_df[esg_df["trecho_id"] == trecho_id]

    buf = io.StringIO()
    buf.write("RAILGUARD AI — RELATÓRIO DE TRECHO\n")
    buf.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    buf.write("=== DADOS DO TRECHO ===\n")
    for k, v in trecho.items():
        buf.write(f"{k};{v}\n")
    buf.write("\n")

    buf.write("=== ATIVOS DO TRECHO ===\n")
    ativos_df.to_csv(buf, index=False, sep=";")
    buf.write("\n")

    if not ativos_df.empty:
        ativo_ids = ativos_df["id"].tolist()
        riscos_trecho = riscos_df[riscos_df["ativo_id"].isin(ativo_ids)]
        buf.write("=== RISCOS CALCULADOS ===\n")
        riscos_trecho.to_csv(buf, index=False, sep=";")
        buf.write("\n")

        alertas_trecho = alertas_df[alertas_df["trecho_id"] == trecho_id]
        buf.write("=== ALERTAS DO TRECHO ===\n")
        alertas_trecho.to_csv(buf, index=False, sep=";")
        buf.write("\n")

    buf.write("=== INDICADORES ESG ===\n")
    esg_df.to_csv(buf, index=False, sep=";")

    return buf.getvalue()
