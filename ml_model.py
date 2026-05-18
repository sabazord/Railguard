"""
RailGuard AI — Módulo de Machine Learning
==========================================
Treina um RandomForestClassifier para prever o nível de risco operacional
de ativos ferroviários.

Extensão futura:
  - Substituir labels heurísticos por dados rotulados por especialistas
  - Adicionar explicabilidade via SHAP: `import shap; explainer = shap.TreeExplainer(model)`
  - Experimentar XGBoost ou LightGBM para melhor performance
  - Exportar modelo com joblib para serving em produção
"""

from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report

from models import CRITICIDADE_PESO, CONDICAO_PESO, ML_FEATURE_NAMES
from risk_engine import calcular_risco_operacional

# Mapeamento label ↔ inteiro
RISK_TO_INT = {"Baixo": 0, "Médio": 1, "Alto": 2, "Crítico": 3}
INT_TO_RISK = {v: k for k, v in RISK_TO_INT.items()}

# Ordem das features (deve ser idêntica ao treinamento)
FEATURE_COLS = [
    "idade_anos",
    "dias_desde_manutencao",
    "criticidade_operacional",
    "fissura",
    "desgaste",
    "corrosao",
    "falha_fixacao",
    "nivel_vibracao",
    "carga_operacional",
    "condicao_visual",
]


# ===================================================
# GERAÇÃO DE DADOS SINTÉTICOS
# ===================================================

def gerar_dados_sinteticos(n_amostras: int = 600) -> tuple[pd.DataFrame, pd.Series]:
    """
    Gera dataset sintético usando o motor de risco como oráculo.
    Usado quando os dados reais são insuficientes para treinar o modelo.
    """
    rng = np.random.default_rng(seed=42)

    criticidades = list(CRITICIDADE_PESO.keys())
    condicoes    = list(CONDICAO_PESO.keys())

    registros = []
    for _ in range(n_amostras):
        crit    = rng.choice(criticidades)
        cond    = rng.choice(condicoes)
        idade   = float(rng.uniform(0, 30))
        dias_m  = int(rng.integers(0, 730))
        fissura = bool(rng.random() < 0.25)
        desgaste = bool(rng.random() < 0.45)
        corrosao = bool(rng.random() < 0.35)
        falha   = bool(rng.random() < 0.20)
        vibr    = float(rng.uniform(0, 10))
        carga   = float(rng.uniform(20, 100))

        score, nivel, _ = calcular_risco_operacional(
            idade_anos=idade,
            dias_desde_manutencao=dias_m,
            criticidade_operacional=crit,
            fissura=fissura,
            desgaste=desgaste,
            corrosao=corrosao,
            falha_fixacao=falha,
            nivel_vibracao=vibr,
            carga_operacional=carga,
            condicao_visual=cond,
        )

        registros.append({
            "idade_anos":             idade,
            "dias_desde_manutencao":  dias_m,
            "criticidade_operacional": CRITICIDADE_PESO.get(crit, 2),
            "fissura":                int(fissura),
            "desgaste":               int(desgaste),
            "corrosao":               int(corrosao),
            "falha_fixacao":          int(falha),
            "nivel_vibracao":         vibr,
            "carga_operacional":      carga,
            "condicao_visual":        CONDICAO_PESO.get(cond, 2),
            "nivel_risco":            RISK_TO_INT.get(nivel, 1),
        })

    df = pd.DataFrame(registros)
    return df[FEATURE_COLS], df["nivel_risco"]


# ===================================================
# PREPARAÇÃO DE FEATURES (dados reais)
# ===================================================

