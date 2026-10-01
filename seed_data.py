"""
RailGuard AI — Dados de Demonstração
======================================
v0.4 — Adicionado Estudo de Caso Heavy Haul (TRC-CASO).

ATENÇÃO: TODOS OS DADOS SÃO FICTÍCIOS E SIMULADOS.
Não representam ferrovias, ativos ou inspeções reais.
Criados exclusivamente para fins de demonstração do MVP.

ESTUDO DE CASO HEAVY HAUL (TRC-CASO):
  Baseado em metodologia de inspeção e análise de risco ferroviário.
  Trecho de 10 km com Zona Crítica identificada no Km 7+100 ao 7+300.
  Implementa a Matriz Probabilidade × Consequência (P×C) ao lado do score ponderado.
"""

import random
from datetime import datetime, timedelta

import database as db
from risk_engine import (calcular_risco_operacional, calcular_rcrs,
                          calcular_esg_indicators, calcular_risco_matriz)

random.seed(42)

# ═══════════════════════════════════════════════════════════════
#  DADOS MESTRES — TRECHOS E ATIVOS PADRÃO
# ═══════════════════════════════════════════════════════════════

TRECHOS = [
    ("TRC-001", "MRS Logística",                   0.0,  45.5, "SP", "Bitola Larga (1,6m)",   "Alta",   "Trecho de alto tráfego — cargas pesadas de minério e contêineres."),
    ("TRC-002", "MRS Logística",                  45.5,  98.0, "SP", "Bitola Larga (1,6m)",   "Crítica","Trecho crítico próximo a área urbana. Fiscalização intensa."),
    ("TRC-003", "Rumo Malha Paulista",             0.0,  60.0, "SP", "Bitola Métrica (1,0m)", "Média",  "Via de carga geral. Velocidade máxima 80 km/h."),
    ("TRC-004", "Rumo Malha Paulista",            60.0, 130.0, "PR", "Bitola Métrica (1,0m)", "Alta",   "Trecho em região montanhosa. Risco elevado de deslizamentos."),
    ("TRC-005", "VLI — Ferrovia Centro-Atlântica", 0.0,  85.0, "MG", "Bitola Métrica (1,0m)", "Alta",   "Via de escoamento agrícola. Tráfego sazonal elevado."),
    ("TRC-006", "VLI — Ferrovia Centro-Atlântica",85.0, 150.0, "BA", "Bitola Métrica (1,0m)", "Média",  "Trecho em área de preservação ambiental."),
    ("TRC-007", "Vale (EFC)",                      0.0,  70.0, "PA", "Bitola Larga (1,6m)",   "Crítica","Via de carga pesada (minério de ferro). Alta tonelagem por eixo."),
    ("TRC-008", "Rumo Malha Sul",                  0.0, 110.0, "RS", "Bitola Métrica (1,0m)", "Baixa",  "Trecho de baixo tráfego. Em processo de reativação."),
]

