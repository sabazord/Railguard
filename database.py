"""
RailGuard AI — Módulo de Banco de Dados
========================================
v0.4 — Adicionado:
  - km_posicao em ativos (posição quilométrica na malha)
  - probabilidade_risco, consequencia_risco, score_matriz em inspecoes
  - tabela zonas_criticas para análise espacial de defeitos
  - funções CRUD para zonas_criticas

MIGRAÇÃO PARA POSTGRESQL:
  1. pip install psycopg2-binary sqlalchemy
  2. Substitua get_connection() por:
       from sqlalchemy import create_engine
       ENGINE = create_engine("postgresql://user:password@localhost:5432/railguard")
  3. Substitua sqlite3.connect() por ENGINE.connect()
  4. Substitua '?' por '%s' nos parâmetros das queries
  5. INTEGER AUTOINCREMENT → SERIAL | TIMESTAMP → TIMESTAMPTZ
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime

# === CONFIGURAÇÃO DO BANCO ===
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "railguard.db")


def get_connection() -> sqlite3.Connection:
    """Retorna conexão ativa com o banco SQLite."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Cria todas as tabelas caso não existam."""
    conn = get_connection()
    cur = conn.cursor()

    # --- trechos ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trechos (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo                  TEXT    UNIQUE NOT NULL,
        ferrovia                TEXT    NOT NULL,
        km_inicial              REAL    NOT NULL,
        km_final                REAL    NOT NULL,
        estado                  TEXT    NOT NULL,
        tipo_via                TEXT    NOT NULL,
        criticidade_operacional TEXT    NOT NULL,
        observacoes             TEXT    DEFAULT '',
        -- Metadados operacionais (usados no estudo de caso Heavy Haul)
        velocidade_max_kmh      REAL    DEFAULT NULL,
        carga_max_eixo_ton      REAL    DEFAULT NULL,
        trens_por_dia           INTEGER DEFAULT NULL,
        data_cadastro           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # --- ativos ---
    # km_posicao: posição exata do ativo na malha (ex.: 7.2 = Km 7+200)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ativos (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo                  TEXT    UNIQUE NOT NULL,
        tipo_ativo              TEXT    NOT NULL,
        trecho_id               INTEGER NOT NULL REFERENCES trechos(id),
        idade_anos              REAL    NOT NULL DEFAULT 0,
        data_ultima_manutencao  TEXT,
        condicao_visual         TEXT    NOT NULL DEFAULT 'Bom',
        km_posicao              REAL    DEFAULT NULL,
        observacoes             TEXT    DEFAULT '',
        data_cadastro           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # --- inspecoes ---
    # probabilidade_risco (1–5), consequencia_risco (1–5), score_matriz (1–25)
    # implementam a Matriz P×C ao lado do score ponderado existente
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inspecoes (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        ativo_id            INTEGER NOT NULL REFERENCES ativos(id),
        data_inspecao       TEXT    NOT NULL,
        responsavel         TEXT    NOT NULL,
        tipo_inspecao       TEXT    NOT NULL,
        fissura             INTEGER DEFAULT 0,
        desgaste            INTEGER DEFAULT 0,
        corrosao            INTEGER DEFAULT 0,
        falha_fixacao       INTEGER DEFAULT 0,
        nivel_vibracao      REAL    DEFAULT 0,
        temperatura         REAL    DEFAULT 0,
        carga_operacional   REAL    DEFAULT 0,
        -- Matriz P×C (v0.4)
        probabilidade_risco INTEGER DEFAULT NULL,
        consequencia_risco  INTEGER DEFAULT NULL,
        score_matriz        INTEGER DEFAULT NULL,
        nivel_matriz        TEXT    DEFAULT NULL,
        observacoes         TEXT    DEFAULT '',
        imagem_path         TEXT,
        data_registro       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # --- riscos ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS riscos (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        inspecao_id         INTEGER NOT NULL REFERENCES inspecoes(id),
        ativo_id            INTEGER NOT NULL REFERENCES ativos(id),
        score_risco         REAL    NOT NULL,
        nivel_risco         TEXT    NOT NULL,
        score_rcrs          REAL,
        classificacao_rcrs  TEXT,
        recomendacao        TEXT,
        data_calculo        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # --- alertas ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alertas (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        ativo_id        INTEGER REFERENCES ativos(id),
        trecho_id       INTEGER REFERENCES trechos(id),
        tipo_alerta     TEXT    NOT NULL,
        nivel_urgencia  TEXT    NOT NULL,
        mensagem        TEXT    NOT NULL,
        status          TEXT    DEFAULT 'Aberto',
        data_alerta     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        data_resolucao  TIMESTAMP
    )""")

    # --- auditoria ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS auditoria (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        tipo_acao     TEXT NOT NULL,
        usuario       TEXT NOT NULL,
        item_alterado TEXT NOT NULL,
        descricao     TEXT NOT NULL
    )""")

    # --- indicadores_esg ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS indicadores_esg (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        trecho_id             INTEGER NOT NULL REFERENCES trechos(id),
        risco_ambiental       REAL,
        impacto_paralisacao   REAL,
        eficiencia_manutencao REAL,
        prioridade_esg        TEXT,
        emissao_co2_estimada  REAL,
        area_impacto_km2      REAL,
        recomendacoes         TEXT,
        data_calculo          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # --- zonas_criticas (v0.4) ---
    # Registra clusters espaciais de defeitos detectados no mesmo trecho de via.
    # A causa-raiz encadeada (drenagem → dormente → fixação → AMV) é registrada aqui.
    cur.execute("""
    CREATE TABLE IF NOT EXISTS zonas_criticas (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        trecho_id           INTEGER NOT NULL REFERENCES trechos(id),
        km_inicio           REAL    NOT NULL,
        km_fim              REAL    NOT NULL,
        total_defeitos      INTEGER NOT NULL DEFAULT 0,
        tipos_ativo         TEXT    DEFAULT '',
        nivel_risco_zona    TEXT    NOT NULL DEFAULT 'Alto',
        score_medio         REAL    DEFAULT 0,
        causa_raiz_provavel TEXT    DEFAULT '',
        descricao           TEXT    DEFAULT '',
        status              TEXT    DEFAULT 'Ativo',
        data_deteccao       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Migração não-destrutiva: adiciona colunas novas em bancos antigos
    _migrate_columns(cur)

    conn.commit()
    conn.close()


def _migrate_columns(cur):
    """Adiciona colunas v0.4 em bancos SQLite já existentes (ALTER TABLE seguro)."""
    migrations = [
        ("ativos",    "km_posicao",           "REAL DEFAULT NULL"),
        ("ativos",    "observacoes",           "TEXT DEFAULT ''"),
        ("inspecoes", "probabilidade_risco",   "INTEGER DEFAULT NULL"),
        ("inspecoes", "consequencia_risco",    "INTEGER DEFAULT NULL"),
        ("inspecoes", "score_matriz",          "INTEGER DEFAULT NULL"),
        ("inspecoes", "nivel_matriz",          "TEXT DEFAULT NULL"),
        ("trechos",   "velocidade_max_kmh",    "REAL DEFAULT NULL"),
        ("trechos",   "carga_max_eixo_ton",    "REAL DEFAULT NULL"),
        ("trechos",   "trens_por_dia",         "INTEGER DEFAULT NULL"),
    ]
    for tabela, coluna, tipo in migrations:
        try:
            cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")
        except Exception:
            pass  # coluna já existe — ignorar


# ═══════════════════════════════════════════════════════
#  TRECHOS
# ═══════════════════════════════════════════════════════

def insert_trecho(codigo, ferrovia, km_inicial, km_final, estado,
                  tipo_via, criticidade_operacional, observacoes="",
                  velocidade_max_kmh=None, carga_max_eixo_ton=None,
                  trens_por_dia=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trechos (codigo, ferrovia, km_inicial, km_final, estado,
                             tipo_via, criticidade_operacional, observacoes,
                             velocidade_max_kmh, carga_max_eixo_ton, trens_por_dia)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (codigo, ferrovia, km_inicial, km_final, estado,
          tipo_via, criticidade_operacional, observacoes,
          velocidade_max_kmh, carga_max_eixo_ton, trens_por_dia))
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid


def get_all_trechos() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM trechos ORDER BY data_cadastro DESC", conn)
    conn.close()
    return df


def get_trecho_by_id(trecho_id) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trechos WHERE id = ?", (trecho_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ═══════════════════════════════════════════════════════
#  ATIVOS
# ═══════════════════════════════════════════════════════

def insert_ativo(codigo, tipo_ativo, trecho_id, idade_anos,
                 data_ultima_manutencao, condicao_visual,
                 observacoes="", km_posicao=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ativos (codigo, tipo_ativo, trecho_id, idade_anos,
                            data_ultima_manutencao, condicao_visual,
                            observacoes, km_posicao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (codigo, tipo_ativo, trecho_id, idade_anos,
          data_ultima_manutencao, condicao_visual, observacoes, km_posicao))
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid


def get_all_ativos() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT a.*, t.codigo AS trecho_codigo, t.ferrovia, t.criticidade_operacional
        FROM ativos a
        JOIN trechos t ON a.trecho_id = t.id
        ORDER BY a.data_cadastro DESC
    """, conn)
    conn.close()
    return df


