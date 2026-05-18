"""
RailGuard AI — Módulo de Banco de Dados
========================================
Gerencia a criação, conexão e operações CRUD no banco SQLite.
Usa sqlite3 nativo com suporte estrutural para futura migração ao PostgreSQL.

MIGRAÇÃO PARA POSTGRESQL:
  1. Instale: pip install psycopg2-binary sqlalchemy
  2. Substitua get_connection() por:
       from sqlalchemy import create_engine
       ENGINE = create_engine("postgresql://user:password@localhost:5432/railguard")
  3. Substitua sqlite3.connect() por ENGINE.connect()
  4. Substitua '?' por '%s' nos parâmetros das queries
  5. Ajuste os tipos de coluna (INTEGER AUTOINCREMENT → SERIAL, TIMESTAMP → TIMESTAMPTZ)
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime

# === CONFIGURAÇÃO DO BANCO ===
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "railguard.db")

# Para PostgreSQL, substitua por:
# DATABASE_URL = "postgresql://railguard_user:senha_segura@localhost:5432/railguard_db"


def get_connection() -> sqlite3.Connection:
    """Retorna conexão ativa com o banco SQLite."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Linhas acessíveis como dicionário
    conn.execute("PRAGMA foreign_keys = ON")  # Ativa integridade referencial
    return conn


def init_database():
    """Cria todas as tabelas caso não existam. Chamada ao iniciar a aplicação."""
    conn = get_connection()
    cur = conn.cursor()

    # --- Tabela: trechos ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trechos (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo                TEXT    UNIQUE NOT NULL,
        ferrovia              TEXT    NOT NULL,
        km_inicial            REAL    NOT NULL,
        km_final              REAL    NOT NULL,
        estado                TEXT    NOT NULL,
        tipo_via              TEXT    NOT NULL,
        criticidade_operacional TEXT  NOT NULL,
        observacoes           TEXT    DEFAULT '',
        data_cadastro         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # --- Tabela: ativos ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ativos (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo                TEXT    UNIQUE NOT NULL,
        tipo_ativo            TEXT    NOT NULL,
        trecho_id             INTEGER NOT NULL REFERENCES trechos(id),
        idade_anos            REAL    NOT NULL DEFAULT 0,
        data_ultima_manutencao TEXT,
        condicao_visual       TEXT    NOT NULL DEFAULT 'Bom',
        observacoes           TEXT    DEFAULT '',
        data_cadastro         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # --- Tabela: inspecoes ---
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
        observacoes         TEXT    DEFAULT '',
        imagem_path         TEXT,
        data_registro       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # --- Tabela: riscos ---
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

    # --- Tabela: alertas ---
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

    # --- Tabela: auditoria ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS auditoria (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        tipo_acao     TEXT NOT NULL,
        usuario       TEXT NOT NULL,
        item_alterado TEXT NOT NULL,
        descricao     TEXT NOT NULL
    )""")

    # --- Tabela: indicadores_esg ---
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

    conn.commit()
    conn.close()


# ===================================================
# TRECHOS
# ===================================================

def insert_trecho(codigo, ferrovia, km_inicial, km_final, estado,
                  tipo_via, criticidade_operacional, observacoes=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trechos (codigo, ferrovia, km_inicial, km_final, estado,
                             tipo_via, criticidade_operacional, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (codigo, ferrovia, km_inicial, km_final, estado,
          tipo_via, criticidade_operacional, observacoes))
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


# ===================================================
# ATIVOS
# ===================================================

def insert_ativo(codigo, tipo_ativo, trecho_id, idade_anos,
                 data_ultima_manutencao, condicao_visual, observacoes=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ativos (codigo, tipo_ativo, trecho_id, idade_anos,
                            data_ultima_manutencao, condicao_visual, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (codigo, tipo_ativo, trecho_id, idade_anos,
          data_ultima_manutencao, condicao_visual, observacoes))
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


# ===================================================
# INSPEÇÕES
# ===================================================

def insert_inspecao(ativo_id, data_inspecao, responsavel, tipo_inspecao,
                    fissura, desgaste, corrosao, falha_fixacao,
                    nivel_vibracao, temperatura, carga_operacional,
                    observacoes="", imagem_path=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO inspecoes (ativo_id, data_inspecao, responsavel, tipo_inspecao,
                               fissura, desgaste, corrosao, falha_fixacao,
                               nivel_vibracao, temperatura, carga_operacional,
                               observacoes, imagem_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ativo_id, data_inspecao, responsavel, tipo_inspecao,
          int(fissura), int(desgaste), int(corrosao), int(falha_fixacao),
          nivel_vibracao, temperatura, carga_operacional,
          observacoes, imagem_path))
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid


def get_all_inspecoes() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT i.*, a.codigo AS ativo_codigo, a.tipo_ativo, a.trecho_id
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


# ===================================================
# RISCOS
# ===================================================

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
        SELECT r.*, a.codigo AS ativo_codigo, a.tipo_ativo
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


# ===================================================
# ALERTAS
# ===================================================

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


# ===================================================
# AUDITORIA
# ===================================================

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


# ===================================================
# ESG
# ===================================================

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


# ===================================================
# ESTATÍSTICAS — DASHBOARD
# ===================================================

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
    """Retorna True se o banco ainda não foi populado."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM trechos")
    count = cur.fetchone()[0]
    conn.close()
    return count == 0
