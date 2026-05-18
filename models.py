"""
RailGuard AI — Modelos e Constantes de Domínio
================================================
Define enumerações, pesos e mapeamentos usados em toda a aplicação.
"""

# Tipos de ativo ferroviário
TIPOS_ATIVO = ["Trilho", "Dormente", "Fixação", "Ponte", "AMV", "Sinalização", "Outro"]

# Estados com malha ferroviária relevante no Brasil
ESTADOS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO"
]

# Tipos de via
TIPOS_VIA = [
    "Bitola Larga (1,6m)",
    "Bitola Métrica (1,0m)",
    "Bitola Padrão (1,435m)",
    "Via Dupla",
    "Pátio",
    "Ramal Industrial",
]

# Níveis de criticidade operacional
CRITICIDADE_OPERACIONAL = ["Baixa", "Média", "Alta", "Crítica"]

# Tipos de inspeção aceitos pelo sistema
TIPOS_INSPECAO = ["Manual", "Drone", "Sensor", "Câmera Embarcada", "Ultrassom"]

# Estados de conservação visual
CONDICAO_VISUAL = ["Ótimo", "Bom", "Regular", "Ruim", "Crítico"]

# Ferrovias representativas do Brasil (dados públicos, para demonstração)
FERROVIAS = [
    "MRS Logística",
    "Rumo Malha Paulista",
    "Rumo Malha Sul",
    "Rumo Malha Oeste",
    "Rumo Malha Norte",
    "VLI — Ferrovia Centro-Atlântica",
    "VLI Malha Norte",
    "Vale (EFC)",
    "Vale (EFVM)",
    "Ferrovia Transnordestina (TLSA)",
]

# Peso numérico de criticidade (usado em cálculos de risco)
CRITICIDADE_PESO: dict[str, int] = {
    "Baixa":   1,
    "Média":   2,
    "Alta":    3,
    "Crítica": 4,
}

# Peso numérico da condição visual
CONDICAO_PESO: dict[str, int] = {
    "Ótimo":   0,
    "Bom":     1,
    "Regular": 2,
    "Ruim":    3,
    "Crítico": 4,
}

# Faixas de classificação do risco operacional (score 0–100)
FAIXAS_RISCO = [
    (0,  25, "Baixo"),
    (26, 50, "Médio"),
    (51, 75, "Alto"),
    (76, 100, "Crítico"),
]

# Faixas de classificação RCRS
FAIXAS_RCRS = [
    (0,  25, "Conforme",                    "✅"),
    (26, 50, "Atenção",                     "⚠️"),
    (51, 75, "Não conformidade potencial",  "🔶"),
    (76, 100, "Crítico",                    "🔴"),
]

# Cores para gráficos e badges (mapeadas por nível de risco)
RISK_COLORS: dict[str, str] = {
    "Baixo":   "#2ecc71",
    "Médio":   "#f39c12",
    "Alto":    "#e67e22",
    "Crítico": "#e74c3c",
}

RCRS_COLORS: dict[str, str] = {
    "Conforme":                   "#2ecc71",
    "Atenção":                    "#f39c12",
    "Não conformidade potencial": "#e67e22",
    "Crítico":                    "#e74c3c",
}

ESG_PRIORITY_COLORS: dict[str, str] = {
    "Baixa":   "#2ecc71",
    "Média":   "#3498db",
    "Alta":    "#e67e22",
    "Crítica": "#e74c3c",
}

# Nomes descritivos das features de ML (ordem importa — deve coincidir com ml_model.py)
ML_FEATURE_NAMES = [
    "Idade do ativo (anos)",
    "Dias desde última manutenção",
    "Criticidade operacional",
    "Fissura detectada",
    "Desgaste detectado",
    "Corrosão detectada",
    "Falha de fixação",
    "Nível de vibração",
    "Carga operacional (%)",
    "Condição visual",
]