def get_ativo_by_id(ativo_id) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ativos WHERE id = ?", (ativo_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_ativos_by_trecho(trecho_id) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM ativos WHERE trecho_id = ? ORDER BY km_posicao ASC NULLS LAST",
        conn, params=(trecho_id,))
    conn.close()
    return df


# ═══════════════════════════════════════════════════════
#  INSPEÇÕES
# ═══════════════════════════════════════════════════════

def insert_inspecao(ativo_id, data_inspecao, responsavel, tipo_inspecao,
                    fissura, desgaste, corrosao, falha_fixacao,
                    nivel_vibracao, temperatura, carga_operacional,
                    observacoes="", imagem_path=None,
                    probabilidade_risco=None, consequencia_risco=None):
    """
    Registra inspeção com suporte à Matriz P×C (v0.4).
    probabilidade_risco e consequencia_risco: inteiros de 1 a 5.
    """
    score_matriz = None
    nivel_matriz = None
    if probabilidade_risco and consequencia_risco:
        from risk_engine import calcular_risco_matriz
        score_matriz, nivel_matriz = calcular_risco_matriz(
            probabilidade_risco, consequencia_risco)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO inspecoes (ativo_id, data_inspecao, responsavel, tipo_inspecao,
                               fissura, desgaste, corrosao, falha_fixacao,
                               nivel_vibracao, temperatura, carga_operacional,
                               observacoes, imagem_path,
                               probabilidade_risco, consequencia_risco,
                               score_matriz, nivel_matriz)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ativo_id, data_inspecao, responsavel, tipo_inspecao,
          int(fissura), int(desgaste), int(corrosao), int(falha_fixacao),
          nivel_vibracao, temperatura, carga_operacional,
          observacoes, imagem_path,
          probabilidade_risco, consequencia_risco,
          score_matriz, nivel_matriz))
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid


def get_all_inspecoes() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT i.*, a.codigo AS ativo_codigo, a.tipo_ativo, a.trecho_id, a.km_posicao
        FROM inspecoes i
        JOIN ativos a ON i.ativo_id = a.id
        ORDER BY i.data_inspecao DESC
    """, conn)
    conn.close()
    return df


def get_inspecoes_by_ativo(ativo_id) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM inspecoes WHERE ativo_id = ? ORDER BY data_inspecao DESC",
        conn, params=(ativo_id,))
    conn.close()
    return df


# ═══════════════════════════════════════════════════════
#  RISCOS
# ═══════════════════════════════════════════════════════

def insert_risco(inspecao_id, ativo_id, score_risco, nivel_risco,
                 score_rcrs, classificacao_rcrs, recomendacao):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO riscos (inspecao_id, ativo_id, score_risco, nivel_risco,
                            score_rcrs, classificacao_rcrs, recomendacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (inspecao_id, ativo_id, score_risco, nivel_risco,
          score_rcrs, classificacao_rcrs, recomendacao))
    conn.commit()
    conn.close()


def get_all_riscos() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT r.*, a.codigo AS ativo_codigo, a.tipo_ativo, a.km_posicao
        FROM riscos r
        JOIN ativos a ON r.ativo_id = a.id
        ORDER BY r.data_calculo DESC
    """, conn)
    conn.close()
    return df


def get_ultimo_risco_by_ativo(ativo_id) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM riscos WHERE ativo_id = ?
        ORDER BY data_calculo DESC LIMIT 1
    """, (ativo_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ═══════════════════════════════════════════════════════
#  ALERTAS
# ═══════════════════════════════════════════════════════

def insert_alerta(ativo_id, trecho_id, tipo_alerta, nivel_urgencia, mensagem):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO alertas (ativo_id, trecho_id, tipo_alerta, nivel_urgencia, mensagem)
        VALUES (?, ?, ?, ?, ?)
    """, (ativo_id, trecho_id, tipo_alerta, nivel_urgencia, mensagem))
    conn.commit()
    conn.close()