def preparar_features_reais(
    df_inspecoes: pd.DataFrame,
    df_ativos: pd.DataFrame,
    df_trechos: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series] | tuple[None, None]:
    """
    Constrói a matriz de features a partir dos dados reais do banco.
    """
    registros = []

    for _, insp in df_inspecoes.iterrows():
        ativo_rows = df_ativos[df_ativos["id"] == insp["ativo_id"]]
        if ativo_rows.empty:
            continue
        ativo = ativo_rows.iloc[0]

        trecho_rows = df_trechos[df_trechos["id"] == ativo["trecho_id"]]
        if trecho_rows.empty:
            continue
        trecho = trecho_rows.iloc[0]

        # Dias desde a última manutenção
        try:
            data_m = pd.to_datetime(ativo["data_ultima_manutencao"])
            data_i = pd.to_datetime(insp["data_inspecao"])
            dias_m = max((data_i - data_m).days, 0)
        except Exception:
            dias_m = 365

        score, nivel, _ = calcular_risco_operacional(
            idade_anos=float(ativo["idade_anos"]),
            dias_desde_manutencao=dias_m,
            criticidade_operacional=trecho["criticidade_operacional"],
            fissura=bool(insp["fissura"]),
            desgaste=bool(insp["desgaste"]),
            corrosao=bool(insp["corrosao"]),
            falha_fixacao=bool(insp["falha_fixacao"]),
            nivel_vibracao=float(insp["nivel_vibracao"]),
            carga_operacional=float(insp["carga_operacional"]),
            condicao_visual=ativo["condicao_visual"],
        )

        registros.append({
            "idade_anos":              float(ativo["idade_anos"]),
            "dias_desde_manutencao":   dias_m,
            "criticidade_operacional": CRITICIDADE_PESO.get(trecho["criticidade_operacional"], 2),
            "fissura":                 int(insp["fissura"]),
            "desgaste":                int(insp["desgaste"]),
            "corrosao":                int(insp["corrosao"]),
            "falha_fixacao":           int(insp["falha_fixacao"]),
            "nivel_vibracao":          float(insp["nivel_vibracao"]),
            "carga_operacional":       float(insp["carga_operacional"]),
            "condicao_visual":         CONDICAO_PESO.get(ativo["condicao_visual"], 2),
            "nivel_risco":             RISK_TO_INT.get(nivel, 1),
        })

    if len(registros) < 10:
        return None, None

    df = pd.DataFrame(registros)
    return df[FEATURE_COLS], df["nivel_risco"]


# ===================================================
# TREINAMENTO
# ===================================================

def treinar_modelo(
    X: pd.DataFrame,
    y: pd.Series,
) -> tuple[RandomForestClassifier, float, pd.DataFrame, pd.Series, str]:
    """
    Treina o RandomForestClassifier e retorna métricas.

    Retorna:
        model, accuracy, X_test, y_test, classification_report_str
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred   = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    target_names = [INT_TO_RISK.get(i, str(i)) for i in sorted(y.unique())]
    report = classification_report(y_test, y_pred, target_names=target_names, zero_division=0)

    return model, accuracy, X_test, y_test, report


# ===================================================
# IMPORTÂNCIA DE FEATURES
# ===================================================

def get_feature_importance(model: RandomForestClassifier) -> pd.DataFrame:
    """Retorna DataFrame com importância de cada feature, ordenado decrescente."""
    return pd.DataFrame({
        "Variável":    ML_FEATURE_NAMES,
        "Importância": model.feature_importances_,
    }).sort_values("Importância", ascending=False).reset_index(drop=True)


# ===================================================
# PREDIÇÃO
# ===================================================

def prever_risco(model: RandomForestClassifier, params: dict) -> tuple[str, np.ndarray]:
    """
    Prediz o nível de risco para um novo ativo com base nos parâmetros fornecidos.

    `params` deve conter as chaves em FEATURE_COLS com valores numéricos.

    Retorna:
        (nivel_risco: str, probabilidades: np.ndarray shape (4,))
    """
    vetor = np.array([[params[col] for col in FEATURE_COLS]])
    pred  = model.predict(vetor)[0]
    probs = model.predict_proba(vetor)[0]

    # Expande probabilidades para sempre ter 4 classes (Baixo/Médio/Alto/Crítico)
    classes = model.classes_
    probs_full = np.zeros(4)
    for cls, prob in zip(classes, probs):
        probs_full[int(cls)] = prob

    return INT_TO_RISK.get(int(pred), "Médio"), probs_full