ATIVOS = [
    ("ATI-001", "Trilho",      1, 15.0, 180, "Regular", None, "Trilho UIC-60 em curva. Desgaste lateral visível."),
    ("ATI-002", "Dormente",    1, 20.0, 365, "Ruim",    None, "Dormente de madeira tratada. Sinais de apodrecimento."),
    ("ATI-003", "AMV",         1,  8.0,  90, "Bom",     None, "AMV tipo agulha dupla. Última lubrificação dentro do prazo."),
    ("ATI-004", "Ponte",       2, 25.0, 540, "Ruim",    None, "Ponte metálica. Corrosão nas vigas laterais."),
    ("ATI-005", "Trilho",      2, 18.0, 270, "Regular", None, "Trilho em alta trafegabilidade. Desgaste uniforme."),
    ("ATI-006", "Fixação",     2, 12.0, 200, "Regular", None, "Clip Pandrol. Molas com deformação leve."),
    ("ATI-007", "Sinalização", 3,  5.0,  60, "Ótimo",   None, "Sinalização LED recém-instalada."),
    ("ATI-008", "Trilho",      3, 10.0, 120, "Bom",     None, "Trilho em reta. Condição adequada."),
    ("ATI-009", "Dormente",    3, 22.0, 420, "Ruim",    None, "Dormentes com fissuras transversais."),
    ("ATI-010", "Ponte",       4, 30.0, 700, "Crítico", None, "Ponte em concreto. Rachaduras na laje e armadura exposta."),
    ("ATI-011", "AMV",         4, 15.0, 300, "Regular", None, "AMV com desgaste no coração da agulha."),
    ("ATI-012", "Trilho",      5, 12.0, 150, "Bom",     None, "Trilho TR-57. Boas condições estruturais."),
    ("ATI-013", "Fixação",     5,  7.0,  90, "Bom",     None, "Fixação elástica. Sem anomalias."),
    ("ATI-014", "Dormente",    5, 18.0, 250, "Regular", None, "Dormentes de concreto. Pequenas fissuras de fabricação."),
    ("ATI-015", "Trilho",      6,  8.0, 110, "Bom",     None, "Trilho UIC-54. Operação normal."),
    ("ATI-016", "Sinalização", 6,  3.0,  30, "Ótimo",   None, "Painel de sinalização dinâmica. Calibração recente."),
    ("ATI-017", "Ponte",       7, 20.0, 450, "Ruim",    None, "Ponte sobre Rio Tocantins. Corrosão estrutural avançada."),
    ("ATI-018", "AMV",         7, 10.0, 180, "Regular", None, "AMV com folga na agulha. Necessita ajuste."),
    ("ATI-019", "Trilho",      7, 16.0, 320, "Regular", None, "Trilho com marcas de contato. Desgaste dentro do limite."),
    ("ATI-020", "Dormente",    8,  6.0,  80, "Bom",     None, "Dormente de concreto novo."),
    ("ATI-021", "Fixação",     8,  4.0,  50, "Ótimo",   None, "Fixação inelástica. Estado excelente."),
    ("ATI-022", "Trilho",      8,  9.0, 100, "Bom",     None, "Trilho laminado a quente."),
]

RESPONSAVEIS = [
    "Eng. Carlos Mendes", "Eng. Ana Paula Silva",
    "Tec. Roberto Ferreira", "Eng. Mariana Costa",
    "Tec. João Santos", "Eng. Fernanda Lima",
]

TIPOS_INSPECAO = ["Manual", "Drone", "Sensor", "Câmera Embarcada", "Ultrassom"]

PERFIS = {
    "Ótimo":   (False, False, False, False, 0.2, 2.0, 18, 33, 20, 55),
    "Bom":     (False, True,  False, False, 0.5, 4.0, 20, 38, 30, 70),
    "Regular": (False, True,  True,  False, 1.5, 6.0, 22, 45, 45, 85),
    "Ruim":    (True,  True,  True,  False, 3.0, 8.0, 25, 50, 55, 92),
    "Crítico": (True,  True,  True,  True,  6.0, 10.0,28, 58, 60,100),
}


def _rand_date(dias_min, dias_max):
    d = random.randint(dias_min, dias_max)
    return (datetime.now() - timedelta(days=d)).strftime("%Y-%m-%d")


# ═══════════════════════════════════════════════════════════════
#  ESTUDO DE CASO — HEAVY HAUL (TRC-CASO)
#  Trecho de 10 km com Zona Crítica no Km 7+100 ao 7+300
#  Dados baseados em metodologia de análise de risco ferroviário.
# ═══════════════════════════════════════════════════════════════

TRECHO_CASO = {
    "codigo":   "TRC-CASO",
    "ferrovia": "Heavy Haul Demo (Estudo de Caso)",
    "km_ini":   0.0,
    "km_fim":   10.0,
    "estado":   "PA",
    "tipo_via": "Bitola Larga (1,6m)",
    "critica":  "Crítica",
    "obs": (
        "ESTUDO DE CASO — Trecho Heavy Haul de 10 km. "
        "Velocidade autorizada: 60 km/h | Operacional: 45 km/h. "
        "Carga máxima por eixo: 32,5 toneladas. "
        "18 trens/dia × 4.500 t/trem × 365 dias/ano. "
        "Zona Crítica identificada: Km 7+100 ao 7+300."
    ),
    "velocidade_max_kmh":  60.0,
    "carga_max_eixo_ton":  32.5,
    "trens_por_dia":       18,
}