def get_all_alertas() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT al.*,
               a.codigo AS ativo_codigo,
               t.codigo AS trecho_codigo
        FROM alertas al
        LEFT JOIN ativos  a ON al.ativo_id  = a.id
        LEFT JOIN trechos t ON al.trecho_id = t.id
        ORDER BY al.data_alerta DESC
    """, conn)
    conn.close()
    return df


def fechar_alerta(alerta_id):
    conn = get_connection()
    conn.execute("""
        UPDATE alertas SET status = 'Resolvido', data_resolucao = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (alerta_id,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════
#  AUDITORIA
# ═══════════════════════════════════════════════════════

def insert_auditoria(tipo_acao, usuario, item_alterado, descricao):
    conn = get_connection()
    conn.execute("""
        INSERT INTO auditoria (tipo_acao, usuario, item_alterado, descricao)
        VALUES (?, ?, ?, ?)
    """, (tipo_acao, usuario, item_alterado, descricao))
    conn.commit()
    conn.close()


def get_all_auditoria() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM auditoria ORDER BY data_hora DESC", conn)
    conn.close()
    return df


# ═══════════════════════════════════════════════════════
#  ESG
# ═══════════════════════════════════════════════════════

def insert_esg(trecho_id, risco_ambiental, impacto_paralisacao,
               eficiencia_manutencao, prioridade_esg,
               emissao_co2_estimada, area_impacto_km2, recomendacoes):
    conn = get_connection()
    conn.execute("""
        INSERT INTO indicadores_esg (trecho_id, risco_ambiental, impacto_paralisacao,
                                     eficiencia_manutencao, prioridade_esg,
                                     emissao_co2_estimada, area_impacto_km2, recomendacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (trecho_id, risco_ambiental, impacto_paralisacao,
          eficiencia_manutencao, prioridade_esg,
          emissao_co2_estimada, area_impacto_km2, recomendacoes))
    conn.commit()
    conn.close()


def get_all_esg() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT e.*, t.codigo AS trecho_codigo, t.ferrovia, t.estado
        FROM indicadores_esg e
        JOIN trechos t ON e.trecho_id = t.id
        ORDER BY e.data_calculo DESC
    """, conn)
    conn.close()
    return df


# ═══════════════════════════════════════════════════════
#  ZONAS CRÍTICAS (v0.4)
# ═══════════════════════════════════════════════════════

def insert_zona_critica(trecho_id, km_inicio, km_fim, total_defeitos,
                        tipos_ativo, nivel_risco_zona, score_medio,
                        causa_raiz_provavel, descricao):
    """Registra uma zona crítica detectada por clustering espacial de defeitos."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO zonas_criticas (trecho_id, km_inicio, km_fim, total_defeitos,
                                    tipos_ativo, nivel_risco_zona, score_medio,
                                    causa_raiz_provavel, descricao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (trecho_id, km_inicio, km_fim, total_defeitos,
          tipos_ativo, nivel_risco_zona, score_medio,
          causa_raiz_provavel, descricao))
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid


def get_all_zonas_criticas() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT zc.*, t.codigo AS trecho_codigo, t.ferrovia
        FROM zonas_criticas zc
        JOIN trechos t ON zc.trecho_id = t.id
        ORDER BY zc.nivel_risco_zona DESC, zc.total_defeitos DESC
    """, conn)
    conn.close()
    return df


def get_zonas_criticas_by_trecho(trecho_id) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM zonas_criticas WHERE trecho_id = ? ORDER BY km_inicio ASC",
        conn, params=(trecho_id,))
    conn.close()
    return df


# ═══════════════════════════════════════════════════════
#  DASHBOARD STATS
# ═══════════════════════════════════════════════════════

def get_dashboard_stats() -> dict:
    """Retorna totalizadores para o painel principal."""
    conn = get_connection()
    cur = conn.cursor()

    def scalar(sql, params=()):
        cur.execute(sql, params)
        r = cur.fetchone()
        return r[0] if r else 0

    stats = {
        "total_trechos":          scalar("SELECT COUNT(*) FROM trechos"),
        "total_ativos":           scalar("SELECT COUNT(*) FROM ativos"),
        "total_inspecoes":        scalar("SELECT COUNT(*) FROM inspecoes"),
        "total_alertas_abertos":  scalar("SELECT COUNT(*) FROM alertas WHERE status = 'Aberto'"),
        "total_zonas_criticas":   scalar("SELECT COUNT(*) FROM zonas_criticas WHERE status = 'Ativo'"),
    }

    cur.execute("SELECT nivel_risco, COUNT(*) FROM riscos GROUP BY nivel_risco")
    risk_map = {row[0]: row[1] for row in cur.fetchall()}
    stats["risco_baixo"]   = risk_map.get("Baixo",   0)
    stats["risco_medio"]   = risk_map.get("Médio",   0)
    stats["risco_alto"]    = risk_map.get("Alto",    0)
    stats["risco_critico"] = risk_map.get("Crítico", 0)

    conn.close()
    return stats


def check_db_empty() -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM trechos")
    count = cur.fetchone()[0]
    conn.close()
    return count == 0
