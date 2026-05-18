"""
RailGuard AI — Dados de Demonstração
======================================
⚠️  TODOS OS DADOS AQUI SÃO FICTÍCIOS E SIMULADOS.
Não representam ferrovias, ativos ou inspeções reais.
Criados exclusivamente para fins de demonstração do MVP.
"""

import random
from datetime import datetime, timedelta

import database as db
from risk_engine import calcular_risco_operacional, calcular_rcrs, calcular_esg_indicators

random.seed(42)

# ------------------------------------------------------------------
# Dados mestres de referência
# ------------------------------------------------------------------
TRECHOS = [
    # (codigo, ferrovia, km_ini, km_fin, estado, tipo_via, criticidade, observacao)
    ("TRC-001", "MRS Logística",                  0.0,  45.5, "SP", "Bitola Larga (1,6m)",   "Alta",   "Trecho de alto tráfego — cargas pesadas de minério e contêineres."),
    ("TRC-002", "MRS Logística",                 45.5,  98.0, "SP", "Bitola Larga (1,6m)",   "Crítica","Trecho crítico próximo a área urbana. Fiscalização intensa."),
    ("TRC-003", "Rumo Malha Paulista",            0.0,  60.0, "SP", "Bitola Métrica (1,0m)", "Média",  "Via de carga geral. Velocidade máxima 80 km/h."),
    ("TRC-004", "Rumo Malha Paulista",           60.0, 130.0, "PR", "Bitola Métrica (1,0m)", "Alta",   "Trecho em região montanhosa. Risco elevado de deslizamentos."),
    ("TRC-005", "VLI — Ferrovia Centro-Atlântica",0.0,  85.0, "MG", "Bitola Métrica (1,0m)", "Alta",   "Via de escoamento agrícola. Tráfego sazonal elevado."),
    ("TRC-006", "VLI — Ferrovia Centro-Atlântica",85.0,150.0, "BA", "Bitola Métrica (1,0m)", "Média",  "Trecho em área de preservação ambiental. Restrições operacionais."),
    ("TRC-007", "Vale (EFC)",                     0.0,  70.0, "PA", "Bitola Larga (1,6m)",   "Crítica","Via de carga pesada (minério de ferro). Alta tonelagem por eixo."),
    ("TRC-008", "Rumo Malha Sul",                 0.0, 110.0, "RS", "Bitola Métrica (1,0m)", "Baixa",  "Trecho de baixo tráfego. Em processo de reativação."),
]

ATIVOS = [
    # (codigo, tipo, trecho_idx[1-based], idade_anos, dias_sem_manut, condicao_visual, obs)
    ("ATI-001", "Trilho",      1, 15.0, 180, "Regular", "Trilho UIC-60 em trecho de curva. Desgaste lateral visível."),
    ("ATI-002", "Dormente",    1, 20.0, 365, "Ruim",    "Dormente de madeira tratada. Sinais de apodrecimento na extremidade."),
    ("ATI-003", "AMV",         1,  8.0,  90, "Bom",     "AMV tipo agulha dupla. Última lubrificação dentro do prazo."),
    ("ATI-004", "Ponte",       2, 25.0, 540, "Ruim",    "Ponte metálica sobre córrego. Corrosão nas vigas laterais."),
    ("ATI-005", "Trilho",      2, 18.0, 270, "Regular", "Trilho em área de alta trafegabilidade. Desgaste uniforme."),
    ("ATI-006", "Fixação",     2, 12.0, 200, "Regular", "Clip Pandrol. Algumas molas com deformação leve."),
    ("ATI-007", "Sinalização", 3,  5.0,  60, "Ótimo",   "Sinalização LED recém-instalada. Funcionamento normal."),
    ("ATI-008", "Trilho",      3, 10.0, 120, "Bom",     "Trilho em reta. Condição adequada para operação."),
    ("ATI-009", "Dormente",    3, 22.0, 420, "Ruim",    "Dormentes de madeira com fissuras transversais."),
    ("ATI-010", "Ponte",       4, 30.0, 700, "Crítico", "Ponte em concreto armado. Rachaduras na laje e armadura exposta."),
    ("ATI-011", "AMV",         4, 15.0, 300, "Regular", "AMV com desgaste no coração da agulha. Monitoramento necessário."),
    ("ATI-012", "Trilho",      5, 12.0, 150, "Bom",     "Trilho TR-57. Boas condições estruturais."),
    ("ATI-013", "Fixação",     5,  7.0,  90, "Bom",     "Fixação elástica. Sem anomalias identificadas."),
    ("ATI-014", "Dormente",    5, 18.0, 250, "Regular", "Dormentes de concreto bimoldado. Pequenas fissuras de fabricação."),
    ("ATI-015", "Trilho",      6,  8.0, 110, "Bom",     "Trilho UIC-54. Operação normal."),
    ("ATI-016", "Sinalização", 6,  3.0,  30, "Ótimo",   "Painel de sinalização dinâmica. Calibração recente."),
    ("ATI-017", "Ponte",       7, 20.0, 450, "Ruim",    "Ponte sobre o Rio Tocantins. Corrosão estrutural avançada."),
    ("ATI-018", "AMV",         7, 10.0, 180, "Regular", "AMV com folga na agulha. Necessita ajuste."),
    ("ATI-019", "Trilho",      7, 16.0, 320, "Regular", "Trilho com marcas de contato de roda. Desgaste dentro do limite."),
    ("ATI-020", "Dormente",    8,  6.0,  80, "Bom",     "Dormente de concreto novo. Instalação recente."),
    ("ATI-021", "Fixação",     8,  4.0,  50, "Ótimo",   "Fixação inelástica. Estado excelente."),
    ("ATI-022", "Trilho",      8,  9.0, 100, "Bom",     "Trilho laminado a quente. Condição regular de operação."),
]