# Ativos do estudo de caso com posição quilométrica precisa
# Formato: (codigo, tipo, km_posicao, idade_anos, dias_manut, condicao, probabilidade, consequencia, obs)
ATIVOS_CASO = [
    # ── Fora da zona crítica — condição aceitável ──────────────────────
    ("CASO-TRI-T1", "Trilho",      1.5, 8.0,  120, "Bom",     2, 2,
     "T1 — Km 1+500. Desgaste moderado. Dentro dos limites da ABNT NBR."),
    ("CASO-TRI-T2", "Trilho",      3.2, 10.0, 150, "Regular", 2, 3,
     "T2 — Km 3+200. Desgaste lateral. Monitoramento preventivo recomendado."),
    ("CASO-TRI-T3", "Trilho",      4.8, 7.0,   90, "Bom",     2, 2,
     "T3 — Km 4+800. Condição adequada. Inspeção de rotina."),
    ("CASO-DOR-G1", "Dormente",    2.0, 12.0, 200, "Regular", 2, 2,
     "Dormentes de concreto. Fissuras de fabricação — sem comprometimento estrutural."),
    ("CASO-DOR-G2", "Dormente",    5.5, 9.0,  110, "Bom",     1, 2,
     "Dormentes em bom estado. Sem anomalias."),

    # ── Trecho T4 — severidade isolada fora da zona crítica ────────────
    ("CASO-TRI-T4", "Trilho",      6.7, 15.0, 280, "Ruim",    4, 4,
     "T4 — Km 6+700. Desgaste SEVERO em curva R=600m. Alta prioridade de inspeção."),

    # ── ZONA CRÍTICA — Km 7+100 ao 7+300 ──────────────────────────────
    # Os defeitos abaixo estão espacialmente correlacionados.
    # A sequência causal é: Drenagem (7+300) → Dormente (7+200)
    #                       → Fixação (7+150–7+250) → AMV (7+180)
    # A sinalização deficiente (7+100) impede que o maquinista perceba o risco.

    ("CASO-SIN-01", "Sinalização", 7.1, 6.0,  180, "Ruim",    3, 3,
     "Km 7+100 — Perda parcial de visibilidade e falha de iluminação. "
     "Maquinista tem dificuldade de visualizar instruções operacionais. "
     "2 elementos com não conformidade."),

    ("CASO-FIX-01", "Fixação",     7.2, 8.0,  220, "Crítico", 4, 5,
     "Km 7+150 a 7+250 — 10 FIXAÇÕES CONSECUTIVAS DEFEITUOSAS. "
     "Concentração anômala em trecho de 100m. Risco de alargamento de bitola. "
     "Das 4.000 fixações inspecionadas, 100 com NC (2,5%). Porém 20 estão "
     "concentradas nesta região de 500m — padrão atípico."),

    ("CASO-AMV-04", "AMV",         7.18, 12.0, 300, "Ruim",   4, 5,
     "Km 7+180 — AMV-04 com desgaste elevado, deficiência de ajuste e "
     "irregularidade no contato roda/trilho. "
     "6 movimentos diários a 40 km/h sobre via geometricamente instável. "
     "Não conformidade diretamente associada aos dormentes deteriorados adjacentes."),

    ("CASO-DOR-01", "Dormente",    7.2, 18.0, 400, "Crítico", 5, 5,
     "Km 7+200 — 5 DORMENTES CONSECUTIVOS SEVERAMENTE DETERIORADOS. "
     "Localizados em curva com raio de 500m — geometria exigente. "
     "Dos 60 dormentes com deterioração moderada, 15 são severos. "
     "Os 5 aqui concentrados representam o ponto de maior risco estrutural. "
     "Associação direta com falha da drenagem no Km 7+300."),

    ("CASO-DRE-01", "Drenagem",    7.3, 10.0, 350, "Crítico", 5, 5,
     "Km 7+300 — OBSTRUÇÃO SEVERA DE DRENAGEM. "
     "Durante chuvas intensas: acúmulo de água próximo à plataforma. "
     "Causa raiz provável da deterioração dos dormentes no Km 7+200. "
     "A água satura o lastro e o sub-leito, acelerando o apodrecimento "
     "e a perda de capacidade de suporte dos dormentes."),

    # ── Fora da zona crítica — trecho posterior ────────────────────────
    ("CASO-TRI-T5", "Trilho",      8.5, 6.0,  100, "Bom",     2, 2,
     "T5 — Km 8+500. Trilho em boa condição. Desgaste dentro do limite."),
    ("CASO-DOR-G3", "Dormente",    9.0, 5.0,   80, "Bom",     1, 2,
     "Dormentes novos. Instalação recente. Sem anomalias."),
    ("CASO-FIX-02", "Fixação",     9.5, 4.0,   60, "Ótimo",   1, 1,
     "Fixações em excelente estado. Sem ocorrências."),
]

# Resumo de Não Conformidades por tipo (para exibição no estudo de caso)
NC_RESUMO = {
    "Dormentes":    {"total_inspecionados": 2000, "total_nc": 80,
                     "moderados": 60, "severos": 15, "consecutivos_criticos": 5},
    "Trilhos":      {"total_inspecionados": "20 km", "total_nc": 6,
                     "severidade_media": "Moderada", "ponto_critico": "T4 (Km 6+700)"},
    "Fixações":     {"total_inspecionados": 4000, "total_nc": 100,
                     "concentradas_500m": 20, "consecutivas_criticas": 10},
    "AMV":          {"total_inspecionados": 10, "total_nc": 1,
                     "identificacao": "AMV-04 (Km 7+180)"},
    "Drenagem":     {"total_inspecionados": 40, "total_nc": 5,
                     "obstrucoes_parciais": 4, "obstrucao_severa": 1},
    "Sinalização":  {"total_inspecionados": 30, "total_nc": 2,
                     "localizacao": "Km 7+100"},
}


# ═══════════════════════════════════════════════════════════════
#  FUNÇÃO PRINCIPAL DE SEED
# ═══════════════════════════════════════════════════════════════

def seed_database():
    """Popula o banco com dados de demonstração."""
    random.seed(42)  # reinicia a semente: "Recarregar Demonstração" gera sempre os mesmos dados
    print("Iniciando carga de dados de demonstração RailGuard AI v0.4 …")

    # ── TRECHOS PADRÃO ──────────────────────────────────────────────────
    trecho_ids: list[int] = []
    for codigo, ferrovia, km_i, km_f, estado, tipo_via, crit, obs in TRECHOS:
        tid = db.insert_trecho(codigo, ferrovia, km_i, km_f, estado, tipo_via, crit, obs)
        trecho_ids.append(tid)
        db.insert_auditoria("INSERÇÃO", "Sistema (Seed)", f"Trecho {codigo}",
                            f"Trecho {codigo} da ferrovia {ferrovia} cadastrado.")
    print(f"{len(trecho_ids)} trechos padrão inseridos.")

    # ── TRECHO ESTUDO DE CASO ─────────────────────────────────────────
    t = TRECHO_CASO
    tid_caso = db.insert_trecho(
        t["codigo"], t["ferrovia"], t["km_ini"], t["km_fim"],
        t["estado"], t["tipo_via"], t["critica"], t["obs"],
        velocidade_max_kmh=t["velocidade_max_kmh"],
        carga_max_eixo_ton=t["carga_max_eixo_ton"],
        trens_por_dia=t["trens_por_dia"],
    )
    db.insert_auditoria("INSERÇÃO", "Sistema (Seed)", "Trecho TRC-CASO",
                        "Estudo de Caso Heavy Haul cadastrado.")
    print(f"Trecho Estudo de Caso (TRC-CASO) inserido.")

    # ── ATIVOS PADRÃO ─────────────────────────────────────────────────
    ativo_meta: list[dict] = []
    for codigo, tipo, t_idx, idade, dias_m, cond, km_pos, obs in ATIVOS:
        data_m = (datetime.now() - timedelta(days=dias_m)).strftime("%Y-%m-%d")
        aid = db.insert_ativo(codigo, tipo, trecho_ids[t_idx - 1],
                               idade, data_m, cond, obs, km_pos)
        ativo_meta.append({
            "id": aid, "codigo": codigo, "tipo": tipo,
            "trecho_idx": t_idx - 1, "idade": idade,
            "dias_manut": dias_m, "condicao": cond,
        })
        db.insert_auditoria("INSERÇÃO", "Sistema (Seed)", f"Ativo {codigo}",
                            f"Ativo {tipo} ({codigo}) cadastrado.")
    print(f"{len(ATIVOS)} ativos padrão inseridos.")

    # ── ATIVOS DO ESTUDO DE CASO ──────────────────────────────────────
    ativo_caso_meta: list[dict] = []
    for codigo, tipo, km_pos, idade, dias_m, cond, prob, cons, obs in ATIVOS_CASO:
        data_m = (datetime.now() - timedelta(days=dias_m)).strftime("%Y-%m-%d")
        aid = db.insert_ativo(codigo, tipo, tid_caso,
                               idade, data_m, cond, obs, km_pos)
        ativo_caso_meta.append({
            "id": aid, "codigo": codigo, "tipo": tipo,
            "km": km_pos, "idade": idade, "dias_manut": dias_m,
            "condicao": cond, "prob": prob, "cons": cons,
        })
        db.insert_auditoria("INSERÇÃO", "Sistema (Seed)", f"Ativo {codigo}",
                            f"Ativo do estudo de caso: {tipo} no Km {km_pos:.3f}.")
    print(f"{len(ATIVOS_CASO)} ativos do estudo de caso inseridos.")

    # ── INSPEÇÕES + RISCOS + ALERTAS — PADRÃO ─────────────────────────
    insp_count = 0
    for meta in ativo_meta:
        cond   = meta["condicao"]
        perfil = PERFIS.get(cond, PERFIS["Regular"])
        td     = TRECHOS[meta["trecho_idx"]]
        criticidade = td[6]
        tid         = trecho_ids[meta["trecho_idx"]]

        n_insp = random.randint(1, 3)
        for k in range(n_insp):
            fissura  = perfil[0];  desgaste = perfil[1]
            corrosao = perfil[2];  falha    = perfil[3]
            if random.random() < 0.12: fissura  = not fissura
            if random.random() < 0.10: falha    = not falha
            vibr  = round(random.uniform(perfil[4], perfil[5]), 1)
            temp  = round(random.uniform(perfil[6], perfil[7]), 1)
            carga = round(random.uniform(perfil[8], perfil[9]), 1)
            data_i = _rand_date(k * 30, (k + 1) * 110)
            resp   = random.choice(RESPONSAVEIS)
            tipo_i = random.choice(TIPOS_INSPECAO)

            iid = db.insert_inspecao(
                meta["id"], data_i, resp, tipo_i,
                fissura, desgaste, corrosao, falha,
                vibr, temp, carga,
                f"Inspeção #{k+1} — Condição: {cond}.",
            )
            insp_count += 1

            score, nivel, _ = calcular_risco_operacional(
                meta["idade"], meta["dias_manut"], criticidade,
                fissura, desgaste, corrosao, falha, vibr, carga, cond)

            hist = int(fissura) + int(desgaste) + int(corrosao)
            rcrs, cls_rcrs, rec = calcular_rcrs(score, criticidade, hist,
                                                 score*0.80, score*0.55,
                                                 round(random.uniform(65, 95), 1))
            db.insert_risco(iid, meta["id"], score, nivel, rcrs, cls_rcrs, rec)

            if nivel in ("Alto", "Crítico"):
                urg = "Urgente" if nivel == "Crítico" else "Alta"
                if fissura:
                    db.insert_alerta(meta["id"], tid, "Integridade Estrutural", urg,
                                     f"Fissura em {meta['codigo']}. Score: {score:.0f}/100.")
                if falha:
                    db.insert_alerta(meta["id"], tid, "Falha de Fixação", urg,
                                     f"Falha de fixação em {meta['codigo']}.")
                if rcrs >= 70:
                    db.insert_alerta(meta["id"], tid, "Compliance Crítico", urg,
                                     f"RCRS {rcrs:.0f}/100 em {meta['codigo']}.")
            db.insert_auditoria("INSERÇÃO", resp, f"Inspeção {meta['codigo']}",
                                f"Inspeção {tipo_i}. Score: {score:.0f}.")

    print(f"{insp_count} inspeções padrão inseridas.")

    # ── INSPEÇÕES + RISCOS — ESTUDO DE CASO ───────────────────────────
    insp_caso = 0
    for meta in ativo_caso_meta:
        cond   = meta["condicao"]
        perfil = PERFIS.get(cond, PERFIS["Regular"])
        data_i = _rand_date(10, 30)
        resp   = "Eng. Carlos Mendes"
        tipo_i = "Manual"

        fissura  = perfil[0]; desgaste = perfil[1]
        corrosao = perfil[2]; falha    = perfil[3]
        vibr     = round(random.uniform(perfil[4], perfil[5]), 1)
        temp     = round(random.uniform(perfil[6], perfil[7]), 1)
        carga    = 75.0  # trecho Heavy Haul — carga alta

        iid = db.insert_inspecao(
            meta["id"], data_i, resp, tipo_i,
            fissura, desgaste, corrosao, falha,
            vibr, temp, carga,
            f"Inspeção do Estudo de Caso. Km {meta['km']:.3f}. Condição: {cond}.",
            probabilidade_risco=meta["prob"],
            consequencia_risco=meta["cons"],
        )
        insp_caso += 1

        score, nivel, _ = calcular_risco_operacional(
            meta["idade"], meta["dias_manut"], "Crítica",
            fissura, desgaste, corrosao, falha, vibr, carga, cond)

        hist = int(fissura) + int(desgaste) + int(corrosao)
        rcrs, cls_rcrs, rec = calcular_rcrs(score, "Crítica", hist,
                                             score*0.90, score*0.65, 75.0)
        db.insert_risco(iid, meta["id"], score, nivel, rcrs, cls_rcrs, rec)

        if nivel in ("Alto", "Crítico"):
            urg = "Urgente" if nivel == "Crítico" else "Alta"
            db.insert_alerta(meta["id"], tid_caso, "Estudo de Caso — Risco Elevado",
                             urg,
                             f"[Heavy Haul] {meta['codigo']} | Km {meta['km']:.3f} | "
                             f"Risco {nivel} (score {score:.0f}/100). "
                             f"P={meta['prob']}×C={meta['cons']}="
                             f"{meta['prob']*meta['cons']} (Matriz P×C).")
        db.insert_auditoria("INSERÇÃO", resp, f"Inspeção {meta['codigo']}",
                            f"Inspeção estudo de caso. Score:{score:.0f} RCRS:{rcrs:.0f}.")

    print(f"{insp_caso} inspeções do estudo de caso inseridas.")

    # ── ZONA CRÍTICA — registro no banco ──────────────────────────────
    db.insert_zona_critica(
        trecho_id=tid_caso,
        km_inicio=7.1,
        km_fim=7.3,
        total_defeitos=5,
        tipos_ativo="Sinalização, Fixação, AMV, Dormente, Drenagem",
        nivel_risco_zona="Crítico",
        score_medio=91.0,
        causa_raiz_provavel=(
            "Obstrução severa de drenagem (Km 7+300) → saturação do lastro → "
            "deterioração acelerada dos dormentes (Km 7+200) → perda de fixações "
            "(Km 7+150–7+250) → instabilidade no AMV-04 (Km 7+180). "
            "Sinalização deficiente (Km 7+100) impede percepção do risco pelo maquinista. "
            "Risco iminente: alargamento de bitola e DESCARRILAMENTO em curva (R=500m) "
            "com trens de 32,5 t/eixo a 60 km/h."
        ),
        descricao=(
            "ZONA CRÍTICA — Km 7+100 ao 7+300 (200m) | Estudo de Caso Heavy Haul. "
            "5 tipos de ativo com falhas espacialmente correlacionadas. "
            "Falha em cascata detectada pelo sistema RailGuard AI."
        ),
    )
    db.insert_auditoria("DETECÇÃO", "Sistema (RailGuard AI)", "Zona Crítica TRC-CASO",
                        "Zona crítica detectada automaticamente pelo motor de análise espacial.")
    print(f"Zona Crítica (Km 7+100–7+300) registrada.")

    # ── INDICADORES ESG ───────────────────────────────────────────────
    todos_trechos = TRECHOS + [(TRECHO_CASO["codigo"], TRECHO_CASO["ferrovia"],
                                 TRECHO_CASO["km_ini"], TRECHO_CASO["km_fim"],
                                 TRECHO_CASO["estado"], TRECHO_CASO["tipo_via"],
                                 TRECHO_CASO["critica"], "")]
    todos_ids = trecho_ids + [tid_caso]

    for i, tid in enumerate(todos_ids):
        td  = todos_trechos[i]
        comp = abs(float(td[3]) - float(td[2]))
        esg = calcular_esg_indicators(
            td[0], td[6],
            random.randint(0, 5) if i < len(trecho_ids) else 5,
            comp,
            random.uniform(60, 420) if i < len(trecho_ids) else 350,
        )
        db.insert_esg(tid, esg["risco_ambiental"], esg["impacto_paralisacao"],
                      esg["eficiencia_manutencao"], esg["prioridade_esg"],
                      esg["emissao_co2_estimada"], esg["area_impacto_km2"],
                      esg["recomendacoes"])

    print(f"{len(todos_ids)} indicadores ESG calculados.")
    print("Base de dados de demonstração v0.4 populada com sucesso!\n")