RESPONSAVEIS = [
    "Eng. Carlos Mendes",
    "Eng. Ana Paula Silva",
    "Tec. Roberto Ferreira",
    "Eng. Mariana Costa",
    "Tec. João Santos",
    "Eng. Fernanda Lima",
]

TIPOS_INSPECAO = ["Manual", "Drone", "Sensor", "Câmera Embarcada", "Ultrassom"]

# Perfis de inspeção por condição visual do ativo
# (fissura, desgaste, corrosao, falha_fixacao, vibr_min, vibr_max, temp_min, temp_max, carga_min, carga_max)
PERFIS = {
    "Ótimo":   (False, False, False, False, 0.2, 2.0, 18, 33, 20, 55),
    "Bom":     (False, True,  False, False, 0.5, 4.0, 20, 38, 30, 70),
    "Regular": (False, True,  True,  False, 1.5, 6.0, 22, 45, 45, 85),
    "Ruim":    (True,  True,  True,  False, 3.0, 8.0, 25, 50, 55, 92),
    "Crítico": (True,  True,  True,  True,  6.0, 10.0,28, 58, 60,100),
}


def _rand_date(dias_atras_min: int, dias_atras_max: int) -> str:
    dias = random.randint(dias_atras_min, dias_atras_max)
    return (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")


def seed_database():
    """Popula o banco com dados de demonstração."""
    print("🚂  Iniciando carga de dados de demonstração RailGuard AI …")

    # ---- TRECHOS ----
    trecho_ids: list[int] = []
    for codigo, ferrovia, km_i, km_f, estado, tipo_via, crit, obs in TRECHOS:
        tid = db.insert_trecho(codigo, ferrovia, km_i, km_f, estado, tipo_via, crit, obs)
        trecho_ids.append(tid)
        db.insert_auditoria("INSERÇÃO", "Sistema (Seed)", f"Trecho {codigo}",
                            f"Trecho {codigo} da ferrovia {ferrovia} cadastrado via seed.")
    print(f"  ✅ {len(trecho_ids)} trechos inseridos.")

    # ---- ATIVOS ----
    ativo_ids: list[int] = []
    ativo_meta: list[dict] = []   # guarda metadados para uso posterior
    for codigo, tipo, t_idx, idade, dias_m, cond, obs in ATIVOS:
        data_m = (datetime.now() - timedelta(days=dias_m)).strftime("%Y-%m-%d")
        aid = db.insert_ativo(codigo, tipo, trecho_ids[t_idx - 1],
                               idade, data_m, cond, obs)
        ativo_ids.append(aid)
        ativo_meta.append({
            "id": aid, "codigo": codigo, "tipo": tipo,
            "trecho_idx": t_idx - 1, "idade": idade,
            "dias_manut": dias_m, "condicao": cond,
        })
        db.insert_auditoria("INSERÇÃO", "Sistema (Seed)", f"Ativo {codigo}",
                            f"Ativo {tipo} ({codigo}) cadastrado via seed.")
    print(f"  ✅ {len(ativo_ids)} ativos inseridos.")

    # ---- INSPEÇÕES + RISCOS + ALERTAS ----
    insp_count = 0
    risco_count = 0

    for meta in ativo_meta:
        cond = meta["condicao"]
        perfil = PERFIS.get(cond, PERFIS["Regular"])
        trecho_data = TRECHOS[meta["trecho_idx"]]
        criticidade = trecho_data[6]
        tid = trecho_ids[meta["trecho_idx"]]

        # 1 a 3 inspeções por ativo
        n_insp = random.randint(1, 3)
        for k in range(n_insp):
            fissura   = perfil[0]
            desgaste  = perfil[1]
            corrosao  = perfil[2]
            falha     = perfil[3]

            # Pequena aleatoriedade para variação dos dados
            if random.random() < 0.12:
                fissura = not fissura
            if random.random() < 0.10:
                falha = not falha

            vibr  = round(random.uniform(perfil[4], perfil[5]), 1)
            temp  = round(random.uniform(perfil[6], perfil[7]), 1)
            carga = round(random.uniform(perfil[8], perfil[9]), 1)
            data_i = _rand_date(k * 30, (k + 1) * 110)
            resp   = random.choice(RESPONSAVEIS)
            tipo_i = random.choice(TIPOS_INSPECAO)
            obs_i  = f"Inspeção #{k+1} — Condição geral: {cond}."

            iid = db.insert_inspecao(
                meta["id"], data_i, resp, tipo_i,
                fissura, desgaste, corrosao, falha,
                vibr, temp, carga, obs_i,
            )
            insp_count += 1

            db.insert_auditoria("INSERÇÃO", resp, f"Inspeção {meta['codigo']}",
                                f"Inspeção {tipo_i} registrada para {meta['codigo']} em {data_i}.")

            # --- Calcular risco ---
            score, nivel, contrib = calcular_risco_operacional(
                idade_anos=meta["idade"],
                dias_desde_manutencao=meta["dias_manut"],
                criticidade_operacional=criticidade,
                fissura=fissura, desgaste=desgaste,
                corrosao=corrosao, falha_fixacao=falha,
                nivel_vibracao=vibr, carga_operacional=carga,
                condicao_visual=cond,
            )

            hist = int(fissura) + int(desgaste) + int(corrosao)
            rcrs, class_rcrs, rec = calcular_rcrs(
                score_risco_operacional=score,
                criticidade_trecho=criticidade,
                historico_falhas=hist,
                impacto_regulatorio=round(score * 0.80, 2),
                risco_esg=round(score * 0.55, 2),
                confiabilidade_dado=round(random.uniform(65, 95), 1),
            )

            db.insert_risco(iid, meta["id"], score, nivel, rcrs, class_rcrs, rec)
            risco_count += 1

            # --- Alertas para riscos altos/críticos ---
            if nivel in ("Alto", "Crítico"):
                urg = "Urgente" if nivel == "Crítico" else "Alta"
                if fissura:
                    db.insert_alerta(meta["id"], tid, "Integridade Estrutural", urg,
                                     f"Fissura detectada em {meta['codigo']}. Score: {score:.0f}/100.")
                if falha:
                    db.insert_alerta(meta["id"], tid, "Falha de Fixação", urg,
                                     f"Falha de fixação em {meta['codigo']}. Risco de descarrilamento.")
                if rcrs >= 70:
                    db.insert_alerta(meta["id"], tid, "Compliance Crítico", urg,
                                     f"RCRS {rcrs:.0f}/100 — {class_rcrs} no ativo {meta['codigo']}.")

    print(f"  ✅ {insp_count} inspeções inseridas.")
    print(f"  ✅ {risco_count} registros de risco calculados.")

    # ---- INDICADORES ESG ----
    for i, tid in enumerate(trecho_ids):
        td = TRECHOS[i]
        # Tupla: (codigo, ferrovia, km_ini, km_fin, estado, tipo_via, criticidade, obs)
        #          0       1         2       3        4       5          6           7
        comprimento = abs(float(td[3]) - float(td[2]))  # km_final - km_inicial
        n_criticos  = random.randint(0, 5)
        media_dias  = random.uniform(60, 420)

        esg = calcular_esg_indicators(
            trecho_codigo=td[0],
            criticidade=td[6],
            num_ativos_criticos=n_criticos,
            comprimento_km=comprimento,
            ultima_manutencao_media_dias=media_dias,
        )
        db.insert_esg(
            tid,
            esg["risco_ambiental"], esg["impacto_paralisacao"],
            esg["eficiencia_manutencao"], esg["prioridade_esg"],
            esg["emissao_co2_estimada"], esg["area_impacto_km2"],
            esg["recomendacoes"],
        )
    print(f"  ✅ {len(trecho_ids)} indicadores ESG calculados.")
    print("✅  Base de dados de demonstração populada com sucesso!\n")
